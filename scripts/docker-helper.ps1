# AskRAG Docker PowerShell Helper Script for Windows

param(
    [Parameter(Position=0)]
    [string]$Command,
    
    [Parameter(Position=1)]
    [string]$Service
)

# Colors for output
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Function to check if Docker is running
function Test-Docker {
    try {
        docker info | Out-Null
        Write-Success "Docker is running"
        return $true
    }
    catch {
        Write-Error "Docker is not running. Please start Docker Desktop."
        return $false
    }
}

# Function to check if docker-compose is available
function Test-DockerCompose {
    try {
        docker-compose version | Out-Null
        Write-Success "docker-compose is available"
        return $true
    }
    catch {
        Write-Error "docker-compose is not installed or not in PATH"
        return $false
    }
}

# Function to start development environment
function Start-DevEnvironment {
    Write-Info "Starting AskRAG development environment..."
    
    # Copy environment file if not exists
    if (-not (Test-Path ".env")) {
        Copy-Item ".env.docker.dev" ".env"
        Write-Success "Created .env file from .env.docker.dev"
    }
    
    # Build and start services
    docker-compose -f docker-compose.dev.yml up --build -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Development environment started!"
        Write-Info "Services available at:"
        Write-Host "  - Frontend: http://localhost:5173" -ForegroundColor Cyan
        Write-Host "  - Backend API: http://localhost:8000" -ForegroundColor Cyan
        Write-Host "  - MongoDB: localhost:27017" -ForegroundColor Cyan
        Write-Host "  - Redis: localhost:6379" -ForegroundColor Cyan
    } else {
        Write-Error "Failed to start development environment"
    }
}

# Function to start production environment
function Start-ProdEnvironment {
    Write-Info "Starting AskRAG production environment..."
    
    # Copy environment file if not exists
    if (-not (Test-Path ".env")) {
        Copy-Item ".env.docker" ".env"
        Write-Warning "Created .env file from .env.docker - please configure it!"
    }
    
    # Build and start services
    docker-compose up --build -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Production environment started!"
        Write-Info "Services available at:"
        Write-Host "  - Frontend: http://localhost:3000" -ForegroundColor Cyan
        Write-Host "  - Backend API: http://localhost:8000" -ForegroundColor Cyan
        Write-Host "  - MongoDB: localhost:27017" -ForegroundColor Cyan
        Write-Host "  - Redis: localhost:6379" -ForegroundColor Cyan
    } else {
        Write-Error "Failed to start production environment"
    }
}

# Function to stop all services
function Stop-AllServices {
    Write-Info "Stopping all AskRAG services..."
    
    docker-compose -f docker-compose.dev.yml down
    docker-compose down
    
    Write-Success "All services stopped"
}

# Function to show logs
function Show-ServiceLogs {
    param([string]$ServiceName)
    
    if ([string]::IsNullOrEmpty($ServiceName)) {
        Write-Info "Showing logs for all services..."
        docker-compose -f docker-compose.dev.yml logs -f
    } else {
        Write-Info "Showing logs for service: $ServiceName"
        docker-compose -f docker-compose.dev.yml logs -f $ServiceName
    }
}

# Function to reset all data
function Reset-AllData {
    Write-Warning "This will remove all Docker volumes and data. Are you sure? (y/N)"
    $response = Read-Host
    
    if ($response -match "^[yY]") {
        Write-Info "Stopping services and removing volumes..."
        
        docker-compose -f docker-compose.dev.yml down -v
        docker-compose down -v
        
        # Remove volumes
        docker volume rm askrag_mongodb_data, askrag_mongodb_dev_data, askrag_redis_data 2>$null
        
        Write-Success "All data reset successfully"
    } else {
        Write-Info "Reset cancelled"
    }
}

# Function to run backend tests
function Start-BackendTests {
    Write-Info "Running backend tests..."
    
    docker-compose -f docker-compose.dev.yml exec backend-dev pytest tests/ -v
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Tests completed successfully"
    } else {
        Write-Error "Tests failed"
    }
}

# Function to show service status
function Show-ServiceStatus {
    Write-Info "AskRAG Services Status:"
    docker-compose -f docker-compose.dev.yml ps
}

# Function to open shell in service
function Open-ServiceShell {
    param([string]$ServiceName = "backend-dev")
    
    Write-Info "Opening shell in service: $ServiceName"
    docker-compose -f docker-compose.dev.yml exec $ServiceName /bin/bash
}

# Function to show help
function Show-Help {
    Write-Host "AskRAG Docker Helper Script for Windows" -ForegroundColor Cyan
    Write-Host "Usage: .\docker-helper.ps1 {Command} [Service]" -ForegroundColor White
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor Yellow
    Write-Host "  dev        Start development environment" -ForegroundColor White
    Write-Host "  prod       Start production environment" -ForegroundColor White
    Write-Host "  stop       Stop all services" -ForegroundColor White
    Write-Host "  logs       Show logs (optional: specify service)" -ForegroundColor White
    Write-Host "  status     Show service status" -ForegroundColor White
    Write-Host "  reset      Reset all data (removes volumes)" -ForegroundColor White
    Write-Host "  test       Run backend tests" -ForegroundColor White
    Write-Host "  shell      Open shell in service (default: backend-dev)" -ForegroundColor White
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  .\docker-helper.ps1 dev                 # Start development environment" -ForegroundColor White
    Write-Host "  .\docker-helper.ps1 logs backend-dev    # Show backend logs" -ForegroundColor White
    Write-Host "  .\docker-helper.ps1 shell frontend-dev  # Open shell in frontend container" -ForegroundColor White
}

# Main script logic
if (-not (Test-Docker) -or -not (Test-DockerCompose)) {
    exit 1
}

switch ($Command.ToLower()) {
    { $_ -in @("dev", "start-dev") } {
        Start-DevEnvironment
    }
    { $_ -in @("prod", "start-prod") } {
        Start-ProdEnvironment
    }
    "stop" {
        Stop-AllServices
    }
    "logs" {
        Show-ServiceLogs -ServiceName $Service
    }
    "status" {
        Show-ServiceStatus
    }
    "reset" {
        Reset-AllData
    }
    "test" {
        Start-BackendTests
    }
    "shell" {
        Open-ServiceShell -ServiceName $Service
    }
    default {
        Show-Help
    }
}
