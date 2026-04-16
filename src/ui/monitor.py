import os
import time
import threading
import re
import subprocess
import tkinter as tk
import sys

from config import *
from languages import LANGS

# Maximum number of lines collected in one batch before dispatching to the UI.
# Keeps the main thread responsive even under intense log flux.
_BATCH_MAX = 150

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
                            except Exception:
                                pass

                            f = open(self.log_file_path, 'r', encoding='utf-8', errors='ignore')
                            f.seek(last_pos)

                            self.is_file_inaccessible = False
                            if self.running:
                                self.root.after(0, self.inactivity_timer_var.set, "")
                                self.root.after(0, lambda: self.update_status_color(
                                    LOG_COLORS["info"] if not self.load_full_file.get() else LOG_COLORS["warning"]
                                ))
                                self.root.after(0, self.reset_all_filters)

                        # 3. Detect Log Rotations (Kodi restarts)
                        if current_size < last_pos:
                            if self.running:
                                self.root.after(0, self.start_monitoring, self.log_file_path, False, False)
                            return

                        # 4. Read all available lines as a batch.
                        #    Collecting up to _BATCH_MAX lines before dispatching
                        #    means one after() call instead of one per line, which
                        #    prevents flooding the Tkinter event queue under high flux.
                        batch = []
                        has_new_lines = False  # raw file activity, independent of filters
                        while self.running and len(batch) < _BATCH_MAX:
                            line = f.readline()
                            if not line:
                                break
                            last_pos = f.tell()
                            has_new_lines = True  # file wrote something, regardless of filter
                            data = self.get_line_data(line)
                            if data and not self.is_duplicate(data[0]):
                                batch.append((data[0], data[1]))

                        # 5a. File had new content: update indicator on raw activity,
                        #     dispatch only the filtered batch to the GUI.
                        if has_new_lines:
                            self.last_activity_time = time.time()
                            self.is_file_inaccessible = False
                            if self.running:
                                if batch:
                                    self.root.after(0, self.append_batch_to_gui, batch)
                                self.root.after(0, lambda: self.update_status_color(
                                    LOG_COLORS["info"] if not self.load_full_file.get() else LOG_COLORS["warning"]
                                ))
                                self.root.after(0, self.inactivity_timer_var.set, "")
                            # Brief pause between batches: gives the main thread time
                            # to process the after() callback and remain responsive.
                            time.sleep(0.05)

                        # 5b. No new data: handle inactivity timer then wait
                        else:
                            if self.inactivity_limit > 0:
                                elapsed = time.time() - self.last_activity_time
                                if elapsed >= self.inactivity_limit:
                                    if self.running:
                                        try:
                                            self.root.after(0, self.update_status_color, COLOR_DANGER)
                                            mins, secs = divmod(int(elapsed), 60)
                                            timer_str = f"{l_ui.get('inactive', 'Inactive')} : {mins:02d}:{secs:02d}"
                                            self.root.after(0, self.inactivity_timer_var.set, timer_str)
                                        except Exception:
                                            pass
                                else:
                                    if self.running:
                                        try:
                                            self.root.after(0, self.update_status_color, COLOR_INDICATOR_OFF)
                                            self.root.after(0, self.inactivity_timer_var.set, "")
                                        except Exception:
                                            pass
                            else:
                                if self.running:
                                    try:
                                        self.root.after(0, self.update_status_color, COLOR_INDICATOR_OFF)
                                        self.root.after(0, self.inactivity_timer_var.set, "")
                                        self.root.after(0, self.update_stats)
                                    except Exception:
                                        pass
                            time.sleep(0.4)

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
                except Exception:
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
        self._reset_seen_cache()   # clears deque + O(1) set together
        self.log_file_path = path

        # Reset footer stats so update_stats re-fetches fresh values for the new file
        if hasattr(self, 'stats_var'):
            self.stats_var.set("")
        if hasattr(self, 'size_var'):
            self.size_var.set("")

        # --- AUTO-DISABLE PAUSE MODE ---
        if hasattr(self, 'is_paused'):
            self.is_paused.set(False)

        if hasattr(self, 'update_button_colors'):
            self.root.after(0, self.update_button_colors)
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

    def _reset_seen_cache(self):
        """
        Clears both the deque and its companion set so they stay in sync.
        Call this wherever seen_lines.clear() was previously used.
        """
        self.seen_lines.clear()
        self._seen_set.clear()

    def is_duplicate(self, text):
        """
        Checks if a line of text has already been processed.

        Uses a set for O(1) lookup (vs O(n) on the deque).  The deque is kept
        alongside to bound memory: when it is full the oldest entry is about to
        be evicted by the maxlen mechanism, so we remove it from the set first
        to keep both structures in sync.

        Args:
            text (str): The line text to check.

        Returns:
            bool: True if duplicate or empty, False otherwise.
        """
        clean_text = text.strip()
        if not clean_text:
            return True
        if clean_text in self._seen_set:          # O(1)
            return True
        # Keep deque + set in sync: remove the item that is about to be evicted
        if len(self.seen_lines) == self.seen_lines.maxlen:
            self._seen_set.discard(self.seen_lines[0])
        self.seen_lines.append(clean_text)
        self._seen_set.add(clean_text)
        return False

    def periodic_display_check(self):
        """
        Checks periodically (every 3 s) whether the screen resolution has changed
        (width or height). On change, offers the user to restart the app so that
        CTK scaling, DPI and window geometry are recalculated correctly.
        """
        if sys.platform != "win32":
            return

        try:
            from ctypes import windll
            current_w = windll.user32.GetSystemMetrics(0)   # SM_CXSCREEN
            current_h = windll.user32.GetSystemMetrics(1)   # SM_CYSCREEN

            changed = False
            if hasattr(self, "last_screen_width") and current_w != self.last_screen_width:
                changed = True
            if hasattr(self, "last_screen_height") and current_h != self.last_screen_height:
                changed = True

            if changed:
                self.last_screen_width  = current_w
                self.last_screen_height = current_h
                # Show dialog on the main thread via after_idle
                self.root.after_idle(self.show_display_changed_dialog)
                return   # Don't reschedule — the dialog will handle the next step

        except Exception:
            pass

        self.root.after(3000, self.periodic_display_check)

    def show_display_changed_dialog(self):
        """
        Notifies the user of a display change (resolution, scaling) and offers
        to close the app so it can be relaunched with correct CTK geometry/DPI.
        Shows a Yes / No dialog:
          - Yes → clear saved geometry + close cleanly via _graceful_close()
          - No  → update title bar + resume periodic check
        """
        from tkinter import messagebox

        # Guard: only one dialog at a time
        if getattr(self, '_showing_dpi_msg', False):
            return
        self._showing_dpi_msg = True

        l = LANGS.get(self.current_lang.get(), LANGS["EN"])
        title = l.get("display_change_title", "Display settings changed")
        msg   = l.get(
            "display_change_msg",
            "The Windows display settings have changed.\n\n"
            "It is recommended to close the application\n"
            "so the interface adapts correctly on next launch.\n\n"
            "Close now?"
        )

        answer = messagebox.askyesno(title, msg)
        self._showing_dpi_msg = False

        if answer:
            # Clear saved geometry so next launch recalculates the correct default
            self.window_geometry = ""
            self._graceful_close()
        else:
            # User declined — update title bar and resume periodic monitoring
            if hasattr(self, 'update_windows_title_bar'):
                self.update_windows_title_bar()
            self.root.after(3000, self.periodic_display_check)
