# 📂 Kodi Log Monitor
A lightweight and intuitive real-time log viewer or a simple log editor for Kodi. It helps users and developers track events, troubleshoot errors, and monitor system status through a clean, color-coded interface.

![screenshot](https://github.com/user-attachments/assets/0fe33ca1-d2ba-4a8c-9156-32cffe775058)


---

### 📝 What is it for?
Kodi generates a log file that records everything happening in the background. This application allows you to:
* **Monitor in real-time**: See new log lines instantly as they are written (tail -f style).
* **Identify issues**: Errors are highlighted in red and warnings in orange for quick spotting.
* **Filter easily**: Focus on specific levels (Error, Warning, Info) or search for keywords.
* **Analyze setup**: Access a quick system summary to check your Kodi version and environment.

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
