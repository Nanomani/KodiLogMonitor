import re
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import threading
import webbrowser
import os
import sys
import subprocess
from urllib.parse import quote

from config import *
from config import APP_THEME
from languages import LANGS, LANG_NAMES, LANG_CODES
from utils import get_system_font, parse_version
from ui.ui_builder import ToolTip, _patch_combo_hover_text


class ActionsMixin:
    """Manages all user interactions (buttons, menus, shortcuts)."""

    def open_file(self, event=None):
        path = filedialog.askopenfilename(
            filetypes=[("Log files", "*.log"), ("All files", "*.*")]
        )
        if path:
            self.start_monitoring(path, is_manual=False)
        return "break"

    def export_log(self, event=None):
        """Saves the current content of the text area to a file chosen by the user."""
        if not self.check_log_loaded():
            return
        if not self.check_log_available():
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=EXPORT_FILE
        )
        if save_path:
            try:
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(self._strip_pad(self.txt_area.get("1.0", tk.END)))
            except IOError as e:
                print(f"Error exporting log: {e}")

    def upload_to_pastebin(self, event=None):
        """Copy the entire log to clipboard and open paste.kodi.tv."""
        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])
        if not self.check_log_loaded():
            return
        if not self.check_log_available():
            return

        try:
            with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            self.root.update()

            self.open_url(self.paste_url)

            msg_confirm = l_ui.get("copy_ok", "Log copied! Paste it on the site.")
            self.inactivity_timer_var.set(msg_confirm)
            self.root.after(5000, lambda: self.inactivity_timer_var.set(""))

        except Exception as e:
            messagebox.showerror("Error", f"Unable to read the file: {e}")

    # ------------------------------------------------------------------
    # Exclusion list  (file: .kodi_show_exclude, one pattern per line)
    # ------------------------------------------------------------------

    def update_exclude_button(self):
        """
        Refreshes the exclusion list button icon and tooltip to reflect
        whether any exclusion patterns are currently active.
        ☰ = empty list (neutral);  ⛔ = at least one active exclusion.
        Safe to call at any time; no-ops if the button does not exist yet.
        """
        if not hasattr(self, "btn_exclude_list"):
            return
        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])
        if self.exclude_patterns:
            self.btn_exclude_list.configure(
                text="⛔",
                fg_color=COLOR_DANGER,
                text_color=COLOR_TEXT_ON_ACCENT,
            )
            tip = l_ui.get("tip_exclude_active", "Active exclusions - click to manage")
        else:
            self.btn_exclude_list.configure(
                text="☰",
                fg_color=COLOR_BTN_DEFAULT,
                text_color=COLOR_TEXT_BRIGHT,
            )
            tip = l_ui.get("tip_exclude_empty", "No active exclusions")
        if hasattr(self, "exclude_list_tooltip"):
            self.exclude_list_tooltip.text = tip

    def show_exclude_list(self):
        """Opens the exclusion pattern manager."""
        if not self.check_log_loaded():
            return
        if not self.check_log_available():
            return
        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])

        def _on_save(new_list):
            self.save_exclude_patterns(new_list)
            self.update_exclude_button()
            self.trigger_refresh()

        self.show_list_manager(
            title=l_ui.get("exclude_list_title", "Exclusion list"),
            get_items=lambda: list(self.exclude_patterns),
            on_save=_on_save,
            empty_msg=l_ui.get("exclude_list_empty", "No active exclusions."),
        )

    def show_history_manager(self):
        """Opens the search history manager."""
        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])

        def _on_save(new_list):
            self.search_history = new_list
            self.save_search_history()
            self.history_listbox.delete(0, tk.END)
            for item in new_list:
                self.history_listbox.insert(tk.END, item)
            self.hide_history_dropdown()
            self.update_history_clear_tooltip()

        self.show_list_manager(
            title=l_ui.get("history_list_title", "Search history"),
            get_items=lambda: list(self.search_history),
            on_save=_on_save,
            empty_msg=l_ui.get("history_list_empty", "No search history."),
        )

    def show_list_manager(self, title, get_items, on_save, empty_msg=""):
        """
        Generic list manager window.
        Handles exclusions, search history, or any simple string list.
        - title     : str - window title and header label
        - get_items : callable → list[str] - always-fresh item list
        - on_save   : callable(list[str]) - persist + refresh UI after any change
        - empty_msg : str - message shown when the list is empty
        """
        # Only one manager can be open at a time
        if getattr(self, "_list_manager_open", False):
            return
        self._list_manager_open = True

        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])

        # --- Window ---
        win = ctk.CTkToplevel(self.root)
        win.title(title)
        win.configure(fg_color=COLOR_BG_DIALOG)
        win.transient(self.root)
        win.resizable(False, False)
        # Start off-screen to avoid flicker during build.
        # Avoid withdraw(): CTkToplevel may call deiconify() internally after
        # its own init delay, leaving the window in an inconsistent state.
        win.geometry("+10000+10000")

        def _on_close(event=None):
            self._list_manager_open = False
            try:
                win.grab_release()
                win.destroy()
            except Exception:
                pass

        win.protocol("WM_DELETE_WINDOW", _on_close)
        win.bind("<Escape>",    _on_close)
        win.bind("<BackSpace>", _on_close)

        # --- Layout ---
        content = ctk.CTkFrame(win, fg_color=COLOR_BG_DIALOG, corner_radius=0)
        content.pack(fill="both", expand=True, padx=0, pady=0)

        tk.Label(
            content,
            text=title,
            bg=COLOR_BG_DIALOG,
            fg=COLOR_ACCENT,
            font=(self._main_font, 14, "bold"),
        ).pack(pady=(20, 10), fill="x")
        tk.Frame(content, bg=COLOR_SEPARATOR, height=2).pack(fill="x", padx=self.sc(40))

        # Buttons packed first (bottom) so they are always visible
        btn_frame = tk.Frame(content, bg=COLOR_BG_DIALOG)
        btn_frame.pack(side="bottom", pady=(self.sc(50), self.sc(40)))

        # Scrollable list area
        list_container = tk.Frame(content, bg=COLOR_BG_DIALOG)
        list_container.pack(fill="both", expand=True, padx=self.sc(40), pady=(14, 4))

        vscroll = ctk.CTkScrollbar(
            list_container,
            orientation="vertical",
            width=12,
            fg_color="transparent",
            button_color=SCROLL_THUMB_DEFAULT,
            button_hover_color=SCROLL_THUMB_HOVER,
            corner_radius=10,
            border_spacing=2,
        )
        vscroll.pack(side="right", fill="y", padx=(5, 0))

        list_canvas = tk.Canvas(
            list_container,
            bg=COLOR_BG_DIALOG,
            highlightthickness=0,
            bd=0,
            yscrollcommand=vscroll.set,
        )
        list_canvas.pack(side="left", fill="both", expand=True)
        vscroll.configure(command=list_canvas.yview)

        inner_frame = tk.Frame(list_canvas, bg=COLOR_BG_DIALOG)
        _canvas_win = list_canvas.create_window((0, 0), window=inner_frame, anchor="nw")

        def _on_inner_configure(e=None):
            list_canvas.configure(scrollregion=list_canvas.bbox("all"))

        def _on_canvas_configure(e=None):
            list_canvas.itemconfig(_canvas_win, width=list_canvas.winfo_width())
            list_canvas.configure(scrollregion=list_canvas.bbox("all"))

        inner_frame.bind("<Configure>", _on_inner_configure)
        list_canvas.bind("<Configure>", _on_canvas_configure)

        def _on_mousewheel(e):
            bbox = list_canvas.bbox("all")
            if bbox and bbox[3] > list_canvas.winfo_height():
                list_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        list_canvas.bind("<MouseWheel>", _on_mousewheel)
        inner_frame.bind("<MouseWheel>", _on_mousewheel)

        # --- Buttons ---
        def _clear_all():
            on_save([])
            _rebuild()

        btn_clear_all = ctk.CTkButton(
            btn_frame,
            text=l_ui.get("exclude_clear_all", "Clear all"),
            fg_color=COLOR_BTN_DEFAULT,
            hover=False,
            text_color=COLOR_TEXT_MAIN,
            font=ctk.CTkFont(family=self._main_font, size=12, weight="bold"),
            corner_radius=5,
            width=120,
            height=32,
            command=_clear_all,
        )
        btn_clear_all.bind("<Enter>", lambda e: btn_clear_all.configure(fg_color=COLOR_DANGER,      text_color="#ffffff"),       add="+")
        btn_clear_all.bind("<Leave>", lambda e: btn_clear_all.configure(fg_color=COLOR_BTN_DEFAULT, text_color=COLOR_TEXT_MAIN), add="+")

        btn_ok = ctk.CTkButton(
            btn_frame,
            text="Ok",
            command=_on_close,
            fg_color=COLOR_BTN_DEFAULT,
            hover_color=COLOR_BTN_ACTIVE,
            text_color=COLOR_TEXT_MAIN,
            font=ctk.CTkFont(family=self._main_font, size=12, weight="bold"),
            corner_radius=5,
            width=120,
            height=32,
        )
        btn_ok.pack(side="left")

        # --- Keyboard navigation state ---
        _LABEL_MAX_CHARS = 55
        _del_buttons  = []                          # list of (CTkButton, command_fn)
        _focus_state  = {"type": "none", "idx": 0} # "delete" | "ok" | "clear"

        def _set_focus(ftype, idx=0):
            """Move visual keyboard focus to the target button."""
            prev = _focus_state["type"]
            if prev == "delete" and _focus_state["idx"] < len(_del_buttons):
                _del_buttons[_focus_state["idx"]][0].configure(
                    fg_color=COLOR_BTN_DEFAULT, text_color=COLOR_TEXT_BRIGHT
                )
            elif prev == "ok":
                btn_ok.configure(fg_color=COLOR_BTN_DEFAULT)
            elif prev == "clear":
                try:
                    if btn_clear_all.winfo_ismapped():
                        btn_clear_all.configure(fg_color=COLOR_BTN_DEFAULT, text_color=COLOR_TEXT_MAIN)
                except Exception:
                    pass

            _focus_state["type"] = ftype
            _focus_state["idx"]  = idx

            if ftype == "delete" and idx < len(_del_buttons):
                btn = _del_buttons[idx][0]
                btn.configure(fg_color=COLOR_DANGER, text_color="#ffffff")
                # Auto-scroll so the focused button stays visible
                inner_frame.update_idletasks()
                bbox = list_canvas.bbox("all")
                if bbox:
                    total_h  = bbox[3] - bbox[1]
                    canvas_h = list_canvas.winfo_height()
                    if total_h > canvas_h:
                        btn_y     = btn.winfo_rooty() - inner_frame.winfo_rooty()
                        btn_h     = btn.winfo_height()
                        top_px    = list_canvas.yview()[0] * total_h
                        bottom_px = top_px + canvas_h
                        if btn_y < top_px:
                            list_canvas.yview_moveto(btn_y / total_h)
                        elif btn_y + btn_h > bottom_px:
                            list_canvas.yview_moveto((btn_y + btn_h - canvas_h) / total_h)
            elif ftype == "ok":
                btn_ok.configure(fg_color=COLOR_BTN_ACTIVE)
            elif ftype == "clear":
                btn_clear_all.configure(fg_color=COLOR_DANGER, text_color="#ffffff")

        def _rebuild(restore_idx=None):
            """Clears and redraws the list rows, then syncs button visibility."""
            _del_buttons.clear()
            for w in inner_frame.winfo_children():
                w.destroy()

            items = get_items()

            if not items:
                tk.Label(
                    inner_frame,
                    text=empty_msg,
                    bg=COLOR_BG_DIALOG,
                    fg=COLOR_TEXT_DIM,
                    font=(self._mono_font, 11),
                    justify="left",
                ).pack(anchor="w", pady=(0, 4))
            else:
                for idx, item in enumerate(items):
                    row = tk.Frame(inner_frame, bg=COLOR_BG_DIALOG)
                    row.pack(fill="x", pady=2)

                    display = item if len(item) <= _LABEL_MAX_CHARS else item[:_LABEL_MAX_CHARS - 1] + "…"
                    lbl = tk.Label(
                        row,
                        text=display,
                        bg=COLOR_BG_DIALOG,
                        fg=COLOR_TEXT_MAIN,
                        font=(self._mono_font, 11),
                        justify="left",
                        anchor="w",
                    )
                    lbl.pack(side="left", fill="x", expand=True, padx=(0, 10))
                    if display != item:
                        ToolTip(lbl, item)

                    def _make_remove(i):
                        def _remove():
                            current   = get_items()
                            updated   = [p for j, p in enumerate(current) if j != i]
                            on_save(updated)
                            n_after   = len(updated)
                            _rebuild(restore_idx=min(i, n_after - 1) if n_after > 0 else None)
                        return _remove

                    cmd = _make_remove(idx)
                    btn_del = ctk.CTkButton(
                        row,
                        text="×",
                        width=28,
                        height=22,
                        fg_color=COLOR_BTN_DEFAULT,
                        hover=False,
                        text_color=COLOR_TEXT_BRIGHT,
                        font=(self._main_font, 14, "bold"),
                        corner_radius=4,
                        command=cmd,
                    )
                    btn_del.bind("<Enter>", lambda e, b=btn_del: b.configure(fg_color=COLOR_DANGER,      text_color="#ffffff"),         add="+")
                    btn_del.bind("<Leave>", lambda e, b=btn_del: b.configure(fg_color=COLOR_BTN_DEFAULT, text_color=COLOR_TEXT_BRIGHT), add="+")
                    btn_del.pack(side="right")
                    _del_buttons.append((btn_del, cmd))

            if len(items) >= 2:
                btn_clear_all.pack(side="left", padx=(0, 10))
                btn_ok.pack_forget()
                btn_ok.pack(side="left")
            else:
                btn_clear_all.pack_forget()

            _focus_state["type"] = "none"
            if restore_idx is not None and _del_buttons:
                _set_focus("delete", restore_idx)
            elif _del_buttons:
                _set_focus("delete", 0)
            else:
                _set_focus("ok")

        def _on_key(e):
            """Arrow / Enter keyboard navigation."""
            key       = e.keysym
            n         = len(_del_buttons)
            t         = _focus_state["type"]
            idx       = _focus_state["idx"]
            has_clear = btn_clear_all.winfo_ismapped()

            if key == "Return":
                if t == "delete" and idx < n: _del_buttons[idx][1]()
                elif t == "ok":               _on_close()
                elif t == "clear":            _clear_all()
                return "break"
            elif key == "Down":
                if t == "delete" and idx + 1 < n:      _set_focus("delete", idx + 1)
                elif t in ("ok", "clear") and n > 0:   _set_focus("delete", 0)
                return "break"
            elif key == "Up":
                if t == "delete" and idx - 1 >= 0:     _set_focus("delete", idx - 1)
                elif t in ("ok", "clear") and n > 0:   _set_focus("delete", n - 1)
                return "break"
            elif key == "Right":
                if t == "delete":                       _set_focus("clear" if has_clear else "ok")
                elif t == "clear":                      _set_focus("ok")
                elif t == "ok" and has_clear:           _set_focus("clear")
                return "break"
            elif key == "Left":
                if t == "ok" and has_clear:             _set_focus("clear")
                elif t == "clear":                      _set_focus("ok")
                elif t == "delete":                     _set_focus("clear" if has_clear else "ok")
                return "break"
            elif key in ("Escape", "BackSpace"):
                _on_close()
                return "break"

        _rebuild()
        win.bind("<Key>", _on_key)

        # --- Geometry (identical to show_help) ---
        win.update()

        dpi_scale = 1.0
        if sys.platform == "win32":
            try:
                from ctypes import windll
                hwnd = windll.user32.GetParent(win.winfo_id())
                dpi  = windll.user32.GetDpiForWindow(hwnd)
                if dpi > 0:
                    dpi_scale = dpi / 96.0
            except Exception:
                pass
        else:
            try:
                dpi_scale = ctk.ScalingTracker.get_widget_scaling(win)
            except Exception:
                pass

        TARGET_W_LOGICAL  = 560
        n                 = max(1, len(get_items()))
        TARGET_H_LOGICAL  = max(280, min(440, 160 + n * 32))
        final_w           = int(TARGET_W_LOGICAL * dpi_scale)
        final_h           = int(TARGET_H_LOGICAL * dpi_scale)
        pos_x             = self.root.winfo_x() + (self.root.winfo_width()  // 2) - (final_w // 2)
        pos_y             = self.root.winfo_y() + (self.root.winfo_height() // 2) - (final_h // 2)
        win.wm_geometry(f"{final_w}x{final_h}+{max(0, pos_x)}+{max(0, pos_y)}")

        def _finalize():
            try:
                win.lift()
                win.attributes("-topmost", True)
                win.after(150, lambda: win.attributes("-topmost", False))
                win.focus_force()
                win.grab_set()
                list_canvas.yview_moveto(0)
            except Exception:
                pass

        win.after(150, _finalize)

    def load_exclude_patterns(self):
        """
        Loads exclusion patterns from EXCLUDE_LIST_FILE into self.exclude_patterns.
        Patterns are stored lowercase for case-insensitive matching.
        Safe to call at startup or whenever the file is modified.
        """
        patterns = []
        try:
            if os.path.exists(EXCLUDE_LIST_FILE):
                with open(EXCLUDE_LIST_FILE, "r", encoding="utf-8") as f:
                    for line in f:
                        p = line.strip()
                        if p:
                            patterns.append(p.lower())
        except Exception as e:
            print(f"[EXCLUDE] Failed to load {EXCLUDE_LIST_FILE}: {e}")
        self.exclude_patterns = patterns[:EXCLUDE_LIST_MAX_SIZE]
        self.update_exclude_button()

    def save_exclude_patterns(self, patterns):
        """
        Persists the exclusion list to EXCLUDE_LIST_FILE (one entry per line).
        Updates self.exclude_patterns in memory immediately.
        """
        try:
            with open(EXCLUDE_LIST_FILE, "w", encoding="utf-8") as f:
                for p in patterns:
                    f.write(p + "\n")
            self.exclude_patterns = [p.lower() for p in patterns]
        except Exception as e:
            print(f"[EXCLUDE] Failed to save {EXCLUDE_LIST_FILE}: {e}")

    def exclude_selection(self):
        """
        Adds the current text selection to the exclusion list after confirmation.
        Shows a themed CTkToplevel dialog; refreshes the display on confirm.
        """
        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])

        # --- Retrieve and validate selection ---
        try:
            selected = self.txt_area.get(tk.SEL_FIRST, tk.SEL_LAST).strip()
        except tk.TclError:
            return
        if not selected:
            return

        # Truncate display label if the selection is very long
        display_label = selected if len(selected) <= 60 else selected[:57] + "..."

        # --- Guard: already in list ---
        if selected.lower() in self.exclude_patterns:
            self._show_info_dialog(
                l_ui.get("exclude_confirm_title", "Exclude"),
                l_ui.get("exclude_already", "This term is already in the exclusion list."),
            )
            return

        # --- Guard: list full ---
        current_patterns = list(self.exclude_patterns)
        if len(current_patterns) >= EXCLUDE_LIST_MAX_SIZE:
            self._show_info_dialog(
                l_ui.get("exclude_max_title", "Limit reached"),
                l_ui.get("exclude_max_msg", "The list is limited to {} entries.").format(EXCLUDE_LIST_MAX_SIZE),
            )
            return

        # --- Confirmation dialog ---
        confirmed = [False]

        dlg = ctk.CTkToplevel(self.root)
        dlg.title(l_ui.get("exclude_confirm_title", "Confirm exclusion"))
        dlg.configure(fg_color=COLOR_BG_DIALOG)
        dlg.transient(self.root)
        dlg.resizable(False, False)

        # Message: split template at {} so the excluded string renders in mono font
        msg_template = l_ui.get("exclude_confirm_msg", "Exclude all messages containing:\n\n\"{}\"")
        msg_intro = msg_template.split("{}")[0].rstrip('\n "')

        ctk.CTkLabel(
            dlg,
            text=msg_intro,
            font=(self._main_font, 13),
            text_color=COLOR_TEXT_MAIN,
            wraplength=380,
            justify="center",
        ).pack(padx=24, pady=(20, 8))

        ctk.CTkLabel(
            dlg,
            text=display_label,
            font=(self._mono_font, 15),
            text_color=COLOR_TEXT_MAIN,
            wraplength=380,
            justify="center",
        ).pack(padx=24, pady=(0, 20))

        # Buttons
        btn_frame = tk.Frame(dlg, bg=COLOR_BG_DIALOG)
        btn_frame.pack(padx=24, pady=(0, self.sc(48)))

        def _confirm():
            confirmed[0] = True
            dlg.destroy()

        def _cancel():
            dlg.destroy()

        btn_yes = ctk.CTkButton(
            btn_frame,
            text=l_ui.get("yes", "Yes"),
            width=90,
            fg_color=COLOR_BTN_DEFAULT,
            hover_color=COLOR_BTN_ACTIVE,
            text_color=COLOR_TEXT_BRIGHT,
            font=(self._main_font, 13),
            command=_confirm,
        )
        btn_yes.pack(side="left", padx=(0, 10))

        btn_no = ctk.CTkButton(
            btn_frame,
            text=l_ui.get("no", "No"),
            width=90,
            fg_color=COLOR_BTN_DEFAULT,
            hover_color=COLOR_BTN_ACTIVE,
            text_color=COLOR_TEXT_BRIGHT,
            font=(self._main_font, 13),
            command=_cancel,
        )
        btn_no.pack(side="left")

        # Keyboard navigation: track which button has keyboard focus
        _focused = ["no"]

        def _set_focus(which):
            """Highlight the keyboard-focused button; dim the other."""
            _focused[0] = which
            if which == "no":
                btn_no.configure(fg_color=COLOR_BTN_ACTIVE)
                btn_yes.configure(fg_color=COLOR_BTN_DEFAULT)
            else:
                btn_yes.configure(fg_color=COLOR_BTN_ACTIVE)
                btn_no.configure(fg_color=COLOR_BTN_DEFAULT)

        def _activate(e=None):
            """Trigger the currently focused button."""
            if _focused[0] == "yes":
                _confirm()
            else:
                _cancel()

        dlg.bind("<Left>",    lambda e: _set_focus("yes" if _focused[0] == "no" else "no"))
        dlg.bind("<Right>",   lambda e: _set_focus("yes" if _focused[0] == "no" else "no"))
        dlg.bind("<Return>",  _activate)
        dlg.bind("<KP_Enter>", _activate)
        dlg.bind("<Escape>",  lambda e: _cancel())

        # Default keyboard focus on No
        _set_focus("no")

        # Center over the main window (DPI-aware, identical to show_help)
        self._center_dialog(dlg, 460)

        dlg.lift()
        dlg.attributes("-topmost", True)
        dlg.after(150, lambda: dlg.attributes("-topmost", False))
        dlg.grab_set()
        self.root.wait_window(dlg)

        if not confirmed[0]:
            return

        # Defer the entire post-confirm logic so the event queue is fully flushed
        # before we touch txt_area. CTkButton fires its command on <ButtonRelease-1>;
        # when the dialog is destroyed and the grab released, a residual release event
        # can reach txt_area if the cursor overlaps the log area, causing a spurious
        # selection. The after() delay lets those events drain first.
        def _apply():
            try:
                self.txt_area.tag_remove(tk.SEL, "1.0", tk.END)
            except tk.TclError:
                pass
            # --- Append, save, refresh ---
            # Preserve original case in file; matching is always done lowercase
            current_patterns.append(selected)
            self.save_exclude_patterns(current_patterns)
            self.update_exclude_button()
            self.trigger_refresh()

        self.root.after(50, _apply)

    def show_summary(self):
        """Displays the system summary and pauses the log scrolling."""
        if not self.check_log_loaded():
            return
        if not self.check_log_available():
            return
        if not self.log_file_path or not os.path.exists(self.log_file_path):
            return

        self.is_paused.set(True)
        self._summary_showing = True
        self.update_button_colors()
        self.update_stats()

        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])
        summary_content = []
        found_header = False

        self.txt_area.tag_configure("summary_color", foreground=LOG_COLORS["summary"])

        try:
            with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if "info <general>: --------" in line:
                        if not found_header:
                            found_header = True
                            summary_content.append(line)
                            continue
                        else:
                            summary_content.append(line)
                            break
                    if found_header:
                        summary_content.append(line)
                    if len(summary_content) > 100:
                        break

            if summary_content:
                self.txt_area.config(state=tk.NORMAL)
                self.txt_area.delete('1.0', tk.END)

                header_title = l_ui.get("sys_sum", "\n--- SYSTEM SUMMARY ---\n")
                self.txt_area.insert(tk.END, f"{header_title}\n", "summary_color")
                for s_line in summary_content:
                    self.txt_area.insert(tk.END, s_line, "summary_color")

                self.txt_area.config(state=tk.DISABLED)
                self.txt_area.see("1.0")

        except Exception as e:
            print(f"Summary error: {e}")

    def show_help(self):
        """
        Displays the help window with keyboard shortcuts.
        Uses CTkToplevel and auto-sizes to content using a full render pass.
        """
        # Prevent double opening
        if hasattr(self, "help_win_active") and self.help_win_active:
            return
        self.help_win_active = True

        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])

        help_win = ctk.CTkToplevel(self.root)
        help_win.title(l_ui.get("win_help_title", "Help"))
        help_win.configure(fg_color=COLOR_BG_DIALOG)
        help_win.transient(self.root)
        help_win.withdraw()

        def safe_close(event=None):
            try:
                help_win.grab_release()
                help_win.destroy()
            except Exception:
                pass
            self.root.after(200, lambda: setattr(self, "help_win_active", False))

        help_win.protocol("WM_DELETE_WINDOW", safe_close)
        for key in ["<Return>", "<Escape>", "<BackSpace>", "<F1>"]:
            help_win.bind(key, safe_close)

        # --- Content frame (no canvas/scrollbar needed for a short static list) ---
        content = ctk.CTkFrame(help_win, fg_color=COLOR_BG_DIALOG, corner_radius=0)
        content.pack(fill="both", expand=True, padx=0, pady=0)

        tk.Label(
            content,
            text=l_ui.get("help_title", "Keyboard Shortcuts"),
            bg=COLOR_BG_DIALOG,
            fg=COLOR_ACCENT,
            font=(self._main_font, 14, "bold"),
        ).pack(pady=(20, 10), fill="x")

        tk.Frame(content, bg=COLOR_SEPARATOR, height=2).pack(fill="x", padx=40)

        raw_text = l_ui.get("help_text", "")
        formatted_lines = []
        for line in raw_text.split('\n'):
            if " : " in line:
                cmd, desc = line.split(" : ", 1)
                formatted_lines.append(f"{cmd:<12} : {desc}")
            else:
                formatted_lines.append(line)

        tk.Label(
            content,
            text="\n".join(formatted_lines).strip(),
            bg=COLOR_BG_DIALOG,
            fg=COLOR_TEXT_MAIN,
            justify="left",
            font=(self._mono_font, 11),
            padx=40,
        ).pack(fill="x", pady=(20, 10))

        # OK button
        ctk.CTkButton(
            content,
            text="Ok",
            command=safe_close,
            fg_color=COLOR_BTN_DEFAULT,
            hover_color=COLOR_BTN_ACTIVE,
            text_color=COLOR_TEXT_MAIN,
            font=ctk.CTkFont(family=self._main_font, size=12, weight="bold"),
            corner_radius=5,
            border_width=0,
            width=120,
            height=32,
        ).pack(pady=20)

        # --- Sizing: DPI-aware fixed logical size ---
        help_win.update()

        # Detect the true DPI scaling factor so the dialog has a consistent
        # LOGICAL size regardless of whether the screen is FHD, QHD or 4K.
        dpi_scale = 1.0
        if sys.platform == "win32":
            try:
                from ctypes import windll
                hwnd = windll.user32.GetParent(help_win.winfo_id())
                dpi = windll.user32.GetDpiForWindow(hwnd)
                if dpi > 0:
                    dpi_scale = dpi / 96.0
            except Exception:
                pass
        else:
            # On Linux/macOS fall back to CTK's own scaling tracker
            try:
                dpi_scale = ctk.ScalingTracker.get_widget_scaling(help_win)
            except Exception:
                pass

        # FIXED SETTINGS
        TARGET_W_LOGICAL = 510
        MAX_H_LOGICAL = 470

        req_h = help_win.winfo_reqheight()

        # Convert logical dimensions to physical pixels for the geometry call
        final_w = int(TARGET_W_LOGICAL * dpi_scale)
        max_h_phys = int(MAX_H_LOGICAL * dpi_scale)

        final_h = min(req_h, max_h_phys)

        # Calculate coordinates to center the window relative to the root window
        pos_x = self.root.winfo_x() + (self.root.winfo_width()  // 2) - (final_w // 2)
        pos_y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (final_h // 2)

        # Use wm_geometry to bypass CustomTkinter's auto-scaling
        help_win.wm_geometry(f"{final_w}x{final_h}+{max(0, pos_x)}+{max(0, pos_y)}")

        # Apply title bar color matching the current app theme
        if sys.platform == "win32":
            try:
                from ctypes import windll, byref, sizeof, c_int
                hwnd = windll.user32.GetParent(help_win.winfo_id())
                is_dark = 1 if APP_THEME == "dark" else 0
                caption_color = c_int(0x002d2d2d) if APP_THEME == "dark" else c_int(0x00f0f0f0)
                windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, byref(c_int(is_dark)), sizeof(c_int(is_dark)))
                windll.dwmapi.DwmSetWindowAttribute(hwnd, 34, byref(caption_color), sizeof(caption_color))
            except Exception:
                pass

        help_win.deiconify()
        help_win.grab_set()
        help_win.focus_force()

    def check_for_updates(self):
        """Check for updates with free offline mode support."""
        if not self.updates_enabled:
            return

        def _check():
            url = GITHUB_API_URL
            try:
                import urllib.request, json
                from urllib.error import URLError

                req = urllib.request.Request(url, headers={'User-Agent': 'KodiLogMonitor-App'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode())

                    latest_v_str = data.get("tag_name", "")

                    if latest_v_str:
                        current_v_tuple = parse_version(APP_VERSION)
                        latest_v_tuple = parse_version(latest_v_str)

                        if latest_v_tuple > current_v_tuple and latest_v_str != self.skip_version:
                            # A version newer than the skipped one is available:
                            # the skip entry is now stale - clear it silently so
                            # the 🔕 indicator disappears without user action.
                            if self.skip_version:
                                self.skip_version = ""
                                self.save_session()
                                self.root.after(0, self.update_notify_indicator)
                            self.root.after(0, lambda: self._show_update_dialog(
                                latest_v_str,
                                data.get("html_url")
                            ))

            except Exception as e:
                print(f"Update check skipped (reason: {e})")

        threading.Thread(target=_check, daemon=True).start()

    def _show_update_dialog(self, new_version, url):
        """
        Displays the update notification dialog.
        Uses CTkToplevel for consistent dark theming.
        Uses DPI-aware fixed width of 470px to avoid 4K double scaling issues.
        """
        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])

        upd_win = ctk.CTkToplevel(self.root)
        upd_win.title(l_ui.get("upd_title", "Update Available"))
        upd_win.configure(fg_color=COLOR_BG_DIALOG)
        upd_win.transient(self.root)
        upd_win.withdraw()

        def safe_close(event=None):
            try:
                upd_win.grab_release()
                upd_win.destroy()
            except Exception:
                pass

        upd_win.protocol("WM_DELETE_WINDOW", safe_close)
        for key in ["<Return>", "<Escape>", "<BackSpace>"]:
            upd_win.bind(key, safe_close)

        # --- Main content frame ---
        main_frame = ctk.CTkFrame(
            upd_win, fg_color=COLOR_BG_DIALOG, corner_radius=0
        )
        main_frame.pack(fill="both", expand=True, padx=self.sc(40), pady=20)

        tk.Label(
            main_frame,
            text=f"{l_ui.get('upd_new_ver', 'NEW VERSION:')} {new_version}",
            bg=COLOR_BG_DIALOG,
            fg=COLOR_ACCENT,
            font=(self._main_font, 14, "bold"),
        ).pack(pady=(0, 15), fill="x")

        tk.Frame(main_frame, bg=COLOR_SEPARATOR, height=2).pack(fill="x")

        tk.Label(
            main_frame,
            text=l_ui.get("upd_msg", ""),
            bg=COLOR_BG_DIALOG,
            fg=COLOR_TEXT_MAIN,
            font=(self._main_font, 11),
            justify="center",
        ).pack(fill="both", expand=True, pady=(10, 20))

        # --- Button area (centered) ---
        outer_btn_frame = ctk.CTkFrame(upd_win, fg_color=COLOR_BG_DIALOG, corner_radius=0)
        outer_btn_frame.pack(side="bottom", fill="x", pady=(0, self.sc(25)))

        inner_btn_frame = ctk.CTkFrame(outer_btn_frame, fg_color=COLOR_BG_DIALOG, corner_radius=0)
        inner_btn_frame.pack()

        def on_open():
            self.open_url(url)
            safe_close()

        def on_skip():
            self.skip_version = new_version
            self.save_session()
            self.update_notify_indicator()
            safe_close()

        def on_disable():
            upd_title = l_ui.get("upd_confirm_title", "Confirm")
            upd_msg   = l_ui.get("upd_confirm_msg",   "Disable update notifications permanently?")

            dis_confirmed = [False]

            dis_dlg = ctk.CTkToplevel(self.root)
            dis_dlg.title(upd_title)
            dis_dlg.configure(fg_color=COLOR_BG_DIALOG)
            dis_dlg.transient(self.root)
            dis_dlg.resizable(False, False)

            ctk.CTkLabel(
                dis_dlg,
                text=upd_msg,
                font=(self._main_font, 13),
                text_color=COLOR_TEXT_MAIN,
                wraplength=340,
                justify="center",
            ).pack(padx=24, pady=(24, 20))

            dis_btn_frame = tk.Frame(dis_dlg, bg=COLOR_BG_DIALOG)
            dis_btn_frame.pack(padx=24, pady=(0, self.sc(48)))

            def _dis_confirm():
                dis_confirmed[0] = True
                dis_dlg.destroy()

            def _dis_cancel():
                dis_dlg.destroy()

            dis_btn_yes = ctk.CTkButton(
                dis_btn_frame,
                text=l_ui.get("yes", "Yes"),
                width=90,
                fg_color=COLOR_BTN_DEFAULT,
                hover_color=COLOR_BTN_ACTIVE,
                text_color=COLOR_TEXT_BRIGHT,
                font=(self._main_font, 13),
                command=_dis_confirm,
            )
            dis_btn_yes.pack(side="left", padx=(0, 10))

            dis_btn_no = ctk.CTkButton(
                dis_btn_frame,
                text=l_ui.get("no", "No"),
                width=90,
                fg_color=COLOR_BTN_DEFAULT,
                hover_color=COLOR_BTN_ACTIVE,
                text_color=COLOR_TEXT_BRIGHT,
                font=(self._main_font, 13),
                command=_dis_cancel,
            )
            dis_btn_no.pack(side="left")

            _dis_focused = ["no"]

            def _dis_set_focus(which):
                _dis_focused[0] = which
                if which == "no":
                    dis_btn_no.configure(fg_color=COLOR_BTN_ACTIVE)
                    dis_btn_yes.configure(fg_color=COLOR_BTN_DEFAULT)
                else:
                    dis_btn_yes.configure(fg_color=COLOR_BTN_ACTIVE)
                    dis_btn_no.configure(fg_color=COLOR_BTN_DEFAULT)

            def _dis_activate(e=None):
                if _dis_focused[0] == "yes":
                    _dis_confirm()
                else:
                    _dis_cancel()

            dis_dlg.bind("<Left>",     lambda e: _dis_set_focus("yes" if _dis_focused[0] == "no" else "no"))
            dis_dlg.bind("<Right>",    lambda e: _dis_set_focus("yes" if _dis_focused[0] == "no" else "no"))
            dis_dlg.bind("<Return>",   _dis_activate)
            dis_dlg.bind("<KP_Enter>", _dis_activate)
            dis_dlg.bind("<Escape>",   lambda e: _dis_cancel())

            _dis_set_focus("no")

            self._center_dialog(dis_dlg, 400)

            dis_dlg.lift()
            dis_dlg.attributes("-topmost", True)
            dis_dlg.after(150, lambda: dis_dlg.attributes("-topmost", False))
            dis_dlg.grab_set()
            self.root.wait_window(dis_dlg)

            if dis_confirmed[0]:
                self.updates_enabled = False
                self.save_session()
                self.update_notify_indicator()
                safe_close()

        btn_style = dict(
            fg_color=COLOR_BTN_DEFAULT,
            hover_color=COLOR_BTN_ACTIVE,
            text_color=COLOR_TEXT_MAIN,
            font=ctk.CTkFont(family=self._main_font, size=12, weight="bold"),
            corner_radius=5,
            border_width=0,
            width=120,
            height=32,
        )

        btn_dl = ctk.CTkButton(
            inner_btn_frame,
            text=l_ui.get("upd_btn_dl", "DOWNLOAD"),
            command=on_open,
            **btn_style
        )
        btn_dl.pack(side="left", padx=self.sc(5))
        ToolTip(btn_dl, l_ui.get("tip_upd_dl", "Download from GitHub"), self.scale)

        btn_skip = ctk.CTkButton(
            inner_btn_frame,
            text=l_ui.get("upd_btn_skip", "SKIP"),
            command=on_skip,
            **btn_style
        )
        btn_skip.pack(side="left", padx=self.sc(5))
        ToolTip(btn_skip, l_ui.get("tip_upd_sk", "Ignore this version"), self.scale)

        btn_disable = ctk.CTkButton(
            inner_btn_frame,
            text=l_ui.get("upd_btn_dis", "DISABLE"),
            command=on_disable,
            **btn_style
        )
        btn_disable.pack(side="left", padx=self.sc(5))
        ToolTip(btn_disable, l_ui.get("tip_upd_di", "Permanently disable notifications"), self.scale)

        # --- Sizing: DPI-aware fixed logical size ---
        upd_win.update_idletasks()

        # Detect the true DPI scaling factor so the dialog has a consistent
        # LOGICAL size regardless of whether the screen is FHD, QHD or 4K.
        dpi_scale = 1.0
        if sys.platform == "win32":
            try:
                from ctypes import windll
                hwnd = windll.user32.GetParent(upd_win.winfo_id())
                dpi = windll.user32.GetDpiForWindow(hwnd)
                if dpi > 0:
                    dpi_scale = dpi / 96.0
            except Exception:
                pass
        else:
            # On Linux/macOS fall back to CTK's own scaling tracker
            try:
                dpi_scale = ctk.ScalingTracker.get_widget_scaling(upd_win)
            except Exception:
                pass

        # FIXED SETTINGS: 470px width and max height of 300px
        TARGET_W_LOGICAL = 470
        MAX_H_LOGICAL = 300

        req_h = upd_win.winfo_reqheight()

        # Convert logical dimensions to physical pixels for the geometry call
        final_w = int(TARGET_W_LOGICAL * dpi_scale)
        max_h_phys = int(MAX_H_LOGICAL * dpi_scale)

        # Retain original +10 pixels height padding but scaled properly
        final_h = min(req_h + int(10 * dpi_scale), max_h_phys)

        # Calculate coordinates to center the window relative to the root window
        pos_x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (final_w // 2)
        pos_y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (final_h // 2)

        # Use wm_geometry to bypass CustomTkinter's auto-scaling
        upd_win.wm_geometry(f"{final_w}x{final_h}+{max(0, pos_x)}+{max(0, pos_y)}")

        # Apply title bar color matching the current app theme
        if sys.platform == "win32":
            try:
                from ctypes import windll, byref, sizeof, c_int
                hwnd = windll.user32.GetParent(upd_win.winfo_id())
                is_dark = 1 if APP_THEME == "dark" else 0
                caption_color = c_int(0x002d2d2d) if APP_THEME == "dark" else c_int(0x00f0f0f0)
                windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, byref(c_int(is_dark)), sizeof(c_int(is_dark)))
                windll.dwmapi.DwmSetWindowAttribute(hwnd, 34, byref(caption_color), sizeof(caption_color))
            except Exception:
                pass

        upd_win.deiconify()
        upd_win.grab_set()
        upd_win.focus_force()

    # ------------------------------------------------------------------
    # Update-notifications muted indicator (🔕 in footer)
    # ------------------------------------------------------------------

    def update_notify_indicator(self):
        """
        Shows or hides the 🔕 muted indicator in the footer.
        Visible when updates are permanently disabled OR a specific version
        has been skipped (i.e. any deviation from the default state).
        Also refreshes the tooltip text to reflect the current reason.
        """
        l_ui    = LANGS.get(self.current_lang.get(), LANGS["EN"])
        is_perm = not self.updates_enabled
        is_skip = bool(self.skip_version)
        is_muted = is_perm or is_skip

        if is_muted:
            if is_perm:
                tip = l_ui.get(
                    "tip_notify_disabled",
                    "Update notifications disabled - click to restore",
                )
            else:
                tip = l_ui.get(
                    "tip_notify_skipped",
                    "Version {version} skipped - click to restore",
                ).format(version=self.skip_version)
            self.notify_muted_tooltip.text = tip

            # Insert icon and separator to the RIGHT of the version label.
            # `before=github_label` places each widget earlier in the pack list,
            # which with side=tk.RIGHT means further to the right visually.
            # Pack order in list: [lbl_notify_muted, sep_notify_muted, github_label]
            # Visual result (left→right): [version | sep | 🔕]
            self.lbl_notify_muted.pack(
                side=tk.RIGHT, padx=(6, 6), before=self.github_label
            )
            self.sep_notify_muted.pack(
                side=tk.RIGHT, fill=tk.Y, padx=(5, 0), pady=2,
                before=self.github_label
            )
        else:
            self.lbl_notify_muted.pack_forget()
            self.sep_notify_muted.pack_forget()

    def _reset_update_notifications_dialog(self, event=None):
        """
        Asks the user to confirm resetting update notification options to
        their defaults (updates_enabled=True, skip_version="").
        Opens a simple Yes / No confirmation dialog - same pattern as the
        existing disable-confirmation dialog.
        """
        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])

        confirmed = [False]

        dlg = ctk.CTkToplevel(self.root)
        dlg.title(l_ui.get("notify_reset_title", "Update notifications"))
        dlg.configure(fg_color=COLOR_BG_DIALOG)
        dlg.transient(self.root)
        dlg.resizable(False, False)

        ctk.CTkLabel(
            dlg,
            text=l_ui.get("notify_reset_msg", "Restore default update notification settings?"),
            font=(self._main_font, 13),
            text_color=COLOR_TEXT_MAIN,
            wraplength=320,
            justify="center",
        ).pack(padx=24, pady=(24, 20))

        btn_frame = tk.Frame(dlg, bg=COLOR_BG_DIALOG)
        btn_frame.pack(padx=24, pady=(0, self.sc(48)))

        def _confirm():
            confirmed[0] = True
            dlg.destroy()

        def _cancel():
            dlg.destroy()

        _focused = ["no"]

        def _set_focus(which):
            _focused[0] = which
            btn_yes.configure(fg_color=COLOR_BTN_ACTIVE  if which == "yes" else COLOR_BTN_DEFAULT)
            btn_no.configure( fg_color=COLOR_BTN_ACTIVE  if which == "no"  else COLOR_BTN_DEFAULT)

        def _activate(e=None):
            (_confirm if _focused[0] == "yes" else _cancel)()

        btn_yes = ctk.CTkButton(
            btn_frame,
            text=l_ui.get("yes", "Yes"),
            width=90,
            fg_color=COLOR_BTN_DEFAULT,
            hover_color=COLOR_BTN_ACTIVE,
            text_color=COLOR_TEXT_BRIGHT,
            font=(self._main_font, 13),
            command=_confirm,
        )
        btn_yes.pack(side="left", padx=(0, 10))

        btn_no = ctk.CTkButton(
            btn_frame,
            text=l_ui.get("no", "No"),
            width=90,
            fg_color=COLOR_BTN_DEFAULT,
            hover_color=COLOR_BTN_ACTIVE,
            text_color=COLOR_TEXT_BRIGHT,
            font=(self._main_font, 13),
            command=_cancel,
        )
        btn_no.pack(side="left")

        dlg.bind("<Left>",     lambda e: _set_focus("yes" if _focused[0] == "no" else "no"))
        dlg.bind("<Right>",    lambda e: _set_focus("yes" if _focused[0] == "no" else "no"))
        dlg.bind("<Return>",   _activate)
        dlg.bind("<KP_Enter>", _activate)
        dlg.bind("<Escape>",   lambda e: _cancel())

        _set_focus("no")
        self._center_dialog(dlg, 380)
        dlg.lift()
        dlg.attributes("-topmost", True)
        dlg.after(150, lambda: dlg.attributes("-topmost", False))
        dlg.grab_set()
        self.root.wait_window(dlg)

        if confirmed[0]:
            self.updates_enabled = True
            self.skip_version    = ""
            self.save_session()
            self.update_notify_indicator()

    def check_log_loaded(self):
        """Check if a log file is loaded; show a message if not."""
        if not self.log_file_path:
            self.txt_area.config(state=tk.NORMAL)
            self.txt_area.delete('1.0', tk.END)

            l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])
            self.txt_area.tag_configure(
                "no_log_text",
                foreground=LOG_COLORS["error"],
                font=(self.mono_font_family, self.font_size, "bold")
            )
            self.txt_area.insert(tk.END, "\n\n\n\n\t\t")
            self.txt_area.insert(tk.END, l_ui.get('no_log', 'No LOG file loaded.'), "no_log_text")
            self.txt_area.config(state=tk.DISABLED)
            return False
        return True

    def check_log_available(self):
        """
        Checks if the log file is physically accessible.
        Clears error messages if the file returns to normal.
        """
        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])
        err_msg = l_ui.get('file_error', '⚠️ LOG INACCESSIBLE')

        if self.log_file_path:
            if not os.path.exists(self.log_file_path):
                self.txt_area.config(state=tk.NORMAL)
                self.txt_area.delete('1.0', tk.END)
                self.txt_area.tag_configure(
                    "file_err_text",
                    foreground=LOG_COLORS["error"],
                    font=(self.mono_font_family, self.font_size, "bold")
                )
                self.txt_area.insert(tk.END, "\n\n\n\n\t\t")
                self.txt_area.insert(tk.END, err_msg, "file_err_text")
                self.txt_area.config(state=tk.DISABLED)

                self.inactivity_timer_var.set(err_msg)
                self.update_status_color(COLOR_DANGER)
                return False
            else:
                if self.inactivity_timer_var.get() == err_msg:
                    self.inactivity_timer_var.set("")
                    self.update_status_color(COLOR_ACCENT)

        return True

    def on_list_change(self, *args):
        """Triggered when the keyword list selection changes."""
        # Invalidate the keyword cache so get_keywords_from_file() re-reads from disk
        self._kw_cache = None
        self._kw_cache_key = None
        if not self.check_log_loaded():
            return
        if not self.check_log_available():
            return
        self.trigger_refresh()

    def clear_console(self):
        self.txt_area.config(state=tk.NORMAL)
        self.txt_area.delete("1.0", tk.END)
        self.update_stats()

    def toggle_line_break(self, *args):
        """
        Toggles word-wrap mode and refreshes the log display.

        If the log area has keyboard focus and the cursor is on a non-empty line,
        monitoring is paused, the view centres on that line after the refresh,
        and the line is highlighted briefly so the user can locate it immediately.
        Otherwise the current scroll position is simply restored.
        """
        new_mode = tk.WORD if self.wrap_mode.get() else tk.NONE
        self.txt_area.config(wrap=new_mode)

        # Immediately sync button color and tooltip to new state
        self.update_button_colors()

        if not self.check_log_loaded() or not self.check_log_available():
            return

        # --- Detect the target line, by priority ---

        cursor_line_content = ""
        cursor_idx = None

        # Priority 1: explicit double-click anchor (set by on_double_click_line).
        # After reset_all_filters the INSERT cursor lands at "1.0" which would
        # silently win over _last_wrap_content if checked first - so we check
        # _last_wrap_content first and skip the live-cursor read entirely.
        if getattr(self, "_last_wrap_content", None):
            cursor_line_content = self._last_wrap_content
            cursor_idx = "1.0"  # dummy - _focus_line uses content search, not this index

        else:
            # Priority 2: live INSERT cursor (keyboard navigation / manual click)
            try:
                if self.root.focus_get() == self.txt_area:
                    cursor_idx = self.txt_area.index(tk.INSERT)
                    cursor_line_content = self.txt_area.get(
                        cursor_idx + " linestart", cursor_idx + " lineend"
                    ).strip()
            except tk.TclError:
                pass

            # Priority 3: remembered index anchor from the previous toggle
            if not (cursor_idx and cursor_line_content) and getattr(self, "_last_wrap_anchor", None):
                try:
                    cursor_idx = self._last_wrap_anchor
                    cursor_line_content = self.txt_area.get(
                        cursor_idx + " linestart", cursor_idx + " lineend"
                    ).strip()
                except tk.TclError:
                    cursor_idx = None
                    cursor_line_content = ""

        if cursor_idx and cursor_line_content:
            # Remember this anchor for the next toggle
            self._last_wrap_anchor = cursor_idx

            # Pause before refresh so bulk_insert does not scroll to END
            self.is_paused.set(True)
            if hasattr(self, "update_button_colors"):
                self.update_button_colors()

            # When type filters are active, refresh_natural_order ignores them and
            # rebuilds with all lines, making cursor_idx point to the wrong line.
            # Use refresh_display_with_sorting instead to keep the filtered view.
            has_type_filter = not self.filter_vars.get("all", tk.BooleanVar(value=True)).get()
            if has_type_filter:
                self.txt_area.config(state=tk.NORMAL)
                self.txt_area.delete("1.0", tk.END)
                self.refresh_display_with_sorting()
            else:
                self.refresh_natural_order()

            # Pre-scroll to END while still in synchronous context so the first
            # rendered frame shows the bottom of the log instead of the top.
            # _focus_line will fine-tune to the exact anchor line afterwards.
            self.txt_area.see(tk.END)

            # After any rebuild the widget indices are reassigned: find the line
            # by its text content rather than the pre-rebuild cursor_idx.
            search_text = cursor_line_content

            def _focus_line():
                try:
                    # Prefer timestamp-based search (millisecond precision → near-unique)
                    # then validate the full line content, exactly like
                    # find_and_highlight_timestamp does.  Fall back to plain content
                    # search for lines that carry no timestamp.
                    ts_match = re.search(
                        r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}", search_text
                    )
                    pos = None
                    if ts_match:
                        ts = ts_match.group(0)
                        scan = "1.0"
                        while True:
                            idx = self.txt_area.search(ts, scan, stopindex=tk.END, exact=True)
                            if not idx:
                                break
                            line_txt = self.txt_area.get(
                                idx + " linestart", idx + " lineend"
                            ).strip()
                            if search_text in line_txt:
                                pos = idx
                                break
                            scan = self.txt_area.index(idx + " lineend")
                    if pos is None:
                        pos = self.txt_area.search(
                            search_text, "1.0", stopindex=tk.END, exact=True
                        )
                    if not pos:
                        return
                    line_start = self.txt_area.index(pos + " linestart")
                    line_end   = self.txt_area.index(pos + " lineend")
                    # Keep _last_wrap_anchor valid for the next toggle
                    self._last_wrap_anchor = line_start
                    self.txt_area.see(line_start)
                    self.txt_area.xview_moveto(0)
                    self.txt_area.tag_remove("highlight_temp", "1.0", tk.END)
                    self.txt_area.tag_add("highlight_temp", line_start, line_end)
                    self.txt_area.tag_config(
                        "highlight_temp",
                        background=LOG_COLORS["highlight_kwl_bg"],
                        foreground=LOG_COLORS["highlight_kwl_fg"],
                        font=(self.mono_font_family, self.font_size),
                    )
                    self.root.after(
                        3000, lambda: self.txt_area.tag_remove("highlight_temp", "1.0", tk.END)
                    )
                except tk.TclError:
                    pass

            self.root.after(0, _focus_line)

        else:
            # No focused line and no remembered anchor: use the ~10th visible line as
            # anchor so repeated toggles stay in the same area (more stable than @0,0)
            first_line = int(self.txt_area.index("@0,0").split(".")[0])
            total_lines = int(self.txt_area.index(tk.END).split(".")[0])
            anchor_line = min(first_line + 9, total_lines)
            anchor = f"{anchor_line}.0"
            self._last_wrap_anchor = anchor
            self.refresh_natural_order()
            self.root.after(0, lambda: self.txt_area.see(anchor))

    def toggle_full_load(self):
        """
        Toggles between loading the full log file and loading only the last 1000 lines.
        The confirmation dialog (for large files) is shown BEFORE any state or color change,
        so the button only updates after the user's decision.
        """
        if not self.check_log_loaded() or not self.check_log_available():
            return

        # Compute what the new value would be after toggling
        new_value = not self.load_full_file.get()

        # 1. Security check: warn before switching to unlimited on a large file
        if new_value and self.log_file_path and os.path.exists(self.log_file_path):
            file_size_mb = os.path.getsize(self.log_file_path) / (1024 * 1024)
            if file_size_mb > DEFAULT_SECURITY_FILE_MAX_SIZE_BUTTON:
                l = LANGS.get(self.current_lang.get(), LANGS["EN"])
                title = l.get("perf_confirm_title", "Performance Warning")
                default_msg = (
                    "This file is larger than 10 MB ({:.1f} MB).\n"
                    "Loading it completely may cause performance issues or freezes.\n\n"
                    "Do you want to proceed?"
                )
                msg = l.get("perf_confirm_msg", default_msg).format(file_size_mb)

                confirmed = [False]

                dlg = ctk.CTkToplevel(self.root)
                dlg.title(title)
                dlg.configure(fg_color=COLOR_BG_DIALOG)
                dlg.transient(self.root)
                dlg.resizable(False, False)

                ctk.CTkLabel(
                    dlg,
                    text=msg,
                    font=(self._main_font, 13),
                    text_color=COLOR_TEXT_MAIN,
                    wraplength=360,
                    justify="center",
                ).pack(padx=24, pady=(24, 20))

                btn_frame = tk.Frame(dlg, bg=COLOR_BG_DIALOG)
                btn_frame.pack(padx=24, pady=(0, self.sc(48)))

                def _confirm():
                    confirmed[0] = True
                    dlg.destroy()

                def _cancel():
                    dlg.destroy()

                btn_yes = ctk.CTkButton(
                    btn_frame,
                    text=l.get("yes", "Yes"),
                    width=90,
                    fg_color=COLOR_BTN_DEFAULT,
                    hover_color=COLOR_BTN_ACTIVE,
                    text_color=COLOR_TEXT_BRIGHT,
                    font=(self._main_font, 13),
                    command=_confirm,
                )
                btn_yes.pack(side="left", padx=(0, 10))

                btn_no = ctk.CTkButton(
                    btn_frame,
                    text=l.get("no", "No"),
                    width=90,
                    fg_color=COLOR_BTN_DEFAULT,
                    hover_color=COLOR_BTN_ACTIVE,
                    text_color=COLOR_TEXT_BRIGHT,
                    font=(self._main_font, 13),
                    command=_cancel,
                )
                btn_no.pack(side="left")

                _focused = ["no"]

                def _set_focus(which):
                    _focused[0] = which
                    if which == "no":
                        btn_no.configure(fg_color=COLOR_BTN_ACTIVE)
                        btn_yes.configure(fg_color=COLOR_BTN_DEFAULT)
                    else:
                        btn_yes.configure(fg_color=COLOR_BTN_ACTIVE)
                        btn_no.configure(fg_color=COLOR_BTN_DEFAULT)

                def _activate(e=None):
                    if _focused[0] == "yes":
                        _confirm()
                    else:
                        _cancel()

                dlg.bind("<Left>",     lambda e: _set_focus("yes" if _focused[0] == "no" else "no"))
                dlg.bind("<Right>",    lambda e: _set_focus("yes" if _focused[0] == "no" else "no"))
                dlg.bind("<Return>",   _activate)
                dlg.bind("<KP_Enter>", _activate)
                dlg.bind("<Escape>",   lambda e: _cancel())

                _set_focus("no")

                self._center_dialog(dlg, 440)

                dlg.lift()
                dlg.attributes("-topmost", True)
                dlg.after(150, lambda: dlg.attributes("-topmost", False))
                dlg.grab_set()
                self.root.wait_window(dlg)

                if not confirmed[0]:
                    return  # User cancelled - nothing changes (no .set, no color update)

        # 2. Commit the state change now that the user has confirmed (or no dialog was needed)
        self.load_full_file.set(new_value)

        # If the user explicitly chose unlimited mode for a large file, mark the auto-limit
        # flag as already triggered so that update_stats (scheduled via after(0,...) inside
        # start_monitoring) does not immediately revert load_full_file back to False.
        if new_value:
            self.has_auto_limited = True

        # 3. Apply visual updates
        self.update_button_colors()

        # Update the button text (Limit / Unlimited)
        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])
        new_text = (
            l_ui.get("unlimited", "⚠️ Unlimited")
            if new_value
            else l_ui.get("limit", "ℹ️ 1000 lines max")
        )
        self.limit_var.set(new_text)

        # 4. Execute the heavy task (reload file)
        self.root.update_idletasks()

        if self.log_file_path:
            self.start_monitoring(self.log_file_path, is_manual=True)

        self.save_session()

    def toggle_pause_scroll(self):
        if not self.check_log_loaded():
            return
        if not self.check_log_available():
            return

        if not self.is_paused.get() and self.log_file_path:
            # If the summary was displayed, clear it and restore normal log view
            if getattr(self, "_summary_showing", False):
                self._summary_showing = False
                self._last_wrap_anchor = None
                self.update_button_colors()
                self.trigger_refresh()
                return

            current_x = self.txt_area.xview()[0]
            self.txt_area.see(tk.END)
            self.txt_area.xview_moveto(current_x)

        self._last_wrap_anchor  = None  # Pause toggle invalidates the remembered line
        self._last_wrap_content = None

        # Immediately sync button color and tooltip to new state
        self.update_button_colors()

        self.update_stats()

    def _show_info_dialog(self, title, msg, w_logical=400):
        """
        Shows a themed single-button info/warning dialog centered over the main window.
        Blocks until the user closes it (grab_set + wait_window).
        """
        dlg = ctk.CTkToplevel(self.root)
        dlg.title(title)
        dlg.configure(fg_color=COLOR_BG_DIALOG)
        dlg.transient(self.root)
        dlg.resizable(False, False)

        ctk.CTkLabel(
            dlg,
            text=msg,
            font=(self._main_font, 13),
            text_color=COLOR_TEXT_MAIN,
            wraplength=w_logical - 80,
            justify="center",
        ).pack(padx=24, pady=(24, 16))

        l = LANGS.get(self.current_lang.get(), LANGS["EN"])
        btn_frame = tk.Frame(dlg, bg=COLOR_BG_DIALOG)
        btn_frame.pack(padx=24, pady=(0, self.sc(48)))

        ctk.CTkButton(
            btn_frame,
            text=l.get("ok", "OK"),
            width=90,
            fg_color=COLOR_BTN_DEFAULT,
            hover_color=COLOR_BTN_ACTIVE,
            text_color=COLOR_TEXT_BRIGHT,
            font=(self._main_font, 13),
            command=dlg.destroy,
        ).pack()

        dlg.bind("<Return>",   lambda e: dlg.destroy())
        dlg.bind("<KP_Enter>", lambda e: dlg.destroy())
        dlg.bind("<Escape>",   lambda e: dlg.destroy())

        self._center_dialog(dlg, w_logical)

        dlg.lift()
        dlg.attributes("-topmost", True)
        dlg.after(150, lambda: dlg.attributes("-topmost", False))
        dlg.grab_set()
        self.root.wait_window(dlg)

    def _center_dialog(self, dlg, w_logical):
        """
        Centers a CTkToplevel dialog over the main window using DPI-aware geometry.
        Uses the same approach as show_help / show_list_manager:
        wm_geometry() bypasses CustomTkinter's auto-scaling so the dialog is
        positioned correctly on FHD, QHD, and 4K screens.
        - w_logical : desired dialog width in logical (96 DPI) pixels
        """
        dlg.update_idletasks()

        dpi_scale = 1.0
        if sys.platform == "win32":
            try:
                from ctypes import windll
                hwnd = windll.user32.GetParent(dlg.winfo_id())
                dpi  = windll.user32.GetDpiForWindow(hwnd)
                if dpi > 0:
                    dpi_scale = dpi / 96.0
            except Exception:
                pass
        else:
            try:
                dpi_scale = ctk.ScalingTracker.get_widget_scaling(dlg)
            except Exception:
                pass

        final_w = int(w_logical * dpi_scale)
        final_h = dlg.winfo_reqheight()
        pos_x   = self.root.winfo_x() + (self.root.winfo_width()  // 2) - (final_w // 2)
        pos_y   = self.root.winfo_y() + (self.root.winfo_height() // 2) - (final_h // 2)
        dlg.wm_geometry(f"{final_w}x{final_h}+{max(0, pos_x)}+{max(0, pos_y)}")

    def _graceful_close(self):
        """
        Stops the monitoring thread cleanly, saves the session, then closes the app.

        Without the thread join, calling root.destroy() while monitor_loop is alive
        causes a fatal GIL crash: the daemon thread wakes from sleep(0.4) and tries
        to access a Tkinter interpreter that no longer exists.

        Sequence:
          1. self.running = False  → exits the 'while self.running:' loop
          2. thread.join(1.2 s)   → wait at most one sleep cycle (0.4 s) + margin
          3. root.destroy()       → safe now, thread is done
        """
        self.running = False
        if (hasattr(self, 'monitor_thread')
                and self.monitor_thread is not None
                and self.monitor_thread.is_alive()):
            self.monitor_thread.join(timeout=1.2)
        self.window_geometry = self.root.geometry()
        self.save_session()
        self.root.destroy()

    def cycle_app_theme(self):
        """
        Cycles the theme choice: dark → light → dark …
        Shows a themed confirmation dialog; saves the choice and closes the app
        only if the user confirms. COLOR_* constants are resolved at import time,
        so a full restart is needed to apply the new theme.
        """
        _order = ["dark", "light"]
        current = self.app_theme.get()
        next_theme = _order[(_order.index(current) + 1) % len(_order)] \
                     if current in _order else "light"

        l = LANGS.get(self.current_lang.get(), LANGS["EN"])
        title = l.get("theme_close_title", "Theme changed")
        msg   = l.get("theme_close_msg",
                      "The theme has been changed.\n\n"
                      "The application will now close.\n"
                      "Please relaunch it to apply the new theme.")

        confirmed = [False]

        dlg = ctk.CTkToplevel(self.root)
        dlg.title(title)
        dlg.configure(fg_color=COLOR_BG_DIALOG)
        dlg.transient(self.root)
        dlg.resizable(False, False)

        ctk.CTkLabel(
            dlg,
            text=msg,
            font=(self._main_font, 13),
            text_color=COLOR_TEXT_MAIN,
            wraplength=340,
            justify="center",
        ).pack(padx=24, pady=(24, 20))

        btn_frame = tk.Frame(dlg, bg=COLOR_BG_DIALOG)
        btn_frame.pack(padx=24, pady=(0, self.sc(48)))

        def _confirm():
            confirmed[0] = True
            dlg.destroy()

        def _cancel():
            dlg.destroy()

        btn_yes = ctk.CTkButton(
            btn_frame,
            text=l.get("yes", "Yes"),
            width=90,
            fg_color=COLOR_BTN_DEFAULT,
            hover_color=COLOR_BTN_ACTIVE,
            text_color=COLOR_TEXT_BRIGHT,
            font=(self._main_font, 13),
            command=_confirm,
        )
        btn_yes.pack(side="left", padx=(0, 10))

        btn_no = ctk.CTkButton(
            btn_frame,
            text=l.get("no", "No"),
            width=90,
            fg_color=COLOR_BTN_DEFAULT,
            hover_color=COLOR_BTN_ACTIVE,
            text_color=COLOR_TEXT_BRIGHT,
            font=(self._main_font, 13),
            command=_cancel,
        )
        btn_no.pack(side="left")

        _focused = ["no"]

        def _set_focus(which):
            _focused[0] = which
            if which == "no":
                btn_no.configure(fg_color=COLOR_BTN_ACTIVE)
                btn_yes.configure(fg_color=COLOR_BTN_DEFAULT)
            else:
                btn_yes.configure(fg_color=COLOR_BTN_ACTIVE)
                btn_no.configure(fg_color=COLOR_BTN_DEFAULT)

        def _activate(e=None):
            if _focused[0] == "yes":
                _confirm()
            else:
                _cancel()

        dlg.bind("<Left>",     lambda e: _set_focus("yes" if _focused[0] == "no" else "no"))
        dlg.bind("<Right>",    lambda e: _set_focus("yes" if _focused[0] == "no" else "no"))
        dlg.bind("<Return>",   _activate)
        dlg.bind("<KP_Enter>", _activate)
        dlg.bind("<Escape>",   lambda e: _cancel())

        _set_focus("no")

        # Center over the main window (DPI-aware, identical to show_help)
        self._center_dialog(dlg, 420)

        dlg.lift()
        dlg.attributes("-topmost", True)
        dlg.after(150, lambda: dlg.attributes("-topmost", False))
        dlg.grab_set()
        self.root.wait_window(dlg)

        if not confirmed[0]:
            return

        self.app_theme.set(next_theme)
        self._graceful_close()

    def toggle_single_instance(self):
        """
        Toggles the ENABLE_SINGLE_INSTANCE global variable and updates the UI icon.
        """
        global ENABLE_SINGLE_INSTANCE

        self.enable_single_instance_var = not self.enable_single_instance_var
        new_icon = "🔒" if self.enable_single_instance_var else "🔓"
        self.btn_single_instance.configure(text=new_icon)
        if hasattr(self, "btn_single_instance_tooltip") and self.btn_single_instance_tooltip:
            l = LANGS.get(self.current_lang.get(), LANGS["EN"])
            tip_key = "tip_single_instance" if self.enable_single_instance_var else "tip_multi_instance"
            self.btn_single_instance_tooltip.text = l[tip_key]

        import config as config_module
        config_module.ENABLE_SINGLE_INSTANCE = self.enable_single_instance_var

        self.save_session()
        self.root.after(100, lambda: self._reinit_single_instance())

    def _reinit_single_instance(self):
        """Re-initializes the single instance listener."""
        from utils import check_single_instance
        check_single_instance()

    def sync_config_on_focus(self):
        """
        Reloads the single instance state only when the user focuses the window.
        Uses a safe approach to avoid overwriting default values.
        """
        global ENABLE_SINGLE_INSTANCE

        if not os.path.exists(CONFIG_FILE):
            return

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f.readlines() if l.strip()]
                if len(lines) >= 17:
                    val_part = lines[16].split('#')[0].strip()
                    if val_part in ["0", "1"]:
                        new_state = (val_part == "1")
                        if not hasattr(self, "enable_single_instance_var") or self.enable_single_instance_var != new_state:
                            self.enable_single_instance_var = new_state
                            ENABLE_SINGLE_INSTANCE = new_state
                            if hasattr(self, "btn_single_instance"):
                                self.btn_single_instance.configure(text="🔒" if new_state else "🔓")
        except Exception as e:
            print(f"Debug: sync_config_on_focus error: {e}")

    def select_show_summary_from_keyboard(self, event=None):
        """Simulates clicking the Summary button using the keyboard."""
        current_focus = self.root.focus_get()
        if current_focus == self.search_entry:
            return None
        if event and (event.state & 0x4):
            return "break"
        self.show_summary()
        return "break"

    def select_clear_console_from_keyboard(self, event=None):
        """Simulates clicking the Clear Console button using the keyboard."""
        self.clear_console()
        return "break"

    def toggle_limit_from_keyboard(self, event=None):
        """Switch between limited (1000 lines) and full load mode using the keyboard."""
        self.toggle_full_load()  # toggle_full_load handles load_full_file.set() internally
        self.root.update_idletasks()  # Force CTK repaint so text_color applies immediately
        return "break"

    def select_all_filter_from_keyboard(self, event=None):
        """Simulates clicking the ALL filter button using the keyboard."""
        if not self.check_log_loaded():
            return
        if not self.check_log_available():
            return

        current_focus = self.root.focus_get()
        if current_focus == self.search_entry:
            return None
        if event and (event.state & 0x4):
            return "break"

        current_val = self.filter_vars["all"].get()
        self.filter_vars["all"].set(not current_val)
        self.on_filter_toggle("all")
        return "break"

    def toggle_info_filter_from_keyboard(self, event=None):
        """Toggles the INFO filter using the keyboard."""
        current_focus = self.root.focus_get()
        if current_focus == self.search_entry:
            return None
        if event and (event.state & 0x4):
            return "break"
        current_val = self.filter_vars["info"].get()
        self.filter_vars["info"].set(not current_val)
        self.on_filter_toggle("info")
        return "break"

    def toggle_warning_filter_from_keyboard(self, event=None):
        """Toggles the WARNING filter using the keyboard."""
        current_focus = self.root.focus_get()
        if current_focus == self.search_entry:
            return None
        if event and (event.state & 0x4):
            return "break"
        current_val = self.filter_vars["warning"].get()
        self.filter_vars["warning"].set(not current_val)
        self.on_filter_toggle("warning")
        return "break"

    def toggle_error_filter_from_keyboard(self, event=None):
        """Toggles the ERROR filter using the keyboard."""
        current_focus = self.root.focus_get()
        if current_focus == self.search_entry:
            return None
        if event and (event.state & 0x4):
            return "break"
        current_val = self.filter_vars["error"].get()
        self.filter_vars["error"].set(not current_val)
        self.on_filter_toggle("error")
        return "break"

    def toggle_debug_filter_from_keyboard(self, event=None):
        """Toggles the DEBUG filter using the keyboard."""
        current_focus = self.root.focus_get()
        if current_focus == self.search_entry:
            return None
        if event and (event.state & 0x4):
            return "break"
        current_val = self.filter_vars["debug"].get()
        self.filter_vars["debug"].set(not current_val)
        self.on_filter_toggle("debug")
        return "break"

    def toggle_line_break_from_keyboard(self, event=None):
        """Toggles line break mode using the keyboard."""
        self.wrap_mode.set(not self.wrap_mode.get())
        self.toggle_line_break()
        self.update_button_colors()
        self.root.update_idletasks()  # Force CTK repaint so text_color applies immediately
        return "break"

    def toggle_pause_from_keyboard(self, event=None):
        """Toggles pause mode using the keyboard (unless writing in search)."""
        current_focus = self.root.focus_get()
        if current_focus == self.search_entry:
            return None
        self.is_paused.set(not self.is_paused.get())
        self.toggle_pause_scroll()
        self.update_button_colors()
        self.root.update_idletasks()  # Force CTK repaint so text_color applies immediately
        return "break"

    def select_reset_all_filters_from_keyboard(self, event=None):
        """Simulates clicking the RESET button via the keyboard."""
        self.root.focus_set()
        self.reset_all_filters()
        return "break"

    def focus_search_entry(self, event=None):
        """Gives focus to the search field and selects the existing text."""
        self.search_entry.focus_set()
        self.search_entry.selection_range(0, tk.END)  # works on tk.Entry
        return "break"

    def refocus_log(self, event=None):
        """Returns focus to the log area after a combobox selection."""
        self.txt_area.focus_set()

    # ── FILTER LOGIC ──────────────────────────────────────────────────────────

    def on_filter_toggle(self, mode):
        """Stabilized filtering logic for filter toggle buttons."""
        if mode == "all":
            if self.filter_vars["all"].get():
                for m in ["debug", "info", "warning", "error"]:
                    self.filter_vars[m].set(False)
                self.refresh_natural_order()
            else:
                if not any(
                    self.filter_vars[m].get()
                    for m in ["debug", "info", "warning", "error"]
                ):
                    self.filter_vars["all"].set(True)
        else:
            if self.filter_vars[mode].get():
                self.filter_vars["all"].set(False)
            if not any(self.filter_vars[m].get() for m in self.filter_vars):
                self.filter_vars["all"].set(True)
                self.refresh_natural_order()
            else:
                self.trigger_refresh()

        self.update_button_colors()

    def reset_all_filters(self):
        """Resets all filters, search, and pause state to defaults."""
        self._last_wrap_anchor = None   # Reset invalidates the remembered line
        self.hide_history_dropdown()
        self.root.focus_set()
        self.search_query.set("")
        self.selected_list.set("")

        lang_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])
        none_text = lang_ui.get("none", "None")
        self.combo_lists.set(none_text)  # CTkComboBox.set() works

        for mode in ["info", "warning", "error", "debug"]:
            self.filter_vars[mode].set(False)
        self.filter_vars["all"].set(True)

        # Reset pause state
        self.is_paused.set(False)

        self.update_button_colors()
        self.root.update_idletasks()
        self.seen_lines.clear()
        self.refresh_natural_order()
        self.txt_area.see(tk.END)
        self.txt_area.xview_moveto(0)

    def update_button_colors(self):
        """Applies background and text colors according to the state of each filter button.
        When active: colored background + white text (readable on any filter color).
        When inactive: default background + theme text color.
        """
        for mode, var in self.filter_vars.items():
            widget = self.filter_widgets.get(mode)
            if widget:
                if var.get():
                    active_color = self.filter_colors.get(mode, COLOR_ACCENT)
                    widget.configure(fg_color=active_color, text_color=COLOR_TEXT_ON_ACCENT)
                else:
                    widget.configure(fg_color=COLOR_BTN_DEFAULT, text_color=COLOR_TEXT_BRIGHT)

        # Sync option button colors and tooltips to their BooleanVar state
        l = LANGS.get(self.current_lang.get(), LANGS["EN"])

        if hasattr(self, "cde_limit"):
            _active = self.load_full_file.get()
            self.cde_limit.configure(
                fg_color=LOG_COLORS["warning"] if _active else COLOR_BTN_DEFAULT,
                text_color=COLOR_TEXT_ON_ACCENT if _active else COLOR_TEXT_BRIGHT,
                text="♾" if _active else "🛡️",
            )
            if hasattr(self, "btn_limit_tooltip") and self.btn_limit_tooltip:
                self.btn_limit_tooltip.text = l.get(
                    "tip_limit_on" if _active else "tip_limit_off", ""
                )

        if hasattr(self, "cde_wrap"):
            _active = self.wrap_mode.get()
            self.cde_wrap.configure(
                fg_color=COLOR_ACCENT if _active else COLOR_BTN_DEFAULT,
                text_color=COLOR_TEXT_ON_ACCENT if _active else COLOR_TEXT_BRIGHT,
                text="↩" if _active else "➡️",
            )
            if hasattr(self, "btn_wrap_tooltip") and self.btn_wrap_tooltip:
                self.btn_wrap_tooltip.text = l.get(
                    "tip_wrap_on" if _active else "tip_wrap_off", ""
                )

        if hasattr(self, "cde_pause"):
            _active = self.is_paused.get()
            self.cde_pause.configure(
                fg_color=COLOR_DANGER if _active else COLOR_BTN_DEFAULT,
                text_color=COLOR_TEXT_ON_ACCENT if _active else COLOR_TEXT_BRIGHT,
                text="⏸️" if _active else "▶️",
            )
            if hasattr(self, "btn_pause_tooltip") and self.btn_pause_tooltip:
                self.btn_pause_tooltip.text = l.get(
                    "tip_pause_on" if _active else "tip_pause_off", ""
                )

    def on_hover_filter(self, widget, mode, is_entering):
        """
        Handles visual hover feedback for filter toggle buttons.
        Active buttons show a lighter tint on hover; inactive buttons go grey.
        Text color follows the same active/inactive rule as update_button_colors().
        """
        if is_entering:
            if self.filter_vars[mode].get():
                color = self.filter_colors.get(mode, COLOR_ACCENT)
                widget.configure(fg_color=self._lighten_color(color, 0.25), text_color=COLOR_TEXT_ON_ACCENT)
            else:
                widget.configure(fg_color=COLOR_BTN_ACTIVE, text_color=COLOR_TEXT_BRIGHT)
        else:
            if self.filter_vars[mode].get():
                color = self.filter_colors.get(mode, COLOR_ACCENT)
                widget.configure(fg_color=color, text_color=COLOR_TEXT_ON_ACCENT)
            else:
                widget.configure(fg_color=COLOR_BTN_DEFAULT, text_color=COLOR_TEXT_BRIGHT)

    def on_list_selected(self, event=None):
        if not self.check_log_loaded():
            return
        if not self.check_log_available():
            return

        selection = self.selected_list.get()
        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])

        if not selection or selection == l_ui["none"]:
            self.trigger_refresh()
            return

        search_text = l_ui["search_ph"]
        self.show_loading(True, message=search_text)
        self.root.after(300, lambda: self._process_keyword_search(selection))

    def _process_keyword_search(self, selection):
        """Internal method: performs the actual keyword-list search."""
        try:
            self.trigger_refresh()
        finally:
            self.show_loading(False)

    def refresh_keyword_list(self, trigger_monitor=True):
        """Reloads the keyword list combobox from the keyword directory."""
        l = LANGS.get(self.current_lang.get(), LANGS["EN"])
        files = [
            f.replace(".txt", "") for f in os.listdir(KEYWORD_DIR) if f.endswith(".txt")
        ]
        kw_vals = [l["none"]] + sorted(files)
        self.combo_lists.configure(values=kw_vals)  # CTkComboBox API
        _patch_combo_hover_text(self.combo_lists)   # Re-patch after values rebuild (light theme)

        if self.selected_list.get() not in kw_vals:
            self.selected_list.set(l["none"])

        if trigger_monitor:
            self.trigger_refresh()

    def open_keyword_folder(self):
        abs_path = os.path.abspath(KEYWORD_DIR)
        if sys.platform == "win32":
            os.startfile(abs_path)
        else:
            subprocess.Popen(
                ["open" if sys.platform == "darwin" else "xdg-open", abs_path]
            )

    def change_language(self):
        """
        Handles language change when an item is selected in the language combobox.
        The combo now displays full names (e.g. "Français"); we translate back to
        the language code (e.g. "FR") before storing it in current_lang.
        """
        display_val = self.combo_lang.get().strip()
        code = LANG_CODES.get(display_val, display_val)  # fallback: value is already a code
        self.current_lang.set(code)
        self.root.focus_set()
        self.retranslate_ui(True)
        self.save_session()

    def retranslate_ui(self, refresh_monitor=True):
        """Retranslates all UI text strings to the currently selected language."""
        l = LANGS.get(self.current_lang.get(), LANGS["EN"])

        # Main toolbar buttons (CTkButton → configure)
        self.btn_log.configure(text=l["log"])
        self.btn_sum.configure(text=l["sum"])  # icon only now
        self.btn_exp.configure(text=l["exp"])
        self.btn_upl.configure(text=l["upl"])
        self.btn_clr.configure(text=l["clr"])

        if hasattr(self, "btn_reset"):
            self.btn_reset.configure(text=l.get("btn_reset", "↻ RESET"))

        # Tooltip text updates (ToolTip objects store text as attribute)
        if hasattr(self, "btn_open_tooltip") and self.btn_open_tooltip:
            self.btn_open_tooltip.text = l["tip_open"]
        if hasattr(self, "btn_export_tooltip") and self.btn_export_tooltip:
            self.btn_export_tooltip.text = l["tip_export"]
        if hasattr(self, "btn_upload_tooltip") and self.btn_upload_tooltip:
            self.btn_upload_tooltip.text = l["tip_upload"]
        if hasattr(self, "btn_summary_tooltip") and self.btn_summary_tooltip:
            self.btn_summary_tooltip.text = l["tip_summary"]
        if hasattr(self, "btn_clear_tooltip") and self.btn_clear_tooltip:
            self.btn_clear_tooltip.text = l["tip_clear"]
        if hasattr(self, "label_duration_tooltip") and self.label_duration_tooltip:
            self.label_duration_tooltip.text = l.get("tip_duration", "")
        if hasattr(self, "btn_limit_tooltip") and self.btn_limit_tooltip:
            self.btn_limit_tooltip.text = l["tip_limit_on" if not self.load_full_file.get() else "tip_limit_off"]
        if hasattr(self, "btn_wrap_tooltip") and self.btn_wrap_tooltip:
            self.btn_wrap_tooltip.text = l["tip_wrap_on" if self.wrap_mode.get() else "tip_wrap_off"]
        if hasattr(self, "btn_pause_tooltip") and self.btn_pause_tooltip:
            self.btn_pause_tooltip.text = l["tip_pause_on" if self.is_paused.get() else "tip_pause_off"]
        if hasattr(self, "btn_single_instance_tooltip") and self.btn_single_instance_tooltip:
            _tip_si_key = "tip_single_instance" if self.enable_single_instance_var else "tip_multi_instance"
            self.btn_single_instance_tooltip.text = l[_tip_si_key]
        if hasattr(self, "combo_lang_tooltip") and self.combo_lang_tooltip:
            self.combo_lang_tooltip.text = l["tip_lang"]
        if hasattr(self, "combo_kw_tooltip") and self.combo_kw_tooltip:
            self.combo_kw_tooltip.text = l["tip_kw_list"]
        self.update_history_clear_tooltip()
        if hasattr(self, "search_bar_tooltip") and self.search_bar_tooltip:
            self.search_bar_tooltip.text = l["tip_search_bar"]
        if hasattr(self, "btn_help_tooltip") and self.btn_help_tooltip:
            self.btn_help_tooltip.text = l["tip_help"]
        if hasattr(self, "btn_reset_tooltip") and self.btn_reset_tooltip:
            self.btn_reset_tooltip.text = l["tip_reset"]
        if hasattr(self, "btn_down_font_tooltip") and self.btn_down_font_tooltip:
            self.btn_down_font_tooltip.text = l["tip_down_font"]
        if hasattr(self, "btn_up_font_tooltip") and self.btn_up_font_tooltip:
            self.btn_up_font_tooltip.text = l["tip_up_font"]
        if hasattr(self, "btn_kw_refresh_tooltip") and self.btn_kw_refresh_tooltip:
            self.btn_kw_refresh_tooltip.text = l["tip_kw_refresh"]
        if hasattr(self, "btn_kw_folder_tooltip") and self.btn_kw_folder_tooltip:
            self.btn_kw_folder_tooltip.text = l["tip_kw_folder"]
        if hasattr(self, "github_tooltip") and self.github_tooltip:
            self.github_tooltip.text = l["tip_github"]
        if hasattr(self, "btn_theme_tooltip") and self.btn_theme_tooltip:
            _next_tip = {"dark": "tip_theme_light", "light": "tip_theme_dark"}
            tip_key = _next_tip.get(self.app_theme.get(), "tip_theme_light")
            self.btn_theme_tooltip.text = l.get(tip_key, "Toggle theme")

        # Restore inaccessible file error message if needed
        if getattr(self, "is_file_inaccessible", False):
            msg = l.get("file_error", "⚠️ LOG INACCESSIBLE!")
            self.inactivity_timer_var.set(msg)

        # --- Translate filter button labels (CTkButton) ---
        tm = {"all": "all", "info": "info", "warning": "warn", "error": "err", "debug": "debug"}
        for mode, cb in self.filter_widgets.items():
            new_text = l[tm[mode]]
            # Recalculate width so padding stays 15px on each side regardless of language
            _fnt = ctk.CTkFont(family=self._emoji_font, size=12, weight="bold")
            cb.configure(text=new_text, width=_fnt.measure(new_text) + 30)

        # --- Translate filter button tooltips ---
        for mode, tooltip in self.filter_tooltips.items():
            if tooltip:
                tip_key = f"tip_filter_{mode}"
                tooltip.text = l[tip_key]

        # --- Context menu item labels (tk.Label - uses .config()) ---
        if hasattr(self, "menu_items"):
            self.menu_items[0].config(text=f"  {l['copy']}  ")
            self.menu_items[1].config(text=f"  {l['sel_all']}  ")
            self.menu_items[2].config(text=f"  {l['search_localy']}  ")
            self.menu_items[3].config(text=f"  {l['search_google']}  ")
            self.menu_items[4].config(text=f"  {l['exclude']}  ")
        self.update_exclude_button()

        # --- Status label StringVars ---
        if self.is_paused.get():
            self.paused_var.set(l["paused"])
        else:
            self.paused_var.set("")

        if self.wrap_mode.get():
            self.wrap_var.set(l["line_break"])
        else:
            self.wrap_var.set("")

        if not self.load_full_file.get():
            self.limit_var.set(l["limit"])
        else:
            self.limit_var.set("")

        # --- Update Search Placeholder ---
        if hasattr(self, "placeholder_label"):
            self.placeholder_label.config(text=l.get("search_localy", "Search"))
            # Re-run visibility logic in case the field is currently empty and unfocused
            if not self.search_query.get() and self.search_entry.focus_get() != self.search_entry:
                self.placeholder_label.place(relx=0, rely=0.5, anchor="w", x=5)

        self.refresh_keyword_list(trigger_monitor=refresh_monitor)
        self.update_stats()
        self.update_button_colors()
        self._build_search_menu_items()

    def increase_font(self):
        self.font_size += 1
        self.update_tags_config()
        self.save_session()

    def decrease_font(self):
        if self.font_size > 6:
            self.font_size -= 1
            self.update_tags_config()
            self.save_session()

    def show_loading(self, show, message=None):
        """Shows or hides the loading overlay on the text area."""
        if show:
            if message:
                self.loading_label.configure(text=message)  # CTkLabel
            else:
                self.loading_label.configure(
                    text=LANGS[self.current_lang.get()]["loading"]
                )
            self.overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.root.update_idletasks()
        else:
            self.overlay.place_forget()

    def on_search_change(self, *args):
        """
        Triggered on every keystroke in the search field.
        Updates the ×-button immediately, then debounces the actual search so
        the file is not scanned on every single character.
        """
        if not self.check_log_loaded():
            return
        if not self.check_log_available():
            return

        query = self.search_query.get()

        if query:
            self.btn_clear_search.place(relx=0.5, rely=0.5, anchor="center")
        else:
            self.btn_clear_search.place_forget()
            # Invalidate the remembered line - search change makes it stale.
            self._last_wrap_anchor = None
            # NOTE: pause state is intentionally NOT changed here.
            # Only explicit user actions (DEL button, ESC key, Reset) deactivate pause.
            # This prevents the pause being silently released when search is cleared
            # character by character, which the user would only notice when new log
            # activity causes an unexpected scroll.

            # Empty query: bypass the sorting search worker and restore natural order.
            self._cancel_pending_search()
            self.refresh_natural_order()
            return

        # Debounce: cancel any pending search timer and start a fresh one.
        # The actual file scan only starts 250 ms after the last keystroke.
        if self._search_after_id:
            self.root.after_cancel(self._search_after_id)
        self._search_after_id = self.root.after(250, self._fire_search)

    def _fire_search(self):
        """
        Called 250 ms after the last keystroke (debounce).
        Captures all Tkinter variable state on the main thread, then hands off
        the heavy file-read + filter work to a background thread.
        """
        self._search_after_id = None

        if not self.check_log_loaded() or not self.check_log_available():
            self.show_loading(False)
            return

        # --- Capture Tkinter state HERE (main thread only) ---
        # Background threads must not call .get() on Tkinter variables.
        query_lower      = self.search_query.get().strip().lower()
        filter_all       = self.filter_vars["all"].get()
        active_tags      = {k for k, v in self.filter_vars.items()
                            if k != "all" and v.get()}
        load_full        = self.load_full_file.get()
        keywords_lower   = [k.lower() for k in self.get_keywords_from_file()]

        # Increment version: any worker still running for the previous query
        # will see the mismatch and stop early.
        self._search_version += 1
        version = self._search_version

        self.show_loading(True)

        threading.Thread(
            target=self._search_worker,
            args=(version, query_lower, filter_all, active_tags,
                  load_full, keywords_lower),
            daemon=True,
        ).start()

    def _search_worker(self, version, query_lower, filter_all,
                       active_tags, load_full, keywords_lower):
        """
        Background thread: reads the log file and filters lines using only
        plain Python values (no Tkinter calls - not thread-safe).

        Aborts early whenever _search_version no longer matches, meaning
        the user typed another character and a newer search has taken over.
        """
        _ts_re = re.compile(r"^\d{4}-\d{2}-\d{2}")
        try:
            if not self.log_file_path or not self.running:
                return

            with open(self.log_file_path, "r", encoding="utf-8",
                      errors="ignore") as f:
                if load_full:
                    lines = f.readlines()
                else:
                    f.seek(0, os.SEEK_END)
                    f.seek(max(0, f.tell() - 200_000))
                    lines = f.readlines()[-1000:]

            if version != self._search_version:
                return

            to_display = []
            last_parent_visible = False

            for line in lines:
                if version != self._search_version:
                    return  # Newer search started - discard current work

                stripped = line.strip()
                if not stripped or "info <general>: --------" in line:
                    last_parent_visible = False
                    continue

                low = line.lower()

                # Exclusion list check - safe to read from background thread.
                if self.exclude_patterns and any(exc in low for exc in self.exclude_patterns):
                    last_parent_visible = False
                    continue

                if not _ts_re.match(stripped):
                    # Orphan continuation: inherit parent visibility.
                    if last_parent_visible:
                        to_display.append((line, None))
                    continue

                # Determine log level (mirrors get_line_data)
                if " error " in low or " critical " in low:
                    current_tag = "error"
                elif " warning " in low:
                    current_tag = "warning"
                elif " info " in low:
                    current_tag = "info"
                elif " debug " in low:
                    current_tag = "debug"
                else:
                    current_tag = None

                # Level filter (mirrors is_filter_match)
                if not filter_all:
                    if current_tag is None or current_tag not in active_tags:
                        last_parent_visible = False
                        continue

                # Text search filter
                if query_lower and query_lower not in low:
                    last_parent_visible = False
                    continue

                # Keyword-list filter
                if keywords_lower and not any(k in low for k in keywords_lower):
                    last_parent_visible = False
                    continue

                to_display.append((line, current_tag))
                last_parent_visible = True

            if version != self._search_version:
                return

            # File is already chronological - no sort needed.

            if self.running:
                self.root.after(0, self._apply_search_results,
                                to_display, version)

        except Exception as e:
            if self.running:
                print(f"[SEARCH ERROR] {type(e).__name__}: {e}")
                try:
                    self.root.after(0, self.show_loading, False)
                except Exception:
                    pass

    def _apply_search_results(self, to_display, version):
        """
        Called on the main thread with the results from _search_worker.
        Discards stale results if a newer search has already started.
        """
        if version != self._search_version:
            return  # Superseded by a more recent search - ignore
        # Clear the widget before calling bulk_insert so that, when to_display
        # is empty, bulk_insert sees an empty widget and shows the "no results"
        # message instead of leaving the previous log visible.
        self.txt_area.config(state=tk.NORMAL)
        self.txt_area.delete("1.0", tk.END)
        self.bulk_insert(to_display)

    def clear_search(self):
        # Deactivate pause first so that on_search_change's refresh_natural_order
        # call already runs with pause=False and scrolls to end - avoids a
        # redundant second refresh when we clear the query below.
        if self.is_paused.get():
            self.is_paused.set(False)
            self._last_wrap_anchor = None
            self.update_button_colors()
        # Clearing the query fires on_search_change which cancels pending search
        # and calls refresh_natural_order (scrolls to end now that pause is off).
        self.search_query.set("")
        self.search_entry.focus_set()

    def _cancel_pending_search(self):
        """Cancels any debounced search timer and invalidates any running worker."""
        if getattr(self, "_search_after_id", None):
            self.root.after_cancel(self._search_after_id)
            self._search_after_id = None
        self._search_version = getattr(self, "_search_version", 0) + 1

    @staticmethod
    def _strip_pad(text: str) -> str:
        """Strip trailing whitespace from each line.
        Removes the fixed-width padding added by _pad_line() for the horizontal
        scrollbar, so copied text does not contain hundreds of trailing spaces."""
        return "\n".join(line.rstrip() for line in text.splitlines())

    def copy_selection(self):
        try:
            selected_text = self.txt_area.get(tk.SEL_FIRST, tk.SEL_LAST)
            if selected_text:
                self.root.clipboard_clear()
                self.root.clipboard_append(self._strip_pad(selected_text))
        except tk.TclError:
            pass

    def search_on_google(self):
        try:
            selected_text = self.txt_area.get(tk.SEL_FIRST, tk.SEL_LAST)
            if selected_text.strip():
                url = f"https://www.google.com/search?q={quote(selected_text.strip())}"
                self.open_url(url)
        except tk.TclError:
            pass

    def search_selection_locally(self, event=None):
        """
        Gets selected text from the log area, sets it as the search query,
        and triggers a local search.
        """
        try:
            selected_text = self.txt_area.get(tk.SEL_FIRST, tk.SEL_LAST).strip()
            if selected_text:
                self.search_query.set(selected_text)
                self.validate_and_save_search()
                self.search_entry.focus_set()
                self.search_entry.icursor(tk.END)  # tk.Entry
        except tk.TclError:
            pass

    def _clamp_menu(self, menu, x, y):
        """
        Clamps a Toplevel context menu position so it never overflows
        outside the application window boundaries.

        Args:
            menu (tk.Toplevel): The menu window to position.
            x (int): Desired screen x coordinate (from event.x_root).
            y (int): Desired screen y coordinate (from event.y_root).

        Returns:
            tuple[int, int]: Clamped (x, y) screen coordinates.
        """
        menu.update_idletasks()
        mw = menu.winfo_reqwidth()
        mh = menu.winfo_reqheight()

        # App window bounds (screen coordinates)
        rx = self.root.winfo_rootx()
        ry = self.root.winfo_rooty()
        rw = self.root.winfo_width()
        rh = self.root.winfo_height()

        # Clamp so the menu stays fully inside the app window
        clamped_x = min(x, rx + rw - mw)
        clamped_y = min(y, ry + rh - mh)

        # Never place it above/left of the app window either
        clamped_x = max(clamped_x, rx)
        clamped_y = max(clamped_y, ry)

        return clamped_x, clamped_y

    def _menu_visible_items(self):
        """Returns the list of visible (packed) log context menu items."""
        return [item for item in self.menu_items if item.winfo_ismapped()]

    def _menu_highlight(self, delta):
        """
        Moves keyboard focus within the context menu by delta steps.
        delta=0 initialises the highlight on the first item.
        """
        items = self._menu_visible_items()
        if not items:
            return
        n = len(items)
        # Clear current highlight
        if 0 <= self._menu_kbfocus < n:
            items[self._menu_kbfocus].config(bg=COLOR_BTN_DEFAULT, fg=COLOR_TEXT_BRIGHT)
        # Compute new index (wraps around)
        if self._menu_kbfocus < 0:
            new_idx = 0 if delta >= 0 else n - 1
        else:
            new_idx = (self._menu_kbfocus + delta) % n
        self._menu_kbfocus = new_idx
        items[new_idx].config(bg=COLOR_ACCENT, fg=COLOR_TEXT_ON_ACCENT)

    def _menu_activate(self):
        """Triggers the currently highlighted context menu item."""
        items = self._menu_visible_items()
        if 0 <= self._menu_kbfocus < len(items):
            items[self._menu_kbfocus].event_generate("<Button-1>")

    def show_context_menu_from_keyboard(self, event=None):
        """
        Opens the log context menu via keyboard shortcut (M key).
        Positions the menu below the insertion cursor when visible,
        otherwise at the centre of the log area.
        Keyboard navigation (Up/Down/Return/Escape) is enabled.
        Requires an active text selection in the log area.
        """
        if not self.txt_area.tag_ranges("sel"):
            return "break"
        try:
            bbox = self.txt_area.bbox(tk.INSERT)
            if bbox:
                bx, by, _, bh = bbox
                x_root = self.txt_area.winfo_rootx() + bx
                y_root = self.txt_area.winfo_rooty() + by + bh
            else:
                raise tk.TclError
        except (tk.TclError, TypeError):
            x_root = self.txt_area.winfo_rootx() + self.txt_area.winfo_width() // 2
            y_root = self.txt_area.winfo_rooty() + self.txt_area.winfo_height() // 2

        class _Ev:
            pass
        ev = _Ev()
        ev.x_root = x_root
        ev.y_root = y_root
        self.show_context_menu(ev)

        # Start keyboard navigation on first item
        self._menu_kbfocus = -1
        self._menu_highlight(0)
        return "break"

    def show_context_menu(self, event):
        """
        Displays the custom context menu at the mouse position,
        clamped so it never overflows outside the application window.
        Dynamically toggles the Google Search option.
        Requires an active text selection in the log area.
        """
        if not self.txt_area.tag_ranges("sel"):
            return
        self.txt_area.focus_set()

        if self.show_google_search.get():
            self.google_menu_item.pack(fill="x")
        else:
            self.google_menu_item.pack_forget()

        # Reset keyboard focus index on each display
        self._menu_kbfocus = -1

        # Pre-show offscreen to get real dimensions before clamping
        self.context_menu.geometry(f"+{event.x_root}+{event.y_root}")
        self.context_menu.deiconify()

        cx, cy = self._clamp_menu(self.context_menu, event.x_root, event.y_root)
        self.context_menu.geometry(f"+{cx}+{cy}")

        self.context_menu.lift()
        self.context_menu.focus_set()
        self.context_menu.bind("<FocusOut>", lambda e: self.context_menu.withdraw())

        # Keyboard navigation bindings (bound once, persistent)
        if not getattr(self, "_context_menu_kb_bound", False):
            self.context_menu.bind("<Up>",     lambda e: self._menu_highlight(-1))
            self.context_menu.bind("<Down>",   lambda e: self._menu_highlight(1))
            self.context_menu.bind("<Return>",  lambda e: self._menu_activate())
            self.context_menu.bind("<KP_Enter>", lambda e: self._menu_activate())
            self.context_menu.bind("<Escape>",  lambda e: self.context_menu.withdraw())
            self._context_menu_kb_bound = True

    def show_search_context_menu(self, event):
        """
        Displays the search-field context menu, clamped inside the app window.
        """
        self.context_menu.withdraw()

        # Pre-show offscreen to get real dimensions before clamping
        self.search_context_menu.geometry(f"+{event.x_root}+{event.y_root}")
        self.search_context_menu.deiconify()

        cx, cy = self._clamp_menu(self.search_context_menu, event.x_root, event.y_root)
        self.search_context_menu.geometry(f"+{cx}+{cy}")

        self.search_context_menu.lift()
        self.search_context_menu.focus_set()
        self.search_context_menu.bind("<FocusOut>", lambda e: self.search_context_menu.withdraw())

    def _build_search_menu_items(self):
        """Rebuilds the search-field context menu items with current language strings."""
        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])

        for widget in self.search_menu_inner.winfo_children():
            widget.destroy()

        def _make_item(text, cmd):
            """Create a tk.Label menu item with manual hover styling.
            tk.Label is used instead of CTkButton because overrideredirect
            windows don't propagate mouse events reliably to CTk's internal
            canvas widgets, breaking hover detection."""
            lbl = tk.Label(
                self.search_menu_inner,
                text=text,
                bg=COLOR_BTN_DEFAULT,
                fg=COLOR_TEXT_BRIGHT,
                font=(self.main_font_family, 11),
                padx=10,
                pady=self.sc(7),
                anchor="w",
                cursor="hand2",
            )
            lbl.pack(fill="x")
            lbl.bind("<Enter>", lambda e, l=lbl: l.config(bg=COLOR_ACCENT, fg=COLOR_TEXT_ON_ACCENT))
            lbl.bind("<Leave>", lambda e, l=lbl: l.config(bg=COLOR_BTN_DEFAULT, fg=COLOR_TEXT_BRIGHT))
            lbl.bind("<Button-1>", lambda e: cmd())
            return lbl

        _make_item(
            text=f"  {l_ui['paste']}  ",
            cmd=lambda: [
                self.search_entry.event_generate("<<Paste>>"),
                self.search_context_menu.withdraw(),
            ],
        )
        _make_item(
            text=f"  {l_ui['clear']}  ",
            cmd=lambda: [
                self.search_query.set(""),
                self.search_context_menu.withdraw(),
            ],
        )

    def open_url(self, url):
        """
        Centralized URL opener with a fallback for Linux/Snap environments.
        """
        if sys.platform.startswith('linux'):
            try:
                subprocess.Popen(
                    ['xdg-open', url],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except Exception:
                webbrowser.open(url)
        else:
            webbrowser.open(url)

    def open_github_link(self, event=None):
        self.open_url(GITHUB_URL)

    def update_windows_title_bar(self):
        """Apply the title bar color based on the resolved APP_THEME (dark or light)."""
        if sys.platform == "win32":
            try:
                from ctypes import windll, byref, sizeof, c_int
                self.root.update_idletasks()
                hwnd = windll.user32.GetAncestor(self.root.winfo_id(), 2)
                is_dark = 1 if APP_THEME == "dark" else 0
                caption_color = c_int(0x002D2D2D) if APP_THEME == "dark" else c_int(0x00d6d6d6)
                windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, byref(c_int(is_dark)), sizeof(c_int(is_dark)))
                windll.dwmapi.DwmSetWindowAttribute(hwnd, 34, byref(caption_color), sizeof(caption_color))
                windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0020 | 0x0002 | 0x0001 | 0x0004)
            except Exception:
                pass

    def update_status_color(self, color):
        """Updates the status indicator circle color."""
        if hasattr(self, "status_indicator"):
            self.status_indicator.itemconfig(self.status_circle, fill=color)

    def hide_cursor(self):
        """Hides the text cursor by disabling its blink."""
        self.txt_area.config(insertontime=0)
        self.cursor_visible = False
        self.cursor_timer = None

    def reset_cursor_timer(self, event=None):
        """Resets the inactivity timer and restores cursor visibility."""
        if self.cursor_timer:
            self.root.after_cancel(self.cursor_timer)
        if not self.cursor_visible:
            self.txt_area.config(insertontime=600)
            self.cursor_visible = True
        self.cursor_timer = self.root.after(5000, self.hide_cursor)

    def safe_vertical_scroll(self, event):
        """Vertical scroll using the mouse wheel without resetting the X axis."""
        if event.delta:
            direction = -1 if event.delta > 0 else 1
            self.txt_area.yview_scroll(direction, "units")
        elif event.num == 4:
            self.txt_area.yview_scroll(-1, "units")
        elif event.num == 5:
            self.txt_area.yview_scroll(1, "units")
        return "break"

    def immediate_ui_refresh(self):
        """Immediately syncs the limit label with the current toggle state."""
        l = LANGS.get(self.current_lang.get(), LANGS["EN"])
        txt = l["unlimited"] if self.load_full_file.get() else l["limit"]
        self.limit_var.set(txt)  # uses textvariable - no .config() needed

    def copy_to_clipboard(self, event=None):
        """Copies the currently selected text from the log area to the clipboard.
        Trailing spaces added by _pad_line() are stripped before copying."""
        try:
            selected_text = self.txt_area.get(tk.SEL_FIRST, tk.SEL_LAST)
            if selected_text:
                self.root.clipboard_clear()
                self.root.clipboard_append(self._strip_pad(selected_text))
                self.root.update()
        except tk.TclError:
            pass
        return "break"

    # ── HISTORY DROPDOWN ──────────────────────────────────────────────────────

    def setup_history_events(self):
        """Initializes history and binds events to the search field."""
        self.load_search_history()

        self.search_entry.bind("<KeyRelease>", self.on_search_keyrelease)
        self.search_entry.bind("<Up>",   self.on_search_up)
        self.search_entry.bind("<Down>", self.on_search_down)
        self.search_entry.bind("<Left>",  self._exit_history_to_entry)
        self.search_entry.bind("<Right>", self._exit_history_to_entry)
        self.history_listbox.bind("<Left>",  self._exit_history_to_entry)
        self.history_listbox.bind("<Right>", self._exit_history_to_entry)
        self.search_entry.bind("<Escape>", self.reset_search_and_focus_log)
        self.search_entry.bind("<Return>", self.validate_and_save_search)
        self.txt_area.bind("<FocusIn>", lambda e: self.hide_history_dropdown(), add="+")
        self.root.bind("<Button-1>", self._close_dropdown_on_outside_click, add="+")
        self.update_history_clear_tooltip()

    def load_search_history(self):
        """Loads search history from file."""
        self.search_history = []
        if os.path.exists(SEARCH_HISTORY_FILE):
            try:
                with open(SEARCH_HISTORY_FILE, "r", encoding="utf-8") as f:
                    self.search_history = [line.strip() for line in f.readlines() if line.strip()]
            except Exception as e:
                print(f"Error loading history: {e}")

    def save_search_history(self):
        """Saves search history to file."""
        try:
            with open(SEARCH_HISTORY_FILE, "w", encoding="utf-8") as f:
                for item in self.search_history:
                    f.write(f"{item}\n")
        except Exception as e:
            print(f"Error saving history: {e}")

    def add_to_history(self, text):
        """Adds a search term to history (no duplicates, most recent first)."""
        text = text.strip()
        if not text:
            return
        if text in self.search_history:
            self.search_history.remove(text)
        self.search_history.insert(0, text)
        self.search_history = self.search_history[:SEARCH_HISTORY_MAX_SIZE]
        self.save_search_history()
        self.update_history_clear_tooltip()

    def update_history_clear_tooltip(self):
        """Updates the history button tooltip text and color based on whether history is empty."""
        if not hasattr(self, "history_clear_tooltip") or not self.history_clear_tooltip:
            return
        if not hasattr(self, "search_history"):
            return
        l = LANGS.get(self.current_lang.get(), LANGS["EN"])
        if self.search_history:
            self.history_clear_tooltip.text = l.get("tip_history_manage", "Search history - click to manage")
            if hasattr(self, "btn_clear_history"):
                self.btn_clear_history.configure(text_color=COLOR_TEXT_DIM)
        else:
            self.history_clear_tooltip.text = l.get("tip_history_empty", "No search history")
            if hasattr(self, "btn_clear_history"):
                self.btn_clear_history.configure(text_color=COLOR_TEXT_LIGHT)

    def clean_search_input(self, *args):
        """
        Sanitizes the search input: removes multi-line, limits length,
        and collapses whitespace.
        """
        raw_text = self.search_query.get()
        if not raw_text:
            return

        clean_text = raw_text.splitlines()[0] if raw_text.splitlines() else ""

        max_length = 100
        if len(clean_text) > max_length:
            clean_text = clean_text[:max_length]

        clean_text = re.sub(r'[ \t]+', ' ', clean_text)
        clean_text = clean_text.lstrip()

        if raw_text != clean_text:
            self.search_query.set(clean_text)
            self.search_entry.icursor(tk.END)  # tk.Entry

    def show_history_dropdown(self, items=None):
        """Displays the history dropdown with matching entries."""
        if items is None:
            items = self.search_history

        if not items:
            self.hide_history_dropdown()
            return

        self.history_window.configure(
            bg=COLOR_BG_HEADER,
            highlightbackground=COLOR_TEXT_DIM,
            highlightthickness=1,
            relief="flat",
        )

        self.history_listbox.config(
            bg=COLOR_BG_HEADER,
            fg=COLOR_TEXT_MAIN,
            selectbackground=COLOR_ACCENT,
            selectforeground=COLOR_TEXT_ON_ACCENT,  # Always white on blue selection (readable in both themes)
            font=(get_system_font()[0], 12),
            borderwidth=0,
            highlightthickness=0,
            relief="flat",
            selectborderwidth=0,
        )

        self.history_listbox.delete(0, tk.END)
        self._hist_tip_items = []
        max_chars = getattr(self, "_HIST_MAX_CHARS", 40)
        for item in items:
            display = item if len(item) <= max_chars else item[:max_chars - 1] + "…"
            self.history_listbox.insert(tk.END, f"  {display}")
            self._hist_tip_items.append(item)

        # Reset scroll to top: tk.Listbox remembers the last active item and
        # auto-scrolls to it on re-populate, leaving a blank gap at the bottom.
        self.history_listbox.yview_moveto(0)

        visible_lines = min(len(items), 7)
        self.history_listbox.config(height=visible_lines)

        self.root.update_idletasks()

        x = self.search_entry.winfo_rootx()
        y = self.search_entry.winfo_rooty() + self.search_entry.winfo_height() + 10
        width  = self.search_entry.winfo_width()
        height = self.history_listbox.winfo_reqheight() + 4

        self.history_window.geometry(f"{width}x{height}+{x}+{y}")
        self.history_window.deiconify()
        self.history_window.lift()

    def hide_history_dropdown(self, event=None):
        """Hides the history popup window and its truncation tooltip."""
        if hasattr(self, 'history_window'):
            self.history_window.withdraw()
        if hasattr(self, '_hist_tooltip'):
            self._hist_tooltip.withdraw()

    def reset_search_and_focus_log(self, event=None):
        """Clears the search, hides history, and returns focus to the log area.
        Deactivates pause first so that on_search_change's refresh already runs
        with pause=False, avoiding a redundant second refresh_natural_order call.
        Also cancels any pending search worker."""
        had_query = bool(self.search_query.get())
        self.hide_history_dropdown()

        # Deactivate pause BEFORE clearing the query so that on_search_change's
        # refresh_natural_order fires with the correct (unpaused) state and
        # scrolls to end in a single pass.
        if self.is_paused.get():
            self.is_paused.set(False)
            self._last_wrap_anchor = None
            self.update_button_colors()

        # Clearing the query fires on_search_change which cancels pending search
        # and calls refresh_natural_order (scrolls to end since pause is now off).
        self.search_query.set("")

        # Extra safety: cancel any search timer/worker that might still be queued.
        self._cancel_pending_search()

        if had_query:
            # on_search_change already refreshed; just ensure we land at the bottom.
            self.root.after(0, lambda: self.txt_area.see(tk.END))
        if hasattr(self, 'txt_area'):
            self.txt_area.focus_set()
        return "break"

    def _close_dropdown_on_outside_click(self, event):
        """Closes the history dropdown when the user clicks outside it."""
        if hasattr(self, "history_listbox") and self.history_listbox.winfo_viewable():
            if event.widget != self.search_entry and event.widget != self.history_listbox:
                self.hide_history_dropdown()

    def _on_window_configure(self, event):
        """Hides the history dropdown when the main window moves or resizes."""
        if event.widget == self.root:
            if hasattr(self, "history_listbox") and self.history_listbox.winfo_viewable():
                self.hide_history_dropdown()

    def on_search_keyrelease(self, event):
        """Opens the history dropdown after entering at least one character."""
        if event.keysym in ("Up", "Down", "Return", "Escape", "Left", "Right"):
            return

        query = self.search_query.get().strip().lower()
        if len(query) >= 1:
            filtered = [item for item in self.search_history if query in item.lower()]
            if filtered:
                self.show_history_dropdown(filtered)
            else:
                self.hide_history_dropdown()
        else:
            self.hide_history_dropdown()

    def on_search_up(self, event):
        """Handles the Up arrow in the search field (navigates history dropdown)."""
        if not self.history_listbox.winfo_viewable():
            if self.search_history:
                self.show_history_dropdown()
            return "break"

        current = self.history_listbox.curselection()
        if not current:
            last_idx = self.history_listbox.size() - 1
            if last_idx >= 0:
                self.history_listbox.selection_set(last_idx)
                self.history_listbox.see(last_idx)
                self._hist_highlight_idx(last_idx)
        else:
            idx = max(0, current[0] - 1)
            self.history_listbox.selection_clear(0, tk.END)
            self.history_listbox.selection_set(idx)
            self.history_listbox.see(idx)
            self._hist_highlight_idx(idx)

        return "break"

    def on_search_down(self, event):
        """Handles the Down arrow in the search field (navigates history dropdown)."""
        if not self.history_listbox.winfo_viewable():
            if self.search_history:
                self.show_history_dropdown()
            return "break"

        current = self.history_listbox.curselection()
        if not current:
            self.history_listbox.selection_set(0)
            self._hist_highlight_idx(0)
        else:
            idx = min(current[0] + 1, self.history_listbox.size() - 1)
            self.history_listbox.selection_clear(0, tk.END)
            self.history_listbox.selection_set(idx)
            self.history_listbox.see(idx)
            self._hist_highlight_idx(idx)

        return "break"

    def on_history_select(self, event):
        """Handles item selection from the history dropdown via mouse or keyboard."""
        if event.widget == self.history_listbox and ("Button" in str(event.type) or "5" == str(event.type)):
            index = self.history_listbox.nearest(event.y)
        else:
            selection = self.history_listbox.curselection()
            if selection:
                index = selection[0]
            else:
                active_index = self.history_listbox.index("active")
                index = active_index if active_index >= 0 else 0

        if index >= 0:
            try:
                # Use the full original value from _hist_tip_items when available
                # (listbox may display a truncated version with "…").
                tip_items = getattr(self, "_hist_tip_items", [])
                if index < len(tip_items):
                    selected_text = tip_items[index]
                else:
                    selected_text = self.history_listbox.get(index).strip()
                self._apply_history_selection(selected_text)
                self.history_listbox.place_forget()
                self.search_entry.focus_set()
                self.search_entry.icursor("end")  # tk.Entry
            except Exception:
                pass

        return "break"

    def validate_and_save_search(self, event=None):
        """
        Validates the search: prioritizes a history selection if visible,
        otherwise validates the current entry text.
        """
        if self.history_listbox.winfo_viewable():
            selection = self.history_listbox.curselection()
            if selection:
                idx = selection[0]
                tip_items = getattr(self, "_hist_tip_items", [])
                if idx < len(tip_items):
                    selected_text = tip_items[idx]
                else:
                    selected_text = self.history_listbox.get(idx)
                self._apply_history_selection(selected_text)
                return "break"

        query = self.search_query.get().strip()
        if query:
            self.add_to_history(query)

        self.hide_history_dropdown()

        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])
        filter_msg = l_ui.get('filter_applied', 'Applied filter(s):')
        has_no_matches = (
            filter_msg in self.txt_area.get("1.0", tk.END) or
            len(self.txt_area.tag_ranges("filter_header")) > 0
        )

        if not has_no_matches and hasattr(self, 'txt_area'):
            self.txt_area.focus_set()
        else:
            self.search_entry.focus_set()
            self.search_entry.icursor(tk.END)  # tk.Entry

        return "break"

    def _apply_history_selection(self, text):
        """Internal: applies a history item as the current search term."""
        self.search_query.set(text)
        self.search_entry.icursor(tk.END)  # tk.Entry
        self.search_entry.focus_set()
        self.hide_history_dropdown()
        self.validate_and_save_search()

    def _exit_history_to_entry(self, event=None):
        """Hides the history list and returns focus to the search entry."""
        if self.history_listbox.winfo_viewable():
            self.hide_history_dropdown()
            self.search_entry.focus_set()
            self.search_entry.icursor(tk.END)  # tk.Entry
            return "break"
        return None

    # periodic_display_check is defined in MonitorMixin (monitor.py).
    # It handles display/resolution/DPI changes with a restart dialog.

    def scheduled_stats_update(self):
        """Periodically refreshes the footer stats while the app is running."""
        self.update_stats()
        self.root.after(5000, self.scheduled_stats_update)

    def on_mouse_wheel_font_resize(self, event):
        """Handles Ctrl+MouseWheel to resize the log font."""
        if event.delta > 0 or event.num == 4:
            self.increase_font()
        elif event.delta < 0 or event.num == 5:
            self.decrease_font()
