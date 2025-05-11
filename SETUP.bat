@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

:: Ask for Python path
set /p PYTHON_PATH=Enter full path to your Python executable (e.g., C:\Users\you\AppData\Local\Programs\Python\Python310\python.exe): 

:: Ask for Chrome path
set /p CHROME_PATH=Enter full path to Chrome.exe (e.g., C:\Program Files\Google\Chrome\Application\chrome.exe): 


:: Create Chrome profile folder
echo Creating Chrome user profile folder at: %CHROME_PROFILE_DIR%
"%CHROME_PATH%" --user-data-dir="C:\temp\chrome_test"

:: Create virtual environment
echo Creating virtual environment in 'venv' folder...
"%PYTHON_PATH%" -m venv venv

:: Activate and install requirements
call venv\Scripts\activate
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt

echo.
echo Setup complete! Your virtual environment and Chrome profile are ready.
pause
