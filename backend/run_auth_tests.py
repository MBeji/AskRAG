"""
Simple test runner to validate authentication system
"""
import requests
import json

def test_authentication_system():
    """Run comprehensive authentication tests"""
    base_url = "http://localhost:8000"
    
    print("🚀 Starting Authentication Integration Tests...")
    print("=" * 60)
    
    # Test 1: Health Check
    print("\n1. Testing Health Endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test 2: Login with Valid Credentials
    print("\n2. Testing Login with Valid Credentials...")
    try:
        credentials = {"email": "test@example.com", "password": "test123"}
        response = requests.post(f"{base_url}/api/v1/auth/login", json=credentials, timeout=5)
        
        if response.status_code == 200:
            print("✅ Login successful")
            login_data = response.json()
            access_token = login_data["tokens"]["accessToken"]
            print(f"   User: {login_data['user']['firstName']} {login_data['user']['lastName']}")
            print(f"   Email: {login_data['user']['email']}")
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False
    
    # Test 3: Login with Invalid Credentials
    print("\n3. Testing Login with Invalid Credentials...")
    try:
        invalid_credentials = {"email": "invalid@example.com", "password": "wrong"}
        response = requests.post(f"{base_url}/api/v1/auth/login", json=invalid_credentials, timeout=5)
        
        if response.status_code == 401:
            print("✅ Invalid credentials correctly rejected")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Invalid credentials test failed: Expected 401, got {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Invalid credentials test error: {e}")
        return False
    
    # Test 4: Protected Endpoint with Token
    print("\n4. Testing Protected Endpoint with Token...")
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(f"{base_url}/api/v1/auth/me", headers=headers, timeout=5)
        
        if response.status_code == 200:
            print("✅ Protected endpoint access successful")
            user_data = response.json()
            print(f"   User Profile: {user_data['firstName']} {user_data['lastName']}")
            print(f"   Role: {user_data['role']}")
        else:
            print(f"❌ Protected endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Protected endpoint error: {e}")
        return False
    
    # Test 5: Protected Endpoint without Token
    print("\n5. Testing Protected Endpoint without Token...")
    try:
        response = requests.get(f"{base_url}/api/v1/auth/me", timeout=5)
        
        if response.status_code == 401:
            print("✅ Unauthorized access correctly blocked")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Unauthorized test failed: Expected 401, got {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Unauthorized test error: {e}")
        return False
    
    # Test 6: CORS Headers
    print("\n6. Testing CORS Headers...")
    try:
        response = requests.options(f"{base_url}/api/v1/auth/login", timeout=5)
        cors_headers = {
            "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
            "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
            "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers")
        }
        
        if any(cors_headers.values()):
            print("✅ CORS headers present")
            for header, value in cors_headers.items():
                if value:
                    print(f"   {header}: {value}")
        else:
            print("⚠️  No CORS headers found")
    except Exception as e:
        print(f"❌ CORS test error: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 All Authentication Tests Completed Successfully!")
    print("✅ Backend Authentication System is Working Correctly")
    return True

if __name__ == "__main__":
    success = test_authentication_system()
    if success:
        print("\n🎯 Ready for Frontend Integration Testing!")
        exit(0)
    else:
        print("\n❌ Tests Failed - Check server status")
        exit(1)
