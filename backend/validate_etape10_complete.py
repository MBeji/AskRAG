#!/usr/bin/env python3
"""
Validation complète d'Étape 10 - Test du système d'ingestion de documents
"""
import requests
import json
import os
import tempfile
from pathlib import Path

# Configuration du serveur
BASE_URL = "http://127.0.0.1:8003"
API_BASE = f"{BASE_URL}/api/v1"

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_step(step, description):
    """Print a formatted step"""
    print(f"\n🔹 Étape {step}: {description}")

def print_success(message):
    """Print success message"""
    print(f"✅ {message}")

def print_error(message):
    """Print error message"""
    print(f"❌ {message}")

def print_info(message):
    """Print info message"""
    print(f"📋 {message}")

def test_server_health():
    """Test server health and basic endpoints"""
    print_step(1, "Test de santé du serveur")
    
    try:
        # Test health endpoint
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print_success(f"Health check: {response.json()}")
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False
        
        # Test root endpoint
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print_success(f"Root endpoint: {response.json()}")
        else:
            print_error(f"Root endpoint failed: {response.status_code}")
            return False
        
        # Test API docs
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print_success("API documentation accessible")
        else:
            print_error(f"API docs failed: {response.status_code}")
        
        return True
        
    except requests.RequestException as e:
        print_error(f"Erreur de connexion au serveur: {e}")
        return False

def test_user_registration():
    """Test user registration"""
    print_step(2, "Test d'enregistrement d'utilisateur")
    
    # Test data
    user_data = {
        "email": "test@askrag.com",
        "username": "testuser",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/auth/register",
            json=user_data,
            timeout=10
        )
        
        if response.status_code == 200:
            user_info = response.json()
            print_success(f"Utilisateur créé: {user_info['email']}")
            print_info(f"ID utilisateur: {user_info['id']}")
            return user_info
        else:
            print_error(f"Échec de l'enregistrement: {response.status_code} - {response.text}")
            return None
            
    except requests.RequestException as e:
        print_error(f"Erreur lors de l'enregistrement: {e}")
        return None

def test_user_login(email, password):
    """Test user login"""
    print_step(3, "Test de connexion utilisateur")
    
    login_data = {
        "email": email,
        "password": password
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/auth/login",
            json=login_data,
            timeout=10
        )
        
        if response.status_code == 200:
            login_result = response.json()
            token = login_result["access_token"]
            user_info = login_result["user"]
            print_success(f"Connexion réussie pour: {user_info['email']}")
            print_info(f"Token généré: {token[:50]}...")
            return token
        else:
            print_error(f"Échec de la connexion: {response.status_code} - {response.text}")
            return None
            
    except requests.RequestException as e:
        print_error(f"Erreur lors de la connexion: {e}")
        return None

def test_authenticated_access(token):
    """Test authenticated access to user info"""
    print_step(4, "Test d'accès authentifié")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(
            f"{API_BASE}/auth/me",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            user_info = response.json()
            print_success(f"Informations utilisateur récupérées: {user_info['email']}")
            return True
        else:
            print_error(f"Échec d'accès authentifié: {response.status_code} - {response.text}")
            return False
            
    except requests.RequestException as e:
        print_error(f"Erreur lors de l'accès authentifié: {e}")
        return False

def test_document_upload(token):
    """Test document upload"""
    print_step(5, "Test d'upload de document")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # Create a test document
    test_content = """
    Ceci est un document de test pour AskRAG.
    
    Il contient du texte qui devrait être traité par le système d'ingestion.
    
    Points clés:
    - Test de l'upload
    - Validation de l'authentification
    - Vérification du stockage
    
    Date: 2025-05-28
    Auteur: Système de test automatisé
    """
    
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_file_path = f.name
        
        # Upload the file
        with open(temp_file_path, 'rb') as f:
            files = {'file': ('test_document.txt', f, 'text/plain')}
            response = requests.post(
                f"{API_BASE}/documents/upload",
                headers=headers,
                files=files,
                timeout=30
            )
        
        # Clean up temp file
        os.unlink(temp_file_path)
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"Document uploadé: {result['message']}")
            return True
        else:
            print_error(f"Échec de l'upload: {response.status_code} - {response.text}")
            return False
            
    except requests.RequestException as e:
        print_error(f"Erreur lors de l'upload: {e}")
        return False
    except Exception as e:
        print_error(f"Erreur générale lors de l'upload: {e}")
        return False

def test_document_listing(token):
    """Test document listing"""
    print_step(6, "Test de listage des documents")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(
            f"{API_BASE}/documents",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"Documents listés: {result['message']}")
            return True
        else:
            print_error(f"Échec du listage: {response.status_code} - {response.text}")
            return False
            
    except requests.RequestException as e:
        print_error(f"Erreur lors du listage: {e}")
        return False

def validate_etape10():
    """Run complete Étape 10 validation"""
    print_section("🚀 VALIDATION ÉTAPE 10 - SYSTÈME D'INGESTION DE DOCUMENTS")
    
    # Counters
    tests_passed = 0
    total_tests = 6
    
    # Test 1: Server health
    if test_server_health():
        tests_passed += 1
    
    # Test 2: User registration
    user_info = test_user_registration()
    if user_info:
        tests_passed += 1
        email = user_info["email"]
        password = "testpassword123"
    else:
        print_error("Impossible de continuer sans utilisateur")
        return False
    
    # Test 3: User login
    token = test_user_login(email, password)
    if token:
        tests_passed += 1
    else:
        print_error("Impossible de continuer sans token")
        return False
    
    # Test 4: Authenticated access
    if test_authenticated_access(token):
        tests_passed += 1
    
    # Test 5: Document upload
    if test_document_upload(token):
        tests_passed += 1
    
    # Test 6: Document listing
    if test_document_listing(token):
        tests_passed += 1
    
    # Final results
    print_section("📊 RÉSULTATS DE VALIDATION")
    print(f"Tests réussis: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print_success("🎉 ÉTAPE 10 COMPLÈTEMENT VALIDÉE!")
        print_info("✅ Authentification fonctionnelle")
        print_info("✅ Upload de documents fonctionnel")
        print_info("✅ Listage de documents fonctionnel")
        print_info("✅ Sécurité JWT implémentée")
        print_info("✅ API REST complète")
        return True
    else:
        print_error(f"❌ Validation incomplète: {total_tests - tests_passed} tests échoués")
        return False

if __name__ == "__main__":
    print("🔍 Démarrage de la validation d'Étape 10...")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print_error("Le serveur ne répond pas correctement. Assurez-vous qu'il fonctionne sur http://127.0.0.1:8003")
            exit(1)
    except requests.RequestException:
        print_error("Le serveur n'est pas accessible. Démarrez-le avec:")
        print_info("cd d:\\11-coding\\AskRAG\\backend")
        print_info("uvicorn simple_etape10_server:app --host 127.0.0.1 --port 8003")
        exit(1)
    
    # Run validation
    success = validate_etape10()
    
    if success:
        print("\n🎯 Prochaines étapes recommandées:")
        print("1. Implémenter le traitement des documents (chunking, embedding)")
        print("2. Ajouter la recherche vectorielle")
        print("3. Intégrer le système de chat/questions-réponses")
        exit(0)
    else:
        print("\n🔧 Actions à corriger avant de continuer")
        exit(1)
