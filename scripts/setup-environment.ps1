# Environment Setup Script for AskRAG (PowerShell)
# Helps setup environment variables for different environments

param(
    [Parameter(Position=0)]
    [ValidateSet("development", "staging", "production", "validate", "help")]
    [string]$Environment
)

# Functions for colored output
function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Blue
}

# Project root
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

Write-Host "🔧 AskRAG Environment Setup" -ForegroundColor Blue
Write-Host "==============================="

# Function to copy environment template
function Copy-EnvTemplate {
    param(
        [string]$Component,
        [string]$Environment
    )
    
    $SourceFile = Join-Path $ProjectRoot "$Component\.env.$Environment"
    $TargetFile = Join-Path $ProjectRoot "$Component\.env"
    
    if (Test-Path $SourceFile) {
        Copy-Item $SourceFile $TargetFile -Force
        Write-Success "Copied $Component\.env.$Environment to $Component\.env"
    } else {
        Write-Error "Template file not found: $SourceFile"
        return $false
    }
    return $true
}

# Function to setup environment
function Setup-Environment {
    param([string]$Environment)
    
    Write-Info "Setting up $Environment environment..."
    
    # Copy backend environment
    $backendSuccess = Copy-EnvTemplate "backend" $Environment
    
    # Copy frontend environment  
    $frontendSuccess = Copy-EnvTemplate "frontend" $Environment
    
    if (-not $backendSuccess -or -not $frontendSuccess) {
        Write-Error "Failed to setup environment"
        return
    }
    
    # Create necessary directories
    $directories = @(
        "backend\uploads",
        "backend\data", 
        "backend\logs",
        "frontend\dist"
    )
    
    foreach ($dir in $directories) {
        $fullPath = Join-Path $ProjectRoot $dir
        if (-not (Test-Path $fullPath)) {
            New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
        }
    }
    
    Write-Success "Environment setup complete for $Environment"
}

# Function to validate environment
function Validate-Environment {
    Write-Info "Validating environment configuration..."
    
    $validationScript = Join-Path $ProjectRoot "scripts\validate_environments.py"
    
    if (Test-Path $validationScript) {
        python $validationScript
    } else {
        Write-Warning "Validation script not found. Skipping validation."
    }
}

# Function to show help
function Show-Help {
    Write-Host "Usage: .\setup-environment.ps1 [ENVIRONMENT]"
    Write-Host ""
    Write-Host "Environments:"
    Write-Host "  development  - Setup development environment"
    Write-Host "  staging      - Setup staging environment"
    Write-Host "  production   - Setup production environment"
    Write-Host "  validate     - Validate current environment configuration"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\setup-environment.ps1 development"
    Write-Host "  .\setup-environment.ps1 staging"
    Write-Host "  .\setup-environment.ps1 validate"
}

# Function for interactive setup
function Interactive-Setup {
    Write-Host ""
    Write-Host "Select environment to setup:"
    Write-Host "1) Development"
    Write-Host "2) Staging"
    Write-Host "3) Production"
    Write-Host "4) Validate current configuration"
    Write-Host "5) Exit"
    
    $choice = Read-Host "Enter your choice (1-5)"
    
    switch ($choice) {
        "1" {
            Setup-Environment "development"
        }
        "2" {
            Setup-Environment "staging"
            Write-Warning "Remember to replace secret placeholders with actual values!"
        }
        "3" {
            Setup-Environment "production"
            Write-Warning "Remember to replace secret placeholders with actual values!"
            Write-Warning "Ensure all secrets are properly configured in your secret manager!"
        }
        "4" {
            Validate-Environment
        }
        "5" {
            Write-Info "Goodbye!"
            exit 0
        }
        default {
            Write-Error "Invalid choice. Please select 1-5."
            Interactive-Setup
        }
    }
}

# Main logic
if (-not $Environment) {
    # No arguments, run interactive setup
    Interactive-Setup
} elseif ($Environment -eq "help") {
    Show-Help
} elseif ($Environment -eq "validate") {
    Validate-Environment
} elseif ($Environment -in @("development", "staging", "production")) {
    Setup-Environment $Environment
    
    # Show warnings for non-development environments
    if ($Environment -ne "development") {
        Write-Host ""
        Write-Warning "IMPORTANT: This is a $Environment environment setup!"
        Write-Warning "Make sure to:"
        Write-Warning "1. Replace all `${SECRET_NAME} placeholders with actual values"
        Write-Warning "2. Use a proper secret management system"
        Write-Warning "3. Validate the configuration before deployment"
        Write-Host ""
        Write-Info "Run '.\setup-environment.ps1 validate' to check your configuration"
    }
}

Write-Success "Environment setup completed!"
