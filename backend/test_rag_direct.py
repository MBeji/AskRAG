"""
Test direct du pipeline RAG - Étape 15.1
Test des fonctionnalités RAG sans serveur web
"""

import os
import sys

# Configuration d'environnement
os.environ['OPENAI_API_KEY'] = 'sk-test-placeholder-key-for-development'
os.environ['ENVIRONMENT'] = 'development'
os.environ['SECRET_KEY'] = 'test-secret-key-for-development-only'

# Ajouter le chemin
sys.path.insert(0, '.')

def test_rag_pipeline():
    """Test complet du pipeline RAG"""
    print("🧪 Test du pipeline RAG...")
    
    try:
        # Import du pipeline
        from app.core.rag_pipeline import rag_pipeline
        print("✓ Import pipeline RAG OK")
        
        # Document de test
        test_doc = """
        AskRAG est une application de RAG (Retrieval-Augmented Generation).
        Elle permet d'analyser des documents et de répondre aux questions.
        L'authentification se fait via JWT.
        Le système utilise FAISS pour la vectorisation.
        Le backend est développé avec FastAPI.
        Le frontend utilise React et TypeScript.
        """
        
        print("📄 Traitement du document de test...")
        
        # Traitement du document
        result = rag_pipeline.process_document(
            file_content=test_doc.encode('utf-8'),
            filename="test.txt",
            document_metadata={'user_id': 'test_user', 'source': 'test'}
        )
        
        print(f"📊 Résultat traitement: {result.get('success', False)}")
        if result.get('success'):
            print(f"   - Chunks créés: {result.get('chunking', {}).get('total_chunks', 0)}")
            print(f"   - Vecteurs stockés: {result.get('vectorization', {}).get('vectors_stored', 0)}")
        else:
            print(f"   - Erreur: {result.get('error', 'Inconnue')}")
            return False
        
        # Test de recherche
        questions = [
            "Qu'est-ce que AskRAG ?",
            "Quelle technologie est utilisée pour l'authentification ?",
            "Comment fonctionne la vectorisation ?"
        ]
        
        for i, question in enumerate(questions, 1):
            print(f"\n🔍 Question {i}: {question}")
            
            search_result = rag_pipeline.search(
                query=question,
                k=3,
                score_threshold=0.1
            )
            
            results = search_result.get('results', [])
            print(f"   - Résultats trouvés: {len(results)}")
            
            if results:
                for j, result in enumerate(results[:2], 1):
                    score = result.get('score', 0)
                    content = result.get('content', '')[:100] + "..."
                    print(f"     {j}. Score: {score:.3f} - {content}")
        
        print("\n✅ Test du pipeline RAG terminé avec succès !")
        return True
        
    except Exception as e:
        print(f"❌ Erreur dans le test RAG: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_vector_store():
    """Test du vector store"""
    print("\n🔧 Test du vector store...")
    
    try:
        from app.core.vector_store import vector_store
        print("✓ Import vector store OK")
        
        # Test d'ajout de vecteurs
        import numpy as np
        test_vectors = np.random.rand(3, 384).astype(np.float32)
        test_metadata = [
            {'content': 'Test 1', 'source': 'test'},
            {'content': 'Test 2', 'source': 'test'},
            {'content': 'Test 3', 'source': 'test'}
        ]
        
        vector_store.add_vectors(test_vectors, test_metadata)
        print("✓ Ajout de vecteurs OK")
        
        # Test de recherche
        query_vector = np.random.rand(384).astype(np.float32)
        results = vector_store.search(query_vector, k=2)
        print(f"✓ Recherche OK - {len(results)} résultats")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur vector store: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_embeddings():
    """Test du service d'embeddings"""
    print("\n🔤 Test du service d'embeddings...")
    
    try:
        from app.core.embeddings import embedding_service
        print("✓ Import embedding service OK")
        
        # Test d'embedding
        test_texts = [
            "AskRAG est une application RAG",
            "FastAPI est utilisé pour le backend",
            "FAISS gère la vectorisation"
        ]
        
        embeddings = embedding_service.get_embeddings(test_texts)
        print(f"✓ Génération embeddings OK - Shape: {embeddings.shape}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur embeddings: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Tests des composants RAG")
    print("=" * 50)
    
    # Tests individuels
    results = []
    results.append(test_embeddings())
    results.append(test_vector_store())
    results.append(test_rag_pipeline())
    
    # Résumé
    print("\n" + "=" * 50)
    print("📋 Résumé des tests:")
    tests = ["Embeddings", "Vector Store", "Pipeline RAG"]
    for i, (test_name, success) in enumerate(zip(tests, results)):
        status = "✅ SUCCÈS" if success else "❌ ÉCHEC"
        print(f"   {i+1}. {test_name}: {status}")
    
    total_success = sum(results)
    print(f"\n🎯 Total: {total_success}/{len(results)} tests réussis")
    
    if total_success == len(results):
        print("🎉 Tous les tests sont passés ! Le système RAG est fonctionnel.")
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
