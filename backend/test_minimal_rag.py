"""
Serveur de test RAG minimal pour diagnostic
"""

import os
import sys

# Configuration d'environnement
os.environ['OPENAI_API_KEY'] = 'sk-test-placeholder-key-for-development'
os.environ['ENVIRONMENT'] = 'development'
os.environ['SECRET_KEY'] = 'test-secret-key-for-development-only'

# Ajouter le chemin du backend
sys.path.insert(0, '.')

print("🔍 Diagnostic du serveur de test...")
print(f"Python path: {sys.path[:3]}")
print(f"Working directory: {os.getcwd()}")

try:
    from fastapi import FastAPI
    print("✓ FastAPI import OK")
    
    app = FastAPI(title="AskRAG Test Minimal")
    print("✓ FastAPI app créée")
    
    @app.get("/")
    def root():
        return {"message": "Test minimal OK"}
    
    @app.get("/health")
    def health():
        try:
            from app.core.rag_pipeline import rag_pipeline
            return {"status": "healthy", "rag": "ok"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    print("✓ Endpoints définis")
    
    if __name__ == "__main__":
        import uvicorn
        print("🚀 Démarrage du serveur minimal...")
        uvicorn.run(app, host="127.0.0.1", port=8001)
        
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
