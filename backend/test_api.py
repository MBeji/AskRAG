"""
Tests de base pour l'API FastAPI.
"""

import requests
import json


def test_api_endpoints():
    """Test des endpoints de base de l'API."""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing AskRAG API Endpoints")
    print("=" * 40)
    
    # Test endpoint racine
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ GET / - Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Message: {data.get('message')}")
            print(f"   Version: {data.get('version')}")
    except Exception as e:
        print(f"❌ GET / - Error: {e}")
    
    # Test health check
    try:
        response = requests.get(f"{base_url}/health")
        print(f"✅ GET /health - Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: {data.get('status')}")
    except Exception as e:
        print(f"❌ GET /health - Error: {e}")
    
    # Test API v1 health
    try:
        response = requests.get(f"{base_url}/api/v1/health")
        print(f"✅ GET /api/v1/health - Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: {data.get('status')}")
            print(f"   API Version: {data.get('api_version')}")
    except Exception as e:
        print(f"❌ GET /api/v1/health - Error: {e}")
    
    # Test documentation
    try:
        response = requests.get(f"{base_url}/docs")
        print(f"✅ GET /docs - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ GET /docs - Error: {e}")
    
    print("\n🎉 API tests completed!")
    print("\n📍 Available endpoints:")
    print("   • Root: http://localhost:8000/")
    print("   • Health: http://localhost:8000/health")
    print("   • API v1 Health: http://localhost:8000/api/v1/health")
    print("   • Documentation: http://localhost:8000/docs")


if __name__ == "__main__":
    test_api_endpoints()
