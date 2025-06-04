"""
Unit Tests for Authentication Module
Tests JWT token generation, validation, and user authentication
"""
import pytest
from datetime import datetime, timedelta
import jwt
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.auth import AuthService
# from app.models.user import User, UserLogin, UserResponse

class TestAuthService:
    """Test cases for AuthService"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.auth_service = AuthService()
        
    def test_create_access_token(self):
        """Test access token creation"""
        email = "test@example.com"
        token = self.auth_service.create_access_token(email)
        
        assert token is not None
        assert isinstance(token, str)
        
        # Decode and verify token
        payload = jwt.decode(
            token, 
            self.auth_service.secret_key, 
            algorithms=[self.auth_service.algorithm]
        )
        
        assert payload["sub"] == email
        assert "exp" in payload
        
    def test_create_refresh_token(self):
        """Test refresh token creation"""
        email = "test@example.com"
        token = self.auth_service.create_refresh_token(email)
        
        assert token is not None
        assert isinstance(token, str)
        
        # Decode and verify token
        payload = jwt.decode(
            token, 
            self.auth_service.secret_key, 
            algorithms=[self.auth_service.algorithm]
        )
        
        assert payload["sub"] == email
        assert payload["type"] == "refresh"
        assert "exp" in payload
        
    def test_verify_token_valid(self):
        """Test token verification with valid token"""
        email = "test@example.com"
        token = self.auth_service.create_access_token(email)
        
        decoded_email = self.auth_service.verify_token(token)
        assert decoded_email == email
        
    def test_verify_token_expired(self):
        """Test token verification with expired token"""
        email = "test@example.com"
        
        # Create token that expires immediately
        expired_payload = {
            "sub": email,
            "exp": datetime.utcnow() - timedelta(seconds=1)
        }
        
        expired_token = jwt.encode(
            expired_payload,
            self.auth_service.secret_key,
            algorithm=self.auth_service.algorithm
        )
        
        with pytest.raises(jwt.ExpiredSignatureError):
            self.auth_service.verify_token(expired_token)
            
    def test_verify_token_invalid(self):
        """Test token verification with invalid token"""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(jwt.DecodeError):
            self.auth_service.verify_token(invalid_token)
            
    def test_hash_password(self):
        """Test password hashing"""
        password = "test123"
        hashed = self.auth_service.hash_password(password)
        
        assert hashed != password
        assert isinstance(hashed, str)
        assert len(hashed) > 20  # bcrypt hashes are long
        
    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "test123"
        hashed = self.auth_service.hash_password(password)
        
        assert self.auth_service.verify_password(password, hashed) is True
        
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "test123"
        wrong_password = "wrong123"
        hashed = self.auth_service.hash_password(password)
        
        assert self.auth_service.verify_password(wrong_password, hashed) is False
        
    def test_authenticate_user_valid(self):
        """Test user authentication with valid credentials"""
        credentials = UserLogin(email="test@example.com", password="test123")
        user = self.auth_service.authenticate_user(credentials)
        
        assert user is not None
        assert user.email == credentials.email
        assert user.isActive is True
        
    def test_authenticate_user_invalid_email(self):
        """Test user authentication with invalid email"""
        credentials = UserLogin(email="invalid@example.com", password="test123")
        user = self.auth_service.authenticate_user(credentials)
        
        assert user is None
        
    def test_authenticate_user_invalid_password(self):
        """Test user authentication with invalid password"""
        credentials = UserLogin(email="test@example.com", password="wrongpassword")
        user = self.auth_service.authenticate_user(credentials)
        
        assert user is None


class TestUserModels:
    """Test cases for User models"""
    
    def test_user_model_creation(self):
        """Test User model creation"""
        user_data = {
            "id": "user-123",
            "email": "test@example.com",
            "firstName": "Test",
            "lastName": "User",
            "role": "USER",
            "isActive": True,
            "createdAt": "2024-01-01T00:00:00Z",
            "updatedAt": "2024-01-01T00:00:00Z"
        }
        
        user = User(**user_data)
        
        assert user.id == "user-123"
        assert user.email == "test@example.com"
        assert user.firstName == "Test"
        assert user.lastName == "User"
        assert user.role == "USER"
        assert user.isActive is True
        
    def test_user_login_model(self):
        """Test UserLogin model creation"""
        login_data = {
            "email": "test@example.com",
            "password": "test123"
        }
        
        login = UserLogin(**login_data)
        
        assert login.email == "test@example.com"
        assert login.password == "test123"
        
    def test_user_response_model(self):
        """Test UserResponse model creation"""
        user_data = {
            "id": "user-123",
            "email": "test@example.com",
            "firstName": "Test",
            "lastName": "User",
            "role": "USER",
            "isActive": True,
            "createdAt": "2024-01-01T00:00:00Z",
            "updatedAt": "2024-01-01T00:00:00Z"
        }
        
        user_response = UserResponse(**user_data)
        
        assert user_response.id == "user-123"
        assert user_response.email == "test@example.com"
        # UserResponse shouldn't include password fields
        assert not hasattr(user_response, 'password')
        assert not hasattr(user_response, 'hashedPassword')
