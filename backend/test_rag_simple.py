"""
Test simple des services RAG Core
"""

print("=== Test Simple RAG ===")

try:
    print("1. Test import FAISS...")
    import faiss
    print(f"✓ FAISS OK - Version: {faiss.__version__}")
    
    print("2. Test import OpenAI...")
    import openai
    print(f"✓ OpenAI OK - Version: {openai.__version__}")
    
    print("3. Test import services...")
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    from app.core.vector_store import VectorStore
    print("✓ VectorStore importé")
    
    from app.core.embeddings import EmbeddingService
    print("✓ EmbeddingService importé")
    
    from app.core.rag_pipeline import RAGPipeline
    print("✓ RAGPipeline importé")
    
    print("4. Test création instances...")
    # Test création vector store
    vs = VectorStore(collection_name="test", dimension=1536)
    print("✓ VectorStore instance créée")
    
    print("\n🎉 Tous les imports fonctionnent!")
    
except Exception as e:
    print(f"✗ Erreur: {e}")
    import traceback
    traceback.print_exc()
