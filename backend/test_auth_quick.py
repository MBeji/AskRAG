import requests
import json

# Test configuration
SERVER_URL = "http://localhost:8003"
API_BASE = f"{SERVER_URL}/api/v1"

def test_registration():
    """Test user registration"""
    user_data = {
        "email": "test@askrag.com",
        "username": "testuser",
        "full_name": "Test User",
        "password": "TestPassword123"
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/register", json=user_data)
        print(f"Registration Response: {response.status_code}")
        
        if response.status_code == 200:
            user_info = response.json()
            print(f"✅ Registration successful!")
            print(f"   Email: {user_info['email']}")
            print(f"   Name: {user_info['full_name']}")
            print(f"   ID: {user_info['id']}")
            print(f"   Active: {user_info['is_active']}")
            return True
        else:
            print(f"❌ Registration failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return False

def test_login():
    """Test user login"""
    login_data = {
        "email": "test@askrag.com",
        "password": "TestPassword123"
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        print(f"Login Response: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Login successful!")
            print(f"   Token length: {len(result['access_token'])}")
            print(f"   User: {result['user']['email']}")
            return result['access_token']
        else:
            print(f"❌ Login failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

if __name__ == "__main__":
    print("🚀 Testing AskRAG Authentication Flow")
    print("=" * 50)
    
    # Test registration
    print("\n1. Testing Registration...")
    reg_success = test_registration()
    
    if reg_success:
        print("\n2. Testing Login...")
        token = test_login()
        
        if token:
            print(f"\n🎉 Authentication flow working!")
            print(f"   Token: {token[:50]}...")
        else:
            print("\n❌ Login failed")
    else:
        print("\n❌ Registration failed, skipping login test")
