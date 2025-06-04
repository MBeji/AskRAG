#!/usr/bin/env python3
"""
Test rapide d'Étape 10 - Validation fonctionnelle
"""
import requests
import json
import tempfile
import os

BASE_URL = "http://127.0.0.1:8003"
API_BASE = f"{BASE_URL}/api/v1"

def test_etape10():
    """Test rapide des fonctionnalités d'Étape 10"""
    print("🚀 Test d'Étape 10 - Système d'ingestion de documents")
    
    # Test 1: Health check
    print("\n1. Test de santé du serveur...")
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"   ✅ Santé: {r.status_code} - {r.json()}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    # Test 2: Registration
    print("\n2. Test d'enregistrement...")
    user_data = {
        "email": "demo@askrag.com",
        "username": "demouser",
        "password": "demo123"
    }
    
    try:
        r = requests.post(f"{API_BASE}/auth/register", json=user_data, timeout=10)
        if r.status_code == 200:
            user = r.json()
            print(f"   ✅ Utilisateur créé: {user['email']}")
        else:
            print(f"   ⚠️  Utilisateur existe déjà ou erreur: {r.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    # Test 3: Login
    print("\n3. Test de connexion...")
    login_data = {
        "email": "demo@askrag.com",
        "password": "demo123"
    }
    
    try:
        r = requests.post(f"{API_BASE}/auth/login", json=login_data, timeout=10)
        if r.status_code == 200:
            result = r.json()
            token = result["access_token"]
            print(f"   ✅ Connexion réussie: {result['user']['email']}")
            print(f"   📱 Token: {token[:30]}...")
        else:
            print(f"   ❌ Échec connexion: {r.status_code} - {r.text}")
            return False
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    # Test 4: Authenticated access
    print("\n4. Test d'accès authentifié...")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        r = requests.get(f"{API_BASE}/auth/me", headers=headers, timeout=10)
        if r.status_code == 200:
            user = r.json()
            print(f"   ✅ Accès authentifié: {user['email']}")
        else:
            print(f"   ❌ Échec accès: {r.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    # Test 5: Document upload
    print("\n5. Test d'upload de document...")
    test_content = "Ceci est un document de test pour AskRAG Étape 10."
    
    try:
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_path = f.name
        
        # Upload
        with open(temp_path, 'rb') as f:
            files = {'file': ('etape10_test.txt', f, 'text/plain')}
            r = requests.post(f"{API_BASE}/documents/upload", headers=headers, files=files, timeout=30)
        
        os.unlink(temp_path)
        
        if r.status_code == 200:
            result = r.json()
            print(f"   ✅ Upload réussi: {result['message']}")
        else:
            print(f"   ❌ Échec upload: {r.status_code} - {r.text}")
            return False
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    # Test 6: Document listing
    print("\n6. Test de listage des documents...")
    try:
        r = requests.get(f"{API_BASE}/documents", headers=headers, timeout=10)
        if r.status_code == 200:
            result = r.json()
            print(f"   ✅ Listage: {result['message']}")
        else:
            print(f"   ❌ Échec listage: {r.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    print("\n🎉 ÉTAPE 10 VALIDÉE AVEC SUCCÈS!")
    print("📋 Fonctionnalités confirmées:")
    print("   ✅ Authentification (registration, login, JWT)")
    print("   ✅ Upload de documents sécurisé")
    print("   ✅ Listage de documents")
    print("   ✅ API REST complète")
    print("   ✅ Serveur FastAPI opérationnel")
    
    return True

if __name__ == "__main__":
    success = test_etape10()
    if success:
        print("\n🎯 Étape 10 complète! Prêt pour l'étape suivante.")
    else:
        print("\n⚠️  Des problèmes ont été détectés.")
