@echo off
setlocal enabledelayedexpansion

echo --------------------------------------------------------
echo ESP32 Scale Project: Environment Setup
echo --------------------------------------------------------

:: 1. Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python is not detected. 
    echo [!] Downloading Python 3.12 installer...
    
    :: Downloads the official web installer
    powershell -Command "Invoke-WebRequest -Uri https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe -OutFile python_installer.exe"
    
    echo [!] Running installer... 
    echo [!] IMPORTANT: Please ensure 'Add Python to PATH' is CHECKED in the window that appears.
    start /wait python_installer.exe /quiet PrependPath=1 Include_test=0
    
    del python_installer.exe
    echo [!] Python installation attempt finished.
) else (
    echo [V] Python is already installed.
)

:: 2. Refresh Path for the current session
:: This helps if Python was just installed in this window
set "PATH=%PATH%;%APPDATA%\Python\Scripts;%USERPROFILE%\AppData\Local\Programs\Python\Python312\Scripts"

:: 3. Ensure Pip is up to date and working
echo [*] Checking/Upgrading pip...
python -m ensurepip --upgrade
python -m pip install --upgrade pip

:: 4. Install Dependencies
echo [*] Installing required libraries: pandas, matplotlib, scikit-learn, pyserial...

:: We use 'python -m pip' instead of just 'pip' to avoid "command not found" errors
python -m pip install pandas numpy matplotlib scikit-learn pyserial

if %errorlevel% neq 0 (
    echo [X] There was an error installing dependencies.
) else (
    echo --------------------------------------------------------
    echo [V] SUCCESS: Environment is ready.
    echo [*] You can now run 'python read_scales.py' or 'python Plot.py'
    echo --------------------------------------------------------
)

pause