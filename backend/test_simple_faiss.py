"""
Test simple du système FAISS
"""

import sys
import os

# Configuration de base
os.environ['OPENAI_API_KEY'] = 'sk-test-dummy-key'

def test_simple():
    print("=== Test Simple FAISS ===")
    
    # Test 1: Import FAISS
    try:
        import faiss
        print("✓ FAISS importé")
    except Exception as e:
        print(f"✗ FAISS erreur: {e}")
        return False
    
    # Test 2: Import OpenAI
    try:
        import openai
        print("✓ OpenAI importé")
    except Exception as e:
        print(f"✗ OpenAI erreur: {e}")
        return False
    
    # Test 3: Test FAISS simple
    try:
        import numpy as np
        
        # Créer index
        dimension = 128
        index = faiss.IndexFlatIP(dimension)
        
        # Ajouter des vecteurs de test
        vectors = np.random.random((10, dimension)).astype('float32')
        faiss.normalize_L2(vectors)
        index.add(vectors)
        
        print(f"✓ Index FAISS créé avec {index.ntotal} vecteurs")
        
        # Test recherche
        scores, indices = index.search(vectors[:1], 3)
        print(f"✓ Recherche OK - Score max: {scores[0][0]:.3f}")
        
    except Exception as e:
        print(f"✗ FAISS test erreur: {e}")
        return False
    
    print("🎉 Tests de base réussis!")
    return True

if __name__ == "__main__":
    success = test_simple()
    print(f"\nRésultat: {'SUCCESS' if success else 'FAILED'}")
