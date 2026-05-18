@echo off
title LTRSEC-2381 Lab Runner
cls


:: Switch working directory to the script folder
cd /d "C:\scripts\startsection"
python "C:\scripts\StartSection\startSection.py"

:: 3. Graceful Exit
echo.
echo [OK] Section updated successfully.
echo This window will close in 3 seconds...
timeout /t 5
exit

