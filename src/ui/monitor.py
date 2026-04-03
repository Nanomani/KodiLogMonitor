import os
import time
import threading
import re
import tkinter as tk
import sys

from config import *
from languages import LANGS

class MonitorMixin:
    def monitor_loop(self):
        """Monitors the log file in a background thread and updates the UI."""
        try:
            # --- CAPTURE UI VALUES SAFELY AT START ---
            if not self.running:
                return

            try:
                # Capture Tkinter variables once to avoid crashes during loop
                load_full = self.load_full_file.get()
                current_lang_code = self.current_lang.get()
                # Capture the language dictionary for this thread session
                l_ui = LANGS.get(current_lang_code, LANGS["EN"])
            except (tk.TclError, RuntimeError):
                # If UI is destroyed or inaccessible, exit thread
                return

            # --- INITIAL OPENING OF THE FILE ---
            with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                if load_full:
                    f.seek(0)
                else:
                    # Seek to the end and read a chunk (approx 100kb)
                    f.seek(0, os.SEEK_END)
                    f.seek(max(0, f.tell() - 100000))

                initial_lines = f.readlines()
                if not load_full:
                    initial_lines = initial_lines[-1000:]

                last_pos = f.tell()

                to_display = []
                for line in initial_lines:
                    data = self.get_line_data(line)
                    if data and not self.is_duplicate(data[0]):
                        to_display.append(data)

                # Send initial data to GUI
                if self.running:
                    try:
                        if to_display:
                            self.root.after(0, self.bulk_insert, to_display)
                        else:
                            # Logic for empty files or filtering
                            is_filtering = any(v.get() for k, v in self.filter_vars.items() if k != "all")
                            if not load_full and not is_filtering:
                                self.root.after(0, self.bulk_insert, to_display)
                            else:
                                # Delayed update to ensure UI is ready
                                self.root.after(1000, lambda: self.bulk_insert(to_display) if self.running else None)
                    except (tk.TclError, RuntimeError):
                        return

                # Persistent flag for file access errors
                self.is_file_inaccessible = False

                # --- REAL-TIME MONITORING LOOP ---
                while self.running:
                    try:
                        # 1. Check if the file still exists/is accessible
                        current_size = os.path.getsize(self.log_file_path)

                        # 2. Recovery: If file WAS inaccessible, reconnect!
                        if self.is_file_inaccessible:
                            try:
                                f.close()
                            except:
                                pass

                            f = open(self.log_file_path, 'r', encoding='utf-8', errors='ignore')
                            f.seek(last_pos)

                            self.is_file_inaccessible = False
                            if self.running:
                                self.root.after(0, self.inactivity_timer_var.set, "")
                                final_color = COLOR_WARNING if not load_full else LOG_COLORS["info"]
                                self.root.after(0, self.update_status_color, final_color)

                                # Trigger a full UI refresh
                                self.root.after(0, self.reset_all_filters)
                                # print(f"[DEBUG] File recovered, triggering full reset...")
                                # self.root.after(0, lambda: self.start_monitoring(self.log_file_path, is_manual=False))

                                # Clear the text area when the log file becomes accessible again
                                # self.root.after(0, lambda: self.txt_area.config(state=tk.NORMAL))
                                # self.root.after(0, lambda: self.txt_area.delete('1.0', tk.END))
                                # self.root.after(0, lambda: self.txt_area.config(state=tk.DISABLED))

                        # 3. Detect Log Rotations (Kodi restarts)
                        if current_size < last_pos:
                            if self.running:
                                self.root.after(0, self.start_monitoring, self.log_file_path, False, False)
                            return

                        # 4. Read new line
                        line = f.readline()
                        if not line:
                            if self.inactivity_limit > 0:
                                elapsed = time.time() - self.last_activity_time
                                if elapsed >= self.inactivity_limit:
                                    if self.running:
                                        try:
                                            self.root.after(0, self.update_status_color, COLOR_DANGER)
                                            mins, secs = divmod(int(elapsed), 60)
                                            timer_str = f"{l_ui.get('inactive', 'Inactive')} : {mins:02d}:{secs:02d}"
                                            self.root.after(0, self.inactivity_timer_var.set, timer_str)
                                        except: pass
                                else:
                                    if self.running:
                                        try:
                                            self.root.after(0, self.update_status_color, COLOR_INDICATOR_OFF)
                                            self.root.after(0, self.inactivity_timer_var.set, "")
                                        except: pass
                            else:
                                if self.running:
                                    try:
                                        self.root.after(0, self.update_status_color, COLOR_INDICATOR_OFF)
                                        self.root.after(0, self.inactivity_timer_var.set, "")
                                        self.root.after(0, self.update_stats)
                                    except: pass

                            time.sleep(0.4)
                            continue

                        # 5. Data Received: Update activity and UI status
                        self.last_activity_time = time.time()
                        if self.running:
                            self.is_file_inaccessible = False
                            final_color = COLOR_WARNING if not load_full else LOG_COLORS["info"]
                            self.root.after(0, self.update_status_color, final_color)
                            self.root.after(0, self.inactivity_timer_var.set, "")

                        # 6. Process line and append to GUI
                        last_pos = f.tell()
                        data = self.get_line_data(line)
                        if data and self.running and not self.is_duplicate(data[0]):
                            self.root.after(0, self.append_to_gui, data[0], data[1])

                    except (IOError, OSError):
                        # File becomes locked or deleted temporarily
                        if not self.is_file_inaccessible and self.running:
                            self.is_file_inaccessible = True
                            # SAFE: Use local l_ui instead of self.current_lang.get()
                            msg = l_ui.get("file_error", "⚠️ LOG INACCESSIBLE!")
                            self.root.after(0, self.inactivity_timer_var.set, msg)
                            self.root.after(0, self.update_status_color, COLOR_DANGER)

                        time.sleep(2)
                        continue

                    except (tk.TclError, RuntimeError):
                        break

        except Exception as e:
            if self.running:
                print(f"[ERROR] {type(e).__name__}: {e}")
                try:
                    self.root.after(0, self.show_loading, False)
                except:
                    pass

    def start_monitoring(self, path, save=True, retranslate=True, is_manual=True):
        """
        Prepares the environment and launches the monitoring thread for a specific file.

        Args:
            path (str): Path to the log file.
            save (bool): Whether to save the file path to the session config.
            retranslate (bool): Whether to refresh UI translations.
            is_manual (bool): Whether the file was selected manually by the user.
        """
        self.last_activity_time = time.time()
        self.inactivity_timer_var.set("")
        self.running = True
        self.seen_lines.clear()
        self.log_file_path = path

        # --- AUTO-DISABLE PAUSE MODE ---
        if hasattr(self, 'is_paused'):
            self.is_paused.set(False)

        if hasattr(self, 'update_pause_button_look'):
            self.root.after(0, self.update_pause_button_look)
        # ---------------------------------------

        # Update the footer with safety truncation and tooltip ---
        if hasattr(self, 'update_footer_path'):
            self.update_footer_path(path)

        self.is_file_inaccessible = False

        # --- 10 MB SECURITY BLOCK ---
        try:
            if os.path.exists(path):
                file_size_mb = os.path.getsize(path) / (1024 * 1024)
                # If auto-loading AND large file -> we limit
                if not is_manual and file_size_mb > self.max_size_mb:
                    self.load_full_file.set(False)

                # FORCE the update of statistics and the interface
                self.root.after(0, self.update_stats)

        except Exception as e:
            print(f"[ERROR] {type(e).__name__}: {e}")
        # ---------------------------------------

        if retranslate:
            self.retranslate_ui(refresh_monitor=False)
        if save:
            self.save_session()
        self.txt_area.config(state=tk.NORMAL)
        self.txt_area.delete("1.0", tk.END)
        self.show_loading(True)
        self.root.after(150, self._launch_thread)

    def _launch_thread(self):
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()

    def is_duplicate(self, text):
        """
        Checks if a line of text has already been processed using a deque buffer.

        Args:
            text (str): The line text to check.

        Returns:
            bool: True if duplicate or empty, False otherwise.
        """
        clean_text = text.strip()
        if not clean_text:
            return True
        if clean_text in self.seen_lines:
            return True
        self.seen_lines.append(clean_text)
        return False

    def sort_logs_by_time(self, log_list):
        """
        Sorts a list of log lines chronologically based on their timestamp.

        Args:
            log_list (list): List of log strings or data tuples.

        Returns:
            list: Sorted log lines.
        """
        return sorted(log_list, key=lambda x: x[0] if isinstance(x, list) else x)

    def periodic_display_check(self):
        """
        Checks if the screen resolution or scaling has changed.
        """
        if sys.platform != "win32":
            return

        try:
            from ctypes import windll
            # Get current screen width
            current_width = windll.user32.GetSystemMetrics(0)

            if current_width != self.last_screen_width:
                self.last_screen_width = current_width
                # Call the new dialog instead of the old prompt
                self.root.after_idle(self.show_display_changed_dialog)
                return
        except Exception:
            pass

        self.root.after(3000, self.periodic_display_check)

    def show_display_changed_dialog(self):
        """
        Affiche une boîte info système standard (Bouton OK centré par Windows).
        Garantit une visibilité parfaite sur tous les types d'écrans.
        """
        from tkinter import messagebox

        if getattr(self, '_showing_dpi_msg', False):
            return
        self._showing_dpi_msg = True

        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])

        # showinfo creates a window with a single OK button centered in the window.
        messagebox.showinfo(
            l_ui.get("shutdown_confirm_title", "Display Settings Changed"),
            l_ui.get("shutdown_confirm_msg", "Display settings changed. The app will now close to recalculate geometry.")
        )

        # As soon as the user clicks OK or closes the dialog box:
        self._showing_dpi_msg = False
        self.shutdown_with_reset()

    def shutdown_with_reset(self):
        """
        Réinitialise la géométrie dans la configuration et ferme proprement.
        """
        # Clear the geometry to force a re-detection on the next launch
        self.window_geometry = ""

        if hasattr(self, 'save_session'):
            self.save_session()

        # Complete shutdown of the process
        self.root.quit()
        sys.exit(0)
