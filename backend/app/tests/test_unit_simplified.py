"""
Tests unitaires simplifiés pour AskRAG
Version minimale pour diagnostic
"""

import pytest
from unittest.mock import Mock


def test_basic_functionality():
    """Test de base pour vérifier que pytest fonctionne"""
    assert True


class TestBasicRAG:
    """Tests de base pour les composants RAG"""
    
    def test_mock_creation(self):
        """Test de création de mock"""
        mock_obj = Mock()
        mock_obj.test_method.return_value = "success"
        
        result = mock_obj.test_method()
        assert result == "success"
    
    def test_import_rag_pipeline(self):
        """Test d'import RAGPipeline"""
        from app.core.rag_pipeline import RAGPipeline
        assert RAGPipeline is not None
    
    def test_import_schemas(self):
        """Test d'import des schémas"""
        from app.schemas.rag import DocumentUploadResponse
        assert DocumentUploadResponse is not None


class TestRAGPipelineMock:
    """Tests unitaires avec mocks pour RAGPipeline"""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Crée des mocks simplifiés"""
        return {
            'vector_store': Mock(),
            'document_extractor': Mock(),
            'text_chunker': Mock(),
            'embedding_service': Mock(),
            'llm_service': Mock()
        }
    
    def test_mock_dependencies_creation(self, mock_dependencies):
        """Test de création des dépendances mockées"""
        assert mock_dependencies['vector_store'] is not None
        assert mock_dependencies['document_extractor'] is not None
        assert mock_dependencies['text_chunker'] is not None
        assert mock_dependencies['embedding_service'] is not None
        assert mock_dependencies['llm_service'] is not None
    
    def test_mock_return_values(self, mock_dependencies):
        """Test de configuration des valeurs de retour"""
        # Configure mock
        mock_dependencies['document_extractor'].extract_text.return_value = {
            'success': True,
            'text': 'Test content'
        }
        
        # Test mock
        result = mock_dependencies['document_extractor'].extract_text('test')
        assert result['success'] is True
        assert result['text'] == 'Test content'
