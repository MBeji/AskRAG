# Configuration simple Git Bash pour VS Code
Write-Host "Configuration Git Bash..." -ForegroundColor Green

# Chemin vers les paramètres VS Code
$settingsPath = "$env:APPDATA\Code\User\settings.json"

# Configuration minimale
$config = @'
{
    "terminal.integrated.defaultProfile.windows": "Git Bash",
    "terminal.integrated.profiles.windows": {
        "Git Bash": {
            "path": "C:\\Program Files\\Git\\bin\\bash.exe"
        }
    }
}
'@

# Écrire la configuration
$config | Out-File -FilePath $settingsPath -Encoding UTF8 -Force

Write-Host "Configuration appliquée à : $settingsPath" -ForegroundColor Green
Write-Host "Redémarrez VS Code pour appliquer les changements" -ForegroundColor Yellow
