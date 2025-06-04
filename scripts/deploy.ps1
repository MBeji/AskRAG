# AskRAG Deployment Script for Windows PowerShell
# Usage: .\deploy.ps1 -Environment <staging|production> -ImageTag <tag>

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("staging", "production")]
    [string]$Environment,
    
    [Parameter(Mandatory=$false)]
    [string]$ImageTag = "latest"
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Script configuration
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$K8sDir = Join-Path $ProjectRoot "k8s"
$TempDir = New-TemporaryFile | ForEach-Object { Remove-Item $_; New-Item -ItemType Directory -Path $_.FullName }

# Colors for output
$Colors = @{
    Info = "Cyan"
    Success = "Green"
    Warning = "Yellow"
    Error = "Red"
}

# Logging functions
function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "Info"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = $Colors[$Level]
    Write-Host "[$timestamp] [$Level] $Message" -ForegroundColor $color
}

function Write-Info { param([string]$Message) Write-Log $Message "Info" }
function Write-Success { param([string]$Message) Write-Log $Message "Success" }
function Write-Warning { param([string]$Message) Write-Log $Message "Warning" }
function Write-Error { param([string]$Message) Write-Log $Message "Error" }

# Cleanup function
function Cleanup {
    if (Test-Path $TempDir) {
        Remove-Item -Recurse -Force $TempDir
    }
}

# Register cleanup on exit
trap { Cleanup }

# Validate prerequisites
function Test-Prerequisites {
    Write-Info "Checking prerequisites..."
    
    # Check kubectl
    try {
        kubectl version --client | Out-Null
        Write-Success "kubectl found"
    }
    catch {
        Write-Error "kubectl is not installed or not in PATH"
        exit 1
    }
    
    # Check kubectl context
    try {
        $context = kubectl config current-context
        Write-Success "kubectl context: $context"
    }
    catch {
        Write-Error "No kubectl context is set"
        exit 1
    }
    
    # Check if namespace exists
    try {
        kubectl get namespace "askrag-$Environment" | Out-Null
        Write-Success "Namespace askrag-$Environment exists"
    }
    catch {
        Write-Info "Creating namespace askrag-$Environment"
        kubectl apply -f (Join-Path $K8sDir "namespace.yaml")
    }
}

# Update image tags in manifests
function Update-ImageTags {
    Write-Info "Updating image tags to $ImageTag..."
    
    # Copy manifests to temp directory
    Copy-Item -Recurse "$K8sDir\*" $TempDir
    
    # Update backend image tag
    $backendFile = Join-Path $TempDir "backend.yaml"
    $content = Get-Content $backendFile -Raw
    $content = $content -replace "ghcr\.io/.*askrag.*backend:.*", "ghcr.io/$env:GITHUB_REPOSITORY/backend:$ImageTag"
    Set-Content -Path $backendFile -Value $content
    
    # Update frontend image tag
    $frontendFile = Join-Path $TempDir "frontend.yaml"
    $content = Get-Content $frontendFile -Raw
    $content = $content -replace "ghcr\.io/.*askrag.*frontend:.*", "ghcr.io/$env:GITHUB_REPOSITORY/frontend:$ImageTag"
    Set-Content -Path $frontendFile -Value $content
    
    Write-Success "Image tags updated"
}

# Deploy core infrastructure
function Deploy-Infrastructure {
    Write-Info "Deploying core infrastructure..."
    
    $files = @("namespace.yaml", "secrets.yaml", "configmap.yaml", "storage.yaml")
    
    foreach ($file in $files) {
        $filePath = Join-Path $TempDir $file
        kubectl apply -f $filePath
    }
    
    Write-Success "Core infrastructure deployed"
}

# Deploy databases
function Deploy-Databases {
    Write-Info "Deploying databases..."
    
    kubectl apply -f (Join-Path $TempDir "mongodb.yaml")
    kubectl apply -f (Join-Path $TempDir "redis.yaml")
    
    # Wait for databases to be ready
    Write-Info "Waiting for MongoDB to be ready..."
    kubectl wait --for=condition=ready pod -l app=mongodb -n "askrag-$Environment" --timeout=300s
    
    Write-Info "Waiting for Redis to be ready..."
    kubectl wait --for=condition=ready pod -l app=redis -n "askrag-$Environment" --timeout=300s
    
    Write-Success "Databases deployed and ready"
}

# Deploy applications
function Deploy-Applications {
    Write-Info "Deploying applications..."
    
    # Deploy backend
    kubectl apply -f (Join-Path $TempDir "backend.yaml")
    
    # Wait for backend rollout
    Write-Info "Waiting for backend deployment..."
    kubectl rollout status deployment/askrag-backend -n "askrag-$Environment" --timeout=600s
    
    # Deploy frontend
    kubectl apply -f (Join-Path $TempDir "frontend.yaml")
    
    # Wait for frontend rollout
    Write-Info "Waiting for frontend deployment..."
    kubectl rollout status deployment/askrag-frontend -n "askrag-$Environment" --timeout=600s
    
    Write-Success "Applications deployed"
}

# Deploy ingress
function Deploy-Ingress {
    Write-Info "Deploying ingress..."
    
    kubectl apply -f (Join-Path $TempDir "ingress.yaml")
    
    Write-Success "Ingress deployed"
}

# Verify deployment
function Test-Deployment {
    Write-Info "Verifying deployment..."
    
    # Check all pods are running
    Write-Info "Checking pod status..."
    kubectl get pods -n "askrag-$Environment"
    
    # Check services
    Write-Info "Checking services..."
    kubectl get services -n "askrag-$Environment"
    
    # Check ingress
    Write-Info "Checking ingress..."
    kubectl get ingress -n "askrag-$Environment"
    
    # Health check
    $backendUrl = "http://askrag-backend.askrag-$Environment.svc.cluster.local:8000"
    Write-Info "Performing health check..."
    
    try {
        kubectl run health-check --rm -i --restart=Never --image=curlimages/curl:latest --timeout=60s -n "askrag-$Environment" -- curl -f "$backendUrl/health" | Out-Null
        Write-Success "Health check passed"
    }
    catch {
        Write-Warning "Health check failed, but deployment may still be starting"
    }
}

# Main deployment process
function Start-Deployment {
    Write-Info "Starting AskRAG deployment to $Environment"
    Write-Info "Image tag: $ImageTag"
    
    try {
        Test-Prerequisites
        Update-ImageTags
        Deploy-Infrastructure
        Deploy-Databases
        Deploy-Applications
        Deploy-Ingress
        Test-Deployment
        
        Write-Success "Deployment to $Environment completed successfully!"
        Write-Info "Applications should be available shortly at the configured ingress endpoints"
    }
    catch {
        Write-Error "Deployment failed: $($_.Exception.Message)"
        throw
    }
    finally {
        Cleanup
    }
}

# Run deployment
Start-Deployment
