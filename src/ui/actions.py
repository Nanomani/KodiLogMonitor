import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import webbrowser
import os
import sys
import subprocess
from urllib.parse import quote

from config import *
from languages import LANGS
from utils import get_windows_theme, get_system_font
from ui.ui_builder import ToolTip

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
        """
        Saves the current content of the text area to a file chosen by the user.
        """
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
                    # Retrieve all text from the start (1.0) to the end
                    f.write(self.txt_area.get("1.0", tk.END))
            except IOError as e:
                print(f"Error exporting log: {e}")

    def upload_to_pastebin(self, event=None):
        """Copy the entire log and open paste.kodi.tv with the translation."""
        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])

        if not self.check_log_loaded():
            return

        if not self.check_log_available():
            return

        try:
            # Read the entire file
            with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Copy to clipboard
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            self.root.update()

            # Open the link
            self.open_url(self.paste_url)

            # Temporary confirmation message in the status bar
            msg_confirm = l_ui.get("copy_ok", "Log copied! Paste it on the site.")
            self.inactivity_timer_var.set(msg_confirm)

            # Deletes the message after 5 seconds
            self.root.after(5000, lambda: self.inactivity_timer_var.set(""))

        except Exception as e:
            messagebox.showerror("Erreur", f"Unable to read the file : {e}")

    def show_summary(self):
        """Displays the system summary and pauses the log to stop it from scrolling."""
        if not self.check_log_loaded():
            return

        if not self.check_log_available():
            return

        if not self.log_file_path or not os.path.exists(self.log_file_path):
            return

        self.is_paused.set(True)
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

                    # Security for large files
                    if len(summary_content) > 100:
                        break

            if summary_content:
                self.txt_area.config(state=tk.NORMAL)
                self.txt_area.delete('1.0', tk.END)

                header_title = l_ui.get("sys_sum", "\n--- RÉSUMÉ SYSTÈME ---\n")
                self.txt_area.insert(tk.END, f"{header_title}\n", "summary_color")

                for s_line in summary_content:
                    self.txt_area.insert(tk.END, s_line, "summary_color")

                self.txt_area.config(state=tk.DISABLED)
                self.txt_area.see("1.0")

        except Exception as e:
            print(f"Erreur résumé : {e}")

    def show_help(self):
        """
        Displays the help window with keyboard shortcuts.
        Adapts automatically to screen resolution and OS.
        """
        # ANTI-DOUBLE LOCK
        if hasattr(self, "help_win_active") and self.help_win_active:
            return

        self.help_win_active = True
        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])

        help_win = tk.Toplevel(self.root)
        help_win.title(l_ui.get("win_help_title", "Help"))
        help_win.configure(bg=COLOR_BG_HEADER)
        help_win.transient(self.root)
        help_win.withdraw()

        # --- INTERNAL CLOSING FUNCTION ---
        def safe_close(event=None):
            help_win.bind_all("<MouseWheel>", lambda e: None)
            try:
                help_win.grab_release()
                help_win.destroy()
            except: pass
            # Reset flag after a short delay
            self.root.after(200, lambda: setattr(self, "help_win_active", False))

        help_win.protocol("WM_DELETE_WINDOW", safe_close)
        for key in ["<Return>", "<Escape>", "<BackSpace>", "<F1>"]:
            help_win.bind(key, safe_close)

        # --- SCROLLABLE LAYOUT ---
        container = tk.Frame(help_win, bg=COLOR_BG_HEADER)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, bg=COLOR_BG_HEADER, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLOR_BG_HEADER)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # --- CONTENT ---
        # Title inside window
        tk.Label(
            scrollable_frame,
            text=l_ui.get("help_title", "Keyboard Shortcuts"),
            bg=COLOR_BG_HEADER,
            fg=COLOR_ACCENT,
            font=("Segoe UI", 14, "bold")
        ).pack(pady=(self.sc(20), self.sc(10)), fill="x")

        tk.Frame(
            scrollable_frame,
            bg=COLOR_SEPARATOR,
            height=2
        ).pack(fill="x", padx=self.sc(40))

        # Formatting help text
        raw_text = l_ui.get("help_text", "")
        formatted_lines = []
        for line in raw_text.split('\n'):
            if " : " in line:
                cmd, desc = line.split(" : ", 1)
                formatted_lines.append(f"{cmd:<12} : {desc}")
            else:
                formatted_lines.append(line)

        # TEXT LABEL
        # Note: pady is removed from Label config and moved to .pack() to avoid TclError
        help_label = tk.Label(
            scrollable_frame,
            text="\n".join(formatted_lines).strip(),
            bg=COLOR_BG_HEADER,
            fg=COLOR_TEXT_MAIN,
            justify="left",
            font=("Consolas", 11),
            padx=self.sc(40)
        )
        # We put the padding here (top=20, bottom=60) to ensure the last line is visible
        help_label.pack(
            fill="both",
            expand=True,
            pady=(self.sc(20), self.sc(60))
        )

        # OK Button at the bottom (fixed)
        btn_frame = tk.Frame(help_win, bg=COLOR_BG_HEADER)
        btn_frame.pack(side="bottom", fill="x", pady=self.sc(20))

        btn_close = tk.Button(
            btn_frame,
            text="Ok",
            command=safe_close,
            bg=COLOR_BTN_DEFAULT,
            fg=COLOR_TEXT_MAIN,
            font=("Segoe UI", 10, "bold"),
            relief="flat", width=15, pady=5,
            cursor="hand2",
            activebackground=COLOR_BTN_ACTIVE,
            activeforeground=COLOR_TEXT_MAIN,
            highlightthickness=0,
            bd=0
        )
        btn_close.pack()

        # --- HOVER EFFECT ---
        def on_enter(e):
            btn_close.config(bg=COLOR_BTN_ACTIVE)

        def on_leave(e):
            btn_close.config(bg=COLOR_BTN_DEFAULT)

        btn_close.bind("<Enter>", on_enter)
        btn_close.bind("<Leave>", on_leave)

        # --- FINAL SIZING LOGIC ---
        help_win.update_idletasks()

        req_w = scrollable_frame.winfo_reqwidth()
        # Generous buffer for height to avoid cutting the button
        req_h = scrollable_frame.winfo_reqheight() + 110

        screen_h = help_win.winfo_screenheight()
        max_h = int(screen_h * 0.85)

        if req_h > max_h:
            final_h, final_w = max_h, req_w + 35
            scrollbar.pack(side="right", fill="y")
            canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        else:
            final_h, final_w = req_h, req_w
            canvas.configure(scrollregion=(0, 0, final_w, final_h))

        canvas.pack(side="left", fill="both", expand=True)

        # Centering relative to root
        pos_x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (final_w // 2)
        pos_y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (final_h // 2)

        help_win.geometry(f"{final_w}x{final_h}+{max(0, pos_x)}+{max(0, pos_y)}")

        # Windows Dark Mode Title Bar
        if sys.platform == "win32":
            try:
                from ctypes import windll, byref, sizeof, c_int
                hwnd = windll.user32.GetParent(help_win.winfo_id())
                is_dark = 1 if COLOR_BG_MAIN.lower() == COLOR_BG_MAIN else 0
                windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, byref(c_int(is_dark)), sizeof(c_int(is_dark)))
                color = 0x2d2d2d if is_dark else 0xFFFFFF
                windll.dwmapi.DwmSetWindowAttribute(hwnd, 34, byref(c_int(color)), sizeof(c_int(color)))
            except: pass

        help_win.deiconify()
        if sys.platform != "win32":
            help_win.update()

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
                from urllib.error import URLError # Import to handle the connection error

                req = urllib.request.Request(url, headers={'User-Agent': 'KodiLogMonitor-App'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode())
                    latest_v = data.get("tag_name", "")

                    if latest_v and latest_v != APP_VERSION and latest_v != self.skip_version:
                        self.root.after(0, lambda: self._show_update_dialog(latest_v, data.get("html_url")))

            except URLError as e:
                pass
            except Exception as e:
                print(f"Update check skipped (reason: {e})")

        threading.Thread(target=_check, daemon=True).start()

    def _show_update_dialog(self, new_version, url):
        """Auto-adaptive refresh rate notification (HD/4K) and centered buttons."""
        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])

        upd_win = tk.Toplevel(self.root)
        upd_win.title(l_ui.get("upd_title", "Update Available"))
        upd_win.configure(bg=COLOR_BG_HEADER)
        upd_win.transient(self.root)
        upd_win.withdraw()

        # --- SECURE CLOSING FUNCTION ---
        def safe_close(event=None): # Ajout de 'event' pour accepter les binds
            try:
                upd_win.grab_release()
                upd_win.destroy()
            except: pass

        upd_win.protocol("WM_DELETE_WINDOW", safe_close)

        # --- ADDING KEYBOARD SHORTCUTS ---
        for key in ["<Return>", "<Escape>", "<BackSpace>"]:
            upd_win.bind(key, safe_close)

        # --- UTILITY FUNCTION FOR HOVER ---
        def apply_standard_hover(btn):
            btn.bind("<Enter>", lambda e: btn.config(bg=COLOR_BTN_ACTIVE))
            btn.bind("<Leave>", lambda e: btn.config(bg=COLOR_BTN_DEFAULT))

        # --- MAIN CONTAINER ---
        # We use generous padding to prevent the text from sticking to the edges
        main_frame = tk.Frame(upd_win, bg=COLOR_BG_HEADER, padx=self.sc(40), pady=self.sc(20))
        main_frame.pack(fill="both", expand=True)

        # Title
        tk.Label(
            main_frame,
            text=f"{l_ui.get('upd_new_ver', 'NEW VERSION:')} {new_version}",
            bg=COLOR_BG_HEADER,
            fg=COLOR_ACCENT,
            font=("Segoe UI", 12, "bold")).pack(pady=(0, 15)
        )

        tk.Frame(main_frame, bg=COLOR_SEPARATOR, height=2).pack(fill="x", padx=0)

        tk.Label(
            main_frame,
            text=l_ui.get("upd_msg", ""),
            bg=COLOR_BG_HEADER,
            fg=COLOR_TEXT_MAIN,
            font=("Segoe UI", 10), justify="center").pack(fill="both", expand=True, pady=(self.sc(10), self.sc(20))
        )

        # --- BUTTON AREA CENTERED ---
        # 1. The outer frame that spans the entire width at the bottom
        outer_btn_frame = tk.Frame(upd_win, bg=COLOR_BG_HEADER)
        outer_btn_frame.pack(side="bottom", fill="x", pady=(0, self.sc(25)))

        # 2. The inner frame that contains the buttons (centered by default in `outer_btn_frame`)
        inner_btn_frame = tk.Frame(outer_btn_frame, bg=COLOR_BG_HEADER)
        inner_btn_frame.pack(side="top") # Sans fill="x", il reste centré

        def on_open():
            self.open_url(url)
            safe_close()

        def on_skip():
            self.skip_version = new_version
            self.save_session()
            safe_close()

        def on_disable():
            if messagebox.askyesno(l_ui.get("upd_confirm_title", "Confirm"),
                                  l_ui.get("upd_confirm_msg", "Disable?")):
                self.updates_enabled = False
                self.save_session()
                safe_close()

        btn_style = {
            "bg": COLOR_BTN_DEFAULT,
            "fg": COLOR_TEXT_MAIN,
            "font": ("Segoe UI", 10, "bold"),
            "relief": "flat",
            "width": 15,
            "pady": 5,
            "cursor": "hand2",
            "activebackground": COLOR_BTN_ACTIVE,
            "activeforeground": COLOR_TEXT_MAIN,
            "highlightthickness": 0,
            "bd": 0
        }

        # Button DOWNLOAD
        btn_dl = tk.Button(inner_btn_frame, text=l_ui.get("upd_btn_dl", "DOWNLOAD"), command=on_open, **btn_style)
        btn_dl.pack(side="left", padx=self.sc(10))
        apply_standard_hover(btn_dl)
        ToolTip(btn_dl, l_ui.get("tip_upd_dl", "Download the update from GitHub"), self.scale)

        # Button SKIP
        btn_skip = tk.Button(inner_btn_frame, text=l_ui.get("upd_btn_skip", "SKIP"), command=on_skip, **btn_style)
        btn_skip.pack(side="left", padx=self.sc(10))
        apply_standard_hover(btn_skip)
        ToolTip(btn_skip, l_ui.get("tip_upd_sk", "Ignore notifications for this version"), self.scale)

        # Button DISABLE
        btn_disable = tk.Button(inner_btn_frame, text=l_ui.get("upd_btn_dis", "DISABLE"), command=on_disable, **btn_style)
        btn_disable.pack(side="left", padx=self.sc(10))
        apply_standard_hover(btn_disable)
        ToolTip(btn_disable, l_ui.get("tip_upd_di", "Permanently disable notifications"), self.scale)

        # --- DYNAMIC SIZE CALCULATION (SHOW_HELP LOGIC) ---
        upd_win.update_idletasks()

        # We ask the window what size it "wants" to be based on its content
        # We add a small safety margin (buffer)
        final_w = upd_win.winfo_reqwidth() + 20
        final_h = upd_win.winfo_reqheight() + 10

        # Centered relative to the main window
        pos_x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (final_w // 2)
        pos_y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (final_h // 2)

        upd_win.geometry(f"{final_w}x{final_h}+{max(0, pos_x)}+{max(0, pos_y)}")

        # Dark Mode Title Bar (Windows)
        if sys.platform == "win32":
            try:
                from ctypes import windll, byref, sizeof, c_int
                hwnd = windll.user32.GetParent(upd_win.winfo_id())
                is_dark = 1
                windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, byref(c_int(is_dark)), sizeof(c_int(is_dark)))
                color = 0x2d2d2d
                windll.dwmapi.DwmSetWindowAttribute(hwnd, 34, byref(c_int(color)), sizeof(c_int(color)))
            except: pass

        upd_win.deiconify()
        upd_win.grab_set()
        upd_win.focus_force()

    def check_log_loaded(self):
        """Check if a log file is loaded; if not, display the message 'no_log'."""
        if not self.log_file_path:
            self.txt_area.config(state=tk.NORMAL)
            self.txt_area.delete('1.0', tk.END)

            l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])

            # Configure tags for colored text
            self.txt_area.tag_configure("no_log_text", foreground=LOG_COLORS["error"], font=(self.mono_font_family, self.font_size, "bold"))

            # Message with spacing
            self.txt_area.insert(tk.END, "\n\n\n\n\t\t")
            self.txt_area.insert(tk.END, l_ui.get('no_log', 'No LOG file loaded.'), "no_log_text")

            self.txt_area.config(state=tk.DISABLED)
            return False
        return True

    def check_log_available(self):
        """
        Checks if the file is physically accessible.
        If it returns to normal, clears the error messages.
        """
        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])
        err_msg = l_ui.get('file_error', '⚠️ LOG INACCESSIBLE')

        if self.log_file_path:
            if not os.path.exists(self.log_file_path):
                # --- ERROR CASE ---
                self.txt_area.config(state=tk.NORMAL)
                self.txt_area.delete('1.0', tk.END)
                self.txt_area.tag_configure("file_err_text", foreground=LOG_COLORS["error"], font=(self.mono_font_family, self.font_size, "bold"))
                self.txt_area.insert(tk.END, "\n\n\n\n\t\t")
                self.txt_area.insert(tk.END, err_msg, "file_err_text")
                self.txt_area.config(state=tk.DISABLED)

                self.inactivity_timer_var.set(err_msg)
                self.update_status_color(COLOR_DANGER)
                return False
            else:
                # --- RETURN TO NORMAL CASE ---
                # If the current footer message is the error, clear it
                if self.inactivity_timer_var.get() == err_msg:
                    self.inactivity_timer_var.set("")
                    self.update_status_color(COLOR_ACCENT)

        return True

    def on_list_change(self, *args):
        """Triggered when the selection in the keyword list changes."""
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
        # 1. Update the Text widget wrap mode
        new_mode = tk.WORD if self.wrap_mode.get() else tk.NONE
        self.txt_area.config(wrap=new_mode)

        # 2. Basic safety checks
        if not self.check_log_loaded() or not self.check_log_available():
            return

        # 3. Refresh display ONLY if the 'all' filter is active
        # This prevents unnecessary re-insertions when viewing filtered logs
        if self.filter_vars.get("all") and self.filter_vars["all"].get():
            self.refresh_natural_order()

    def toggle_full_load(self):
        """
        Toggles between loading the full log file and loading only the last 1000 lines.
        """
        if not self.check_log_loaded():
            return

        if not self.check_log_available():
            return

        # Check if the user is attempting to ENABLE the unlimited mode.
        if self.load_full_file.get():
            if self.log_file_path and os.path.exists(self.log_file_path):
                file_size_mb = os.path.getsize(self.log_file_path) / (1024 * 1024)

                if file_size_mb > DEFAULT_SECURITY_FILE_MAX_SIZE_BUTTON:
                    l = LANGS.get(self.current_lang.get(), LANGS["EN"])
                    title = l.get("perf_confirm_title", "Performance Warning")
                    default_msg = "This file is larger than 20 MB ({:.1f} MB).\nLoading it may cause performance issues.\n\nDo you want to proceed?"
                    msg = l.get("perf_confirm_msg", default_msg).format(file_size_mb)

                    from tkinter import messagebox
                    if not messagebox.askyesno(title, msg):
                        self.load_full_file.set(False)
                        return

        # --- STEP 1: FORCE IMMEDIATE UI UPDATE BEFORE LOADING ---
        # Get translations
        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])

        # Determine the text to display
        if self.load_full_file.get():
            new_text = l_ui.get("unlimited", "⚠️ Unlimited")
        else:
            new_text = l_ui.get("limit", "ℹ️ 1000 lines max")

        # Apply the text to the label immediately
        if hasattr(self, 'label_limit'):
            self.label_limit.config(text=new_text)

        # CRITICAL: Tell Tkinter to redraw the screen NOW, before starting the file load
        self.root.update_idletasks()

        # --- STEP 2: START MONITORING (This part can take time) ---
        if self.log_file_path:
            # We pass is_manual=True to allow full loading.
            self.start_monitoring(self.log_file_path, is_manual=True)

        self.save_session()

    def toggle_pause_scroll(self):
        if not self.check_log_loaded():
            return

        if not self.check_log_available():
            return

        if not self.is_paused.get() and self.log_file_path:
            # Get current horizontal position
            current_x = self.txt_area.xview()[0]

            # Scroll to the end vertically
            self.txt_area.see(tk.END)

            # Restore the horizontal position
            self.txt_area.xview_moveto(current_x)
        self.update_stats()

    def toggle_single_instance(self):
        """
        Toggles the ENABLE_SINGLE_INSTANCE global variable and updates the UI button.
        """
        global ENABLE_SINGLE_INSTANCE

        self.enable_single_instance_var = not self.enable_single_instance_var
        new_icon = "🔒" if self.enable_single_instance_var else "🔓"
        self.btn_single_instance.config(text=new_icon)

        import config as config_module
        config_module.ENABLE_SINGLE_INSTANCE = self.enable_single_instance_var

        self.save_session()

        # RESUME THE CHECK AFTER 100 ms
        self.root.after(100, lambda: self._reinit_single_instance())

    def _reinit_single_instance(self):
        """Réinitialise le listener single instance."""
        from utils import check_single_instance
        # This will re-read the file and restart the listener
        check_single_instance()

    def sync_config_on_focus(self):
        """
        Reloads the single instance state only when the user interacts with the window.
        Uses a safer approach to avoid overwriting with default values.
        """
        global ENABLE_SINGLE_INSTANCE

        if not os.path.exists(CONFIG_FILE):
            return

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                # Read lines and filter out empty ones
                lines = [l.strip() for l in f.readlines() if l.strip()]

                # Check if we have the expected number of lines
                if len(lines) >= 17:
                    # Extract only the value before the comment
                    val_part = lines[16].split('#')[0].strip()

                    # Safety: ensure the value is actually "1" or "0"
                    if val_part in ["0", "1"]:
                        new_state = (val_part == "1")

                        # Only update if there is a real change to avoid UI flickering
                        if not hasattr(self, "enable_single_instance_var") or self.enable_single_instance_var != new_state:
                            self.enable_single_instance_var = new_state
                            ENABLE_SINGLE_INSTANCE = new_state

                            # Update the button icon if it exists
                            if hasattr(self, "btn_single_instance"):
                                self.btn_single_instance.config(text="🔒" if new_state else "🔓")
        except Exception as e:
            print(f"Debug: sync_config_on_focus error: {e}")

    def select_show_summary_from_keyboard(self, event=None):
        """Simulates clicking the ALL filter button using the keyboard"""
        current_focus = self.root.focus_get()
        if current_focus == self.search_entry:
            return None

        if event and (event.state & 0x4):
            return "break"

        self.show_summary()
        return "break"

    def select_clear_console_from_keyboard(self, event=None):
        """Simulates clicking CLEAR CONSOLE button using the keyboard"""
        self.clear_console()
        return "break"

    def toggle_limit_from_keyboard(self, event=None):
        """Switch between limited mode (1000 lines) and full mode using the 'i' key."""
        # current_focus = self.root.focus_get()
        # if current_focus == self.search_entry:
            # return None

        # if event and (event.state & 0x4):
            # return "break"

        self.load_full_file.set(not self.load_full_file.get())
        self.toggle_full_load()
        return "break"

    def select_all_filter_from_keyboard(self, event=None):
        """Simulates clicking the ALL filter button using the keyboard"""
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
        """Toggles the INFO filter and refreshes the interface."""
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
        """Toggles the WARNING filter and refreshes the interface."""
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
        """Toggles the ERROR filter and refreshes the interface."""
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
        """Toggles the DEBUG filter and refreshes the interface."""
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
        """Toggles line break mode unless writing in search."""
        self.wrap_mode.set(not self.wrap_mode.get())
        self.toggle_line_break()
        return "break"

    def toggle_pause_from_keyboard(self, event=None):
        """Toggles pause mode unless writing in search."""
        current_focus = self.root.focus_get()
        if current_focus == self.search_entry:
            return None

        self.is_paused.set(not self.is_paused.get())
        self.toggle_pause_scroll()
        return "break"

    def select_reset_all_filters_from_keyboard(self, event=None):
        """Simulates clicking the RESET button via the keyboard"""
        self.root.focus_set()
        self.reset_all_filters()
        return "break"

    def focus_search_entry(self, event=None):
        """Gives focus to the search field and selects the existing text."""
        self.search_entry.focus_set()
        self.search_entry.selection_range(0, tk.END)
        return "break"

    def refocus_log(self, event=None):
        """Redonne le focus à la zone de log après une sélection."""
        self.txt_area.focus_set()

    # === FILTER ===
    # Button ALL

    def on_filter_toggle(self, mode):
        """Stabilized filtering logic."""
        if mode == "all":
            if self.filter_vars["all"].get():
                # Specific filters are disabled without triggering trigger_refresh.
                for m in ["debug", "info", "warning", "error"]:
                    self.filter_vars[m].set(False)

                # Force clean reload (like RESET)
                self.refresh_natural_order()
            else:
                # Security: You cannot uncheck ALL if there is no other filter.
                if not any(
                    self.filter_vars[m].get()
                    for m in ["debug", "info", "warning", "error"]
                ):
                    self.filter_vars["all"].set(True)
        else:
            # If INFO, WARN, etc. are enabled, the "ALL" mode is disabled.
            if self.filter_vars[mode].get():
                self.filter_vars["all"].set(False)

            # If nothing is checked, we go back to EVERYTHING.
            if not any(self.filter_vars[m].get() for m in self.filter_vars):
                self.filter_vars["all"].set(True)
                self.refresh_natural_order()
            else:
                self.trigger_refresh()

        self.update_button_colors()

    def reset_all_filters(self):
        """Resets everything with a single click."""
        # 0. The focus is removed from the search field and returned to the main window.
        self.root.focus_set()

        # 1. Stop searching and clear the bar
        self.search_query.set("")

        # 2. Resets the variable associated with the list
        self.selected_list.set("")

        # 3. Forces the visual display to "None" (or "Aucun" depending on your language)
        # We retrieve the correct translation of "None" defined in your LANGS dictionary
        lang_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])
        none_text = lang_ui.get("none", "None")
        self.combo_lists.set(none_text)

        # 4. Reset filter variables (without triggering trigger_refresh immediately)
        for mode in ["info", "warning", "error", "debug"]:
            self.filter_vars[mode].set(False)
        self.filter_vars["all"].set(True)

        # 5. CRITICAL RESET OF THE PAUSE BUTTON
        self.is_paused.set(False)
        if hasattr(self, "btn_pause"):
            self.btn_pause.config(
                text="⏸ PAUSE", bg=COLOR_BTN_DEFAULT, activebackground="white"
            )

        # 6. Force update of filter button colors
        self.update_button_colors()

        # 7. THE DOUBLE-CLICK SOLUTION:
        # We force Tkinter to process pending events before continuing.
        self.root.update_idletasks()

        # 8. Clear the cache of lines to start from scratch
        self.seen_lines.clear()

        # 9. Reload display (Natural order as discussed)
        self.refresh_natural_order()

        # 10. Ensure that the text box scrolls down properly since the pause has been lifted.
        self.txt_area.see(tk.END)

    def update_button_colors(self):
        """Applies background colors according to the status of each filter."""
        for mode, var in self.filter_vars.items():
            widget = self.filter_widgets.get(mode)
            if widget:
                if var.get():
                    # Active color (Blue for All, Green for Info, etc.)
                    active_color = self.filter_colors.get(mode, COLOR_ACCENT)
                    widget.config(bg=active_color, selectcolor=active_color)
                else:
                    # Neutral color (Gray)
                    widget.config(bg=COLOR_BTN_DEFAULT, selectcolor=COLOR_BTN_DEFAULT)

    def update_filter_button_colors(self):
        for mode, cb in self.filter_widgets.items():
            if self.filter_vars[mode].get():
                bg = self.filter_colors[mode]
                cb.config(bg=bg, selectcolor=bg)
            else:
                cb.config(bg=COLOR_BTN_DEFAULT, selectcolor=COLOR_BTN_DEFAULT)

    def on_hover_filter(self, widget, mode, is_entering):
        """
        Handles the visual feedback when the mouse hovers over or leaves a filter button.

        This method updates the background color of the filter buttons to provide
        an interactive feel. It distinguishes between the 'active' (selected) state
        and the 'inactive' state to ensure the current filtering status remains visible.

        Args:
            event (tk.Event): The Tkinter event object (Enter or Leave).
            tag (str): The log level associated with the button (e.g., 'error', 'warning').
            state (str): The hover state, either 'enter' (mouse over) or 'leave' (mouse out).
        """
        if is_entering:
            # Hover color (light gray, for example)
            widget.config(bg=COLOR_BTN_ACTIVE)
        else:
            # Return to normal state (either the filter color or default gray)
            if self.filter_vars[mode].get():
                color = self.filter_colors.get(mode, COLOR_ACCENT)
                widget.config(bg=color)
            else:
                widget.config(bg=COLOR_BTN_DEFAULT)

    def on_list_selected(self, event=None):
        if not self.check_log_loaded():
            return

        if not self.check_log_available():
            return

        selection = self.selected_list.get()
        # The language dictionary is retrieved only once for clarity.
        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])

        if not selection or selection == l_ui["none"]:
            self.trigger_refresh()
            return

        # 1. Using the "search_ph" translation for the loading message
        search_text = l_ui["search_ph"]
        self.show_loading(True, message=search_text)

        # 2. Micro-delay for processing
        self.root.after(300, lambda: self._process_keyword_search(selection))

    def _process_keyword_search(self, selection):
        """Internal method for performing the actual search"""
        try:
            # After processing, the UI is refreshed.
            self.trigger_refresh()
        finally:
            # Hide the message once finished
            self.show_loading(False)

    def refresh_keyword_list(self, trigger_monitor=True):
        l = LANGS.get(self.current_lang.get(), LANGS["EN"])
        files = [
            f.replace(".txt", "") for f in os.listdir(KEYWORD_DIR) if f.endswith(".txt")
        ]
        self.combo_lists["values"] = [l["none"]] + sorted(files)
        if self.selected_list.get() not in self.combo_lists["values"]:
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
        Handles the language change when an item is selected in the combobox.
        Removes padding spaces before processing the translation.
        """
        # 1. Get the current value and remove the 2 padding spaces
        selected_val = self.current_lang.get().strip()

        # 2. Update the variable with the clean value
        # (This ensures self.current_lang contains "FR" and not "  FR")
        self.current_lang.set(selected_val)

        # 3. Standard UI logic
        self.combo_lang.selection_clear()
        self.root.focus_set()

        # 4. Retranslate and save
        self.retranslate_ui(True)
        self.save_session()

    def retranslate_ui(self, refresh_monitor=True):
        l = LANGS.get(self.current_lang.get(), LANGS["EN"])
        self.btn_log.config(text=l["log"])
        self.btn_sum.config(text=l["sum"])
        self.btn_exp.config(text=l["exp"])
        self.btn_upl.config(text=l["upl"])
        self.btn_clr.config(text=l["clr"])

        # Button reset
        if hasattr(self, "btn_reset"):
            self.btn_reset.config(text=l.get("btn_reset", "↻ RESET"))

        # Button open Tooltip
        if hasattr(self, "btn_open_tooltip") and self.btn_open_tooltip:
            self.btn_open_tooltip.text = l["tip_open"]

        # Button export Tooltip
        if hasattr(self, "btn_export_tooltip") and self.btn_export_tooltip:
            self.btn_export_tooltip.text = l["tip_export"]

        # Button upload Tooltip
        if hasattr(self, "btn_upload_tooltip") and self.btn_upload_tooltip:
            self.btn_upload_tooltip.text = l["tip_upload"]

        # Button summary Tooltip
        if hasattr(self, "btn_summary_tooltip") and self.btn_summary_tooltip:
            self.btn_summary_tooltip.text = l["tip_summary"]

        # Button clear Tooltip
        if hasattr(self, "btn_clear_tooltip") and self.btn_clear_tooltip:
            self.btn_clear_tooltip.text = l["tip_clear"]

        # Button limite Tooltip
        if hasattr(self, "btn_limit_tooltip") and self.btn_limit_tooltip:
            self.btn_limit_tooltip.text = l["tip_limit"]

        # Button wrap Tooltip
        if hasattr(self, "btn_wrap_tooltip") and self.btn_wrap_tooltip:
            self.btn_wrap_tooltip.text = l["tip_wrap"]

        # Button pause Tooltip
        if hasattr(self, "btn_pause_tooltip") and self.btn_pause_tooltip:
            self.btn_pause_tooltip.text = l["tip_pause"]

        # Button instance Tooltip
        if hasattr(self, "btn_single_instance_tooltip") and self.btn_single_instance_tooltip:
            self.btn_single_instance_tooltip.text = l["tip_single_instance"]

        # Language selection list Tooltip
        if hasattr(self, "combo_lang_tooltip") and self.combo_lang_tooltip:
            self.combo_lang_tooltip.text = l["tip_lang"]

        # keyword list selection list Tooltip
        if hasattr(self, "combo_kw_tooltip") and self.combo_kw_tooltip:
            self.combo_kw_tooltip.text = l["tip_kw_list"]

        # Search clear liste Tooltip
        if hasattr(self, "history_clear_tooltip") and self.history_clear_tooltip:
            self.history_clear_tooltip.text = l["tip_history_clear"]

        # Search by keyword Tooltip
        if hasattr(self, "search_bar_tooltip") and self.search_bar_tooltip:
            self.search_bar_tooltip.text = l["tip_search_bar"]

        # Button help Tooltip
        if hasattr(self, "btn_help_tooltip") and self.btn_help_tooltip:
            self.btn_help_tooltip.text = l["tip_help"]

        # Button reset Tooltip
        if hasattr(self, "btn_reset_tooltip") and self.btn_reset_tooltip:
            # self.btn_reset_tooltip.text = l.get("tip_reset", "Restore all default settings")
            self.btn_reset_tooltip.text = l["tip_reset"]

        # Button down font size
        if hasattr(self, "btn_down_font_tooltip") and self.btn_down_font_tooltip:
            self.btn_down_font_tooltip.text = l["tip_down_font"]

        # Button up font size
        if hasattr(self, "btn_up_font_tooltip") and self.btn_up_font_tooltip:
            self.btn_up_font_tooltip.text = l["tip_up_font"]

        # Button refresh keyword list
        if hasattr(self, "btn_kw_refresh_tooltip") and self.btn_kw_refresh_tooltip:
            self.btn_kw_refresh_tooltip.text = l["tip_kw_refresh"]

        # Button folder keyword list
        if hasattr(self, "btn_kw_folder_tooltip") and self.btn_kw_folder_tooltip:
            self.btn_kw_folder_tooltip.text = l["tip_kw_folder"]

        # Message file is currently marked as inaccessible
        if getattr(self, "is_file_inaccessible", False):
            msg = l.get("file_error", "⚠️ LOG INACCESSIBLE!")
            self.inactivity_timer_var.set(msg)

        # GitHub Tooltip Update
        if hasattr(self, "github_tooltip") and self.github_tooltip:
            self.github_tooltip.text = l["tip_github"]

        # --- TRANSLATION OF FILTER ---
        tm = {
            "all": "all",
            "info": "info",
            "warning": "warn",
            "error": "err",
            "debug": "debug",
        }
        for mode, cb in self.filter_widgets.items():
            cb.config(text=l[tm[mode]])

        # --- TRANSLATION OF FILTER TOOLTIPS ---
        for mode, tooltip in self.filter_tooltips.items():
            if tooltip:
                tip_key = f"tip_filter_{mode}"
                tooltip.text = l[tip_key]

        self.footer_var.set(
            l["sel"] if not self.log_file_path else f"📍 {self.log_file_path}"
        )
        self.refresh_keyword_list(trigger_monitor=refresh_monitor)
        self.update_stats()
        self.update_filter_button_colors()
        self._build_search_menu_items()

        if hasattr(self, "menu_items"):
            self.menu_items[0].config(text=l["copy"])
            self.menu_items[1].config(text=l["sel_all"])
            self.menu_items[2].config(text=l["search_localy"])
            self.menu_items[3].config(text=l["search_google"])

        # 1. We create a dictionary of all existing translations into English
        reverse_theme_map = {}
        for lang_code in LANGS:
            ld = LANGS[lang_code]
            reverse_theme_map[ld["t_auto"]] = "Auto"
            reverse_theme_map[ld["t_light"]] = "Light"
            reverse_theme_map[ld["t_dark"]] = "Dark"

        # 2. We retrieve the current value (e.g., "Sombre") and find its technical equivalent ("Dark")
        current_val = self.theme_mode.get()
        tech_value = reverse_theme_map.get(current_val, current_val)

        # 3. We are updating the list of options with the new language
        theme_values = [l["t_auto"], l["t_light"], l["t_dark"]]
        self.combo_theme['values'] = theme_values

        # 4. The translation is reapplied in the new language for the fixed field
        new_mapping = {"Auto": l["t_auto"], "Light": l["t_light"], "Dark": l["t_dark"]}
        self.theme_mode.set(new_mapping.get(tech_value, tech_value))

        # Is paused
        if self.is_paused.get():
            self.paused_var.set(l["paused"])
        else:
            self.paused_var.set("")

        # Is wraped
        if self.wrap_mode.get():
            self.wrap_var.set(l["line_break"])
        else:
            self.wrap_var.set("")

        # Is limited 1000 line
        if not self.load_full_file.get():
            self.limit_var.set(l["limit"])
        else:
            self.limit_var.set("")

        self.update_stats()

    def on_theme_change(self, event=None):
        """
        Applies the Windows theme (Dark/Light) based on the selected option.
        Cleans padding spaces from the selection.
        """
        if sys.platform != "win32":
            return

        # 1. Get the value and remove the padding spaces
        raw_selection = self.theme_mode.get()
        selection = raw_selection.strip()

        # 2. Update the variable with the clean value
        self.theme_mode.set(selection)

        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])

        # 3. Compare with localized strings (now using the clean 'selection')
        if selection == l_ui.get("t_dark"):
            mode = 1  # Dark
        elif selection == l_ui.get("t_light"):
            mode = 0  # Light
        else:
            # For "System" or any other value
            from utils import get_windows_theme
            mode = get_windows_theme()

        try:
            from ctypes import windll, byref, sizeof, c_int
            hwnd = windll.user32.GetParent(self.root.winfo_id())

            # Attribute 20: Immersive Dark Mode
            windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 20, byref(c_int(mode)), sizeof(c_int(mode))
            )

            # Update the title bar color (34)
            # 0x002d2d2d is the dark gray used in your interface
            caption_color = c_int(0x002d2d2d) if mode == 1 else c_int(0x00FFFFFF)
            windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 34, byref(caption_color), sizeof(caption_color)
            )

            self.root.update()
        except Exception as e:
            print(f"Error during theme change: {e}")

        # 4. UI Polish and saving
        self.combo_theme.selection_clear()
        self.root.focus_set()

        # Ensure session is saved with the clean theme name
        self.save_session()

    def get_windows_theme():
        """Détecte si Windows est en mode sombre (1) ou clair (0)."""
        if sys.platform != "win32":
            return 1
        try:
            import winreg
            registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return 0 if value == 1 else 1
        except:
            return 1

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
        if show:
            # If a specific message is passed (e.g., "Search..."), it is displayed.
            if message:
                self.loading_label.config(text=message)
            else:
                self.loading_label.config(
                    text=LANGS[self.current_lang.get()]["loading"]
                )

            self.overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.root.update_idletasks()
        else:
            self.overlay.place_forget()

    def on_search_change(self, *args):
        """
        Triggered on every keystroke in the search field.
        Cleans the input and refreshes the display.
        """
        if not self.check_log_loaded():
            return

        if not self.check_log_available():
            return

        # 1. Force the security cleanup (one line, max length, etc.)
        # This ensures self.search_query.get() returns clean data immediately
        self.clean_search_input()

        # 2. Get the cleaned query
        query = self.search_query.get()

        # 3. Update 'X' button visibility inside the fixed container
        # We use pack() inside the container; the container itself never moves.
        if query:
            self.btn_clear_search.pack(expand=True)
        else:
            self.btn_clear_search.pack_forget()

        # 4. Trigger the actual search/refresh
        self.trigger_refresh()

    def clear_search(self):
        self.search_query.set("")
        self.search_entry.focus()

    def reset_search_and_focus_log(self, event=None):
        """
        Clears the search field, hides the history, and returns focus to the log.
        """
        # 1. Clear the search text variable
        self.search_query.set("")

        # 2. Hide the history dropdown if it's visible
        if hasattr(self, 'history_listbox'):
            self.history_listbox.place_forget()

        # 3. Return focus to the log area (txt_area)
        if hasattr(self, 'txt_area'):
            self.txt_area.focus_set()

        # 4. CRITICAL: 'break' prevents other binds from firing
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
        Gets the selected text from the text area, updates the search field,
        focuses it, and triggers the local log search.
        """
        try:
            # 1. Get the selected text from the text area
            selected_text = self.txt_area.get(tk.SEL_FIRST, tk.SEL_LAST).strip()

            if selected_text:
                # 2. Update the search field with the selected text
                self.search_query.set(selected_text)

                # 3. Trigger the search automatically (this will move focus to log area)
                self.validate_and_save_search()

                # 4. Re-grab the focus and move cursor to the end of the search entry
                self.search_entry.focus_set()
                self.search_entry.icursor(tk.END)

        except tk.TclError:
            # Handle the case where no text is selected (Tkinter throws a TclError)
            pass

    def show_context_menu(self, event):
        """
        Displays the custom context menu at the mouse position and
        dynamically toggles the Google Search option based on config.
        """
        self.txt_area.focus_set()

        # Show or hide the Google Search item based on the user's preference
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
        # Hide the other menu if it is open
        self.context_menu.withdraw()

        # The search menu is displayed.
        self.search_context_menu.geometry(f"+{event.x_root}+{event.y_root}")
        self.search_context_menu.deiconify()
        self.search_context_menu.lift()
        self.search_context_menu.focus_set()

    def _build_search_menu_items(self):
        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])

        for widget in self.search_menu_inner.winfo_children():
            widget.destroy()

        # Paste button
        btn_paste = tk.Label(
            self.search_menu_inner,
            text=l_ui["paste"],
            bg=COLOR_BTN_DEFAULT,
            fg=COLOR_TEXT_BRIGHT,
            font=(self.main_font_family, 10),
            padx=15,
            pady=7,
            anchor="w",
            cursor="hand2",
        )

        btn_paste.pack(fill="x")
        btn_paste.bind("<Enter>", lambda e: btn_paste.config(bg=COLOR_ACCENT))
        btn_paste.bind("<Leave>", lambda e: btn_paste.config(bg=COLOR_BTN_DEFAULT))
        btn_paste.bind(
            "<Button-1>",
            lambda e: [
                self.search_entry.event_generate("<<Paste>>"),
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
            pady=7,
            anchor="w",
            cursor="hand2",
        )

        btn_clear.pack(fill="x")
        btn_clear.bind("<Enter>", lambda e: btn_clear.config(bg=COLOR_ACCENT))
        btn_clear.bind("<Leave>", lambda e: btn_clear.config(bg=COLOR_BTN_DEFAULT))
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
                # Tentative via xdg-open pour contourner les restrictions Snap
                subprocess.Popen(['xdg-open', url],
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
            except Exception:
                # Fallback sur webbrowser si xdg-open échoue
                webbrowser.open(url)
        else:
            # Comportement standard pour Windows/macOS
            webbrowser.open(url)

    def open_github_link(self, event=None):
        self.open_url(GITHUB_URL)

    def update_windows_title_bar(self):
        """Apply theme to the Windows title bar."""
        if sys.platform == "win32":
            try:
                from ctypes import windll, byref, sizeof, c_int

                self.root.update_idletasks()

                # Use GA_ROOT to get the real window handle
                hwnd = windll.user32.GetAncestor(self.root.winfo_id(), 2)

                mode = self.theme_mode.get()
                if mode == "Dark":
                    IS_DARK = 1
                elif mode == "Light":
                    IS_DARK = 0
                else:
                    IS_DARK = get_windows_theme()

                # Attribute 20: Immersive Dark Mode
                windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, 20, byref(c_int(IS_DARK)), sizeof(c_int(IS_DARK))
                )

                # Attribute 34: Title bar color (BGR)
                color = 0x002D2D2D if IS_DARK else 0x00FFFFFF
                windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, 34, byref(c_int(color)), sizeof(c_int(color))
                )

                # Refresh frame
                windll.user32.SetWindowPos(
                    hwnd, 0, 0, 0, 0, 0, 0x0020 | 0x0002 | 0x0001 | 0x0004
                )
            except Exception:
                pass

    def listen_for_theme_changes(self):
        """Intercepts the WM_SETTINGCHANGE message securely (64-bit compatible))."""
        if sys.platform != "win32":
            return

        from ctypes import windll, WINFUNCTYPE, c_int64, c_void_p, c_uint64

        WM_SETTINGCHANGE = 0x001A
        GWLP_WNDPROC = -4

        # 1. Strict type definition to avoid "Access Violation"
        # We use c_int64 and c_void_p to properly support 64 bits
        WNDPROC = WINFUNCTYPE(c_int64, c_void_p, c_uint64, c_uint64, c_int64)

        windll.user32.CallWindowProcW.argtypes = [
            c_void_p,
            c_void_p,
            c_uint64,
            c_uint64,
            c_int64,
        ]
        windll.user32.CallWindowProcW.restype = c_int64

        windll.user32.SetWindowLongPtrW.argtypes = [c_void_p, c_int64, c_void_p]
        windll.user32.SetWindowLongPtrW.restype = c_void_p

        def wndproc(hwnd, msg, wparam, lparam):
            if msg == WM_SETTINGCHANGE:
                # We use after so as not to block the main Windows thread.
                self.root.after(200, self.update_windows_title_bar)

            # Using the original saved pointer
            return windll.user32.CallWindowProcW(
                self.old_wndproc, hwnd, msg, wparam, lparam
            )

        try:
            # Retrieving the correct handle (the parent of winfo_id for Tkinter)
            hwnd = windll.user32.GetParent(self.root.winfo_id())

            # We keep a reference to the function to prevent it from being deleted by the Garbage Collector.
            self.new_wndproc = WNDPROC(wndproc)

            # Replacement of the procedure
            self.old_wndproc = windll.user32.SetWindowLongPtrW(
                hwnd, GWLP_WNDPROC, self.new_wndproc
            )
        except Exception as e:
            print(f"[ERROR] {type(e).__name__}: {e}")

    def check_theme_periodically(self):
        """Checks the Windows theme every 2 seconds in a secure manner."""
        if not self.running:
            return

        try:
            # We retrieve the current theme via your existing function.
            current_IS_DARK = get_windows_theme()

            # If this is your first time or if the theme has changed
            if (
                not hasattr(self, "_last_recorded_theme")
                or self._last_recorded_theme != current_IS_DARK
            ):
                self.check_theme_periodically()
                self._last_recorded_theme = current_IS_DARK

        except Exception:
            pass

        # We will restart the verification in 2000ms (2 seconds).
        self.root.after(2000, self.check_theme_periodically)

    def update_status_color(self, color):
        if hasattr(self, "status_indicator"):
            self.status_indicator.itemconfig(self.status_circle, fill=color)

    def hide_cursor(self):
        """
        Hides the text cursor by setting the blink time to 0.
        """
        self.txt_area.config(insertontime=0)
        self.cursor_visible = False
        self.cursor_timer = None

    def reset_cursor_timer(self, event=None):
        """
        Resets the inactivity timer and restores cursor visibility.
        """
        # Cancel existing timer if it exists
        if self.cursor_timer:
            self.root.after_cancel(self.cursor_timer)

        # Restore cursor blink settings if it was hidden
        if not self.cursor_visible:
            self.txt_area.config(insertontime=600)
            self.cursor_visible = True

        # Set new timer for 5 seconds (5000 ms)
        self.cursor_timer = self.root.after(5000, self.hide_cursor)

    def safe_vertical_scroll(self, event):
        """Vertical scrolling using the mouse wheel without resetting the X-axis."""
        if event.delta:
            direction = -1 if event.delta > 0 else 1
            self.txt_area.yview_scroll(direction, "units")

        # On Linux (buttons 4 and 5)
        elif event.num == 4:
            self.txt_area.yview_scroll(-1, "units")
        elif event.num == 5:
            self.txt_area.yview_scroll(1, "units")

        return "break"

    def sc(self, value):
        """Calculates the scaled value."""
        return int(value * self.scale)

    def immediate_ui_refresh(self):
        # Quick function to sync label with toggle state
        l = LANGS.get(self.current_lang.get(), LANGS["EN"])
        txt = l["unlimited"] if self.load_full_file.get() else l["limit"]
        self.label_limit.config(text=txt) # or self.limit_var.set(txt)

    def copy_to_clipboard(self, event=None):
            """
            Copies the currently selected text from the log area to the system clipboard.
            """
            try:
                # 1. Try to get the selected text from the text widget
                # tk.SEL_FIRST and tk.SEL_LAST represent the start and end of the selection
                selected_text = self.txt_area.get(tk.SEL_FIRST, tk.SEL_LAST)

                if selected_text:
                    # 2. Clear the clipboard and append the new text
                    self.root.clipboard_clear()
                    self.root.clipboard_append(selected_text)
                    # This ensures the text stays in the clipboard even after the app closes on some OS
                    self.root.update()
            except tk.TclError:
                # Error occurs if no text is selected; we simply ignore it
                pass

            # 3. Return "break" to prevent the default Tkinter event from firing
            return "break"

    # === 1. SEARCH LIST - INITIALIZATION & EVENTS ===

    def setup_history_events(self):
        """Initializes history and binds events to the search field."""
        # 1. Load history
        self.load_search_history()

        # 2. Bind for auto-opening on typing
        self.search_entry.bind("<KeyRelease>", self.on_search_keyrelease)

        # 3. Handle navigation and Escape
        self.search_entry.bind("<Up>", self.on_search_up)
        self.search_entry.bind("<Down>", self.on_search_down)

        # Bind on search_entry because focus stays there when using UP/DOWN
        self.search_entry.bind("<Left>", self._exit_history_to_entry)
        self.search_entry.bind("<Right>", self._exit_history_to_entry)

        # Bind on history_listbox just in case user explicitly clicked on it
        self.history_listbox.bind("<Left>", self._exit_history_to_entry)
        self.history_listbox.bind("<Right>", self._exit_history_to_entry)

        # FIX: Call the full reset function instead of just hiding the dropdown
        self.search_entry.bind("<Escape>", self.reset_search_and_focus_log)

        # 4. Save search on ENTER
        self.search_entry.bind("<Return>", self.validate_and_save_search)

        # 5. Close if focus moves to log
        self.txt_area.bind("<FocusIn>", lambda e: self.hide_history_dropdown(), add="+")

        # 6. Close if clicking outside
        self.root.bind("<Button-1>", self._close_dropdown_on_outside_click, add="+")

    # === 2. SEARCH LIST - DATA MANAGEMENT (FILES) ===

    def load_search_history(self):
        """Loads search history from a file."""
        self.search_history = []
        # Use a dedicated file for history
        if os.path.exists(SEARCH_HISTORY_FILE):
            try:
                with open(SEARCH_HISTORY_FILE, "r", encoding="utf-8") as f:
                    self.search_history = [line.strip() for line in f.readlines() if line.strip()]
            except Exception as e:
                print(f"Error loading history: {e}")

    def save_search_history(self):
        """Saves search history to a file."""
        try:
            with open(SEARCH_HISTORY_FILE, "w", encoding="utf-8") as f:
                for item in self.search_history:
                    f.write(f"{item}\n")
        except Exception as e:
            print(f"Error saving history: {e}")

    def add_to_history(self, text):
        """Adds a term to history (no duplicates and at the beginning)."""
        text = text.strip()
        if not text:
            return

        # Remove the term if it already existed to put it back at the top
        if text in self.search_history:
            self.search_history.remove(text)

        self.search_history.insert(0, text)

        # Limit history to the last 15 searches, for example
        self.search_history = self.search_history[:15]
        self.save_search_history()

    def clear_all_history_data(self):
        """Deletes the history file and clears the list from memory."""
        l = LANGS.get(self.current_lang.get(), LANGS["EN"])

        msg = l.get("clear_confirm_msg", "Do you want to delete all search history?")
        confirm = messagebox.askyesno(APP_NAME, msg)

        if confirm:
            try:
                # 2. Get the path to your history file
                # Assuming it's in the same directory as the main script
                history_path = ".kodi_search_history"

                # 3. Delete the physical file if it exists
                import os
                if os.path.exists(history_path):
                    os.remove(history_path)

                # 4. Clear the memory and UI
                self.search_history = []
                self.history_listbox.delete(0, tk.END)

                # 5. Hide the dropdown if it was open
                self.hide_history_dropdown()

                print("Search history cleared successfully.")

            except Exception as e:
                print(f"Error clearing history: {e}")

    # === 3. SEARCH LIST - INTERFACE & SECURITY ===

    def clean_search_input(self, *args):
        """
        Sanitizes the search input: prevents multi-line,
        limits length, and removes suspicious characters.
        """
        raw_text = self.search_query.get()

        if not raw_text:
            return

        # 1. Keep only the first line (remove everything after the first \n or \r)
        clean_text = raw_text.splitlines()[0] if raw_text.splitlines() else ""

        # 2. Limit the total length (e.g., 100 characters max)
        max_length = 100
        if len(clean_text) > max_length:
            clean_text = clean_text[:max_length]

        # 3. Clean whitespace but allow a single trailing space for active typing
        # Replace tabs or multiple consecutive spaces with a single space
        clean_text = re.sub(r'[ \t]+', ' ', clean_text)

        # By removing .strip(), we allow the user to type a space at the end of a word.
        # clean_text = clean_text.lstrip().strip()
        clean_text = clean_text.lstrip()

        # 4. Update the variable only if it has changed to avoid infinite recursion
        if raw_text != clean_text:
            self.search_query.set(clean_text)
            # Move cursor to the end since setting the var might reset it
            self.search_entry.icursor(tk.END)

    def show_history_dropdown(self, items=None):
        """Displays the history list with theme colors."""
        if items is None:
            items = self.search_history

        if not items:
            self.hide_history_dropdown()
            return

        # --- 1. CONFIGURE THE TOPLEVEL WINDOW BORDER ---
        # We use highlightthickness on the window itself to create a 1px border
        self.history_window.configure(
            bg=COLOR_BG_HEADER,
            highlightbackground=COLOR_TEXT_DIM, # The color of the 1px border
            highlightthickness=1,               # The width of the border
            relief="flat"
        )

        # --- 2. CONFIGURE THE LISTBOX ---
        self.history_listbox.config(
            bg=COLOR_BG_HEADER,
            fg=COLOR_TEXT_MAIN,
            selectbackground=COLOR_ACCENT,
            selectforeground=COLOR_TEXT_BRIGHT,
            font=(get_system_font()[0], 10),
            borderwidth=0,          # Set to 0 because the window handles the border
            highlightthickness=0,   # Ensure no internal highlight
            relief="flat",
            selectborderwidth=0
        )

        self.history_listbox.delete(0, tk.END)
        for item in items:
            # Indent the text by 2 spaces from the left margin
            self.history_listbox.insert(tk.END, f"  {item}")
            # self.history_listbox.insert(tk.END, item)

        # Set height (max 7 lines)
        visible_lines = min(len(items), 7)
        self.history_listbox.config(height=visible_lines)

        self.root.update_idletasks()

        # Position calculation
        x = self.search_entry.winfo_rootx()
        y = self.search_entry.winfo_rooty() + self.search_entry.winfo_height()+ 10

        # --- 3. ADJUST GEOMETRY ---
        # Note: We don't change the width/height calculation,
        # but the window will look 2px larger total due to 1px border on each side.
        width = self.search_entry.winfo_width()
        height = self.history_listbox.winfo_reqheight()

        self.history_window.geometry(f"{width}x{height}+{x}+{y}")

        self.history_window.deiconify()
        self.history_window.lift()

    def hide_history_dropdown(self, event=None):
        """Hides the history popup window."""
        if hasattr(self, 'history_window'):
            self.history_window.withdraw()

    def reset_search_and_focus_log(self, event=None):
        """
        Clears the search, hides history, and returns focus to the log area.
        """
        # Clear the text
        self.search_query.set("")

        # Hide the dropdown
        self.hide_history_dropdown()

        # Return focus to the log
        if hasattr(self, 'txt_area'):
            self.txt_area.focus_set()

        # Prevent event propagation
        return "break"

    def _close_dropdown_on_outside_click(self, event):
        """Closes the history dropdown if the user clicks outside of it."""
        if hasattr(self, "history_listbox") and self.history_listbox.winfo_viewable():
            # Check if the click is outside both the search entry and the history listbox
            if event.widget != self.search_entry and event.widget != self.history_listbox:
                self.hide_history_dropdown()

    def _on_window_configure(self, event):
        """Hides the history dropdown when the main window moves or resizes."""
        # Ensure the event is coming from the root window itself,
        # not from its children widgets resizing.
        if event.widget == self.root:
            # Check if the dropdown exists and is currently visible
            if hasattr(self, "history_listbox") and self.history_listbox.winfo_viewable():
                self.hide_history_dropdown()

    # === 4. SEARCH LIST - NAVIGATION & SELECTION ===

    def on_search_keyrelease(self, event):
        """Opens after entering at least one letter."""
        # The control keys are omitted so as not to interfere with filtering
        if event.keysym in ("Up", "Down", "Return", "Escape", "Left", "Right"):
            return

        query = self.search_query.get().strip().lower()

        if len(query) >= 1:
            # Filter the results based on the text
            filtered = [item for item in self.search_history if query in item.lower()]
            if filtered:
                self.show_history_dropdown(filtered)
            else:
                self.hide_history_dropdown()
        else:
            self.hide_history_dropdown()

    def on_search_up(self, event):
        """Handles the up arrow in the search field without scrolling through the log."""
        if not self.history_listbox.winfo_viewable():
            # If it's closed and there are items inside, we open it
            if self.search_history:
                self.show_history_dropdown()
            return "break" # Stop the log from scrolling!

        # If the list is open, scroll up through the selection
        current = self.history_listbox.curselection()
        if not current:
            # If nothing is selected, start from the last item in the list
            last_idx = self.history_listbox.size() - 1
            if last_idx >= 0:
                self.history_listbox.selection_set(last_idx)
                self.history_listbox.see(last_idx)
        else:
            # Move up one item, bounded by 0
            idx = max(0, current[0] - 1)
            self.history_listbox.selection_clear(0, tk.END)
            self.history_listbox.selection_set(idx)
            self.history_listbox.see(idx)

        return "break" # Prevent the log from scrolling!

    def on_search_down(self, event):
        """Handles the down arrow in the search field without scrolling through the log."""
        if not self.history_listbox.winfo_viewable():
            # If it's closed and there are items inside, we open it
            if self.search_history:
                self.show_history_dropdown()
            return "break" # Stop the log from scrolling!

        # If the list is open, scroll down through the selection
        current = self.history_listbox.curselection()
        if not current:
            self.history_listbox.selection_set(0)
        else:
            idx = min(current[0] + 1, self.history_listbox.size() - 1)
            self.history_listbox.selection_clear(0, tk.END)
            self.history_listbox.selection_set(idx)
            self.history_listbox.see(idx)
        return "break" # Prevent the log from scrolling!

    def on_history_select(self, event):
        """Handles item selection from the history dropdown using mouse click or Enter key."""
        # 1. Determine the index based on the source and type of event
        # If the event comes from the listbox and is a mouse button click/release
        if event.widget == self.history_listbox and ("Button" in str(event.type) or "5" == str(event.type)):
            index = self.history_listbox.nearest(event.y)
        else:
            # Keyboard event (Enter key) from either the Entry or the Listbox
            selection = self.history_listbox.curselection()

            if selection:
                index = selection[0]
            else:
                # Fallback to the active item, or default to the first item (0)
                active_index = self.history_listbox.index("active")
                index = active_index if active_index >= 0 else 0

        # 2. Apply the text if the index is valid
        if index >= 0:
            try:
                selected_text = self.history_listbox.get(index).strip()
                self._apply_history_selection(selected_text)

                # Hide the list and return focus to the search entry field
                self.history_listbox.place_forget()
                self.search_entry.focus_set()

                # Put the cursor at the end of the newly inserted text
                self.search_entry.icursor("end")
            except Exception:
                pass

        # 3. Prevent the event from propagating (prevents jumping to the log)
        return "break"

    def validate_and_save_search(self, event=None):
        """
        Validates search: priority to history selection if visible,
        otherwise validates the current entry text.
        """
        # 1. Check if the history list is visible
        if self.history_listbox.winfo_viewable():
            selection = self.history_listbox.curselection()
            if selection:
                # An item is selected: use it
                selected_text = self.history_listbox.get(selection[0])
                self._apply_history_selection(selected_text)
                return "break"

        # 2. Otherwise, validate the text from the search entry field
        query = self.search_query.get().strip()
        if query:
            self.add_to_history(query)

        # 3. Close the list
        self.hide_history_dropdown()

        # 4. Check if results are found or if the "No match" screen is shown
        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])
        filter_msg = l_ui.get('filter_applied', 'Applied filter(s):')

        # We can detect no matches either by the text or by the presence of the 'filter_header' tag
        has_no_matches = (filter_msg in self.txt_area.get("1.0", tk.END) or
                          len(self.txt_area.tag_ranges("filter_header")) > 0)

        # Decide where to place the focus based on search results
        if not has_no_matches and hasattr(self, 'txt_area'):
            # Results were found, we go to the log area
            self.txt_area.focus_set()
        else:
            # No results or empty search, we stay in the search entry
            self.search_entry.focus_set()
            self.search_entry.icursor(tk.END)

        return "break"

    def _apply_history_selection(self, text):
        """Internal helper to apply the selected text and trigger search."""
        # 1. Update the search field
        self.search_query.set(text)

        # 2. Position cursor and focus
        self.search_entry.icursor(tk.END)
        self.search_entry.focus_set()

        # 3. Close the popup
        self.hide_history_dropdown()

        # 4. Trigger search (we use your existing validation method)
        self.validate_and_save_search()

    def _exit_history_to_entry(self, event=None):
        """
        Hides the history list and returns focus to the search entry without selecting anything.
        """
        # Check if the list is visible (inspired by on_search_up/down)
        if self.history_listbox.winfo_viewable():
            # 1. Hide the dropdown list
            self.hide_history_dropdown()

            # 2. Return focus to the search entry field (just in case)
            self.search_entry.focus_set()

            # 3. Put the cursor at the end of the text
            self.search_entry.icursor(tk.END)

            # 4. Prevent the default behavior (so it doesn't move the cursor inside the entry)
            return "break"

        # If the list is not visible, let the cursor move left/right normally in the search entry
        return


