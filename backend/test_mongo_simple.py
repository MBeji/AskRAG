"""
Test MongoDB connection simple - sans FastAPI
"""
import pymongo
import os
from datetime import datetime

def test_basic_connection():
    """Test de connexion MongoDB basique"""
    try:
        # URL MongoDB par défaut
        mongodb_url = "mongodb://localhost:27017"
        print(f"🔗 Tentative de connexion à: {mongodb_url}")
        
        # Connexion client
        client = pymongo.MongoClient(mongodb_url, serverSelectionTimeoutMS=5000)
        
        # Test ping
        client.admin.command('ping')
        print("✅ Connexion MongoDB réussie!")
        
        # Test base de données
        db = client["askrag_test"]
        collection = db["test_collection"]
        
        # Insert test
        test_doc = {
            "test": "hello",
            "timestamp": datetime.utcnow(),
            "message": "MongoDB fonctionne!"
        }
        
        result = collection.insert_one(test_doc)
        print(f"✅ Document inséré avec ID: {result.inserted_id}")
        
        # Read test
        found_doc = collection.find_one({"test": "hello"})
        print(f"✅ Document trouvé: {found_doc['message']}")
        
        # Cleanup
        collection.delete_one({"_id": result.inserted_id})
        print("✅ Document supprimé")
        
        # Fermer connexion
        client.close()
        print("✅ Connexion fermée")
        
        return True
        
    except pymongo.errors.ServerSelectionTimeoutError:
        print("❌ MongoDB n'est pas démarré ou n'est pas accessible")
        print("💡 Vérifiez que MongoDB est installé et démarré")
        return False
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def check_mongodb_status():
    """Vérifier si MongoDB est installé et accessible"""
    try:
        import subprocess
        
        # Essayer de voir si MongoDB est en cours d'exécution
        print("🔍 Vérification du statut MongoDB...")
        
        # Pour Windows, vérifier les services
        result = subprocess.run(
            ['sc', 'query', 'MongoDB'], 
            capture_output=True, 
            text=True
        )
        
        if "RUNNING" in result.stdout:
            print("✅ Service MongoDB est en cours d'exécution")
            return True
        elif "STOPPED" in result.stdout:
            print("⚠️ Service MongoDB est arrêté")
            print("💡 Démarrez le service avec: net start MongoDB")
            return False
        else:
            print("❓ Service MongoDB non trouvé")
            return False
            
    except Exception as e:
        print(f"⚠️ Impossible de vérifier le statut: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🧪 TEST MONGODB SIMPLE")
    print("=" * 50)
    
    # Étape 1: Vérifier le statut
    print("\n📋 Étape 1: Vérification du statut MongoDB")
    mongodb_running = check_mongodb_status()
    
    # Étape 2: Test de connexion
    print("\n📋 Étape 2: Test de connexion")
    if test_basic_connection():
        print("\n🎉 TOUS LES TESTS RÉUSSIS!")
        print("MongoDB est prêt pour l'intégration FastAPI")
    else:
        print("\n💥 ÉCHEC DES TESTS")
        print("Veuillez installer/démarrer MongoDB avant de continuer")
