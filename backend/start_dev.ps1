# AskRAG Backend Development Server Starter

Write-Host "🚀 Starting AskRAG Backend Development Server" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

Set-Location "d:\11-coding\AskRAG\backend"

Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

Write-Host "Starting FastAPI server..." -ForegroundColor Yellow
Write-Host ""
Write-Host "📍 Server will be available at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📍 API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan  
Write-Host "📍 Health Check: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
