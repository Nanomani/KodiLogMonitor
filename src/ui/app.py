# ui/app.py
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import os
import time
import sys

from collections import deque

import config
from config import *
from config import APP_THEME
from languages import LANGS
from utils import get_system_font, get_mono_font, get_emoji_font

from ui.monitor import MonitorMixin
from ui.log_display import LogDisplayMixin
from ui.session import SessionMixin
from ui.actions import ActionsMixin
from ui.ui_builder import UIBuilderMixin
from ui.timeline import TimelineMixin


class KodiLogMonitor(UIBuilderMixin, TimelineMixin, ActionsMixin, SessionMixin, LogDisplayMixin, MonitorMixin):
    """
    Main class - assembles all modules via multiple inheritance.
    Converted to CustomTkinter (CTk root window).
    """
    def __init__(self, root):
        # root is now a ctk.CTk instance
        self.root = root
        self.root.title(APP_NAME)
        self.inactivity_timer_var = tk.StringVar(value="")

        # --- 4K DYNAMIC DETECTION ---
        screen_width = self.root.winfo_screenwidth()

        if screen_width > 2560:
            self.window_geometry = DEFAULT_GEOMETRY_4K
            self.scale = 1
        elif screen_width > 1280:
            self.window_geometry = DEFAULT_GEOMETRY_FHD
            self.scale = 0.50
        else:
            self.window_geometry = DEFAULT_GEOMETRY_HD
            self.scale = 0.25

        # Window state: 'normal' or 'zoomed' (maximised).  Persisted so the app
        # reopens in the same state it was closed in.
        self.window_state = "normal"

        # --- SAFE DISPLAY MONITORING (Windows only) ---
        if sys.platform == "win32":
            from ctypes import windll
            self.last_screen_width  = windll.user32.GetSystemMetrics(0)  # SM_CXSCREEN
            self.last_screen_height = windll.user32.GetSystemMetrics(1)  # SM_CYSCREEN
            self.root.after(3000, self.periodic_display_check)

        self.enable_single_instance_var = self._load_single_instance_state()

        # Configure root background color to match dark theme
        self.root.configure(fg_color=COLOR_BG_MAIN)
        self.last_activity_time = time.time()
        self.inactivity_limit = DEFAULT_TIME_INACTIVITY
        self.last_line_count = 0
        self.last_pause_state = False
        self.last_limit_state = False
        self.last_wrap_state = False

        # --- Font families for cross-platform compatibility ---
        self.main_font_family = get_system_font()
        self.mono_font_family = get_mono_font()
        self.emoji_font_family = get_emoji_font()

        # Extract first font family name (CTkFont needs a single string)
        self._main_font = self.main_font_family[0] if isinstance(self.main_font_family, tuple) else self.main_font_family
        self._mono_font = self.mono_font_family[0] if isinstance(self.mono_font_family, tuple) else self.mono_font_family
        self._emoji_font = self.emoji_font_family[0] if isinstance(self.emoji_font_family, tuple) else self.emoji_font_family

        self.set_window_icon()
        self.log_file_path = ""
        self.paste_url = DEFAULT_PASTE_URL
        self.max_size_mb = DEFAULT_SECURITY_FILE_MAX_SIZE_STARTUP
        self.updates_enabled = True
        self.skip_version = ""
        self.debug_mode = False           # Toggled by Ctrl+Shift+D; persisted in config
        self._colors_file_mtime = None    # mtime snapshot taken when 🎨 opens the colors file
        self.running = False
        self.monitor_thread = None
        self.seen_lines = deque(maxlen=2000)
        self._seen_set = set()          # O(1) companion set for is_duplicate()
        self.pending_jump_timestamp = None
        self.log_lock = threading.Lock()
        self._search_version = 0        # Incremented on each new search to cancel stale workers
        self._search_after_id = None    # Pending debounce timer ID
        self._last_wrap_anchor = None   # Last explicitly-focused line index for wrap toggle
        self._last_wrap_content = None  # Line text set by double-click; survives filter resets
        self._menu_kbfocus = -1         # Keyboard-focused item index in the log context menu
        self._summary_showing = False   # True while the summary view is displayed
        self.exclude_patterns = []      # Lowercase exclusion strings, cached from file

        # --- Tkinter control variables (compatible with CTK) ---
        self.load_full_file = tk.BooleanVar(value=False)
        self.wrap_mode = tk.BooleanVar(value=False)
        self.is_paused = tk.BooleanVar(value=False)
        self.current_lang = tk.StringVar(value=self.detect_os_language())
        self.app_theme = tk.StringVar(value=APP_THEME)  # "dark" or "light"

        self.filter_vars = {
            "all":     tk.BooleanVar(value=True),
            "debug":   tk.BooleanVar(value=False),
            "info":    tk.BooleanVar(value=False),
            "warning": tk.BooleanVar(value=False),
            "error":   tk.BooleanVar(value=False)
        }

        self.search_query = tk.StringVar()
        self.selected_list = tk.StringVar()
        self.font_size = 10
        self.show_google_search = tk.BooleanVar(value=True)

        self.filter_colors = {
            "all":     COLOR_ACCENT,
            "debug":   LOG_COLORS["debug"],
            "info":    LOG_COLORS["info"],
            "warning": LOG_COLORS["warning"],
            "error":   LOG_COLORS["error"]
        }

        # --- Cursor visibility management ---
        self.cursor_timer = None
        self.cursor_visible = True

        # Build all UI widgets (CTK-converted)
        self.setup_ui()
        self.load_exclude_patterns()
        self.load_session()

        # --- Reset geometry if empty after session load ---
        if not self.window_geometry or self.window_geometry.strip() == "":
            if screen_width > 2560:
                self.window_geometry = DEFAULT_GEOMETRY_4K
            elif screen_width > 1280:
                self.window_geometry = DEFAULT_GEOMETRY_FHD
            else:
                self.window_geometry = DEFAULT_GEOMETRY_HD

        # ── Orphan debug file cleanup ─────────────────────────────────────────
        # If the app crashed or the file handle was not released properly on the
        # previous run, the debug log file may still exist while debug_mode is off.
        if not self.debug_mode:
            try:
                if os.path.exists(DEBUG_LOG_FILE):
                    os.remove(DEBUG_LOG_FILE)
            except OSError:
                pass

        # ── Startup timing (active only when debug_mode was persisted as True) ─
        # debug_mode is now set from load_session(), so the logger is available.
        # Each startup run is preceded by a separator line for easy navigation.
        _dlog = self._get_debug_logger()
        if _dlog:
            _t_start = time.time()
            _dlog.debug("STARTUP   BEGIN")
            def _sstep(label):
                _dlog.debug("STARTUP   %s  (+%d ms)", label, (time.time() - _t_start) * 1000)
        else:
            def _sstep(label):
                pass   # no-op when debug mode is off

        _sstep("load_session done")

        # Refresh footer indicators now that session values are loaded
        self.update_notify_indicator()
        self.update_debug_indicator()
        _sstep("footer indicators updated")

        self.check_for_updates()
        _sstep("check_for_updates done")

        # Note: start_monitoring() is already called at the end of load_session()
        # if a saved log path exists. No second call is needed here.

        self.root.geometry(self.window_geometry)
        # Restore maximised state AFTER geometry so the window manager has
        # valid coordinates to fall back on when un-maximising later.
        # "zoomed" is Windows-only; Linux uses the -zoomed attribute instead.
        if self.window_state == "zoomed":
            if sys.platform == "win32":
                self.root.state("zoomed")
            else:
                self.root.attributes("-zoomed", True)
        _sstep("geometry applied")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- KEYBOARD SHORTCUTS ---

        # Close dropdown search list when clicking outside
        self.root.bind("<Button-1>", self._close_dropdown_on_outside_click)
        self.root.bind("<Configure>", self._on_window_configure)

        self.root.bind("<Control-c>", self.copy_to_clipboard)
        self.root.bind("<Control-C>", self.copy_to_clipboard)
        self.txt_area.bind("<Control-c>", self.copy_to_clipboard)
        self.txt_area.bind("<Control-C>", self.copy_to_clipboard)

        # Ctrl+A: select all text in the log area only (not bound on root to avoid
        # interfering with the search entry or other text inputs)
        self.txt_area.bind("<Control-a>", lambda e: (self.txt_area.tag_add("sel", "1.0", tk.END), "break")[1])
        self.txt_area.bind("<Control-A>", lambda e: (self.txt_area.tag_add("sel", "1.0", tk.END), "break")[1])

        self.root.bind("<Control-o>", self.open_file)
        self.root.bind("<Control-O>", self.open_file)
        self.txt_area.bind("<Control-o>", self.open_file)
        self.txt_area.bind("<Control-O>", self.open_file)

        self.root.bind("<Control-s>", self.export_log)
        self.root.bind("<Control-S>", self.export_log)
        self.txt_area.bind("<Control-s>", self.export_log)
        self.txt_area.bind("<Control-S>", self.export_log)

        self.root.bind("<Control-p>", self.upload_to_pastebin)
        self.root.bind("<Control-P>", self.upload_to_pastebin)
        self.txt_area.bind("<Control-p>", self.upload_to_pastebin)
        self.txt_area.bind("<Control-P>", self.upload_to_pastebin)

        self.root.bind("<Control-f>", self.focus_search_entry)
        self.root.bind("<Control-F>", self.focus_search_entry)
        self.txt_area.bind("<Control-f>", self.focus_search_entry)
        self.txt_area.bind("<Control-F>", self.focus_search_entry)

        self.root.bind("<Control-n>", lambda e: self.show_exclude_list())
        self.root.bind("<Control-N>", lambda e: self.show_exclude_list())
        self.txt_area.bind("<Control-n>", lambda e: self.show_exclude_list())
        self.txt_area.bind("<Control-N>", lambda e: self.show_exclude_list())

        self.root.bind("<Control-g>", self.select_clear_console_from_keyboard)
        self.root.bind("<Control-G>", self.select_clear_console_from_keyboard)
        self.txt_area.bind("<Control-g>", self.select_clear_console_from_keyboard)
        self.txt_area.bind("<Control-G>", self.select_clear_console_from_keyboard)

        # txt_area needs its own binding: the tk.Text class binding for <space>
        # returns "break" even when disabled, which would block bind_all below.
        # The instance binding fires first, handles the toggle, and its own "break"
        # prevents the Text class from interfering - no double-fire.
        self.txt_area.bind("<space>", self.toggle_pause_from_keyboard)
        # bind_all catches all other widgets (CTk buttons, scrollbars, canvas…)
        # that would otherwise consume the event before it reaches root.bind().
        self.root.bind_all("<space>", self.toggle_pause_from_keyboard)

        self.root.bind("<Control-l>", self.toggle_line_break_from_keyboard)
        self.root.bind("<Control-L>", self.toggle_line_break_from_keyboard)
        self.txt_area.bind("<Control-l>", self.toggle_line_break_from_keyboard)
        self.txt_area.bind("<Control-L>", self.toggle_line_break_from_keyboard)

        self.root.bind("<Control-t>", self.toggle_limit_from_keyboard)
        self.root.bind("<Control-T>", self.toggle_limit_from_keyboard)
        self.txt_area.bind("<Control-t>", self.toggle_limit_from_keyboard)
        self.txt_area.bind("<Control-T>", self.toggle_limit_from_keyboard)

        self.root.bind("<Control-r>", self.select_reset_all_filters_from_keyboard)
        self.root.bind("<Control-R>", self.select_reset_all_filters_from_keyboard)
        self.txt_area.bind("<Control-r>", self.select_reset_all_filters_from_keyboard)
        self.txt_area.bind("<Control-R>", self.select_reset_all_filters_from_keyboard)

        # Ctrl+Shift+D — toggle debug mode (🐞 indicator + shutdown log)
        self.root.bind("<Control-D>", self.toggle_debug_mode)
        self.txt_area.bind("<Control-D>", self.toggle_debug_mode)

        self.root.bind("<s>", self.select_show_summary_from_keyboard)
        self.root.bind("<S>", self.select_show_summary_from_keyboard)
        self.txt_area.bind("<s>", self.select_show_summary_from_keyboard)
        self.txt_area.bind("<S>", self.select_show_summary_from_keyboard)

        self.root.bind("<a>", self.select_all_filter_from_keyboard)
        self.root.bind("<A>", self.select_all_filter_from_keyboard)
        self.txt_area.bind("<a>", self.select_all_filter_from_keyboard)
        self.txt_area.bind("<A>", self.select_all_filter_from_keyboard)

        self.root.bind("<i>", self.toggle_info_filter_from_keyboard)
        self.root.bind("<I>", self.toggle_info_filter_from_keyboard)
        self.txt_area.bind("<i>", self.toggle_info_filter_from_keyboard)
        self.txt_area.bind("<I>", self.toggle_info_filter_from_keyboard)

        self.root.bind("<w>", self.toggle_warning_filter_from_keyboard)
        self.root.bind("<W>", self.toggle_warning_filter_from_keyboard)
        self.txt_area.bind("<w>", self.toggle_warning_filter_from_keyboard)
        self.txt_area.bind("<W>", self.toggle_warning_filter_from_keyboard)

        self.root.bind("<e>", self.toggle_error_filter_from_keyboard)
        self.root.bind("<E>", self.toggle_error_filter_from_keyboard)
        self.txt_area.bind("<e>", self.toggle_error_filter_from_keyboard)
        self.txt_area.bind("<E>", self.toggle_error_filter_from_keyboard)

        self.root.bind("<d>", self.toggle_debug_filter_from_keyboard)
        self.root.bind("<D>", self.toggle_debug_filter_from_keyboard)
        self.txt_area.bind("<d>", self.toggle_debug_filter_from_keyboard)
        self.txt_area.bind("<D>", self.toggle_debug_filter_from_keyboard)

        self.txt_area.bind("<m>", self.show_context_menu_from_keyboard)
        self.txt_area.bind("<M>", self.show_context_menu_from_keyboard)

        self.root.bind("<F1>", lambda e: self.show_help())
        self.txt_area.bind("<F1>", lambda e: self.show_help())

        self.root.bind("<Up>", lambda e: self.txt_area.yview_scroll(-1, "units"))
        self.root.bind("<Down>", lambda e: self.txt_area.yview_scroll(1, "units"))
        self.txt_area.bind("<Up>", lambda e: self.txt_area.yview_scroll(-1, "units"))
        self.txt_area.bind("<Down>", lambda e: self.txt_area.yview_scroll(1, "units"))

        # Ctrl+MouseWheel for font resize (Windows/macOS)
        self.txt_area.bind("<Control-MouseWheel>", self.on_mouse_wheel_font_resize)
        # Linux scrolling support
        self.txt_area.bind("<Control-Button-4>", self.on_mouse_wheel_font_resize)
        self.txt_area.bind("<Control-Button-5>", self.on_mouse_wheel_font_resize)

        # Safe vertical scroll with MouseWheel (Windows & macOS)
        self.txt_area.bind("<MouseWheel>", self.safe_vertical_scroll)
        # Linux
        self.txt_area.bind("<Button-4>", self.safe_vertical_scroll)
        self.txt_area.bind("<Button-5>", self.safe_vertical_scroll)

        # Clear the wrap anchor whenever focus leaves the log area.
        # _last_wrap_content is intentionally NOT cleared here: it must survive
        # programmatic focus changes such as reset_all_filters() calling
        # root.focus_set(), so that toggle_line_break() can still use it on the
        # first attempt after a double-click. It is cleared only by explicit
        # user single-click (Button-1 binding in ui_builder.py).
        def _clear_wrap_anchors(e):
            self._last_wrap_anchor = None
        self.txt_area.bind("<FocusOut>", _clear_wrap_anchors, add="+")

        # Escape in search field clears it and returns focus to log
        self.search_entry.bind("<Escape>", self.reset_search_and_focus_log)

        # History event bindings
        self.setup_history_events()

        # Note: filter_vars traces are intentionally omitted here.
        # on_filter_toggle() calls trigger_refresh / refresh_natural_order directly,
        # so adding traces would double-trigger with an inconsistent state in between,
        # causing a brief "no results" flash when de-selecting a filter.

        self.search_query.trace_add("write", self.clean_search_input)
        self.search_query.trace_add("write", self.on_search_change)

        self.selected_list.trace_add("write", self.on_list_change)
        self.load_full_file.trace_add("write", lambda *args: self.immediate_ui_refresh())

        # --- History Popup (tk.Toplevel with overrideredirect for frameless popup) ---
        self.history_window = tk.Toplevel(self.root)
        self.history_window.withdraw()
        self.history_window.overrideredirect(True)
        # 1px COLOR_SEPARATOR border - same technique as the context menus
        self.history_window.configure(bg=COLOR_SEPARATOR)

        # Style the history listbox to match dark theme
        self.history_listbox = tk.Listbox(
            self.history_window,
            bg=COLOR_BG_HEADER,
            fg=COLOR_TEXT_MAIN,
            selectbackground=COLOR_ACCENT,
            selectforeground=COLOR_TEXT_BRIGHT,
            font=(self._main_font, 12),
            borderwidth=0,
            highlightthickness=0,
            activestyle="none",
            exportselection=False
        )
        self.history_listbox.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        self.history_listbox.bind("<ButtonRelease-1>", self.on_history_select)

        # Max display characters before truncation with "…" in the dropdown.
        # Items longer than this get a tooltip showing the full value on hover.
        self._HIST_MAX_CHARS = 32

        # Full original items parallel to the listbox content - used for tooltip.
        self._hist_tip_items = []

        # Tooltip Toplevel for truncated history items (created once, shown/hidden).
        self._hist_tooltip = tk.Toplevel(self.root)
        self._hist_tooltip.withdraw()
        self._hist_tooltip.overrideredirect(True)
        self._hist_tooltip.configure(bg=COLOR_BG_TIPS)
        self._hist_tooltip_label = tk.Label(
            self._hist_tooltip,
            text="",
            bg=COLOR_BG_TIPS,
            fg=COLOR_TEXT_TIPS,
            font=(self._mono_font, 10),
            padx=6,
            pady=4,
        )
        self._hist_tooltip_label.pack()

        # Hover highlight for history listbox (tk.Listbox has no native hover)
        self._history_hover_idx = None

        def _on_history_motion(event):
            idx = self.history_listbox.nearest(event.y)
            # Clear any keyboard-driven selection so its native blue highlight
            # does not persist alongside the mouse hover highlight.
            self.history_listbox.selection_clear(0, tk.END)
            self._hist_highlight_idx(idx, y_offset=event.y)

        def _on_history_leave(event):
            self._hist_tooltip.withdraw()
            if self._history_hover_idx is not None:
                try:
                    self.history_listbox.itemconfigure(
                        self._history_hover_idx, background=COLOR_BG_HEADER, foreground=COLOR_TEXT_MAIN
                    )
                except tk.TclError:
                    pass
            self._history_hover_idx = None

        self.history_listbox.bind("<Motion>", _on_history_motion)
        self.history_listbox.bind("<Leave>", _on_history_leave)

        self.root.after(5000, self.scheduled_stats_update)

        # Close the history dropdown when the main window is minimised.
        # <Unmap> fires on Windows when the window is iconified (minimised button).
        self.root.bind("<Unmap>", lambda e: self.hide_history_dropdown()
                       if e.widget is self.root else None)

        if sys.platform == "win32":
            self.update_windows_title_bar()

        self.update_button_colors()
        _sstep("STARTUP COMPLETE")
        self.root.bind("<FocusIn>", lambda e: self.sync_config_on_focus())

    def _get_debug_logger(self):
        """
        Returns the shared debug logger when debug_mode is active, None otherwise.
        The logger is initialised lazily on first call and reused on subsequent ones.
        Writes to DEBUG_LOG_FILE (config.py) with rotation: 500 KB max, 1 backup.
        """
        if not self.debug_mode:
            return None
        import logging
        _log = logging.getLogger("kodi_debug")
        if not _log.handlers:
            # mode='w' overwrites the file at each new session (first activation).
            _h = logging.FileHandler(DEBUG_LOG_FILE, mode="w", encoding="utf-8")
            _h.setFormatter(logging.Formatter(
                "%(asctime)s.%(msecs)03d  %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            ))
            _log.addHandler(_h)
            _log.setLevel(logging.DEBUG)
        return _log

    def _load_single_instance_state(self):
        """Pre-loads the 'single instance' state from the config file."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    lines = [line.split('#')[0].strip() for line in f.readlines()]
                    if len(lines) >= 17 and lines[16] in ["0", "1"]:
                        return lines[16] == "1"
            except Exception:
                pass
        return config.ENABLE_SINGLE_INSTANCE

    def on_closing(self):
        """Handles the window close event: stops monitoring thread, saves session, destroys window."""
        # ── Shutdown timing (active only when debug_mode is True) ────────────
        # Each run is preceded by a separator line for easy navigation in the file.
        _log = self._get_debug_logger()
        if _log:
            _t0 = time.time()
            def _step(label):
                _log.debug("SHUTDOWN  %s  (+%d ms)", label, (time.time() - _t0) * 1000)
        else:
            def _step(label):
                pass   # no-op when debug mode is off

        _step("on_closing START")

        self.running = False
        _step("running = False")

        if hasattr(self, "monitor_thread") and \
           self.monitor_thread is not None and \
           self.monitor_thread.is_alive():
            _step("monitor_thread alive — join(timeout=1.2s) …")
            self.monitor_thread.join(timeout=1.2)
            _step(f"monitor_thread join done  still_alive={self.monitor_thread.is_alive()}")
        else:
            _step("monitor_thread not running — join skipped")

        if sys.platform == "win32" and hasattr(self, "old_wndproc"):
            from ctypes import windll
            hwnd = windll.user32.GetParent(self.root.winfo_id())
            windll.user32.SetWindowLongPtrW(hwnd, -4, self.old_wndproc)
            _step("wndproc restored")

        # Capture maximised state — platform-specific API
        if sys.platform == "win32":
            self.window_state = self.root.state()   # 'normal' or 'zoomed'
        else:
            self.window_state = "zoomed" if self.root.attributes("-zoomed") else "normal"
        self.window_geometry = self.root.geometry()
        _step("geometry captured")

        self.save_session()
        _step("session saved")

        _step("root.destroy() …")
        self.root.destroy()
        _step("root.destroy() returned")

    def _hist_highlight_idx(self, idx, y_offset=None):
        """
        Highlights item `idx` in the history dropdown and shows/hides the
        truncation tooltip.  Called by both mouse motion and keyboard navigation
        so that whichever input fired last naturally controls the visual state.

        `y_offset` - pixel offset within the listbox widget for tooltip
        positioning.  When None (keyboard path), the item's bbox is used.
        """
        # Restore previous hover highlight if it changed
        if self._history_hover_idx is not None and self._history_hover_idx != idx:
            try:
                self.history_listbox.itemconfigure(
                    self._history_hover_idx,
                    background=COLOR_BG_HEADER,
                    foreground=COLOR_TEXT_MAIN,
                )
            except tk.TclError:
                pass

        # Apply hover highlight to new item
        try:
            self.history_listbox.itemconfigure(
                idx, background=COLOR_ACCENT, foreground=COLOR_TEXT_ON_ACCENT
            )
            self._history_hover_idx = idx
        except tk.TclError:
            self._history_hover_idx = None
            self._hist_tooltip.withdraw()
            return

        # Show tooltip only when the displayed value is truncated
        if 0 <= idx < len(self._hist_tip_items):
            full = self._hist_tip_items[idx]
            if len(full) > self._HIST_MAX_CHARS:
                self._hist_tooltip_label.configure(text=full)
                # Keyboard path: derive y from the item's bounding box
                if y_offset is None:
                    bbox = self.history_listbox.bbox(idx)
                    y_offset = (bbox[1] + bbox[3] // 2) if bbox else 0
                x = (self.history_window.winfo_rootx()
                     + self.history_window.winfo_width() + 4)
                y = self.history_window.winfo_rooty() + y_offset - 10
                self._hist_tooltip.geometry(f"+{x}+{y}")
                self._hist_tooltip.deiconify()
                self._hist_tooltip.lift()
                return
        self._hist_tooltip.withdraw()

