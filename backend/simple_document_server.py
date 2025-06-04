"""
Simple Document Server for testing
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.core.config import get_settings
from app.api.v1.endpoints import documents

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="AskRAG Document Service",
    description="Document ingestion and processing API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents.router, prefix="/api/v1", tags=["documents"])

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "AskRAG Document API"}

if __name__ == "__main__":
    print("🚀 Starting Simple AskRAG Document Server...")
    print(f"📁 Upload directory: {settings.UPLOAD_DIR}")
    print(f"📡 Server will be available at: http://localhost:8000")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
