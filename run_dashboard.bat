@echo off
echo ============================================================
echo  VoltSight BI — Dashboard Launcher
echo ============================================================
echo.

set VENV=C:\Users\USER\Downloads\voltsight-bi-part1\.venv
set PROJECT=C:\Users\USER\Downloads\voltsight-bi-part1\voltsight-bi
set PYTHON=%VENV%\Scripts\python.exe
set PIP=%VENV%\Scripts\pip.exe

if not exist "%PYTHON%" (
    echo ERROR: Virtual environment not found at %VENV%
    pause
    exit /b 1
)

echo [0/3] Pulling latest code from GitHub...
cd "%PROJECT%"
git pull
echo       Done!
echo.

echo [1/3] Installing required packages into venv...
"%PIP%" install streamlit plotly --quiet
echo       Done!
echo.

echo [2/3] Building Gold layer data...
"%PYTHON%" scripts/build_gold.py
echo       Done!
echo.

echo [3/3] Starting VoltSight BI Dashboard...
echo.
echo  Opening browser at: http://localhost:8501
echo  Press Ctrl+C to stop the dashboard
echo.
echo ============================================================
"%PYTHON%" -m streamlit run "%PROJECT%\dashboard\app.py"

pause
