@echo off
chcp 65001 > nul
cd /d %~dp0

echo ========================================
echo   FileFlow
echo ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found
    echo Please install Python from https://www.python.org/
    echo.
    echo Press Enter to exit...
    set /p dummy=
    exit /b 1
)

python -c "import colorama, yaml" >nul 2>&1
if errorlevel 1 (
    echo Installing required libraries...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo Error: Failed to install libraries
        echo.
        echo Press Enter to exit...
        set /p dummy=
        exit /b 1
    )
    echo.
)

echo Starting FileFlow...
echo.
python file_flow.py

if errorlevel 1 (
    echo.
    echo Error occurred
    echo.
    echo Press Enter to exit...
    set /p dummy=
    exit /b 1
)