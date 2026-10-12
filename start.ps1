Write-Host "Starting AI-Powered Study Planner..." -ForegroundColor Cyan

# Start Backend in a separate window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot'; python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload"

# Start Frontend in a separate window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot/frontend'; npm run dev"

Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host "Backend API:      http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "Frontend Web App: http://localhost:5173" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Green
