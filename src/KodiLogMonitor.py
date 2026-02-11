import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk
import threading
import os
import time
import re
import sys
import locale
import subprocess
from collections import deque

# --- CONFIGURATION ---
APP_VERSION = "v1.2.1" 
CONFIG_FILE = ".kodi_monitor_config"
ICON_NAME = "logo.ico"
KEYWORD_DIR = "keyword_lists"

# --- UI THEME ---
COLOR_BG_MAIN = "#1e1e1e"        
COLOR_BG_HEADER = "#2d2d2d"      
COLOR_BG_SUBHEADER = "#333333"   
COLOR_BG_FOOTER = "#2d2d2d"      
COLOR_BTN_DEFAULT = "#3e3e42"    
COLOR_BTN_ACTIVE = "#505050"     
COLOR_ACCENT = "#007acc"         
COLOR_DANGER = "#e81123"         

LOG_COLORS = {
    "info": "#4CAF50",           
    "warning": "#FF9800",        
    "error": "#F44336",          
    "summary": "#00E5FF",        
    "highlight_bg": "#FFF176",   
    "highlight_fg": "#000000"    
}

if not os.path.exists(KEYWORD_DIR):
    os.makedirs(KEYWORD_DIR)

LANGS = {
    "FR": {
        "log": "📂  LOG", "sum": "📝  RÉSUMÉ", "exp": "💾  EXPORT", "clr": "🗑️  VIDER", "all": "TOUT", "info": "INFO", "warn": "WARNING", "err": "ERROR",
        "ready": "Prêt", "sel": "Sélectionnez un log.", "sys_sum": "\n--- RÉSUMÉ SYSTÈME ---\n", "loading": "Chargement...", "reset": "\n--- FICHIER RÉINITIALISÉ PAR KODI ---\n",
        "stats": " | 📈 {}{} : {} / {} lignes | 📁 {}", "stats_simple": " | 📈 TOTAL : {} lignes | 📁 {}", "limit": " | ⚠️ LIMITÉ AUX 1000 DERNIÈRES LIGNES", "none": "Aucun",
        "paused": "⏸️ EN PAUSE"
    },
    "EN": {
        "log": "📂  LOG", "sum": "📝  SUMMARY", "exp": "💾  EXPORT", "clr": "CLEAR", "all": "ALL", "info": "INFO", "warn": "WARNING", "err": "ERROR",
        "ready": "Ready", "sel": "Select a log.", "sys_sum": "\n--- SYSTEM SUMMARY ---\n", "loading": "Loading...", "reset": "\n--- FILE RESET BY KODI ---\n",
        "stats": " | 📈 {}{} : {} / {} lines | 📁 {}", "stats_simple": " | 📈 TOTAL : {} lines | 📁 {}", "limit": " | ⚠️ LIMITED TO LAST 1000 LINES", "none": "None",
        "paused": "⏸️ PAUSED"
    },
    "ES": {
        "log": "📂  LOG", "sum": "📝  RESUMEN", "exp": "💾  EXPORTAR", "clr": "LIMPIAR", "all": "TODO", "info": "INFO", "warn": "AVISO", "err": "ERROR",
        "ready": "Listo", "sel": "Seleccione un log.", "sys_sum": "\n--- RESUMEN DEL SISTEMA ---\n", "loading": "Cargando...", "reset": "\n--- ARCHIVO REINICIADO POR KODI ---\n",
        "stats": " | 📈 {}{} : {} / {} líneas | 📁 {}", "stats_simple": " | 📈 TOTAL : {} líneas | 📁 {}", "limit": " | ⚠️ LIMITADO A LAS ULTIMAS 1000 LÍNEAS", "none": "Ninguno",
        "paused": "⏸️ EN PAUSA"
    },
    "DE": {
        "log": "📂  LOG", "sum": "📝  REZUMAT", "exp": "💾  EXPORT", "clr": "LEEREN", "all": "ALLES", "info": "INFO", "warn": "WARNUNG", "err": "FEHLER",
        "ready": "Bereit", "sel": "Log auswählen.", "sys_sum": "\n--- SYSTEMZUSAMMENFASSUNG ---\n", "loading": "Laden...", "reset": "\n--- DATEI VON KODI ZURÜCKGESETZT ---\n",
        "stats": " | 📈 {}{} : {} / {} Zeilen | 📁 {}", "stats_simple": " | 📈 GESAMT : {} Zeilen | 📁 {}", "limit": " | ⚠️ BEGRENZT AUF DIE LETZTEN 1000 ZEILEN", "none": "Keiner",
        "paused": "⏸️ PAUSE"
    },
    "IT": {
        "log": "📂  LOG", "sum": "📝  SOMMARIO", "exp": "💾  ESPORTA", "clr": "PULISCI", "all": "TUTTO", "info": "INFO", "warn": "AVVISO", "err": "ERRORE",
        "ready": "Pronto", "sel": "Seleziona un log.", "sys_sum": "\n--- SOMMARIO DI SISTEMA ---\n", "loading": "Caricamento...", "reset": "\n--- FILE REINIZIALIZZATO DA KODI ---\n",
        "stats": " | 📈 {}{} : {} / {} righe | 📁 {}", "stats_simple": " | 📈 TOTALE : {} righe | 📁 {}", "limit": " | ⚠️ LIMITATO ALLE ULTIME 1000 RIGHE", "none": "Nessuno",
        "paused": "⏸️ IN PAUSA"
    }
}

class KodiLogMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Kodi Log Monitor") 
        self.window_geometry = "1200x850"
        self.root.configure(bg=COLOR_BG_MAIN)
        self.set_window_icon()
        
        self.log_file_path = ""
        self.running = False
        self.monitor_thread = None
        self.seen_lines = deque(maxlen=150) 
        
        self.load_full_file = tk.BooleanVar(value=False)
        self.wrap_mode = tk.BooleanVar(value=False)
        self.is_paused = tk.BooleanVar(value=False)
        self.current_lang = tk.StringVar(value=self.detect_os_language())
        self.current_filter_tag = tk.StringVar(value="all")
        self.search_query = tk.StringVar()
        self.selected_list = tk.StringVar()
        self.font_size = 10
        
        self.filter_colors = {"all": COLOR_ACCENT, "info": LOG_COLORS["info"], "warning": LOG_COLORS["warning"], "error": LOG_COLORS["error"]}
        
        self.setup_ui()
        self.load_session()
        self.root.geometry(self.window_geometry)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.current_filter_tag.trace_add("write", self.trigger_refresh)
        self.search_query.trace_add("write", self.on_search_change)

    def on_closing(self):
        self.running = False
        self.window_geometry = self.root.geometry()
        self.save_session()
        self.root.destroy()

    def is_duplicate(self, text):
        clean_text = text.strip()
        if not clean_text: return False
        if clean_text in self.seen_lines: return True
        self.seen_lines.append(clean_text)
        return False

    def monitor_loop(self):
        try:
            with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                if self.load_full_file.get(): f.seek(0)
                else:
                    f.seek(0, os.SEEK_END)
                    f.seek(max(0, f.tell() - 250000))
                
                initial_lines = f.readlines()
                if not self.load_full_file.get(): initial_lines = initial_lines[-1000:]
                last_pos = f.tell()
                
                to_display = []
                for line in initial_lines:
                    data = self.get_line_data(line)
                    if data and not self.is_duplicate(data[0]): to_display.append(data)
                self.root.after(0, self.bulk_insert, to_display)

                while self.running:
                    if not os.path.exists(self.log_file_path): break
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
        if not self.running: return
        self.txt_area.config(state=tk.NORMAL)
        for text, tag in data_list: self.insert_with_highlight(text, tag)
        if not self.is_paused.get(): self.txt_area.see(tk.END)
        self.update_stats(); self.show_loading(False)

    def append_to_gui(self, text, tag):
        if not self.running: return
        self.txt_area.config(state=tk.NORMAL)
        self.insert_with_highlight(text, tag)
        if not self.is_paused.get(): self.txt_area.see(tk.END)
        self.update_stats()

    def start_monitoring(self, path, save=True, retranslate=True):
        self.running = False
        self.seen_lines.clear()
        self.log_file_path = path
        if retranslate: self.retranslate_ui(refresh_monitor=False)
        if save: self.save_session()
        self.txt_area.config(state=tk.NORMAL); self.txt_area.delete('1.0', tk.END)
        self.show_loading(True); self.root.after(150, self._launch_thread) 

    def _launch_thread(self):
        self.running = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True); self.monitor_thread.start()

    # --- UI SETUP ---
    def setup_ui(self):
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(2, weight=1)
        btn_style = {"bg": COLOR_BTN_DEFAULT, "fg": "white", "relief": "flat", "borderwidth": 0, "font": ("Segoe UI", 9, "bold"), "padx": 12, "pady": 3, "cursor": "hand2", "activebackground": COLOR_BTN_ACTIVE, "activeforeground": "white"}
        
        header = tk.Frame(self.root, bg=COLOR_BG_HEADER, padx=10, pady=5)
        header.grid(row=0, column=0, sticky="ew")
        
        h_left = tk.Frame(header, bg=COLOR_BG_HEADER)
        h_left.pack(side=tk.LEFT, fill=tk.Y)
        self.btn_log = tk.Button(h_left, command=self.open_file, **btn_style); self.btn_log.pack(side=tk.LEFT, padx=2)
        self.btn_sum = tk.Button(h_left, command=self.show_summary, **btn_style); self.btn_sum.pack(side=tk.LEFT, padx=2)
        self.btn_exp = tk.Button(h_left, command=self.export_log, **btn_style); self.btn_exp.pack(side=tk.LEFT, padx=2)
        self.btn_clr = tk.Button(h_left, command=self.clear_console, **btn_style); self.btn_clr.pack(side=tk.LEFT, padx=10)
        
        tk.Frame(h_left, bg="#444444", width=1).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        self.filter_frame = tk.Frame(h_left, bg=COLOR_BG_HEADER); self.filter_frame.pack(side=tk.LEFT, padx=5)
        self.filter_radios = []
        for mode in ["all", "info", "warning", "error"]:
            rb = tk.Radiobutton(self.filter_frame, variable=self.current_filter_tag, value=mode, indicatoron=0, fg="white", font=("Segoe UI", 8, "bold"), relief="flat", borderwidth=0, padx=10, pady=5, cursor="hand2")
            rb.pack(side=tk.LEFT, padx=1); self.filter_radios.append((rb, mode))

        h_right = tk.Frame(header, bg=COLOR_BG_HEADER)
        h_right.pack(side=tk.RIGHT, fill=tk.Y)
        self.lang_menu = tk.OptionMenu(h_right, self.current_lang, *sorted(LANGS.keys()), command=lambda _: self.change_language())
        self.lang_menu.config(bg=COLOR_BTN_DEFAULT, fg="white", relief="flat", borderwidth=0, font=("Segoe UI", 8, "bold"), width=4, cursor="hand2"); self.lang_menu.pack(side=tk.LEFT, padx=5)

        sub_header = tk.Frame(self.root, bg=COLOR_BG_SUBHEADER, padx=10, pady=4)
        sub_header.grid(row=1, column=0, sticky="ew")

        sh_left = tk.Frame(sub_header, bg=COLOR_BG_SUBHEADER); sh_left.pack(side=tk.LEFT, fill=tk.Y)
        kw_box = tk.Frame(sh_left, bg=COLOR_BG_SUBHEADER); kw_box.pack(side=tk.LEFT)
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TCombobox", fieldbackground=COLOR_BTN_DEFAULT, background=COLOR_BTN_DEFAULT, foreground="white", bordercolor=COLOR_BG_SUBHEADER, arrowcolor="white")
        style.map("TCombobox", fieldbackground=[("readonly", COLOR_BTN_DEFAULT)], background=[("readonly", COLOR_BTN_DEFAULT)])
        self.root.option_add("*TCombobox*Listbox.background", COLOR_BTN_DEFAULT)
        self.root.option_add("*TCombobox*Listbox.foreground", "white")
        self.root.option_add("*TCombobox*Listbox.selectBackground", COLOR_ACCENT)

        self.combo_lists = ttk.Combobox(kw_box, textvariable=self.selected_list, state="readonly", width=18, style="TCombobox")
        self.combo_lists.pack(side=tk.LEFT, padx=2); self.combo_lists.bind("<<ComboboxSelected>>", self.on_list_selected)
        
        btn_tool_style = {"bg": "#454545", "fg": "white", "relief": "flat", "borderwidth": 0, "font": ("Segoe UI", 9), "padx": 8, "pady": 2, "cursor": "hand2"}
        tk.Button(kw_box, text="♻️", command=self.refresh_keyword_lists, **btn_tool_style).pack(side=tk.LEFT, padx=1)
        tk.Button(kw_box, text="📁", command=self.open_keyword_folder, **btn_tool_style).pack(side=tk.LEFT, padx=1)

        search_box = tk.Frame(sh_left, bg=COLOR_BG_MAIN, padx=8); search_box.pack(side=tk.LEFT, padx=15)
        tk.Label(search_box, text="🔍", bg=COLOR_BG_MAIN, fg="#888888").pack(side=tk.LEFT)
        self.search_entry = tk.Entry(search_box, textvariable=self.search_query, bg=COLOR_BG_MAIN, fg="white", borderwidth=0, width=22, insertbackground="white", font=("Segoe UI", 9))
        self.search_entry.pack(side=tk.LEFT, padx=5, pady=4)
        self.btn_clear_search = tk.Button(search_box, text="×", bg=COLOR_BG_MAIN, fg="#888888", relief="flat", font=("Segoe UI", 11, "bold"), command=self.clear_search)

        opt_box = tk.Frame(sh_left, bg=COLOR_BG_SUBHEADER); opt_box.pack(side=tk.LEFT)
        tk.Checkbutton(opt_box, text="∞", variable=self.load_full_file, indicatoron=0, bg=COLOR_BTN_DEFAULT, fg="white", selectcolor=COLOR_ACCENT, relief="flat", font=("Segoe UI", 10, "bold"), padx=10, pady=2, command=self.toggle_full_load).pack(side=tk.LEFT, padx=2)
        tk.Checkbutton(opt_box, text="↵", variable=self.wrap_mode, indicatoron=0, bg=COLOR_BTN_DEFAULT, fg="white", selectcolor=COLOR_ACCENT, relief="flat", font=("Segoe UI", 10, "bold"), padx=10, pady=2, command=self.apply_wrap_mode).pack(side=tk.LEFT, padx=2)
        tk.Checkbutton(opt_box, text="||", variable=self.is_paused, indicatoron=0, bg=COLOR_BTN_DEFAULT, fg="white", selectcolor=COLOR_DANGER, relief="flat", font=("Segoe UI", 8, "bold"), padx=12, pady=3, command=self.toggle_pause_scroll).pack(side=tk.LEFT, padx=2)
        tk.Button(opt_box, text="🔄  RESET", command=self.reset_all_filters, bg=COLOR_BTN_DEFAULT, fg="#FF9800", relief="flat", font=("Segoe UI", 8, "bold"), padx=10, pady=3).pack(side=tk.LEFT, padx=2)

        sh_right = tk.Frame(sub_header, bg=COLOR_BG_SUBHEADER); sh_right.pack(side=tk.RIGHT, fill=tk.Y)
        tk.Button(sh_right, text="-", command=self.decrease_font, **btn_style).pack(side=tk.LEFT, padx=1)
        tk.Button(sh_right, text="+", command=self.increase_font, **btn_style).pack(side=tk.LEFT, padx=1)
        self.font_label = tk.Label(sh_right, text=str(self.font_size), bg=COLOR_BG_SUBHEADER, fg="white", width=3, font=("Segoe UI", 9, "bold")); self.font_label.pack(side=tk.LEFT)

        self.main_container = tk.Frame(self.root, bg=COLOR_BG_MAIN); self.main_container.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.main_container.grid_columnconfigure(0, weight=1); self.main_container.grid_rowconfigure(0, weight=1)
        self.txt_area = scrolledtext.ScrolledText(self.main_container, wrap=tk.NONE, bg=COLOR_BG_MAIN, fg="#d4d4d4", font=("Consolas", self.font_size), borderwidth=0, padx=5, pady=5); self.txt_area.grid(row=0, column=0, sticky="nsew")
        self.overlay = tk.Frame(self.main_container, bg=COLOR_BG_MAIN)
        self.loading_label = tk.Label(self.overlay, text="", bg=COLOR_BG_MAIN, fg="#ffffff", font=("Segoe UI", 12, "bold")); self.loading_label.pack(expand=True)
        
        footer = tk.Frame(self.root, bg=COLOR_BG_FOOTER, padx=15, pady=3); footer.grid(row=3, column=0, sticky="ew")
        self.footer_var = tk.StringVar(); self.stats_var = tk.StringVar(); self.limit_var = tk.StringVar(); self.paused_var = tk.StringVar()
        tk.Label(footer, textvariable=self.footer_var, anchor=tk.W, fg="#ffffff", bg=COLOR_BG_FOOTER, font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT)
        tk.Label(footer, textvariable=self.stats_var, anchor=tk.W, fg="#ffffff", bg=COLOR_BG_FOOTER, font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT)
        tk.Label(footer, textvariable=self.limit_var, anchor=tk.W, fg="#FF9800", bg=COLOR_BG_FOOTER, font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT)
        tk.Label(footer, textvariable=self.paused_var, anchor=tk.W, fg=COLOR_DANGER, bg=COLOR_BG_FOOTER, font=("Segoe UI", 8, "bold"), padx=10).pack(side=tk.LEFT)
        tk.Label(footer, text=f"KODI LOG MONITOR {APP_VERSION}", anchor=tk.E, fg="#e0e0e0", bg=COLOR_BG_FOOTER, font=("Segoe UI", 8, "bold"), padx=10).pack(side=tk.RIGHT)

    def detect_os_language(self):
        try:
            loc = locale.getlocale()[0] or (locale.getdefaultlocale()[0] if hasattr(locale, 'getdefaultlocale') else None)
            if loc: return loc.split('_')[0].upper() if loc.split('_')[0].upper() in LANGS else "EN"
        except: pass
        return "EN"

    def set_window_icon(self):
        if getattr(sys, 'frozen', False): base_path = sys._MEIPASS
        else: base_path = os.path.abspath(".")
        icon_path = os.path.join(base_path, ICON_NAME)
        if os.path.exists(icon_path):
            try: self.root.iconbitmap(icon_path)
            except: pass

    def update_tags_config(self):
        c_font = ("Consolas", self.font_size)
        for t in ["info", "warning", "error", "summary"]: self.txt_area.tag_config(t, foreground=LOG_COLORS[t], font=(c_font[0], self.font_size))
        self.txt_area.tag_config("highlight", background=LOG_COLORS["highlight_bg"], foreground=LOG_COLORS["highlight_fg"], font=(c_font[0], self.font_size))
        self.txt_area.configure(bg=COLOR_BG_MAIN, font=c_font); self.font_label.config(text=str(self.font_size))

    def reset_all_filters(self):
        l = LANGS.get(self.current_lang.get(), LANGS["EN"])
        self.current_filter_tag.set("all"); self.search_query.set(""); self.selected_list.set(l["none"]); self.is_paused.set(False); self.toggle_pause_scroll(); self.trigger_refresh()

    def get_line_data(self, line):
        low = line.lower(); tag_f = self.current_filter_tag.get(); q = self.search_query.get().lower()
        if not (tag_f == "all" or f" {tag_f} " in low): return None
        if q and q not in low: return None
        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])
        if self.selected_list.get() != l_ui["none"]:
            kw = self.get_keywords_from_file()
            if kw and not any(k.lower() in low for k in kw): return None
        tag = "error" if " error " in low else "warning" if " warning " in low else "info" if " info " in low else None
        return (line, tag)

    def insert_with_highlight(self, text, base_tag):
        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])
        if self.selected_list.get() == l_ui["none"]: self.txt_area.insert(tk.END, text, base_tag); return
        kw = self.get_keywords_from_file()
        if not kw: self.txt_area.insert(tk.END, text, base_tag); return
        matches = list(re.finditer("|".join(re.escape(k) for k in kw), text, re.IGNORECASE))
        if not matches: self.txt_area.insert(tk.END, text, base_tag); return
        last_idx = 0
        for m in matches:
            self.txt_area.insert(tk.END, text[last_idx:m.start()], base_tag)
            self.txt_area.insert(tk.END, text[m.start():m.end()], (base_tag, "highlight"))
            last_idx = m.end()
        self.txt_area.insert(tk.END, text[last_idx:], base_tag)

    def get_keywords_from_file(self):
        l_ui = LANGS.get(self.current_lang.get(), LANGS["EN"])
        if self.selected_list.get() == l_ui["none"]: return []
        path = os.path.join(KEYWORD_DIR, f"{self.selected_list.get()}.txt")
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f: return [line.strip() for line in f if line.strip()]
        except: return []

    def update_stats(self):
        if not self.log_file_path: return
        l = LANGS.get(self.current_lang.get(), LANGS["EN"])
        size_str, real_total = self.get_file_info()
        self.limit_var.set(l["limit"] if not self.load_full_file.get() else "")
        content = self.txt_area.get('1.0', 'end-1c')
        display_count = len(content.splitlines()) if content.strip() else 0
        tag = self.current_filter_tag.get()
        if tag == "all" and not self.search_query.get() and self.selected_list.get() == l["none"]:
            self.stats_var.set(l["stats_simple"].format(real_total, size_str))
        else:
            label = l.get({"all":"all","info":"info","warning":"warn","error":"err"}.get(tag), tag.upper())
            kw = f" + SEARCH: '{self.search_query.get()}'" if self.search_query.get() else ""
            lst = f" + LIST: '{self.selected_list.get()}'" if self.selected_list.get() != l["none"] else ""
            self.stats_var.set(l["stats"].format(label, kw+lst, display_count, real_total, size_str))
        self.paused_var.set(f" | {l['paused']}" if self.is_paused.get() else "")

    def get_file_info(self):
        if not self.log_file_path or not os.path.exists(self.log_file_path): return "0 KB", 0
        try:
            size_bytes = os.path.getsize(self.log_file_path); f_obj = open(self.log_file_path, 'rb')
            line_count = sum(1 for _ in f_obj); f_obj.close()
            temp_size = size_bytes
            for unit in ['B', 'KB', 'MB', 'GB']:
                if temp_size < 1024: return f"{temp_size:.2f} {unit}", line_count
                temp_size /= 1024
        except: pass
        return "N/A", 0

    def trigger_refresh(self, *args):
        self.update_filter_button_colors()
        if self.log_file_path: self.start_monitoring(self.log_file_path, save=False, retranslate=False)

    def on_list_selected(self, event): self.combo_lists.selection_clear(); self.root.focus_set(); self.trigger_refresh()
    def open_keyword_folder(self):
        abs_path = os.path.abspath(KEYWORD_DIR)
        if sys.platform == 'win32': os.startfile(abs_path)
        else: subprocess.Popen(['open' if sys.platform == 'darwin' else 'xdg-open', abs_path])

    def refresh_keyword_lists(self, trigger_monitor=True):
        l = LANGS.get(self.current_lang.get(), LANGS["EN"])
        files = [f.replace(".txt", "") for f in os.listdir(KEYWORD_DIR) if f.endswith(".txt")]
        self.combo_lists['values'] = [l["none"]] + sorted(files)
        if self.selected_list.get() not in self.combo_lists['values']: self.selected_list.set(l["none"])
        if trigger_monitor: self.trigger_refresh()

    def update_filter_button_colors(self):
        active = self.current_filter_tag.get()
        for rb, mode in self.filter_radios:
            bg = self.filter_colors[mode] if active in ["all", mode] else COLOR_BTN_DEFAULT
            rb.config(bg=bg, selectcolor=bg)

    def retranslate_ui(self, refresh_monitor=True):
        l = LANGS.get(self.current_lang.get(), LANGS["EN"])
        self.btn_log.config(text=l["log"]); self.btn_sum.config(text=l["sum"]); self.btn_exp.config(text=l["exp"]); self.btn_clr.config(text=l["clr"])
        tm = {"all": "all", "info": "info", "warning": "warn", "error": "err"}
        for rb, mode in self.filter_radios: rb.config(text=l[tm[mode]])
        self.footer_var.set(l["sel"] if not self.log_file_path else f"📍 {self.log_file_path}")
        self.refresh_keyword_lists(trigger_monitor=refresh_monitor)
        self.update_stats(); self.update_filter_button_colors()

    def clear_console(self): self.txt_area.config(state=tk.NORMAL); self.txt_area.delete('1.0', tk.END); self.update_stats()
    def apply_wrap_mode(self): self.txt_area.config(wrap=tk.WORD if self.wrap_mode.get() else tk.NONE)
    def toggle_full_load(self): self.save_session(); self.start_monitoring(self.log_file_path, False, False)
    def toggle_pause_scroll(self): 
        if not self.is_paused.get() and self.log_file_path: self.txt_area.see(tk.END)
        self.update_stats()
    def on_search_change(self, *args):
        if self.search_query.get(): self.btn_clear_search.pack(side=tk.LEFT, padx=(0, 2))
        else: self.btn_clear_search.pack_forget()
        self.trigger_refresh()
    def clear_search(self): self.search_query.set(""); self.search_entry.focus()
    def show_loading(self, state):
        if state: self.loading_label.config(text=LANGS.get(self.current_lang.get(), LANGS["EN"])["loading"]); self.overlay.grid(row=0, column=0, sticky="nsew"); self.root.update_idletasks()
        else: self.overlay.grid_forget()
    def change_language(self): self.retranslate_ui(True); self.save_session()
    def open_file(self):
        p = filedialog.askopenfilename(filetypes=[("Log files", "*.log"), ("All files", "*.*")])
        if p: self.start_monitoring(p)
    def increase_font(self): self.font_size += 1; self.update_tags_config(); self.save_session()
    def decrease_font(self): 
        if self.font_size > 6: self.font_size -= 1; self.update_tags_config(); self.save_session()
    def show_summary(self):
        if not self.log_file_path: return
        try:
            with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                c = f.read(); s = list(re.finditer(r"(-+\n.*?Starting Kodi.*?-+\n)", c, re.DOTALL))
                if s: self.txt_area.insert(tk.END, LANGS.get(self.current_lang.get(), LANGS["EN"])["sys_sum"], "summary"); self.txt_area.insert(tk.END, s[-1].group(1), "summary"); self.txt_area.see(tk.END)
        except: pass
    def export_log(self):
        p = filedialog.asksaveasfilename(defaultextension=".txt", initialfile="kodi_extract.txt")
        if p:
            with open(p, "w", encoding="utf-8") as f: f.write(self.txt_area.get("1.0", tk.END))
    def save_session(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f: f.write(f"{self.log_file_path}\n{self.current_lang.get()}\n{'1' if self.load_full_file.get() else '0'}\n{self.font_size}\n{self.window_geometry}\n{self.selected_list.get()}")
        except: pass
    def load_session(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    ls = f.read().splitlines()
                    if len(ls) >= 1 and os.path.exists(ls[0]): self.log_file_path = ls[0]
                    if len(ls) >= 2 and ls[1] in LANGS: self.current_lang.set(ls[1])
                    if len(ls) >= 3: self.load_full_file.set(ls[2] == "1")
                    if len(ls) >= 4: self.font_size = int(ls[3])
                    if len(ls) >= 5: self.window_geometry = ls[4]
                    if len(ls) >= 6: self.selected_list.set(ls[5] if ls[5] not in [v["none"] for v in LANGS.values()] else LANGS[self.current_lang.get()]["none"])
            except: pass
        self.retranslate_ui(False); self.update_tags_config()
        if self.log_file_path: self.start_monitoring(self.log_file_path, False, False)

if __name__ == "__main__":
    root = tk.Tk()
    try:
        from ctypes import windll, byref, sizeof, c_int
        windll.dwmapi.DwmSetWindowAttribute(windll.user32.GetParent(root.winfo_id()), 35, byref(c_int(1)), sizeof(c_int))
    except: pass
    app = KodiLogMonitor(root); root.mainloop()