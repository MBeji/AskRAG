"""
Test Authentication Endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_auth():
    print("🔑 Testing Authentication Endpoints")
    
    # Test health check first
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Health check: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return
    
    # Test user registration
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123!",
        "full_name": "Test User"
    }
    
    try:
        print("\n📝 Testing user registration...")
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json=user_data
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ Registration successful")
        else:
            print(f"❌ Registration failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Registration error: {e}")
    
    # Test user login
    try:
        print("\n🔐 Testing user login...")
        login_data = {
            "email": "test@example.com",
            "password": "TestPass123!"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json=login_data
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            print(f"✅ Login successful, token: {access_token[:20]}...")
            return access_token
        else:
            print(f"❌ Login failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Login error: {e}")
    
    return None

if __name__ == "__main__":
    test_auth()
