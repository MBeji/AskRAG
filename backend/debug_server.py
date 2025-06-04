#!/usr/bin/env python3
"""
Test de démarrage du serveur AskRAG Étape 10 - Mode debug
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

print("🔍 Testing server initialization...")

try:
    print("1. Testing FastAPI import...")
    from fastapi import FastAPI, Depends, HTTPException, status
    print("   ✅ FastAPI imports OK")
    
    print("2. Testing CORS import...")
    from fastapi.middleware.cors import CORSMiddleware
    print("   ✅ CORS import OK")
    
    print("3. Testing security import...")
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    print("   ✅ Security imports OK")
    
    print("4. Testing auth service import...")
    from app.services.auth_service import AuthService, get_auth_service
    print("   ✅ Auth service import OK")
    
    print("5. Testing mock repositories import...")
    from app.db.repositories.mock_repositories import get_mock_user_repository, MockUserRepository
    print("   ✅ Mock repositories import OK")
    
    print("6. Testing user models import...")
    from app.models.user_v1 import UserCreate, UserLogin, UserResponse
    print("   ✅ User models import OK")
    
    print("7. Testing config import...")
    from app.core.config import get_settings
    settings = get_settings()
    print(f"   ✅ Config import OK - CORS origins: {settings.BACKEND_CORS_ORIGINS}")
    
    print("8. Creating FastAPI app...")
    app = FastAPI(
        title="AskRAG API - Test",
        description="Test server",
        version="1.0.0"
    )
    print("   ✅ FastAPI app created")
    
    print("9. Adding CORS middleware...")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    print("   ✅ CORS middleware added")
    
    print("10. Testing uvicorn import...")
    import uvicorn
    print("   ✅ Uvicorn import OK")
    
    print("\n🎉 All imports and initialization successful!")
    print("🚀 Now testing actual server start...")
    
    @app.get("/")
    async def root():
        return {"message": "Debug server working", "status": "ok"}
    
    @app.get("/health")
    async def health():
        return {"status": "healthy"}
    
    print("📡 Starting debug server on port 8005...")
    uvicorn.run(app, host="0.0.0.0", port=8005, log_level="debug")
    
except Exception as e:
    print(f"❌ Error during initialization: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
