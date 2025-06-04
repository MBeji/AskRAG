"""
Test des endpoints RAG
Étape 14.9: Validation des endpoints de base du système RAG
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# Ajouter le chemin du backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration des logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration des variables d'environnement pour les tests
os.environ['OPENAI_API_KEY'] = 'test-key-placeholder'
os.environ['ENVIRONMENT'] = 'development'
os.environ['SECRET_KEY'] = 'test-secret-key-for-testing-only'


def test_imports():
    """Test d'import des services RAG"""
    print("=== Test des imports RAG ===")
    
    try:
        # Test des services core
        from app.core.vector_store import vector_store
        from app.core.embeddings import embedding_service
        from app.core.document_extractor import document_extractor
        from app.core.text_chunker import text_chunker
        from app.core.rag_pipeline import rag_pipeline
        print("✓ Services RAG Core importés")
        
        # Test des schémas
        from app.schemas.rag import (
            RAGQueryRequest, RAGQueryResponse,
            DocumentUploadResponse, SearchResult,
            ChatSession, ChatMessage
        )
        print("✓ Schémas RAG importés")
        
        # Test des endpoints (sans démarrer le serveur)
        from app.api.v1.endpoints import rag
        print("✓ Endpoints RAG importés")
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur d'import: {e}")
        return False


def test_rag_pipeline():
    """Test du pipeline RAG avec un document de test"""
    print("\n=== Test du pipeline RAG ===")
    
    try:
        from app.core.rag_pipeline import rag_pipeline
        
        # Créer un document de test
        test_content = """
        AskRAG est une application de RAG (Retrieval-Augmented Generation).
        Elle permet d'analyser des documents et de répondre à des questions.
        
        L'authentification se fait via JWT (JSON Web Tokens).
        Les utilisateurs peuvent uploader des documents PDF, DOCX, TXT, MD et HTML.
        
        Le système utilise FAISS pour la vectorisation et OpenAI pour les embeddings.
        Les documents sont découpés en chunks intelligemment.
        """
        
        # Test du traitement de document
        result = rag_pipeline.process_document(
            file_content=test_content.encode('utf-8'),
            filename="test_document.txt",
            document_metadata={
                'file_type': 'txt',
                'title': 'Document de test',
                'user_id': 'test_user_123'
            }
        )
        
        if result.get('success'):
            print(f"✓ Document traité: {result['chunking']['total_chunks']} chunks créés")
            
            # Test de recherche
            search_result = rag_pipeline.search(
                query="Comment fonctionne l'authentification ?",
                k=3,
                score_threshold=0.1
            )
            
            if search_result.get('results'):
                print(f"✓ Recherche réussie: {len(search_result['results'])} résultats")
                return True
            else:
                print("✗ Aucun résultat de recherche")
                return False
        else:
            print(f"✗ Erreur traitement: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"✗ Erreur pipeline RAG: {e}")
        return False


def test_vector_store():
    """Test du vector store FAISS"""
    print("\n=== Test du Vector Store ===")
    
    try:
        from app.core.vector_store import vector_store
        
        # Test d'ajout de document
        doc_id = vector_store.add_document(
            content="Test de vectorisation avec FAISS",
            metadata={'test': True, 'user_id': 'test_user'},
            document_id="test_doc_001"
        )
        print(f"✓ Document ajouté avec ID: {doc_id}")
        
        # Test de recherche
        results = vector_store.search(
            query="vectorisation FAISS",
            k=5,
            score_threshold=0.1
        )
        
        if results:
            print(f"✓ Recherche réussie: {len(results)} résultats")
            best_score = max(r['score'] for r in results) if results else 0
            print(f"  Meilleur score: {best_score:.3f}")
            return True
        else:
            print("✗ Aucun résultat trouvé")
            return False
            
    except Exception as e:
        print(f"✗ Erreur vector store: {e}")
        return False


def test_text_chunker():
    """Test du chunker de texte"""
    print("\n=== Test du Text Chunker ===")
    
    try:
        from app.core.text_chunker import text_chunker, ChunkStrategy
        
        test_text = """
        Premier paragraphe sur l'authentification JWT.
        Les tokens JWT sont sécurisés et permettent l'accès aux API.
        
        Deuxième paragraphe sur les documents.
        L'application supporte PDF, DOCX, TXT, MD et HTML.
        Les documents sont traités par le pipeline RAG.
        
        Troisième paragraphe sur la vectorisation.
        FAISS est utilisé pour stocker les embeddings.
        OpenAI génère les embeddings avec text-embedding-3-small.
        """
        
        # Test avec différentes stratégies
        strategies = [ChunkStrategy.SENTENCE, ChunkStrategy.PARAGRAPH, ChunkStrategy.HYBRID]
        
        for strategy in strategies:
            text_chunker.strategy = strategy
            chunks = text_chunker.chunk_text(
                text=test_text,
                document_id="test_chunking",
                metadata={'test': True}
            )
            
            print(f"✓ Stratégie {strategy.value}: {len(chunks)} chunks")
            
        return True
        
    except Exception as e:
        print(f"✗ Erreur text chunker: {e}")
        return False


def test_document_extractor():
    """Test de l'extracteur de documents"""
    print("\n=== Test du Document Extractor ===")
    
    try:
        from app.core.document_extractor import document_extractor
        
        # Test avec du contenu texte
        test_content = "Contenu de test pour l'extraction."
        
        result = document_extractor.extract_content(
            file_content=test_content.encode('utf-8'),
            filename="test.txt"
        )
        
        if result['metadata']['extraction_success']:
            print(f"✓ Extraction réussie: {len(result['content'])} caractères")
            
            # Test des formats supportés
            formats = document_extractor.get_supported_formats()
            print(f"✓ Formats supportés: {', '.join(formats)}")
            return True
        else:
            print(f"✗ Extraction échouée: {result['metadata'].get('error')}")
            return False
            
    except Exception as e:
        print(f"✗ Erreur document extractor: {e}")
        return False


def test_schemas():
    """Test des schémas Pydantic"""
    print("\n=== Test des schémas Pydantic ===")
    
    try:
        from app.schemas.rag import (
            RAGQueryRequest, RAGQueryResponse,
            DocumentUploadResponse, SearchResult
        )
        
        # Test RAGQueryRequest
        request = RAGQueryRequest(
            question="Test question",
            session_id="test_session",
            max_chunks=5,
            temperature=0.7
        )
        print(f"✓ RAGQueryRequest: {request.question}")
        
        # Test SearchResult
        result = SearchResult(
            chunk_id="test_chunk",
            content="Test content",
            score=0.85,
            metadata={'test': True},
            document_title="Test Doc"
        )
        print(f"✓ SearchResult: score {result.score}")
        
        # Test DocumentUploadResponse
        upload_response = DocumentUploadResponse(
            document_id="doc_123",
            filename="test.pdf",
            title="Test Document",
            chunks_count=10,
            processing_time=1.5,
            status="success",
            message="OK"
        )
        print(f"✓ DocumentUploadResponse: {upload_response.chunks_count} chunks")
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur schémas: {e}")
        return False


def main():
    """Fonction principale des tests"""
    print("🔬 Tests des endpoints RAG - Étape 14.9")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Schémas", test_schemas),
        ("Document Extractor", test_document_extractor),
        ("Text Chunker", test_text_chunker),
        ("Vector Store", test_vector_store),
        ("Pipeline RAG", test_rag_pipeline),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"✗ Erreur dans {name}: {e}")
            results.append((name, False))
    
    # Résumé
    print("\n" + "=" * 60)
    print("=== RÉSUMÉ DES TESTS ===")
    
    passed = 0
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} - {name}")
        if success:
            passed += 1
    
    total = len(results)
    print(f"\nRésultat: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Tous les tests sont passés ! Les endpoints RAG sont prêts.")
        return True
    else:
        print(f"⚠️  {total - passed} tests ont échoué. Vérifiez la configuration.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
