@echo off
chcp 65001 >nul
title GPX Ride Renderer - Build EXE
cd /d "%~dp0"

if exist "..\.venv\Scripts\python.exe" (
    "..\.venv\Scripts\python.exe" build_exe.py
) else (
    python build_exe.py
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] ??????????%ERRORLEVEL%
    pause
)
