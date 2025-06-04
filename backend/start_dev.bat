@echo off
echo 🚀 Starting AskRAG Backend Development Server
echo ==========================================

cd /d "d:\11-coding\AskRAG\backend"

echo Activating virtual environment...
call .\venv\Scripts\activate.bat

echo Starting FastAPI server...
echo.
echo 📍 Server will be available at: http://localhost:8000
echo 📍 API Documentation: http://localhost:8000/docs
echo 📍 Health Check: http://localhost:8000/health
echo.

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
