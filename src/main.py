"""
Main entry point for the Kodi Log Monitor application.
Handles high-DPI scaling, Windows-specific dark mode styling, and application initialization.
"""

__author__ = "Nanomani"

import sys
import tkinter as tk

from utils import get_windows_theme
from ui.app import KodiLogMonitor

if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            # On importe une seule fois pour tout le bloc
            from ctypes import windll, byref, sizeof, c_int

            # 1. Gestion de la netteté (DPI)
            windll.shcore.SetProcessDpiAwareness(1)

            root = tk.Tk()
            root.update()

            # 2. Récupération de l'identifiant de la fenêtre (HWND)
            hwnd = windll.user32.GetParent(root.winfo_id())

            # 3. Détection du thème Windows
            IS_DARK = get_windows_theme()  # Retourne 1 (Sombre) ou 0 (Clair)

            # 4. Application du mode sombre immersif (Attribut 20)
            windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 20, byref(c_int(IS_DARK)), sizeof(c_int(IS_DARK))
            )

            # 5. Application de la couleur de la barre de titre (Attribut 34)
            if IS_DARK:
                caption_color = c_int(0x002D2D2D)  # Gris foncé BGR
            else:
                caption_color = c_int(0x00FFFFFF)  # Blanc BGR

            windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 34, byref(caption_color), sizeof(caption_color)
            )

        except (ImportError, AttributeError, OSError) as e:
            # Si tk.Tk() n'est pas encore créé en cas d'erreur DPI
            if "root" not in locals():
                root = tk.Tk()
            print(f"[ERROR] Windows UI styling failed: {e}")
    else:
        # Pour Linux / MacOS
        root = tk.Tk()

    app = KodiLogMonitor(root)
    root.mainloop()
