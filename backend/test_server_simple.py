"""
Test simple du serveur FastAPI avec authentification
"""
import sys
import os

# Ajouter le répertoire app au path pour les imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    
    # Configuration simple
    app = FastAPI(
        title="AskRAG Test Server",
        description="Serveur de test pour l'authentification AskRAG",
        version="1.0.0"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/")
    async def root():
        return {
            "message": "AskRAG Test Server Running",
            "status": "success",
            "version": "1.0.0"
        }
    
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "service": "askrag-backend"
        }
    
    # Mock auth endpoints pour test
    @app.post("/api/v1/auth/login")
    async def mock_login():
        return {
            "access_token": "mock-jwt-token",
            "token_type": "bearer",
            "user": {
                "id": "test-user-id",
                "email": "test@example.com",
                "username": "testuser"
            }
        }
    
    @app.get("/api/v1/auth/me")
    async def mock_current_user():
        return {
            "id": "test-user-id",
            "email": "test@example.com", 
            "username": "testuser",
            "is_active": True
        }
    
    if __name__ == "__main__":
        print("🚀 Démarrage du serveur de test AskRAG...")
        print("📍 Serveur disponible sur: http://localhost:8000")
        print("📖 Documentation API: http://localhost:8000/docs")
        print("🔧 Health check: http://localhost:8000/health")
        print("Press Ctrl+C to stop the server")
        
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8000,
            reload=False
        )
        
except ImportError as e:
    print(f"❌ Dépendance manquante: {e}")
    print("💡 Installer avec: pip install fastapi uvicorn")
except Exception as e:
    print(f"❌ Erreur de démarrage: {e}")
    import traceback
    traceback.print_exc()
