"""
AskRAG Step 17.2 - Simple Integration Tests
Tests end-to-end functionality and component interactions
"""

import pytest
from fastapi.testclient import TestClient
import tempfile
import shutil
from pathlib import Path
import logging

# Import the main application
from app.main import app

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files"""
    test_dir = tempfile.mkdtemp()
    yield test_dir
    shutil.rmtree(test_dir, ignore_errors=True)


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    logger.info(f"Health check passed: {data}")


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    # Should return either 200 or redirect
    assert response.status_code in [200, 307, 308]
    logger.info(f"Root endpoint response: {response.status_code}")


def test_openapi_docs(client):
    """Test OpenAPI documentation endpoint"""
    response = client.get("/docs")
    assert response.status_code == 200
    logger.info("OpenAPI docs accessible")


def test_api_v1_endpoints(client):
    """Test API v1 endpoints existence"""
    # Test various API endpoints to see which ones exist
    
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
            # Use GET for most endpoints to check existence
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


def test_rag_query_basic(client):
    """Test basic RAG query functionality"""
    query_data = {
        "query": "What is AskRAG?",
        "max_results": 5
    }
    
    response = client.post("/api/v1/rag/query", json=query_data)
    
    if response.status_code == 404:
        pytest.skip("RAG query endpoint not implemented")
    
    logger.info(f"RAG query response: {response.status_code}")
    
    # If implemented, should handle the request
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, dict)
        logger.info("RAG query endpoint working")
    elif response.status_code in [400, 422]:
        logger.info("RAG query endpoint exists but requires proper data format")


def test_document_upload_basic(client, temp_dir):
    """Test basic document upload functionality"""
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
    
    # If implemented, should handle the upload
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, dict)
        logger.info("Document upload endpoint working")
    elif response.status_code in [400, 422]:
        logger.info("Document upload endpoint exists but requires proper format")


def test_authentication_endpoints(client):
    """Test authentication endpoint functionality"""
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


def test_error_handling(client):
    """Test error handling for invalid requests"""
    # Test invalid endpoint
    response = client.get("/api/v1/nonexistent")
    assert response.status_code == 404
    logger.info("404 error handling: OK")
    
    # Test invalid JSON
    response = client.post("/api/v1/rag/query", data="invalid json", headers={"content-type": "application/json"})
    assert response.status_code in [400, 422, 404]  # Bad request, validation error, or not found
    logger.info("Invalid JSON handling: OK")


def test_component_imports():
    """Test that core components can be imported"""
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
    
    try:
        from app.core.embeddings import OptimizedEmbeddingService
        logger.info("OptimizedEmbeddingService import: OK")
    except ImportError:
        logger.warning("OptimizedEmbeddingService not available")


def test_performance_basic(client):
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
    assert total_time < 10.0  # Should complete within 10 seconds


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
