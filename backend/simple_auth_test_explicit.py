#!/usr/bin/env python3
"""Simple auth test with explicit output"""
import requests
import json
import sys

print("🔍 Starting authentication test...", flush=True)

# Test registration
print("\n📝 Testing user registration...", flush=True)

user_data = {
    "email": "test@askrag.com",
    "username": "testuser", 
    "full_name": "Test User",
    "password": "TestPassword123"
}

try:
    print(f"   Sending POST to http://localhost:8003/api/v1/auth/register", flush=True)
    response = requests.post("http://localhost:8003/api/v1/auth/register", json=user_data, timeout=10)
    print(f"   Response status: {response.status_code}", flush=True)
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Registration successful!", flush=True)
        print(f"   User created: {result['email']} - {result['full_name']}", flush=True)
    else:
        print(f"   ❌ Registration failed: {response.status_code}", flush=True)
        print(f"   Error: {response.text}", flush=True)
        
except requests.exceptions.RequestException as e:
    print(f"   ❌ Request error: {e}", flush=True)
except Exception as e:
    print(f"   ❌ Unexpected error: {e}", flush=True)

print("\n✅ Test completed!", flush=True)
