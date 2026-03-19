"""
Utility functions for cross-platform font selection and Windows-specific theme detection.
Provides helper methods for system, monospaced, and emoji font families.
"""

import os
import sys
import socket
import locale
import tkinter as tk
from tkinter import messagebox

from config import SINGLE_INSTANCE_HOST, SINGLE_INSTANCE_PORT, CONFIG_FILE
from languages import LANGS

if sys.platform == "win32":
    import winreg
else:
    winreg = None

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


def get_windows_theme():
    """
    Check the Windows Registry to see if the user prefers Dark Mode.
    Returns: 1 for Dark Mode, 0 for Light Mode.
    """
    try:
        registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        key = winreg.OpenKey(
            registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        )
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return 0 if value == 1 else 1  # 1 = Dark, 0 = Light
    except (OSError, AttributeError, FileNotFoundError):
        return 1  # Default to Dark Mode if check fails


def check_single_instance():
    """
    Checks if another instance is running using host/port from config file.
    This runs BEFORE the main app initialization.
    """
    global _lock_socket

    # Default values
    host = SINGLE_INSTANCE_HOST
    port = SINGLE_INSTANCE_PORT

    # 1. Manually parse the config file to find host/port
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    if "=" in line:
                        key, value = line.strip().split("=", 1)
                        if key == "single_instance_host":
                            host = value
                        elif key == "single_instance_port":
                            try:
                                port = int(value)
                            except ValueError:
                                pass
        except Exception:
            pass # Fallback to defaults on read error

    # 2. Try to bind the socket
    _lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        _lock_socket.bind((host, port))
    except socket.error:
        # Detect system language for the error message
        try:
            sys_lang_tuple = locale.getlocale()
            sys_lang = sys_lang_tuple[0][:2].upper() if sys_lang_tuple[0] else "EN"
        except Exception:
            sys_lang = "EN"

        l_ui = LANGS.get(sys_lang, LANGS["EN"])

        temp_root = tk.Tk()
        temp_root.withdraw()
        messagebox.showwarning(
            "Kodi Log Monitor",
            l_ui.get("already_running", "An instance of this program is already running.")
        )
        temp_root.destroy()
        sys.exit(0)
