"""
Test du système de vectorisation FAISS
Étape 14.4: Test de connexion et fonctionnement FAISS
"""

import os
import sys
import logging
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.append(str(Path(__file__).parent))

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_faiss_import():
    """Test d'importation de FAISS"""
    try:
        import faiss
        print(f"✓ FAISS importé avec succès - Version: {faiss.__version__ if hasattr(faiss, '__version__') else 'N/A'}")
        return True
    except ImportError as e:
        print(f"✗ Erreur import FAISS: {e}")
        return False

def test_openai_import():
    """Test d'importation d'OpenAI"""
    try:
        import openai
        print(f"✓ OpenAI importé avec succès - Version: {openai.__version__}")
        return True
    except ImportError as e:
        print(f"✗ Erreur import OpenAI: {e}")
        return False

def test_embedding_service():
    """Test du service d'embeddings"""
    try:
        # Configuration OpenAI fictive pour test
        os.environ['OPENAI_API_KEY'] = 'sk-test-key-not-real'
        
        from app.core.embeddings import EmbeddingService
        
        # Test d'initialisation
        service = EmbeddingService()
        print(f"✓ EmbeddingService initialisé - Modèle: {service.model_name}")
        print(f"  Dimension: {service.embedding_dimension}")
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur EmbeddingService: {e}")
        return False

def test_vector_store():
    """Test du VectorStore FAISS"""
    try:
        # Configuration OpenAI fictive
        os.environ['OPENAI_API_KEY'] = 'sk-test-key-not-real'
        
        from app.core.vector_store import VectorStore
        
        # Test d'initialisation
        store = VectorStore(
            collection_name="test_collection",
            persist_directory="./test_faiss_db"
        )
        
        print(f"✓ VectorStore initialisé")
        print(f"  Collection: {store.collection_name}")
        print(f"  Dimension: {store.dimension}")
        print(f"  Répertoire: {store.persist_directory}")
        
        # Test des informations
        info = store.get_collection_info()
        print(f"  Nombre de documents: {info['count']}")
        print(f"  Taille index: {info['index_size']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur VectorStore: {e}")
        return False

def test_faiss_operations():
    """Test des opérations FAISS de base"""
    try:
        import faiss
        import numpy as np
        
        # Créer un index de test
        dimension = 128
        index = faiss.IndexFlatIP(dimension)
        
        # Données de test
        nb = 100
        np.random.seed(1234)
        vectors = np.random.random((nb, dimension)).astype('float32')
        
        # Normaliser pour similarité cosinus
        faiss.normalize_L2(vectors)
        
        # Ajouter à l'index
        index.add(vectors)
        print(f"✓ Index FAISS créé avec {index.ntotal} vecteurs")
        
        # Test de recherche
        k = 5
        query = vectors[:1]  # Premier vecteur comme requête
        scores, indices = index.search(query, k)
        
        print(f"✓ Recherche effectuée - {k} résultats trouvés")
        print(f"  Meilleur score: {scores[0][0]:.4f}")
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur opérations FAISS: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("=== Test du système de vectorisation FAISS ===\n")
    
    tests = [
        ("Import FAISS", test_faiss_import),
        ("Import OpenAI", test_openai_import),
        ("Service Embeddings", test_embedding_service),
        ("VectorStore", test_vector_store),
        ("Opérations FAISS", test_faiss_operations)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            success = test_func()
            results.append(success)
        except Exception as e:
            print(f"✗ Erreur inattendue: {e}")
            results.append(False)
    
    # Résumé
    print(f"\n=== Résumé des tests ===")
    total_tests = len(results)
    passed_tests = sum(results)
    
    for i, (test_name, _) in enumerate(tests):
        status = "✓ PASS" if results[i] else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nRésultat: {passed_tests}/{total_tests} tests réussis")
    
    if passed_tests == total_tests:
        print("🎉 Tous les tests sont passés ! Le système de vectorisation est prêt.")
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez la configuration.")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
