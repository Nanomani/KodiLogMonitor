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
                    f.write(self.txt_area.get("1.0", tk.END))
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

    def show_summary(self):
        """Displays the system summary and pauses the log scrolling."""
        if not self.check_log_loaded():
            return
        if not self.check_log_available():
            return
        if not self.log_file_path or not os.path.exists(self.log_file_path):
            return

        self.is_paused.set(True)
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
        MAX_H_LOGICAL = 440

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
            safe_close()

        def on_disable():
            if messagebox.askyesno(
                l_ui.get("upd_confirm_title", "Confirm"),
                l_ui.get("upd_confirm_msg", "Disable?")
            ):
                self.updates_enabled = False
                self.save_session()
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
        """Sets the wrap mode and refreshes only if 'All' filter is active."""
        new_mode = tk.WORD if self.wrap_mode.get() else tk.NONE
        self.txt_area.config(wrap=new_mode)

        # Immediately sync button color to new state
        if hasattr(self, "cde_wrap"):
            self.cde_wrap.configure(
                fg_color=COLOR_ACCENT if self.wrap_mode.get() else COLOR_BTN_DEFAULT
            )

        if not self.check_log_loaded() or not self.check_log_available():
            return

        if self.filter_vars.get("all") and self.filter_vars["all"].get():
            self.refresh_natural_order()

    def toggle_full_load(self):
        """
        Toggles between loading the full log file and loading only the last 1000 lines.
        Shows a warning for large files and updates UI colors accordingly.
        """
        if not self.check_log_loaded() or not self.check_log_available():
            return

        # 1. Security Check: If user tries to enable "Unlimited" on a large file
        if self.load_full_file.get():
            if self.log_file_path and os.path.exists(self.log_file_path):
                file_size_mb = os.path.getsize(self.log_file_path) / (1024 * 1024)

                if file_size_mb > DEFAULT_SECURITY_FILE_MAX_SIZE_BUTTON:
                    l = LANGS.get(self.current_lang.get(), LANGS["EN"])
                    title = l.get("perf_confirm_title", "Performance Warning")
                    default_msg = (
                        "This file is larger than 20 MB ({:.1f} MB).\n"
                        "Loading it may cause performance issues.\n\nDo you want to proceed?"
                    )
                    msg = l.get("perf_confirm_msg", default_msg).format(file_size_mb)

                    # If user cancels the action
                    if not messagebox.askyesno(title, msg):
                        self.load_full_file.set(False)  # Revert the state
                        self.update_button_colors()     # Refresh UI to "Limited" state
                        # Ensure the text is also updated back to "Limit"
                        self.retranslate_ui(refresh_monitor=False)
                        return

        # 2. Apply Visual Updates (Only reached if size is OK or user confirmed)
        self.update_button_colors()

        # Update the button text (Limit/Unlimited)
        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])
        new_text = l_ui.get("unlimited", "⚠️ Unlimited") if self.load_full_file.get() else l_ui.get("limit", "ℹ️ 1000 lines max")
        self.limit_var.set(new_text)

        # 3. Execute the heavy task (Loading file)
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
            current_x = self.txt_area.xview()[0]
            self.txt_area.see(tk.END)
            self.txt_area.xview_moveto(current_x)

        # Immediately sync button color to new state
        if hasattr(self, "cde_pause"):
            self.cde_pause.configure(
                fg_color=COLOR_DANGER if self.is_paused.get() else COLOR_BTN_DEFAULT
            )

        self.update_stats()

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
        Saves the new choice then closes the app so the user can relaunch it.
        COLOR_* constants are resolved at import time, so a full restart is needed.
        """
        _order = ["dark", "light"]
        current = self.app_theme.get()
        next_theme = _order[(_order.index(current) + 1) % len(_order)] \
                     if current in _order else "light"
        self.app_theme.set(next_theme)

        l = LANGS.get(self.current_lang.get(), LANGS["EN"])
        msg   = l.get("theme_close_msg",   "The theme has been changed.\n\nThe application will now close.\nPlease relaunch it to apply the new theme.")
        title = l.get("theme_close_title", "Theme changed")
        messagebox.showinfo(title, msg)

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
        self.load_full_file.set(not self.load_full_file.get())
        self.toggle_full_load()
        self.update_button_colors()
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
        return "break"

    def toggle_pause_from_keyboard(self, event=None):
        """Toggles pause mode using the keyboard (unless writing in search)."""
        current_focus = self.root.focus_get()
        if current_focus == self.search_entry:
            return None
        self.is_paused.set(not self.is_paused.get())
        self.toggle_pause_scroll()
        self.update_button_colors()
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

        # Sync option button colors to their BooleanVar state
        if hasattr(self, "cde_limit"):
            _active = self.load_full_file.get()
            self.cde_limit.configure(
                fg_color=LOG_COLORS["warning"] if _active else COLOR_BTN_DEFAULT,
                text_color=COLOR_TEXT_ON_ACCENT if _active else COLOR_TEXT_BRIGHT,
            )
        if hasattr(self, "cde_wrap"):
            _active = self.wrap_mode.get()
            self.cde_wrap.configure(
                fg_color=COLOR_ACCENT if _active else COLOR_BTN_DEFAULT,
                text_color=COLOR_TEXT_ON_ACCENT if _active else COLOR_TEXT_BRIGHT,
            )
        if hasattr(self, "cde_pause"):
            _active = self.is_paused.get()
            self.cde_pause.configure(
                fg_color=COLOR_DANGER if _active else COLOR_BTN_DEFAULT,
                text_color=COLOR_TEXT_ON_ACCENT if _active else COLOR_TEXT_BRIGHT,
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
        if hasattr(self, "btn_limit_tooltip") and self.btn_limit_tooltip:
            self.btn_limit_tooltip.text = l["tip_limit"]
        if hasattr(self, "btn_wrap_tooltip") and self.btn_wrap_tooltip:
            self.btn_wrap_tooltip.text = l["tip_wrap"]
        if hasattr(self, "btn_pause_tooltip") and self.btn_pause_tooltip:
            self.btn_pause_tooltip.text = l["tip_pause"]
        if hasattr(self, "btn_single_instance_tooltip") and self.btn_single_instance_tooltip:
            _tip_si_key = "tip_single_instance" if self.enable_single_instance_var else "tip_multi_instance"
            self.btn_single_instance_tooltip.text = l[_tip_si_key]
        if hasattr(self, "combo_lang_tooltip") and self.combo_lang_tooltip:
            self.combo_lang_tooltip.text = l["tip_lang"]
        if hasattr(self, "combo_kw_tooltip") and self.combo_kw_tooltip:
            self.combo_kw_tooltip.text = l["tip_kw_list"]
        if hasattr(self, "history_clear_tooltip") and self.history_clear_tooltip:
            self.history_clear_tooltip.text = l["tip_history_clear"]
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

        # --- Context menu item labels (tk.Label — stays as .config()) ---
        if hasattr(self, "menu_items"):
            self.menu_items[0].config(text=l["copy"])
            self.menu_items[1].config(text=l["sel_all"])
            self.menu_items[2].config(text=l["search_localy"])
            self.menu_items[3].config(text=l["search_google"])

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

            # On Linux (Ubuntu)
            y_offset = 4 if sys.platform != "win32" else 0

            # Calcul final du Y
            y_pos = int((self.sc(6) + y_offset) * self.scale)

            if not self.search_query.get() and not self.search_entry.focus_get() == self.search_entry:
                self.placeholder_label.place(x=int(60 * self.scale), y=y_pos)

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
        Sanitizes input and refreshes the display.
        """
        if not self.check_log_loaded():
            return
        if not self.check_log_available():
            return

        self.clean_search_input()
        query = self.search_query.get()

        if query:
            self.btn_clear_search.pack(expand=True)
        else:
            self.btn_clear_search.pack_forget()

        self.trigger_refresh()

    def clear_search(self):
        self.search_query.set("")
        self.search_entry.focus_set()  # tk.Entry / CTkEntry both support focus_set()

    def reset_search_and_focus_log(self, event=None):
        """Clears the search field, hides history, and returns focus to the log."""
        self.search_query.set("")
        if hasattr(self, 'history_listbox'):
            self.history_listbox.place_forget()
        if hasattr(self, 'txt_area'):
            self.txt_area.focus_set()
        return "break"

    def copy_selection(self):
        try:
            selected_text = self.txt_area.get(tk.SEL_FIRST, tk.SEL_LAST)
            if selected_text:
                self.root.clipboard_clear()
                self.root.clipboard_append(selected_text)
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

    def show_context_menu(self, event):
        """
        Displays the custom context menu at the mouse position.
        Dynamically toggles the Google Search option.
        """
        self.txt_area.focus_set()

        if self.show_google_search.get():
            self.google_menu_item.pack(fill="x")
        else:
            self.google_menu_item.pack_forget()

        self.context_menu.geometry(f"+{event.x_root}+{event.y_root}")
        self.context_menu.deiconify()
        self.context_menu.lift()
        self.context_menu.focus_set()
        self.context_menu.bind("<FocusOut>", lambda e: self.context_menu.withdraw())

    def show_search_context_menu(self, event):
        """Displays the search-field context menu."""
        self.context_menu.withdraw()
        self.search_context_menu.geometry(f"+{event.x_root}+{event.y_root}")
        self.search_context_menu.deiconify()
        self.search_context_menu.lift()
        self.search_context_menu.focus_set()

    def _build_search_menu_items(self):
        """Rebuilds the search-field context menu items with current language strings."""
        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])

        for widget in self.search_menu_inner.winfo_children():
            widget.destroy()

        # Paste button (tk.Label in a tk.Toplevel context menu)
        btn_paste = tk.Label(
            self.search_menu_inner,
            text=l_ui["paste"],
            bg=COLOR_BTN_DEFAULT,
            fg=COLOR_TEXT_BRIGHT,
            font=(self.main_font_family, 10),
            padx=15,
            pady=self.sc(7),
            anchor="w",
            cursor="hand2",
        )
        btn_paste.pack(fill="x")
        btn_paste.bind("<Enter>", lambda e: btn_paste.config(bg=COLOR_ACCENT, fg=COLOR_TEXT_ON_ACCENT))
        btn_paste.bind("<Leave>", lambda e: btn_paste.config(bg=COLOR_BTN_DEFAULT, fg=COLOR_TEXT_BRIGHT))
        btn_paste.bind(
            "<Button-1>",
            lambda e: [
                self.search_entry.event_generate("<<Paste>>"),  # tk.Entry
                self.search_context_menu.withdraw(),
            ],
        )

        # Clear button
        btn_clear = tk.Label(
            self.search_menu_inner,
            text=l_ui["clear"],
            bg=COLOR_BTN_DEFAULT,
            fg=COLOR_TEXT_BRIGHT,
            font=(self.main_font_family, 10),
            padx=15,
            pady=self.sc(7),
            anchor="w",
            cursor="hand2",
        )
        btn_clear.pack(fill="x")
        btn_clear.bind("<Enter>", lambda e: btn_clear.config(bg=COLOR_ACCENT, fg=COLOR_TEXT_ON_ACCENT))
        btn_clear.bind("<Leave>", lambda e: btn_clear.config(bg=COLOR_BTN_DEFAULT, fg=COLOR_TEXT_BRIGHT))
        btn_clear.bind(
            "<Button-1>",
            lambda e: [self.search_query.set(""), self.search_context_menu.withdraw()],
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
        self.limit_var.set(txt)  # uses textvariable — no .config() needed

    def copy_to_clipboard(self, event=None):
        """Copies the currently selected text from the log area to the clipboard."""
        try:
            selected_text = self.txt_area.get(tk.SEL_FIRST, tk.SEL_LAST)
            if selected_text:
                self.root.clipboard_clear()
                self.root.clipboard_append(selected_text)
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
        self.search_history = self.search_history[:15]
        self.save_search_history()

    def clear_all_history_data(self):
        """Deletes the history file and clears the in-memory list."""
        l = LANGS.get(self.current_lang.get(), LANGS["EN"])
        msg = l.get("clear_confirm_msg", "Do you want to delete all search history?")
        confirm = messagebox.askyesno(APP_NAME, msg)

        if confirm:
            try:
                history_path = ".kodi_search_history"
                if os.path.exists(history_path):
                    os.remove(history_path)
                self.search_history = []
                self.history_listbox.delete(0, tk.END)
                self.hide_history_dropdown()
                print("Search history cleared successfully.")
            except Exception as e:
                print(f"Error clearing history: {e}")

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
        for item in items:
            self.history_listbox.insert(tk.END, f"  {item}")

        visible_lines = min(len(items), 7)
        self.history_listbox.config(height=visible_lines)

        self.root.update_idletasks()

        x = self.search_entry.winfo_rootx()
        y = self.search_entry.winfo_rooty() + self.search_entry.winfo_height() + 10
        width  = self.search_entry.winfo_width()
        height = self.history_listbox.winfo_reqheight() + 2

        self.history_window.geometry(f"{width}x{height}+{x}+{y}")
        self.history_window.deiconify()
        self.history_window.lift()

    def hide_history_dropdown(self, event=None):
        """Hides the history popup window."""
        if hasattr(self, 'history_window'):
            self.history_window.withdraw()

    def reset_search_and_focus_log(self, event=None):
        """Clears the search, hides history, and returns focus to the log area."""
        self.search_query.set("")
        self.hide_history_dropdown()
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
        else:
            idx = max(0, current[0] - 1)
            self.history_listbox.selection_clear(0, tk.END)
            self.history_listbox.selection_set(idx)
            self.history_listbox.see(idx)

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
        else:
            idx = min(current[0] + 1, self.history_listbox.size() - 1)
            self.history_listbox.selection_clear(0, tk.END)
            self.history_listbox.selection_set(idx)
            self.history_listbox.see(idx)

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
                selected_text = self.history_listbox.get(selection[0])
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
        else:
            self.decrease_font()
        return "break"

