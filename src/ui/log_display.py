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
            # You can choose to ignore it or leave it as is
            # If you want to remove it: return None
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
        """Inserts a set of data into the text box with detailed filter info if empty."""
        if not self.log_file_path:
            self.check_log_loaded()
            return

        if not self.running:
            return

        valid_data = [d for d in data_list if d is not None]
        self.txt_area.config(state=tk.NORMAL)

        if not valid_data:
            # Check if we should ignore this empty call
            current_text = self.txt_area.get("1.0", tk.END).strip()
            if current_text != "" and "Aucune" not in current_text:
                self.show_loading(False)
                self.update_stats()
                return

            # --- BUILD DETAILED MESSAGE ---
            l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])

            # Clear the text area
            self.txt_area.delete('1.0', tk.END)

            # Configure tags for colored text
            self.txt_area.tag_configure("filter_header", foreground=COLOR_ACCENT, font=(self.mono_font_family, self.font_size, "bold"))
            self.txt_area.tag_configure("filter_list", foreground=COLOR_TEXT_MAIN, font=(self.mono_font_family, self.font_size))
            self.txt_area.tag_configure("no_match_text", foreground=LOG_COLORS["error"], font=(self.mono_font_family, self.font_size, "bold"))
            self.txt_area.tag_configure("separator", foreground=COLOR_SEPARATOR)

            # Header with spacing
            self.txt_area.insert(tk.END, "\n\n\n\n\t\t")
            self.txt_area.insert(tk.END, l_ui.get('filter_applied', 'Applied filter(s):'), "filter_header")
            self.txt_area.insert(tk.END, "\n")

            # Horizontal separator line
            self.txt_area.insert(tk.END, "\t\t" + "─" * 65 + "\n", "separator")

            # Padding width for labels alignment
            pad = 25

            # 1. Message types filter
            if not self.filter_vars["all"].get():
                display_order = [
                    ("info", "info"),
                    ("warning", "warn"),
                    ("error", "err"),
                    ("debug", "debug")
                ]

                active_labels = []
                for internal_key, trans_key in display_order:
                    if self.filter_vars.get(internal_key) and self.filter_vars[internal_key].get():
                        active_labels.append(l_ui.get(trans_key, trans_key))

                if active_labels:
                    label = f" - {l_ui.get('type_filter', 'Message type')}"
                    type_str = ", ".join(active_labels)
                    # Align using the pad variable
                    self.txt_area.insert(tk.END, f"\t\t{label:<{pad}} : \"{type_str}\"\n", "filter_list")

            # 2. Keyword search filter
            query = self.search_query.get().strip()
            if query:
                label = f" - {l_ui.get('keyword_filter', 'Keyword search')}"
                self.txt_area.insert(tk.END, f"\t\t{label:<{pad}} : \"{query}\"\n", "filter_list")

            # 3. Keyword list filter
            kw_list = self.selected_list.get()
            if kw_list and kw_list != l_ui.get("none", "None"):
                label = f" - {l_ui.get('list_filter', 'List search')}"
                self.txt_area.insert(tk.END, f"\t\t{label:<{pad}} : \"{kw_list}\"\n", "filter_list")

            # Add second separator line
            self.txt_area.insert(tk.END, "\t\t" + "─" * 65 + "\n", "separator")

            # Final "No matches" message
            final_no_match = l_ui.get('no_match', "❌ No matches found")
            self.txt_area.insert(tk.END, f"\n\t\t{final_no_match}", "no_match_text")

            self.show_loading(False)
            self.update_stats()
            return

        # Normal insertion if valid_data exists
        self.txt_area.delete('1.0', tk.END)
        for text, tag in valid_data:
            self.insert_with_highlight(text, tag)

        if self.pending_jump_timestamp:
            self.jump_to_timestamp(self.pending_jump_timestamp)
            self.pending_jump_timestamp = None
        elif not self.is_paused.get():
            # Get current horizontal position
            current_x = self.txt_area.xview()[0]

            # Scroll to the end vertically
            self.txt_area.see(tk.END)

            # Restore the horizontal position
            self.txt_area.xview_moveto(current_x)

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
                # Get current horizontal position
                current_x = self.txt_area.xview()[0]

                # Scroll to the end vertically
                self.txt_area.see(tk.END)

                # Restore the horizontal position
                self.txt_area.xview_moveto(current_x)

            self.update_stats()

    def insert_with_highlight(self, text, base_tag):
        """
        Inserts log lines and applies different highlight colors:
        - Blue for keywords from the search bar.
        - Yellow for keywords from the loaded list.
        """
        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])

        # 1. Get terms from search bar
        search_term = self.search_query.get().strip()

        # 2. Get terms from keyword list
        list_keywords = []
        if self.selected_list.get() != l_ui["none"]:
            list_keywords = self.get_keywords_from_file() or []

        # 3. Create a map of keyword -> tag_name
        # We use a dict to know which color to apply to which word
        keyword_to_tag = {}

        # Add list keywords (Yellow)
        for k in list_keywords:
            if k: keyword_to_tag[k.lower()] = "highlight"

        # Add search term (Blue) - This overwrites if the word is in both,
        # giving priority to the search bar color.
        if search_term:
            keyword_to_tag[search_term.lower()] = "search_bar_highlight"

        if not keyword_to_tag:
            self.txt_area.insert(tk.END, text, base_tag)
            return

        try:
            # Sort keywords by length (longest first) to avoid partial matching issues
            sorted_keys = sorted(keyword_to_tag.keys(), key=len, reverse=True)
            pattern = "|".join(re.escape(k) for k in sorted_keys)
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
        except Exception:
            matches = []

        if not matches:
            self.txt_area.insert(tk.END, text, base_tag)
            return

        # 4. Insert text with specific tags
        last_idx = 0
        for m in matches:
            # Insert text before the match
            self.txt_area.insert(tk.END, text[last_idx: m.start()], base_tag)

            # Determine which tag to use for this specific match
            matched_text = m.group(0).lower()
            tag_to_apply = keyword_to_tag.get(matched_text, "highlight")

            # Apply both the base tag (log level color) and the specific highlight (background)
            self.txt_area.insert(
                tk.END, text[m.start(): m.end()], (base_tag, tag_to_apply)
            )
            last_idx = m.end()

        # Insert remaining text
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
        if not self.check_log_loaded():
            return

        if not self.check_log_available():
            return

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
        Includes distinct highlights for search bar and keyword lists.
        """
        c_font = (self.mono_font_family, self.font_size)

        self.txt_area.tag_configure("sel", foreground=COLOR_TEXT_BRIGHT)

        # Standard log levels (info, warning, error, debug)
        for tag_name, color in LOG_COLORS.items():
            # Skip the highlight colors to avoid applying them as text foregrounds
            if tag_name not in ["highlight_kwl_bg", "highlight_kwl_fg",
                               "highlight_kws_bg", "highlight_kws_fg"]:
                self.txt_area.tag_configure(tag_name, foreground=color, font=c_font)

        # --- TAG 1: KEYWORD LIST HIGHLIGHT (Yellow) ---
        self.txt_area.tag_configure(
            "highlight", # This name is used for the keyword list
            background=LOG_COLORS["highlight_kwl_bg"],
            foreground=LOG_COLORS["highlight_kwl_fg"],
            font=c_font,
        )

        # --- TAG 2: SEARCH BAR HIGHLIGHT (Blue) ---
        self.txt_area.tag_configure(
            "search_bar_highlight", # New tag name for search bar
            background=LOG_COLORS["highlight_kws_bg"],
            foreground=LOG_COLORS["highlight_kws_fg"],
            font=c_font,
        )

        self.txt_area.configure(bg=COLOR_BG_MAIN, font=c_font)
        self.font_label.config(text=str(self.font_size))

        # Ensure selection is always visible on top of highlights
        self.txt_area.tag_raise("sel")
        # Ensure search bar highlight has priority over list highlight if both match
        self.txt_area.tag_raise("search_bar_highlight")

    def update_stats(self):
        """
        Updates the visibility and content of stats labels in the bottom bar.
        Now tracks file size changes to prevent UI sync issues on startup.
        """
        if not self.log_file_path:
            # Hide all stats widgets
            self.sep_lines.pack_forget()
            self.label_lines.pack_forget()
            self.sep_size.pack_forget()
            self.label_size.pack_forget()

            # Fetch translation for the "Select a LOG file" message
            l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])

            # Manually update the footer label since textvariable was removed in ui_builder.py
            if hasattr(self, 'update_footer_path'):
                self.update_footer_path(l_ui.get("sel", "Sélectionnez un fichier LOG."))

            return

        # 1. Recovery of current states
        try:
            current_text = self.stats_var.get()
            current_count = int(''.join(filter(str.isdigit, current_text)))
        except (ValueError, TypeError):
            current_count = -1

        current_pause = self.is_paused.get()
        current_limit = self.load_full_file.get()
        current_wrap = self.wrap_mode.get()
        current_size = self.size_var.get() # Captured file size

        # 2. UPDATE CONDITION:
        # Added check for current_size to prevent skipping updates when size changes!
        if (current_count == getattr(self, 'last_line_count', None) and
                current_pause == getattr(self, 'last_pause_state', None) and
                current_limit == getattr(self, 'last_limit_state', None) and
                current_wrap == getattr(self, 'last_wrap_state', None) and
                current_size == getattr(self, 'last_size_text', '')):
            return

        # 3. Memorization of new states
        self.last_line_count = current_count
        self.last_pause_state = current_pause
        self.last_limit_state = current_limit
        self.last_wrap_state = current_wrap
        self.last_size_text = current_size

        l = LANGS.get(self.current_lang.get(), LANGS["EN"])

        # --- Format line count with spaces as thousands separator ---
        if current_count >= 0 and "N/A" not in self.stats_var.get():
            # Python's native comma separator replaced by a space
            formatted_count = f"{current_count:,}".replace(",", " ")
            self.stats_var.set(l["stats_simple"].format(formatted_count))

        self.sep_lines.pack_forget()
        self.label_lines.pack_forget()
        self.sep_size.pack_forget()
        self.label_size.pack_forget()
        self.sep_limit.pack_forget()
        self.label_limit.pack_forget()
        self.sep_wrap.pack_forget()
        self.label_wrap.pack_forget()
        self.sep_pause.pack_forget()
        self.label_pause.pack_forget()

        # --- Bloc NUMBER OF LINES ---
        if self.stats_var.get() and "N/A" not in self.stats_var.get():
            self.sep_lines.pack(side=tk.LEFT, fill=tk.Y, padx=self.sc(20), pady=2)
            self.label_lines.pack(side=tk.LEFT)
        else:
            self.sep_lines.pack_forget()
            self.label_lines.pack_forget()

        # --- FILE SIZE Block ---
        size_text = self.size_var.get()
        if size_text and "N/A" not in size_text:
            # Size analysis to change color
            try:
                # The number is extracted from the text (e.g., "12.5 MB" -> 12.5).
                size_value_str = size_text.split(':')[1].strip() if ":" in size_text else size_text
                size_value = float(re.findall(r"[-+]?\d*\.\d+|\d+", size_value_str)[0])
                is_mb = "Mo" in size_text or "MB" in size_text

                # If it is in MB and > max_size_mb, we put it in red.
                if is_mb and size_value > self.max_size_mb:
                    self.label_size.config(fg=LOG_COLORS["error"])
                    self.label_lines.config(fg=LOG_COLORS["error"])

                    # --- Automatic safety limit when crossing the threshold ---
                    # If we haven't auto-limited yet AND we are in full load mode
                    if not getattr(self, "has_auto_limited", False) and self.load_full_file.get():
                        self.load_full_file.set(False) # Activate the 1000-line limit
                        self.has_auto_limited = True   # Remember that we auto-limited it
                else:
                    self.label_size.config(fg=COLOR_TEXT_MAIN)
                    self.label_lines.config(fg=COLOR_TEXT_MAIN)
                    # Reset the flag if the file becomes smaller again (unlikely but clean)
                    self.has_auto_limited = False

            except Exception:
                # In case of an analysis error, the default color is retained.
                self.label_size.config(fg=COLOR_TEXT_MAIN)
                self.label_lines.config(fg=COLOR_TEXT_MAIN)

            self.sep_size.pack(side=tk.LEFT, fill=tk.Y, padx=self.sc(20), pady=2)
            self.label_size.pack(side=tk.LEFT)
        else:
            self.sep_size.pack_forget()
            self.label_size.pack_forget()
            self.label_lines.config(fg=COLOR_TEXT_MAIN)

        # --- LIMIT Block ---
        txt_limit = l["limit"]
        txt_unlimited = l.get("unlimited", "⚠️ Unlimited")

        if not self.load_full_file.get():
            self.limit_var.set(txt_limit)
            self.label_limit.config(fg=COLOR_TEXT_MAIN) # Standard color for "Info"
        else:
            self.limit_var.set(txt_unlimited)
            self.label_limit.config(fg=COLOR_WARNING)   # Warning color for "Unlimited"

        # Always pack if a file is loaded to ensure it doesn't disappear
        self.sep_limit.pack(side=tk.LEFT, fill=tk.Y, padx=self.sc(20), pady=2)
        self.label_limit.pack(side=tk.LEFT)

        # --- Bloc LINE BREAK ---
        if self.wrap_mode.get():
            self.wrap_var.set(l["line_break"])
            self.sep_wrap.pack(side=tk.LEFT, fill=tk.Y, padx=self.sc(20), pady=2)
            self.label_wrap.pack(side=tk.LEFT)
        else:
            self.wrap_var.set("")
            self.sep_wrap.pack_forget()
            self.label_wrap.pack_forget()

        # --- PAUSE Block ---
        if self.is_paused.get():
            self.paused_var.set(l["paused"])
            self.sep_pause.pack(side=tk.LEFT, fill=tk.Y, padx=self.sc(20), pady=2)
            self.label_pause.pack(side=tk.LEFT)
        else:
            self.paused_var.set("")
            self.sep_pause.pack_forget()
            self.label_pause.pack_forget()

    def scheduled_stats_update(self):
        """
        Periodically updates file statistics (lines and size) and forces
        the UI elements to refresh their visibility.
        """
        if self.running and self.log_file_path:
            size_str, real_total = self.get_file_info()
            l = LANGS.get(self.current_lang.get(), LANGS["EN"])

            # --- Formatting with a thousands separator ---
            try:
                # We're trying to convert it to an integer to apply the format
                formatted_total = f"{int(real_total):,}".replace(",", " ")
            except (ValueError, TypeError):
                # If it's "N/A" or text, leave it as is
                formatted_total = real_total

            # We use 'formatted_total' instead of 'real_total'
            self.stats_var.set(l["stats_simple"].format(formatted_total))
            self.size_var.set(l["file_size_text"].format(size_str))

            # --- FIX: Update the footer label according to the unlimited toggle state ---
            if self.load_full_file.get():
                limit_text = l.get("unlimited", "⚠️ Unlimited")
            else:
                limit_text = l.get("limit", "ℹ️ 1000 lines max")

            # Apply the text.
            # Check if you are using a StringVar (like stats_var) or direct Label config.
            # Replace 'self.limit_var' or 'self.label_limit' with your actual variable name!
            if hasattr(self, 'limit_var'):
                self.limit_var.set(limit_text)
            elif hasattr(self, 'label_limit'):
                self.label_limit.config(text=limit_text)

            # --- Force the UI to show/hide labels based on the new values ---
            self.update_stats()

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
                background=LOG_COLORS["highlight_kwl_bg"],
                foreground=LOG_COLORS["highlight_kwl_fg"],
                font=(self.mono_font_family, self.font_size),
            )

            # Delete after 5 seconds
            self.root.after(
                5000, lambda: self.txt_area.tag_remove("highlight_temp", "1.0", tk.END)
            )

    def on_double_click_line(self, event):
        """
        Double-click management: Full reset + Pause + Exact search (TS + Content).
        """
        # --- NEW SECURITY CHECK ---
        # If no log is loaded, show the warning message and stop the event
        if not self.check_log_loaded():
            return "break"


        if not self.check_log_available():
            return "break"

        # 1. Clear selection to avoid visual conflicts
        self.txt_area.tag_remove("sel", "1.0", tk.END)

        try:
            # 2. Retrieve the index and complete content of the clicked line
            line_index = self.txt_area.index(tk.CURRENT)
            line_content = self.txt_area.get(
                line_index + " linestart", line_index + " lineend"
            ).strip()

            if not line_content:
                return

            # Extracting the timestamp for the initial search
            timestamp_match = re.search(
                r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}", line_content
            )

            if not timestamp_match:
                return

            target_ts = timestamp_match.group(0)
            # Keep the entire line content to remove any ambiguity during search
            target_content = line_content

        except Exception as e:
            print(f"[ERROR] {type(e).__name__}: {e}")
            return

        # 3. Complete reset of filters to ensure the line is visible
        self.reset_all_filters()

        # 4. Pause monitoring to let the user analyze the specific line
        self.is_paused.set(True)
        if hasattr(self, "btn_pause"):
            self.btn_pause.config(text="▶ RESUME", bg=COLOR_DANGER)

        # 5. Force the interface to update so that the entire log is loaded if needed
        self.root.update_idletasks()

        # 6. Search with TIMESTAMP and CONTENT
        self.find_and_highlight_timestamp(target_ts, target_content)

        return "break"

    def on_mouse_wheel_font_resize(self, event):
        """
        Handles Ctrl + Mouse Wheel to increase or decrease font size.
        Simulates a click on the + or - buttons.
        """
        # Windows and macOS use event.delta
        if event.delta:
            if event.delta > 0:
                # Scrolled up -> Increase font
                self.increase_font()
            else:
                # Scrolled down -> Decrease font
                self.decrease_font()

        # Linux handles scrolling via mouse buttons 4 and 5
        else:
            if event.num == 4:
                self.increase_font()
            elif event.num == 5:
                self.decrease_font()

        # "break" prevents the text widget from scrolling the log at the same time
        return "break"
