@echo off
REM Student Focus Tracker Launcher
REM Usage: start_tracking.bat <class_id>

if "%~1"=="" (
    echo Error: Class ID is required
    echo Usage: start_tracking.bat ^<class_id^>
    echo Example: start_tracking.bat 507f1f77bcf86cd799439011
    pause
    exit /b 1
)

echo Starting Student Focus Tracker for class: %~1
echo Press Ctrl+C to stop tracking
echo.

python main.py %~1 --headless

echo.
echo Tracking stopped.
pause