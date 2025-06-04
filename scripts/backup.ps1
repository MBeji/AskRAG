# AskRAG Backup Script for Windows PowerShell
# Usage: .\backup.ps1 -Environment <staging|production> [-BackupType <full|incremental|config-only>]

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("staging", "production")]
    [string]$Environment,
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("full", "incremental", "config-only")]
    [string]$BackupType = "full"
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Script configuration
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackupDir = "C:\Backups\askrag"
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"

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

# Create backup directory structure
function New-BackupStructure {
    $backupPath = Join-Path $BackupDir "$Environment\$Timestamp"
    
    $subDirs = @("mongodb", "redis", "uploads", "configs", "k8s")
    foreach ($dir in $subDirs) {
        New-Item -ItemType Directory -Path (Join-Path $backupPath $dir) -Force | Out-Null
    }
    
    return $backupPath
}

# Backup MongoDB data
function Backup-MongoDB {
    param([string]$BackupPath)
    
    Write-Info "Backing up MongoDB data..."
    
    try {
        $mongoPod = kubectl get pods -n "askrag-$Environment" -l app=mongodb -o jsonpath='{.items[0].metadata.name}'
        
        if (-not $mongoPod) {
            Write-Error "MongoDB pod not found"
            return
        }
        
        # Get MongoDB credentials
        $mongoUser = kubectl get secret askrag-secrets -n "askrag-$Environment" -o jsonpath='{.data.MONGODB_USERNAME}' | ForEach-Object { [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($_)) }
        $mongoPass = kubectl get secret askrag-secrets -n "askrag-$Environment" -o jsonpath='{.data.MONGODB_PASSWORD}' | ForEach-Object { [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($_)) }
        
        # Create MongoDB dump
        kubectl exec $mongoPod -n "askrag-$Environment" -- mongodump --username $mongoUser --password $mongoPass --authenticationDatabase admin --out /tmp/backup
        
        # Copy dump to backup location
        kubectl cp "askrag-$Environment/$mongoPod:/tmp/backup" (Join-Path $BackupPath "mongodb")
        
        # Compress the backup
        $mongoBackupPath = Join-Path $BackupPath "mongodb"
        $archivePath = Join-Path $mongoBackupPath "mongodb-$Timestamp.zip"
        Compress-Archive -Path (Join-Path $mongoBackupPath "backup") -DestinationPath $archivePath
        Remove-Item -Recurse -Force (Join-Path $mongoBackupPath "backup")
        
        Write-Success "MongoDB backup completed"
    }
    catch {
        Write-Error "MongoDB backup failed: $($_.Exception.Message)"
    }
}

# Backup Redis data
function Backup-Redis {
    param([string]$BackupPath)
    
    Write-Info "Backing up Redis data..."
    
    try {
        $redisPod = kubectl get pods -n "askrag-$Environment" -l app=redis -o jsonpath='{.items[0].metadata.name}'
        
        if (-not $redisPod) {
            Write-Error "Redis pod not found"
            return
        }
        
        # Create Redis backup
        kubectl exec $redisPod -n "askrag-$Environment" -- redis-cli BGSAVE
        
        # Wait for background save to complete
        do {
            Start-Sleep -Seconds 1
            $saveTime = kubectl exec $redisPod -n "askrag-$Environment" -- redis-cli LASTSAVE
        } while ($saveTime -eq $saveTime)
        
        # Copy Redis dump
        kubectl cp "askrag-$Environment/$redisPod:/data/dump.rdb" (Join-Path $BackupPath "redis\redis-$Timestamp.rdb")
        
        Write-Success "Redis backup completed"
    }
    catch {
        Write-Error "Redis backup failed: $($_.Exception.Message)"
    }
}

# Backup uploaded files
function Backup-Uploads {
    param([string]$BackupPath)
    
    Write-Info "Backing up uploaded files..."
    
    try {
        $backendPod = kubectl get pods -n "askrag-$Environment" -l app=askrag-backend -o jsonpath='{.items[0].metadata.name}'
        
        if (-not $backendPod) {
            Write-Error "Backend pod not found"
            return
        }
        
        # Create tar archive of uploads
        kubectl exec $backendPod -n "askrag-$Environment" -- tar -czf /tmp/uploads-backup.tar.gz -C /app/uploads .
        
        # Copy uploads backup
        kubectl cp "askrag-$Environment/$backendPod:/tmp/uploads-backup.tar.gz" (Join-Path $BackupPath "uploads\uploads-$Timestamp.tar.gz")
        
        Write-Success "Uploads backup completed"
    }
    catch {
        Write-Error "Uploads backup failed: $($_.Exception.Message)"
    }
}

# Backup configurations
function Backup-Configs {
    param([string]$BackupPath)
    
    Write-Info "Backing up configurations..."
    
    try {
        # Backup secrets
        kubectl get secrets -n "askrag-$Environment" -o yaml | Out-File -FilePath (Join-Path $BackupPath "configs\secrets-$Timestamp.yaml") -Encoding UTF8
        
        # Backup configmaps
        kubectl get configmaps -n "askrag-$Environment" -o yaml | Out-File -FilePath (Join-Path $BackupPath "configs\configmaps-$Timestamp.yaml") -Encoding UTF8
        
        # Backup PVCs
        kubectl get pvc -n "askrag-$Environment" -o yaml | Out-File -FilePath (Join-Path $BackupPath "configs\pvcs-$Timestamp.yaml") -Encoding UTF8
        
        Write-Success "Configurations backup completed"
    }
    catch {
        Write-Error "Configurations backup failed: $($_.Exception.Message)"
    }
}

# Backup Kubernetes manifests
function Backup-K8sManifests {
    param([string]$BackupPath)
    
    Write-Info "Backing up Kubernetes manifests..."
    
    try {
        # Backup all resources in namespace
        kubectl get all,ingress,pvc,secrets,configmaps -n "askrag-$Environment" -o yaml | Out-File -FilePath (Join-Path $BackupPath "k8s\all-resources-$Timestamp.yaml") -Encoding UTF8
        
        # Backup specific deployments
        kubectl get deployment -n "askrag-$Environment" -o yaml | Out-File -FilePath (Join-Path $BackupPath "k8s\deployments-$Timestamp.yaml") -Encoding UTF8
        
        # Backup services
        kubectl get service -n "askrag-$Environment" -o yaml | Out-File -FilePath (Join-Path $BackupPath "k8s\services-$Timestamp.yaml") -Encoding UTF8
        
        # Backup HPA
        kubectl get hpa -n "askrag-$Environment" -o yaml | Out-File -FilePath (Join-Path $BackupPath "k8s\hpa-$Timestamp.yaml") -Encoding UTF8
        
        Write-Success "Kubernetes manifests backup completed"
    }
    catch {
        Write-Error "Kubernetes manifests backup failed: $($_.Exception.Message)"
    }
}

# Create backup metadata
function New-BackupMetadata {
    param([string]$BackupPath)
    
    Write-Info "Creating backup metadata..."
    
    $metadata = @{
        backup_id = $Timestamp
        environment = $Environment
        backup_type = $BackupType
        timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssK")
        created_by = $env:USERNAME
        components = @{
            mongodb = (Test-Path (Join-Path $BackupPath "mongodb\mongodb-$Timestamp.zip"))
            redis = (Test-Path (Join-Path $BackupPath "redis\redis-$Timestamp.rdb"))
            uploads = (Test-Path (Join-Path $BackupPath "uploads\uploads-$Timestamp.tar.gz"))
            configs = (Test-Path (Join-Path $BackupPath "configs\secrets-$Timestamp.yaml"))
            k8s = (Test-Path (Join-Path $BackupPath "k8s\all-resources-$Timestamp.yaml"))
        }
        backup_script_version = "1.0.0"
    }
    
    $metadata | ConvertTo-Json -Depth 10 | Out-File -FilePath (Join-Path $BackupPath "backup-metadata.json") -Encoding UTF8
    
    Write-Success "Backup metadata created"
}

# Finalize backup
function Complete-Backup {
    param([string]$BackupPath)
    
    Write-Info "Finalizing backup..."
    
    # Create final compressed archive
    $finalBackup = Join-Path $BackupDir "$Environment\askrag-$Environment-$BackupType-$Timestamp.zip"
    Compress-Archive -Path $BackupPath -DestinationPath $finalBackup
    
    # Calculate checksums
    $hash = Get-FileHash -Path $finalBackup -Algorithm SHA256
    $hash.Hash | Out-File -FilePath "$finalBackup.sha256" -Encoding UTF8
    
    # Remove temporary directory
    Remove-Item -Recurse -Force $BackupPath
    
    $backupSize = (Get-Item $finalBackup).Length / 1MB
    Write-Success "Backup finalized: $finalBackup"
    Write-Info "Backup size: $([math]::Round($backupSize, 2)) MB"
    Write-Info "Checksum: $($hash.Hash)"
}

# Send notification
function Send-Notification {
    param(
        [string]$Status,
        [string]$Message
    )
    
    if ($env:SLACK_WEBHOOK_URL) {
        try {
            $payload = @{ text = "AskRAG Backup $Status`: $Message" } | ConvertTo-Json
            Invoke-RestMethod -Uri $env:SLACK_WEBHOOK_URL -Method Post -Body $payload -ContentType "application/json"
        }
        catch {
            Write-Warning "Failed to send Slack notification: $($_.Exception.Message)"
        }
    }
}

# Main backup process
function Start-Backup {
    Write-Info "Starting AskRAG backup process"
    Write-Info "Environment: $Environment"
    Write-Info "Backup type: $BackupType"
    Write-Info "Timestamp: $Timestamp"
    
    try {
        $backupPath = New-BackupStructure
        
        switch ($BackupType) {
            "full" {
                Backup-MongoDB $backupPath
                Backup-Redis $backupPath
                Backup-Uploads $backupPath
                Backup-Configs $backupPath
                Backup-K8sManifests $backupPath
            }
            "incremental" {
                Backup-MongoDB $backupPath
                Backup-Uploads $backupPath
            }
            "config-only" {
                Backup-Configs $backupPath
                Backup-K8sManifests $backupPath
            }
        }
        
        New-BackupMetadata $backupPath
        Complete-Backup $backupPath
        
        $successMessage = "Backup completed successfully for $Environment environment"
        Write-Success $successMessage
        Send-Notification "SUCCESS" $successMessage
    }
    catch {
        $errorMessage = "Backup failed for $Environment environment: $($_.Exception.Message)"
        Write-Error $errorMessage
        Send-Notification "FAILED" $errorMessage
        throw
    }
}

# Run backup
Start-Backup
