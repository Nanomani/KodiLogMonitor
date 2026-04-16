# 📂 Kodi Log Monitor

[![Tool for Kodi](https://img.shields.io/badge/Tool%20for-Kodi-blue?logo=kodi)](https://forum.kodi.tv/showthread.php?tid=384328) 
![Python](https://img.shields.io/badge/Python-3.0%2B-green?logo=python)
[![License](https://img.shields.io/badge/License-GPLv3-orange)](LICENSE.txt)
![Downloads](https://img.shields.io/github/downloads/Nanomani/KodiLogMonitor/total)

🚀 **A fast, lightweight real-time log viewer for Kodi — built for users and developers.**

Quickly monitor, filter, and analyze Kodi logs with a clean and responsive interface.

---

### ✨ Features

- **Real-Time Log Monitoring** – Instantly view new log entries  
- **Advanced Filtering** – Filter by level (Info, Warning, Error, Debug) or keywords  
- **Dynamic Search** – Fast search, even on very large log files  
- **Large Log Support** – Optimized for high-volume logs with smart limits  
- **Color-Coded UI** – Quickly identify issues at a glance  
- **Log Upload (paste.kodi.tv)** – Share logs in one click (Ctrl + P)  
- **System Summary** – Instantly view Kodi/system info  
- **Keyboard Shortcuts** – Full control without leaving the keyboard  
- **Multi-Instance Support** – Optional single-instance lock  
- **Responsive UI** – Works seamlessly from HD to 4K  
- **Light & Dark Themes** – Comfortable for long sessions  
- **Localization** – Multi-language support with auto-detection  
- **Robust Network Handling** – Stable with remote logs and reconnections  

---

### 📸 Screenshots

![screenshot1](https://github.com/user-attachments/assets/06b52ded-0a25-4cb6-8241-cf376868fc38)
![screenshot2](https://github.com/user-attachments/assets/92a5cee4-bb74-496c-bf0b-330258555d06)

---

### 🎯 Why use Kodi Log Monitor?

Kodi logs can be large, noisy, and hard to read.  
This tool helps you:

- **Understand what's happening in real time**
- **Quickly spot errors and warnings**
- **Focus only on relevant information**
- **Debug issues faster**

---

## ⚡ Quick Start

### 👉 Download (recommended)
1. Go to the **[Releases](../../releases)** section  
2. Download the latest version  
3. Run — no installation required  

---

### ⌨️ Shortcuts

Press **F1** anytime to view all shortcuts.

```
Space        : Pause / Resume auto-scroll  
Ctrl + O     : Open log file  
Ctrl + S     : Export log
Ctrl + P     : Upload log  
Ctrl + F     : Search keywords  
Ctrl + G     : Clear console  
Ctrl + L     : Toggle word wrap  
Ctrl + T     : Unlimited mode (∞) / 1000 lines  
Ctrl + A     : Select all
M            : Open context menu in the log
S            : Show system summary (also accessible via F1)  
A            : Show Info, Warn, Error, Debug  
I, W, E, D   : Filter Info, Warn, Error or Debug  
Ctrl + R     : Reset all filters  
```
---

### 🌐 Log Upload

Upload logs instantly to paste.kodi.tv using **Ctrl + P** or the **UPLOAD** button.  
The log is copied to your clipboard and the website opens automatically.

---

### 🔍 Keyword Lists

- Create `.txt` files with keywords  
- Highlight and filter matching log lines  
- Easily manage via the UI  

👉 Examples available [here](https://github.com/Nanomani/KodiLogMonitor/tree/main/keyword_list).

---

### 🛠️ Run from Source

```bash
git clone https://github.com/Nanomani/KodiLogMonitor.git
cd KodiLogMonitor/src
python main.py
```
---

### 📝 Project Structure (v1.3.7+)
```
src/
│
├── main.py                 # Entry point
├── config.py               # Configuration
├── languages.py            # Localization
├── utils.py                # Utilities
│  
├── ui/                     # User Interface Package  
│   ├── __init__.py         # Package initialization
│   ├── app.py              # Main Class
│   ├── ui_builder.py       # UI Construction
│   ├── actions.py          # User Interactions
│   ├── log_display.py      # Log Rendering
│   ├── monitor.py          # Threaded Monitoring
│   └── session.py          # Persistence  
│  
└── assets/                 # Graphics Resources  
    ├── logo.ico            # Windows application icon.  
    ├── logo.png            # Generic image asset.  
    └── logo.icns           # macOS application icon.  
```

