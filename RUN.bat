@echo off
cd /d %~dp0
call venv\Scripts\activate

REM Redirect stderr to nul (silence internal Chrome/TF logs)
python main.py 2>nul

echo.
echo Script finished. Press any key to exit.
pause >nul
