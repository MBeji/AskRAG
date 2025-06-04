#!/usr/bin/env python3
"""
Test simple pour vérifier le démarrage du serveur
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

try:
    print("🔍 Testing imports...")
    
    print("1. Testing FastAPI...")
    from fastapi import FastAPI
    print("   ✅ FastAPI OK")
    
    print("2. Testing core config...")
    from app.core.config import get_settings
    settings = get_settings()
    print(f"   ✅ Config OK - Upload dir: {settings.UPLOAD_DIR}")
    
    print("3. Testing auth service...")
    from app.services.auth_service import AuthService, get_auth_service
    print("   ✅ Auth service OK")
    
    print("4. Testing repositories...")
    from app.db.repositories.mock_repositories import MockUserRepository
    repo = MockUserRepository()
    print("   ✅ Mock repositories OK")
    
    print("5. Testing endpoints...")
    from app.api.v1.endpoints import auth, documents, database, users
    print("   ✅ Endpoints OK")
    
    print("6. Creating FastAPI app...")
    app = FastAPI(title="Test AskRAG API")
    print("   ✅ FastAPI app created")
    
    print("7. Testing uvicorn...")
    import uvicorn
    print("   ✅ Uvicorn available")
    
    print("\n🎉 All imports successful! Starting test server...")
    
    # Simple test server
    @app.get("/")
    async def root():
        return {"message": "Test server working!"}
    
    @app.get("/health")
    async def health():
        return {"status": "healthy", "message": "Test server is running"}
    
    if __name__ == "__main__":
        print("🚀 Starting test server on port 8001...")
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8001,
            log_level="info"
        )
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
