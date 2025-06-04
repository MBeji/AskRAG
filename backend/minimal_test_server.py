#!/usr/bin/env python3
"""
Minimal FastAPI server for AskRAG Étape 10 - Testing AuthService static methods
"""
import sys
import os
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from fastapi import FastAPI
from pydantic import BaseModel

# Response models
class StatusResponse(BaseModel):
    status: str
    message: str

# Create FastAPI app
app = FastAPI(
    title="AskRAG Test Server",
    description="Minimal server for testing",
    version="1.0.0"
)

@app.get("/", response_model=StatusResponse)
async def root():
    """Root endpoint"""
    return StatusResponse(status="success", message="Minimal test server is running")

@app.get("/health", response_model=StatusResponse)
async def health_check():
    """Health check endpoint"""
    return StatusResponse(status="healthy", message="Server is operational")

@app.get("/test-auth", response_model=StatusResponse)
async def test_auth():
    """Test AuthService static methods"""
    try:
        from app.core.auth import AuthService
        
        # Test password hashing
        test_password = "test123"
        hashed = AuthService.get_password_hash(test_password)
        verified = AuthService.verify_password(test_password, hashed)
        
        # Test token creation
        token = AuthService.create_access_token(data={"sub": "test-user-id"})
        
        return StatusResponse(
            status="success",
            message=f"AuthService working! Password verify: {verified}, Token length: {len(token)}"
        )
    except Exception as e:
        return StatusResponse(
            status="error",
            message=f"AuthService error: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting minimal test server...")
    print("📡 Server: http://localhost:8005")
    print("🔍 Health: http://localhost:8005/health")
    print("🧪 Test: http://localhost:8005/test-auth")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8005,
        log_level="info"
    )
