"""
Main entry point for the Kodi Log Monitor application.
Handles high-DPI scaling, Windows-specific dark mode styling, and application initialization.
"""

__author__ = "Nanomani"

import sys
import tkinter as tk

from utils import get_windows_theme
from utils import check_single_instance
from ui.app import KodiLogMonitor
from config import ENABLE_SINGLE_INSTANCE

if __name__ == "__main__":
    check_single_instance()

    # 1. Handle DPI Awareness before creating the UI
    if sys.platform == "win32":
        try:
            from ctypes import windll
            # Use Process_Per_Monitor_DPI_Aware_V2 (value 2) for better Win 11 stability
            # This prevents scaling-related crashes when moving windows or changing display settings
            windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                # Fallback to older DPI awareness if V2 is not supported
                windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                pass

    root = tk.Tk()

    # 2. Apply Windows 11 Theme and DWM Attributes
    if sys.platform == "win32":
        try:
            from ctypes import windll, byref, sizeof, c_int

            # Force a window update to ensure the HWND is valid and registered by the OS
            root.update()

            # Retrieve the Window Handle (HWND)
            hwnd = windll.user32.GetParent(root.winfo_id())

            # Detect Windows dark/light mode preference
            is_dark = get_windows_theme()

            try:
                # Attribute 20: Immersive Dark Mode
                # This ensures title bar buttons (Min/Max/Close) render correctly
                windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, 20, byref(c_int(is_dark)), sizeof(c_int(is_dark))
                )

                # Attribute 34: Custom Caption Color
                # Changing display settings can make this call fail momentarily;
                # wrapping it in a try block prevents the whole app from crashing.
                if is_dark:
                    caption_color = c_int(0x002d2d2d) # Dark Grey BGR
                else:
                    caption_color = c_int(0x00FFFFFF) # White BGR

                windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, 34, byref(caption_color), sizeof(caption_color)
                )
            except Exception as dwm_err:
                # Log error to console without crashing the application
                print(f"DWM Attribute Error: {dwm_err}")

        except Exception as win_err:
            print(f"Windows Initialization Error: {win_err}")

    # 3. Start the application
    app = KodiLogMonitor(root)
    root.mainloop()
