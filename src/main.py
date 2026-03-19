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

if __name__ == "__main__":
    check_single_instance()

    if sys.platform == "win32":
        try:
            # We import it once for the entire block
            from ctypes import windll, byref, sizeof, c_int

            # 1. Sharpness Management (DPI)
            windll.shcore.SetProcessDpiAwareness(1)

            root = tk.Tk()
            root.update()

            # 2. Retrieving the window handle (HWND)
            hwnd = windll.user32.GetParent(root.winfo_id())

            # 3. Detecting the Windows theme
            IS_DARK = get_windows_theme()  # Returns 1 (Dark) or 0 (Light)

            # 4. Enable immersive dark mode (Attribute 20)
            windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 20, byref(c_int(IS_DARK)), sizeof(c_int(IS_DARK))
            )

            # 5. Applying the title bar color (Attribute 34)
            if IS_DARK:
                caption_color = c_int(0x002D2D2D)  # Gris foncé BGR
            else:
                caption_color = c_int(0x00FFFFFF)  # Blanc BGR

            windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 34, byref(caption_color), sizeof(caption_color)
            )

        except (ImportError, AttributeError, OSError) as e:
            # If tk.Tk() has not yet been created when a DPI error occurs
            if "root" not in locals():
                root = tk.Tk()
            print(f"[ERROR] Windows UI styling failed: {e}")
    else:
        # For Linux / macOS
        root = tk.Tk()

    app = KodiLogMonitor(root)
    root.mainloop()
