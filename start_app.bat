@echo off
setlocal
cd /d "%~dp0"
set PYTHONDONTWRITEBYTECODE=1
python -B run_app.py
if errorlevel 1 (
  echo.
  echo Color Rough Reference Tool failed to start.
  echo Please copy the message above and send it to Codex.
  pause
)
