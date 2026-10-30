@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Project Python environment is missing. See docs\review_demo.md.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo Streamlit is missing. Install requirements-demo.txt first.
    pause
    exit /b 1
)
echo Review demo: http://127.0.0.1:8501
echo Keep this window open. Press Ctrl+C to stop the demo.
".venv\Scripts\python.exe" -m streamlit run streamlit_app.py --server.port 8501
pause
