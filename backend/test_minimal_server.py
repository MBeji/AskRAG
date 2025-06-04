"""
Minimal FastAPI test server for authentication endpoints
"""
try:
    from fastapi import FastAPI, HTTPException, Depends
    from fastapi.security import HTTPBearer
    from pydantic import BaseModel, EmailStr
    import uvicorn
    
    app = FastAPI(title="AskRAG Auth Test", version="1.0.0")
    security = HTTPBearer()
    
    # Simple models for testing
    class UserLogin(BaseModel):
        email: str
        password: str
    
    class Token(BaseModel):
        access_token: str
        token_type: str = "bearer"
    
    @app.get("/")
    async def root():
        return {"message": "AskRAG Authentication Test Server", "status": "running"}
    
    @app.get("/health")
    async def health():
        return {"status": "healthy", "service": "auth"}
    
    @app.post("/api/v1/auth/login", response_model=Token)
    async def login(user_data: UserLogin):
        # Simple mock authentication
        if user_data.email == "test@example.com" and user_data.password == "test123":
            return Token(access_token="mock-jwt-token-12345")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    @app.get("/api/v1/auth/me")
    async def get_current_user(token: str = Depends(security)):
        return {
            "id": "user123",
            "email": "test@example.com",
            "username": "testuser",
            "is_active": True
        }
    
    if __name__ == "__main__":
        print("🚀 Starting AskRAG Authentication Test Server...")
        print("📍 Server will be available at: http://localhost:8000")
        print("📖 API docs at: http://localhost:8000/docs")
        print("🔧 Health check: http://localhost:8000/health")
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info"
        )
        
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("💡 Install with: pip install fastapi uvicorn")
except Exception as e:
    print(f"❌ Error starting server: {e}")
