import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import threading
import os
import time
import re
import sys
import locale

# --- CONFIGURATION FACILE ---
APP_VERSION = "v1.0"  # <--- Changez la version ici
CONFIG_FILE = ".kodi_monitor_config"
ICON_NAME = "kodi.ico"
# ----------------------------

LANGS = {
    "FR": {
        "log": "📂 LOG", "sum": "📝 RÉSUMÉ", "exp": "💾 EXPORT",
        "all": "TOUT", "info": "INFO", "warn": "WARN", "err": "ERR",
        "ready": "Prêt", "sel": "Sélectionnez un log.", "sys_sum": "\n--- RÉSUMÉ SYSTÈME ---\n",
        "loading": "Chargement du fichier...\nMerci de patienter."
    },
    "EN": {
        "log": "📂 LOG", "sum": "📝 SUMMARY", "exp": "💾 EXPORT",
        "all": "ALL", "info": "INFO", "warn": "WARN", "err": "ERR",
        "ready": "Ready", "sel": "Select a log.", "sys_sum": "\n--- SYSTEM SUMMARY ---\n",
        "loading": "Loading file...\nPlease wait."
    },
    "ES": {
        "log": "📂 LOG", "sum": "📝 RESUMEN", "exp": "💾 EXPORTAR",
        "all": "TODO", "info": "INFO", "warn": "AVISO", "err": "ERROR",
        "ready": "Listo", "sel": "Seleccione un log.", "sys_sum": "\n--- RESUMEN DEL SISTEMA ---\n",
        "loading": "Cargando archivo...\nEspere por favor."
    },
    "DE": {
        "log": "📂 LOG", "sum": "📝 ÜBERSICHT", "exp": "💾 EXPORT",
        "all": "ALLE", "info": "INFO", "warn": "WARN", "err": "FEHLER",
        "ready": "Bereit", "sel": "Log auswählen.", "sys_sum": "\n--- SYSTEMÜBERSICHT ---\n",
        "loading": "Datei wird geladen...\nBitte warten."
    },
    "ZH": {
        "log": "📂 日志", "sum": "📝 摘要", "exp": "💾 导出",
        "all": "全部", "info": "信息", "warn": "警告", "err": "错误",
        "ready": "就绪", "sel": "选择日志文件。", "sys_sum": "\n--- 系统摘要 ---\n",
        "loading": "正在加载文件...\n请稍候。"
    },
    "RU": {
        "log": "📂 ЛОГ", "sum": "📝 СВОДКА", "exp": "💾 ЭКСПОРТ",
        "all": "ВСЕ", "info": "ИНФО", "warn": "ВНИМ", "err": "ОШИБ",
        "ready": "Готов", "sel": "Выберите лог.", "sys_sum": "\n--- СИСТЕМНАЯ СВОДКА ---\n",
        "loading": "Загрузка файла...\nПожалуйста, подождите."
    },
    "JP": {
        "log": "📂 ログ", "sum": "📝 概要", "exp": "💾 出力",
        "all": "すべて", "info": "情報", "warn": "警告", "err": "エラー",
        "ready": "準備完了", "sel": "ログを選択してください。", "sys_sum": "\n--- システム概要 ---\n",
        "loading": "ファイルを読み込んでいます...\nお待ちください。"
    }
}

class KodiLogMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Kodi Log Monitor {APP_VERSION}") 
        self.root.geometry("1200x850")
        self.root.configure(bg="#1e1e1e")

        self.set_window_icon()
        
        self.log_file_path = ""
        self.running = False
        self.load_full_file = tk.BooleanVar(value=False)
        self.wrap_mode = tk.BooleanVar(value=False)
        self.is_paused = tk.BooleanVar(value=False)
        self.current_lang = tk.StringVar(value=self.detect_os_language())
        self.current_filter_tag = tk.StringVar(value="all")
        self.search_query = tk.StringVar()
        self.font_size = 10
        
        self.filter_colors = {
            "all": "#3c3c3c", "info": "#2d4a2d", "warning": "#856404", "error": "#a31515"
        }
        
        self.current_filter_tag.trace_add("write", self.trigger_refresh)
        self.search_query.trace_add("write", self.trigger_refresh)

        self.setup_ui()
        self.load_session()

    def detect_os_language(self):
        try:
            loc = locale.getdefaultlocale()[0]
            if loc:
                lang_code = loc.split('_')[0].upper()
                mapping = {"FR": "FR", "EN": "EN", "ES": "ES", "DE": "DE", "ZH": "ZH", "RU": "RU", "JA": "JP"}
                return mapping.get(lang_code, "EN")
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

        # HEADER
        header = tk.Frame(self.root, bg="#2d2d2d", padx=10, pady=5)
        header.grid(row=0, column=0, sticky="ew")

        btn_style = {"bg": "#3e3e42", "fg": "white", "relief": "flat", "borderwidth": 0, "font": ("Segoe UI", 9, "bold"), "padx": 12, "cursor": "hand2", "activebackground": "#505050", "activeforeground": "white"}

        left_group = tk.Frame(header, bg="#2d2d2d")
        left_group.pack(side=tk.LEFT, fill=tk.Y)

        self.btn_log = tk.Button(left_group, command=self.open_file, **btn_style)
        self.btn_log.pack(side=tk.LEFT, padx=2)
        
        self.btn_sum = tk.Button(left_group, command=self.show_summary, **btn_style)
        self.btn_sum.pack(side=tk.LEFT, padx=2)
        
        self.btn_exp = tk.Button(left_group, command=self.export_log, **btn_style)
        self.btn_exp.pack(side=tk.LEFT, padx=10)

        tk.Frame(left_group, bg="#444444", width=1).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        self.filter_frame = tk.Frame(left_group, bg="#2d2d2d")
        self.filter_frame.pack(side=tk.LEFT, padx=5)
        self.filter_radios = []
        for mode in ["all", "info", "warning", "error"]:
            rb = tk.Radiobutton(self.filter_frame, variable=self.current_filter_tag, value=mode, indicatoron=0, fg="white", selectcolor="#007acc", font=("Segoe UI", 8, "bold"), relief="flat", borderwidth=0, padx=10, pady=5, cursor="hand2")
            rb.pack(side=tk.LEFT, padx=1)
            self.filter_radios.append((rb, mode))

        search_container = tk.Frame(left_group, bg="#3c3c3c", padx=8)
        search_container.pack(side=tk.LEFT, padx=10)
        tk.Label(search_container, text="🔍", bg="#3c3c3c", fg="#888888").pack(side=tk.LEFT)
        self.search_entry = tk.Entry(search_container, textvariable=self.search_query, bg="#3c3c3c", fg="white", borderwidth=0, width=18, insertbackground="white", font=("Segoe UI", 9))
        self.search_entry.pack(side=tk.LEFT, padx=5, pady=6)
        
        self.btn_full = tk.Checkbutton(left_group, text="∞", variable=self.load_full_file, indicatoron=0, bg="#3e3e42", fg="white", selectcolor="#007acc", relief="flat", borderwidth=0, font=("Segoe UI", 11, "bold"), padx=10, pady=2, command=self.toggle_full_load, cursor="hand2")
        self.btn_full.pack(side=tk.LEFT, padx=2)

        self.btn_wrap = tk.Checkbutton(left_group, text="↵", variable=self.wrap_mode, indicatoron=0, bg="#3e3e42", fg="white", selectcolor="#007acc", relief="flat", borderwidth=0, font=("Segoe UI", 11, "bold"), padx=10, pady=2, command=self.apply_wrap_mode, cursor="hand2")
        self.btn_wrap.pack(side=tk.LEFT, padx=2)

        self.btn_pause = tk.Checkbutton(left_group, text="||", variable=self.is_paused, indicatoron=0, bg="#3e3e42", fg="white", selectcolor="#e81123", relief="flat", borderwidth=0, font=("Segoe UI", 9, "bold"), padx=12, pady=4, cursor="hand2")
        self.btn_pause.pack(side=tk.LEFT, padx=2)

        right_group = tk.Frame(header, bg="#2d2d2d")
        right_group.pack(side=tk.RIGHT, fill=tk.Y)

        self.lang_menu = tk.OptionMenu(right_group, self.current_lang, *LANGS.keys(), command=lambda _: self.change_language())
        self.lang_menu.config(bg="#3e3e42", fg="white", relief="flat", borderwidth=0, font=("Segoe UI", 8, "bold"), width=3, cursor="hand2")
        self.lang_menu["menu"].config(bg="#3e3e42", fg="white", relief="flat", borderwidth=0)
        self.lang_menu.pack(side=tk.LEFT, padx=5)

        for txt, cmd in [("-", self.decrease_font), ("+", self.increase_font)]:
            b = tk.Button(right_group, text=txt, command=cmd, **btn_style)
            b.config(padx=10)
            b.pack(side=tk.LEFT, padx=1)

        self.font_label = tk.Label(right_group, text=str(self.font_size), bg="#2d2d2d", fg="white", width=3, font=("Segoe UI", 9, "bold"))
        self.font_label.pack(side=tk.LEFT)

        # TEXT AREA
        self.main_container = tk.Frame(self.root, bg="#1e1e1e")
        self.main_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        self.txt_area = scrolledtext.ScrolledText(self.main_container, wrap=tk.NONE, bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", self.font_size), borderwidth=0, padx=5, pady=5)
        self.txt_area.grid(row=0, column=0, sticky="nsew")
        
        self.overlay = tk.Frame(self.main_container, bg="#1e1e1e")
        self.loading_label = tk.Label(self.overlay, text="", bg="#1e1e1e", fg="#ffffff", font=("Segoe UI", 12, "bold"))
        self.loading_label.pack(expand=True)

        self.update_tags_config()
        self.update_filter_button_colors()

        # FOOTER
        footer = tk.Frame(self.root, bg="#2d2d2d", padx=15, pady=3)
        footer.grid(row=2, column=0, sticky="ew")
        
        tk.Frame(self.root, bg="#3e3e42", height=1).grid(row=2, column=0, sticky="new")
        
        self.footer_var = tk.StringVar()
        tk.Label(footer, textvariable=self.footer_var, anchor=tk.W, fg="#888888", bg="#2d2d2d", font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT)
        
        # Le label utilise maintenant la variable APP_VERSION définie en haut
        tk.Label(footer, text=f"Kodi Log Monitor {APP_VERSION}", anchor=tk.E, fg="#555555", bg="#2d2d2d", font=("Segoe UI", 8, "italic")).pack(side=tk.RIGHT)

    def apply_wrap_mode(self):
        self.txt_area.config(wrap=tk.WORD if self.wrap_mode.get() else tk.NONE)

    def update_filter_button_colors(self):
        active = self.current_filter_tag.get()
        for rb, mode in self.filter_radios:
            if active == "all": rb.config(bg=self.filter_colors[mode])
            else: rb.config(bg=self.filter_colors[mode] if mode == active else "#3e3e42")

    def trigger_refresh(self, *args):
        self.update_filter_button_colors()
        if self.log_file_path and self.running: self.start_monitoring(self.log_file_path, save=False)

    def toggle_full_load(self):
        self.save_session()
        if self.log_file_path: self.start_monitoring(self.log_file_path, save=False)

    def show_loading(self, state):
        if state:
            l = LANGS[self.current_lang.get()]
            self.loading_label.config(text=l["loading"])
            self.overlay.grid(row=0, column=0, sticky="nsew")
            self.root.update_idletasks()
        else: self.overlay.grid_forget()

    def change_language(self):
        self.retranslate_ui()
        self.save_session()

    def retranslate_ui(self):
        l = LANGS[self.current_lang.get()]
        self.btn_log.config(text=l["log"])
        self.btn_sum.config(text=l["sum"])
        self.btn_exp.config(text=l["exp"])
        map_tags = {"all": "all", "info": "info", "warning": "warn", "error": "err"}
        for rb, mode in self.filter_radios: rb.config(text=l[map_tags[mode]])
        self.footer_var.set(l["sel"] if not self.log_file_path else f"📍 {self.log_file_path}")

    def save_session(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                f.write(f"{self.log_file_path}\n{self.current_lang.get()}\n{'1' if self.load_full_file.get() else '0'}")
        except: pass

    def load_session(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    lines = f.read().splitlines()
                    if len(lines) >= 1 and os.path.exists(lines[0]): self.log_file_path = lines[0]
                    if len(lines) >= 2 and lines[1] in LANGS: self.current_lang.set(lines[1])
                    if len(lines) >= 3: self.load_full_file.set(lines[2] == "1")
            except: pass
        self.retranslate_ui()
        if self.log_file_path: self.start_monitoring(self.log_file_path, save=False)

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("Log files", "*.log"), ("All files", "*.*")])
        if path: self.start_monitoring(path)

    def start_monitoring(self, path, save=True):
        self.running = False
        self.log_file_path = path
        if save: self.save_session()
        self.show_loading(True)
        self.txt_area.delete('1.0', tk.END)
        self.running = True
        threading.Thread(target=self.monitor_loop, daemon=True).start()

    def monitor_loop(self):
        try:
            with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                if self.load_full_file.get(): lines = f.readlines()
                else:
                    f.seek(0, os.SEEK_END)
                    f.seek(max(0, f.tell() - 250000))
                    lines = f.readlines()[-1000:]
                
                to_display = [d for d in (self.get_line_data(l) for l in lines) if d]
                self.root.after(0, self.bulk_insert, to_display)
                
                f.seek(0, os.SEEK_END)
                while self.running:
                    line = f.readline()
                    if not line:
                        time.sleep(0.2)
                        continue
                    data = self.get_line_data(line)
                    if data: self.root.after(0, self.append_to_gui, data[0], data[1])
        except Exception as e:
            self.root.after(0, lambda: [self.show_loading(False), self.footer_var.set(f"⚠ Error: {e}")])

    def get_line_data(self, line):
        low = line.lower()
        tag_f = self.current_filter_tag.get()
        query = self.search_query.get().lower()
        if (tag_f == "all" or f" {tag_f} " in low) and (not query or query in low):
            tag = "error" if " error " in low else "warning" if " warning " in low else "info" if " info " in low else None
            return (line, tag)
        return None

    def bulk_insert(self, data_list):
        self.txt_area.config(state=tk.NORMAL)
        for text, tag in data_list: self.txt_area.insert(tk.END, text, tag)
        if not self.is_paused.get(): self.txt_area.see(tk.END)
        self.show_loading(False)

    def append_to_gui(self, text, tag):
        self.txt_area.insert(tk.END, text, tag)
        if not self.is_paused.get() and self.txt_area.yview()[1] > 0.90: 
            self.txt_area.see(tk.END)

    def update_tags_config(self):
        c_font = ("Consolas", self.font_size)
        for t, c, s in [("info", "#6A9955", "normal"), ("warning", "#DCDCAA", "normal"), ("error", "#F44747", "bold"), ("summary", "#569CD6", "normal")]:
            self.txt_area.tag_config(t, foreground=c, font=(c_font[0], self.font_size, s))
        self.txt_area.configure(font=c_font)
        self.font_label.config(text=str(self.font_size))

    def show_summary(self):
        if not self.log_file_path: return
        l = LANGS[self.current_lang.get()]
        try:
            with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                match = re.search(r"(-+\n.*?Starting Kodi.*?-+\n)", content, re.DOTALL)
                if match:
                    self.txt_area.insert(tk.END, l["sys_sum"], "summary")
                    self.txt_area.insert(tk.END, match.group(1), "summary")
                    self.txt_area.see(tk.END)
        except: pass

    def export_log(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile="kodi_extract.txt")
        if path:
            with open(path, "w", encoding="utf-8") as f: f.write(self.txt_area.get("1.0", tk.END))

    def increase_font(self): self.font_size += 1; self.update_tags_config()
    def decrease_font(self): 
        if self.font_size > 6: self.font_size -= 1; self.update_tags_config()

if __name__ == "__main__":
    root = tk.Tk()
    try:
        from ctypes import windll, byref, sizeof, c_int
        windll.dwmapi.DwmSetWindowAttribute(windll.user32.GetParent(root.winfo_id()), 35, byref(c_int(1)), sizeof(c_int))
    except: pass
    app = KodiLogMonitor(root)
    root.mainloop()