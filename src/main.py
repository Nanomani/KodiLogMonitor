"""
Main entry point for the Kodi Log Monitor application.
Handles high-DPI scaling, Windows-specific dark mode styling,
and application initialization with CustomTkinter.
"""

__author__ = "Nanomani"

import sys
import os
import tkinter as tk
import customtkinter as ctk

from utils import check_single_instance
from ui.app import KodiLogMonitor
from config import ENABLE_SINGLE_INSTANCE, APP_THEME

# --- CustomTkinter global appearance ---
# Sync CTK appearance mode with the saved app color theme
ctk.set_appearance_mode("light" if APP_THEME == "light" else "dark")
ctk.set_default_color_theme("dark-blue")

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

    # 2. Create the CustomTkinter root window
    root = ctk.CTk()

    # 2.1 Loading the window icone
    if sys.platform == "win32":
        try:
            # PyInstaller extracts the files to a temporary folder stored in sys._MEIPASS
            if hasattr(sys, '_MEIPASS'):
                # If you're in the EXE (your command places the icon at the root: ";.")
                icon_path = os.path.join(sys._MEIPASS, 'logo.ico')
            else:
                # If you run the script normally
                icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'logo.ico')

            if os.path.exists(icon_path):
                root.iconbitmap(icon_path)

        except Exception as e:
            print(f"Erreur chargement icône : {e}")

    # 3. Apply Windows 11 Theme and DWM Attributes (dark title bar)
    if sys.platform == "win32":
        try:
            from ctypes import windll, byref, sizeof, c_int

            # Force a window update to ensure the HWND is valid
            root.update()

            # Retrieve the Window Handle (HWND)
            hwnd = windll.user32.GetParent(root.winfo_id())

            # Use app color theme to drive the title bar appearance
            is_dark = 1 if APP_THEME == "dark" else 0

            try:
                # Attribute 20: Immersive Dark Mode for title bar buttons
                windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, 20, byref(c_int(is_dark)), sizeof(c_int(is_dark))
                )

                # Attribute 34: Custom Caption Color matching the app header
                if APP_THEME == "dark":
                    caption_color = c_int(0x002d2d2d)  # Dark grey BGR
                else:
                    caption_color = c_int(0x00e3e3e3)  # Light grey BGR

                windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, 34, byref(caption_color), sizeof(caption_color)
                )
            except Exception as dwm_err:
                print(f"DWM Attribute Error: {dwm_err}")

        except Exception as win_err:
            print(f"Windows Initialization Error: {win_err}")

    # 4. Start the application
    app = KodiLogMonitor(root)
    root.mainloop()
