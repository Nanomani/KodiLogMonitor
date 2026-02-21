import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import webbrowser
import os
import time
import re
import sys
import locale
import subprocess
from collections import deque
from urllib.parse import quote

# --- CONFIGURATION ---
APP_VERSION = "v1.3.5"
CONFIG_FILE = ".kodi_monitor_config"
DEFAULT_GEOMETRY = "1680x1050"
ICON_NAME = "logo.ico"
KEYWORD_DIR = "keyword_list"

# --- UI THEME ---
COLOR_BG_MAIN = "#1e1e1e"        # Main background color (log area)
COLOR_BG_HEADER = "#2d2d2d"      # Top toolbar background
COLOR_BG_SUBHEADER = "#333333"   # Secondary toolbar background (comboboxes/search)
COLOR_BG_FOOTER = "#2d2d2d"      # Bottom status bar background
COLOR_BTN_DEFAULT = "#3e3e42"    # Standard button background
COLOR_BTN_ACTIVE = "#505050"     # Button background when mouse hovers over it
COLOR_ACCENT = "#007acc"         # Blue accent color (active filters, primary highlights)
COLOR_DANGER = "#e81123"         # Red color for Pause and critical actions
COLOR_WARNING = "#FF9800"        # Orange color for Reset and warnings
COLOR_SEPARATOR = "#444444"      # Vertical line color between button groups
COLOR_TEXT_MAIN = "#d4d4d4"      # Primary text color (log text)
COLOR_TEXT_DIM = "#888888"       # Dimmed text color for icons/placeholders
COLOR_TEXT_BRIGHT = "#ffffff"    # Bright white text for buttons and headers
COLOR_BTN_SECONDARY = "#454545"  # Slightly different grey for secondary small buttons

# COLORS FOR THE CUSTOM SCROLLBAR
SCROLL_THUMB_DEFAULT = "#5a5a5a"  # Lighter gray for the cursor
SCROLL_THUMB_HOVER = "#d4d4d4"    # Light gray when hovering

LOG_COLORS = {
    "debug": "#9e9e9e",           # Grey for debug messages
    "info": "#4CAF50",            # Green for info messages
    "warning": "#FF9800",         # Orange for warnings
    "error": "#F44336",           # Red for errors
    "summary": "#00E5FF",         # Cyan for the system summary block
    "highlight_bg": "#FFF59D",    # Yellow background for search highlights
    "highlight_fg": "#000000"     # Black text for search highlights
}


def get_system_font():
    if sys.platform == "darwin":
        return ("Helvetica", "Arial", "sans-serif")
    if sys.platform == "win32":
        return ("Segoe UI", "Tahoma", "Arial", "sans-serif")
    return ("DejaVu Sans", "Verdana", "sans-serif")


def get_mono_font():
    if sys.platform == "darwin":
        return "Menlo"
    if sys.platform == "win32":
        return "Consolas"
    return "DejaVu Sans Mono"


def get_emoji_font():
    if sys.platform == "win32":
        return "Segoe UI Emoji"
    return get_system_font()


if not os.path.exists(KEYWORD_DIR):
    os.makedirs(KEYWORD_DIR)

LANGS = {
    "FR": {
        "log": "📂  LOG",
        "sum": "📝  RÉSUMÉ",
        "exp": "💾  EXPORT",
        "clr": "🗑️  VIDER",
        "all": "TOUT",
        "debug": "DEBUG",
        "info": "INFO",
        "warn": "WARNING",
        "err": "ERROR",
        "ready": "Prêt",
        "sel": "Sélectionnez un log.",
        "sys_sum": "\n--- RÉSUMÉ SYSTÈME ---\n",
        "loading": "Chargement...",
        "reset": "\n--- FICHIER RÉINITIALISÉ PAR KODI ---\n",
        "stats_simple": "📈 {} lignes",
        "file_size_text": "📁 {}",
        "limit": "⚠️ Limité aux 1000 dernières lignes",
        "file_error": "⚠️ LOG INACCESSIBLE !",
        "none": "Aucun",
        "paused": "⏸️ EN PAUSE",
        "warn_title": "Fichier Volumineux",
        "warn_msg": "Le fichier fait {:.1f} Mo.\nLe chargement complet risque de faire planter l'application.\n\nVeuillez consulter le fichier manuellement.",
        "perf_title": "Performance",
        "perf_msg": "Charger le fichier complet pour voir le contexte ?\n(Cela peut être lent sur les gros fichiers)",
        "search_ph": "Rechercher...",
        "no_match": "❌ Aucune des occurrences recherchées n'a été trouvée",
        "copy": "Copier",
        "sel_all": "Tout sélectionner",
        "search_google": "Rechercher sur Google",
        "paste": "Coller",
        "clear": "Effacer",
        "inactive": "Inactif",
        "t_auto": "Auto",
        "t_light": "Clair",
        "t_dark": "Sombre"
    },
    "EN": {
        "log": "📂  LOG",
        "sum": "📝  SUMMARY",
        "exp": "💾  EXPORT",
        "clr": "CLEAR",
        "all": "ALL",
        "debug": "DEBUG",
        "info": "INFO",
        "warn": "WARNING",
        "err": "ERROR",
        "ready": "Ready",
        "sel": "Select a log.",
        "sys_sum": "\n--- SYSTEM SUMMARY ---\n",
        "loading": "Loading...",
        "reset": "\n--- FILE RESET BY KODI ---\n",
        "stats_simple": "📈 {} lines",
        "file_size_text": "📁 {}",
        "limit": "⚠️ Limited to last 1000 lines",
        "file_error": "⚠️ LOG UNAVAILABLE",
        "none": "None",
        "paused": "⏸️ PAUSED",
        "warn_title": "Large File",
        "warn_msg": "The file is {:.1f} MB.\nLoading the full file may crash the application.\n\nPlease check the file manually.",
        "perf_title": "Performance",
        "perf_msg": "Load the full file to see the context?\n(This might be slow on large files)",
        "search_ph": "Search...",
        "no_match": "❌ No matching occurrences found",
        "copy": "Copy",
        "sel_all": "Select All",
        "search_google": "Search on Google",
        "paste": "Paste",
        "clear": "Clear",
        "inactive": "Inactive",
        "t_auto": "Auto",
        "t_light": "Light",
        "t_dark": "Dark"
    },
    "ES": {
        "log": "📂  LOG",
        "sum": "📝  RESUMEN",
        "exp": "💾  EXPORTAR",
        "clr": "LIMPIAR",
        "all": "TODO",
        "debug": "DEBUG",
        "info": "INFO",
        "warn": "AVISO",
        "err": "ERROR",
        "ready": "Listo",
        "sel": "Seleccione un log.",
        "sys_sum": "\n--- RESUMEN DEL SISTEMA ---\n",
        "loading": "Cargando...",
        "reset": "\n--- ARCHIVO REINICIADO POR KODI ---\n",
        "stats_simple": "📈 {} líneas",
        "file_size_text": "📁 {}",
        "limit": "⚠️ Limitado a 1000 líneas",
        "file_error": "⚠️ LOG NO DISPONIBLE",
        "none": "Ninguno",
        "paused": "⏸️ EN PAUSA",
        "warn_title": "Archivo Grande",
        "warn_msg": "El archivo tiene {:.1f} MB.\nCargar el archivo completo peut colapsar la aplicación.\n\nPor favor, consulte el archivo manualmente.",
        "perf_title": "Rendimiento",
        "perf_msg": "¿Cargar el archivo completo para ver el contexto?\n(Puede ser lento)",
        "search_ph": "Buscar...",
        "no_match": "❌ No se encontró ninguna coincidencia",
        "copy": "Copiar",
        "sel_all": "Seleccionar todo",
        "search_google": "uscar en Google",
        "paste": "Pegar",
        "clear": "Borrar",
        "inactive": "Inactivo",
        "t_auto": "Auto",
        "t_light": "Claro",
        "t_dark": "Oscuro"
    },
    "DE": {
        "log": "📂  LOG",
        "sum": "📝  ÜBERSICHT",
        "exp": "💾  EXPORT",
        "clr": "LEEREN",
        "all": "ALLE",
        "debug": "DEBUG",
        "info": "INFO",
        "warn": "WARNUNG",
        "err": "FEHLER",
        "ready": "Bereit",
        "sel": "Wählen Sie ein Log.",
        "sys_sum": "\n--- SYSTEMÜBERSICHT ---\n",
        "loading": "Ladevorgang...",
        "reset": "\n--- DATEI VON KODI ZURÜCKGESETZT ---\n",
        "stats_simple": "📈 {} Zeilen",
        "file_size_text": "📁 {}",
        "limit": "⚠️ Auf die letzten 1000 zeilen begrenzt",
        "file_error": "⚠️ LOG NICHT VERFÜGBAR",
        "none": "Keine",
        "paused": "⏸️ PAUSE",
        "warn_title": "Große Datei",
        "warn_msg": "Die Datei ist {:.1f} MB groß.\nDas Laden der vollständigen Datei kann die App zum Absturz bringen.\n\nBitte prüfen Sie die Datei manuell.",
        "perf_title": "Leistung",
        "perf_msg": "Vollständige Datei laden, um Kontext zu sehen?\n(Kann bei großen Dateien langsam sein)",
        "search_ph": "Suchen...",
        "no_match": "❌ Keine Treffer gefunden",
        "copy": "Kopieren",
        "sel_all": "Alles auswählen",
        "search_google": "Auf Google suchen",
        "paste": "Einfügen",
        "clear": "Löschen",
        "inactive": "Inaktiv",
        "t_auto": "Auto",
        "t_light": "Hell",
        "t_dark": "Dunkel"
    },
    "IT": {
        "log": "📂  LOG",
        "sum": "📝  RIEPILOGO",
        "exp": "💾  ESPORTA",
        "clr": "PULISCI",
        "all": "TUTTO",
        "debug": "DEBUG",
        "info": "INFO",
        "warn": "AVVISO",
        "err": "ERRORE",
        "ready": "Pronto",
        "sel": "Seleziona un log.",
        "sys_sum": "\n--- RIEPILOGO SISTEMA ---\n",
        "loading": "Caricamento...",
        "reset": "\n--- FILE RESETTATO DA KODI ---\n",
        "stats_simple": "📈 {} righe",
        "file_size_text": "📁 {}",
        "limit": "⚠️ Limitato alle ultime 1000 righe",
        "file_error": "⚠️ LOG NON DISPONIBILE",
        "none": "Nessuno",
        "paused": "⏸️ IN PAUSA",
        "warn_title": "File di Grandi Dimensioni",
        "warn_msg": "Il file è di {:.1f} MB.\nIl caricamento completo potrebbe causare il crash dell'app.\n\nSi prega di consultare il file manualmente.",
        "perf_title": "Prestazioni",
        "perf_msg": "Caricare il file completo per vedere il contesto?\n(Potrebbe essere lento su file grandi)",
        "search_ph": "Cerca...",
        "no_match": "❌ Nessuna occorrenza trovata",
        "copy": "Copia",
        "sel_all": "Seleziona tutto",
        "search_google": "Cerca su Google",
        "paste": "Incolla",
        "clear": "Cancella",
        "inactive": "Inattivo",
        "t_auto": "Auto",
        "t_light": "Chiaro",
        "t_dark": "Scuro"
    }
}


class KodiLogMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Kodi Log Monitor")
        self.window_geometry = DEFAULT_GEOMETRY
        self.root.configure(bg=COLOR_BG_MAIN)
        self.last_activity_time = time.time()
        self.inactivity_limit = 300
        self.last_line_count = 0
        self.last_pause_state = False
        self.last_limit_state = False

        self.main_font_family = get_system_font()
        self.mono_font_family = get_mono_font()
        self.emoji_font_family = get_emoji_font()

        self.set_window_icon()
        self.log_file_path = ""
        self.running = False
        self.monitor_thread = None
        # memory management
        self.seen_lines = deque(maxlen=200)
        self.pending_jump_timestamp = None
        self.log_lock = threading.Lock()

        self.load_full_file = tk.BooleanVar(value=False)
        self.wrap_mode = tk.BooleanVar(value=False)
        self.is_paused = tk.BooleanVar(value=False)
        self.current_lang = tk.StringVar(value=self.detect_os_language())
        self.theme_mode = tk.StringVar(value="Auto")  # Options: Auto, Light, Dark

        self.filter_vars = {
            "all": tk.BooleanVar(value=True),
            "debug": tk.BooleanVar(value=False),
            "info": tk.BooleanVar(value=False),
            "warning": tk.BooleanVar(value=False),
            "error": tk.BooleanVar(value=False)
        }

        self.search_query = tk.StringVar()
        self.selected_list = tk.StringVar()
        self.font_size = 10
        self.show_google_search = tk.BooleanVar(value=True)

        self.filter_colors = {
            "all": COLOR_ACCENT,
            "debug": LOG_COLORS["debug"],
            "info": LOG_COLORS["info"],
            "warning": LOG_COLORS["warning"],
            "error": LOG_COLORS["error"]
        }

        # --- Cursor visibility management ---
        self.cursor_timer = None
        self.cursor_visible = True

        self.setup_ui()
        self.load_session()

        if self.log_file_path:
            # We wait 200ms for the window to be ready before loading.
            self.root.after(200, lambda: self.start_monitoring(self.log_file_path, is_manual=False))

        self.root.geometry(self.window_geometry)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- FILTER CHANGE ---
        for key, var in self.filter_vars.items():
            if key != "all":  # We don't automate "all"; we manage it manually in on_filter_toggle.
                var.trace_add("write", self.trigger_refresh)
        self.search_query.trace_add("write", self.on_search_change)

        self.root.after(5000, self.scheduled_stats_update)

        if sys.platform == "win32":
            self.update_windows_title_bar()
            self.listen_for_theme_changes()

        self.update_button_colors()

    def on_closing(self):
        self.running = False

        if sys.platform == "win32" and hasattr(self, 'old_wndproc'):
            from ctypes import windll
            hwnd = windll.user32.GetParent(self.root.winfo_id())
            windll.user32.SetWindowLongPtrW(hwnd, -4, self.old_wndproc)

        self.window_geometry = self.root.geometry()
        self.save_session()
        self.root.destroy()

    def is_duplicate(self, text):
        clean_text = text.strip()
        if not clean_text:
            return True
        if clean_text in self.seen_lines:
            return True
        self.seen_lines.append(clean_text)
        return False

    # reads the file and sends the lines to the display
    def monitor_loop(self):
        try:
            # Initial opening of the file
            with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                if self.load_full_file.get():
                    f.seek(0)
                else:
                    f.seek(0, os.SEEK_END)
                    f.seek(max(0, f.tell() - 100000))

                initial_lines = f.readlines()
                if not self.load_full_file.get():
                    initial_lines = initial_lines[-1000:]
                last_pos = f.tell()

                to_display = []
                for line in initial_lines:
                    data = self.get_line_data(line)
                    if data and not self.is_duplicate(data[0]):
                        to_display.append(data)
                self.root.after(0, self.bulk_insert, to_display)

                while self.running:
                    try:
                        # 1. Accessibility verification
                        current_size = os.path.getsize(self.log_file_path)

                        # 2. RECONNECTION: Let's get out of this mistake
                        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])
                        msg_erreur = l_ui.get("file_error", "⚠️ IMPORTANT : le fichier de log est inaccessible !")

                        if self.inactivity_timer_var.get() == msg_erreur:
                            # We reset everything to prevent "Inactive" from replacing the error immediately.
                            self.last_activity_time = time.time()
                            self.root.after(0, self.inactivity_timer_var.set, "")
                            # The color is reset according to the actual status (green or orange if limited).
                            new_color = COLOR_WARNING if not self.load_full_file.get() else "#4CAF50"
                            self.root.after(0, self.update_status_color, new_color)

                        # 3. Managing Kodi Restarts
                        if current_size < last_pos:
                            self.root.after(0, self.start_monitoring, self.log_file_path, False, False)
                            return

                        # 4. Reading
                        line = f.readline()
                        if not line:
                            # The calculation is only performed if detection is not disabled (different from 0).
                            if self.inactivity_limit > 0:
                                elapsed = time.time() - self.last_activity_time

                                if elapsed >= self.inactivity_limit:
                                    self.root.after(0, self.update_status_color, COLOR_DANGER)

                                    # Calculating and displaying time (HH:MM)
                                    l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])
                                    mins, secs = divmod(int(elapsed), 60)
                                    timer_str = f"{l_ui['inactive']} : {mins:02d}:{secs:02d}"
                                    self.root.after(0, self.inactivity_timer_var.set, timer_str)
                                else:
                                    self.root.after(0, self.update_status_color, "#666666")
                                    self.root.after(0, self.inactivity_timer_var.set, "")
                            else:
                                # If inactivity_limit is 0, it remains gray with no message.
                                self.root.after(0, self.update_status_color, "#666666")
                                self.root.after(0, self.inactivity_timer_var.set, "")

                            self.root.after(0, self.update_stats)
                            time.sleep(0.4)
                            continue

                        # If reading successful
                        self.last_activity_time = time.time()
                        # If limited mode -> Orange, otherwise Green
                        final_color = COLOR_WARNING if not self.load_full_file.get() else "#4CAF50"
                        self.root.after(0, self.update_status_color, final_color)
                        self.root.after(0, self.inactivity_timer_var.set, "")

                        last_pos = f.tell()
                        data = self.get_line_data(line)
                        if data and not self.is_duplicate(data[0]):
                            self.root.after(0, self.append_to_gui, data[0], data[1])

                    except (IOError, OSError):
                        # LOSS OF ACCESS
                        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])
                        msg = l_ui.get("file_error", "⚠️ IMPORTANT : le fichier de log est inaccessible !")
                        self.root.after(0, self.inactivity_timer_var.set, msg)
                        self.root.after(0, self.update_status_color, COLOR_DANGER)
                        time.sleep(2)
                        continue

        except Exception as e:
            print(f"[ERROR] {type(e).__name__}: {e}")
            self.root.after(0, self.show_loading, False)

    def bulk_insert(self, data_list):
        """Insère un lot de données dans la zone de texte."""
        if not self.running:
            return

        # Data cleansing
        valid_data = [d for d in data_list if d is not None]

        self.txt_area.config(state=tk.NORMAL)
        # Empty before inserting the filter result
        self.txt_area.delete('1.0', tk.END)

        if not valid_data:
            # If nothing is found, the error message is displayed.
            l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])
            message = f"\n\n\n\n\t\t\t{l_ui.get('no_match', 'Aucune occurrence trouvée')}"

            # Insert the message with a specific tag (optional for color)
            # self.txt_area.insert(tk.END, message, "error")
            self.txt_area.insert(tk.END, message, "warning")
            self.show_loading(False)
            self.update_stats()
            return

        # If data exists, it is inserted normally.
        for text, tag in valid_data:
            self.insert_with_highlight(text, tag)

        if self.pending_jump_timestamp:
            self.jump_to_timestamp(self.pending_jump_timestamp)
            self.pending_jump_timestamp = None
        elif not self.is_paused.get():
            self.txt_area.see(tk.END)

        self.update_stats()
        self.show_loading(False)

    # adding new logs
    def append_to_gui(self, text, tag):
        if not self.running or self.is_paused.get():
            return

        with self.log_lock:  # Prevents mixing during writing
            self.txt_area.config(state=tk.NORMAL)
            self.insert_with_highlight(text, tag)
            if not self.is_paused.get():
                self.txt_area.see(tk.END)
            self.update_stats()

    def sort_logs_by_time(self, log_list):
        # Sort lines based on the timestamp (the beginning of the line)
        # The Kodi format "YYYY-MM-DD HH:MM:SS" allows for perfect alphabetical sorting
        return sorted(log_list, key=lambda x: x[0] if isinstance(x, list) else x)

    def start_monitoring(self, path, save=True, retranslate=True, is_manual=True):
        self.last_activity_time = time.time()
        self.inactivity_timer_var.set("")
        self.running = True
        self.seen_lines.clear()
        self.log_file_path = path

        # --- 10 MB SECURITY BLOCK ---
        try:
            if os.path.exists(path):
                file_size_mb = os.path.getsize(path) / (1024 * 1024)
                # If auto-loading AND large file -> we limit
                if not is_manual and file_size_mb > 10:
                    self.load_full_file.set(False)

                # FORCE the update of statistics and the interface
                self.root.after(0, self.update_stats)

        except Exception as e:
            print(f"[ERROR] {type(e).__name__}: {e}")
        # ---------------------------------------

        if retranslate:
            self.retranslate_ui(refresh_monitor=False)
        if save:
            self.save_session()
        self.txt_area.config(state=tk.NORMAL)
        self.txt_area.delete('1.0', tk.END)
        self.show_loading(True)
        self.root.after(150, self._launch_thread)

    def _launch_thread(self):
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()

    def create_custom_button(
        self, parent, text, command,
        bg_color=COLOR_BTN_DEFAULT,
        fg_color=COLOR_TEXT_BRIGHT,
        font=None, padx=12, pady=3
    ):

        if font is None:
            font = (self.emoji_font_family, 9, "bold")

        label = tk.Label(
            parent, text=text, bg=bg_color, fg=fg_color,
            padx=padx, pady=pady, font=font, cursor="hand2"
        )

        label.bind("<Button-1>", lambda event: command())
        label.bind("<Enter>", lambda event: label.config(bg=COLOR_BTN_ACTIVE))
        label.bind("<Leave>", lambda event: label.config(bg=bg_color))

        return label

    def setup_ui(self):
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(2, weight=1)

        style = ttk.Style()
        style.theme_use('clam')

        # --- DARK STYLE FOR COMBOBOX ---
        style.configure(
            "TCombobox",
            fieldbackground=COLOR_BTN_DEFAULT,
            background=COLOR_BTN_DEFAULT,
            foreground=COLOR_TEXT_BRIGHT,
            bordercolor=COLOR_BG_HEADER,
            darkcolor=COLOR_BTN_DEFAULT,
            lightcolor=COLOR_BG_HEADER,
            arrowcolor=COLOR_TEXT_BRIGHT,
            arrowsize=20,
            insertcolor=COLOR_TEXT_BRIGHT,
            selectbackground=COLOR_BTN_DEFAULT,
            selectforeground=COLOR_TEXT_BRIGHT,
            font=(self.main_font_family, 11),
            postoffset=(0, 0, 0, 0)
        )

        style.map(
            "TCombobox",
            fieldbackground=[
                ("readonly", COLOR_BTN_DEFAULT),
                ("focus", COLOR_BTN_DEFAULT),
                ("active", COLOR_BTN_DEFAULT)
            ],
            background=[
                ("readonly", COLOR_BTN_DEFAULT),
                ("focus", COLOR_BTN_DEFAULT),
                ("active", COLOR_BTN_DEFAULT)
            ],
            foreground=[("readonly", COLOR_TEXT_BRIGHT)],
            selectbackground=[
                ("readonly", COLOR_BTN_DEFAULT),
                ("focus", COLOR_BTN_DEFAULT)
            ],
            selectforeground=[
                ("readonly", COLOR_TEXT_BRIGHT),
                ("focus", COLOR_TEXT_BRIGHT)
            ]
        )

        # --- DARK STYLE FOR SCROLLBAR ---
        style.configure(
            "Vertical.TScrollbar",
            gripcount=0,
            background=SCROLL_THUMB_DEFAULT,
            troughcolor=COLOR_BG_HEADER,
            bordercolor=COLOR_BG_HEADER,
            lightcolor=COLOR_BG_HEADER,
            darkcolor=COLOR_BG_HEADER,
            arrowcolor=COLOR_TEXT_DIM,
            width=24,
            arrowsize=24
        )

        style.map("Vertical.TScrollbar",
                  background=[("active", SCROLL_THUMB_HOVER), ("pressed", SCROLL_THUMB_HOVER)])

        self.root.option_add("*TCombobox*exportSelection", False)
        self.root.option_add("*TCombobox*Listbox.background", COLOR_BTN_DEFAULT)
        self.root.option_add("*TCombobox*Listbox.foreground", COLOR_TEXT_BRIGHT)
        self.root.option_add("*TCombobox*Listbox.selectBackground", COLOR_ACCENT)
        self.root.option_add("*TCombobox*Listbox.font", (self.main_font_family, 10))
        self.root.option_add("*TCombobox*Listbox.itemHeight", 45)
        self.root.option_add("*TCombobox*Listbox.padding", 4)
        self.root.option_add("*TCombobox*Listbox.lineSpacing", 2)
        self.root.option_add("*TCombobox*Listbox.listvariable", "")
        self.root.option_add("*TCombobox*Listbox.selectborderwidth", 0)
        self.root.option_add("*TCombobox*Listbox.activestyle", "none")

        if sys.platform.startswith("linux"):
            self.root.option_add("*TCombobox*Listbox.selectForeground", COLOR_TEXT_BRIGHT)

        # Header
        header = tk.Frame(self.root, bg=COLOR_BG_HEADER, padx=10, pady=10)
        header.grid(row=0, column=0, sticky="ew")

        h_left = tk.Frame(header, bg=COLOR_BG_HEADER)
        h_left.pack(side=tk.LEFT, fill=tk.Y)

        # --- Main action buttons ---
        self.btn_log = self.create_custom_button(h_left, "", self.open_file)
        self.btn_log.pack(side=tk.LEFT, padx=5)

        self.btn_exp = self.create_custom_button(h_left, "", self.export_log)
        self.btn_exp.pack(side=tk.LEFT, padx=5)

        # --- Addition of the separator ---
        tk.Frame(
            h_left,
            bg=COLOR_SEPARATOR,
            width=2
        ).pack(side=tk.LEFT, fill=tk.Y, padx=20)

        self.btn_sum = self.create_custom_button(h_left, "", self.show_summary)
        self.btn_sum.pack(side=tk.LEFT, padx=5)

        self.btn_clr = self.create_custom_button(h_left, "", self.clear_console)
        self.btn_clr.pack(side=tk.LEFT, padx=10)

        # --- Addition of the separator ---
        tk.Frame(
            h_left,
            bg=COLOR_SEPARATOR,
            width=2
        ).pack(side=tk.LEFT, fill=tk.Y, padx=20)

        self.filter_frame = tk.Frame(h_left, bg=COLOR_BG_HEADER)
        self.filter_frame.pack(side=tk.LEFT, padx=5)

        # Dictionary to store filter toggle widgets
        self.filter_widgets = {}

        # --- Filter toggle buttons generation ---
        filter_modes = ["all", "info", "warning", "error", "debug"]

        for mode in filter_modes:
            cb = tk.Checkbutton(
                self.filter_frame,
                variable=self.filter_vars[mode],
                indicatoron=0,
                text=mode.upper(),  # Ou votre logique d'icônes/texte
                fg=COLOR_TEXT_BRIGHT,
                font=(self.emoji_font_family, 8, "bold"),
                relief="flat",
                borderwidth=0,
                padx=10,
                pady=5,
                cursor="hand2",
                command=lambda m=mode: self.on_filter_toggle(m),
                highlightthickness=0,
                bg=COLOR_BTN_DEFAULT,
                selectcolor=COLOR_BTN_DEFAULT,
                activebackground="white",
                activeforeground="black"
            )
            cb.pack(side=tk.LEFT, padx=5)

            cb.bind(
                "<Enter>",
                lambda event, w=cb, m=mode: self.on_hover_filter(w, m, True)
            )
            cb.bind(
                "<Leave>",
                lambda event, w=cb, m=mode: self.on_hover_filter(w, m, False)
            )

            # Store widget reference for later updates
            self.filter_widgets[mode] = cb

        # --- Language selection (header right) ---
        h_right = tk.Frame(header, bg=COLOR_BG_HEADER)
        h_right.pack(side=tk.RIGHT, fill=tk.Y)

        # --- Theme selection dropdown ---
        self.combo_theme = ttk.Combobox(
            h_right,
            textvariable=self.theme_mode,
            values=[],
            state="readonly",
            width=12,
            style="TCombobox"
        )

        self.combo_theme.pack(side=tk.LEFT, padx=5)

        if sys.platform != "win32":
            self.combo_theme.pack_forget()

        self.combo_theme.bind("<<ComboboxSelected>>", self.on_theme_change)

        self.combo_lang = ttk.Combobox(
            h_right,
            textvariable=self.current_lang,
            values=sorted(LANGS.keys()),
            state="readonly",
            width=5,
            style="TCombobox"
        )
        self.combo_lang.pack(side=tk.LEFT, padx=5)

        self.combo_lang.bind(
            "<<ComboboxSelected>>",
            lambda event: self.change_language()
        )

        # SUB HEADER
        # --- Sub-header (secondary toolbar) ---
        sub_header = tk.Frame(self.root, bg=COLOR_BG_HEADER, padx=10, pady=4)
        sub_header.grid(row=1, column=0, sticky="ew", pady=(0, 5))

        # Left side of the sub-header
        sh_left = tk.Frame(sub_header, bg=COLOR_BG_HEADER)
        sh_left.pack(side=tk.LEFT, fill=tk.Y)

        # Keyword management box
        kw_box = tk.Frame(sh_left, bg=COLOR_BG_HEADER)
        kw_box.pack(side=tk.LEFT)

        # Keyword list selection combobox
        self.combo_lists = ttk.Combobox(
            kw_box,
            textvariable=self.selected_list,
            state="readonly",
            width=20,
            style="TCombobox"
        )
        self.combo_lists.pack(side=tk.LEFT, padx=5)
        self.combo_lists.bind("<<ComboboxSelected>>", self.on_list_selected)

        # Keyword action buttons (Refresh and Open folder)
        self.create_custom_button(
            kw_box,
            "♻️",
            self.refresh_keyword_list,
            bg_color=COLOR_BTN_SECONDARY,
            padx=8,
            pady=2
        ).pack(side=tk.LEFT, padx=5)

        self.create_custom_button(
            kw_box,
            "📁",
            self.open_keyword_folder,
            bg_color=COLOR_BTN_SECONDARY,
            padx=8,
            pady=2
        ).pack(side=tk.LEFT, padx=5)

        # --- Addition of the separator ---
        tk.Frame(
            sh_left,
            bg=COLOR_SEPARATOR,
            width=2
        ).pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=5)

        # --- Search Box Section ---
        search_box = tk.Frame(sh_left, bg=COLOR_BG_MAIN, padx=8)
        search_box.pack(side=tk.LEFT, padx=5)

        # Search icon
        tk.Label(
            search_box,
            text="🔍",
            bg=COLOR_BG_MAIN,
            fg=COLOR_TEXT_DIM,
            font=(self.emoji_font_family, 9)
        ).pack(side=tk.LEFT)

        # Search entry field
        self.search_entry = tk.Entry(
            search_box,
            textvariable=self.search_query,
            bg=COLOR_BG_MAIN,
            fg=COLOR_TEXT_BRIGHT,
            borderwidth=0,
            width=22,
            insertbackground=COLOR_TEXT_BRIGHT,
            font=(self.main_font_family, 9),
            relief="flat",
            highlightthickness=1,
            highlightbackground=COLOR_BG_MAIN,
            highlightcolor=COLOR_BG_MAIN
        )
        self.search_entry.pack(side=tk.LEFT, padx=5, pady=4)

        self.search_entry.bind("<Button-3>", self.show_search_context_menu)

        # Clear search button (X)
        self.btn_clear_search = tk.Label(
            search_box,
            text="×",
            bg=COLOR_BG_MAIN,
            fg=COLOR_TEXT_DIM,
            font=(self.main_font_family, 11, "bold"),
            cursor="hand2"
        )
        self.btn_clear_search.pack(side=tk.LEFT)
        self.btn_clear_search.bind(
            "<Button-1>",
            lambda event: self.clear_search()
        )

        # --- Addition of the separator ---
        tk.Frame(
            sh_left,
            bg=COLOR_SEPARATOR,
            width=2
        ).pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=5)

        # --- Options Box & Style ---
        opt_box = tk.Frame(sh_left, bg=COLOR_BG_HEADER)
        opt_box.pack(side=tk.LEFT)

        # Common style for option buttons (Checkbuttons used as toggles)
        opt_btn_style = {
            "indicatoron": 0,
            "bg": COLOR_BTN_DEFAULT,
            "fg": COLOR_TEXT_BRIGHT,
            "relief": "flat",
            "font": (self.main_font_family, 10, "bold"),
            "padx": 10,
            "pady": 2,
            "highlightthickness": 0,
            "borderwidth": 0,
            "cursor": "hand2",
            "highlightbackground": COLOR_BG_HEADER
        }

        def add_hover(widget):
            """Add visual hover effects to a widget."""
            # PEP 8: use 'event' instead of 'e' for clarity in lambdas
            widget.bind(
                "<Enter>",
                lambda event: widget.config(bg=COLOR_BTN_ACTIVE)
            )
            widget.bind(
                "<Leave>",
                lambda event: widget.config(bg=COLOR_BTN_DEFAULT)
            )

        # --- Infinity (Full Load) Toggle ---
        self.cb_inf = tk.Checkbutton(
            opt_box,
            text="∞",
            variable=self.load_full_file,
            selectcolor=COLOR_ACCENT,
            command=self.toggle_full_load,
            **opt_btn_style
        )
        self.cb_inf.pack(side=tk.LEFT, padx=5)
        add_hover(self.cb_inf)

        # --- Word Wrap Toggle ---
        self.cb_wrap = tk.Checkbutton(
            opt_box,
            text="↵",
            variable=self.wrap_mode,
            selectcolor=COLOR_ACCENT,
            command=self.apply_wrap_mode,
            **opt_btn_style
        )
        self.cb_wrap.pack(side=tk.LEFT, padx=5)
        add_hover(self.cb_wrap)

        # --- Pause Monitoring Toggle ---
        self.cb_pause = tk.Checkbutton(
            opt_box,
            text="||",
            variable=self.is_paused,
            selectcolor=COLOR_DANGER,
            command=self.toggle_pause_scroll,
            **opt_btn_style
        )
        self.cb_pause.pack(side=tk.LEFT, padx=5)
        add_hover(self.cb_pause)

        # --- Addition of the separator ---
        tk.Frame(
            opt_box,
            bg=COLOR_SEPARATOR,
            width=2
        ).pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=5)

        # --- Reset Filters Button ---
        self.btn_reset = self.create_custom_button(
            opt_box,
            "🔄  RESET",
            self.reset_all_filters,
            fg_color=COLOR_WARNING,
            font=(self.emoji_font_family, 8, "bold"),
            padx=10,
            pady=4
        )
        self.btn_reset.pack(side=tk.LEFT, padx=5)

        # --- Font size controls (sub-header right) ---
        sh_right = tk.Frame(sub_header, bg=COLOR_BG_HEADER)
        sh_right.pack(side=tk.RIGHT, fill=tk.Y)

        self.btn_dec_font = self.create_custom_button(
            sh_right, "-", self.decrease_font, padx=10, pady=3
        )
        self.btn_dec_font.pack(side=tk.LEFT, padx=5)

        self.btn_inc_font = self.create_custom_button(
            sh_right, "+", self.increase_font, padx=10, pady=3
        )
        self.btn_inc_font.pack(side=tk.LEFT, padx=5)

        self.font_label = tk.Label(
            sh_right,
            text=str(self.font_size),
            bg=COLOR_BG_HEADER,
            fg=COLOR_TEXT_BRIGHT,
            width=3,
            font=(self.main_font_family, 9, "bold")
        )
        self.font_label.pack(side=tk.LEFT)

        # --- Main Log Display Area ---
        self.main_container = tk.Frame(self.root, bg=COLOR_BG_MAIN)

        # Grid placement with specific padding (top=0, bottom=10)
        self.main_container.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=10,
            pady=(0, 10)
        )

        # Configure grid weight to allow the container to expand
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        # cursor
        self.txt_area = tk.Text(
            self.main_container,
            wrap=tk.NONE,
            bg=COLOR_BG_MAIN,
            fg=COLOR_TEXT_MAIN,
            font=(self.mono_font_family, self.font_size),
            borderwidth=0,
            highlightthickness=0,
            padx=5, pady=5,
            undo=False,
            selectforeground="#ffffff",
            insertwidth=4,
            insertontime=600,
            insertofftime=300,
            insertbackground=COLOR_TEXT_BRIGHT,
            selectbackground=COLOR_ACCENT,
            inactiveselectbackground=COLOR_ACCENT,
            exportselection=False
        )

        # --- Custom Context Menu (Right-click) ---
        # Create a hidden top-level window for the menu
        self.context_menu = tk.Toplevel(self.root)
        self.context_menu.withdraw()
        self.context_menu.overrideredirect(True)

        # Outer border configuration (using COLOR_SEPARATOR as border color)
        self.context_menu.configure(
            bg=COLOR_SEPARATOR,
            padx=1,
            pady=1
        )

        # Inner container for menu items
        self.menu_inner = tk.Frame(self.context_menu, bg=COLOR_BTN_DEFAULT)
        self.menu_inner.pack(fill="both", expand=True)

        self.search_context_menu = tk.Toplevel(self.root)
        self.search_context_menu.withdraw()
        self.search_context_menu.overrideredirect(True)
        self.search_context_menu.configure(
            bg=COLOR_SEPARATOR,
            padx=1,
            pady=1
        )

        self.search_menu_inner = tk.Frame(self.search_context_menu, bg=COLOR_BTN_DEFAULT)
        self.search_menu_inner.pack(fill="both", expand=True)

        self._build_search_menu_items()

        def add_custom_item(command):
            """Add a stylized clickable item to the custom context menu."""
            item = tk.Label(
                self.menu_inner,
                text="",
                bg=COLOR_BTN_DEFAULT,
                fg=COLOR_TEXT_BRIGHT,
                font=(self.main_font_family, 10),
                padx=15,
                pady=7,
                anchor="w",
                cursor="hand2"
            )
            item.pack(fill="x")

            # PEP 8: Use 'event' instead of 'e' for better clarity in lambdas
            item.bind(
                "<Enter>",
                lambda event: item.config(bg=COLOR_ACCENT)
            )
            item.bind(
                "<Leave>",
                lambda event: item.config(bg=COLOR_BTN_DEFAULT)
            )

            # Execute command and hide menu on click
            item.bind(
                "<Button-1>",
                lambda event: [command(), self.context_menu.withdraw()]
            )

            return item

        # --- Context menu items ---
        self.menu_items = []

        # Item 0: Copy
        self.menu_items.append(
            add_custom_item(self.copy_selection)
        )

        # Item 1: Select All
        self.menu_items.append(
            add_custom_item(lambda: self.txt_area.tag_add("sel", "1.0", "end"))
        )

        # Item 2: Google Search (Stored in a variable for dynamic toggle)
        self.google_menu_item = add_custom_item(self.search_on_google)
        self.menu_items.append(self.google_menu_item)

        # Initial visibility check based on loaded config
        if not self.show_google_search.get():
            self.google_menu_item.pack_forget()

        # --- Scrollbar configuration ---
        self.v_scroll = ttk.Scrollbar(
            self.main_container,
            orient="vertical",
            command=self.txt_area.yview,
            style="Vertical.TScrollbar"
        )
        self.txt_area.configure(yscrollcommand=self.v_scroll.set)

        # --- Text area layout ---
        self.txt_area.grid(row=0, column=0, sticky="nsew")
        self.v_scroll.grid(row=0, column=1, sticky="ns")

        # --- Text area bindings ---
        # Focus on click to display the cursor
        self.txt_area.bind("<Button-1>", lambda event: self.txt_area.focus_set())

        # Reset timer and show cursor on click, key press, or mouse movement
        self.txt_area.bind("<Button-1>", self.reset_cursor_timer, add="+")
        self.txt_area.bind("<Key>", self.reset_cursor_timer, add="+")
        self.txt_area.bind("<Motion>", self.reset_cursor_timer, add="+")

        # Start the initial timer
        self.reset_cursor_timer()

        # Prevent typing while allowing navigation ("soft" read-only)
        allowed_keys = (
            "Up", "Down", "Left", "Right", "Next", "Prior", "Home", "End"
        )
        self.txt_area.bind(
            "<Key>",
            lambda event: "break" if event.keysym not in allowed_keys else None
        )

        # Context menu and interactions
        self.txt_area.bind("<Button-3>", self.show_context_menu)
        self.txt_area.bind("<Double-Button-1>", self.on_double_click_line)

        # --- Loading overlay ---
        self.overlay = tk.Frame(self.main_container, bg=COLOR_BG_MAIN)
        self.loading_label = tk.Label(
            self.overlay,
            text="",
            bg=COLOR_BG_MAIN,
            fg=COLOR_TEXT_BRIGHT,
            font=(self.main_font_family, 12, "bold")
        )
        self.loading_label.pack(expand=True)

        # --- Footer Section ---
        footer = tk.Frame(self.root, bg=COLOR_BG_FOOTER, padx=15, pady=5)  # Padding Y légèrement augmenté
        footer.grid(row=3, column=0, sticky="ew")

        # 1. Indicator Light
        self.status_indicator = tk.Canvas(
            footer, width=20, height=20,
            bg=COLOR_BG_FOOTER, highlightthickness=0
        )
        self.status_indicator.pack(side=tk.LEFT, padx=(20, 12))

        # Creation of the circle
        self.status_circle = self.status_indicator.create_oval(
            2, 2, 18, 18,
            fill=COLOR_WARNING,
            outline="#c4c4c4",
            width=1
        )

        # 2. Inactivity timer
        self.inactivity_timer_var = tk.StringVar(value="")
        self.inactivity_label = tk.Label(
            footer,
            textvariable=self.inactivity_timer_var,
            bg=COLOR_BG_FOOTER,
            fg=COLOR_DANGER,
            font=("Segoe UI", 9, "bold")
        )
        self.inactivity_label.pack(side=tk.LEFT, padx=(0, 10))

        # --- Addition of the separator ---
        tk.Frame(
            footer,
            bg=COLOR_SEPARATOR,
            width=2
        ).pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=2)

        self.footer_var = tk.StringVar()
        self.stats_var = tk.StringVar()
        self.size_var = tk.StringVar()
        self.limit_var = tk.StringVar()
        self.paused_var = tk.StringVar()

        # Shared label style to reduce repetition
        footer_style = {
            "anchor": tk.W,
            "bg": COLOR_BG_FOOTER,
            "font": (self.emoji_font_family, 8, "bold")
        }

        # 3. The file path (📍)
        tk.Label(
            footer, textvariable=self.footer_var,
            fg=COLOR_TEXT_BRIGHT, **footer_style
        ).pack(side=tk.LEFT)

        # --- Addition of the separator ---
        self.sep_lines = tk.Frame(footer, bg=COLOR_SEPARATOR, width=2)

        # 4. Total number of lines (📈)
        self.label_lines = tk.Label(
            footer, textvariable=self.stats_var,
            fg=COLOR_TEXT_BRIGHT, **footer_style
        )

        # --- Addition of the separator ---
        self.sep_size = tk.Frame(footer, bg=COLOR_SEPARATOR, width=2)

        # 5. File size (📁)
        self.label_size = tk.Label(
            footer, textvariable=self.size_var,
            fg=COLOR_TEXT_BRIGHT, **footer_style
        )

        # --- Addition of the separators and labels ---
        self.sep_limit = tk.Frame(footer, bg=COLOR_SEPARATOR, width=2)

        # 6. Lines limited to 1000 (⚠️)
        self.label_limit = tk.Label(
            footer,
            textvariable=self.limit_var,
            fg=COLOR_WARNING,
            **footer_style
        )

        self.sep_pause = tk.Frame(footer, bg=COLOR_SEPARATOR, width=2)

        # 7. Paused (⏸️)
        self.label_pause = tk.Label(
            footer,
            textvariable=self.paused_var,
            fg=COLOR_DANGER,
            **footer_style
        )

        # App version display
        tk.Label(
            footer,
            text=f"KODI LOG MONITOR {APP_VERSION}",
            anchor=tk.E,
            fg=COLOR_TEXT_MAIN,
            bg=COLOR_BG_FOOTER,
            font=(self.main_font_family, 8, "bold"),
            padx=10
        ).pack(side=tk.RIGHT)

    def on_hover_filter(self, widget, mode, is_entering):
        if is_entering:
            # Hover color (light gray, for example)
            widget.config(bg=COLOR_BTN_ACTIVE)
        else:
            # Return to normal state (either the filter color or default gray)
            if self.filter_vars[mode].get():
                color = self.filter_colors.get(mode, COLOR_ACCENT)
                widget.config(bg=color)
            else:
                widget.config(bg=COLOR_BTN_DEFAULT)

    def detect_os_language(self):
        try:
            loc = locale.getlocale()[0]  # Format: 'fr_FR', 'en_US', etc.
            if loc:
                lang_code = loc.split('_')[0].upper()  # Excerpt 'EN' from 'en_US'
                if lang_code in LANGS:
                    return lang_code
        except Exception:
            pass
        return "EN"

    def set_window_icon(self):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")
        icon_path = os.path.join(base_path, ICON_NAME)
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                pass

    def update_tags_config(self):
        c_font = (self.mono_font_family, self.font_size)

        self.txt_area.tag_configure("sel", foreground=COLOR_TEXT_BRIGHT)

        for tag_name, color in LOG_COLORS.items():
            if tag_name not in ["highlight_bg", "highlight_fg"]:
                self.txt_area.tag_configure(tag_name, foreground=color, font=c_font)

        self.txt_area.tag_config("highlight", background=LOG_COLORS["highlight_bg"], foreground=LOG_COLORS["highlight_fg"], font=(c_font[0], self.font_size))

        self.txt_area.configure(bg=COLOR_BG_MAIN, font=c_font)
        self.font_label.config(text=str(self.font_size))
        self.txt_area.tag_raise("sel")

    # Button ALL
    def on_filter_toggle(self, mode):
        """Logique de filtrage stabilisée."""
        if mode == "all":
            if self.filter_vars["all"].get():
                # Specific filters are disabled without triggering trigger_refresh.
                for m in ["debug", "info", "warning", "error"]:
                    self.filter_vars[m].set(False)

                # Force clean reload (like RESET)
                self.refresh_natural_order()
            else:
                # Security: You cannot uncheck ALL if there is no other filter.
                if not any(self.filter_vars[m].get() for m in ["debug", "info", "warning", "error"]):
                    self.filter_vars["all"].set(True)
        else:
            # If INFO, WARN, etc. are enabled, the "ALL" mode is disabled.
            if self.filter_vars[mode].get():
                self.filter_vars["all"].set(False)

            # If nothing is checked, we go back to EVERYTHING.
            if not any(self.filter_vars[m].get() for m in self.filter_vars):
                self.filter_vars["all"].set(True)
                self.refresh_natural_order()
            else:
                self.trigger_refresh()

        self.update_button_colors()

    def reset_all_filters(self):
        """Réinitialise tout en un seul clic."""
        # 1. Stop searching and clear the bar
        self.search_query.set("")

        # 2. Resets the variable associated with the list
        self.selected_list.set("")

        # 3. Forces the visual display to "None" (or "Aucun" depending on your language)
        # We retrieve the correct translation of "None" defined in your LANGS dictionary
        lang_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])
        none_text = lang_ui.get("none", "None")
        self.combo_lists.set(none_text)

        # 4. Reset filter variables (without triggering trigger_refresh immediately)
        for mode in ["info", "warning", "error", "debug"]:
            self.filter_vars[mode].set(False)
        self.filter_vars["all"].set(True)

        # 5. CRITICAL RESET OF THE PAUSE BUTTON
        self.is_paused.set(False)
        if hasattr(self, 'btn_pause'):
            self.btn_pause.config(
                text="⏸ PAUSE",
                bg=COLOR_BTN_DEFAULT,
                activebackground="white"
            )

        # 6. Force update of filter button colors
        self.update_button_colors()

        # 7. THE DOUBLE-CLICK SOLUTION:
        # We force Tkinter to process pending events before continuing.
        self.root.update_idletasks()

        # 8. Clear the cache of lines to start from scratch
        self.seen_lines.clear()

        # 9. Reload display (Natural order as discussed)
        self.refresh_natural_order()

        # 10. Ensure that the text box scrolls down properly since the pause has been lifted.
        self.txt_area.see(tk.END)

    def update_button_colors(self):
        """Applique les couleurs de fond selon l'état de chaque filtre."""
        for mode, var in self.filter_vars.items():
            widget = self.filter_widgets.get(mode)
            if widget:
                if var.get():
                    # Active color (Blue for All, Green for Info, etc.)
                    active_color = self.filter_colors.get(mode, COLOR_ACCENT)
                    widget.config(bg=active_color, selectcolor=active_color)
                else:
                    # Neutral color (Gray)
                    widget.config(bg=COLOR_BTN_DEFAULT, selectcolor=COLOR_BTN_DEFAULT)

    def refresh_natural_order(self):
        """Recharge le log dans l'ordre du fichier (Fixe le problème des lignes sans date)."""
        if not self.log_file_path or not os.path.exists(self.log_file_path):
            return

        self.show_loading(True)
        self.seen_lines.clear()  # Clear the cache to avoid missing lines

        try:
            with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Calculating the playback position
                if self.load_full_file.get():
                    lines = f.readlines()
                else:
                    f.seek(0, os.SEEK_END)
                    # We go back ~200 KB to get the last lines.
                    f.seek(max(0, f.tell() - 200000))
                    lines = f.readlines()[-1000:]

                to_display = []
                # We collect search keywords
                query = self.search_query.get().lower()

                for line in lines:
                    data = self.get_line_data(line)
                    if data:
                        text, tag = data
                        # Filter by search only (Search bar)
                        if not query or query in text.lower():
                            to_display.append((text, tag))

                # INSERTION WITHOUT SORTING (Natural order of the file)
                self.bulk_insert(to_display)

        except Exception as e:
            print(f"[ERROR] {type(e).__name__}: {e}")
            self.show_loading(False)

    def get_line_data(self, line):
        # 1. We check if a specific filter is active (if 'all' is False)
        is_filtering = not self.filter_vars["all"].get()

        # 2. Check if the line has a timestamp (e.g., 2024-05-20)
        # Kodi typically uses the YYYY-MM-DD format at the beginning of lines
        has_timestamp = re.match(r"^\d{4}-\d{2}-\d{2}", line.strip())

        # 3. IF we filter AND the line does NOT have a timestamp, we ignore it (returns None)
        if is_filtering and not has_timestamp:
            return None

        if not line or not line.strip():
            return None

        # SKIP THE KODI STARTUP DASH LINE IF DESIRED
        if "info <general>: --------" in line:
            # On peut décider de l'ignorer ou de la laisser
            # Si vous voulez la supprimer : return None
            return None

        low = line.lower()
        q = self.search_query.get().lower()
        current_tag = None
        if " error " in low:
            current_tag = "error"
        elif " warning " in low:
            current_tag = "warning"
        elif " info " in low:
            current_tag = "info"
        elif " debug " in low:
            current_tag = "debug"
        if not self.filter_vars["all"].get():
            if current_tag is None or not self.filter_vars.get(current_tag, tk.BooleanVar(value=False)).get():
                return None
        if q and q not in low:
            return None
        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])
        if self.selected_list.get() != l_ui["none"]:
            kw = self.get_keywords_from_file()
            if kw and not any(k.lower() in low for k in kw):
                return None
        return (line, current_tag)

    def update_filter_button_colors(self):
        for mode, cb in self.filter_widgets.items():
            if self.filter_vars[mode].get():
                bg = self.filter_colors[mode]
                cb.config(bg=bg, selectcolor=bg)
            else:
                cb.config(bg=COLOR_BTN_DEFAULT, selectcolor=COLOR_BTN_DEFAULT)

    def on_double_click_line(self, event):
        """Gestion du double-clic : Reset complet + Pause + Recherche exacte (TS + Contenu)."""
        self.txt_area.tag_remove("sel", "1.0", tk.END)

        try:
            # 1. Retrieve the index and complete content of the clicked line
            line_index = self.txt_area.index(tk.CURRENT)
            line_content = self.txt_area.get(line_index + " linestart", line_index + " lineend").strip()

            # Extracting the timestamp for the initial search
            timestamp_match = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}', line_content)
            if not timestamp_match:
                return

            target_ts = timestamp_match.group(0)
            # We also keep the entire line (or a large part of it) to remove any ambiguity.
            target_content = line_content

        except Exception as e:
            print(f"[ERROR] {type(e).__name__}: {e}")
            return

        # 2. Complete reset of filters
        self.reset_all_filters()

        # 3. Pause
        self.is_paused.set(True)
        if hasattr(self, 'btn_pause'):
            self.btn_pause.config(text="▶ RESUME", bg=COLOR_DANGER)

        # 4. Force the interface to update so that the entire log is loaded.
        self.root.update_idletasks()

        # 5. Search with TIMESTAMP and CONTENT
        self.find_and_highlight_timestamp(target_ts, target_content)

        return "break"

    def find_and_highlight_timestamp(self, target_ts, target_content=None):
        """Recherche le timestamp et valide avec le contenu de la ligne pour éviter les doublons."""
        self.txt_area.tag_remove("highlight_jump", "1.0", tk.END)

        search_pos = "1.0"
        found_final_idx = None

        while True:
            # We are looking for the next occurrence of the timestamp
            idx = self.txt_area.search(target_ts, search_pos, stopindex=tk.END)
            if not idx:
                break  # No more occurrences found

            # If there is comparison content, the entire line is checked.
            if target_content:
                current_line_text = self.txt_area.get(idx + " linestart", idx + " lineend").strip()

                # Comparison: if the current line contains the target content
                if target_content in current_line_text:
                    found_final_idx = idx
                    break
            else:
                # If there is no comparison content, take the first one found (fallback).
                found_final_idx = idx
                break

            # Otherwise, we continue the search after this line.
            search_pos = self.txt_area.index(idx + " lineend")

        # IF WE FOUND THE EXACT LINE
        if found_final_idx:
            line_end = self.txt_area.index(f"{found_final_idx} lineend")

            # Position the cursor (INSERT)
            self.txt_area.mark_set(tk.INSERT, found_final_idx)

            # Force focus on the text area to validate the position
            self.txt_area.focus_set()

            # Scroll to the line
            self.txt_area.see(found_final_idx)

            # 3. Apply Yellow/Black highlighting
            self.txt_area.tag_add("highlight_temp", found_final_idx, line_end)
            self.txt_area.tag_config(
                "highlight_temp",
                background=LOG_COLORS["highlight_bg"],
                foreground=LOG_COLORS["highlight_fg"],
                font=(self.mono_font_family, self.font_size, "bold")
            )

            # Delete after 5 seconds
            self.root.after(5000, lambda: self.txt_area.tag_remove("highlight_temp", "1.0", tk.END))

    def jump_to_timestamp(self, timestamp):
        self.root.after(100, lambda: self._execute_jump(timestamp))

    def _execute_jump(self, timestamp):
        idx = self.txt_area.search(timestamp, "1.0", tk.END)
        if idx:
            self.txt_area.see(idx)
            start_line = f"{idx} linestart"
            end_line = f"{idx} lineend"
            self.txt_area.tag_add("highlight", start_line, end_line)
            self.root.after(3000, lambda: self.txt_area.tag_remove("highlight", "1.0", tk.END))

    def insert_with_highlight(self, text, base_tag):
        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])
        if self.selected_list.get() == l_ui["none"]:
            self.txt_area.insert(tk.END, text, base_tag)
            return
        kw = self.get_keywords_from_file()
        if not kw:
            self.txt_area.insert(tk.END, text, base_tag)
            return
        try:
            matches = list(re.finditer("|".join(re.escape(k) for k in kw), text, re.IGNORECASE))
        except Exception:
            matches = []
        if not matches:
            self.txt_area.insert(tk.END, text, base_tag)
            return
        last_idx = 0
        for m in matches:
            self.txt_area.insert(tk.END, text[last_idx:m.start()], base_tag)
            self.txt_area.insert(tk.END, text[m.start():m.end()], (base_tag, "highlight"))
            last_idx = m.end()
        self.txt_area.insert(tk.END, text[last_idx:], base_tag)

    def get_keywords_from_file(self):
        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])
        if self.selected_list.get() == l_ui["none"]:
            return []
        path = os.path.join(KEYWORD_DIR, f"{self.selected_list.get()}.txt")
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return [line.strip() for line in f if line.strip()]
        except Exception:
            return []

    def update_stats(self):
        if not self.log_file_path:
            self.sep_lines.pack_forget()
            self.label_lines.pack_forget()
            self.sep_size.pack_forget()
            self.label_size.pack_forget()
            return

        # 1. Recovery of current states
        try:
            current_text = self.stats_var.get()
            current_count = int(''.join(filter(str.isdigit, current_text)))
        except (ValueError, TypeError):
            current_count = -1

        current_pause = self.is_paused.get()
        current_limit = self.load_full_file.get()  # Etat du mode "Infini"

        # 2. UPDATE CONDITION:
        # Refresh only if one of these 3 elements has changed
        if (current_count == self.last_line_count and
                current_pause == self.last_pause_state and
                current_limit == self.last_limit_state):
            return

        # 3. Memorization of new states
        self.last_line_count = current_count
        self.last_pause_state = current_pause
        self.last_limit_state = current_limit

        l = LANGS.get(self.current_lang.get(), LANGS["EN"])

        self.sep_lines.pack_forget()
        self.label_lines.pack_forget()
        self.sep_size.pack_forget()
        self.label_size.pack_forget()
        self.sep_limit.pack_forget()
        self.label_limit.pack_forget()
        self.sep_pause.pack_forget()
        self.label_pause.pack_forget()

        # --- TOTAL NUMBER OF LINES ---
        if self.stats_var.get() and "N/A" not in self.stats_var.get():
            self.sep_lines.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=2)
            self.label_lines.pack(side=tk.LEFT)
        else:
            self.sep_lines.pack_forget()
            self.label_lines.pack_forget()

        # --- Bloc FILE SIZE ---
        size_text = self.size_var.get()
        if size_text and "N/A" not in size_text:
            # Size analysis to change color
            try:
                # The number is extracted from the text (e.g., "12.5 MB" -> 12.5).
                size_value_str = size_text.split(':')[1].strip() if ":" in size_text else size_text
                size_value = float(re.findall(r"[-+]?\d*\.\d+|\d+", size_value_str)[0])
                is_mb = "Mo" in size_text or "MB" in size_text

                # If it is in MB and > 10, we put it in red.
                if is_mb and size_value > 10:
                    self.label_size.config(fg=LOG_COLORS["error"])
                else:
                    self.label_size.config(fg=COLOR_TEXT_BRIGHT)
            except Exception:
                # In case of an analysis error, the default color is retained.
                self.label_size.config(fg=COLOR_TEXT_BRIGHT)

            self.sep_size.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=2)
            self.label_size.pack(side=tk.LEFT)
        else:
            self.sep_size.pack_forget()
            self.label_size.pack_forget()

        # --- Bloc LIMIT ---
        if not self.load_full_file.get():
            self.limit_var.set(l["limit"])
            self.sep_limit.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=2)
            self.label_limit.pack(side=tk.LEFT)
        else:
            self.limit_var.set("")
            self.sep_limit.pack_forget()
            self.label_limit.pack_forget()

        # --- Bloc PAUSE ---
        if self.is_paused.get():
            self.paused_var.set(l["paused"])
            self.sep_pause.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=2)
            self.label_pause.pack(side=tk.LEFT)
        else:
            self.paused_var.set("")
            self.sep_pause.pack_forget()
            self.label_pause.pack_forget()

    def scheduled_stats_update(self):
        if self.running and self.log_file_path:
            size_str, real_total = self.get_file_info()
            l = LANGS.get(self.current_lang.get(), LANGS["EN"])
            self.stats_var.set(l["stats_simple"].format(real_total))
            self.size_var.set(l["file_size_text"].format(size_str))
        self.root.after(5000, self.scheduled_stats_update)

    def get_file_info(self):
        if not self.log_file_path or not os.path.exists(self.log_file_path):
            return "0 KB", 0
        try:
            size_bytes = os.path.getsize(self.log_file_path)
            with open(self.log_file_path, 'rb') as f:
                line_count = sum(1 for _ in f)
            temp_size = size_bytes
            for unit in ['B', 'KB', 'MB', 'GB']:
                if temp_size < 1024:
                    return f"{temp_size:.2f} {unit}", line_count
                temp_size /= 1024
        except Exception:
            pass
        return "N/A", 0

    def trigger_refresh(self, *args):
        """Déclenché lors d'un changement de filtre ou de recherche."""
        if not self.log_file_path:
            return

        # We are temporarily stopping the addition of new lines during the refresh.
        self.txt_area.config(state=tk.NORMAL)
        self.txt_area.delete('1.0', tk.END)

        # We reload the lines from the file or an internal cache.
        # For a robust solution, we reread the relevant lines.
        self.refresh_display_with_sorting()

    def refresh_display_with_sorting(self):
        """Relit le fichier et applique les filtres avec un tri chronologique strict."""
        try:
            with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # The lines are retrieved according to the mode (complete or last 1000).
                if self.load_full_file.get():
                    lines = f.readlines()
                else:
                    f.seek(0, os.SEEK_END)
                    f.seek(max(0, f.tell() - 200000))  # Lecture d'un bloc suffisant
                    lines = f.readlines()[-1000:]

                to_display = []
                for line in lines:
                    data = self.get_line_data(line)
                    if data and self.is_filter_match(data[1], data[0]):
                        # data is (full_text, level_tag)
                        to_display.append(data)

                # --- CORRECTION: CHRONOLOGICAL SORTING ---
                # Sort the list based on the text content (which starts with the date)
                to_display.sort(key=lambda x: x[0])

                # Batch insertion for performance
                self.bulk_insert(to_display)
        except Exception as e:
            print(f"[ERROR] {type(e).__name__}: {e}")

    def is_filter_match(self, tag, text):
        """Vérifie si une ligne correspond aux filtres actifs et à la recherche."""
        # 1. Checking the log level (ALL, INFO filters, etc.)
        if not self.filter_vars["all"].get():
            if not self.filter_vars.get(tag, tk.BooleanVar(value=False)).get():
                return False

        # 2. Verification of textual research
        query = self.search_query.get().lower()
        if query and query not in text.lower():
            return False

        return True

    def on_list_selected(self, event=None):
        selection = self.selected_list.get()
        # The language dictionary is retrieved only once for clarity.
        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])

        if not selection or selection == l_ui["none"]:
            self.trigger_refresh()
            return

        # 1. Using the "search_ph" translation for the loading message
        search_text = l_ui["search_ph"]
        self.show_loading(True, message=search_text)

        # 2. Micro-delay for processing
        self.root.after(300, lambda: self._process_keyword_search(selection))

    def _process_keyword_search(self, selection):
        """Méthode interne pour effectuer la recherche réelle"""
        try:
            # After processing, the UI is refreshed.
            self.trigger_refresh()
        finally:
            # Hide the message once finished
            self.show_loading(False)

    def open_keyword_folder(self):
        abs_path = os.path.abspath(KEYWORD_DIR)
        if sys.platform == 'win32':
            os.startfile(abs_path)
        else:
            subprocess.Popen(['open' if sys.platform == 'darwin' else 'xdg-open', abs_path])

    def refresh_keyword_list(self, trigger_monitor=True):
        l = LANGS.get(self.current_lang.get(), LANGS["EN"])
        files = [f.replace(".txt", "") for f in os.listdir(KEYWORD_DIR) if f.endswith(".txt")]
        self.combo_lists['values'] = [l["none"]] + sorted(files)
        if self.selected_list.get() not in self.combo_lists['values']:
            self.selected_list.set(l["none"])
        if trigger_monitor:
            self.trigger_refresh()

    def retranslate_ui(self, refresh_monitor=True):
        l = LANGS.get(self.current_lang.get(), LANGS["EN"])
        self.btn_log.config(text=l["log"])
        self.btn_sum.config(text=l["sum"])
        self.btn_exp.config(text=l["exp"])
        self.btn_clr.config(text=l["clr"])

        tm = {"all": "all", "info": "info", "warning": "warn", "error": "err", "debug": "debug"}
        for mode, cb in self.filter_widgets.items():
            cb.config(text=l[tm[mode]])

        self.footer_var.set(l["sel"] if not self.log_file_path else f"📍 {self.log_file_path}")
        self.refresh_keyword_list(trigger_monitor=refresh_monitor)
        self.update_stats()
        self.update_filter_button_colors()
        self._build_search_menu_items()

        if hasattr(self, 'menu_items'):
            self.menu_items[0].config(text=l["copy"])
            self.menu_items[1].config(text=l["sel_all"])
            self.menu_items[2].config(text=l["search_google"])

        # Update Theme Combobox values
        self.combo_theme['values'] = [l["t_auto"], l["t_light"], l["t_dark"]]

        # Update displayed text based on current internal state
        mapping = {"Auto": "t_auto", "Light": "t_light", "Dark": "t_dark"}
        current_key = self.theme_mode.get()  # Always "Auto", "Light", or "Dark"
        self.combo_theme.set(l[mapping.get(current_key, "t_auto")])

        if self.is_paused.get():
            self.paused_var.set(l["paused"])
        else:
            self.paused_var.set("")

        if not self.load_full_file.get():
            self.limit_var.set(l["limit"])
        else:
            self.limit_var.set("")

        self.update_stats()

    def on_theme_change(self, event):
        """Map translated selection back to internal keys and apply."""
        l = LANGS.get(self.current_lang.get(), LANGS["EN"])
        selection = self.combo_theme.get()

        # Reverse mapping: Translated string -> Internal key
        if selection == l["t_light"]:
            self.theme_mode.set("Light")
        elif selection == l["t_dark"]:
            self.theme_mode.set("Dark")
        else:
            self.theme_mode.set("Auto")

        self.combo_theme.selection_clear()
        self.root.focus_set()
        self.update_windows_title_bar()
        self.save_session()

    def clear_console(self):
        self.txt_area.config(state=tk.NORMAL)
        self.txt_area.delete('1.0', tk.END)
        self.update_stats()

    def apply_wrap_mode(self):
        self.txt_area.config(wrap=tk.WORD if self.wrap_mode.get() else tk.NONE)

    def toggle_full_load(self):
        # The state of self.load_full_file has already been changed by the Checkbutton.
        if self.log_file_path:
            # We pass is_manual=True to allow full loading.
            self.start_monitoring(self.log_file_path, is_manual=True)
        self.save_session()

    def toggle_pause_scroll(self):
        if not self.is_paused.get() and self.log_file_path:
            self.txt_area.see(tk.END)
        self.update_stats()

    def on_search_change(self, *args):
        if self.search_query.get():
            self.btn_clear_search.pack(side=tk.LEFT, padx=(0, 2))
        else:
            self.btn_clear_search.pack_forget()
        self.trigger_refresh()

    def clear_search(self):
        self.search_query.set("")
        self.search_entry.focus()

    def show_loading(self, show, message=None):
        if show:
            # If a specific message is passed (e.g., "Search..."), it is displayed.
            if message:
                self.loading_label.config(text=message)
            else:
                self.loading_label.config(text=LANGS[self.current_lang.get()]["loading"])

            self.overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.root.update_idletasks()
        else:
            self.overlay.place_forget()

    def change_language(self):
        self.combo_lang.selection_clear()
        self.root.focus_set()
        self.retranslate_ui(True)
        self.save_session()

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("Log files", "*.log"), ("All files", "*.*")])
        if path:
            self.start_monitoring(path, is_manual=False)

    def show_context_menu(self, event):
        """
        Displays the custom context menu at the mouse position and
        dynamically toggles the Google Search option based on config.
        """
        self.txt_area.focus_set()

        # Show or hide the Google Search item based on the user's preference
        if self.show_google_search.get():
            self.google_menu_item.pack(fill="x")
        else:
            self.google_menu_item.pack_forget()

        self.context_menu.geometry(f"+{event.x_root}+{event.y_root}")
        self.context_menu.deiconify()
        self.context_menu.lift()
        self.context_menu.focus_set()
        self.context_menu.bind("<FocusOut>", lambda e: self.context_menu.withdraw())

    def hide_cursor(self):
        """
        Hides the text cursor by setting the blink time to 0.
        """
        self.txt_area.config(insertontime=0)
        self.cursor_visible = False
        self.cursor_timer = None

    def update_windows_title_bar(self):
        """Apply theme to the Windows title bar."""
        if sys.platform == "win32":
            try:
                from ctypes import windll, byref, sizeof, c_int
                self.root.update_idletasks()

                # Use GA_ROOT to get the real window handle
                hwnd = windll.user32.GetAncestor(self.root.winfo_id(), 2)

                mode = self.theme_mode.get()
                if mode == "Dark":
                    is_dark = 1
                elif mode == "Light":
                    is_dark = 0
                else:
                    is_dark = get_windows_theme()

                # Attribute 20: Immersive Dark Mode
                windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, 20, byref(c_int(is_dark)), sizeof(c_int(is_dark))
                )

                # Attribute 34: Title bar color (BGR)
                color = 0x002d2d2d if is_dark else 0x00FFFFFF
                windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, 34, byref(c_int(color)), sizeof(c_int(color))
                )

                # Refresh frame
                windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0020 | 0x0002 | 0x0001 | 0x0004)
            except Exception:
                pass

    def update_status_color(self, color):
        if hasattr(self, 'status_indicator'):
            self.status_indicator.itemconfig(self.status_circle, fill=color)

    def listen_for_theme_changes(self):
        """Intercepte le message WM_SETTINGCHANGE de manière sécurisée (64-bit compatible)."""
        if sys.platform != "win32":
            return

        from ctypes import windll, WINFUNCTYPE, c_int64, c_void_p, c_uint64

        WM_SETTINGCHANGE = 0x001A
        GWLP_WNDPROC = -4

        # 1. Strict type definition to avoid "Access Violation"
        # We use c_int64 and c_void_p to properly support 64 bits
        WNDPROC = WINFUNCTYPE(c_int64, c_void_p, c_uint64, c_uint64, c_int64)

        windll.user32.CallWindowProcW.argtypes = [c_void_p, c_void_p, c_uint64, c_uint64, c_int64]
        windll.user32.CallWindowProcW.restype = c_int64

        windll.user32.SetWindowLongPtrW.argtypes = [c_void_p, c_int64, c_void_p]
        windll.user32.SetWindowLongPtrW.restype = c_void_p

        def wndproc(hwnd, msg, wparam, lparam):
            if msg == WM_SETTINGCHANGE:
                # We use after so as not to block the main Windows thread.
                self.root.after(200, self.update_windows_title_bar)

            # Using the original saved pointer
            return windll.user32.CallWindowProcW(self.old_wndproc, hwnd, msg, wparam, lparam)

        try:
            # Retrieving the correct handle (the parent of winfo_id for Tkinter)
            hwnd = windll.user32.GetParent(self.root.winfo_id())

            # We keep a reference to the function to prevent it from being deleted by the Garbage Collector.
            self.new_wndproc = WNDPROC(wndproc)

            # Replacement of the procedure
            self.old_wndproc = windll.user32.SetWindowLongPtrW(hwnd, GWLP_WNDPROC, self.new_wndproc)
        except Exception as e:
            print(f"[ERROR] {type(e).__name__}: {e}")

    def check_theme_periodically(self):
        """Checks the Windows theme every 2 seconds in a secure manner."""
        if not self.running:
            return

        try:
            # We retrieve the current theme via your existing function.
            current_is_dark = get_windows_theme()

            # If this is your first time or if the theme has changed
            if not hasattr(self, '_last_recorded_theme') or self._last_recorded_theme != current_is_dark:
                self.check_theme_periodically()
                self._last_recorded_theme = current_is_dark

        except Exception:
            pass

        # We will restart the verification in 2000ms (2 seconds).
        self.root.after(2000, self.check_theme_periodically)

    def reset_cursor_timer(self, event=None):
        """
        Resets the inactivity timer and restores cursor visibility.
        """
        # Cancel existing timer if it exists
        if self.cursor_timer:
            self.root.after_cancel(self.cursor_timer)

        # Restore cursor blink settings if it was hidden
        if not self.cursor_visible:
            self.txt_area.config(insertontime=600)
            self.cursor_visible = True

        # Set new timer for 5 seconds (5000 ms)
        self.cursor_timer = self.root.after(5000, self.hide_cursor)

    def search_on_google(self):
        try:
            selected_text = self.txt_area.get(tk.SEL_FIRST, tk.SEL_LAST)
            if selected_text.strip():
                url = f"https://www.google.com/search?q={quote(selected_text.strip())}"
                webbrowser.open(url)
        except tk.TclError:
            pass

    def copy_selection(self):
        try:
            selected_text = self.txt_area.get(tk.SEL_FIRST, tk.SEL_LAST)
            if selected_text:
                self.root.clipboard_clear()
                self.root.clipboard_append(selected_text)
        except tk.TclError:
            pass

    def show_search_context_menu(self, event):
        # Hide the other menu if it is open
        self.context_menu.withdraw()

        # The search menu is displayed.
        self.search_context_menu.geometry(f"+{event.x_root}+{event.y_root}")
        self.search_context_menu.deiconify()
        self.search_context_menu.lift()
        self.search_context_menu.focus_set()

    def _build_search_menu_items(self):
        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])

        for widget in self.search_menu_inner.winfo_children():
            widget.destroy()

        # Paste button
        btn_paste = tk.Label(
            self.search_menu_inner,
            text=l_ui["paste"],
            bg=COLOR_BTN_DEFAULT,
            fg=COLOR_TEXT_BRIGHT,
            font=(self.main_font_family, 10),
            padx=15,
            pady=7,
            anchor="w",
            cursor="hand2"
        )

        btn_paste.pack(fill="x")
        btn_paste.bind("<Enter>", lambda e: btn_paste.config(bg=COLOR_ACCENT))
        btn_paste.bind("<Leave>", lambda e: btn_paste.config(bg=COLOR_BTN_DEFAULT))
        btn_paste.bind("<Button-1>", lambda e: [self.search_entry.event_generate("<<Paste>>"), self.search_context_menu.withdraw()])

        # Clear button
        btn_clear = tk.Label(
            self.search_menu_inner,
            text=l_ui["clear"],
            bg=COLOR_BTN_DEFAULT,
            fg=COLOR_TEXT_BRIGHT,
            font=(self.main_font_family, 10),
            padx=15,
            pady=7,
            anchor="w",
            cursor="hand2"
        )

        btn_clear.pack(fill="x")
        btn_clear.bind("<Enter>", lambda e: btn_clear.config(bg=COLOR_ACCENT))
        btn_clear.bind("<Leave>", lambda e: btn_clear.config(bg=COLOR_BTN_DEFAULT))
        btn_clear.bind("<Button-1>", lambda e: [self.search_query.set(""), self.search_context_menu.withdraw()])

    def increase_font(self):
        self.font_size += 1
        self.update_tags_config()
        self.save_session()

    def decrease_font(self):
        if self.font_size > 6:
            self.font_size -= 1
            self.update_tags_config()
            self.save_session()

    def show_summary(self):
        if not self.log_file_path:
            return
        try:
            with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                c = f.read()
                s = list(re.finditer(r"(-+\n.*?Starting Kodi.*?-+\n)", c, re.DOTALL))
                if s:
                    self.txt_area.insert(tk.END, LANGS.get(self.current_lang.get(), LANGS["EN"])["sys_sum"], "summary")
                    self.txt_area.insert(tk.END, s[-1].group(1), "summary")
                    self.txt_area.see(tk.END)
        except Exception:
            pass

    def export_log(self):
        """
        Saves the current content of the text area to a file chosen by the user.
        """
        save_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile="kodi_extract.txt"
        )

        if save_path:
            try:
                with open(save_path, "w", encoding="utf-8") as f:
                    # Retrieve all text from the start (1.0) to the end
                    f.write(self.txt_area.get("1.0", tk.END))
            except IOError as e:
                print(f"Error exporting log: {e}")

    def save_session(self):
        """
        Saves the current application state with perfectly aligned comments.
        """
        try:
            modes = ["all", "info", "warning", "error", "debug"]
            filter_states = ",".join(["1" if self.filter_vars[m].get() else "0" for m in modes])

            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                # We use a fixed width of 40 characters for the value part
                w = 40
                config_data = [
                    f"{str(self.log_file_path):<{w}} # log_file_path",
                    f"{str(self.current_lang.get()):<{w}} # language",
                    f"{('1' if self.load_full_file.get() else '0'):<{w}} # load_full_file",
                    f"{str(self.font_size):<{w}} # font_size",
                    f"{str(self.window_geometry):<{w}} # window_geometry",
                    f"{str(self.selected_list.get()):<{w}} # selected_keyword_list",
                    f"{filter_states:<{w}} # filter_states (all,debug,info,warn,err)",
                    f"{('1' if self.show_google_search.get() else '0'):<{w}} # show_google_search_menu",
                    f"{str(self.theme_mode.get()):<{w}} # theme_mode",
                    f"{str(self.inactivity_limit):<{w}} # inactivity_limit_seconds"
                ]
                f.write("\n".join(config_data))
        except (IOError, OSError) as e:
            print(f"Error saving session: {e}")

    def load_session(self):
        """
        Load previous session settings from the configuration file.
        """
        if not os.path.exists(CONFIG_FILE):
            # No config file, perform basic UI updates and return
            self.retranslate_ui(False)
            self.update_tags_config()
            return

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                # Use split('#')[0] to get only the value before the comment
                lines = [line.split('#')[0].strip() for line in f.read().splitlines()]

                # 1. Log file path
                if len(lines) >= 1 and os.path.exists(lines[0]):
                    self.log_file_path = lines[0]

                # 2. Current language
                if len(lines) >= 2 and lines[1] in LANGS:
                    self.current_lang.set(lines[1])

                # 3. Load full file preference
                if len(lines) >= 3:
                    self.load_full_file.set(lines[2] == "1")

                # 4. Font size
                if len(lines) >= 4:
                    try:
                        self.font_size = int(lines[3])
                    except ValueError:
                        pass

                # 5. Window geometry
                if len(lines) >= 5:
                    self.window_geometry = lines[4]

                # 6. Selected keyword list
                if len(lines) >= 6:
                    none_values = [v["none"] for v in LANGS.values()]
                    if lines[5] not in none_values:
                        self.selected_list.set(lines[5])
                    else:
                        current_none = LANGS[self.current_lang.get()]["none"]
                        self.selected_list.set(current_none)

                # 7. Filter states
                if len(lines) >= 7:
                    states = lines[6].split(",")
                    modes = ["all", "info", "warning", "error", "debug"]
                    for i, state in enumerate(states):
                        if i < len(modes):
                            self.filter_vars[modes[i]].set(state == "1")

                # 8. Google Search Context Menu Visibility
                if len(lines) >= 8:
                    self.show_google_search.set(lines[7] == "1")
                else:
                    # Default to enabled if the line doesn't exist yet
                    self.show_google_search.set(True)

                # 9. theme windows light, dark, auto
                if len(lines) >= 9:
                    self.theme_mode.set(lines[8])

                # 10. Inactivity Limit
                if len(lines) >= 10:
                    try:
                        self.inactivity_limit = int(lines[9])
                    except ValueError:
                        self.inactivity_limit = 300

        except (IOError, OSError, Exception) as e:
            # Print error for debugging purposes if needed
            print(f"Error loading configuration: {e}")

        # Finalize UI setup after loading data
        self.retranslate_ui(False)
        self.update_tags_config()

        # Automatically resume monitoring if a valid log file was found
        if self.log_file_path:
            self.start_monitoring(self.log_file_path, False, False)


if sys.platform == "win32":
    import winreg
else:
    winreg = None


def get_windows_theme():
    """
    Check the Windows Registry to see if the user prefers Dark Mode.
    Returns: 1 for Dark Mode, 0 for Light Mode.
    """
    try:
        registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return 0 if value == 1 else 1  # 1 = Dark, 0 = Light
    except Exception:
        return 1  # Default to Dark Mode if check fails


if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            from ctypes import windll, byref, sizeof, c_int
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

    root = tk.Tk()

    if sys.platform == "win32":
        try:
            from ctypes import windll, byref, sizeof, c_int
            root.update()
            hwnd = windll.user32.GetParent(root.winfo_id())

            # 1. Detect user theme preference
            is_dark = get_windows_theme()  # Returns 1 (Dark) or 0 (Light)

            # 2. Apply Immersive Dark Mode attribute (20)
            # This ensures the window buttons (Min/Max/Close) adapt their color
            windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 20, byref(c_int(is_dark)), sizeof(c_int(is_dark))
            )

            # 3. Apply custom caption color (Attribute 34)
            # If Dark: use Grey (0x002d2d2d), if Light: let Windows decide (or use White)
            if is_dark:
                caption_color = c_int(0x002d2d2d)  # Grey BGR
                windll.dwmapi.DwmSetWindowAttribute(hwnd, 34, byref(caption_color), sizeof(caption_color))
            else:
                # Default Light color (White/Light Grey)
                caption_color = c_int(0x00FFFFFF)
                windll.dwmapi.DwmSetWindowAttribute(hwnd, 34, byref(caption_color), sizeof(caption_color))

        except Exception as e:
            print(f"[ERROR] {type(e).__name__}: {e}")

    app = KodiLogMonitor(root)
    root.mainloop()
