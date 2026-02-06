import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import threading
import os
import time
import re
import sys
import locale

# --- CONFIGURATION ---
APP_VERSION = "v1.1.3" 
CONFIG_FILE = ".kodi_monitor_config"
ICON_NAME = "logo.ico"
# ----------------------------

LANGS = {
    "FR": {
        "log": "📂 LOG", "sum": "📝 RÉSUMÉ", "exp": "💾 EXPORT", "clr": "🗑️", "all": "TOUT", "info": "INFO", "warn": "WARN", "err": "ERR",
        "ready": "Prêt", "sel": "Sélectionnez un log.", "sys_sum": "\n--- RÉSUMÉ SYSTÈME ---\n", "loading": "Chargement...", "reset": "\n--- FICHIER RÉINITIALISÉ PAR KODI ---\n",
        "stats": " | 📈 Filtre: {} / Total: {} | 📁 Taille: {}"
    },
    "EN": {
        "log": "📂 LOG", "sum": "📝 SUMMARY", "exp": "💾 EXPORT", "clr": "🗑️", "all": "ALL", "info": "INFO", "warn": "WARN", "err": "ERR",
        "ready": "Ready", "sel": "Select a log.", "sys_sum": "\n--- SYSTEM SUMMARY ---\n", "loading": "Loading...", "reset": "\n--- FILE RESET BY KODI ---\n",
        "stats": " | 📈 Filtered: {} / Total: {} | 📁 Size: {}"
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
        self.total_lines = 0
        self.filtered_lines_count = 0
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
        
        self.setup_ui()
        self.load_session()

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
        self.btn_pause = tk.Checkbutton(left_group, text="||", variable=self.is_paused, indicatoron=0, bg="#3e3e42", fg="white", selectcolor="#e81123", relief="flat", borderwidth=0, font=("Segoe UI", 9, "bold"), padx=12, pady=4, cursor="hand2"); self.btn_pause.pack(side=tk.LEFT, padx=2)
        
        right_group = tk.Frame(header, bg="#2d2d2d"); right_group.pack(side=tk.RIGHT, fill=tk.Y)
        self.lang_menu = tk.OptionMenu(right_group, self.current_lang, *LANGS.keys(), command=lambda _: self.change_language())
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
        self.footer_var = tk.StringVar()
        self.stats_var = tk.StringVar()
        
        tk.Label(footer, textvariable=self.footer_var, anchor=tk.W, fg="#ffffff", bg="#2d2d2d", font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT)
        tk.Label(footer, textvariable=self.stats_var, anchor=tk.W, fg="#ffffff", bg="#2d2d2d", font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT)
        
        tk.Label(footer, text=f"Kodi Log Monitor {APP_VERSION}", anchor=tk.E, fg="#555555", bg="#2d2d2d", font=("Segoe UI", 8, "italic")).pack(side=tk.RIGHT)
        self.update_filter_button_colors()

    def get_file_size_info(self):
        if not self.log_file_path: return "0 KB"
        try:
            size_bytes = os.path.getsize(self.log_file_path)
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_bytes < 1024: return f"{size_bytes:.2f} {unit}"
                size_bytes /= 1024
        except: return "N/A"

    def update_stats(self):
        if not self.log_file_path: 
            self.stats_var.set("")
            return
        l = LANGS.get(self.current_lang.get(), LANGS["EN"])
        size_str = self.get_file_size_info()
        self.stats_var.set(l["stats"].format(self.filtered_lines_count, self.total_lines, size_str))

    def on_search_change(self, *args):
        if self.search_query.get(): self.btn_clear_search.pack(side=tk.LEFT, padx=(0, 2))
        else: self.btn_clear_search.pack_forget()
        self.trigger_refresh()

    def clear_search(self): self.search_query.set(""); self.search_entry.focus()

    def update_filter_button_colors(self):
        active = self.current_filter_tag.get()
        for rb, mode in self.filter_radios:
            target_bg = self.filter_colors[mode] if active == "all" or active == mode else "#3e3e42"
            rb.config(bg=target_bg, selectcolor=target_bg)

    def trigger_refresh(self, *args):
        self.update_filter_button_colors()
        if self.log_file_path and self.running: self.start_monitoring(self.log_file_path, save=False)

    def start_monitoring(self, path, save=True):
        self.running = False; self.log_file_path = path; self.total_lines = 0; self.filtered_lines_count = 0; self.retranslate_ui()
        if save: self.save_session()
        self.show_loading(True); self.txt_area.delete('1.0', tk.END)
        self.running = True; threading.Thread(target=self.monitor_loop, daemon=True).start()

    def monitor_loop(self):
        try:
            with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                if self.load_full_file.get(): lines = f.readlines()
                else:
                    f.seek(0, os.SEEK_END); f.seek(max(0, f.tell() - 250000)); lines = f.readlines()[-1000:]
                
                self.total_lines = len(lines)
                to_display = []
                for l_raw in lines:
                    data = self.get_line_data(l_raw)
                    if data:
                        to_display.append(data)
                        self.filtered_lines_count += 1
                
                self.root.after(0, self.bulk_insert, to_display)
                
                f.seek(0, os.SEEK_END); last_pos = f.tell()
                while self.running:
                    if os.path.getsize(self.log_file_path) < last_pos:
                        self.root.after(0, self.start_monitoring, self.log_file_path, False); break
                    line = f.readline()
                    if not line: self.root.after(0, self.update_stats); time.sleep(0.5); continue
                    last_pos = f.tell(); self.total_lines += 1
                    data = self.get_line_data(line)
                    if data:
                        self.filtered_lines_count += 1
                        self.root.after(0, self.append_to_gui, data[0], data[1])
                    else:
                        self.root.after(0, self.update_stats)
        except: self.show_loading(False)

    def get_line_data(self, line):
        low = line.lower(); tag_f = self.current_filter_tag.get(); query = self.search_query.get().lower()
        if (tag_f == "all" or f" {tag_f} " in low) and (not query or query in low):
            tag = "error" if " error " in low else "warning" if " warning " in low else "info" if " info " in low else None
            return (line, tag)
        return None

    def bulk_insert(self, data_list):
        self.txt_area.config(state=tk.NORMAL)
        for text, tag in data_list: self.txt_area.insert(tk.END, text, tag)
        if not self.is_paused.get(): self.txt_area.see(tk.END)
        self.update_stats(); self.show_loading(False)

    def append_to_gui(self, text, tag):
        self.txt_area.insert(tk.END, text, tag)
        if not self.is_paused.get() and self.txt_area.yview()[1] > 0.90: self.txt_area.see(tk.END)
        self.update_stats()

    def clear_console(self): self.txt_area.delete('1.0', tk.END); self.total_lines = 0; self.filtered_lines_count = 0; self.update_stats()
    def apply_wrap_mode(self): self.txt_area.config(wrap=tk.WORD if self.wrap_mode.get() else tk.NONE)
    def toggle_full_load(self): self.save_session(); self.start_monitoring(self.log_file_path, save=False)
    def show_loading(self, state):
        if state:
            l = LANGS.get(self.current_lang.get(), LANGS["EN"])
            self.loading_label.config(text=l["loading"]); self.overlay.grid(row=0, column=0, sticky="nsew"); self.root.update_idletasks()
        else: self.overlay.grid_forget()
    def change_language(self): self.retranslate_ui(); self.save_session()
    def retranslate_ui(self):
        l = LANGS.get(self.current_lang.get(), LANGS["EN"])
        self.btn_log.config(text=l["log"]); self.btn_sum.config(text=l["sum"]); self.btn_exp.config(text=l["exp"]); self.btn_clr.config(text=l["clr"])
        for rb, mode in self.filter_radios: 
            tag_map = {"all": "all", "info": "info", "warning": "warn", "error": "err"}
            rb.config(text=l[tag_map[mode]])
        self.footer_var.set(l["sel"] if not self.log_file_path else f"📍 {self.log_file_path}")
        self.update_stats()

    def save_session(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                f.write(f"{self.log_file_path}\n{self.current_lang.get()}\n{'1' if self.load_full_file.get() else '0'}\n{self.font_size}")
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
            except: pass
        self.retranslate_ui(); self.update_tags_config()
        if self.log_file_path: self.start_monitoring(self.log_file_path, save=False)

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("Log files", "*.log"), ("All files", "*.*")])
        if path: self.start_monitoring(path)

    def update_tags_config(self):
        c_font = ("Consolas", self.font_size)
        for t, c in [("info", "#4CAF50"), ("warning", "#FF9800"), ("error", "#F44336"), ("summary", "#00E5FF")]:
            self.txt_area.tag_config(t, foreground=c, font=(c_font[0], self.font_size))
        self.txt_area.configure(font=c_font); self.font_label.config(text=str(self.font_size))

    def show_summary(self):
        if not self.log_file_path: return
        l = LANGS.get(self.current_lang.get(), LANGS["EN"])
        try:
            with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                match = re.search(r"(-+\n.*?Starting Kodi.*?-+\n)", f.read(), re.DOTALL)
                if match: 
                    self.txt_area.insert(tk.END, l["sys_sum"], "summary")
                    self.txt_area.insert(tk.END, match.group(1), "summary"); self.txt_area.see(tk.END)
        except: pass

    def export_log(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile="kodi_extract.txt")
        if path:
            with open(path, "w", encoding="utf-8") as f: f.write(self.txt_area.get("1.0", tk.END))

    def increase_font(self): self.font_size += 1; self.update_tags_config(); self.save_session()
    def decrease_font(self): 
        if self.font_size > 6: self.font_size -= 1; self.update_tags_config(); self.save_session()

if __name__ == "__main__":
    root = tk.Tk()
    try:
        from ctypes import windll, byref, sizeof, c_int
        windll.dwmapi.DwmSetWindowAttribute(windll.user32.GetParent(root.winfo_id()), 35, byref(c_int(1)), sizeof(c_int))
    except: pass
    app = KodiLogMonitor(root); root.mainloop()