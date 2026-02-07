import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import threading
import os
import time
import re
import sys
import locale

# --- CONFIGURATION ---
APP_VERSION = "v1.1.2" 
CONFIG_FILE = ".kodi_monitor_config"
ICON_NAME = "logo.ico"
# ----------------------------

LANGS = {
    "FR": {
        "log": "📂 LOG", "sum": "📝 RÉSUMÉ", "exp": "💾 EXPORT", "clr": "🗑️ VIDER", "all": "TOUT", "info": "INFO", "warn": "WARNING", "err": "ERROR",
        "ready": "Prêt", "sel": "Sélectionnez un log.", "sys_sum": "\n--- RÉSUMÉ SYSTÈME ---\n", "loading": "Chargement...", "reset": "\n--- FICHIER RÉINITIALISÉ PAR KODI ---\n",
        "stats": " | 📈 {}{} : {} / {} lignes | 📁 {}",
        "stats_simple": " | 📈 TOTAL : {} lignes | 📁 {}"
    },
    "EN": {
        "log": "📂 LOG", "sum": "📝 SUMMARY", "exp": "💾 EXPORT", "clr": "🗑️ CLEAR", "all": "ALL", "info": "INFO", "warn": "WARNING", "err": "ERROR",
        "ready": "Ready", "sel": "Select a log.", "sys_sum": "\n--- SYSTEM SUMMARY ---\n", "loading": "Loading...", "reset": "\n--- FILE RESET BY KODI ---\n",
        "stats": " | 📈 {}{} : {} / {} lines | 📁 {}",
        "stats_simple": " | 📈 TOTAL : {} lines | 📁 {}"
    },
    "DE": {
        "log": "📂 LOG", "sum": "📝 ÜBERSICHT", "exp": "💾 EXPORT", "clr": "LÖSCHEN", "all": "ALLE", "info": "INFO", "warn": "WARNUNG", "err": "FEHLER",
        "ready": "Bereit", "sel": "Log auswählen.", "sys_sum": "\n--- SYSTEMÜBERSICHT ---\n", "loading": "Laden...", "reset": "\n--- DATEI VON KODI ZURÜCKGESETZT ---\n",
        "stats": " | 📈 {}{} : {} / {} zeilen | 📁 {}",
        "stats_simple": " | 📈 TOTAL : {} zeilen | 📁 {}"
    },
    "ES": {
        "log": "📂 LOG", "sum": "📝 RESUMEN", "exp": "💾 EXPORT", "clr": "LIMPIAR", "all": "TODO", "info": "INFO", "warn": "AVISO", "err": "ERROR",
        "ready": "Listo", "sel": "Seleccione un log.", "sys_sum": "\n--- RESUMEN DEL SISTEMA ---\n", "loading": "Cargando...", "reset": "\n--- ARCHIVO REINICIADO POR KODI ---\n",
        "stats": " | 📈 {}{} : {} / {} líneas | 📁 {}",
        "stats_simple": " | 📈 TOTAL : {} líneas | 📁 {}"
    }
}

class KodiLogMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Kodi Log Monitor") 
        self.window_geometry = "1200x850"
        self.root.configure(bg="#1e1e1e")
        self.set_window_icon()
        
        self.log_file_path = ""
        self.running = False
        self.monitor_thread = None
        self.last_sent_line = "" 
        
        self.load_full_file = tk.BooleanVar(value=False)
        self.wrap_mode = tk.BooleanVar(value=False)
        self.is_paused = tk.BooleanVar(value=False)
        self.current_lang = tk.StringVar(value=self.detect_os_language())
        self.current_filter_tag = tk.StringVar(value="all")
        self.search_query = tk.StringVar()
        self.font_size = 10
        
        self.filter_colors = {"all": "#007acc", "info": "#4CAF50", "warning": "#FF9800", "error": "#F44336"}
        self.current_filter_tag.trace_add("write", self.trigger_refresh)
        self.search_query.trace_add("write", self.on_search_change)
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.setup_ui()
        self.load_session()
        self.root.geometry(self.window_geometry)

    def on_closing(self):
        self.window_geometry = self.root.geometry()
        self.save_session()
        self.root.destroy()

    def detect_os_language(self):
        try:
            loc = locale.getlocale()[0] or (locale.getdefaultlocale()[0] if hasattr(locale, 'getdefaultlocale') else None)
            if loc:
                lang_code = loc.split('_')[0].upper()
                return lang_code if lang_code in LANGS else "EN"
        except: pass
        return "EN"

    def set_window_icon(self):
        if getattr(sys, 'frozen', False): base_path = sys._MEIPASS
        else: base_path = os.path.abspath(".")
        icon_path = os.path.join(base_path, ICON_NAME)
        if os.path.exists(icon_path):
            try: self.root.iconbitmap(icon_path)
            except: pass

    def setup_ui(self):
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        header = tk.Frame(self.root, bg="#2d2d2d", padx=10, pady=5); header.grid(row=0, column=0, sticky="ew")
        btn_style = {"bg": "#3e3e42", "fg": "white", "relief": "flat", "borderwidth": 0, "font": ("Segoe UI", 9, "bold"), "padx": 12, "cursor": "hand2", "activebackground": "#505050", "activeforeground": "white"}
        
        left_group = tk.Frame(header, bg="#2d2d2d"); left_group.pack(side=tk.LEFT, fill=tk.Y)
        self.btn_log = tk.Button(left_group, command=self.open_file, **btn_style); self.btn_log.pack(side=tk.LEFT, padx=2)
        self.btn_sum = tk.Button(left_group, command=self.show_summary, **btn_style); self.btn_sum.pack(side=tk.LEFT, padx=2)
        self.btn_exp = tk.Button(left_group, command=self.export_log, **btn_style); self.btn_exp.pack(side=tk.LEFT, padx=2)
        self.btn_clr = tk.Button(left_group, command=self.clear_console, **btn_style); self.btn_clr.pack(side=tk.LEFT, padx=10)
        
        tk.Frame(left_group, bg="#444444", width=1).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        self.filter_frame = tk.Frame(left_group, bg="#2d2d2d"); self.filter_frame.pack(side=tk.LEFT, padx=5)
        self.filter_radios = []
        for mode in ["all", "info", "warning", "error"]:
            rb = tk.Radiobutton(self.filter_frame, variable=self.current_filter_tag, value=mode, indicatoron=0, fg="white", font=("Segoe UI", 8, "bold"), relief="flat", borderwidth=0, padx=10, pady=5, cursor="hand2")
            rb.pack(side=tk.LEFT, padx=1); self.filter_radios.append((rb, mode))
        
        search_container = tk.Frame(left_group, bg="#3c3c3c", padx=8); search_container.pack(side=tk.LEFT, padx=10)
        tk.Label(search_container, text="🔍", bg="#3c3c3c", fg="#888888").pack(side=tk.LEFT)
        self.search_entry = tk.Entry(search_container, textvariable=self.search_query, bg="#3c3c3c", fg="white", borderwidth=0, width=18, insertbackground="white", font=("Segoe UI", 9))
        self.search_entry.pack(side=tk.LEFT, padx=5, pady=6)
        self.btn_clear_search = tk.Button(search_container, text="×", bg="#3c3c3c", fg="#888888", activebackground="#3c3c3c", activeforeground="white", relief="flat", borderwidth=0, font=("Segoe UI", 12, "bold"), cursor="hand2", command=self.clear_search)
        
        self.btn_full = tk.Checkbutton(left_group, text="∞", variable=self.load_full_file, indicatoron=0, bg="#3e3e42", fg="white", selectcolor="#007acc", relief="flat", borderwidth=0, font=("Segoe UI", 11, "bold"), padx=10, pady=2, command=self.toggle_full_load, cursor="hand2"); self.btn_full.pack(side=tk.LEFT, padx=2)
        self.btn_wrap = tk.Checkbutton(left_group, text="↵", variable=self.wrap_mode, indicatoron=0, bg="#3e3e42", fg="white", selectcolor="#007acc", relief="flat", borderwidth=0, font=("Segoe UI", 11, "bold"), padx=10, pady=2, command=self.apply_wrap_mode, cursor="hand2"); self.btn_wrap.pack(side=tk.LEFT, padx=2)
        self.btn_pause = tk.Checkbutton(left_group, text="||", variable=self.is_paused, indicatoron=0, bg="#3e3e42", fg="white", selectcolor="#e81123", relief="flat", borderwidth=0, font=("Segoe UI", 9, "bold"), padx=12, pady=4, cursor="hand2", command=self.toggle_pause_scroll); self.btn_pause.pack(side=tk.LEFT, padx=2)
        
        right_group = tk.Frame(header, bg="#2d2d2d"); right_group.pack(side=tk.RIGHT, fill=tk.Y)
        self.lang_menu = tk.OptionMenu(right_group, self.current_lang, *sorted(LANGS.keys()), command=lambda _: self.change_language())
        self.lang_menu.config(bg="#3e3e42", fg="white", relief="flat", borderwidth=0, font=("Segoe UI", 8, "bold"), width=3, cursor="hand2"); self.lang_menu.pack(side=tk.LEFT, padx=5)
        for txt, cmd in [("-", self.decrease_font), ("+", self.increase_font)]:
            b = tk.Button(right_group, text=txt, command=cmd, **btn_style); b.pack(side=tk.LEFT, padx=1)
        self.font_label = tk.Label(right_group, text=str(self.font_size), bg="#2d2d2d", fg="white", width=3, font=("Segoe UI", 9, "bold")); self.font_label.pack(side=tk.LEFT)
        
        self.main_container = tk.Frame(self.root, bg="#1e1e1e"); self.main_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.main_container.grid_columnconfigure(0, weight=1); self.main_container.grid_rowconfigure(0, weight=1)
        self.txt_area = scrolledtext.ScrolledText(self.main_container, wrap=tk.NONE, bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", self.font_size), borderwidth=0, padx=5, pady=5); self.txt_area.grid(row=0, column=0, sticky="nsew")
        self.overlay = tk.Frame(self.main_container, bg="#1e1e1e")
        self.loading_label = tk.Label(self.overlay, text="", bg="#1e1e1e", fg="#ffffff", font=("Segoe UI", 12, "bold")); self.loading_label.pack(expand=True)
        
        footer = tk.Frame(self.root, bg="#2d2d2d", padx=15, pady=3); footer.grid(row=2, column=0, sticky="ew")
        self.footer_var = tk.StringVar(); self.stats_var = tk.StringVar()
        tk.Label(footer, textvariable=self.footer_var, anchor=tk.W, fg="#ffffff", bg="#2d2d2d", font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT)
        tk.Label(footer, textvariable=self.stats_var, anchor=tk.W, fg="#ffffff", bg="#2d2d2d", font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT)
        tk.Label(footer, text=f"KODI LOG MONITOR {APP_VERSION}", anchor=tk.E, fg="#e0e0e0", bg="#2d2d2d", font=("Segoe UI", 8, "bold"), padx=10).pack(side=tk.RIGHT)
        self.update_filter_button_colors()

    def update_stats(self):
        if not self.log_file_path: self.stats_var.set(""); return
        l = LANGS.get(self.current_lang.get(), LANGS["EN"])
        tag_f = self.current_filter_tag.get()
        query = self.search_query.get()
        size_str, real_total = self.get_file_info()
        
        if tag_f == "all" and not query:
            self.stats_var.set(l["stats_simple"].format(real_total, size_str))
        else:
            lang_key = {"all":"all","info":"info","warning":"warn","error":"err"}.get(tag_f, "all")
            log_type_label = l.get(lang_key, tag_f.upper())
            kw_display = f" + KEYWORD: '{query}'" if query else ""
            content = self.txt_area.get('1.0', 'end-1c')
            display_count = len(content.splitlines()) if content.strip() else 0
            self.stats_var.set(l["stats"].format(log_type_label, kw_display, display_count, real_total, size_str))

    def get_file_info(self):
        if not self.log_file_path or not os.path.exists(self.log_file_path): return "0 KB", 0
        try:
            size_bytes = os.path.getsize(self.log_file_path)
            with open(self.log_file_path, 'rb') as f:
                line_count = sum(1 for _ in f)
            size_str = "0 KB"; temp_size = size_bytes
            for unit in ['B', 'KB', 'MB', 'GB']:
                if temp_size < 1024: size_str = f"{temp_size:.2f} {unit}"; break
                temp_size /= 1024
            return size_str, line_count
        except: return "N/A", 0

    def trigger_refresh(self, *args):
        self.update_filter_button_colors()
        if self.log_file_path: self.start_monitoring(self.log_file_path, save=False)

    def start_monitoring(self, path, save=True):
        self.running = False 
        self.log_file_path = path
        self.last_sent_line = ""
        self.retranslate_ui()
        if save: self.save_session()
        self.txt_area.config(state=tk.NORMAL); self.txt_area.delete('1.0', tk.END)
        self.show_loading(True)
        self.root.after(200, self._launch_thread) 

    def _launch_thread(self):
        self.running = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True); self.monitor_thread.start()

    def monitor_loop(self):
        try:
            with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                if self.load_full_file.get():
                    f.seek(0)
                else:
                    f.seek(0, os.SEEK_END)
                    f.seek(max(0, f.tell() - 250000))
                
                initial_lines = f.readlines()
                if not self.load_full_file.get():
                    initial_lines = initial_lines[-1000:]
                
                if initial_lines:
                    self.last_sent_line = initial_lines[-1].strip()

                to_display = [d for l in initial_lines if (d := self.get_line_data(l))]
                self.root.after(0, self.bulk_insert, to_display)
                
                last_pos = f.tell()

                while self.running:
                    if not os.path.exists(self.log_file_path): break
                    if os.path.getsize(self.log_file_path) < last_pos:
                        self.root.after(0, self.start_monitoring, self.log_file_path, False)
                        return 
                    
                    line = f.readline()
                    if not line:
                        self.root.after(0, self.update_stats)
                        time.sleep(0.5); continue
                    
                    last_pos = f.tell()
                    clean_line = line.strip()
                    
                    if clean_line == self.last_sent_line: continue

                    data = self.get_line_data(line)
                    if data:
                        self.last_sent_line = clean_line
                        self.root.after(0, self.append_to_gui, data[0], data[1])
                    else:
                        self.root.after(0, self.update_stats)
        except:
            self.root.after(0, self.show_loading, False)

    def get_line_data(self, line):
        if not line or line.strip() == "": return None
        low = line.lower(); tag_f = self.current_filter_tag.get(); q = self.search_query.get().lower()
        if (tag_f == "all" or f" {tag_f} " in low) and (not q or q in low):
            tag = "error" if " error " in low else "warning" if " warning " in low else "info" if " info " in low else None
            return (line, tag)
        return None

    def bulk_insert(self, data_list):
        if not self.running: return
        self.txt_area.config(state=tk.NORMAL)
        for text, tag in data_list: self.txt_area.insert(tk.END, text, tag)
        if not self.is_paused.get(): self.txt_area.see(tk.END)
        self.update_stats(); self.show_loading(False)

    def append_to_gui(self, text, tag):
        if not self.running: return
        self.txt_area.insert(tk.END, text, tag)
        if not self.is_paused.get(): self.txt_area.see(tk.END)
        self.update_stats()

    def update_filter_button_colors(self):
        active = self.current_filter_tag.get()
        for rb, mode in self.filter_radios:
            target_bg = self.filter_colors[mode] if active == "all" or active == mode else "#3e3e42"
            rb.config(bg=target_bg, selectcolor=target_bg)

    def retranslate_ui(self):
        l = LANGS.get(self.current_lang.get(), LANGS["EN"])
        self.btn_log.config(text=l["log"]); self.btn_sum.config(text=l["sum"]); self.btn_exp.config(text=l["exp"]); self.btn_clr.config(text=l["clr"])
        tag_m = {"all": "all", "info": "info", "warning": "warn", "error": "err"}
        for rb, mode in self.filter_radios: rb.config(text=l[tag_m[mode]])
        self.footer_var.set(l["sel"] if not self.log_file_path else f"📍 {self.log_file_path}"); self.update_stats()

    def clear_console(self): self.txt_area.config(state=tk.NORMAL); self.txt_area.delete('1.0', tk.END); self.update_stats()
    def apply_wrap_mode(self): self.txt_area.config(wrap=tk.WORD if self.wrap_mode.get() else tk.NONE)
    def toggle_full_load(self): self.save_session(); self.start_monitoring(self.log_file_path, save=False)
    def toggle_pause_scroll(self): 
        if not self.is_paused.get() and self.log_file_path: self.txt_area.see(tk.END)
    def on_search_change(self, *args):
        if self.search_query.get(): self.btn_clear_search.pack(side=tk.LEFT, padx=(0, 2))
        else: self.btn_clear_search.pack_forget()
        self.trigger_refresh()
    def clear_search(self): self.search_query.set(""); self.search_entry.focus()
    def show_loading(self, state):
        if state:
            l = LANGS.get(self.current_lang.get(), LANGS["EN"])
            self.loading_label.config(text=l["loading"]); self.overlay.grid(row=0, column=0, sticky="nsew"); self.root.update_idletasks()
        else: self.overlay.grid_forget()
    def change_language(self): self.retranslate_ui(); self.save_session()
    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("Log files", "*.log"), ("All files", "*.*")])
        if path: self.start_monitoring(path)
    def update_tags_config(self):
        c_font = ("Consolas", self.font_size)
        for t, c in [("info", "#4CAF50"), ("warning", "#FF9800"), ("error", "#F44336"), ("summary", "#00E5FF")]:
            self.txt_area.tag_config(t, foreground=c, font=(c_font[0], self.font_size))
        self.txt_area.configure(font=c_font); self.font_label.config(text=str(self.font_size))
    def increase_font(self): self.font_size += 1; self.update_tags_config(); self.save_session()
    def decrease_font(self): 
        if self.font_size > 6: self.font_size -= 1; self.update_tags_config(); self.save_session()
    def show_summary(self):
        if not self.log_file_path: return
        l = LANGS.get(self.current_lang.get(), LANGS["EN"])
        try:
            with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(); starts = list(re.finditer(r"(-+\n.*?Starting Kodi.*?-+\n)", content, re.DOTALL))
                if starts:
                    self.txt_area.insert(tk.END, l["sys_sum"], "summary")
                    self.txt_area.insert(tk.END, starts[-1].group(1), "summary"); self.txt_area.see(tk.END)
        except: pass
    def export_log(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile="kodi_extract.txt")
        if path:
            with open(path, "w", encoding="utf-8") as f: f.write(self.txt_area.get("1.0", tk.END))
    def save_session(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                f.write(f"{self.log_file_path}\n{self.current_lang.get()}\n{'1' if self.load_full_file.get() else '0'}\n{self.font_size}\n{self.window_geometry}")
        except: pass
    def load_session(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    lines = f.read().splitlines()
                    if len(lines) >= 1 and os.path.exists(lines[0]): self.log_file_path = lines[0]
                    if len(lines) >= 2 and lines[1] in LANGS: self.current_lang.set(lines[1])
                    if len(lines) >= 3: self.load_full_file.set(lines[2] == "1")
                    if len(lines) >= 4: self.font_size = int(lines[3])
                    if len(lines) >= 5: self.window_geometry = lines[4]
            except: pass
        self.retranslate_ui(); self.update_tags_config()
        if self.log_file_path: self.start_monitoring(self.log_file_path, save=False)

if __name__ == "__main__":
    root = tk.Tk()
    try:
        from ctypes import windll, byref, sizeof, c_int
        windll.dwmapi.DwmSetWindowAttribute(windll.user32.GetParent(root.winfo_id()), 35, byref(c_int(1)), sizeof(c_int))
    except: pass
    app = KodiLogMonitor(root); root.mainloop()