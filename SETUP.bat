@echo off
title ULTRON -- First-Time Setup
color 0A

echo ===================================================
echo    ULTRON AI Engine -- First-Time Setup
echo ===================================================
echo.

cd /d "%~dp0"

REM -- Check Python is installed --
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python was not found on this PC.
    echo Please install Python and add it to PATH.
    echo.
    pause
    exit /b 1
)

echo Running ULTRON setup...
echo.
python ULTRON_SETUP.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Setup encountered an error.
    pause
    exit /b %ERRORLEVEL%
)

pause
