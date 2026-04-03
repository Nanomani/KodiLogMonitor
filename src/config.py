"""
Configuration settings and UI theme constants for the Kodi Monitor application.
This module defines application metadata, file paths, and the visual color palette.
"""

import os

# --- CONFIGURATION ---
APP_VERSION = "v1.4.2"
APP_NAME = "Kodi Log Monitor"
CONFIG_FILE = ".kodi_monitor_config"
SEARCH_HISTORY_FILE = ".kodi_search_history"
EXPORT_FILE = "kodi_LOG_export.txt"
DEFAULT_GEOMETRY_HD = "1000x630+16+14"
DEFAULT_GEOMETRY_FHD = "1680x900+90+18"
DEFAULT_GEOMETRY_4K = "3118x1688+203+189"
ICON_NAME = "logo.ico"
KEYWORD_DIR = "keyword_list"
GITHUB_URL = "https://github.com/Nanomani/KodiLogMonitor?tab=readme-ov-file#-kodi-log-monitor"
GITHUB_API_URL = "https://api.github.com/repos/Nanomani/KodiLogMonitor/releases/latest"
DEFAULT_PASTE_URL = "https://paste.kodi.tv/"
DEFAULT_SECURITY_FILE_MAX_SIZE_STARTUP = 10
DEFAULT_SECURITY_FILE_MAX_SIZE_BUTTON = 20
DEFAULT_TIME_INACTIVITY = 300
SINGLE_INSTANCE_HOST = "127.0.0.1"
SINGLE_INSTANCE_PORT = 65432
ENABLE_SINGLE_INSTANCE = False

# --- UI THEME ---
COLOR_BG_MAIN = "#1e1e1e"  # Main background color (log area)
COLOR_BG_HEADER = "#2d2d2d"  # Top toolbar background
COLOR_BG_SUBHEADER = "#333333"  # Secondary toolbar background (comboboxes/search)
COLOR_BG_FOOTER = "#2d2d2d"  # Bottom status bar background
COLOR_BG_TIPS = "#777777"  # Tips color background
COLOR_BTN_DEFAULT = "#3e3e42"  # Standard button background
COLOR_BTN_ACTIVE = "#505050"  # Button background when mouse hovers over it
COLOR_ACCENT = "#4a86ad"  # Blue accent color (active filters, primary highlights)
COLOR_DANGER = "#d32f2f"  # Red color for Pause and critical actions
COLOR_WARNING = "#FF9800"  # Orange color for Reset and warnings
COLOR_SEPARATOR = "#555555"  # Vertical line color between button groups
COLOR_TEXT_BRIGHT = "#ffffff"  # Bright white text for buttons and headers
COLOR_TEXT_MAIN = "#d4d4d4"  # Primary text color (log text, footer text)
COLOR_TEXT_DIM = "#888888"  # Dimmed text color for icons/placeholders
COLOR_TEXT_GREY = "#9e9e9e"  # Grey text for label footer app + version
COLOR_TEXT_TIPS = "#ffffff"  # Bright white text for Tips
COLOR_TEXT_WRAP = "#6aa3c7"  # Blue text for Wrap info
COLOR_BTN_SECONDARY = "#454545"  # Slightly different grey for secondary small buttons
COLOR_INDICATOR_OFF = "#555555"  # Border circle indicator activity
COLOR_INDICATOR_BORDER = "#c4c4c4"  # Grey indicator activity off

# --- COLORS FOR THE CUSTOM SCROLLBAR ---
SCROLL_THUMB_DEFAULT = "#5a5a5a"  # Lighter gray for the cursor
SCROLL_THUMB_HOVER = "#d4d4d4"  # Light gray when hovering

LOG_COLORS = {
    "info": "#4CAF50",  # Green for info messages + button filter
    "warning": "#e68a00",  # Orange for warnings messages + button filter
    "error": "#d32f2f",  # Red for errors messages + button filter
    "debug": "#9e9e9e",  # Grey for debug messages + button filter
    "summary": "#6aa3c7",  # Cyan for the system summary block
    "highlight_kwl_bg": "#FFF59D",  # Yellow background for keyword list
    "highlight_kwl_fg": "#000000",  # Black text for keyword list
    "highlight_kws_bg": "#6FA8DC",  # Blue background for search bar
    "highlight_kws_fg": "#000000",  # Black text for search bar
}

if not os.path.exists(KEYWORD_DIR):
    os.makedirs(KEYWORD_DIR)
