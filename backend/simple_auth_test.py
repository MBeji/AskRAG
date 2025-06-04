import requests
import sys

print("Starting authentication test...")
sys.stdout.flush()

try:
    print("Testing health endpoint...")
    response = requests.get("http://localhost:8000/health", timeout=5)
    print(f"Health Status: {response.status_code}")
    print(f"Health Response: {response.text}")
    
    print("\nTesting registration...")
    user_data = {
        "username": "testuser123",
        "email": "testuser123@example.com", 
        "password": "TestPass123!",
        "full_name": "Test User"
    }
    
    response = requests.post(
        "http://localhost:8000/api/v1/auth/register",
        json=user_data,
        timeout=10
    )
    print(f"Register Status: {response.status_code}")
    print(f"Register Response: {response.text}")
    
    print("\nTesting login...")
    login_data = {
        "email": "testuser123@example.com",
        "password": "TestPass123!"
    }
    
    response = requests.post(
        "http://localhost:8000/api/v1/auth/login",
        json=login_data,
        timeout=10
    )
    print(f"Login Status: {response.status_code}")
    print(f"Login Response: {response.text}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("Test completed.")
