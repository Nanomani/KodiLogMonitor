# ui/app.py
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import os
import time
import sys
from collections import deque

import config
from config import *
from languages import LANGS
from utils import get_system_font, get_mono_font, get_emoji_font, get_windows_theme

from ui.monitor import MonitorMixin
from ui.log_display import LogDisplayMixin
from ui.session import SessionMixin
from ui.actions import ActionsMixin
from ui.ui_builder import UIBuilderMixin


class KodiLogMonitor(UIBuilderMixin, ActionsMixin, SessionMixin, LogDisplayMixin, MonitorMixin):
    """
    Main class — assembles all modules via multiple inheritance.
    """
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.inactivity_timer_var = tk.StringVar(value="")

        # --- 4K DYNAMIC DETECTION ---
        screen_width = self.root.winfo_screenwidth()

        # If the screen is wider than 2560 pixels
        if screen_width > 2560:
            self.window_geometry = DEFAULT_GEOMETRY_4K
            self.scale = 1
        elif screen_width > 1280:
            self.window_geometry = DEFAULT_GEOMETRY_FHD
            self.scale = 0.5
        else:
            self.window_geometry = DEFAULT_GEOMETRY_HD
            self.scale = 0.25

        # --- SAFE DISPLAY MONITORING ---
        if sys.platform == "win32":
            from ctypes import windll
            # Get screen width directly from Windows API (SM_CXSCREEN = 0)
            self.last_screen_width = windll.user32.GetSystemMetrics(0)
            # Start a safe check every 3 seconds
            self.root.after(3000, self.periodic_display_check)

        self.enable_single_instance_var = self._load_single_instance_state()

        self.root.configure(bg=COLOR_BG_MAIN)
        self.last_activity_time = time.time()
        self.inactivity_limit = DEFAULT_TIME_INACTIVITY
        self.last_line_count = 0
        self.last_pause_state = False
        self.last_limit_state = False
        self.last_wrap_state = False

        self.main_font_family = get_system_font()
        self.mono_font_family = get_mono_font()
        self.emoji_font_family = get_emoji_font()

        self.set_window_icon()
        self.log_file_path = ""
        self.paste_url = DEFAULT_PASTE_URL
        self.max_size_mb = DEFAULT_SECURITY_FILE_MAX_SIZE_STARTUP
        self.updates_enabled = True
        self.skip_version = ""
        self.running = False
        self.monitor_thread = None
        self.seen_lines = deque(maxlen=200)
        self.pending_jump_timestamp = None
        self.log_lock = threading.Lock()

        self.load_full_file = tk.BooleanVar(value=False)
        self.wrap_mode = tk.BooleanVar(value=False)
        self.is_paused = tk.BooleanVar(value=False)
        self.current_lang = tk.StringVar(value=self.detect_os_language())
        self.theme_mode = tk.StringVar(value="Dark")  # Options: Auto, Light, Dark

        self.filter_vars = {
            "all": tk.BooleanVar(value=True),
            "debug": tk.BooleanVar(value=False),
            "info": tk.BooleanVar(value=False),
            "warning": tk.BooleanVar(value=False),
            "error": tk.BooleanVar(value=False)
        }

        self.search_query = tk.StringVar()
        self.selected_list = tk.StringVar()
        self.font_size = 10
        self.show_google_search = tk.BooleanVar(value=True)

        self.filter_colors = {
            "all": COLOR_ACCENT,
            "debug": LOG_COLORS["debug"],
            "info": LOG_COLORS["info"],
            "warning": LOG_COLORS["warning"],
            "error": LOG_COLORS["error"]
        }

        # --- Cursor visibility management ---
        self.cursor_timer = None
        self.cursor_visible = True

        self.setup_ui()
        self.load_session()

        # --- NEW LOGIC: RESET GEOMETRY IF EMPTY ---
        if not self.window_geometry or self.window_geometry.strip() == "":
            screen_width = self.root.winfo_screenwidth()
            if screen_width > 2560:
                self.window_geometry = DEFAULT_GEOMETRY_4K
            elif screen_width > 1280:
                self.window_geometry = DEFAULT_GEOMETRY_FHD
            else:
                self.window_geometry = DEFAULT_GEOMETRY_HD

        self.check_for_updates()

        if self.log_file_path:
            # We wait 200ms for the window to be ready before loading.
            self.root.after(200, lambda: self.start_monitoring(self.log_file_path, is_manual=False))

        self.root.geometry(self.window_geometry)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- KEYBOARD SHORTCUTS ---

        # Close the dropdown search list when clicking anywhere else in the application or Windows OS
        self.root.bind("<Button-1>", self._close_dropdown_on_outside_click)
        self.root.bind("<Configure>", self._on_window_configure)

        self.root.bind("<Control-c>", self.copy_to_clipboard)
        self.root.bind("<Control-C>", self.copy_to_clipboard)
        self.txt_area.bind("<Control-c>", self.copy_to_clipboard)
        self.txt_area.bind("<Control-C>", self.copy_to_clipboard)

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

        self.root.bind("<Control-g>", self.select_clear_console_from_keyboard)
        self.root.bind("<Control-G>", self.select_clear_console_from_keyboard)
        self.txt_area.bind("<Control-g>", self.select_clear_console_from_keyboard)
        self.txt_area.bind("<Control-G>", self.select_clear_console_from_keyboard)

        self.root.bind("<space>", self.toggle_pause_from_keyboard)
        self.txt_area.bind("<space>", self.toggle_pause_from_keyboard)

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

        self.root.bind("<F1>", lambda e: self.show_help())
        self.txt_area.bind("<F1>", lambda e: self.show_help())

        self.root.bind("<Up>", lambda e: self.txt_area.yview_scroll(-1, "units"))
        self.root.bind("<Down>", lambda e: self.txt_area.yview_scroll(1, "units"))
        self.txt_area.bind("<Up>", lambda e: self.txt_area.yview_scroll(-1, "units"))
        self.txt_area.bind("<Down>", lambda e: self.txt_area.yview_scroll(1, "units"))

        # Bind Ctrl + Mouse Wheel to handle font resizing
        # Windows and macOS
        self.txt_area.bind("<Control-MouseWheel>", self.on_mouse_wheel_font_resize)
        # Linux support (uses specific button numbers for scrolling)
        self.txt_area.bind("<Control-Button-4>", self.on_mouse_wheel_font_resize)
        self.txt_area.bind("<Control-Button-5>", self.on_mouse_wheel_font_resize)

        # Bind Mouse Wheel safe vertical scroll
        # Windows & macOS
        self.txt_area.bind("<MouseWheel>", self.safe_vertical_scroll)

        # Linux
        self.txt_area.bind("<Button-4>", self.safe_vertical_scroll)
        self.txt_area.bind("<Button-5>", self.safe_vertical_scroll)

        # Bind the Escape key specifically to this entry field
        self.search_entry.bind("<Escape>", self.reset_search_and_focus_log)

        # Bind on history event
        self.setup_history_events()

        # --- FILTER CHANGE ---
        for key, var in self.filter_vars.items():
            if key != "all":  # We don't automate "all"; we manage it manually in on_filter_toggle.
                var.trace_add("write", self.trigger_refresh)

        self.search_query.trace_add("write", self.clean_search_input)
        self.search_query.trace_add("write", self.on_search_change)

        # Trace the search query to sanitize it BEFORE executing the search
        self.selected_list.trace_add("write", self.on_list_change)
        self.load_full_file.trace_add("write", lambda *args: self.immediate_ui_refresh())

        # --- History Popup ---
        self.history_window = tk.Toplevel(self.root)
        self.history_window.withdraw()
        self.history_window.overrideredirect(True)

        self.history_listbox = tk.Listbox(self.history_window)
        self.history_listbox.pack(fill=tk.BOTH, expand=True)

        # Bindings (The names must exist as methods in your class)
        # self.history_listbox.bind("<Return>", self.on_history_select_keyboard)
        self.history_listbox.bind("<ButtonRelease-1>", self.on_history_select)

        self.root.after(5000, self.scheduled_stats_update)

        if sys.platform == "win32":
            self.update_windows_title_bar()
            self.listen_for_theme_changes()
            self.root.after(100, self.on_theme_change)

        self.update_button_colors()
        self.root.bind("<FocusIn>", lambda e: self.sync_config_on_focus())

    def _load_single_instance_state(self):
        """Pré-charge l'état 'single instance' du fichier config."""
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
        self.running = False
        if sys.platform == "win32" and hasattr(self, "old_wndproc"):
            from ctypes import windll
            hwnd = windll.user32.GetParent(self.root.winfo_id())
            windll.user32.SetWindowLongPtrW(hwnd, -4, self.old_wndproc)
        self.window_geometry = self.root.geometry()
        self.save_session()
        self.root.destroy()
