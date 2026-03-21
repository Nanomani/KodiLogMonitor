"""
Configuration settings and UI theme constants for the Kodi Monitor application.
This module defines application metadata, file paths, and the visual color palette.
"""

import os

# --- CONFIGURATION ---
APP_VERSION = "v1.4.0"
CONFIG_FILE = ".kodi_monitor_config"
DEFAULT_GEOMETRY = "1680x900+90+18"
DEFAULT_GEOMETRY_4K = "3118x1688+203+189"
ICON_NAME = "logo.ico"
KEYWORD_DIR = "keyword_list"
GITHUB_URL = "https://github.com/Nanomani/KodiLogMonitor"
GITHUB_API_URL = "https://api.github.com/repos/Nanomani/KodiLogMonitor/releases/latest"
DEFAULT_PASTE_URL = "https://paste.kodi.tv/"
DEFAULT_SECURITY_FILE_MAX_SIZE = 10
DEFAULT_TIME_INACTIVITY = 300
SINGLE_INSTANCE_HOST = "127.0.0.1"
SINGLE_INSTANCE_PORT = 65432

# --- UI THEME ---
COLOR_BG_MAIN = "#1e1e1e"  # Main background color (log area)
COLOR_BG_HEADER = "#2d2d2d"  # Top toolbar background
COLOR_BG_SUBHEADER = "#333333"  # Secondary toolbar background (comboboxes/search)
COLOR_BG_FOOTER = "#2d2d2d"  # Bottom status bar background
COLOR_BTN_DEFAULT = "#3e3e42"  # Standard button background
COLOR_BTN_ACTIVE = "#505050"  # Button background when mouse hovers over it
COLOR_ACCENT = "#007acc"  # Blue accent color (active filters, primary highlights)
COLOR_DANGER = "#e81123"  # Red color for Pause and critical actions
COLOR_WARNING = "#FF9800"  # Orange color for Reset and warnings
COLOR_SEPARATOR = "#444444"  # Vertical line color between button groups
COLOR_TEXT_MAIN = "#d4d4d4"  # Primary text color (log text)
COLOR_TEXT_DIM = "#888888"  # Dimmed text color for icons/placeholders
COLOR_TEXT_BRIGHT = "#ffffff"  # Bright white text for buttons and headers
COLOR_TEXT_GREY = "#9e9e9e"  # Grey text for label footer app + version
COLOR_BTN_SECONDARY = "#454545"  # Slightly different grey for secondary small buttons

# --- COLORS FOR THE CUSTOM SCROLLBAR ---
SCROLL_THUMB_DEFAULT = "#5a5a5a"  # Lighter gray for the cursor
SCROLL_THUMB_HOVER = "#d4d4d4"  # Light gray when hovering

# --- COLORS FOR LOG ---
LOG_COLORS = {
    "debug": "#9e9e9e",  # Grey for debug messages
    "info": "#4CAF50",  # Green for info messages
    "warning": "#FF9800",  # Orange for warnings
    "error": "#F44336",  # Red for errors
    "summary": "#00E5FF",  # Cyan for the system summary block
    "highlight_bg": "#FFF59D",  # Yellow background for search highlights
    "highlight_fg": "#000000",  # Black text for search highlights
}

if not os.path.exists(KEYWORD_DIR):
    os.makedirs(KEYWORD_DIR)
