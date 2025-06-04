# Script d'installation MongoDB pour Windows

Write-Host "🚀 Installation MongoDB Community Edition" -ForegroundColor Green
Write-Host "=" * 50

# Vérifier si MongoDB est déjà installé
$mongoPath = "C:\Program Files\MongoDB\Server\*\bin\mongod.exe"
if (Test-Path $mongoPath) {
    Write-Host "✅ MongoDB semble déjà installé" -ForegroundColor Green
    Write-Host "📂 Trouvé dans: $mongoPath"
    
    # Vérifier si le service existe
    $service = Get-Service -Name "MongoDB" -ErrorAction SilentlyContinue
    if ($service) {
        Write-Host "✅ Service MongoDB trouvé. Statut: $($service.Status)" -ForegroundColor Green
        if ($service.Status -eq "Stopped") {
            Write-Host "🔄 Démarrage du service MongoDB..." -ForegroundColor Yellow
            Start-Service -Name "MongoDB"
            Write-Host "✅ Service MongoDB démarré" -ForegroundColor Green
        }
    } else {
        Write-Host "⚠️ Service MongoDB non trouvé" -ForegroundColor Yellow
    }
    exit
}

Write-Host "🔽 MongoDB non trouvé. Installation requise." -ForegroundColor Yellow
Write-Host ""
Write-Host "OPTIONS D'INSTALLATION:" -ForegroundColor Cyan
Write-Host "1. 🏢 Installation complète MongoDB Community Server (recommandé)"
Write-Host "2. 🐳 Utiliser MongoDB via Docker (plus simple)"
Write-Host "3. 🌐 Utiliser MongoDB Atlas (cloud, gratuit)"
Write-Host ""

$choice = Read-Host "Choisissez une option (1, 2, ou 3)"

switch ($choice) {
    "1" {
        Write-Host "🏢 Installation MongoDB Community Server..." -ForegroundColor Green
        Write-Host ""
        Write-Host "ÉTAPES MANUELLES REQUISES:" -ForegroundColor Yellow
        Write-Host "1. Allez sur: https://www.mongodb.com/try/download/community"
        Write-Host "2. Téléchargez MongoDB Community Server pour Windows"
        Write-Host "3. Exécutez l'installateur (.msi)"
        Write-Host "4. Suivez l'assistant d'installation"
        Write-Host "5. Assurez-vous de cocher 'Install MongoDB as a Service'"
        Write-Host "6. Relancez ce script après l'installation"
        
        $open = Read-Host "Ouvrir la page de téléchargement maintenant? (o/n)"
        if ($open -eq "o" -or $open -eq "O") {
            Start-Process "https://www.mongodb.com/try/download/community"
        }
    }
    
    "2" {
        Write-Host "🐳 Configuration MongoDB avec Docker..." -ForegroundColor Green
        
        # Vérifier Docker
        try {
            docker --version | Out-Null
            Write-Host "✅ Docker détecté" -ForegroundColor Green
            
            Write-Host "🔄 Démarrage container MongoDB..." -ForegroundColor Yellow
            
            # Créer et démarrer container MongoDB
            $dockerCmd = @"
docker run -d --name askrag-mongodb `
    -p 27017:27017 `
    -e MONGO_INITDB_ROOT_USERNAME=admin `
    -e MONGO_INITDB_ROOT_PASSWORD=admin123 `
    -e MONGO_INITDB_DATABASE=askrag_db `
    mongo:latest
"@
            
            Invoke-Expression $dockerCmd
            
            Write-Host "✅ Container MongoDB démarré!" -ForegroundColor Green
            Write-Host "📝 Informations de connexion:" -ForegroundColor Cyan
            Write-Host "   URL: mongodb://admin:admin123@localhost:27017/askrag_db"
            Write-Host "   Username: admin"
            Write-Host "   Password: admin123"
            
        } catch {
            Write-Host "❌ Docker non trouvé ou erreur" -ForegroundColor Red
            Write-Host "💡 Installez Docker Desktop: https://www.docker.com/products/docker-desktop"
        }
    }
    
    "3" {
        Write-Host "🌐 Configuration MongoDB Atlas (cloud)..." -ForegroundColor Green
        Write-Host ""
        Write-Host "ÉTAPES POUR MONGODB ATLAS:" -ForegroundColor Yellow
        Write-Host "1. Allez sur: https://www.mongodb.com/atlas"
        Write-Host "2. Créez un compte gratuit"
        Write-Host "3. Créez un cluster gratuit"
        Write-Host "4. Configurez l'accès réseau (Allow access from anywhere)"
        Write-Host "5. Créez un utilisateur de base de données"
        Write-Host "6. Récupérez la chaîne de connexion"
        Write-Host "7. Mettez à jour le fichier .env avec votre URL"
        
        $open = Read-Host "Ouvrir MongoDB Atlas maintenant? (o/n)"
        if ($open -eq "o" -or $open -eq "O") {
            Start-Process "https://www.mongodb.com/atlas"
        }
    }
    
    default {
        Write-Host "❌ Option invalide" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "🔄 Après installation, relancez: python test_mongo_simple.py" -ForegroundColor Cyan
