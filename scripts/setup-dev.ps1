# Setup-Dev.ps1
# Script de setup rapide pour l'environnement de développement AskRAG

Write-Host "🚀 Setup AskRAG Development Environment" -ForegroundColor Cyan
Write-Host "======================================="

# Variables
$ProjectDir = "d:\11-coding\AskRAG"
$BackendDir = "$ProjectDir\backend"
$FrontendDir = "$ProjectDir\frontend"

Write-Host "📁 Creating project structure..." -ForegroundColor Yellow

# Backend structure
$BackendDirectories = @(
    "$BackendDir\app\api\v1",
    "$BackendDir\app\core",
    "$BackendDir\app\models", 
    "$BackendDir\app\services",
    "$BackendDir\app\utils",
    "$BackendDir\tests",
    "$BackendDir\data\faiss_index",
    "$BackendDir\uploads"
)

foreach ($Dir in $BackendDirectories) {
    if (!(Test-Path $Dir)) {
        New-Item -ItemType Directory -Path $Dir -Force | Out-Null
        Write-Host "Created: $Dir" -ForegroundColor Gray
    }
}

# Frontend structure
$FrontendDirectories = @(
    "$FrontendDir\src\components\ui",
    "$FrontendDir\src\components\chat",
    "$FrontendDir\src\components\auth",
    "$FrontendDir\src\pages",
    "$FrontendDir\src\hooks",
    "$FrontendDir\src\services",
    "$FrontendDir\src\store",
    "$FrontendDir\src\types",
    "$FrontendDir\src\utils",
    "$FrontendDir\public"
)

foreach ($Dir in $FrontendDirectories) {
    if (!(Test-Path $Dir)) {
        New-Item -ItemType Directory -Path $Dir -Force | Out-Null
        Write-Host "Created: $Dir" -ForegroundColor Gray
    }
}

Write-Host "✅ Project structure created!" -ForegroundColor Green

Write-Host "`n📋 Next steps:" -ForegroundColor Cyan
Write-Host "1. Set-Location backend && python -m venv venv" -ForegroundColor White
Write-Host "2. .\venv\Scripts\Activate.ps1" -ForegroundColor White  
Write-Host "3. pip install fastapi uvicorn" -ForegroundColor White
Write-Host "4. Set-Location ..\frontend && npm create vite@latest . --template react-ts" -ForegroundColor White
Write-Host "5. docker-compose up --build" -ForegroundColor White

Write-Host "`n🎉 Setup complete! Ready for development." -ForegroundColor Green
