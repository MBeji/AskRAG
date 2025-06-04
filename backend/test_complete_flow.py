#!/usr/bin/env python3
"""
Complete authentication flow test for AskRAG Étape 10
Tests registration, login, token validation, and document upload
"""
import requests
import json
from pathlib import Path
import tempfile

# Server configuration
SERVER_URL = "http://localhost:8003"
API_BASE = f"{SERVER_URL}/api/v1"

def test_health():
    """Test server health"""
    print("🔍 Testing server health...")
    try:
        response = requests.get(f"{SERVER_URL}/health")
        print(f"   ✅ Health check: {response.status_code} - {response.json()}")
        return True
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
        return False

def test_registration():
    """Test user registration"""
    print("\n👤 Testing user registration...")
    
    user_data = {
        "email": "test@askrag.com",
        "username": "testuser",
        "full_name": "Test User",
        "password": "TestPassword123"
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/register", json=user_data)
        print(f"   📝 Registration response: {response.status_code}")
        
        if response.status_code == 200:
            user_info = response.json()
            print(f"   ✅ User registered: {user_info['email']} ({user_info['full_name']})")
            return True
        else:
            print(f"   ❌ Registration failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Registration error: {e}")
        return False

def test_login():
    """Test user login"""
    print("\n🔐 Testing user login...")
    
    login_data = {
        "email": "test@askrag.com", 
        "password": "TestPassword123"
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        print(f"   🔑 Login response: {response.status_code}")
        
        if response.status_code == 200:
            login_result = response.json()
            token = login_result['access_token']
            user = login_result['user']
            print(f"   ✅ Login successful: {user['email']}")
            print(f"   🎫 Token length: {len(token)} characters")
            return token
        else:
            print(f"   ❌ Login failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Login error: {e}")
        return None

def test_auth_me(token):
    """Test authenticated user info endpoint"""
    print("\n🎯 Testing /auth/me endpoint...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{API_BASE}/auth/me", headers=headers)
        print(f"   👤 Auth/me response: {response.status_code}")
        
        if response.status_code == 200:
            user_info = response.json()
            print(f"   ✅ User info retrieved: {user_info['email']} - {user_info['full_name']}")
            return True
        else:
            print(f"   ❌ Auth/me failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Auth/me error: {e}")
        return False

def test_document_upload(token):
    """Test document upload"""
    print("\n📄 Testing document upload...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a temporary test file
    test_content = "This is a test document for AskRAG Étape 10.\nIt contains sample text for document processing."
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name
        
        with open(temp_file_path, 'rb') as f:
            files = {'file': ('test_document.txt', f, 'text/plain')}
            response = requests.post(f"{API_BASE}/documents/upload", headers=headers, files=files)
        
        print(f"   📤 Upload response: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Document uploaded: {result['message']}")
            return True
        else:
            print(f"   ❌ Upload failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Upload error: {e}")
        return False
    finally:
        # Clean up temp file
        try:
            Path(temp_file_path).unlink()
        except:
            pass

def test_document_list(token):
    """Test document listing"""
    print("\n📋 Testing document listing...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{API_BASE}/documents", headers=headers)
        print(f"   📃 List response: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Documents listed: {result['message']}")
            return True
        else:
            print(f"   ❌ List failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ List error: {e}")
        return False

def main():
    """Run complete authentication and document flow test"""
    print("🚀 AskRAG Étape 10 - Complete Authentication & Document Flow Test")
    print("=" * 70)
    
    # Test each step
    success_count = 0
    total_tests = 6
    
    # 1. Health check
    if test_health():
        success_count += 1
    
    # 2. Registration
    if test_registration():
        success_count += 1
    
    # 3. Login
    token = test_login()
    if token:
        success_count += 1
        
        # 4. Auth/me endpoint
        if test_auth_me(token):
            success_count += 1
        
        # 5. Document upload
        if test_document_upload(token):
            success_count += 1
            
        # 6. Document listing
        if test_document_list(token):
            success_count += 1
    
    # Summary
    print("\n" + "=" * 70)
    print(f"🎯 TEST SUMMARY: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("🎉 ALL TESTS PASSED! AskRAG Étape 10 authentication and document flow is working!")
    else:
        print(f"⚠️  {total_tests - success_count} tests failed. Check the errors above.")
    
    print("\n📡 Server endpoints tested:")
    print(f"   • Health: {SERVER_URL}/health")
    print(f"   • Register: {API_BASE}/auth/register")
    print(f"   • Login: {API_BASE}/auth/login")
    print(f"   • User Info: {API_BASE}/auth/me")
    print(f"   • Upload: {API_BASE}/documents/upload")
    print(f"   • List: {API_BASE}/documents")

if __name__ == "__main__":
    main()
