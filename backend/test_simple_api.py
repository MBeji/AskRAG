"""
Test de l'API avec endpoints simplifiés
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="AskRAG API",
    description="RAG API avec base de données mock",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data
mock_data = {
    "users": [
        {"id": "1", "email": "admin@askrag.com", "username": "admin", "full_name": "Administrator"},
        {"id": "2", "email": "demo@askrag.com", "username": "demo", "full_name": "Demo User"}
    ],
    "documents": [
        {"id": "1", "filename": "demo.pdf", "title": "Document Demo", "user_id": "1"},
        {"id": "2", "filename": "test.txt", "title": "Document Test", "user_id": "2"}
    ]
}

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AskRAG API",
        "version": "1.0.0",
        "status": "running",
        "database": "mock"
    }

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "service": "askrag-api",
        "database": "mock",
        "users_count": len(mock_data["users"]),
        "documents_count": len(mock_data["documents"])
    }

@app.get("/api/v1/health")
async def api_health():
    """API v1 health"""
    return {"status": "healthy", "api_version": "v1"}

@app.get("/api/v1/database/stats")
async def get_stats():
    """Database stats"""
    return {
        "total_users": len(mock_data["users"]),
        "total_documents": len(mock_data["documents"]),
        "database_type": "mock",
        "status": "healthy"
    }

@app.get("/api/v1/database/users")
async def list_users():
    """List users"""
    return {
        "users": mock_data["users"],
        "count": len(mock_data["users"])
    }

@app.get("/api/v1/database/documents")
async def list_documents():
    """List documents"""
    return {
        "documents": mock_data["documents"],
        "count": len(mock_data["documents"])
    }

@app.get("/api/v1/database/test-connection")
async def test_connection():
    """Test connection"""
    return {
        "status": "success",
        "message": "Mock database connection successful",
        "database_type": "mock"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
