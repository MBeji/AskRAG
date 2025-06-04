#!/usr/bin/env python3
"""
Complete AskRAG Étape 10 Validation Script
Tests authentication, document upload, and all functionality
"""

print("=" * 70)
print("🚀 AskRAG ÉTAPE 10 - COMPLETE VALIDATION")
print("=" * 70)

# Test 1: Server Health Check
print("\n1. 🔍 Testing Server Health...")
try:
    import requests
    response = requests.get("http://localhost:8003/health", timeout=5)
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Server is healthy: {result['message']}")
        health_ok = True
    else:
        print(f"   ❌ Health check failed: {response.status_code}")
        health_ok = False
except Exception as e:
    print(f"   ❌ Health check error: {e}")
    health_ok = False

if not health_ok:
    print("\n❌ VALIDATION FAILED: Server is not responding")
    exit(1)

# Test 2: User Registration
print("\n2. 👤 Testing User Registration...")
user_data = {
    "email": "etape10@askrag.com",
    "username": "etape10user",
    "full_name": "Étape 10 Test User", 
    "password": "EtapePassword123!"
}

try:
    response = requests.post("http://localhost:8003/api/v1/auth/register", json=user_data, timeout=10)
    if response.status_code == 200:
        user_result = response.json()
        print(f"   ✅ User registered successfully")
        print(f"      Email: {user_result['email']}")
        print(f"      Name: {user_result['full_name']}")
        print(f"      User ID: {user_result['id']}")
        registration_ok = True
    elif response.status_code == 400 and "already registered" in response.text:
        print(f"   ⚠️ User already exists, continuing with login test")
        registration_ok = True
    else:
        print(f"   ❌ Registration failed: {response.status_code}")
        print(f"      Error: {response.text}")
        registration_ok = False
except Exception as e:
    print(f"   ❌ Registration error: {e}")
    registration_ok = False

# Test 3: User Login
print("\n3. 🔐 Testing User Login...")
login_data = {
    "email": "etape10@askrag.com",
    "password": "EtapePassword123!"
}

token = None
try:
    response = requests.post("http://localhost:8003/api/v1/auth/login", json=login_data, timeout=10)
    if response.status_code == 200:
        login_result = response.json()
        token = login_result['access_token']
        user_info = login_result['user']
        print(f"   ✅ Login successful")
        print(f"      User: {user_info['email']}")
        print(f"      Token: {token[:30]}...")
        login_ok = True
    else:
        print(f"   ❌ Login failed: {response.status_code}")
        print(f"      Error: {response.text}")
        login_ok = False
except Exception as e:
    print(f"   ❌ Login error: {e}")
    login_ok = False

# Test 4: Token Validation (/auth/me)
if token:
    print("\n4. 🎯 Testing Token Validation...")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get("http://localhost:8003/api/v1/auth/me", headers=headers, timeout=10)
        if response.status_code == 200:
            me_result = response.json()
            print(f"   ✅ Token validation successful")
            print(f"      Authenticated as: {me_result['email']}")
            print(f"      Full name: {me_result['full_name']}")
            token_ok = True
        else:
            print(f"   ❌ Token validation failed: {response.status_code}")
            print(f"      Error: {response.text}")
            token_ok = False
    except Exception as e:
        print(f"   ❌ Token validation error: {e}")
        token_ok = False
else:
    print("\n4. ⏭️ Skipping token validation (no token available)")
    token_ok = False

# Test 5: Document Upload
if token:
    print("\n5. 📄 Testing Document Upload...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test document
    test_content = """AskRAG Étape 10 Test Document
    
This is a test document for validating the document upload functionality.
It contains sample text that can be processed by the document ingestion system.

Key features being tested:
- Authentication-protected upload
- File storage functionality
- User-specific document management

Date: May 28, 2025
Test: Étape 10 Complete Validation
"""
    
    try:
        files = {'file': ('etape10_test.txt', test_content, 'text/plain')}
        response = requests.post("http://localhost:8003/api/v1/documents/upload", headers=headers, files=files, timeout=10)
        
        if response.status_code == 200:
            upload_result = response.json()
            print(f"   ✅ Document upload successful")
            print(f"      Message: {upload_result['message']}")
            upload_ok = True
        else:
            print(f"   ❌ Document upload failed: {response.status_code}")
            print(f"      Error: {response.text}")
            upload_ok = False
    except Exception as e:
        print(f"   ❌ Document upload error: {e}")
        upload_ok = False
else:
    print("\n5. ⏭️ Skipping document upload (no valid token)")
    upload_ok = False

# Test 6: Document Listing
if token:
    print("\n6. 📋 Testing Document Listing...")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get("http://localhost:8003/api/v1/documents", headers=headers, timeout=10)
        if response.status_code == 200:
            list_result = response.json()
            print(f"   ✅ Document listing successful")
            print(f"      Message: {list_result['message']}")
            list_ok = True
        else:
            print(f"   ❌ Document listing failed: {response.status_code}")
            print(f"      Error: {response.text}")
            list_ok = False
    except Exception as e:
        print(f"   ❌ Document listing error: {e}")
        list_ok = False
else:
    print("\n6. ⏭️ Skipping document listing (no valid token)")
    list_ok = False

# Final Summary
print("\n" + "=" * 70)
print("📊 VALIDATION SUMMARY")
print("=" * 70)

tests = [
    ("Server Health", health_ok),
    ("User Registration", registration_ok),
    ("User Login", login_ok),
    ("Token Validation", token_ok),
    ("Document Upload", upload_ok),
    ("Document Listing", list_ok)
]

passed_tests = sum(1 for _, success in tests if success)
total_tests = len(tests)

for test_name, success in tests:
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"   {test_name:<20} {status}")

print(f"\n🎯 OVERALL RESULT: {passed_tests}/{total_tests} tests passed")

if passed_tests == total_tests:
    print("\n🎉 CONGRATULATIONS! AskRAG Étape 10 is fully functional!")
    print("   ✅ Authentication system working")
    print("   ✅ Document upload working")
    print("   ✅ User management working")
    print("   ✅ API endpoints responding correctly")
elif passed_tests >= 4:
    print("\n✨ GOOD PROGRESS! Core functionality is working.")
    print("   Some advanced features may need attention.")
else:
    print("\n⚠️ ISSUES DETECTED: Core functionality needs work.")

print("\n📡 API Endpoints tested:")
print("   • GET  /health")
print("   • POST /api/v1/auth/register") 
print("   • POST /api/v1/auth/login")
print("   • GET  /api/v1/auth/me")
print("   • POST /api/v1/documents/upload")
print("   • GET  /api/v1/documents")

print(f"\n📚 FastAPI Documentation: http://localhost:8003/docs")
print("=" * 70)
