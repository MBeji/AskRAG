#!/usr/bin/env python3
"""
Test server startup with debugging
"""
import sys
from pathlib import Path
import traceback

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

try:
    print("🔍 Starting server import test...")
    
    # Test individual imports
    print("📦 Importing FastAPI...")
    from fastapi import FastAPI
    print("✅ FastAPI imported")
    
    print("📦 Importing uvicorn...")
    import uvicorn
    print("✅ uvicorn imported")
    
    print("📦 Importing auth service...")
    from app.services.auth_service import AuthService, get_auth_service
    print("✅ Auth service imported")
    
    print("📦 Importing repositories...")
    from app.db.repositories.mock_repositories import get_mock_user_repository, MockUserRepository
    print("✅ Repositories imported")
    
    print("📦 Importing models...")
    from app.models.user_v1 import UserCreate, UserLogin, UserResponse
    print("✅ Models imported")
    
    print("📦 Importing config...")
    from app.core.config import get_settings
    print("✅ Config imported")
    
    # Create simple app
    print("🏗️ Creating FastAPI app...")
    app = FastAPI(title="Test Server")
    
    @app.get("/")
    def read_root():
        return {"message": "Server is working!"}
    
    @app.get("/health")
    def health_check():
        return {"status": "healthy"}
    
    print("✅ App created successfully")
    
    print("🚀 Starting server on port 8001...")
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8001,
        log_level="info"
    )
    
except Exception as e:
    print(f"❌ Error during startup: {e}")
    print(f"📋 Traceback:")
    traceback.print_exc()
