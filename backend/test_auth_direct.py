#!/usr/bin/env python3
"""
Test d'authentification direct pour Étape 10
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

print("🔍 Testing authentication components directly...")

try:
    # Import components
    from app.services.auth_service import AuthService
    from app.db.repositories.mock_repositories import MockUserRepository
    from app.models.user_v1 import UserCreate
    
    print("✅ All imports successful")
    
    # Initialize services
    auth_service = AuthService()
    user_repo = MockUserRepository()
    
    print("✅ Services initialized")
    
    # Create test user
    test_email = "test@example.com"
    test_password = "test123"
    
    print(f"🔧 Creating test user: {test_email}")
    
    # Check if user already exists
    existing_user = user_repo.get_by_email(test_email)
    if existing_user:
        print("ℹ️  Test user already exists")
    else:
        # Create new user
        hashed_password = auth_service.get_password_hash(test_password)
        user_data = {
            "email": test_email,
            "password": hashed_password,
            "full_name": "Test User",
            "is_active": True
        }
        user = user_repo.create(user_data)
        print(f"✅ Test user created with ID: {user.id}")
    
    # Test login
    print("🔐 Testing login...")
    user = user_repo.get_by_email(test_email)
    
    if user and auth_service.verify_password(test_password, user.password):
        print("✅ Password verification successful")
        
        # Create access token
        access_token = auth_service.create_access_token(data={"sub": user.email})
        print("✅ Access token created")
        
        # Verify token
        payload = auth_service.verify_access_token(access_token)
        print(f"✅ Token verification successful: {payload}")
        
        print(f"\n🎉 Authentication system working!")
        print(f"📊 Test Results:")
        print(f"   - User creation: ✅")
        print(f"   - Password hashing: ✅")
        print(f"   - Password verification: ✅")
        print(f"   - Token creation: ✅")
        print(f"   - Token verification: ✅")
        print(f"\n🔑 Test credentials for API:")
        print(f"   Email: {test_email}")
        print(f"   Password: {test_password}")
        print(f"   Token: {access_token[:50]}...")
        
    else:
        print("❌ Login failed")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
