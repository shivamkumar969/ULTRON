@echo off
title ULTRON -- Wake Word Service
color 0A

echo ==============================================
echo   ULTRON -- Starting Wake Word Listener...
echo ==============================================

cd /d "%~dp0"

REM -- Check Python is installed --
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python was not found in your PATH.
    pause
    exit /b 1
)

echo.
echo Launching Wake Word Listener ("wake up ultron")...
python wake_service.py

echo.
pause
