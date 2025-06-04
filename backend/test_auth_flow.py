#!/usr/bin/env python3
"""
Test script for AskRAG authentication endpoints
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
            return True
    except Exception as e:
        print(f"   Error: {e}")
    return False

def test_register():
    print("\n📝 Testing user registration...")
    user_data = {
        "username": "testuser123",
        "email": "testuser123@example.com", 
        "password": "TestPass123!",
        "full_name": "Test User"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json=user_data,
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code in [201, 400]:  # 400 might be "already exists"
            if response.status_code == 201:
                print("   ✅ Registration successful")
                return response.json()
            else:
                resp_data = response.json()
                if "already" in resp_data.get("detail", "").lower():
                    print("   ⚠️  User already exists, proceeding with login test")
                    return True
        else:
            print(f"   ❌ Registration failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Registration error: {e}")
    
    return False

def test_login():
    print("\n🔐 Testing user login...")
    login_data = {
        "email": "testuser123@example.com",
        "password": "TestPass123!"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json=login_data,
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            print(f"   ✅ Login successful")
            if access_token:
                print(f"   Token: {access_token[:50]}...")
                return access_token
        else:
            print(f"   ❌ Login failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Login error: {e}")
    
    return None

def test_protected_endpoint(token):
    print("\n🛡️  Testing protected endpoint...")
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/auth/me",
            headers=headers,
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            print("   ✅ Protected endpoint access successful")
            return True
        else:
            print(f"   ❌ Protected endpoint failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Protected endpoint error: {e}")
    
    return False

def main():
    print("🔑 Testing AskRAG Authentication System")
    print("=" * 50)
    
    # Test health check
    if not test_health():
        print("❌ Health check failed, aborting tests")
        return
    
    # Test registration
    reg_result = test_register()
    if not reg_result:
        print("❌ Registration failed, aborting tests")
        return
    
    # Test login
    token = test_login()
    if not token:
        print("❌ Login failed, aborting tests")
        return
    
    # Test protected endpoint
    if test_protected_endpoint(token):
        print("\n🎉 All authentication tests passed!")
    else:
        print("\n❌ Protected endpoint test failed")

if __name__ == "__main__":
    main()
