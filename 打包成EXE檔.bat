@echo off
chcp 65001 >nul
title 打包 GPX Ride Renderer 成 EXE 檔
echo ========================================================================
echo   GPX Ride Renderer - 一鍵打包 EXE 腳本
echo ========================================================================
echo.

set PYTHON_EXE=.venv\Scripts\python.exe

if not exist "%PYTHON_EXE%" (
    set PYTHON_EXE=python
)

"%PYTHON_EXE%" build_exe.py

echo.
echo ========================================================================
echo   打包結束！按任意鍵退出...
echo ========================================================================
pause >nul
