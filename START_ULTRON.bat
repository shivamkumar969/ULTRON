@echo off
title ULTRON -- AI Desktop Assistant
color 0A

echo ===================================================
echo    ULTRON AI Engine -- Launcher
echo ===================================================
echo.

cd /d "%~dp0"

REM -- Check Python is installed --
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python was not found in your PATH.
    echo Please make sure Python is installed and added to PATH.
    echo.
    pause
    exit /b 1
)

REM -- Check setup completion --
if not exist ".ultron_setup_complete" (
    echo First-time launch detected. Running setup...
    echo.
    python ULTRON_SETUP.py
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo [ERROR] Setup encountered an issue.
        pause
        exit /b %ERRORLEVEL%
    )
)

REM -- Launch ULTRON Main Orchestrator --
echo Starting ULTRON Assistant...
echo.
python main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [WARNING] ULTRON closed with exit code %ERRORLEVEL%.
    pause
)
