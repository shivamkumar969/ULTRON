@echo off
title J.A.R.V.I.S. -- Tactical AI Operating System
color 0B

echo ===================================================
echo    J.A.R.V.I.S. Tactical AI Operating System
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

REM -- Launch J.A.R.V.I.S. Main Orchestrator --
echo Starting J.A.R.V.I.S. Tactical Assistant...
echo.
python main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [WARNING] J.A.R.V.I.S. closed with exit code %ERRORLEVEL%.
    pause
)
