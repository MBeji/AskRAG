#!/usr/bin/env python3
"""
Test de démarrage simplifié du serveur AskRAG
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

print("🔍 Starting simplified server test...")

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    
    print("✅ FastAPI imports successful")
    
    # Create simple app
    app = FastAPI(
        title="AskRAG Test API",
        description="Test server for debugging",
        version="1.0.0"
    )
    
    # Simple CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/")
    async def root():
        return {"message": "Test server is working!", "status": "ok"}
    
    @app.get("/health")
    async def health():
        return {"status": "healthy", "server": "test"}
    
    print("✅ FastAPI app created successfully")
    
    if __name__ == "__main__":
        print("🚀 Starting test server on port 8001...")
        print("📡 Server will be available at: http://localhost:8001")
        print("🔍 Health check at: http://localhost:8001/health")
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8001,
            log_level="info"
        )
        
except Exception as e:
    print(f"❌ Error in simplified server: {e}")
    import traceback
    traceback.print_exc()
