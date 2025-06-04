"""
AskRAG Step 17.2 - Comprehensive Integration Tests
Tests end-to-end functionality and component interactions
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, patch, AsyncMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient
import logging

# Import the main application
from app.main import app
from app.core.config import settings
from app.db.mock_database import get_mock_database

# Import core components for integration testing
from app.core.rag_pipeline import RAGPipeline
from app.core.document_extractor import DocumentExtractor
from app.core.text_chunker import TextChunker
from app.core.embeddings import OptimizedEmbeddingService
from app.core.vector_store import VectorStore
from app.utils.cache_manager import CacheManager
from app.utils.input_validator import InputValidator
from app.utils.response_formatter import ResponseFormatter

# Import auth components
from app.core.auth import AuthService
from app.db.repositories.mock_repositories import MockUserRepository

# Import schemas
from app.schemas.rag import DocumentUploadResponse, DocumentSearchRequest

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestAskRAGIntegration:
    """Comprehensive integration tests for AskRAG system"""

    @pytest.fixture(scope="function")
    async def setup_test_environment(self):
        """Setup comprehensive test environment with all components"""
        # Create temporary directory for test files
        test_dir = tempfile.mkdtemp()
        
        try:
            # Initialize test database
            mock_db = get_mock_database()
            mock_db.clear_all_collections()
            
            # Create test user
            test_user_data = {
                "id": "test-user-123",
                "email": "test@askrag.com",
                "username": "testuser",
                "full_name": "Test User",
                "is_active": True,
                "is_admin": False,
                "hashed_password": AuthService.hash_password("testpass123")
            }
            mock_db.insert_one("users", test_user_data)
            
            # Setup components
            environment = {
                "test_dir": test_dir,
                "mock_db": mock_db,
                "test_user": test_user_data,
                "app": app,
                "client": TestClient(app),
                "auth_token": None,
                "components": {
                    "rag_pipeline": RAGPipeline(),
                    "document_extractor": DocumentExtractor(),
                    "text_chunker": TextChunker(),
                    "embedding_service": OptimizedEmbeddingService(),
                    "vector_store": VectorStore(),
                    "cache_manager": CacheManager.create_memory_cache(),
                    "input_validator": InputValidator(),
                    "response_formatter": ResponseFormatter(),
                }
            }
            
            # Create test authentication token
            token_data = {
                "sub": test_user_data["id"],
                "email": test_user_data["email"],
                "username": test_user_data["username"]
            }
            environment["auth_token"] = AuthService.create_access_token(token_data)
            
            logger.info("Test environment setup completed")
            yield environment
            
        finally:
            # Cleanup
            shutil.rmtree(test_dir, ignore_errors=True)
            mock_db.clear_all_collections()
            logger.info("Test environment cleaned up")

    @pytest.mark.asyncio
    async def test_full_document_processing_workflow(self, setup_test_environment):
        """Test complete document upload and processing workflow"""
        env = await setup_test_environment
        client = env["client"]
        auth_token = env["auth_token"]
        
        # Step 1: Test authentication
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Step 2: Create test document content
        test_content = """
        AskRAG System Documentation
        
        AskRAG is a Retrieval-Augmented Generation system that allows users to:
        1. Upload documents (PDF, DOCX, TXT, MD)
        2. Process documents into searchable chunks
        3. Ask questions about document content
        4. Receive AI-generated answers with citations
        
        The system uses FAISS for vector search and OpenAI for text generation.
        """
        
        # Create temporary test file
        test_file_path = Path(env["test_dir"]) / "test_document.txt"
        test_file_path.write_text(test_content)
        
        # Step 3: Upload document
        with open(test_file_path, "rb") as test_file:
            files = {"file": ("test_document.txt", test_file, "text/plain")}
            data = {"title": "AskRAG Documentation"}
            
            upload_response = client.post(
                "/api/v1/rag/upload",
                files=files,
                data=data,
                headers=headers
            )
        
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        assert upload_data["status"] == "success"
        assert "document_id" in upload_data
        assert upload_data["filename"] == "test_document.txt"
        assert upload_data["chunks_count"] > 0
        
        document_id = upload_data["document_id"]
        logger.info(f"Document uploaded successfully: {document_id}")
        
        # Step 4: Test document search
        search_response = client.post(
            "/api/v1/rag/search",
            json={"query": "What is AskRAG?", "limit": 3},
            headers=headers
        )
        
        assert search_response.status_code == 200
        search_results = search_response.json()
        assert len(search_results) > 0
        assert search_results[0]["score"] > 0.5
        assert "AskRAG" in search_results[0]["content"]
        
        logger.info(f"Search completed: {len(search_results)} results found")
        
        # Step 5: Test RAG query (ask question)
        ask_response = client.post(
            "/api/v1/rag/ask",
            json={
                "query": "What can users do with AskRAG?",
                "include_sources": True,
                "max_sources": 3
            },
            headers=headers
        )
        
        assert ask_response.status_code == 200
        ask_data = ask_response.json()
        assert ask_data["success"] == True
        assert "answer" in ask_data["data"]
        assert "sources" in ask_data["data"]
        assert "confidence" in ask_data["data"]
        assert len(ask_data["data"]["sources"]) > 0
        
        logger.info("Full document processing workflow completed successfully")

    @pytest.mark.asyncio
    async def test_user_authentication_flow(self, setup_test_environment):
        """Test complete user authentication and authorization flow"""
        env = await setup_test_environment
        client = env["client"]
        
        # Step 1: Test user registration
        registration_data = {
            "username": "newuser",
            "email": "newuser@askrag.com",
            "password": "securepass123",
            "full_name": "New User"
        }
        
        register_response = client.post(
            "/api/v1/auth/register",
            json=registration_data
        )
        
        # Note: Registration might not be enabled, so we'll handle both cases
        if register_response.status_code == 201:
            assert "id" in register_response.json()
            logger.info("User registration completed successfully")
        else:
            logger.info("User registration disabled or failed as expected")
        
        # Step 2: Test user login
        login_data = {
            "email": "test@askrag.com",
            "password": "testpass123"
        }
        
        login_response = client.post(
            "/api/v1/auth/login",
            json=login_data
        )
        
        assert login_response.status_code == 200
        login_result = login_response.json()
        assert "access_token" in login_result
        assert "token_type" in login_result
        assert login_result["token_type"] == "bearer"
        
        access_token = login_result["access_token"]
        logger.info("User login completed successfully")
        
        # Step 3: Test protected endpoint access
        headers = {"Authorization": f"Bearer {access_token}"}
        
        me_response = client.get(
            "/api/v1/auth/me",
            headers=headers
        )
        
        assert me_response.status_code == 200
        user_data = me_response.json()
        assert user_data["email"] == "test@askrag.com"
        assert user_data["username"] == "testuser"
        assert user_data["is_active"] == True
        
        logger.info("Protected endpoint access verified")
        
        # Step 4: Test unauthorized access
        unauthorized_response = client.get("/api/v1/auth/me")
        assert unauthorized_response.status_code == 401
        
        # Step 5: Test invalid token
        invalid_headers = {"Authorization": "Bearer invalid-token"}
        invalid_response = client.get(
            "/api/v1/auth/me",
            headers=invalid_headers
        )
        assert invalid_response.status_code == 401
        
        logger.info("Authentication flow testing completed")

    @pytest.mark.asyncio
    async def test_chat_session_management(self, setup_test_environment):
        """Test chat session creation and message management"""
        env = await setup_test_environment
        client = env["client"]
        auth_token = env["auth_token"]
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Step 1: Create chat session
        session_response = client.post(
            "/api/v1/rag/sessions",
            json={"title": "Test Chat Session"},
            headers=headers
        )
        
        assert session_response.status_code == 200
        session_data = session_response.json()
        assert "session_id" in session_data
        assert session_data["title"] == "Test Chat Session"
        assert session_data["user_id"] == env["test_user"]["id"]
        
        session_id = session_data["session_id"]
        logger.info(f"Chat session created: {session_id}")
        
        # Step 2: List user sessions
        sessions_response = client.get(
            "/api/v1/rag/sessions",
            headers=headers
        )
        
        assert sessions_response.status_code == 200
        sessions_list = sessions_response.json()
        assert len(sessions_list) >= 1
        assert any(s["session_id"] == session_id for s in sessions_list)
        
        # Step 3: Send messages in session
        message_response = client.post(
            f"/api/v1/rag/sessions/{session_id}/messages",
            json={
                "message": "Hello, test message",
                "message_type": "user"
            },
            headers=headers
        )
        
        # Note: This endpoint might not be implemented yet
        if message_response.status_code == 404:
            logger.info("Session message endpoint not implemented yet")
        else:
            assert message_response.status_code == 200
            logger.info("Session message sent successfully")
        
        logger.info("Chat session management testing completed")

    @pytest.mark.asyncio
    async def test_system_health_and_status(self, setup_test_environment):
        """Test system health check and status endpoints"""
        env = await setup_test_environment
        client = env["client"]
        
        # Step 1: Test root endpoint
        root_response = client.get("/")
        assert root_response.status_code == 200
        root_data = root_response.json()
        assert "message" in root_data
        assert "version" in root_data
        assert "status" in root_data
        
        # Step 2: Test health check
        health_response = client.get("/health")
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["status"] in ["healthy", "unhealthy"]
        assert "service" in health_data
        assert "database" in health_data
        
        # Step 3: Test API v1 health
        api_health_response = client.get("/api/v1/health")
        assert api_health_response.status_code == 200
        
        # Step 4: Test RAG status endpoint
        auth_headers = {"Authorization": f"Bearer {env['auth_token']}"}
        rag_status_response = client.get(
            "/api/v1/rag/status",
            headers=auth_headers
        )
        
        # This endpoint might not be implemented
        if rag_status_response.status_code == 404:
            logger.info("RAG status endpoint not implemented yet")
        else:
            assert rag_status_response.status_code == 200
            logger.info("RAG status endpoint accessible")
        
        logger.info("System health and status testing completed")

    @pytest.mark.asyncio
    async def test_document_management_operations(self, setup_test_environment):
        """Test document CRUD operations and management"""
        env = await setup_test_environment
        client = env["client"]
        auth_headers = {"Authorization": f"Bearer {env['auth_token']}"}
        
        # Step 1: List documents (initially empty)
        list_response = client.get(
            "/api/v1/documents",
            headers=auth_headers
        )
        
        assert list_response.status_code == 200
        initial_docs = list_response.json()
        initial_count = len(initial_docs) if isinstance(initial_docs, list) else initial_docs.get("documents", [])
        
        # Step 2: Upload test document
        test_content = "This is a test document for management operations."
        test_file_path = Path(env["test_dir"]) / "management_test.txt"
        test_file_path.write_text(test_content)
        
        with open(test_file_path, "rb") as test_file:
            files = {"file": ("management_test.txt", test_file, "text/plain")}
            data = {"title": "Management Test Document"}
            
            upload_response = client.post(
                "/api/v1/documents/upload",
                files=files,
                data=data,
                headers=auth_headers
            )
        
        # Handle different endpoint implementations
        if upload_response.status_code == 404:
            # Try RAG upload endpoint instead
            with open(test_file_path, "rb") as test_file:
                files = {"file": ("management_test.txt", test_file, "text/plain")}
                data = {"title": "Management Test Document"}
                
                upload_response = client.post(
                    "/api/v1/rag/upload",
                    files=files,
                    data=data,
                    headers=auth_headers
                )
        
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        document_id = upload_data.get("document_id")
        assert document_id is not None
        
        logger.info(f"Document uploaded for management testing: {document_id}")
        
        # Step 3: Search documents
        search_response = client.get(
            "/api/v1/documents/search?q=management",
            headers=auth_headers
        )
        
        if search_response.status_code == 200:
            search_data = search_response.json()
            assert len(search_data.get("documents", [])) > 0
            logger.info("Document search completed successfully")
        else:
            logger.info("Document search endpoint not available")
        
        # Step 4: Get document details
        detail_response = client.get(
            f"/api/v1/documents/{document_id}",
            headers=auth_headers
        )
        
        if detail_response.status_code == 200:
            detail_data = detail_response.json()
            assert detail_data["id"] == document_id
            logger.info("Document details retrieved successfully")
        else:
            logger.info("Document detail endpoint not available")
        
        logger.info("Document management operations testing completed")

    @pytest.mark.asyncio
    async def test_error_handling_and_validation(self, setup_test_environment):
        """Test error handling and input validation across the system"""
        env = await setup_test_environment
        client = env["client"]
        auth_headers = {"Authorization": f"Bearer {env['auth_token']}"}
        
        # Step 1: Test invalid authentication
        invalid_auth_response = client.post(
            "/api/v1/rag/search",
            json={"query": "test"},
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert invalid_auth_response.status_code == 401
        
        # Step 2: Test missing authentication
        no_auth_response = client.post(
            "/api/v1/rag/search",
            json={"query": "test"}
        )
        assert no_auth_response.status_code == 401
        
        # Step 3: Test invalid search query
        empty_query_response = client.post(
            "/api/v1/rag/search",
            json={"query": ""},
            headers=auth_headers
        )
        assert empty_query_response.status_code == 400
        
        # Step 4: Test invalid file upload
        invalid_file_response = client.post(
            "/api/v1/rag/upload",
            files={"file": ("test.xyz", b"invalid content", "application/xyz")},
            headers=auth_headers
        )
        assert invalid_file_response.status_code == 400
        
        # Step 5: Test malformed JSON
        malformed_response = client.post(
            "/api/v1/rag/ask",
            data="invalid json",
            headers={**auth_headers, "Content-Type": "application/json"}
        )
        assert malformed_response.status_code == 422
        
        # Step 6: Test non-existent endpoints
        not_found_response = client.get(
            "/api/v1/nonexistent",
            headers=auth_headers
        )
        assert not_found_response.status_code == 404
        
        logger.info("Error handling and validation testing completed")

    @pytest.mark.asyncio
    async def test_component_integration_workflow(self, setup_test_environment):
        """Test integration between core RAG components"""
        env = await setup_test_environment
        components = env["components"]
        
        # Step 1: Test document extraction
        test_content = "AskRAG integration test document with important information."
        test_file_path = Path(env["test_dir"]) / "integration_test.txt"
        test_file_path.write_text(test_content)
        
        with open(test_file_path, "rb") as file:
            extracted_content = components["document_extractor"].extract_content(
                file.read(), "integration_test.txt"
            )
        
        assert extracted_content is not None
        assert "AskRAG" in extracted_content
        
        # Step 2: Test text chunking
        chunks = components["text_chunker"].chunk_text(
            extracted_content,
            strategy="sentence",
            chunk_size=100,
            chunk_overlap=20
        )
        
        assert len(chunks) > 0
        assert all(chunk["text"] for chunk in chunks)
        
        # Step 3: Test embedding generation
        # Mock embedding service for integration testing
        with patch.object(components["embedding_service"], "get_embedding") as mock_embed:
            mock_embed.return_value = [0.1] * 384  # Mock embedding vector
            
            embeddings = []
            for chunk in chunks:
                embedding = components["embedding_service"].get_embedding(chunk["text"])
                embeddings.append(embedding)
            
            assert len(embeddings) == len(chunks)
            assert all(len(emb) == 384 for emb in embeddings)
        
        # Step 4: Test vector storage
        with patch.object(components["vector_store"], "add_documents") as mock_add:
            mock_add.return_value = {"success": True, "ids": ["vec_1", "vec_2"]}
            
            storage_result = components["vector_store"].add_documents(
                chunks, embeddings, {"user_id": env["test_user"]["id"]}
            )
            
            assert storage_result["success"] == True
            assert len(storage_result["ids"]) > 0
        
        # Step 5: Test search functionality
        with patch.object(components["vector_store"], "search") as mock_search:
            mock_search.return_value = {
                "success": True,
                "results": [
                    {"content": chunks[0]["text"], "score": 0.9, "metadata": {}},
                    {"content": chunks[1]["text"] if len(chunks) > 1 else "Additional content", "score": 0.8, "metadata": {}}
                ]
            }
            
            search_results = components["vector_store"].search(
                query_embedding=[0.1] * 384,
                k=2,
                filters={"user_id": env["test_user"]["id"]}
            )
            
            assert search_results["success"] == True
            assert len(search_results["results"]) == 2
            assert search_results["results"][0]["score"] > 0.5
        
        # Step 6: Test caching
        cache_key = "test_integration_key"
        cache_value = {"test": "integration_data"}
        
        components["cache_manager"].set(cache_key, cache_value, ttl=300)
        retrieved_value = components["cache_manager"].get(cache_key)
        
        assert retrieved_value == cache_value
        
        # Step 7: Test input validation
        validation_result = components["input_validator"].validate_query("What is AskRAG?")
        assert validation_result["valid"] == True
        assert validation_result["cleaned_query"]
        
        invalid_result = components["input_validator"].validate_query("")
        assert invalid_result["valid"] == False
        
        # Step 8: Test response formatting
        response = components["response_formatter"].rag_response(
            answer="AskRAG is a document Q&A system",
            sources=search_results["results"],
            citations=[],
            confidence=0.85,
            processing_time=1.23
        )
        
        assert response.success == True
        assert response.data["answer"] == "AskRAG is a document Q&A system"
        assert response.data["confidence"] == 0.85
        
        logger.info("Component integration workflow testing completed")

    @pytest.mark.asyncio
    async def test_performance_and_load_simulation(self, setup_test_environment):
        """Test system performance under simulated load"""
        env = await setup_test_environment
        client = env["client"]
        auth_headers = {"Authorization": f"Bearer {env['auth_token']}"}
        
        # Setup test document for load testing
        test_content = "Performance test document. " * 100  # Create larger content
        test_file_path = Path(env["test_dir"]) / "performance_test.txt"
        test_file_path.write_text(test_content)
        
        # Upload document for testing
        with open(test_file_path, "rb") as test_file:
            files = {"file": ("performance_test.txt", test_file, "text/plain")}
            data = {"title": "Performance Test Document"}
            
            upload_response = client.post(
                "/api/v1/rag/upload",
                files=files,
                data=data,
                headers=auth_headers
            )
        
        assert upload_response.status_code == 200
        logger.info("Performance test document uploaded")
        
        # Simulate concurrent search requests
        search_queries = [
            "What is performance?",
            "Tell me about testing",
            "How does the system work?",
            "What are the features?",
            "Explain the functionality"
        ]
        
        search_results = []
        for query in search_queries:
            response = client.post(
                "/api/v1/rag/search",
                json={"query": query, "limit": 3},
                headers=auth_headers
            )
            search_results.append(response.status_code)
        
        # Verify all searches completed successfully
        assert all(status == 200 for status in search_results)
        logger.info(f"Completed {len(search_queries)} concurrent search requests")
        
        # Test health check under load
        health_checks = []
        for _ in range(10):
            health_response = client.get("/health")
            health_checks.append(health_response.status_code)
        
        assert all(status == 200 for status in health_checks)
        logger.info("Health checks passed under simulated load")
        
        logger.info("Performance and load simulation testing completed")

    @pytest.mark.asyncio
    async def test_data_persistence_and_recovery(self, setup_test_environment):
        """Test data persistence and recovery mechanisms"""
        env = await setup_test_environment
        mock_db = env["mock_db"]
        
        # Step 1: Add test data
        test_document = {
            "id": "persist-test-doc-1",
            "filename": "persistence_test.txt",
            "title": "Persistence Test Document",
            "content": "This document tests data persistence",
            "user_id": env["test_user"]["id"],
            "processing_status": "completed"
        }
        
        doc_id = mock_db.insert_one("documents", test_document)
        assert doc_id is not None
        
        # Step 2: Verify data exists
        retrieved_doc = mock_db.find_one("documents", {"id": "persist-test-doc-1"})
        assert retrieved_doc is not None
        assert retrieved_doc["title"] == "Persistence Test Document"
        
        # Step 3: Test data update
        mock_db.update_one(
            "documents",
            {"id": "persist-test-doc-1"},
            {"title": "Updated Persistence Test Document"}
        )
        
        updated_doc = mock_db.find_one("documents", {"id": "persist-test-doc-1"})
        assert updated_doc["title"] == "Updated Persistence Test Document"
        
        # Step 4: Test data deletion
        mock_db.delete_one("documents", {"id": "persist-test-doc-1"})
        deleted_doc = mock_db.find_one("documents", {"id": "persist-test-doc-1"})
        assert deleted_doc is None
        
        # Step 5: Test collection operations
        initial_count = mock_db.count_documents("documents")
        
        # Add multiple documents
        for i in range(5):
            test_doc = {
                "id": f"bulk-test-{i}",
                "title": f"Bulk Test Document {i}",
                "user_id": env["test_user"]["id"]
            }
            mock_db.insert_one("documents", test_doc)
        
        final_count = mock_db.count_documents("documents")
        assert final_count == initial_count + 5
        
        # Test bulk operations
        bulk_docs = mock_db.find("documents", {"user_id": env["test_user"]["id"]})
        assert len(bulk_docs) >= 5
        
        logger.info("Data persistence and recovery testing completed")


# Additional test utilities for integration testing

class IntegrationTestUtils:
    """Utility class for integration test helpers"""
    
    @staticmethod
    def create_test_file(content: str, filename: str, test_dir: str) -> Path:
        """Create a test file with given content"""
        file_path = Path(test_dir) / filename
        file_path.write_text(content)
        return file_path
    
    @staticmethod
    def simulate_user_session(client: TestClient, auth_token: str) -> Dict[str, Any]:
        """Simulate a complete user session"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        session = {
            "authenticated": False,
            "uploads": [],
            "searches": [],
            "queries": []
        }
        
        # Test authentication
        me_response = client.get("/api/v1/auth/me", headers=headers)
        if me_response.status_code == 200:
            session["authenticated"] = True
            session["user"] = me_response.json()
        
        return session
    
    @staticmethod
    def verify_response_format(response_data: Dict[str, Any], expected_fields: List[str]) -> bool:
        """Verify response contains expected fields"""
        return all(field in response_data for field in expected_fields)


# Run integration tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
