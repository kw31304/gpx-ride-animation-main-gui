@echo off
setlocal
cd /d "%~dp0"
title Build GPX Ride Renderer EXE

echo ========================================================================
echo   Run GPX Ride Renderer
echo ========================================================================
echo.

set PYTHON_EXE=.venv\Scripts\python.exe

if not exist "%PYTHON_EXE%" (
    set PYTHON_EXE=python
)

"%PYTHON_EXE%" GPX_Ride_Renderer.py

echo.
echo ========================================================================
echo   Press any key to exit.
echo ========================================================================
pause
