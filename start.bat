@echo off
echo Starting AI-Powered Study Planner...

:: Start FastAPI Backend in a new window
start "Study Planner Backend (FastAPI)" cmd /k "cd /d "%~dp0" && python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload"

:: Start React Frontend in a new window
start "Study Planner Frontend (React)" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo ========================================================
echo Backend starting at:  http://localhost:8000/docs
echo Frontend starting at: http://localhost:5173
echo ========================================================
echo.
pause
