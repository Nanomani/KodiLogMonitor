@echo off
cls
pyinstaller --noconsole --onefile --add-data "assets\logo.ico;." --icon="assets\logo.ico" --name "KodiLogMonitor-windows" main.py

