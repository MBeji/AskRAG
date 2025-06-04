"""
Integrati        self.base_url = "http://localhost:8000"
        self.auth_base = f"{self.base_url}/api/v1/auth" Tests for Authentication Endpoints
Tests the Flask authentication server API endpoints
"""
import pytest
import requests
import json
from datetime import datetime, timedelta

class TestAuthenticationEndpoints:
    """Integration tests for authentication API endpoints"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.base_url = "http://localhost:8000"
        self.auth_base = f"{self.base_url}/api/v1/auth"
        
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = requests.get(f"{self.base_url}/health", timeout=5)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "timestamp" in data
          def test_login_endpoint_valid_credentials(self):
        """Test login with valid credentials"""
        credentials = {
            "username": "test@example.com",
            "password": "test123"
        }
        
        response = requests.post(
            f"{self.auth_base}/login",
            json=credentials,
            timeout=5
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "tokens" in data
        assert "user" in data
        
        # Check tokens
        tokens = data["tokens"]
        assert "accessToken" in tokens
        assert "refreshToken" in tokens
        assert "tokenType" in tokens
        assert tokens["tokenType"] == "bearer"
        
        # Check user data
        user = data["user"]
        assert user["email"] == credentials["email"]
        assert "id" in user
        assert "firstName" in user
        assert "lastName" in user
        assert "role" in user
        assert user["isActive"] is True
        
    def test_login_endpoint_invalid_email(self):
        """Test login with invalid email"""        credentials = {
            "username": "invalid@example.com",
            "password": "test123"
        }
        
        response = requests.post(
            f"{self.auth_base}/login",
            json=credentials,
            timeout=5
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert "Invalid credentials" in data["error"]
        
    def test_login_endpoint_invalid_password(self):
        """Test login with invalid password"""
        credentials = {
            "email": "test@example.com",
            "password": "wrongpassword"
        }
        
        response = requests.post(
            f"{self.auth_base}/login",
            json=credentials,
            timeout=5
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert "Invalid credentials" in data["error"]
        
    def test_login_endpoint_missing_fields(self):
        """Test login with missing required fields"""
        # Missing password
        credentials = {
            "email": "test@example.com"
        }
        
        response = requests.post(
            f"{self.auth_base}/login",
            json=credentials,
            timeout=5
        )
        
        assert response.status_code == 422  # Validation error
        
    def test_register_endpoint_new_user(self):
        """Test user registration with new user"""
        user_data = {
            "email": "newuser@example.com",
            "password": "newpassword123",
            "firstName": "New",
            "lastName": "User"
        }
        
        response = requests.post(
            f"{self.auth_base}/register",
            json=user_data,
            timeout=5
        )
        
        # Note: This might fail if user already exists in mock DB
        # In a real test, we'd reset the DB between tests
        if response.status_code == 201:
            data = response.json()
            assert "tokens" in data
            assert "user" in data
            assert data["user"]["email"] == user_data["email"]
        elif response.status_code == 400:
            # User might already exist in mock DB
            data = response.json()
            assert "already exists" in data["error"]
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")
            
    def test_register_endpoint_existing_user(self):
        """Test user registration with existing user"""
        user_data = {
            "email": "test@example.com",  # Already exists in mock DB
            "password": "newpassword123",
            "firstName": "Test",
            "lastName": "User"
        }
        
        response = requests.post(
            f"{self.auth_base}/register",
            json=user_data,
            timeout=5
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "already exists" in data["error"]
        
    def test_protected_endpoint_with_token(self):
        """Test accessing protected endpoint with valid token"""
        # First login to get a token
        credentials = {
            "email": "test@example.com",
            "password": "test123"
        }
        
        login_response = requests.post(
            f"{self.auth_base}/login",
            json=credentials,
            timeout=5
        )
        
        assert login_response.status_code == 200
        token_data = login_response.json()
        access_token = token_data["tokens"]["accessToken"]
        
        # Now test protected endpoint
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        response = requests.get(
            f"{self.auth_base}/me",
            headers=headers,
            timeout=5
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == credentials["email"]
        
    def test_protected_endpoint_without_token(self):
        """Test accessing protected endpoint without token"""
        response = requests.get(f"{self.auth_base}/me", timeout=5)
        
        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        
    def test_protected_endpoint_invalid_token(self):
        """Test accessing protected endpoint with invalid token"""
        headers = {
            "Authorization": "Bearer invalid.token.here"
        }
        
        response = requests.get(
            f"{self.auth_base}/me",
            headers=headers,
            timeout=5
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        
    def test_cors_headers(self):
        """Test CORS headers are present"""
        response = requests.options(f"{self.auth_base}/login", timeout=5)
        
        # Check CORS headers
        assert "Access-Control-Allow-Origin" in response.headers
        assert "Access-Control-Allow-Methods" in response.headers
        assert "Access-Control-Allow-Headers" in response.headers
        
    def test_content_type_headers(self):
        """Test content type headers"""
        response = requests.get(f"{self.base_url}/health", timeout=5)
        
        assert response.headers["Content-Type"] == "application/json"
        
    def test_api_response_time(self):
        """Test API response time performance"""
        import time
        
        start_time = time.time()
        response = requests.get(f"{self.base_url}/health", timeout=5)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 1.0  # Should respond within 1 second
