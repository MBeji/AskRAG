"""
Serveur de test simple pour l'authentification AskRAG
Compatible avec le frontend React existant
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
import uvicorn
import jwt
import hashlib
from datetime import datetime, timedelta
from typing import Optional

# Configuration
SECRET_KEY = "test-secret-key-for-development"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI(
    title="AskRAG Auth Test Server",
    description="Serveur de test pour l'authentification AskRAG",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Modèles de données
class LoginRequest(BaseModel):
    username: str  # En fait l'email
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    firstName: str
    lastName: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: str
    email: str
    firstName: str
    lastName: str
    role: str
    isActive: bool
    createdAt: str
    updatedAt: str

class AuthResponse(BaseModel):
    user: UserResponse
    tokens: dict

# Base de données mock (en mémoire)
mock_users = {
    "test@example.com": {
        "id": "user-123",
        "email": "test@example.com",
        "firstName": "Test",
        "lastName": "User",
        "password_hash": "test123",  # En réalité, devrait être hashé
        "role": "USER",
        "isActive": True,
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:00Z"
    }
}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérification simple du mot de passe (pour les tests)"""
    return plain_password == hashed_password

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Récupère l'utilisateur actuel depuis le token JWT"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = mock_users.get(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

# Endpoints

@app.get("/")
async def root():
    return {
        "message": "AskRAG Authentication Test Server", 
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "askrag-auth",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/v1/auth/login")
async def login(login_data: LoginRequest):
    """Endpoint de connexion compatible avec le frontend"""
    user = mock_users.get(login_data.username)
    if not user or not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    refresh_token = create_access_token(
        data={"sub": user["email"], "type": "refresh"}, 
        expires_delta=timedelta(days=7)
    )
    
    user_response = UserResponse(**{k: v for k, v in user.items() if k != "password_hash"})
    
    return AuthResponse(
        user=user_response,
        tokens={
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "tokenType": "bearer"
        }
    )

@app.post("/api/v1/auth/register")
async def register(register_data: RegisterRequest):
    """Endpoint d'inscription"""
    if register_data.email in mock_users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    new_user = {
        "id": f"user-{len(mock_users) + 1}",
        "email": register_data.email,
        "firstName": register_data.firstName,
        "lastName": register_data.lastName,
        "password_hash": register_data.password,  # En réalité, devrait être hashé
        "role": "USER",
        "isActive": True,
        "createdAt": datetime.utcnow().isoformat() + "Z",
        "updatedAt": datetime.utcnow().isoformat() + "Z"
    }
    
    mock_users[register_data.email] = new_user
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user["email"]}, expires_delta=access_token_expires
    )
    refresh_token = create_access_token(
        data={"sub": new_user["email"], "type": "refresh"}, 
        expires_delta=timedelta(days=7)
    )
    
    user_response = UserResponse(**{k: v for k, v in new_user.items() if k != "password_hash"})
    
    return AuthResponse(
        user=user_response,
        tokens={
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "tokenType": "bearer"
        }
    )

@app.get("/api/v1/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Récupère les informations de l'utilisateur actuel"""
    return UserResponse(**{k: v for k, v in current_user.items() if k != "password_hash"})

@app.post("/api/v1/auth/logout")
async def logout():
    """Endpoint de déconnexion"""
    return {"message": "Successfully logged out"}

@app.post("/api/v1/auth/refresh")
async def refresh_token(request: dict):
    """Endpoint de renouvellement de token"""
    refresh_token = request.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token required"
        )
    
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if email is None or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user = mock_users.get(email)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access_token = create_access_token(
            data={"sub": email}, expires_delta=access_token_expires
        )
        new_refresh_token = create_access_token(
            data={"sub": email, "type": "refresh"}, 
            expires_delta=timedelta(days=7)
        )
        
        return {
            "accessToken": new_access_token,
            "refreshToken": new_refresh_token,
            "tokenType": "bearer"
        }
        
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

if __name__ == "__main__":
    print("🚀 Démarrage du serveur d'authentification AskRAG...")
    print("📍 Serveur disponible sur: http://localhost:8000")
    print("📖 Documentation API: http://localhost:8000/docs")
    print("🔧 Health check: http://localhost:8000/health")
    print("\n📋 Credentials de test:")
    print("  Email: test@example.com")
    print("  Password: test123")
    print("\nPress Ctrl+C to stop the server")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=False
    )
