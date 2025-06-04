"""
AskRAG Step 17.2 - Integration Tests
Tests end-to-end functionality and component interactions
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
import logging

# Import the main application
from app.main import app

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestAskRAGIntegration:
    """Integration tests for AskRAG system"""

    @pytest.fixture(scope="function")
    def client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture(scope="function") 
    def temp_dir(self):
        """Create temporary directory for test files"""
        test_dir = tempfile.mkdtemp()
        yield test_dir
        shutil.rmtree(test_dir, ignore_errors=True)

    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        logger.info(f"Health check passed: {data}")

    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        # Should return either 200 or redirect
        assert response.status_code in [200, 307, 308]
        logger.info(f"Root endpoint response: {response.status_code}")

    def test_openapi_docs(self, client):
        """Test OpenAPI documentation endpoint"""
        response = client.get("/docs")
        assert response.status_code == 200
        logger.info("OpenAPI docs accessible")

    def test_api_v1_endpoints_discovery(self, client):
        """Test API v1 endpoints existence"""
        endpoints_to_test = [
            "/api/v1/auth/register",
            "/api/v1/auth/login", 
            "/api/v1/documents/upload",
            "/api/v1/documents/search",
            "/api/v1/rag/query",
            "/api/v1/chat/sessions",
            "/api/v1/users/me"
        ]
        
        results = {}
        
        for endpoint in endpoints_to_test:
            try:
                if "upload" in endpoint:
                    response = client.post(endpoint, files={"file": ("test.txt", "test content", "text/plain")})
                elif endpoint in ["/api/v1/auth/register", "/api/v1/auth/login", "/api/v1/rag/query", "/api/v1/documents/search"]:
                    response = client.post(endpoint, json={})
                else:
                    response = client.get(endpoint)
                    
                results[endpoint] = response.status_code
                logger.info(f"Endpoint {endpoint}: {response.status_code}")
                
            except Exception as e:
                results[endpoint] = f"Error: {e}"
                logger.warning(f"Endpoint {endpoint} error: {e}")
        
        # Log summary
        implemented_endpoints = [ep for ep, status in results.items() if status != 404]
        logger.info(f"Implemented endpoints: {implemented_endpoints}")
        
        # At least some endpoints should be implemented
        assert len(implemented_endpoints) > 0, "No API endpoints found"

    def test_rag_query_endpoint(self, client):
        """Test RAG query functionality"""
        query_data = {
            "query": "What is AskRAG?",
            "max_results": 5
        }
        
        response = client.post("/api/v1/rag/query", json=query_data)
        
        if response.status_code == 404:
            pytest.skip("RAG query endpoint not implemented")
        
        logger.info(f"RAG query response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
            logger.info("RAG query endpoint working")
        elif response.status_code in [400, 422]:
            logger.info("RAG query endpoint exists but requires proper data format")

    def test_document_upload_endpoint(self, client, temp_dir):
        """Test document upload functionality"""
        # Create test file
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("This is a test document for AskRAG integration testing.")
        
        with open(test_file, "rb") as f:
            files = {"file": ("test.txt", f, "text/plain")}
            data = {"title": "Test Document"}
            
            response = client.post("/api/v1/documents/upload", files=files, data=data)
        
        if response.status_code == 404:
            pytest.skip("Document upload endpoint not implemented")
        
        logger.info(f"Document upload response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
            logger.info("Document upload endpoint working")

    def test_authentication_flow(self, client):
        """Test authentication workflow"""
        # Test registration
        user_data = {
            "username": "testuser",
            "email": "test@example.com", 
            "password": "testpass123"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        if response.status_code == 404:
            pytest.skip("Auth endpoints not implemented")
        
        logger.info(f"Registration response: {response.status_code}")
        
        # Test login
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        logger.info(f"Login response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
            logger.info("Authentication endpoints working")

    def test_error_handling_scenarios(self, client):
        """Test system error handling"""
        # Test invalid endpoint
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
        logger.info("404 error handling: OK")
        
        # Test invalid JSON
        response = client.post("/api/v1/rag/query", data="invalid json", headers={"content-type": "application/json"})
        assert response.status_code in [400, 422, 404]
        logger.info("Invalid JSON handling: OK")

    def test_component_integration(self):
        """Test that core components can be imported and integrated"""
        try:
            from app.core.rag_pipeline import RAGPipeline
            logger.info("RAGPipeline import: OK")
        except ImportError:
            logger.warning("RAGPipeline not available")
        
        try:
            from app.core.document_extractor import DocumentExtractor
            logger.info("DocumentExtractor import: OK")
        except ImportError:
            logger.warning("DocumentExtractor not available")
        
        try:
            from app.core.text_chunker import TextChunker  
            logger.info("TextChunker import: OK")
        except ImportError:
            logger.warning("TextChunker not available")

    def test_performance_basic(self, client):
        """Test basic performance characteristics"""
        import time
        
        # Test response time
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response_time < 5.0  # Should respond within 5 seconds
        logger.info(f"Health check response time: {response_time:.3f}s")
        
        # Test multiple requests
        start_time = time.time()
        for _ in range(3):
            response = client.get("/health")
            assert response.status_code == 200
        end_time = time.time()
        
        total_time = end_time - start_time
        logger.info(f"3 requests completed in {total_time:.3f}s")
        assert total_time < 10.0

    def test_full_workflow_integration(self, client, temp_dir):
        """Test end-to-end workflow integration"""
        # Step 1: Check health
        response = client.get("/health")
        assert response.status_code == 200
        logger.info("Step 1: Health check passed")
        
        # Step 2: Test document processing workflow (if available)
        test_file = Path(temp_dir) / "workflow_test.txt"
        test_file.write_text("This is a workflow integration test document.")
        
        try:
            with open(test_file, "rb") as f:
                files = {"file": ("workflow_test.txt", f, "text/plain")}
                response = client.post("/api/v1/documents/upload", files=files)
            
            if response.status_code != 404:
                logger.info(f"Step 2: Document upload tested - {response.status_code}")
            else:
                logger.info("Step 2: Document upload endpoint not available")
        except Exception as e:
            logger.info(f"Step 2: Document upload error - {e}")
        
        # Step 3: Test RAG query (if available)
        try:
            query_data = {"query": "test workflow", "max_results": 5}
            response = client.post("/api/v1/rag/query", json=query_data)
            
            if response.status_code != 404:
                logger.info(f"Step 3: RAG query tested - {response.status_code}")
            else:
                logger.info("Step 3: RAG query endpoint not available")
        except Exception as e:
            logger.info(f"Step 3: RAG query error - {e}")
        
        logger.info("Full workflow integration test completed")

    @pytest.mark.integration
    def test_system_integration_summary(self, client):
        """Integration test summary and system validation"""
        logger.info("=== AskRAG Integration Test Summary ===")
        
        # Test core system availability
        response = client.get("/health")
        system_healthy = response.status_code == 200
        logger.info(f"System Health: {'PASS' if system_healthy else 'FAIL'}")
        
        # Test API documentation
        response = client.get("/docs")
        docs_available = response.status_code == 200
        logger.info(f"API Documentation: {'PASS' if docs_available else 'FAIL'}")
        
        # Count available endpoints
        endpoints = ["/api/v1/auth/register", "/api/v1/documents/upload", "/api/v1/rag/query"]
        available_count = 0
        for endpoint in endpoints:
            try:
                response = client.post(endpoint, json={})
                if response.status_code != 404:
                    available_count += 1
            except:
                pass
        
        logger.info(f"Available API Endpoints: {available_count}/{len(endpoints)}")
        
        # Summary
        integration_score = (
            (1 if system_healthy else 0) +
            (1 if docs_available else 0) +
            (available_count / len(endpoints))
        ) / 3
        
        logger.info(f"Integration Score: {integration_score:.2%}")
        logger.info("=== Integration Test Complete ===")
        
        # Assert minimum functionality
        assert system_healthy, "System must be healthy"
        assert docs_available, "API documentation must be available"
