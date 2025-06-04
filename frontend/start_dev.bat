@echo off
echo ================================
echo   AskRAG Frontend - React Dev
echo ================================
echo.

echo Checking Node.js installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

echo Node.js version:
node --version

echo.
echo Checking npm installation...
npm --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: npm is not installed or not in PATH
    pause
    exit /b 1
)

echo npm version:
npm --version

echo.
echo Navigating to frontend directory...
cd /d "%~dp0"

echo.
echo Checking dependencies...
if not exist "node_modules" (
    echo Installing dependencies...
    npm install
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
) else (
    echo Dependencies already installed
)

echo.
echo ================================
echo   Starting React Dev Server
echo ================================
echo.
echo The application will be available at:
echo http://localhost:5173
echo.
echo Press Ctrl+C to stop the server
echo.

npm run dev

echo.
echo Development server stopped.
pause
