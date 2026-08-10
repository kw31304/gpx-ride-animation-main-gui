@echo off
setlocal
cd /d "%~dp0"
title Build GPX Ride Renderer EXE

echo ========================================================================
echo   GPX Ride Renderer - Build EXE Script
echo ========================================================================
echo.

set PYTHON_EXE=.venv\Scripts\python.exe

if not exist "%PYTHON_EXE%" (
    set PYTHON_EXE=python
)

"%PYTHON_EXE%" build_exe.py

echo.
echo ========================================================================
echo   Build finished! Press any key to exit.
echo ========================================================================
pause
