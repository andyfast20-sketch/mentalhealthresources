@echo off
title Mental Health Resources App
cd /d "%~dp0"

echo Starting Mental Health Resources App...
echo.
echo Once the server is ready, open your browser to:
echo   http://127.0.0.1:5001
echo.
echo Close this window to stop the app.
echo ----------------------------------------

start "" "http://127.0.0.1:5001"

"C:\Users\Windows\AppData\Local\Python\pythoncore-3.14-64\python.exe" app.py

pause
