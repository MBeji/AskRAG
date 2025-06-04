"""
Test unitaire minimal pour vérifier les imports
"""

def test_basic_imports():
    """Test des imports de base"""
    try:
        from app.core.rag_pipeline import RAGPipeline
        print("✓ RAGPipeline importé")
        
        from app.core.document_extractor import DocumentExtractor
        print("✓ DocumentExtractor importé")
        
        from app.core.text_chunker import TextChunker
        print("✓ TextChunker importé")
        
        from app.core.vector_store import VectorStore
        print("✓ VectorStore importé")
        
        from app.core.embeddings import EmbeddingService
        print("✓ EmbeddingService importé")
        
        from app.core.llm_service import LLMService
        print("✓ LLMService importé")
        
        assert True
        return True
        
    except Exception as e:
        print(f"✗ Erreur import: {e}")
        assert False
        return False


def test_mock_creation():
    """Test de création de mocks simples"""
    from unittest.mock import Mock
    
    mock_obj = Mock()
    mock_obj.test_method.return_value = "test"
    
    assert mock_obj.test_method() == "test"
    return True


if __name__ == "__main__":
    print("=== Test des imports ===")
    test_basic_imports()
    test_mock_creation()
    print("✓ Tests terminés")
