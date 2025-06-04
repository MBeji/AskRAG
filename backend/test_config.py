"""
Configuration d'environnement pour les tests
"""

import os

# Configuration pour les tests - variables d'environnement
os.environ['OPENAI_API_KEY'] = 'sk-test-placeholder-key-for-development'
os.environ['ENVIRONMENT'] = 'development'
os.environ['SECRET_KEY'] = 'test-secret-key-for-development-only'

print("=== Configuration Test Environnement ===")
print(f"OPENAI_API_KEY: {os.environ.get('OPENAI_API_KEY', 'NON DEFINIE')[:20]}...")
print(f"ENVIRONMENT: {os.environ.get('ENVIRONMENT')}")
print(f"SECRET_KEY: {os.environ.get('SECRET_KEY', 'NON DEFINIE')[:10]}...")

try:
    print("\n=== Test imports avec configuration ===")
    
    from app.core.vector_store import VectorStore
    print("✓ VectorStore importé")
    
    from app.core.embeddings import EmbeddingService
    print("✓ EmbeddingService importé")
    
    from app.core.rag_pipeline import RAGPipeline
    print("✓ RAGPipeline importé")
    
    print("\n🎉 Configuration réussie !")
    
except Exception as e:
    print(f"✗ Erreur: {e}")
    import traceback
    traceback.print_exc()
