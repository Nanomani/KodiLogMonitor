# 📂 Kodi Log Monitor
[![Tool for Kodi](https://img.shields.io/badge/Tool%20for-Kodi-blue?logo=kodi)](https://forum.kodi.tv/showthread.php?tid=384328) 
![Python](https://img.shields.io/badge/Python-3.0%2B-green?logo=python)
[![License](https://img.shields.io/badge/License-GPLv3-orange)](https://github.com/Nanomani/KodiLogMonitor/blob/master/LICENSE.txt)
![Total Downloads](https://img.shields.io/github/downloads/Nanomani/KodiLogMonitor/total)
![Téléchargements Latest](https://img.shields.io/github/downloads/Nanomani/KodiLogMonitor/latest/total)

A lightweight and intuitive real-time log viewer or a simple log editor for Kodi. It helps users and developers track events, troubleshoot errors, and monitor system status through a clean, color-coded interface.

![2026-04-10_183538](https://github.com/user-attachments/assets/06b52ded-0a25-4cb6-8241-cf376868fc38)

![2026-04-10_183705](https://github.com/user-attachments/assets/92a5cee4-bb74-496c-bf0b-330258555d06)

---

### 🎯 What is it for?
Kodi generates a log file that records everything happening in the background. This application allows you to:
* **Monitor in real-time**: See new log lines instantly as they are written.
* **Identify issues**: Errors are highlighted in red and warnings in orange for quick spotting.
* **Filter easily**: Focus on specific levels (Error, Warning, Info, Debug) or search for keywords.
* **Analyze setup**: Access a quick system summary to check your Kodi version and environment.

---

### 🔍 Keyword Lists (v1.2.0+)
You can now filter your logs using custom keyword lists:
* **Custom Filtering**: Create a `.txt` file in the `keyword_list` folder (one keyword or phrase per line).
* **Smart Highlighting**: The monitor only displays lines containing your keywords and highlights them for better visibility.
* **Easy Management**: Use the 📁 button to open the folder and ♻️ to refresh your lists instantly.

Some sample: [here](https://github.com/Nanomani/KodiLogMonitor/tree/main/keyword_list)

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

Update preferences are stored in the .kodi_monitor_config file:
You can edit or delete this file to reset the settings.

---

### ⌨️ Shortcuts (v1.3.7+)

Quick keyboard shortcuts to navigate and control the application efficiently.  
**Tip**: Press **F1** or the button **?** at any time to display help.  
```
Space        : Pause / Resume auto-scroll  
Ctrl + O     : Open log file  
Ctrl + S     : Export log
Ctrl + P     : Upload LOG  
Ctrl + F     : Search keyword  
Ctrl + G     : Clear console display  
Ctrl + L     : Toggle word wrap  
Ctrl + T     : Unlimited mode (∞) / 1000 lines  
S            : Show system summary (also accessible via F1)  
A            : Show Info, Warn, Error, Debug  
I, W, E, D   : Filter Info, Warn, Error or Debug  
Ctrl + R     : Reset all filters  
```
---

### 💡 Google Search Context Menu (v1.3.2+)
The application provides a convenient "Search on Google" option in the right-click context menu, allowing you to quickly look up any selected text from the logs.

---

### 🚀 For Regular Users
If you just want to use the tool without installing Python:

1. Go to the **[Releases](../../releases)** section on the right.
2. Download the latest for your OS.
3. Run the file. No installation is required.

---

### 🛠️ For Advanced Users & Developers
If you want to run the script manually or explore the code:

#### Running from source
Ensure you have Python 3.x installed, then:
```bash
git clone [https://github.com/YOUR_USERNAME/YOUR_REPO.git](https://github.com/YOUR_USERNAME/YOUR_REPO.git)
cd YOUR_REPO/src
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
