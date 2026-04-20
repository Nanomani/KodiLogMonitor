import tkinter as tk
import customtkinter as ctk
import os
import re
from datetime import datetime

from config import *
from languages import LANGS


def _pad_line(text: str, chars_label: str = "chars") -> str:
    """
    Prepares a log line for display:
    1. Truncates lines exceeding LOG_MAX_LINE_DISPLAY characters and appends a
       translated suffix with the number of hidden characters.
       The source file is never modified.
    2. Pads to LOG_MIN_LINE_WIDTH so the horizontal scroll region stays stable.
    """
    has_newline = text.endswith("\n")
    content = text[:-1] if has_newline else text

    if len(content) > LOG_MAX_LINE_DISPLAY:
        hidden = len(content) - LOG_MAX_LINE_DISPLAY
        content = content[:LOG_MAX_LINE_DISPLAY] + f"  […+{hidden:,} {chars_label}]"

    content = content.ljust(LOG_MIN_LINE_WIDTH)
    return content + "\n" if has_newline else content


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

        # Exclusion list check (cached lowercase patterns, loaded from file).
        # Short-circuits immediately when any pattern matches — O(n_patterns).
        if self.exclude_patterns and any(exc in low for exc in self.exclude_patterns):
            return None

        q = self.search_query.get().lower()
        current_tag = None
        if " error " in low or " critical " in low:
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
            # Skip the no-results screen only when real log content is visible.
            # If the no-results screen is already showing (_no_results_showing=True),
            # always rebuild it so the filter summary reflects the current state.
            if not getattr(self, "_no_results_showing", False):
                current_text = self.txt_area.get("1.0", tk.END).strip()
                if current_text:
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
            self.txt_area.insert(tk.END, "\n\n\n\n\t")
            self.txt_area.insert(tk.END, l_ui.get('filter_applied', 'Applied filter(s):'), "filter_header")
            self.txt_area.insert(tk.END, "\n")

            # --- Collect rows to display (label, value) ---
            rows = []

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
                    rows.append((
                        f" - {l_ui.get('type_filter', 'Message type')}",
                        ", ".join(active_labels)
                    ))

            # 2. Keyword search filter
            query = self.search_query.get().strip()
            if query:
                rows.append((f" - {l_ui.get('keyword_filter', 'Keyword search')}", query))

            # 3. Keyword list filter
            kw_list = self.selected_list.get()
            if kw_list and kw_list != l_ui.get("none", "None"):
                rows.append((f" - {l_ui.get('list_filter', 'List search')}", kw_list))

            # 4. Search scope (always shown)
            scope_value = (
                l_ui.get("scope_full_log", "Full log")
                if self.load_full_file.get()
                else l_ui.get("scope_last_1000", "Last 1,000 lines")
            )
            rows.append((l_ui.get("search_scope", " - Search scope"), scope_value))

            # Compute pad from the longest label so all ":" align regardless of language
            pad = max(len(label) for label, _ in rows) + 1

            # Horizontal separator line (extra margin so values have room too)
            sep_width = pad + 35
            self.txt_area.insert(tk.END, "\t" + "─" * sep_width + "\n", "separator")

            for label, value in rows:
                self.txt_area.insert(tk.END, f"\t{label:<{pad}} : \"{value}\"\n", "filter_list")

            # Add second separator line
            self.txt_area.insert(tk.END, "\t" + "─" * sep_width + "\n", "separator")

            # Final "No matches" message
            final_no_match = l_ui.get('no_match', "❌ No matches found")
            self.txt_area.insert(tk.END, f"\n\t{final_no_match}", "no_match_text")
            self._no_results_showing = True   # Flag: no-results screen is active

            self.show_loading(False)
            self.update_stats()
            return

        # Normal insertion if valid_data exists
        self._no_results_showing = False      # Flag: real content is being displayed
        self.txt_area.delete('1.0', tk.END)

        # Hoist keyword detection outside the loop (avoid N Tkinter .get() calls)
        l_ui_bulk   = LANGS.get(self.current_lang.get(), LANGS["EN"])
        search_term = self.search_query.get().strip()
        has_list    = self.selected_list.get() not in ("", l_ui_bulk.get("none", "None"))
        list_kw     = self.get_keywords_from_file() if has_list else []

        chars_label = l_ui_bulk.get("truncated_chars", "chars")

        if not search_term and not list_kw:
            # Fast path: no highlighting needed.
            # Batch consecutive lines that share the same tag into a single insert()
            # call. This reduces the number of Tk tag-range B-tree entries from N
            # (one per line) to at most the number of tag transitions, which for a
            # typical log file is orders of magnitude smaller. The result is
            # dramatically faster scrolling on large files.
            prev_tag = None
            batch    = []
            for text, tag in valid_data:
                padded = _pad_line(text, chars_label)
                if tag == prev_tag:
                    batch.append(padded)
                else:
                    if batch:
                        self.txt_area.insert(tk.END, "".join(batch), prev_tag)
                    prev_tag = tag
                    batch    = [padded]
            if batch:
                self.txt_area.insert(tk.END, "".join(batch), prev_tag)
        else:
            # Slow path: per-line keyword highlighting (unavoidable)
            for text, tag in valid_data:
                self.insert_with_highlight(_pad_line(text, chars_label), tag)

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

    def append_batch_to_gui(self, batch):
        """
        Appends a batch of (text, tag) lines to the text area in a single lock
        acquisition.  Called by monitor_loop instead of one append_to_gui() per
        line, which would flood the Tkinter event queue under high log flux.

        Behaviour mirrors append_to_gui(): silently returns when paused or stopped,
        scrolls to end, and refreshes stats once for the whole batch.
        """
        if not self.running:
            return
        if self.is_paused.get():
            return
        if not batch:
            return
        if getattr(self, "_no_results_showing", False):
            # Matching lines arrived while no-results was showing (e.g. after a log
            # rotation): rebuild the view once. trigger_refresh sets
            # _no_results_showing = False so subsequent batches are appended normally.
            self.trigger_refresh()
            return

        with self.log_lock:
            self.txt_area.config(state=tk.NORMAL)
            chars_label = LANGS.get(self.current_lang.get(), LANGS["EN"]).get("truncated_chars", "chars")
            for text, tag in batch:
                self.insert_with_highlight(_pad_line(text, chars_label), tag)
            current_x = self.txt_area.xview()[0]
            self.txt_area.see(tk.END)
            self.txt_area.xview_moveto(current_x)
            self.update_stats()

    def append_to_gui(self, text, tag):
        """
        Appends a single log line to the end of the text area.

        Args:
            text (str): The log line text.
            tag (str): The Tkinter tag associated with the log level.
        """
        if not self.running:
            return
        # Capture once to avoid a race condition with the pause toggle
        paused = self.is_paused.get()
        if paused:
            return
        if getattr(self, "_no_results_showing", False):
            # Same logic as append_batch_to_gui: a matching line arrived while
            # no-results was showing → rebuild once, then resume normal flow.
            self.trigger_refresh()
            return

        with self.log_lock:  # Prevents mixing during writing
            self.txt_area.config(state=tk.NORMAL)
            chars_label = LANGS.get(self.current_lang.get(), LANGS["EN"]).get("truncated_chars", "chars")
            self.insert_with_highlight(_pad_line(text, chars_label), tag)

            # Scroll to end (pause already checked above)
            current_x = self.txt_area.xview()[0]
            self.txt_area.see(tk.END)
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
        """
        Returns the keyword list for the currently selected list file.
        Results are cached in memory; the cache is invalidated automatically
        when the selected list or the file's modification time changes.
        """
        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])
        current_list = self.selected_list.get()
        if current_list == l_ui["none"] or not current_list:
            self._kw_cache = None
            self._kw_cache_key = None
            return []

        path = os.path.join(KEYWORD_DIR, f"{current_list}.txt")

        # Build a cache key from (list name, file mtime) so edits to the file
        # are picked up automatically without requiring a UI action.
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            mtime = 0

        cache_key = (current_list, mtime)
        if getattr(self, "_kw_cache_key", None) == cache_key and self._kw_cache is not None:
            return self._kw_cache

        # Cache miss — read from disk and store
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                keywords = [line.strip() for line in f if line.strip()]
        except Exception:
            keywords = []

        self._kw_cache = keywords
        self._kw_cache_key = cache_key
        return keywords

    def refresh_natural_order(self):
        """Reloads the log in file order (Fixes the issue of lines without dates)."""
        if not self.log_file_path or not os.path.exists(self.log_file_path):
            return

        self.show_loading(True)
        self._reset_seen_cache()  # Clear deque + O(1) set together

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
                    f.seek(max(0, f.tell() - 200000))
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
        self._last_wrap_anchor = None   # Filter change invalidates the remembered line
        # Cancel any pending debounced search and invalidate a running worker
        # so its results don't overwrite the filter refresh we're about to do.
        if getattr(self, '_search_after_id', None):
            self.root.after_cancel(self._search_after_id)
            self._search_after_id = None
        self._search_version = getattr(self, '_search_version', 0) + 1

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

        self.txt_area.tag_configure("sel", foreground=COLOR_TEXT_ON_ACCENT)  # Always white on blue selection (both themes)

        # Standard log levels (info, warning, error, debug)
        for tag_name, color in LOG_COLORS.items():
            # Skip the highlight colors to avoid applying them as text foregrounds
            if tag_name not in ["highlight_kwl_bg", "highlight_kwl_fg",
                               "highlight_kws_bg", "highlight_kws_fg"]:
                self.txt_area.tag_configure(tag_name, foreground=color, font=c_font)

        # --- TAG 1: KEYWORD LIST HIGHLIGHT (Yellow) ---
        self.txt_area.tag_configure(
            "highlight",  # This name is used for the keyword list
            background=LOG_COLORS["highlight_kwl_bg"],
            foreground=LOG_COLORS["highlight_kwl_fg"],
            font=c_font,
        )

        # --- TAG 2: SEARCH BAR HIGHLIGHT (Blue) ---
        self.txt_area.tag_configure(
            "search_bar_highlight",  # New tag name for search bar
            background=LOG_COLORS["highlight_kws_bg"],
            foreground=LOG_COLORS["highlight_kws_fg"],
            font=c_font,
        )

        # txt_area is a tk.Text widget — use standard Tkinter configure
        self.txt_area.configure(bg=COLOR_BG_MAIN, font=c_font)

        # font_label is a CTkLabel — use CTK configure
        self.font_label.configure(text=str(self.font_size))

        # Tag priority order (lowest → highest): highlight → search_bar_highlight → sel
        # tag_raise() without second arg moves a tag to the very top of the stack,
        # so the LAST call wins. sel must be raised last so the selection colour
        # always shows on top of any search/keyword highlight underneath.
        self.txt_area.tag_raise("highlight")
        self.txt_area.tag_raise("search_bar_highlight")
        self.txt_area.tag_raise("sel")

    def update_stats(self):
        """
        Fetches current file info and updates the footer stats labels.
        Called on file load, on every scheduled tick (every 4 s), and on
        state changes (pause, wrap, limit toggled).
        """
        if not self.log_file_path:
            # Hide all stats widgets
            self.sep_lines.pack_forget()
            self.label_lines.pack_forget()
            self.sep_size.pack_forget()
            self.label_size.pack_forget()
            self.sep_duration.pack_forget()
            self.label_duration.pack_forget()

            # Fetch translation for the "Select a LOG file" message
            l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])

            if hasattr(self, 'update_footer_path'):
                self.update_footer_path(l_ui.get("sel", "Sélectionnez un fichier LOG."))

            return

        l = LANGS.get(self.current_lang.get(), LANGS["EN"])

        # --- Always fetch fresh file info for accurate stats ---
        size_str, real_total = self.get_file_info()
        try:
            formatted_total = f"{int(real_total):,}".replace(",", " ")
        except (ValueError, TypeError):
            formatted_total = str(real_total)
        lines_text = l["stats_simple"].format(formatted_total)
        size_text  = l["file_size_text"].format(size_str)
        self.stats_var.set(lines_text)
        self.size_var.set(size_text)

        # Set label texts explicitly (no textvariable — avoids CTK pack_forget issue)
        self.label_lines.configure(text=lines_text)
        self.label_size.configure(text=size_text)

        self.sep_lines.pack_forget()
        self.label_lines.pack_forget()
        self.sep_size.pack_forget()
        self.label_size.pack_forget()
        self.sep_duration.pack_forget()
        self.label_duration.pack_forget()
        self.sep_limit.pack_forget()
        self.label_limit.pack_forget()
        self.sep_wrap.pack_forget()
        self.label_wrap.pack_forget()
        self.sep_pause.pack_forget()
        self.label_pause.pack_forget()

        # --- Bloc NUMBER OF LINES ---
        if lines_text and "N/A" not in lines_text:
            self.sep_lines.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=2)
            self.label_lines.pack(side=tk.LEFT)
        else:
            self.sep_lines.pack_forget()
            self.label_lines.pack_forget()

        # --- FILE SIZE Block ---
        if size_text and "N/A" not in size_text:
            # Size analysis to change color
            try:
                # The number is extracted from the text (e.g., "12.5 MB" -> 12.5).
                size_value_str = size_text.split(':')[1].strip() if ":" in size_text else size_text
                size_value = float(re.findall(r"[-+]?\d*\.\d+|\d+", size_value_str)[0])
                is_mb = "Mo" in size_text or "MB" in size_text

                # If it is in MB and > max_size_mb, we put it in red.
                if is_mb and size_value > self.max_size_mb:
                    self.label_size.configure(text_color=LOG_COLORS["error"])
                    self.label_lines.configure(text_color=LOG_COLORS["error"])

                    # --- Automatic safety limit when crossing the threshold ---
                    # If we haven't auto-limited yet AND we are in full load mode
                    if not getattr(self, "has_auto_limited", False) and self.load_full_file.get():
                        self.load_full_file.set(False)  # Activate the 1000-line limit
                        self.has_auto_limited = True     # Remember that we auto-limited it
                        # Sync button appearance immediately (no hover needed)
                        self.update_button_colors()
                        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])
                        self.limit_var.set(l_ui.get("limit", "ℹ️ 1000 lines max"))
                        self.root.update_idletasks()
                else:
                    self.label_size.configure(text_color=COLOR_TEXT_MAIN)
                    self.label_lines.configure(text_color=COLOR_TEXT_MAIN)
                    # Reset the flag if the file becomes smaller again (unlikely but clean)
                    self.has_auto_limited = False

            except Exception:
                # In case of an analysis error, the default color is retained.
                self.label_size.configure(text_color=COLOR_TEXT_MAIN)
                self.label_lines.configure(text_color=COLOR_TEXT_MAIN)

            self.sep_size.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=2)
            self.label_size.pack(side=tk.LEFT)
        else:
            self.sep_size.pack_forget()
            self.label_size.pack_forget()
            self.label_lines.configure(text_color=COLOR_TEXT_MAIN)

        # --- LOG DURATION Block ---
        duration_text = self.get_log_duration()
        if duration_text:
            self.label_duration.configure(text=duration_text)
            self.sep_duration.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=2)
            self.label_duration.pack(side=tk.LEFT)
        else:
            self.sep_duration.pack_forget()
            self.label_duration.pack_forget()

        # --- LIMIT Block ---
        txt_limit = l["limit"]
        txt_unlimited = l.get("unlimited", "⚠️ Unlimited")

        if not self.load_full_file.get():
            self.limit_var.set(txt_limit)
            self.label_limit.configure(text=txt_limit, text_color=COLOR_TEXT_MAIN)
        else:
            self.limit_var.set(txt_unlimited)
            self.label_limit.configure(text=txt_unlimited, text_color=COLOR_WARNING)

        # Always pack if a file is loaded to ensure it doesn't disappear
        self.sep_limit.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=2)
        self.label_limit.pack(side=tk.LEFT)

        # --- Bloc LINE BREAK ---
        if self.wrap_mode.get():
            self.wrap_var.set(l["line_break"])
            self.label_wrap.configure(text=l["line_break"])
            self.sep_wrap.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=2)
            self.label_wrap.pack(side=tk.LEFT)
        else:
            self.wrap_var.set("")
            self.sep_wrap.pack_forget()
            self.label_wrap.pack_forget()

        # --- PAUSE Block ---
        if self.is_paused.get():
            self.paused_var.set(l["paused"])
            self.label_pause.configure(text=l["paused"])
            self.sep_pause.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=2)
            self.label_pause.pack(side=tk.LEFT)
        else:
            self.paused_var.set("")
            self.sep_pause.pack_forget()
            self.label_pause.pack_forget()

    def scheduled_stats_update(self):
        """
        Periodically refreshes file statistics (lines, size) every 4 seconds.
        update_stats() handles the fetch and all show/hide logic.
        """
        if self.running and self.log_file_path:
            self.update_stats()

        self.root.after(4000, self.scheduled_stats_update)

    # ── File-info helpers ────────────────────────────────────────────────────────
    # Size is read instantly via os.path.getsize().
    # Line-count is computed in a daemon thread and cached; a stale value is
    # shown immediately and refreshed once the background thread completes.

    def _format_size(self, size_bytes):
        """Convert a byte count to a human-readable string."""
        temp = size_bytes
        for unit in ["B", "KB", "MB", "GB"]:
            if temp < 1024:
                return f"{temp:.2f} {unit}"
            temp /= 1024
        return "N/A"

    def _refresh_line_count_async(self, path, size_bytes):
        """
        Counts lines in *path* on a background thread and updates the footer
        labels on the main thread when done.  Skipped if a count job is already
        running for the same file+size combination.
        """
        import threading

        # Deduplicate: don't launch a second thread for the same snapshot
        job_key = (path, size_bytes)
        if getattr(self, "_line_count_job", None) == job_key:
            return
        self._line_count_job = job_key

        def _count():
            try:
                with open(path, "rb") as f:
                    count = sum(1 for _ in f)
            except Exception:
                count = 0
            # Store result and schedule a lightweight UI refresh on the main thread
            self._cached_line_count = count
            self._cached_line_count_key = job_key
            try:
                self.root.after(0, self._apply_cached_file_info)
            except Exception:
                pass

        threading.Thread(target=_count, daemon=True).start()

    def _apply_cached_file_info(self):
        """
        Called on the main thread after a background line-count finishes.
        Refreshes only the lines / size labels without repeating the full
        update_stats() layout pass.
        """
        if not self.log_file_path:
            return
        l = LANGS.get(self.current_lang.get(), LANGS["EN"])
        count = getattr(self, "_cached_line_count", 0)
        size_str = self._format_size(
            os.path.getsize(self.log_file_path)
            if os.path.exists(self.log_file_path) else 0
        )
        try:
            formatted_total = f"{int(count):,}".replace(",", " ")
        except (ValueError, TypeError):
            formatted_total = str(count)
        lines_text = l["stats_simple"].format(formatted_total)
        size_text  = l["file_size_text"].format(size_str)
        self.stats_var.set(lines_text)
        self.size_var.set(size_text)
        self.label_lines.configure(text=lines_text)
        self.label_size.configure(text=size_text)

    def get_file_info(self):
        """
        Returns (size_str, line_count) for the current log file.
        Size is always fresh; line-count comes from the in-memory cache and a
        background thread is launched to refresh it asynchronously.
        """
        if not self.log_file_path or not os.path.exists(self.log_file_path):
            return "0 KB", 0
        try:
            size_bytes = os.path.getsize(self.log_file_path)
            size_str = self._format_size(size_bytes)

            # Use the cached line-count if available for the same file+size
            cached_key = getattr(self, "_cached_line_count_key", None)
            if cached_key == (self.log_file_path, size_bytes):
                line_count = self._cached_line_count
            else:
                # Show the last known count while the background thread runs
                line_count = getattr(self, "_cached_line_count", 0)
                self._refresh_line_count_async(self.log_file_path, size_bytes)

            return size_str, line_count
        except Exception:
            pass
        return "N/A", 0

    def get_log_duration(self):
        """
        Returns the time span covered by the log as a formatted string '🕒 HH:MM:SS',
        or an empty string if the duration cannot be determined.

        Strategy: read only the first 4 KB for the earliest timestamp and the
        last 4 KB for the latest timestamp — O(1) regardless of file size.
        """
        if not self.log_file_path or not os.path.exists(self.log_file_path):
            return ""

        TS_RE = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}")
        TS_FMT = "%Y-%m-%d %H:%M:%S.%f"
        CHUNK = 4096

        try:
            with open(self.log_file_path, "r", encoding="utf-8", errors="ignore") as f:
                # --- First timestamp: read from file start ---
                head = f.read(CHUNK)
                first_matches = TS_RE.findall(head)
                if not first_matches:
                    return ""
                first_ts = datetime.strptime(first_matches[0], TS_FMT)

                # --- Last timestamp: read from file end ---
                f.seek(0, os.SEEK_END)
                file_size = f.tell()
                f.seek(max(0, file_size - CHUNK))
                tail = f.read()
                last_matches = TS_RE.findall(tail)
                if not last_matches:
                    return ""
                last_ts = datetime.strptime(last_matches[-1], TS_FMT)

            delta = last_ts - first_ts
            if delta.total_seconds() < 1:
                return ""

            total_seconds = int(delta.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"🕒 {hours:02d}:{minutes:02d}:{seconds:02d}"

        except Exception:
            return ""

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
        Resets all filters, pauses monitoring, and scrolls to the exact line
        that was double-clicked, identified by its timestamp and full content.

        A one-shot <ButtonRelease-1> instance binding is registered before
        returning to suppress the Text widget's class binding, which would
        otherwise re-apply a word selection after the handler exits.
        Instance bindings fire before class bindings; returning "break" stops
        propagation and the binding removes itself immediately after firing.
        """
        def _clear_sel():
            self.txt_area.tag_remove("sel", "1.0", tk.END)

        def _intercept_release(e):
            self.txt_area.unbind("<ButtonRelease-1>")
            _clear_sel()
            return "break"

        if not self.check_log_loaded():
            return "break"

        if not self.check_log_available():
            return "break"

        # Clear the word selection that Tkinter's Button-1 class binding already applied
        _clear_sel()

        try:
            line_index = self.txt_area.index(tk.CURRENT)
            line_content = self.txt_area.get(
                line_index + " linestart", line_index + " lineend"
            ).strip()

            if not line_content:
                return "break"

            # Save the line text as wrap anchor so Ctrl+L can find it after any rebuild
            self._last_wrap_content = line_content
            self._last_wrap_anchor  = None  # index is stale after reset_all_filters

            timestamp_match = re.search(
                r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}", line_content
            )

            if not timestamp_match:
                return "break"

            target_ts = timestamp_match.group(0)
            target_content = line_content

        except Exception as e:
            print(f"[ERROR] {type(e).__name__}: {e}")
            return "break"

        self.reset_all_filters()

        self.is_paused.set(True)
        if hasattr(self, "update_button_colors"):
            self.update_button_colors()

        self.root.update_idletasks()

        self.find_and_highlight_timestamp(target_ts, target_content)

        _clear_sel()

        self.txt_area.bind("<ButtonRelease-1>", _intercept_release)

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
