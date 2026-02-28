"""
Utility functions for cross-platform font selection and Windows-specific theme detection.
Provides helper methods for system, monospaced, and emoji font families.
"""

import sys

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
