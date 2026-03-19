import tkinter as tk
import os
import re

from config import *
from languages import LANGS


class LogDisplayMixin:
    """Manages the display, filtering, and highlighting of logs."""

    def get_line_data(self, line):
        # 1. We check if a specific filter is active (if 'all' is False)
        is_filtering = not self.filter_vars["all"].get()

        # 2. Check if the line has a timestamp (e.g., 2024-05-20)
        # Kodi typically uses the YYYY-MM-DD format at the beginning of lines
        has_timestamp = re.match(r"^\d{4}-\d{2}-\d{2}", line.strip())

        # 3. IF we filter AND the line does NOT have a timestamp, we ignore it (returns None)
        if is_filtering and not has_timestamp:
            return None

        if not line or not line.strip():
            return None

        # SKIP THE KODI STARTUP DASH LINE IF DESIRED
        if "info <general>: --------" in line:
            # On peut décider de l'ignorer ou de la laisser
            # Si vous voulez la supprimer : return None
            return None

        low = line.lower()
        q = self.search_query.get().lower()
        current_tag = None
        if " error " in low:
            current_tag = "error"
        elif " warning " in low:
            current_tag = "warning"
        elif " info " in low:
            current_tag = "info"
        elif " debug " in low:
            current_tag = "debug"
        if not self.filter_vars["all"].get():
            if (
                current_tag is None
                or not self.filter_vars.get(
                    current_tag, tk.BooleanVar(value=False)
                ).get()
            ):
                return None
        if q and q not in low:
            return None
        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])
        if self.selected_list.get() != l_ui["none"]:
            kw = self.get_keywords_from_file()
            if kw and not any(k.lower() in low for k in kw):
                return None
        return (line, current_tag)

    def bulk_insert(self, data_list):
        """Inserts a set of data into the text box."""
        if not self.running:
            return

        valid_data = [d for d in data_list if d is not None]
        self.txt_area.config(state=tk.NORMAL)

        if not valid_data:
            current_text = self.txt_area.get("1.0", tk.END).strip()

            if current_text != "" and "Aucune" not in current_text:
                self.show_loading(False)
                self.update_stats()
                return

            l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])
            message = f"\n\n\n\n\t\t\t{l_ui.get('no_match', 'Aucune occurrence trouvée')}"

            self.txt_area.delete('1.0', tk.END)
            self.txt_area.insert(tk.END, message, "warning")
            self.show_loading(False)
            self.update_stats()
            return

        self.txt_area.delete('1.0', tk.END)

        for text, tag in valid_data:
            self.insert_with_highlight(text, tag)

        if self.pending_jump_timestamp:
            self.jump_to_timestamp(self.pending_jump_timestamp)
            self.pending_jump_timestamp = None
        elif not self.is_paused.get():
            self.txt_area.see(tk.END)

        self.update_stats()
        self.show_loading(False)

    def append_to_gui(self, text, tag):
        """
        Appends a single log line to the end of the text area.

        Args:
            text (str): The log line text.
            tag (str): The Tkinter tag associated with the log level.
        """
        if not self.running or self.is_paused.get():
            return

        with self.log_lock:  # Prevents mixing during writing
            self.txt_area.config(state=tk.NORMAL)
            self.insert_with_highlight(text, tag)
            if not self.is_paused.get():
                self.txt_area.see(tk.END)
            self.update_stats()

    def insert_with_highlight(self, text, base_tag):
        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])
        if self.selected_list.get() == l_ui["none"]:
            self.txt_area.insert(tk.END, text, base_tag)
            return
        kw = self.get_keywords_from_file()
        if not kw:
            self.txt_area.insert(tk.END, text, base_tag)
            return
        try:
            matches = list(
                re.finditer("|".join(re.escape(k) for k in kw), text, re.IGNORECASE)
            )
        except Exception:
            matches = []
        if not matches:
            self.txt_area.insert(tk.END, text, base_tag)
            return
        last_idx = 0
        for m in matches:
            self.txt_area.insert(tk.END, text[last_idx: m.start()], base_tag)
            self.txt_area.insert(
                tk.END, text[m.start(): m.end()], (base_tag, "highlight")
            )
            last_idx = m.end()
        self.txt_area.insert(tk.END, text[last_idx:], base_tag)

    def get_keywords_from_file(self):
        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])
        if self.selected_list.get() == l_ui["none"]:
            return []
        path = os.path.join(KEYWORD_DIR, f"{self.selected_list.get()}.txt")
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return [line.strip() for line in f if line.strip()]
        except Exception:
            return []

    def refresh_natural_order(self):
        """Reloads the log in file order (Fixes the issue of lines without dates)."""
        if not self.log_file_path or not os.path.exists(self.log_file_path):
            return

        self.show_loading(True)
        self.seen_lines.clear()  # Clear the cache to avoid missing lines

        try:
            with open(self.log_file_path, "r", encoding="utf-8", errors="ignore") as f:
                # Calculating the playback position
                if self.load_full_file.get():
                    lines = f.readlines()
                else:
                    f.seek(0, os.SEEK_END)
                    # We go back ~200 KB to get the last lines.
                    f.seek(max(0, f.tell() - 200000))
                    lines = f.readlines()[-1000:]

                to_display = []
                # We collect search keywords
                query = self.search_query.get().lower()

                for line in lines:
                    data = self.get_line_data(line)
                    if data:
                        text, tag = data
                        # Filter by search only (Search bar)
                        if not query or query in text.lower():
                            to_display.append((text, tag))

                # INSERTION WITHOUT SORTING (Natural order of the file)
                self.bulk_insert(to_display)

        except Exception as e:
            print(f"[ERROR] {type(e).__name__}: {e}")
            self.show_loading(False)

    def refresh_display_with_sorting(self):
        """Reads the file and applies filters with strict chronological sorting."""
        try:
            with open(self.log_file_path, "r", encoding="utf-8", errors="ignore") as f:
                # The lines are retrieved according to the mode (complete or last 1000).
                if self.load_full_file.get():
                    lines = f.readlines()
                else:
                    f.seek(0, os.SEEK_END)
                    f.seek(max(0, f.tell() - 200000))  # Lecture d'un bloc suffisant
                    lines = f.readlines()[-1000:]

                to_display = []
                for line in lines:
                    data = self.get_line_data(line)
                    if data and self.is_filter_match(data[1], data[0]):
                        # data is (full_text, level_tag)
                        to_display.append(data)

                # --- CORRECTION: CHRONOLOGICAL SORTING ---
                # Sort the list based on the text content (which starts with the date)
                to_display.sort(key=lambda x: x[0])

                # Batch insertion for performance
                self.bulk_insert(to_display)
        except Exception as e:
            print(f"[ERROR] {type(e).__name__}: {e}")

    def trigger_refresh(self, *args):
        """Triggered during a filter change or search."""
        if not self.log_file_path:
            return

        # We are temporarily stopping the addition of new lines during the refresh.
        self.txt_area.config(state=tk.NORMAL)
        self.txt_area.delete("1.0", tk.END)

        # We reload the lines from the file or an internal cache.
        # For a robust solution, we reread the relevant lines.
        self.refresh_display_with_sorting()

    def is_filter_match(self, tag, text):
        """Checks whether a line matches the active filters and the search."""
        # 1. Checking the log level (ALL, INFO filters, etc.)
        if not self.filter_vars["all"].get():
            if not self.filter_vars.get(tag, tk.BooleanVar(value=False)).get():
                return False

        # 2. Verification of textual research
        query = self.search_query.get().lower()
        if query and query not in text.lower():
            return False

        return True

    def update_tags_config(self):
        """
        Configures the visual styles (tags) for the log display area.

        This method defines how different types of log lines are rendered
        in the Text widget. It maps log levels (ERROR, WARNING, INFO, etc.)
        to specific foreground and background colors.

        Key functionalities:
        - Sets colors for standard Kodi log levels.
        - Configures the 'search' tag for highlighting search results.
        - Defines the 'summary' style for the analysis view.
        - Ensures that even when the theme changes, the log readability
          remains consistent.
        """
        c_font = (self.mono_font_family, self.font_size)

        self.txt_area.tag_configure("sel", foreground=COLOR_TEXT_BRIGHT)

        for tag_name, color in LOG_COLORS.items():
            if tag_name not in ["highlight_bg", "highlight_fg"]:
                self.txt_area.tag_configure(tag_name, foreground=color, font=c_font)

        self.txt_area.tag_config(
            "highlight",
            background=LOG_COLORS["highlight_bg"],
            foreground=LOG_COLORS["highlight_fg"],
            font=(c_font[0], self.font_size),
        )

        self.txt_area.configure(bg=COLOR_BG_MAIN, font=c_font)
        self.font_label.config(text=str(self.font_size))
        self.txt_area.tag_raise("sel")

    def update_stats(self):
        if not self.log_file_path:
            self.sep_lines.pack_forget()
            self.label_lines.pack_forget()
            self.sep_size.pack_forget()
            self.label_size.pack_forget()
            return

        # 1. Recovery of current states
        try:
            current_text = self.stats_var.get()
            current_count = int("".join(filter(str.isdigit, current_text)))
        except (ValueError, TypeError):
            current_count = -1

        current_pause = self.is_paused.get()
        current_limit = self.load_full_file.get()  # Etat du mode "Infini"

        # 2. UPDATE CONDITION:
        # Refresh only if one of these 3 elements has changed
        if (
            current_count == self.last_line_count
            and current_pause == self.last_pause_state
            and current_limit == self.last_limit_state
        ):
            return

        # 3. Memorization of new states
        self.last_line_count = current_count
        self.last_pause_state = current_pause
        self.last_limit_state = current_limit

        l = LANGS.get(self.current_lang.get(), LANGS["EN"])

        self.sep_lines.pack_forget()
        self.label_lines.pack_forget()
        self.sep_size.pack_forget()
        self.label_size.pack_forget()
        self.sep_limit.pack_forget()
        self.label_limit.pack_forget()
        self.sep_pause.pack_forget()
        self.label_pause.pack_forget()

        # --- TOTAL NUMBER OF LINES ---
        if self.stats_var.get() and "N/A" not in self.stats_var.get():
            self.sep_lines.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=2)
            self.label_lines.pack(side=tk.LEFT)
        else:
            self.sep_lines.pack_forget()
            self.label_lines.pack_forget()

        # --- Bloc FILE SIZE ---
        size_text = self.size_var.get()
        if size_text and "N/A" not in size_text:
            # Size analysis to change color
            try:
                # The number is extracted from the text (e.g., "12.5 MB" -> 12.5).
                size_value_str = (
                    size_text.split(":")[1].strip() if ":" in size_text else size_text
                )
                size_value = float(re.findall(r"[-+]?\d*\.\d+|\d+", size_value_str)[0])
                is_mb = "Mo" in size_text or "MB" in size_text

                # If it is in MB and > 10, we put it in red.
                if is_mb and size_value > self.max_size_mb:
                    self.label_size.config(fg=LOG_COLORS["error"])
                else:
                    self.label_size.config(fg=COLOR_TEXT_BRIGHT)
            except Exception:
                # In case of an analysis error, the default color is retained.
                self.label_size.config(fg=COLOR_TEXT_BRIGHT)

            self.sep_size.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=2)
            self.label_size.pack(side=tk.LEFT)
        else:
            self.sep_size.pack_forget()
            self.label_size.pack_forget()

        # --- Bloc LIMIT ---
        if not self.load_full_file.get():
            self.limit_var.set(l["limit"])
            self.sep_limit.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=2)
            self.label_limit.pack(side=tk.LEFT)
        else:
            self.limit_var.set("")
            self.sep_limit.pack_forget()
            self.label_limit.pack_forget()

        # --- Bloc PAUSE ---
        if self.is_paused.get():
            self.paused_var.set(l["paused"])
            self.sep_pause.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=2)
            self.label_pause.pack(side=tk.LEFT)
        else:
            self.paused_var.set("")
            self.sep_pause.pack_forget()
            self.label_pause.pack_forget()

    def scheduled_stats_update(self):
        if self.running and self.log_file_path:
            size_str, real_total = self.get_file_info()
            l = LANGS.get(self.current_lang.get(), LANGS["EN"])
            self.stats_var.set(l["stats_simple"].format(real_total))
            self.size_var.set(l["file_size_text"].format(size_str))
        self.root.after(5000, self.scheduled_stats_update)

    def get_file_info(self):
        if not self.log_file_path or not os.path.exists(self.log_file_path):
            return "0 KB", 0
        try:
            size_bytes = os.path.getsize(self.log_file_path)
            with open(self.log_file_path, "rb") as f:
                line_count = sum(1 for _ in f)
            temp_size = size_bytes
            for unit in ["B", "KB", "MB", "GB"]:
                if temp_size < 1024:
                    return f"{temp_size:.2f} {unit}", line_count
                temp_size /= 1024
        except Exception:
            pass
        return "N/A", 0

    def jump_to_timestamp(self, timestamp):
        self.root.after(100, lambda: self._execute_jump(timestamp))

    def _execute_jump(self, timestamp):
        idx = self.txt_area.search(timestamp, "1.0", tk.END)
        if idx:
            self.txt_area.see(idx)
            start_line = f"{idx} linestart"
            end_line = f"{idx} lineend"
            self.txt_area.tag_add("highlight", start_line, end_line)
            self.root.after(
                3000, lambda: self.txt_area.tag_remove("highlight", "1.0", tk.END)
            )

    def find_and_highlight_timestamp(self, target_ts, target_content=None):
        """Search for the timestamp and validate with the line content to avoid duplicates."""
        self.txt_area.tag_remove("highlight_jump", "1.0", tk.END)

        search_pos = "1.0"
        found_final_idx = None

        while True:
            # We are looking for the next occurrence of the timestamp
            idx = self.txt_area.search(target_ts, search_pos, stopindex=tk.END)
            if not idx:
                break  # No more occurrences found

            # If there is comparison content, the entire line is checked.
            if target_content:
                current_line_text = self.txt_area.get(
                    idx + " linestart", idx + " lineend"
                ).strip()

                # Comparison: if the current line contains the target content
                if target_content in current_line_text:
                    found_final_idx = idx
                    break
            else:
                # If there is no comparison content, take the first one found (fallback).
                found_final_idx = idx
                break

            # Otherwise, we continue the search after this line.
            search_pos = self.txt_area.index(idx + " lineend")

        # IF WE FOUND THE EXACT LINE
        if found_final_idx:
            line_end = self.txt_area.index(f"{found_final_idx} lineend")

            # Position the cursor (INSERT)
            self.txt_area.mark_set(tk.INSERT, found_final_idx)

            # Force focus on the text area to validate the position
            self.txt_area.focus_set()

            # Scroll to the line
            self.txt_area.see(found_final_idx)

            # 3. Apply Yellow/Black highlighting
            self.txt_area.tag_add("highlight_temp", found_final_idx, line_end)
            self.txt_area.tag_config(
                "highlight_temp",
                background=LOG_COLORS["highlight_bg"],
                foreground=LOG_COLORS["highlight_fg"],
                font=(self.mono_font_family, self.font_size, "bold"),
            )

            # Delete after 5 seconds
            self.root.after(
                5000, lambda: self.txt_area.tag_remove("highlight_temp", "1.0", tk.END)
            )

    def on_double_click_line(self, event):
        """Double-click management: Full reset + Pause + Exact search (TS + Content)."""
        self.txt_area.tag_remove("sel", "1.0", tk.END)

        try:
            # 1. Retrieve the index and complete content of the clicked line
            line_index = self.txt_area.index(tk.CURRENT)
            line_content = self.txt_area.get(
                line_index + " linestart", line_index + " lineend"
            ).strip()

            # Extracting the timestamp for the initial search
            timestamp_match = re.search(
                r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}", line_content
            )
            if not timestamp_match:
                return

            target_ts = timestamp_match.group(0)
            # We also keep the entire line (or a large part of it) to remove any ambiguity.
            target_content = line_content

        except Exception as e:
            print(f"[ERROR] {type(e).__name__}: {e}")
            return

        # 2. Complete reset of filters
        self.reset_all_filters()

        # 3. Pause
        self.is_paused.set(True)
        if hasattr(self, "btn_pause"):
            self.btn_pause.config(text="▶ RESUME", bg=COLOR_DANGER)

        # 4. Force the interface to update so that the entire log is loaded.
        self.root.update_idletasks()

        # 5. Search with TIMESTAMP and CONTENT
        self.find_and_highlight_timestamp(target_ts, target_content)

        return "break"
