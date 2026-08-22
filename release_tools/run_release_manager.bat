@echo off
chcp 65001 >nul
title GPX Ride Renderer - Release Manager
cd /d "%~dp0"

if exist "..\.venv\Scripts\python.exe" (
    "..\.venv\Scripts\python.exe" release_manager_gui.py
) else (
    python release_manager_gui.py
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] ??????????%ERRORLEVEL%
    pause
)
