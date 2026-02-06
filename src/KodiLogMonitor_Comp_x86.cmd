@echo off
cls
pyinstaller --noconsole --onefile --add-data "logo.ico;." --icon="logo.ico" --name "KodiLogMonitor" KodiLogMonitor.py

