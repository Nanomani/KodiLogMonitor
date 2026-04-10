"""
Utility functions for cross-platform font selection and single-instance management.
Provides helper methods for system, monospaced, and emoji font families.
"""

import os
import sys
import socket
import locale
import config
import tkinter as tk
from tkinter import messagebox

from config import APP_NAME, SINGLE_INSTANCE_HOST, SINGLE_INSTANCE_PORT, CONFIG_FILE, ENABLE_SINGLE_INSTANCE
from languages import LANGS

# Module-level sentinel for the single-instance lock socket.
# Initialized here so any code path can safely reference it.
_lock_socket = None

def get_system_font():
    """
    Returns a suitable system font tuple based on the current operating system.

    Returns:
        tuple: A tuple containing font family names.
    """
    if sys.platform == "darwin":
        return ("Helvetica", "Arial", "sans-serif")
    if sys.platform == "win32":
        return ("Segoe UI", "Tahoma", "Arial", "sans-serif")
    return ("DejaVu Sans", "Verdana", "sans-serif")


def get_mono_font():
    """
    Returns the preferred monospaced font family name for the current platform.

    Returns:
        str: The font family name.
    """
    if sys.platform == "darwin":
        return "Menlo"
    if sys.platform == "win32":
        return "Consolas"
    return "DejaVu Sans Mono"


def get_emoji_font():
    """
    Returns an emoji-compatible font family name, primarily for Windows support.

    Returns:
        str: The font family name.
    """
    if sys.platform == "win32":
        return "Segoe UI Emoji"
    return get_system_font()


def check_single_instance():
    """
    Checks if another instance is running using host/port from config file.
    """
    global ENABLE_SINGLE_INSTANCE, _lock_socket

    host = SINGLE_INSTANCE_HOST
    port = SINGLE_INSTANCE_PORT
    user_lang = "EN" # Default fallback

    # 1. Parse the config file
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()

                def get_val(line_idx):
                    if line_idx < len(lines):
                        return lines[line_idx].split('#')[0].strip()
                    return None

                # --- NEW: Get Language from config line 2 (Index 1) ---
                cfg_lang = get_val(1)
                if cfg_lang: user_lang = cfg_lang

                # Host, Port and Enable (Existing logic)
                cfg_host = get_val(14)
                if cfg_host: host = cfg_host
                cfg_port = get_val(15)

                if cfg_port:
                    try: port = int(cfg_port)
                    except ValueError: pass
                cfg_enable = get_val(16)

                if cfg_enable is not None:
                    is_enabled = (cfg_enable == "1")
                    ENABLE_SINGLE_INSTANCE = is_enabled
                    config.ENABLE_SINGLE_INSTANCE = is_enabled

        except Exception as e:
            print(f"Error reading config: {e}")

    if not ENABLE_SINGLE_INSTANCE:
        # Release any previously held lock so other instances can start freely
        if _lock_socket is not None:
            try:
                _lock_socket.close()
            except Exception:
                pass
            _lock_socket = None
        return

    # Close any pre-existing socket from a previous call to avoid leaking file descriptors
    if _lock_socket is not None:
        try:
            _lock_socket.close()
        except Exception:
            pass
    _lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # DO NOT use SO_REUSEADDR here: on Windows it allows multiple processes to
    # bind the same port simultaneously, which defeats the single-instance check.
    # A bound-but-never-connected TCP socket never enters TIME_WAIT, so REUSEADDR
    # is not needed to reclaim the port after the previous instance closes.
    try:
        _lock_socket.bind((host, port))
    except socket.error:
        # --- Language Detection logic ---
        def get_startup_lang(fallback_lang):
            # 1. If we found a lang in config, use it first
            if fallback_lang in LANGS:
                return fallback_lang

            # 2. Otherwise, check Windows system language
            try:
                import ctypes
                import locale
                # Specific Windows API call for UI Language
                lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
                lang_name = locale.windows_locale.get(lang_id)
                if lang_name and lang_name.lower().startswith('fr'):
                    return "FR"
            except Exception:
                pass
            return "EN"

        sys_lang = get_startup_lang(user_lang)
        l_ui = LANGS.get(sys_lang, LANGS["EN"])

        # Create hidden root for message
        temp_root = tk.Tk()
        temp_root.withdraw()

        # Get the localized message from languages.py
        # Ensure "already_running" is defined in your LANGS["FR"] in languages.py!
        msg = l_ui.get("already_running", "Une instance de ce programme est déjà en cours d'exécution.")

        messagebox.showwarning(APP_NAME, msg)
        temp_root.destroy()
        sys.exit(0)


def parse_version(version_str):
    """Converts the string 'v1.4.3' into a tuple of integers (1, 4, 3)."""
    try:
        # Remove the initial 'v' and cut along the dotted lines
        return tuple(int(x) for x in version_str.lstrip('v').split('.'))
    except Exception:
        return (0, 0, 0)
