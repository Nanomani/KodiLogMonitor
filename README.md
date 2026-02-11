# 📂 Kodi Log Monitor
[![Tool for Kodi](https://img.shields.io/badge/Tool%20for-Kodi-blue)](https://forum.kodi.tv/showthread.php?tid=384328) ![Total downloads](https://img.shields.io/github/downloads/Nanomani/KodiLogMonitor/total) ![Downloads latest release](https://img.shields.io/github/downloads/Nanomani/KodiLogMonitor/latest/total)





A lightweight and intuitive real-time log viewer or a simple log editor for Kodi. It helps users and developers track events, troubleshoot errors, and monitor system status through a clean, color-coded interface.

![screenshot_01](https://github.com/user-attachments/assets/a483407d-9225-40f2-bbe4-8f4e7bcf282f)

---

### 📝 What is it for?
Kodi generates a log file that records everything happening in the background. This application allows you to:
* **Monitor in real-time**: See new log lines instantly as they are written (tail -f style).
* **Identify issues**: Errors are highlighted in red and warnings in orange for quick spotting.
* **Filter easily**: Focus on specific levels (Error, Warning, Info) or search for keywords.
* **Analyze setup**: Access a quick system summary to check your Kodi version and environment.

---

### 🔍 Keyword Lists (v1.2.0+)
You can now filter your logs using custom keyword lists:
* **Custom Filtering**: Create a `.txt` file in the `keyword_lists` folder (one keyword or phrase per line).
* **Smart Highlighting**: The monitor only displays lines containing your keywords and highlights them for better visibility.
* **Easy Management**: Use the 📁 button to open the folder and ♻️ to refresh your lists instantly.

---

### 🎨 Customization (v1.2.0+)
The code is now designed for easy styling. You can find the **UI THEME** section at the very beginning of the script to change:
* **Interface Colors**: Modify backgrounds for the text area, header, and buttons.
* **Log & Highlight Colors**: Change the hex codes for `info`, `warning`, `error`, and the keyword `highlight`.
* **Centralized Design**: No need to search through the functions; everything is at the top of the file.

---

### 🚀 For Regular Users
If you just want to use the tool without installing Python:

1. Go to the **[Releases](../../releases)** section on the right.
2. Download the latest `KodiLogMonitor.exe`.
3. Run the file. No installation is required.
*Note: This binary is pre-built for Windows.*

---

### 🛠️ For Advanced Users & Developers
If you want to run the script manually or explore the code:

#### Running from source
Ensure you have Python 3.x installed, then:
```bash
git clone [https://github.com/YOUR_USERNAME/YOUR_REPO.git](https://github.com/YOUR_USERNAME/YOUR_REPO.git)
cd YOUR_REPO
python kodi_log_monitor.py
