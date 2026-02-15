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

# --- CONFIGURATION ---
APP_VERSION = "v1.3.2"
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
    "highlight_bg": "#FFF176",    # Yellow background for search highlights
    "highlight_fg": "#000000"     # Black text for search highlights
}


def get_system_font():
    if sys.platform == "darwin":
        return "Helvetica"
    if sys.platform == "win32":
        return "Segoe UI"
    return "DejaVu Sans"


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
        "stats_simple": " | 📈 TOTAL : {} lignes | 📁 {}",
        "limit": " | ⚠️ LIMITÉ AUX 1000 DERNIÈRES LIGNES",
        "none": "Aucun",
        "paused": "⏸️ EN PAUSE",
        "warn_title": "Fichier Volumineux",
        "warn_msg": "Le fichier fait {:.1f} Mo.\nLe chargement complet risque de faire planter l'application.\n\nVeuillez consulter le fichier manuellement.",
        "perf_title": "Performance",
        "perf_msg": "Charger le fichier complet pour voir le contexte ?\n(Cela peut être lent sur les gros fichiers)",
        "search_ph": "Rechercher...",
        "copy": "Copier",
        "sel_all": "Tout sélectionner",
        "search_google": "Rechercher sur Google"
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
        "stats_simple": " | 📈 TOTAL : {} lines | 📁 {}",
        "limit": " | ⚠️ LIMITED TO LAST 1000 LINES",
        "none": "None",
        "paused": "⏸️ PAUSED",
        "warn_title": "Large File",
        "warn_msg": "The file is {:.1f} MB.\nLoading the full file may crash the application.\n\nPlease check the file manually.",
        "perf_title": "Performance",
        "perf_msg": "Load the full file to see the context?\n(This might be slow on large files)",
        "search_ph": "Search...",
        "copy": "Copy",
        "sel_all": "Select All",
        "search_google": "Search on Google"
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
        "stats_simple": " | 📈 TOTAL : {} líneas | 📁 {}",
        "limit": " | ⚠️ LIMITADO A 1000 LÍNEAS",
        "none": "Ninguno",
        "paused": "⏸️ EN PAUSA",
        "warn_title": "Archivo Grande",
        "warn_msg": "El archivo tiene {:.1f} MB.\nCargar el archivo completo peut colapsar la aplicación.\n\nPor favor, consulte el archivo manualmente.",
        "perf_title": "Rendimiento",
        "perf_msg": "¿Cargar el archivo completo para ver el contexto?\n(Puede ser lento)",
        "search_ph": "Buscar...",
        "copy": "Copiar",
        "sel_all": "Seleccionar todo",
        "search_google": "uscar en Google"
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
        "stats_simple": " | 📈 GESAMT: {} Zeilen | 📁 {}",
        "limit": " | ⚠️ AUF DIE LETZTEN 1000 ZEILEN BEGRENZT",
        "none": "Keine",
        "paused": "⏸️ PAUSE",
        "warn_title": "Große Datei",
        "warn_msg": "Die Datei ist {:.1f} MB groß.\nDas Laden der vollständigen Datei kann die App zum Absturz bringen.\n\nBitte prüfen Sie die Datei manuell.",
        "perf_title": "Leistung",
        "perf_msg": "Vollständige Datei laden, um Kontext zu sehen?\n(Kann bei großen Dateien langsam sein)",
        "search_ph": "Suchen...",
        "copy": "Kopieren",
        "sel_all": "Alles auswählen",
        "search_google": "Auf Google suchen"
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
        "stats_simple": " | 📈 TOTALE: {} righe | 📁 {}",
        "limit": " | ⚠️ LIMITATO ALLE ULTIME 1000 RIGHE",
        "none": "Nessuno",
        "paused": "⏸️ IN PAUSA",
        "warn_title": "File di Grandi Dimensioni",
        "warn_msg": "Il file è di {:.1f} MB.\nIl caricamento completo potrebbe causare il crash dell'app.\n\nSi prega di consultare il file manualmente.",
        "perf_title": "Prestazioni",
        "perf_msg": "Caricare il file completo per vedere il contesto?\n(Potrebbe essere lento su file grandi)",
        "search_ph": "Cerca...",
        "copy": "Copia",
        "sel_all": "Seleziona tutto",
        "search_google": "Cerca su Google"
    }
}

class KodiLogMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Kodi Log Monitor")
        self.window_geometry = DEFAULT_GEOMETRY
        self.root.configure(bg=COLOR_BG_MAIN)

        self.main_font_family = get_system_font()
        self.mono_font_family = get_mono_font()
        self.emoji_font_family = get_emoji_font()

        self.set_window_icon()
        self.log_file_path = ""
        self.running = False
        self.monitor_thread = None
        self.seen_lines = deque(maxlen=200)
        self.pending_jump_timestamp = None

        self.load_full_file = tk.BooleanVar(value=False)
        self.wrap_mode = tk.BooleanVar(value=False)
        self.is_paused = tk.BooleanVar(value=False)
        self.current_lang = tk.StringVar(value=self.detect_os_language())

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

        self.filter_colors = {
            "all": COLOR_ACCENT,
            "debug": LOG_COLORS["debug"],
            "info": LOG_COLORS["info"],
            "warning": LOG_COLORS["warning"],
            "error": LOG_COLORS["error"]
        }

        self.setup_ui()
        self.load_session()
        self.root.geometry(self.window_geometry)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        for var in self.filter_vars.values():
            var.trace_add("write", self.trigger_refresh)
        self.search_query.trace_add("write", self.on_search_change)

        self.root.after(5000, self.scheduled_stats_update)

    def on_closing(self):
        self.running = False
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

    def monitor_loop(self):
        try:
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
                    if not os.path.exists(self.log_file_path):
                        break
                    current_size = os.path.getsize(self.log_file_path)
                    if current_size < last_pos:
                        self.root.after(0, self.start_monitoring, self.log_file_path, False, False)
                        return

                    line = f.readline()
                    if not line:
                        self.root.after(0, self.update_stats)
                        time.sleep(0.4)
                        continue

                    last_pos = f.tell()
                    data = self.get_line_data(line)
                    if data and not self.is_duplicate(data[0]):
                        self.root.after(0, self.append_to_gui, data[0], data[1])
        except:
            self.root.after(0, self.show_loading, False)

    def bulk_insert(self, data_list):
        """Insère un lot de données dans la zone de texte de manière optimisée."""
        if not self.running:
            return

        valid_data = [d for d in data_list if d is not None]
        if not valid_data:
            self.show_loading(False)
            return

        self.txt_area.config(state=tk.NORMAL)

        for text, tag in valid_data:
            self.insert_with_highlight(text, tag)

        if self.pending_jump_timestamp:
            self.jump_to_timestamp(self.pending_jump_timestamp)
            self.pending_jump_timestamp = None
        elif not self.is_paused.get():
            self.txt_area.see(tk.END)

        self.update_stats()
        self.show_loading(False)

    def append_to_gui(self, text, tag):
        if not self.running:
            return

        if self.is_paused.get():
            return

        self.txt_area.config(state=tk.NORMAL)
        self.insert_with_highlight(text, tag)
        if not self.is_paused.get():
            self.txt_area.see(tk.END)
        self.update_stats()

    def start_monitoring(self, path, save=True, retranslate=True):
        self.running = True
        self.seen_lines.clear()
        self.log_file_path = path
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
            """Crée un bouton personnalisé à partir d'un label Tkinter."""
            if font is None:
                font = (self.emoji_font_family, 9, "bold")

            label = tk.Label(
                parent, text=text, bg=bg_color, fg=fg_color,
                padx=padx, pady=pady, font=font, cursor="hand2"
            )

            # Liaison des événements (PEP 8 : 'event' au lieu de 'e')
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
            insertcolor=COLOR_TEXT_BRIGHT
        )

        style.map("TCombobox",
                  fieldbackground=[("readonly", COLOR_BTN_DEFAULT), ("focus", COLOR_BTN_DEFAULT)],
                  background=[("readonly", COLOR_BTN_DEFAULT), ("focus", COLOR_BTN_DEFAULT)])

        # --- DARK STYLE FOR SCROLLBAR ---
        style.configure("Vertical.TScrollbar",
            gripcount=0,
            background=SCROLL_THUMB_DEFAULT,
            troughcolor=COLOR_BG_HEADER,
            bordercolor=COLOR_BG_HEADER,
            lightcolor=COLOR_BG_HEADER,
            darkcolor=COLOR_BG_HEADER,
            arrowcolor=COLOR_TEXT_DIM
        )

        style.map("Vertical.TScrollbar",
                  background=[("active", SCROLL_THUMB_HOVER), ("pressed", SCROLL_THUMB_HOVER)])

        self.root.option_add("*TCombobox*Listbox.background", COLOR_BTN_DEFAULT)
        self.root.option_add("*TCombobox*Listbox.foreground", COLOR_TEXT_BRIGHT)
        self.root.option_add("*TCombobox*Listbox.selectBackground", COLOR_ACCENT)

        if sys.platform.startswith("linux"):
            self.root.option_add("*TCombobox*Listbox.selectForeground", COLOR_TEXT_BRIGHT)

        # Header
        header = tk.Frame(self.root, bg=COLOR_BG_HEADER, padx=10, pady=10)
        header.grid(row=0, column=0, sticky="ew")

        h_left = tk.Frame(header, bg=COLOR_BG_HEADER)
        h_left.pack(side=tk.LEFT, fill=tk.Y)

        # --- Main action buttons ---
        # Note: Using a helper method to keep button creation consistent
        self.btn_log = self.create_custom_button(h_left, "", self.open_file)
        self.btn_log.pack(side=tk.LEFT, padx=5)

        self.btn_sum = self.create_custom_button(h_left, "", self.show_summary)
        self.btn_sum.pack(side=tk.LEFT, padx=5)

        self.btn_exp = self.create_custom_button(h_left, "", self.export_log)
        self.btn_exp.pack(side=tk.LEFT, padx=5)

        self.btn_clr = self.create_custom_button(h_left, "", self.clear_console)
        self.btn_clr.pack(side=tk.LEFT, padx=10)

        # --- Visual separator and Filters area ---
        # Thin vertical frame acting as a UI separator
        tk.Frame(
            h_left,
            bg=COLOR_SEPARATOR,
            width=1
        ).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        self.filter_frame = tk.Frame(h_left, bg=COLOR_BG_HEADER)
        self.filter_frame.pack(side=tk.LEFT, padx=5)

        # Dictionary to store filter toggle widgets
        self.filter_widgets = {}

        # --- Filter toggle buttons generation ---
        filter_modes = ["all", "debug", "info", "warning", "error"]

        for mode in filter_modes:
            # Create a toggleable checkbutton for each log level
            cb = tk.Checkbutton(
                self.filter_frame,
                variable=self.filter_vars[mode],
                indicatoron=0,
                fg=COLOR_TEXT_BRIGHT,
                font=(self.emoji_font_family, 8, "bold"),
                relief="flat",
                borderwidth=0,
                padx=10,
                pady=5,
                cursor="hand2",
                command=lambda m=mode: self.on_filter_toggle(m),
                highlightthickness=0,
                highlightbackground=COLOR_BG_HEADER
            )
            cb.pack(side=tk.LEFT, padx=5)

            # Bind hover events for visual feedback
            # Using 'event' instead of 'e' as per PEP 8 naming conventions
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

        self.combo_lang = ttk.Combobox(
            h_right,
            textvariable=self.current_lang,
            values=sorted(LANGS.keys()),
            state="readonly",
            width=4,
            style="TCombobox"
        )
        self.combo_lang.pack(side=tk.LEFT, padx=5)

        # Bind language change event
        # PEP 8: use 'event' instead of 'e' for better clarity
        self.combo_lang.bind(
            "<<ComboboxSelected>>",
            lambda event: self.change_language()
        )

        # Sub Header
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
            width=18,
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

        # --- Search Box Section ---
        search_box = tk.Frame(sh_left, bg=COLOR_BG_MAIN, padx=8)
        search_box.pack(side=tk.LEFT, padx=15)

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
            highlightcolor=COLOR_ACCENT
        )
        self.search_entry.pack(side=tk.LEFT, padx=5, pady=4)

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
        self.txt_area = tk.Text(self.main_container, wrap=tk.NONE, bg=COLOR_BG_MAIN,
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

        # Remove window borders and title bar for a professional look
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

        def add_custom_item(command):
            """Add a stylized clickable item to the custom context menu."""
            item = tk.Label(
                self.menu_inner,
                text="",
                bg=COLOR_BTN_DEFAULT,
                fg=COLOR_TEXT_BRIGHT,
                font=(self.main_font_family, 9),
                padx=15,
                pady=6,
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
        self.menu_items.append(
            add_custom_item(
                lambda: self.root.focus_get().event_generate("<<Copy>>")
            )
        )
        self.menu_items.append(
            add_custom_item(
                lambda: self.txt_area.tag_add("sel", "1.0", "end")
            )
        )
        self.menu_items.append(add_custom_item(self.search_on_google))

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
        footer = tk.Frame(self.root, bg=COLOR_BG_FOOTER, padx=15, pady=3)
        footer.grid(row=3, column=0, sticky="ew")

        self.footer_var = tk.StringVar()
        self.stats_var = tk.StringVar()
        self.limit_var = tk.StringVar()
        self.paused_var = tk.StringVar()

        # Shared label style to reduce repetition
        footer_style = {
            "anchor": tk.W,
            "bg": COLOR_BG_FOOTER,
            "font": (self.emoji_font_family, 8, "bold")
        }

        tk.Label(
            footer, textvariable=self.footer_var,
            fg=COLOR_TEXT_BRIGHT, **footer_style
        ).pack(side=tk.LEFT)

        tk.Label(
            footer, textvariable=self.stats_var,
            fg=COLOR_TEXT_BRIGHT, **footer_style
        ).pack(side=tk.LEFT)

        tk.Label(
            footer, textvariable=self.limit_var,
            fg=COLOR_WARNING, **footer_style
        ).pack(side=tk.LEFT)

        tk.Label(
            footer, textvariable=self.paused_var,
            fg=COLOR_DANGER, padx=10, **footer_style
        ).pack(side=tk.LEFT)

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
        if self.filter_vars[mode].get():
            widget.config(bg=self.filter_colors[mode])
        else:
            widget.config(bg=COLOR_BTN_ACTIVE if is_entering else COLOR_BTN_DEFAULT)

    def detect_os_language(self):
        try:
            loc = locale.getlocale()[0] or (locale.getdefaultlocale()[0] if hasattr(locale, 'getdefaultlocale') else None)
            if loc:
                return loc.split('_')[0].upper() if loc.split('_')[0].upper() in LANGS else "EN"
        except:
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
            except:
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

    def on_filter_toggle(self, clicked_mode):
        if clicked_mode == "all":
            if self.filter_vars["all"].get():
                for mode in ["debug", "info", "warning", "error"]:
                    self.filter_vars[mode].set(False)
            else:
                if not any(self.filter_vars[m].get() for m in ["debug", "info", "warning", "error"]):
                    self.filter_vars["all"].set(True)
        else:
            if self.filter_vars[clicked_mode].get():
                self.filter_vars["all"].set(False)
            else:
                if not any(self.filter_vars[m].get() for m in ["debug", "info", "warning", "error"]):
                    self.filter_vars["all"].set(True)
        self.update_filter_button_colors()

    def reset_all_filters(self):
        self.running = False
        l = LANGS.get(self.current_lang.get(), LANGS["EN"])
        self.search_query.set("")
        self.selected_list.set(l["none"])
        self.is_paused.set(False)
        self.filter_vars["all"].set(True)
        for mode in ["debug", "info", "warning", "error"]:
            self.filter_vars[mode].set(False)
        self.txt_area.config(state=tk.NORMAL)
        self.txt_area.delete('1.0', tk.END)
        if self.log_file_path:
            self.root.after(100, lambda: self.start_monitoring(self.log_file_path, save=False, retranslate=False))

    def on_double_click_line(self, event):
        if not self.log_file_path:
            return
        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])

        index = self.txt_area.index(f"@{event.x},{event.y} linestart")
        line_text = self.txt_area.get(index, f"{index} lineend")
        ts_match = re.search(r"(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\.\d{3})", line_text)

        if not ts_match:
            return
        timestamp = ts_match.group(1)

        # Filter check
        has_filter = not self.filter_vars["all"].get()
        has_search = len(self.search_query.get().strip()) > 0
        has_keywords = self.selected_list.get() != l_ui["none"]

        # 1. Security: File size
        try:
            file_size_mb = os.path.getsize(self.log_file_path) / (1024 * 1024)
            if file_size_mb > 50:
                messagebox.showwarning(l_ui["warn_title"], l_ui["warn_msg"].format(file_size_mb))
                return
        except:
            pass

        # 2. Case "View already complete" -> Pause + Simple highlighting
        if not has_filter and not has_search and not has_keywords and self.load_full_file.get():
            self.is_paused.set(True)
            self.update_stats()
            self._execute_jump(timestamp)
            return

        # 3. Performance confirmation for full load
        if not self.load_full_file.get():
            if not messagebox.askyesno(l_ui["perf_title"], l_ui["perf_msg"]):
                return

        # 4. Reloading execution
        self.pending_jump_timestamp = timestamp
        self.is_paused.set(True)
        self.filter_vars["all"].set(True)
        for m in ["debug", "info", "warning", "error"]:
            self.filter_vars[m].set(False)
        self.search_query.set("")
        self.load_full_file.set(True)
        self.start_monitoring(self.log_file_path, save=False, retranslate=False)

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

    def get_line_data(self, line):
        if not line or not line.strip():
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
        except:
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
        except:
            return []

    def update_stats(self):
        if not self.log_file_path:
            return
        l = LANGS.get(self.current_lang.get(), LANGS["EN"])
        self.limit_var.set(l["limit"] if not self.load_full_file.get() else "")
        self.paused_var.set(f" | {l['paused']}" if self.is_paused.get() else "")

    def scheduled_stats_update(self):
        if self.running and self.log_file_path:
            size_str, real_total = self.get_file_info()
            l = LANGS.get(self.current_lang.get(), LANGS["EN"])
            self.stats_var.set(l["stats_simple"].format(real_total, size_str))
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
        except:
            pass
        return "N/A", 0

    def trigger_refresh(self, *args):
        self.update_filter_button_colors()
        if self.log_file_path:
            self.start_monitoring(self.log_file_path, save=False, retranslate=False)

    def on_list_selected(self, event):
        self.combo_lists.selection_clear()
        self.root.focus_set()
        self.trigger_refresh()

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

    def update_filter_button_colors(self):
        for mode, cb in self.filter_widgets.items():
            if self.filter_vars[mode].get():
                bg = self.filter_colors[mode]
                cb.config(bg=bg, selectcolor=bg)
            else:
                cb.config(bg=COLOR_BTN_DEFAULT, selectcolor=COLOR_BTN_DEFAULT)

    def retranslate_ui(self, refresh_monitor=True):
        l = LANGS.get(self.current_lang.get(), LANGS["EN"])
        self.btn_log.config(text=l["log"])
        self.btn_sum.config(text=l["sum"])
        self.btn_exp.config(text=l["exp"])
        self.btn_clr.config(text=l["clr"])
        tm = {"all": "all", "debug": "debug", "info": "info", "warning": "warn", "error": "err"}
        for mode, cb in self.filter_widgets.items():
            cb.config(text=l[tm[mode]])
        self.footer_var.set(l["sel"] if not self.log_file_path else f"📍 {self.log_file_path}")
        self.refresh_keyword_list(trigger_monitor=refresh_monitor)
        self.update_stats()
        self.update_filter_button_colors()

        if hasattr(self, 'menu_items'):
            self.menu_items[0].config(text=l["copy"])
            self.menu_items[1].config(text=l["sel_all"])
            self.menu_items[2].config(text=l["search_google"])

    def clear_console(self):
        self.txt_area.config(state=tk.NORMAL)
        self.txt_area.delete('1.0', tk.END)
        self.update_stats()

    def apply_wrap_mode(self):
        self.txt_area.config(wrap=tk.WORD if self.wrap_mode.get() else tk.NONE)

    def toggle_full_load(self):
        self.save_session()
        self.start_monitoring(self.log_file_path, False, False)

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

    def show_loading(self, state):
        if state:
            self.loading_label.config(text=LANGS.get(self.current_lang.get(), LANGS["EN"])["loading"])
            self.overlay.grid(row=0, column=0, sticky="nsew")
            self.root.update_idletasks()
        else:
            self.overlay.grid_forget()

    def change_language(self):
        self.combo_lang.selection_clear()
        self.root.focus_set()
        self.retranslate_ui(True)
        self.save_session()

    def open_file(self):
        p = filedialog.askopenfilename(filetypes=[("Log files", "*.log"), ("All files", "*.*")])
        if p:
            self.start_monitoring(p)

    def show_context_menu(self, event):
        self.txt_area.focus_set()
        self.context_menu.geometry(f"+{event.x_root}+{event.y_root}")
        self.context_menu.deiconify()
        self.context_menu.lift()
        self.context_menu.focus_set()
        self.context_menu.bind("<FocusOut>", lambda e: self.context_menu.withdraw())

    def search_on_google(self):
        try:
            selected_text = self.txt_area.get(tk.SEL_FIRST, tk.SEL_LAST)
            if selected_text.strip():
                url = f"https://www.google.com/search?q={selected_text.strip()}"
                webbrowser.open(url)
        except tk.TclError:
            pass

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
        """
        Extracts and displays the system summary (Kodi start block) in the text area.
        """
        if not self.log_file_path:
            return

        try:
            with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                # Find all Kodi startup sequences in the log
                summaries = list(re.finditer(
                    r"(-+\n.*?Starting Kodi.*?-+\n)",
                    content,
                    re.DOTALL
                ))

                if summaries:
                    # Get the translation for the summary header
                    lang_key = self.current_lang.get()
                    header = LANGS.get(lang_key, LANGS["en"])["sys_sum"]

                    # Insert header and the last (most recent) startup sequence found
                    self.txt_area.insert(tk.END, header, "summary")
                    self.txt_area.insert(tk.END, summaries[-1].group(1), "summary")
                    self.txt_area.see(tk.END)
        except (IOError, OSError, re.error) as e:
            print(f"Error reading summary: {e}")

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
        Saves the current application state and user preferences to a config file.
        """
        try:
            # Build string for filter states (all, debug, info, warning, error)
            modes = ["all", "debug", "info", "warning", "error"]
            filter_states = ",".join(
                ["1" if self.filter_vars[m].get() else "0" for m in modes]
            )

            # Write settings sequentially to the configuration file
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                config_data = [
                    str(self.log_file_path),
                    str(self.current_lang.get()),
                    "1" if self.load_full_file.get() else "0",
                    str(self.font_size),
                    str(self.window_geometry),
                    str(self.selected_list.get()),
                    filter_states
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
                lines = f.read().splitlines()

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
                    modes = ["all", "debug", "info", "warning", "error"]
                    for i, state in enumerate(states):
                        if i < len(modes):
                            self.filter_vars[modes[i]].set(state == "1")

        except (IOError, OSError, Exception) as e:
            # Print error for debugging purposes if needed
            print(f"Error loading configuration: {e}")

        # Finalize UI setup after loading data
        self.retranslate_ui(False)
        self.update_tags_config()

        # Automatically resume monitoring if a valid log file was found
        if self.log_file_path:
            self.start_monitoring(self.log_file_path, False, False)

if __name__ == "__main__":
    # Windows-specific configurations for High DPI and Dark Mode title bar
    if sys.platform == "win32":
        # 1. Enable High DPI awareness to prevent blurry UI on 4K/Laptop screens
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except (ImportError, AttributeError, OSError):
            # Fallback if the system doesn't support Shcore.dll
            pass

    root = tk.Tk()

    # 2. Apply Windows Dark Mode to the title bar (Win 10/11)
    if sys.platform == "win32":
        try:
            from ctypes import windll, byref, sizeof, c_int
            # Attribute 35: DWMWA_USE_IMMERSIVE_DARK_MODE
            # This makes the title bar background dark to match the app theme
            hwnd = windll.user32.GetParent(root.winfo_id())
            dark_mode = c_int(1)
            windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                35,
                byref(dark_mode),
                sizeof(dark_mode)
            )
        except (ImportError, AttributeError, OSError):
            # Fallback if DWMAPI is unavailable or version is incompatible
            pass

    # Initialize and run the application
    app = KodiLogMonitor(root)
    root.mainloop()
