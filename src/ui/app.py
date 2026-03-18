# ui/app.py
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import os
import time
import sys
from collections import deque

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
        self.root.title("Kodi Log Monitor")
        self.window_geometry = DEFAULT_GEOMETRY
        self.root.configure(bg=COLOR_BG_MAIN)
        self.last_activity_time = time.time()
        self.inactivity_limit = 300
        self.last_line_count = 0
        self.last_pause_state = False
        self.last_limit_state = False

        self.main_font_family = get_system_font()
        self.mono_font_family = get_mono_font()
        self.emoji_font_family = get_emoji_font()

        self.set_window_icon()
        self.log_file_path = ""
        self.paste_url = "https://paste.kodi.tv/"
        self.running = False
        self.monitor_thread = None
        self.seen_lines = __import__('collections').deque(maxlen=200)
        self.pending_jump_timestamp = None
        self.log_lock = threading.Lock()

        self.load_full_file = tk.BooleanVar(value=False)
        self.wrap_mode = tk.BooleanVar(value=False)
        self.is_paused = tk.BooleanVar(value=False)
        self.current_lang = tk.StringVar(value=self.detect_os_language())
        self.theme_mode = tk.StringVar(value="Dark")

        self.filter_vars = {
            "all": tk.BooleanVar(value=True),
            "debug": tk.BooleanVar(value=False),
            "info": tk.BooleanVar(value=False),
            "warning": tk.BooleanVar(value=False),
            "error": tk.BooleanVar(value=False),
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
            "error": LOG_COLORS["error"],
        }

        self.cursor_timer = None
        self.cursor_visible = True

        self.setup_ui()
        self.load_session()

        if self.log_file_path:
            self.root.after(200, lambda: self.start_monitoring(self.log_file_path, is_manual=False))

        self.root.geometry(self.window_geometry)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- KEYBOARD SHORTCUTS ---

        self.root.bind("<Control-o>", self.open_file)
        self.root.bind("<Control-O>", self.open_file)
        self.txt_area.bind("<Control-o>", self.open_file)
        self.txt_area.bind("<Control-O>", self.open_file)

        self.root.bind("<Control-s>", self.export_log)
        self.root.bind("<Control-S>", self.export_log)
        self.txt_area.bind("<Control-s>", self.export_log)
        self.txt_area.bind("<Control-S>", self.export_log)

        self.root.bind("<Control-f>", self.focus_search_entry)
        self.root.bind("<Control-F>", self.focus_search_entry)
        self.txt_area.bind("<Control-f>", self.focus_search_entry)
        self.txt_area.bind("<Control-F>", self.focus_search_entry)

        self.root.bind("<s>", self.select_show_summary_from_keyboard)
        self.root.bind("<S>", self.select_show_summary_from_keyboard)
        self.txt_area.bind("<s>", self.select_show_summary_from_keyboard)
        self.txt_area.bind("<S>", self.select_show_summary_from_keyboard)

        self.root.bind("<Control-g>", self.select_clear_console_from_keyboard)
        self.root.bind("<Control-G>", self.select_clear_console_from_keyboard)
        self.txt_area.bind("<Control-g>", self.select_clear_console_from_keyboard)
        self.txt_area.bind("<Control-G>", self.select_clear_console_from_keyboard)

        self.root.bind("<space>", self.toggle_pause_from_keyboard)
        self.txt_area.bind("<space>", self.toggle_pause_from_keyboard)

        self.root.bind("<Control-l>", self.toggle_wrap_from_keyboard)
        self.root.bind("<Control-L>", self.toggle_wrap_from_keyboard)
        self.txt_area.bind("<Control-l>", self.toggle_wrap_from_keyboard)
        self.txt_area.bind("<Control-L>", self.toggle_wrap_from_keyboard)

        self.root.bind("<Control-t>", self.toggle_limit_from_keyboard)
        self.root.bind("<Control-T>", self.toggle_limit_from_keyboard)
        self.txt_area.bind("<Control-t>", self.toggle_limit_from_keyboard)
        self.txt_area.bind("<Control-T>", self.toggle_limit_from_keyboard)

        self.root.bind("<Control-r>", self.select_reset_all_filters_from_keyboard)
        self.root.bind("<Control-R>", self.select_reset_all_filters_from_keyboard)
        self.txt_area.bind("<Control-r>", self.select_reset_all_filters_from_keyboard)
        self.txt_area.bind("<Control-R>", self.select_reset_all_filters_from_keyboard)

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

        # --- FILTER CHANGE ---
        for key, var in self.filter_vars.items():
            if key != "all":
                var.trace_add("write", self.trigger_refresh)
        self.search_query.trace_add("write", self.on_search_change)

        self.root.after(5000, self.scheduled_stats_update)

        if sys.platform == "win32":
            self.update_windows_title_bar()
            self.listen_for_theme_changes()
            self.root.after(100, self.on_theme_change)

        self.update_button_colors()

    def on_closing(self):
        self.running = False
        if sys.platform == "win32" and hasattr(self, "old_wndproc"):
            from ctypes import windll
            hwnd = windll.user32.GetParent(self.root.winfo_id())
            windll.user32.SetWindowLongPtrW(hwnd, -4, self.old_wndproc)
        self.window_geometry = self.root.geometry()
        self.save_session()
        self.root.destroy()
