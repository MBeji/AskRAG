"""
Tests unitaires complets pour AskRAG
Étape 17.1 - Tests unitaires pour tous les composants
"""

import pytest
import asyncio
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any
from datetime import datetime, timedelta

# Imports des modules à tester
from app.core.rag_pipeline import RAGPipeline
from app.core.document_extractor import DocumentExtractor
from app.core.text_chunker import TextChunker, ChunkStrategy
from app.core.vector_store import VectorStore
from app.core.embeddings import EmbeddingService
from app.core.llm_service import LLMService
from app.utils.cache import CacheManager, MemoryCache
from app.utils.database_optimizer import OptimizedQueryBuilder, PaginationParams
from app.utils.pagination import RAGPaginator
from app.core.optimized_embeddings import OptimizedEmbeddingService
from app.schemas.rag import DocumentUploadResponse, DocumentSearchRequest


class TestRAGPipeline:
    """Tests unitaires pour le pipeline RAG principal"""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Crée des mocks pour toutes les dépendances"""
        return {
            'vector_store': Mock(spec=VectorStore),
            'document_extractor': Mock(spec=DocumentExtractor),
            'text_chunker': Mock(spec=TextChunker),
            'embedding_service': Mock(spec=EmbeddingService),
            'llm_service': Mock(spec=LLMService)
        }
    
    @pytest.fixture
    def rag_pipeline(self, mock_dependencies):
        """Crée une instance RAGPipeline avec des mocks"""
        return RAGPipeline(**mock_dependencies)
    
    def test_pipeline_initialization(self, mock_dependencies):
        """Test l'initialisation du pipeline"""
        pipeline = RAGPipeline(**mock_dependencies)
        
        assert pipeline.vector_store is not None
        assert pipeline.document_extractor is not None
        assert pipeline.text_chunker is not None
        assert pipeline.embedding_service is not None
        assert pipeline.llm_service is not None
        assert pipeline.stats['documents_processed'] == 0
    
    def test_process_document_success(self, rag_pipeline, mock_dependencies):
        """Test le traitement réussi d'un document"""
        # Setup mocks        mock_dependencies['document_extractor'].extract_content.return_value = {
            'content': 'Contenu du document de test',
            'metadata': {'extraction_success': True}
        }
        
        mock_dependencies['text_chunker'].chunk_text.return_value = {
            'success': True,
            'chunks': [
                {'content': 'Chunk 1', 'metadata': {}},
                {'content': 'Chunk 2', 'metadata': {}}
            ]
        }
        
        mock_dependencies['embedding_service'].generate_embeddings.return_value = {
            'success': True,
            'embeddings': [[0.1, 0.2], [0.3, 0.4]]
        }
        
        mock_dependencies['vector_store'].add_documents.return_value = {
            'success': True,
            'document_id': 'doc_123'
        }
        
        # Test
        result = rag_pipeline.process_document(
            file_content=b'test content',
            filename='test.txt'
        )
        
        # Assertions
        assert result['success'] is True
        assert result['document_id'] == 'doc_123'
        assert 'processing_time' in result
        assert rag_pipeline.stats['documents_processed'] == 1
        assert rag_pipeline.stats['chunks_created'] == 2
    
    def test_process_document_extraction_failure(self, rag_pipeline, mock_dependencies):
        """Test l'échec d'extraction de document"""
        mock_dependencies['document_extractor'].extract_text.return_value = {
            'success': False,
            'error': 'Format non supporté'
        }
        
        result = rag_pipeline.process_document(
            file_content=b'test',
            filename='test.unknown'
        )
        
        assert result['success'] is False
        assert result['stage'] == 'extraction'
        assert 'Format non supporté' in result['error']
    
    def test_search_success(self, rag_pipeline, mock_dependencies):
        """Test une recherche réussie"""
        mock_dependencies['embedding_service'].generate_embeddings.return_value = {
            'success': True,
            'embeddings': [[0.1, 0.2, 0.3]]
        }
        
        mock_dependencies['vector_store'].search.return_value = {
            'success': True,
            'results': [
                {'content': 'Résultat 1', 'score': 0.9},
                {'content': 'Résultat 2', 'score': 0.8}
            ]
        }
        
        result = rag_pipeline.search('test query', k=2)
        
        assert result['success'] is True
        assert len(result['results']) == 2
        assert result['query'] == 'test query'
        assert rag_pipeline.stats['searches_performed'] == 1
    
    def test_generate_answer_with_llm(self, rag_pipeline, mock_dependencies):
        """Test la génération de réponse avec LLM"""
        # Mock search results
        search_results = [
            {'content': 'Contexte pertinent 1', 'score': 0.9, 'metadata': {}},
            {'content': 'Contexte pertinent 2', 'score': 0.8, 'metadata': {}}
        ]
        
        mock_dependencies['llm_service'].generate_rag_response.return_value = {
            'success': True,
            'response': 'Réponse générée par le LLM',
            'metadata': {'tokens': 50}
        }
        
        result = rag_pipeline.generate_answer_with_llm(
            query='Question test',
            search_results=search_results
        )
        
        assert result['success'] is True
        assert result['answer'] == 'Réponse générée par le LLM'
        assert len(result['sources']) == 2
        assert result['context_used'] == 2


class TestDocumentExtractor:
    """Tests unitaires pour l'extracteur de documents"""
    
    @pytest.fixture
    def extractor(self):
        return DocumentExtractor()
    
    def test_extract_text_from_txt(self, extractor):
        """Test extraction de texte simple"""
        content = "Ceci est un texte de test".encode('utf-8')
        
        result = extractor.extract_text(content, 'test.txt')
        
        assert result['success'] is True
        assert result['text'] == "Ceci est un texte de test"
        assert result['metadata']['file_type'] == 'txt'
    
    def test_extract_text_unsupported_format(self, extractor):
        """Test extraction d'un format non supporté"""
        result = extractor.extract_text(b'content', 'test.unknown')
        
        assert result['success'] is False
        assert 'non supporté' in result['error'].lower()
    
    @patch('PyPDF2.PdfReader')
    def test_extract_text_from_pdf(self, mock_pdf_reader, extractor):
        """Test extraction PDF avec mock"""
        # Setup mock
        mock_page = Mock()
        mock_page.extract_text.return_value = "Texte PDF"
        mock_pdf_reader.return_value.pages = [mock_page]
        
        result = extractor.extract_text(b'pdf content', 'test.pdf')
        
        assert result['success'] is True
        assert "Texte PDF" in result['text']


class TestTextChunker:
    """Tests unitaires pour le chunker de texte"""
    
    @pytest.fixture
    def chunker(self):
        return TextChunker()
    
    def test_chunk_text_fixed_size(self, chunker):
        """Test chunking avec taille fixe"""
        text = "Ceci est un texte de test très long. " * 20
        
        result = chunker.chunk_text(
            text=text,
            strategy=ChunkStrategy.FIXED_SIZE,
            chunk_size=100
        )
        
        assert result['success'] is True
        assert len(result['chunks']) > 1
        for chunk in result['chunks']:
            assert len(chunk['content']) <= 150  # Avec overlap
    
    def test_chunk_text_semantic(self, chunker):
        """Test chunking sémantique"""
        text = """
        Introduction au machine learning.
        
        Le machine learning est une branche de l'intelligence artificielle.
        Il permet aux ordinateurs d'apprendre sans être explicitement programmés.
        
        Les types d'apprentissage.
        
        Il existe trois types principaux d'apprentissage automatique.
        """
        
        result = chunker.chunk_text(
            text=text,
            strategy=ChunkStrategy.SEMANTIC
        )
        
        assert result['success'] is True
        assert len(result['chunks']) >= 2
        assert all('content' in chunk for chunk in result['chunks'])
    
    def test_chunk_empty_text(self, chunker):
        """Test chunking d'un texte vide"""
        result = chunker.chunk_text(text="", strategy=ChunkStrategy.FIXED_SIZE)
        
        assert result['success'] is False
        assert 'vide' in result['error'].lower()


class TestCacheManager:
    """Tests unitaires pour le gestionnaire de cache"""
    
    @pytest.fixture
    def cache_manager(self):
        return CacheManager.create_memory_cache(max_size=100)
    
    @pytest.mark.asyncio
    async def test_cache_set_get(self, cache_manager):
        """Test basique set/get du cache"""
        cache = cache_manager.backend
        
        await cache.set('test_key', {'data': 'test_value'}, ttl=60)
        result = await cache.get('test_key')
        
        assert result is not None
        assert result['data'] == 'test_value'
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self, cache_manager):
        """Test expiration du cache"""
        cache = cache_manager.backend
        
        await cache.set('expire_key', 'value', ttl=0.1)  # 100ms
        await asyncio.sleep(0.2)  # Attendre expiration
        
        result = await cache.get('expire_key')
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_size_limit(self, cache_manager):
        """Test limite de taille du cache"""
        cache = cache_manager.backend
        
        # Remplir le cache au-delà de sa limite
        for i in range(150):  # Plus que max_size=100
            await cache.set(f'key_{i}', f'value_{i}', ttl=60)
        
        # Vérifier que certaines entrées ont été supprimées
        missing_count = 0
        for i in range(50):  # Vérifier les premières entrées
            if await cache.get(f'key_{i}') is None:
                missing_count += 1
        
        assert missing_count > 0  # Certaines entrées anciennes supprimées


class TestOptimizedQueryBuilder:
    """Tests unitaires pour le constructeur de requêtes optimisé"""
    
    @pytest.fixture
    def mock_collection(self):
        collection = Mock()
        collection.find.return_value = Mock()
        collection.count_documents.return_value = 0
        return collection
    
    @pytest.fixture
    def query_builder(self, mock_collection):
        return OptimizedQueryBuilder(mock_collection)
    
    def test_add_filter(self, query_builder):
        """Test ajout de filtre"""
        result = query_builder.add_filter('user_id', 'user123')
        
        assert result is query_builder  # Chaînage
        assert 'user_id' in query_builder._filters
    
    def test_add_text_search(self, query_builder):
        """Test recherche textuelle"""
        result = query_builder.add_text_search('search term', ['title', 'content'])
        
        assert result is query_builder
        assert '$text' in query_builder._filters
    
    def test_build_query(self, query_builder):
        """Test construction de requête complète"""
        query = (query_builder
                .add_filter('status', 'active')
                .add_text_search('test')
                .add_projection(['title', 'content'])
                .build())
        
        assert isinstance(query, dict)
        assert 'status' in str(query)  # Filtre inclus
    
    def test_pagination_params(self):
        """Test paramètres de pagination"""
        params = PaginationParams.from_request(page=2, page_size=20)
        
        assert params.page == 2
        assert params.page_size == 20
        assert params.offset() == 20  # (page-1) * page_size
        assert params.limit() == 20


class TestOptimizedEmbeddingService:
    """Tests unitaires pour le service d'embeddings optimisé"""
    
    @pytest.fixture
    def embedding_service(self):
        return OptimizedEmbeddingService(
            api_key=None,  # Mode test
            max_batch_size=10,
            max_concurrent_batches=2
        )
    
    @pytest.mark.asyncio
    async def test_generate_single_embedding(self, embedding_service):
        """Test génération d'un embedding simple"""
        result = await embedding_service.generate_single_embedding("test text")
        
        assert isinstance(result, list)
        assert len(result) == 1536  # Dimension OpenAI standard
        assert all(isinstance(x, float) for x in result)
    
    @pytest.mark.asyncio
    async def test_cache_embedding(self, embedding_service):
        """Test mise en cache d'embedding"""
        text = "test cache text"
        embedding = [0.1, 0.2, 0.3]
        
        await embedding_service.cache_embedding(text, embedding)
        cached = await embedding_service.get_embedding_cached(text)
        
        assert cached == embedding
    
    @pytest.mark.asyncio
    async def test_batch_embeddings(self, embedding_service):
        """Test traitement par batch"""
        texts = [f"test text {i}" for i in range(25)]  # Plus que batch_size
        
        result = await embedding_service.generate_embeddings_batch(
            texts=texts,
            batch_size=10
        )
        
        assert result['success'] is True
        assert len(result['embeddings']) == 25
        assert result['stats'].total_batches >= 3  # 25/10 = 3 batches
    
    def test_cache_key_generation(self, embedding_service):
        """Test génération de clés de cache"""
        key1 = embedding_service._get_cache_key("test text")
        key2 = embedding_service._get_cache_key("test text")
        key3 = embedding_service._get_cache_key("different text")
        
        assert key1 == key2  # Même texte = même clé
        assert key1 != key3  # Textes différents = clés différentes
        assert len(key1) == 16  # Longueur attendue


class TestRAGPaginator:
    """Tests unitaires pour le paginateur RAG"""
    
    @pytest.fixture
    def paginator(self):
        return RAGPaginator()
    
    @pytest.mark.asyncio
    async def test_paginate_documents_basic(self, paginator):
        """Test pagination basique de documents"""
        # Cette fonction nécessite une base de données
        # Test avec mock ou skip si DB non disponible
        pytest.skip("Nécessite une base de données pour les tests complets")
    
    def test_pagination_params_validation(self):
        """Test validation des paramètres de pagination"""
        # Test paramètres valides
        params = PaginationParams.from_request(page=1, page_size=20)
        assert params.page == 1
        assert params.page_size == 20
        
        # Test paramètres par défaut
        params_default = PaginationParams.from_request()
        assert params_default.page >= 1
        assert params_default.page_size > 0


class TestIntegrationComponents:
    """Tests d'intégration entre composants"""
    
    @pytest.fixture
    def full_pipeline(self):
        """Pipeline avec composants réels (mode test)"""
        return RAGPipeline()
    
    def test_pipeline_component_initialization(self, full_pipeline):
        """Test que tous les composants sont initialisés"""
        stats = full_pipeline.get_statistics()
        service_status = stats['service_status']
        
        # Au moins certains services doivent être disponibles
        available_services = sum(service_status.values())
        assert available_services > 0
    
    @pytest.mark.asyncio
    async def test_cache_integration_with_embeddings(self):
        """Test intégration cache avec embeddings"""
        cache_manager = CacheManager.create_memory_cache(max_size=50)
        embedding_service = OptimizedEmbeddingService(
            api_key=None,
            max_batch_size=5
        )
        
        # Test que le cache améliore les performances
        text = "integration test text"
        
        # Premier appel (cache miss)
        start = datetime.now()
        embedding1 = await embedding_service.generate_single_embedding(text)
        time1 = (datetime.now() - start).total_seconds()
        
        # Mettre en cache
        await embedding_service.cache_embedding(text, embedding1)
        
        # Deuxième appel (cache hit)
        start = datetime.now()
        embedding2 = await embedding_service.get_embedding_cached(text)
        time2 = (datetime.now() - start).total_seconds()
        
        assert embedding1 == embedding2
        assert time2 < time1  # Cache doit être plus rapide


class TestErrorHandling:
    """Tests de gestion d'erreurs"""
    
    def test_pipeline_with_none_dependencies(self):
        """Test pipeline avec dépendances None"""
        pipeline = RAGPipeline(
            vector_store=None,
            document_extractor=None,
            text_chunker=None,
            embedding_service=None,
            llm_service=None
        )
        
        # Le pipeline doit gérer les None gracieusement
        result = pipeline.process_document(b'test', 'test.txt')
        assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_cache_error_handling(self):
        """Test gestion d'erreurs du cache"""
        cache_manager = CacheManager.create_memory_cache(max_size=10)
        cache = cache_manager.backend
        
        # Test avec clé None
        result = await cache.get(None)
        assert result is None
        
        # Test avec valeur None
        await cache.set('test_key', None, ttl=60)
        result = await cache.get('test_key')
        # Doit gérer les valeurs None sans erreur
    
    def test_query_builder_error_handling(self):
        """Test gestion d'erreurs du query builder"""
        mock_collection = Mock()
        builder = OptimizedQueryBuilder(mock_collection)
        
        # Test avec paramètres invalides
        try:
            builder.add_filter("", "")  # Clé vide
            builder.build()
        except Exception:
            pass  # Exception attendue ou gérée gracieusement


@pytest.mark.performance
class TestPerformanceRequirements:
    """Tests de validation des exigences de performance"""
    
    @pytest.mark.asyncio
    async def test_cache_performance_requirements(self):
        """Test que le cache respecte les exigences de performance"""
        cache_manager = CacheManager.create_memory_cache(max_size=1000)
        cache = cache_manager.backend
        
        # Test performance d'écriture
        start = datetime.now()
        for i in range(100):
            await cache.set(f'perf_key_{i}', f'value_{i}', ttl=60)
        write_time = (datetime.now() - start).total_seconds()
        
        # Doit être < 1ms par opération en moyenne
        avg_write_time = write_time / 100
        assert avg_write_time < 0.001, f"Écriture trop lente: {avg_write_time:.4f}s"
        
        # Test performance de lecture
        start = datetime.now()
        for i in range(100):
            await cache.get(f'perf_key_{i}')
        read_time = (datetime.now() - start).total_seconds()
        
        avg_read_time = read_time / 100
        assert avg_read_time < 0.001, f"Lecture trop lente: {avg_read_time:.4f}s"
    
    def test_embedding_generation_performance(self):
        """Test performance de génération d'embeddings"""
        service = OptimizedEmbeddingService(api_key=None, max_batch_size=50)
        
        start = datetime.now()
        embedding = service._generate_test_embedding("test performance")
        generation_time = (datetime.now() - start).total_seconds()
        
        # Génération d'un embedding doit être < 10ms
        assert generation_time < 0.01, f"Génération trop lente: {generation_time:.4f}s"
        assert len(embedding) == 1536
    
    def test_query_builder_performance(self):
        """Test performance du constructeur de requêtes"""
        mock_collection = Mock()
        builder = OptimizedQueryBuilder(mock_collection)
        
        start = datetime.now()
        for i in range(1000):
            query = (builder
                    .add_filter("user_id", f"user_{i}")
                    .add_text_search("test")
                    .build())
        build_time = (datetime.now() - start).total_seconds()
        
        avg_build_time = build_time / 1000
        # Construction de requête doit être < 100μs
        assert avg_build_time < 0.0001, f"Construction trop lente: {avg_build_time:.6f}s"


if __name__ == "__main__":
    # Configuration pour exécution directe
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--disable-warnings"
    ])
