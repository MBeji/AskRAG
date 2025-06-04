"""
Simple test for authentication system with minimal dependencies
"""
import sys
sys.path.append('.')

print("Starting authentication tests...")

try:
    from datetime import datetime, timedelta
    import json
    from app.core.auth import AuthService
    print("✅ Imports successful")
    
    # Test password hashing
    print("\n🔐 Testing password hashing...")
    password = "test123"
    hashed = AuthService.get_password_hash(password)
    print(f"Original: {password}")
    print(f"Hashed: {hashed}")
    print(f"Verification: {AuthService.verify_password(password, hashed)}")
    
    # Test token creation
    print("\n🎫 Testing token creation...")
    user_data = {
        "sub": "user123",
        "email": "test@example.com", 
        "username": "testuser"
    }
    
    tokens = AuthService.create_token_pair(user_data)
    print(f"Access token created: {tokens.access_token[:50]}...")
    print(f"Refresh token created: {tokens.refresh_token[:50]}...")
    print(f"Token type: {tokens.token_type}")
    print(f"Expires in: {tokens.expires_in} seconds")
    
    # Test token verification
    print("\n🔍 Testing token verification...")
    payload = AuthService.verify_token(tokens.access_token, "access")
    print(f"Token verified successfully!")
    print(f"User ID: {payload.sub}")
    print(f"Email: {payload.email}")
    print(f"Username: {payload.username}")
    
    print("\n✅ All authentication system tests passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
