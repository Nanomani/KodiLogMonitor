# 📂 Kodi Log Monitor
[![Tool for Kodi](https://img.shields.io/badge/Tool%20for-Kodi-blue?logo=kodi)](https://forum.kodi.tv/showthread.php?tid=384328) 
![Python](https://img.shields.io/badge/Python-3.0%2B-green?logo=python)
[![License](https://img.shields.io/badge/License-GPLv3-orange)](https://github.com/Nanomani/KodiLogMonitor/blob/master/LICENSE.txt)
![Total Downloads](https://img.shields.io/github/downloads/Nanomani/KodiLogMonitor/total)
![Téléchargements Latest](https://img.shields.io/github/downloads/Nanomani/KodiLogMonitor/latest/total)

A lightweight and intuitive real-time log viewer and simple log editor for Kodi.  
It helps users and developers track events, troubleshoot errors, and monitor system status through a clean, color-coded interface.  
🚀 Designed for both users and developers to quickly analyze and troubleshoot Kodi logs.

![2026-04-10_183538](https://github.com/user-attachments/assets/06b52ded-0a25-4cb6-8241-cf376868fc38)

![2026-04-10_183705](https://github.com/user-attachments/assets/92a5cee4-bb74-496c-bf0b-330258555d06)

---

### ✨ Features
* **Real-Time Log Monitoring**: Instantly view new log entries as they are written.  
* **Advanced Filtering**: Filter logs by level (Info, Warning, Error, Debug) or custom keywords.  
* **Keyword Lists**: Use custom keyword files for targeted log analysis and highlighting.  
* **Dynamic Search**: Fast and responsive search, even on large log files.  
* **Color-Coded Interface**: Quickly identify issues with intuitive color highlighting.  
* **Large Log Handling**: Optimized for high-volume logs with smart limiting and performance safeguards.  
* **Log Upload Integration**: Upload logs to paste.kodi.tv with one click or via shortcut (Ctrl + P).  
* **System Summary**: Access key system and Kodi information instantly.  
* **Multi-Instance Support**: Run multiple instances with optional single-instance lock.  
* **Keyboard Shortcuts**: Full control via shortcuts for efficient navigation and actions.  
* **Responsive UI**: Optimized display across HD, FHD, and 4K screens.  
* **Light & Dark Themes**: Adapt the interface to your preference and reduce eye strain.  
* **Localization Support**: Multi-language interface with automatic OS language detection.  
* **Robust Log Access**: Handles network logs and connection loss with improved recovery mechanisms.  
---

### 🎯 What is it for?
Kodi generates a log file that records everything happening in the background.  
This tool helps you quickly understand and analyze that data:

* **Monitor activity in real time**
* **Quickly spot errors and warnings**
* **Focus on relevant information using filters and search**
* **Get a clear overview of your system and Kodi environment**
---

### 🔍 Keyword Lists (v1.2.0+)
You can filter your logs using custom keyword lists:

* **Custom filtering**: Create a `.txt` file in the `keyword_list` folder (one keyword or phrase per line).  
* **Smart highlighting**: Only matching lines are displayed and highlighted for better visibility.  
* **Easy management**: Use the 📁 button to open the folder and ♻️ to refresh your lists instantly.  

Examples available [here](https://github.com/Nanomani/KodiLogMonitor/tree/main/keyword_list).

---

### ⌨️ Shortcuts (v1.3.7+)

Quick keyboard shortcuts to navigate and control the application efficiently.  
**Tip**: Press **F1** or click the **?** button at any time to display help.  
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
### 🔔 Update Notifications (v1.4.0+)

The application can automatically detect new versions available on GitHub.

When an update is found, a dialog offers the following options:
```
Download     : Opens the latest release page on GitHub.  
Skip         : Ignores this version for future checks.  
Disable      : Turns off update notifications permanently.  
```
ℹ️ Notes

Update preferences are stored in the `.kodi_monitor_config` file.  
You can edit or delete this file to reset the settings.

---
### 💡 Google Search Context Menu (v1.3.2+)
The application provides a convenient "Search on Google" option in the right-click context menu, allowing you to quickly search any selected text from the logs.

---
### 🌐 Upload to Paste Kodi web service (v1.4.0+)
The application provides a convenient way to quickly upload logs to the Paste Kodi web service.

Use the **"UPLOAD"** button or **Ctrl + P** shortcut.  
The log is automatically copied to the clipboard, and paste.kodi.tv opens in your browser for easy sharing.

---
### 🚀 For Regular Users
If you want to use the tool without installing Python:

1. Go to the **[Releases](../../releases)** section.  
2. Download the latest version for your OS.  
3. Run the file — no installation required.  

---

### 🛠️ For Advanced Users & Developers
If you want to run the application from source or explore the code:

#### Running from source
Ensure you have Python 3.x installed, then:
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
├── main.py                 # Entry point: Initializes the Tkinter root and starts the application.  
├── config.py               # Configuration: Defines global constants, colors, and file paths.  
├── languages.py            # Localization: Contains dictionary for multi-language UI support.  
├── utils.py                # Utilities: Helper functions for fonts, system themes, and OS detection.  
│  
├── ui/                     # User Interface Package  
│   ├── __init__.py         # Package initialization.  
│   ├── app.py              # Main Class: Assembles all mixins to build the core application logic.  
│   ├── ui_builder.py       # UI Construction: Methods to build widgets, styles, and layout (setup_ui).  
│   ├── actions.py          # User Interactions: Handles file opening, exporting, and help windows.  
│   ├── log_display.py      # Log Rendering: Manages text insertion, highlighting, and filtering logic.  
│   ├── monitor.py          # Threaded Monitoring: Background loop for real-time log file reading.  
│   └── session.py          # Persistence: Saves and loads user settings (language, filters, window size).  
│  
└── assets/                 # Graphics Resources  
    ├── logo.ico            # Windows application icon.  
    ├── logo.png            # Generic image asset.  
    └── logo.icns           # macOS application icon.  
```
