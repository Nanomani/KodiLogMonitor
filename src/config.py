"""
Configuration settings and UI theme constants for the Kodi Monitor application.
This module defines application metadata, file paths, and the visual color palette.

Theme selection is applied at import time: the saved app_theme preference is read
from the config file (line 18). All COLOR_* constants and LOG_COLORS are set from
the matching palette. Changing themes requires an app restart (handled by actions.py).
"""

import os

# --- CONFIGURATION ---
APP_VERSION = "v1.7.2"
APP_NAME = "Kodi Log Monitor"
CONFIG_FILE = ".kodi_monitor_config"
SEARCH_HISTORY_FILE = ".kodi_search_history"
EXPORT_FILE = "kodi_LOG_export.txt"
DEFAULT_GEOMETRY_HD = "1190x629+63+39 "
DEFAULT_GEOMETRY_FHD = "1350x788+70+73 "
DEFAULT_GEOMETRY_4K = "1350x788+128+122"
ICON_NAME = "logo.ico"
KEYWORD_DIR = "keyword_list"
GITHUB_URL = "https://github.com/Nanomani/KodiLogMonitor?tab=readme-ov-file#-kodi-log-monitor"
GITHUB_API_URL = "https://api.github.com/repos/Nanomani/KodiLogMonitor/releases/latest"
DEFAULT_PASTE_URL = "https://paste.kodi.tv/"
DEFAULT_SECURITY_FILE_MAX_SIZE_STARTUP = 10
DEFAULT_SECURITY_FILE_MAX_SIZE_BUTTON = 10
DEFAULT_TIME_INACTIVITY = 300
SEARCH_HISTORY_MAX_SIZE = 50
EXCLUDE_LIST_FILE = ".kodi_show_exclude"
# Output file for shutdown debug logging (activated via Ctrl+Shift+D in the UI).
DEBUG_LOG_FILE = "kodi_monitor_debug.log"
# Maximum number of exclusion patterns. Keeps substring-search overhead negligible
# (each check is O(pattern_count * line_len); 20 patterns on 1 000 lines ≈ 1 ms).
EXCLUDE_LIST_MAX_SIZE = 20
SINGLE_INSTANCE_HOST = "127.0.0.1"
SINGLE_INSTANCE_PORT = 65432
ENABLE_SINGLE_INSTANCE = False

# Every log line is padded to at least this many characters before display.
# This keeps the horizontal scroll region stable: the scrollbar thumb never
# shrinks and the user's horizontal position is preserved even when only
# short lines are visible. Trailing spaces have no impact on performance.
LOG_MIN_LINE_WIDTH = 500

# Maximum number of characters displayed per log line.
# Lines exceeding this limit are truncated in the UI and a suffix indicating
# the number of hidden characters is appended. The source log file is never
# modified. Increase this value if you need more context, but be aware that
# very long lines (> ~10 000 chars) significantly slow down word-wrap rendering.
LOG_MAX_LINE_DISPLAY = 5000

# ==============================================================
# THEME PALETTES
# Each palette maps every COLOR_* key + LOG_COLORS to theme values.
# ==============================================================

_DARK_PALETTE = {
    # --- Backgrounds ---
    "COLOR_BG_MAIN":          "#1e1e1e",   # Main background (log area)
    "COLOR_BG_HEADER":        "#2d2d2d",   # Top toolbar background
    "COLOR_BG_SUBHEADER":     "#333333",   # Secondary toolbar background
    "COLOR_BG_FOOTER":        "#2d2d2d",   # Bottom status bar background
    "COLOR_BG_TIPS":          "#777777",   # Tooltip background
    "COLOR_BG_DIALOG":        "#2d2d2d",   # Dialog / popup window background

    # --- Buttons ---
    "COLOR_BTN_DEFAULT":      "#3e3e42",   # Standard button background
    "COLOR_BTN_ACTIVE":       "#505050",   # Button background on hover
    "COLOR_BTN_SECONDARY":    "#454545",   # Slightly different grey for small buttons

    # --- Semantic colors ---
    "COLOR_ACCENT":           "#4a86ad",   # Blue accent (active filters, highlights)
    "COLOR_LOG_SELECTION":    "#1565c0",   # Log text selection bg (distinct from accent)
    "COLOR_LOG_SELECTION_FG": "#e3f2fd",   # Log text selection foreground
    "COLOR_DANGER":           "#E57373",   # Red (Pause, critical actions)
    "COLOR_WARNING":          "#EEB74D",   # Orange (Reset, warnings)
    "COLOR_SEPARATOR":        "#555555",   # Vertical line between button groups

    # --- Text ---
    "COLOR_TEXT_BRIGHT":      "#ffffff",   # Bright white text for buttons/headers
    "COLOR_TEXT_MAIN":        "#d4d4d4",   # Primary text (log, footer)
    "COLOR_TEXT_DIM":         "#888888",   # Dimmed text (icons, placeholders)
    "COLOR_TEXT_GREY":        "#9e9e9e",   # Grey label (app name + version)
    "COLOR_TEXT_TIPS":        "#ffffff",   # White text on tooltips
    "COLOR_TEXT_WRAP":        "#6aa3c7",   # Blue text for Wrap indicator
    "COLOR_TEXT_LIGHT":       "#6f7680",   # Light grey for placeholder

    # --- Status indicator ---
    "COLOR_INDICATOR_OFF":    "#555555",   # Activity circle off
    "COLOR_INDICATOR_BORDER": "#c4c4c4",   # Activity circle border

    # --- Scrollbar ---
    "SCROLL_THUMB_DEFAULT":   "#5a5a5a",   # Scrollbar thumb
    "SCROLL_THUMB_HOVER":     "#d4d4d4",   # Scrollbar thumb hover

    # --- Fixed overlay text (same in both themes) ---
    "COLOR_TEXT_ON_ACCENT":        "#ffffff",   # White text on accent/colored bg (active buttons, hover, selection)

    # --- Timeline viewport overlay ---
    "COLOR_TIMELINE_VIEWPORT":     "#ffffff",   # Outline of the visible-range rectangle on the timeline strip

    # --- Log text tag colors ---
    "LOG_COLORS": {
        "info":              "#81C784",    # Green
        "warning":           "#EEB74D",    # Orange
        "error":             "#E57373",    # Red
        "debug":             "#B0BEC5",    # Grey
        "summary":           "#8fa8b3",    # Cyan/Blue
        "highlight_kwl_bg":  "#0d3c61",    # Blue bg for keyword list match
        "highlight_kwl_fg":  "#90caf9",    # Blue text on blue
        "highlight_kws_bg":  "#5c4b00",    # Brown bg for search bar match
        "highlight_kws_fg":  "#fff176",    # Yellow text on brown
    },
}

_LIGHT_PALETTE = {
    # --- Backgrounds ---
    "COLOR_BG_MAIN":          "#f5f5f5",   # Main background (log area)
    "COLOR_BG_HEADER":        "#e3e3e3",   # Top toolbar background
    "COLOR_BG_SUBHEADER":     "#ebebeb",   # Secondary toolbar background
    "COLOR_BG_FOOTER":        "#e3e3e3",   # Bottom status bar background
    "COLOR_BG_TIPS":          "#424242",   # Tooltip background (keep dark for contrast)
    "COLOR_BG_DIALOG":        "#f0f0f0",   # Dialog / popup window background (natural Windows grey)

    # --- Buttons ---
    "COLOR_BTN_DEFAULT":      "#d0d0d4",   # Standard button background
    "COLOR_BTN_ACTIVE":       "#b8b8bc",   # Button background on hover
    "COLOR_BTN_SECONDARY":    "#c8c8cc",   # Slightly different grey for small buttons

    # --- Semantic colors ---
    "COLOR_ACCENT":           "#1976d2",   # Darker blue accent (readable on light bg)
    "COLOR_LOG_SELECTION":    "#9fa8da",   # Log text selection bg (distinct from accent)
    "COLOR_LOG_SELECTION_FG": "#0d1b2a",   # Log text selection foreground
    "COLOR_DANGER":           "#c62828",   # Darker red
    "COLOR_WARNING":          "#e65100",   # Darker orange
    "COLOR_SEPARATOR":        "#c0c0c0",   # Vertical line between button groups

    # --- Text ---
    "COLOR_TEXT_BRIGHT":      "#1a1a1a",   # Near-black text for buttons/headers
    "COLOR_TEXT_MAIN":        "#212121",   # Primary text (near black)
    "COLOR_TEXT_DIM":         "#757575",   # Dimmed text
    "COLOR_TEXT_GREY":        "#616161",   # Grey label (app name + version)
    "COLOR_TEXT_TIPS":        "#ffffff",   # White text on dark tooltips
    "COLOR_TEXT_WRAP":        "#1565c0",   # Darker blue for Wrap indicator
    "COLOR_TEXT_LIGHT":       "#d0d0d4",   # Light grey for placeholder

    # --- Status indicator ---
    "COLOR_INDICATOR_OFF":    "#9e9e9e",   # Activity circle off
    "COLOR_INDICATOR_BORDER": "#424242",   # Activity circle border

    # --- Scrollbar ---
    "SCROLL_THUMB_DEFAULT":   "#9e9e9e",   # Scrollbar thumb
    "SCROLL_THUMB_HOVER":     "#424242",   # Scrollbar thumb hover

    # --- Fixed overlay text (same in both themes) ---
    "COLOR_TEXT_ON_ACCENT":        "#ffffff",   # White text on accent/colored bg (active buttons, hover, selection)

    # --- Timeline viewport overlay ---
    "COLOR_TIMELINE_VIEWPORT":     "#0d47a1",   # Outline of the visible-range rectangle on the timeline strip

    # --- Log text tag colors (darker variants for readability on light bg) ---
    "LOG_COLORS": {
        "info":              "#2e7d32",    # Dark green
        "warning":           "#e69500",    # Deep orange
        "error":             "#c62828",    # Dark red
        "debug":             "#757575",    # Medium grey
        "summary":           "#1565c0",    # Dark blue
        "highlight_kwl_bg":  "#bbdefb",    # Blue light bg for keyword list match
        "highlight_kwl_fg":  "#0d47a1",    # Blue text on blue light
        "highlight_kws_bg":  "#fff59d",    # Brown bg for search bar match
        "highlight_kws_fg":  "#7f6000",    # Yellow text on brown
    },
}

# ==============================================================
# THEME SELECTION  (read saved preference at import time)
# ==============================================================

def _read_saved_app_theme():
    """
    Reads the theme choice from the config file (line 18, 0-indexed = index 17).
    Returns 'dark' or 'light'. Falls back to 'dark' on any error or unknown value.
    """
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                lines = [ln.split('#')[0].strip() for ln in f.read().splitlines()]
            if len(lines) >= 18:
                val = lines[17].strip().lower()
                if val in ("dark", "light"):
                    return val
    except Exception:
        pass
    return "dark"


# Resolved palette: "dark" or "light"
APP_THEME = _read_saved_app_theme()

_palette  = _LIGHT_PALETTE if APP_THEME == "light" else _DARK_PALETTE

# --- Expose all palette values as module-level constants (backward-compatible) ---
COLOR_BG_MAIN          = _palette["COLOR_BG_MAIN"]
COLOR_BG_HEADER        = _palette["COLOR_BG_HEADER"]
COLOR_BG_SUBHEADER     = _palette["COLOR_BG_SUBHEADER"]
COLOR_BG_FOOTER        = _palette["COLOR_BG_FOOTER"]
COLOR_BG_TIPS          = _palette["COLOR_BG_TIPS"]
COLOR_BG_DIALOG        = _palette["COLOR_BG_DIALOG"]
COLOR_BTN_DEFAULT      = _palette["COLOR_BTN_DEFAULT"]
COLOR_BTN_ACTIVE       = _palette["COLOR_BTN_ACTIVE"]
COLOR_BTN_SECONDARY    = _palette["COLOR_BTN_SECONDARY"]
COLOR_ACCENT           = _palette["COLOR_ACCENT"]
COLOR_LOG_SELECTION    = _palette["COLOR_LOG_SELECTION"]
COLOR_LOG_SELECTION_FG = _palette["COLOR_LOG_SELECTION_FG"]
COLOR_DANGER           = _palette["COLOR_DANGER"]
COLOR_WARNING          = _palette["COLOR_WARNING"]
COLOR_SEPARATOR        = _palette["COLOR_SEPARATOR"]
COLOR_TEXT_BRIGHT      = _palette["COLOR_TEXT_BRIGHT"]
COLOR_TEXT_MAIN        = _palette["COLOR_TEXT_MAIN"]
COLOR_TEXT_DIM         = _palette["COLOR_TEXT_DIM"]
COLOR_TEXT_GREY        = _palette["COLOR_TEXT_GREY"]
COLOR_TEXT_TIPS        = _palette["COLOR_TEXT_TIPS"]
COLOR_TEXT_WRAP        = _palette["COLOR_TEXT_WRAP"]
COLOR_TEXT_LIGHT       = _palette["COLOR_TEXT_LIGHT"]
COLOR_INDICATOR_OFF    = _palette["COLOR_INDICATOR_OFF"]
COLOR_INDICATOR_BORDER = _palette["COLOR_INDICATOR_BORDER"]
SCROLL_THUMB_DEFAULT   = _palette["SCROLL_THUMB_DEFAULT"]
SCROLL_THUMB_HOVER     = _palette["SCROLL_THUMB_HOVER"]
COLOR_TEXT_ON_ACCENT       = _palette["COLOR_TEXT_ON_ACCENT"]
COLOR_TIMELINE_VIEWPORT    = _palette["COLOR_TIMELINE_VIEWPORT"]
LOG_COLORS                 = _palette["LOG_COLORS"]

if not os.path.exists(KEYWORD_DIR):
    os.makedirs(KEYWORD_DIR)
