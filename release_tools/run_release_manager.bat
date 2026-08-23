@echo off
cd /d "%~dp0"

if exist "..\.venv\Scripts\pythonw.exe" (
    set "PYTHONW=..\.venv\Scripts\pythonw.exe"
) else (
    set "PYTHONW=pythonw.exe"
)

start "" /b "%PYTHONW%" release_manager_gui.py
exit /b 0
