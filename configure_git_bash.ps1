# Configuration Git Bash comme terminal par défaut dans VS Code
# Script PowerShell pour Windows

Write-Host "Configuration de Git Bash comme terminal par défaut dans VS Code..." -ForegroundColor Green

# Vérifier si Git est installé
$gitPath = "C:\Program Files\Git\bin\bash.exe"
if (Test-Path $gitPath) {
    Write-Host "✅ Git Bash trouvé à : $gitPath" -ForegroundColor Green
} else {
    Write-Host "❌ Git Bash non trouvé. Veuillez installer Git for Windows." -ForegroundColor Red
    exit 1
}

# Créer le répertoire de configuration VS Code s'il n'existe pas
$vsCodeConfigDir = "$env:APPDATA\Code\User"
if (!(Test-Path $vsCodeConfigDir)) {
    New-Item -ItemType Directory -Path $vsCodeConfigDir -Force
    Write-Host "📁 Répertoire de configuration VS Code créé" -ForegroundColor Yellow
}

# Configuration JSON pour VS Code
$settingsPath = "$vsCodeConfigDir\settings.json"
$gitBashConfig = @{
    "terminal.integrated.defaultProfile.windows" = "Git Bash"
    "terminal.integrated.profiles.windows" = @{
        "PowerShell" = @{
            "source" = "PowerShell"
            "icon" = "terminal-powershell"
        }
        "Command Prompt" = @{
            "path" = @(
                "${env:windir}\Sysnative\cmd.exe",
                "${env:windir}\System32\cmd.exe"
            )
            "args" = @()
            "icon" = "terminal-cmd"
        }
        "Git Bash" = @{
            "path" = "C:\Program Files\Git\bin\bash.exe"
            "args" = @()
            "icon" = "terminal-bash"
        }
    }
}

# Lire les paramètres existants s'ils existent
$existingSettings = @{}
if (Test-Path $settingsPath) {
    try {
        $existingSettings = Get-Content $settingsPath -Raw | ConvertFrom-Json -AsHashtable
        Write-Host "📖 Paramètres existants lus" -ForegroundColor Yellow
    } catch {
        Write-Host "⚠️ Impossible de lire les paramètres existants, création de nouveaux paramètres" -ForegroundColor Yellow
    }
}

# Fusionner les configurations
foreach ($key in $gitBashConfig.Keys) {
    $existingSettings[$key] = $gitBashConfig[$key]
}

# Écrire la configuration
try {
    $existingSettings | ConvertTo-Json -Depth 10 | Set-Content $settingsPath -Encoding UTF8
    Write-Host "✅ Configuration Git Bash appliquée avec succès!" -ForegroundColor Green
    Write-Host "📍 Fichier de configuration : $settingsPath" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Erreur lors de l'écriture de la configuration : $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n🔄 Redémarrez VS Code pour appliquer les changements" -ForegroundColor Magenta
Write-Host "🚀 Une fois redémarré, Git Bash sera le terminal par défaut" -ForegroundColor Green

# Instructions supplémentaires
Write-Host "`n📋 Instructions:" -ForegroundColor Cyan
Write-Host "1. Fermez complètement VS Code" -ForegroundColor White
Write-Host "2. Rouvrez VS Code" -ForegroundColor White
Write-Host "3. Ouvrez un nouveau terminal (Ctrl+Shift+`)" -ForegroundColor White
Write-Host "4. Git Bash devrait maintenant être le terminal par défaut" -ForegroundColor White

Write-Host "`n✨ Configuration terminée!" -ForegroundColor Green
