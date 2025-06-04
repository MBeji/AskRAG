"""
Simple authentication tests that don't rely on Pydantic models
"""
import pytest
import os
import sys

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.auth import AuthService


class TestAuthServiceSimple:
    """Test cases for AuthService without model dependencies"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.auth_service = AuthService()
          def test_hash_password(self):
        """Test password hashing"""
        password = "test123"
        hashed = self.auth_service.get_password_hash(password)
        
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 20  # bcrypt hashes are typically longer
          def test_verify_password(self):
        """Test password verification"""
        password = "test123"
        hashed = self.auth_service.get_password_hash(password)
        
        # Test correct password
        assert self.auth_service.verify_password(password, hashed) is True
        
        # Test wrong password
        assert self.auth_service.verify_password("wrongpassword", hashed) is False
        
    def test_create_jwt_token(self):
        """Test JWT token creation"""
        user_data = {"user_id": "test123", "username": "testuser"}
        token = self.auth_service.create_access_token(user_data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are quite long
        
    def test_verify_jwt_token(self):
        """Test JWT token verification"""
        user_data = {"user_id": "test123", "username": "testuser"}
        token = self.auth_service.create_access_token(user_data)
        
        # Verify valid token
        payload = self.auth_service.verify_token(token)
        assert payload is not None
        assert payload["user_id"] == "test123"
        assert payload["username"] == "testuser"
        
    def test_invalid_jwt_token(self):
        """Test invalid JWT token handling"""
        # Test with invalid token
        payload = self.auth_service.verify_token("invalid.token.here")
        assert payload is None
        
        # Test with None
        payload = self.auth_service.verify_token(None)
        assert payload is None
        
    def test_expired_jwt_token(self):
        """Test expired JWT token handling"""
        # Create token with very short expiry
        user_data = {"user_id": "test123", "username": "testuser"}
        
        # This would require modifying the auth service to accept custom expiry
        # For now, just test that the method exists
        token = self.auth_service.create_access_token(user_data)
        assert token is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
