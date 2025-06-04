"""
ÉTAPE 5: Configuration Docker - Validation Finale
Vérification de tous les fichiers Docker créés
"""

import os
from pathlib import Path

def check_files():
    """Vérifier tous les fichiers Docker créés"""
    
    print("🐳 ÉTAPE 5: Configuration Docker - VALIDATION FINALE")
    print("=" * 60)
    
    # Liste des fichiers Docker à vérifier
    docker_files = [
        # Docker Compose
        ("docker-compose.yml", "Configuration production"),
        ("docker-compose.dev.yml", "Configuration développement"),
        
        # Environment files
        (".env.docker", "Variables environnement production"),
        (".env.docker.dev", "Variables environnement développement"),
        
        # Backend Docker
        ("backend/Dockerfile", "Dockerfile production backend"),
        ("backend/Dockerfile.dev", "Dockerfile développement backend"),
        ("backend/.dockerignore", "Docker ignore backend"),
        
        # Frontend Docker  
        ("frontend/Dockerfile", "Dockerfile production frontend"),
        ("frontend/Dockerfile.dev", "Dockerfile développement frontend"),
        ("frontend/.dockerignore", "Docker ignore frontend"),
        ("frontend/nginx.conf", "Configuration Nginx"),
        
        # Scripts
        ("scripts/mongo-init.js", "Script initialisation MongoDB"),
        ("scripts/docker-helper.sh", "Script utilitaire Linux"),
        ("scripts/docker-helper.ps1", "Script utilitaire PowerShell"),
    ]
    
    created_files = 0
    total_files = len(docker_files)
    
    print("\n📋 VÉRIFICATION DES FICHIERS DOCKER:")
    print("-" * 60)
    
    for file_path, description in docker_files:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"✅ {file_path:<35} ({file_size:>6} bytes) - {description}")
            created_files += 1
        else:
            print(f"❌ {file_path:<35} - MANQUANT - {description}")
    
    print("\n" + "=" * 60)
    print(f"📊 RÉSULTAT: {created_files}/{total_files} fichiers créés ({created_files/total_files*100:.0f}%)")
    
    if created_files == total_files:
        print("🎉 SUCCÈS: Tous les fichiers Docker ont été créés!")
        
        print("\n📝 PROCHAINES ÉTAPES:")
        print("1. Installer Docker Desktop (si pas déjà fait)")
        print("2. Configurer les variables d'environnement dans .env")
        print("3. Démarrer l'environnement de développement:")
        print("   docker-compose -f docker-compose.dev.yml up --build")
        print("\n🌐 SERVICES DISPONIBLES:")
        print("   - Frontend:  http://localhost:5173")
        print("   - Backend:   http://localhost:8000")
        print("   - MongoDB:   localhost:27017")
        print("   - Redis:     localhost:6379")
        
        print("\n🔧 UTILISATION DES SCRIPTS:")
        print("   Windows: .\\scripts\\docker-helper.ps1 dev")
        print("   Linux:   ./scripts/docker-helper.sh dev")
        
    else:
        print("❌ ÉCHEC: Certains fichiers sont manquants")
        
    return created_files == total_files

if __name__ == "__main__":
    success = check_files()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ ÉTAPE 5 COMPLÉTÉE AVEC SUCCÈS!")
        print("➡️  Prêt pour Étape 6: Variables d'environnement")
    else:
        print("❌ ÉTAPE 5 INCOMPLÈTE - Vérifier les fichiers manquants")
