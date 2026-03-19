import os
import time
import threading
import re
import tkinter as tk
import sys

from config import *
from languages import LANGS

class MonitorMixin:
    # reads the file and sends the lines to the display
    def monitor_loop(self):
        """
        Background thread loop that monitors the log file for changes.
        Handles file rotation (Kodi restarts), inactivity detection, and UI updates.
        """
        try:
            # Initial opening of the file
            with open(self.log_file_path, "r", encoding="utf-8", errors="ignore") as f:
                if self.load_full_file.get():
                    f.seek(0)
                else:
                    f.seek(0, os.SEEK_END)
                    f.seek(max(0, f.tell() - 100000))

                initial_lines = f.readlines()
                if not self.load_full_file.get():
                    initial_lines = initial_lines[-1000:]
                last_pos = f.tell()

                to_display = []
                for line in initial_lines:
                    data = self.get_line_data(line)
                    if data and not self.is_duplicate(data[0]):
                        to_display.append(data)

                if to_display:
                    self.root.after(0, self.bulk_insert, to_display)
                else:
                    is_filtering = any(v.get() for k, v in self.filter_vars.items() if k != "all")

                    if not self.load_full_file.get() and not is_filtering:
                        self.root.after(0, self.bulk_insert, to_display)
                    else:
                        self.root.after(1000, lambda: self.bulk_insert(to_display) if (self.running and not self.txt_area.get("1.0", tk.END).strip()) else None)

                while self.running:
                    try:
                        # 1. Accessibility verification
                        current_size = os.path.getsize(self.log_file_path)

                        # 2. RECONNECTION: Let's get out of this mistake
                        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])
                        msg_erreur = l_ui.get(
                            "file_error",
                            "⚠️ IMPORTANT : le fichier de log est inaccessible !",
                        )

                        if self.inactivity_timer_var.get() == msg_erreur:
                            # We reset everything to prevent "Inactive" from replacing the error immediately.
                            self.last_activity_time = time.time()
                            self.root.after(0, self.inactivity_timer_var.set, "")
                            # The color is reset according to the actual status (green or orange if limited).
                            new_color = (
                                COLOR_WARNING
                                if not self.load_full_file.get()
                                else "#4CAF50"
                            )
                            self.root.after(0, self.update_status_color, new_color)

                        # 3. Managing Kodi Restarts
                        if current_size < last_pos:
                            self.root.after(
                                0,
                                self.start_monitoring,
                                self.log_file_path,
                                False,
                                False,
                            )
                            return

                        # 4. Reading
                        line = f.readline()
                        if not line:
                            # The calculation is only performed if detection is not disabled (different from 0).
                            if self.inactivity_limit > 0:
                                elapsed = time.time() - self.last_activity_time

                                if elapsed >= self.inactivity_limit:
                                    self.root.after(
                                        0, self.update_status_color, COLOR_DANGER
                                    )

                                    # Calculating and displaying time (HH:MM)
                                    l_ui = LANGS.get(
                                        self.current_lang.get(), LANGS["EN"]
                                    )
                                    mins, secs = divmod(int(elapsed), 60)
                                    timer_str = (
                                        f"{l_ui['inactive']} : {mins:02d}:{secs:02d}"
                                    )
                                    self.root.after(
                                        0, self.inactivity_timer_var.set, timer_str
                                    )
                                else:
                                    self.root.after(
                                        0, self.update_status_color, "#666666"
                                    )
                                    self.root.after(
                                        0, self.inactivity_timer_var.set, ""
                                    )
                            else:
                                # If inactivity_limit is 0, it remains gray with no message.
                                self.root.after(0, self.update_status_color, "#666666")
                                self.root.after(0, self.inactivity_timer_var.set, "")

                            self.root.after(0, self.update_stats)
                            time.sleep(0.4)
                            continue

                        # If reading successful
                        self.last_activity_time = time.time()
                        # If limited mode -> Orange, otherwise Green
                        final_color = (
                            COLOR_WARNING
                            if not self.load_full_file.get()
                            else "#4CAF50"
                        )
                        self.root.after(0, self.update_status_color, final_color)
                        self.root.after(0, self.inactivity_timer_var.set, "")

                        last_pos = f.tell()
                        data = self.get_line_data(line)
                        if data and not self.is_duplicate(data[0]):
                            self.root.after(0, self.append_to_gui, data[0], data[1])

                    except (IOError, OSError):
                        # LOSS OF ACCESS
                        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])
                        msg = l_ui.get(
                            "file_error",
                            "⚠️ IMPORTANT : le fichier de log est inaccessible !",
                        )
                        self.root.after(0, self.inactivity_timer_var.set, msg)
                        self.root.after(0, self.update_status_color, COLOR_DANGER)
                        time.sleep(2)
                        continue

        except Exception as e:
            print(f"[ERROR] {type(e).__name__}: {e}")
            self.root.after(0, self.show_loading, False)

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
