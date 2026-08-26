@echo off
cd /d "%~dp0"

if exist "..\.venv\Scripts\pythonw.exe" (
    set "PYTHONW=..\.venv\Scripts\pythonw.exe"
) else if exist "%USERPROFILE%\miniconda3\pythonw.exe" (
    set "PYTHONW=%USERPROFILE%\miniconda3\pythonw.exe"
    set "PATH=%USERPROFILE%\miniconda3;%USERPROFILE%\miniconda3\Scripts;%USERPROFILE%\miniconda3\Library\bin;%PATH%"
) else (
    set "PYTHONW=pythonw.exe"
)

start "" /b "%PYTHONW%" release_manager_gui.py
exit /b 0
