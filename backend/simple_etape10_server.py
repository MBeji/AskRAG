#!/usr/bin/env python3
"""
Simple FastAPI server for AskRAG Étape 10
"""
import sys
import os
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import json
try:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
except Exception:
    model = None
try:
    import pdfplumber
except ImportError:
    pdfplumber = None
try:
    import docx
except ImportError:
    docx = None

# Import our components
from app.core.auth import AuthService  # Use static methods version
from app.db.repositories.mock_repositories import MockUserRepository
from app.models.user_v1 import UserCreate, UserLogin, UserResponse
from chat_history import save_chat, get_history
from vector_store import add_document_embeddings, query_similar_chunk
from chat_sessions import create_session, list_sessions

# Simple models for responses
class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class StatusResponse(BaseModel):
    status: str
    message: str

# Create FastAPI app
app = FastAPI(
    title="AskRAG Document Ingestion API",
    description="Authentication and document upload API for Étape 10",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Dependencies
def get_user_repository() -> MockUserRepository:
    return MockUserRepository()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_repo: MockUserRepository = Depends(get_user_repository)
) -> UserResponse:
    """Get current authenticated user"""
    try:
        # Decode JWT token manually
        import jwt
        from app.core.config import settings
        
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        # Get user from repository
        user = await user_repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

# Routes
@app.get("/", response_model=StatusResponse)
async def root():
    """Root endpoint"""
    return StatusResponse(status="success", message="AskRAG Document Ingestion API is running")

@app.get("/health", response_model=StatusResponse)
async def health_check():
    """Health check endpoint"""
    return StatusResponse(status="healthy", message="Server is operational")

@app.post("/api/v1/auth/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    user_repo: MockUserRepository = Depends(get_user_repository)
):
    """Register a new user"""
    # Check if user already exists
    existing_user = await user_repo.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user - password will be hashed in repository
    new_user = await user_repo.create(user_data)
    
    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        username=new_user.username,
        full_name=new_user.full_name,
        is_active=new_user.is_active,
        is_verified=new_user.is_verified,
        is_superuser=new_user.is_superuser,
        created_at=new_user.created_at,
        updated_at=new_user.updated_at,
        last_login=new_user.last_login
    )

@app.post("/api/v1/auth/login", response_model=LoginResponse)
async def login(
    user_credentials: UserLogin,
    user_repo: MockUserRepository = Depends(get_user_repository)
):
    """Login user and return access token"""
    # Get user by email
    user = await user_repo.get_by_email(user_credentials.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password using static method
    if not AuthService.verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create access token using static method
    access_token = AuthService.create_access_token(data={"sub": str(user.id)})
      # Update last login
    await user_repo.update_last_login(user.id)
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login
        )
    )

@app.get("/api/v1/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@app.post("/api/v1/documents/upload", response_model=StatusResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """Upload a document for processing"""
    # Create uploads directory if it doesn't exist
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)
    
    # Save uploaded file
    file_path = uploads_dir / f"{current_user.id}_{file.filename}"
    
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        return StatusResponse(
            status="success",
            message=f"Document '{file.filename}' uploaded successfully for user {current_user.email}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )

@app.get("/api/v1/documents", response_model=StatusResponse)
async def list_documents(current_user: UserResponse = Depends(get_current_user)):
    """List documents for current user"""
    uploads_dir = Path("uploads")
    if not uploads_dir.exists():
        user_files = []
    else:
        user_files = [f.name for f in uploads_dir.glob(f"{current_user.id}_*")]
    
    return StatusResponse(
        status="success",
        message=f"Found {len(user_files)} documents for user {current_user.email}: {', '.join(user_files)}"
    )

@app.post("/api/v1/documents/process", response_model=StatusResponse)
async def process_document(
    filename: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Traite un document uploadé (TXT, PDF, DOCX) : extraction, chunking, embeddings (optionnel), stockage dans data/embeddings.json
    """
    uploads_dir = Path("uploads")
    file_path = uploads_dir / f"{current_user.id}_{filename}"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fichier non trouvé")

    ext = file_path.suffix.lower()
    text = ""
    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        # Chunking simple
        chunks = [text[i:i+500] for i in range(0, len(text), 500)]
    elif ext == ".pdf" and pdfplumber:
        with pdfplumber.open(str(file_path)) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        # Chunking par paragraphe
        chunks = [p for p in text.split("\n\n") if p.strip()]
    elif ext == ".docx" and docx:
        doc = docx.Document(str(file_path))
        text = "\n".join([p.text for p in doc.paragraphs])
        chunks = [p for p in text.split("\n") if p.strip()]
    else:
        raise HTTPException(status_code=415, detail="Format non supporté ou dépendance manquante")

    # Embeddings si possible
    embeddings = None
    if model:
        try:
            embeddings = model.encode(chunks).tolist()
        except Exception:
            embeddings = None

    # Ajout ChromaDB si embeddings OK
    chroma_ok = False
    if embeddings:
        try:
            chroma_ok = add_document_embeddings(current_user.id, filename, chunks, embeddings)
        except Exception:
            chroma_ok = False

    # Stockage dans data/embeddings.json
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    embeddings_path = data_dir / "embeddings.json"
    if embeddings_path.exists():
        with open(embeddings_path, "r", encoding="utf-8") as f:
            all_embeddings = json.load(f)
    else:
        all_embeddings = {}

    all_embeddings[f"{current_user.id}_{filename}"] = {
        "chunks": chunks,
        "embeddings": embeddings
    }

    with open(embeddings_path, "w", encoding="utf-8") as f:
        json.dump(all_embeddings, f, ensure_ascii=False, indent=2)

    return StatusResponse(
        status="success",
        message=f"Document {filename} traité : {len(chunks)} chunks, embeddings={'ok' if embeddings else 'non générés'}, chromadb={'ok' if chroma_ok else 'non'}"
    )

@app.get("/api/v1/rag/history", response_model=StatusResponse)
async def rag_history(current_user: UserResponse = Depends(get_current_user)):
    """
    Retourne l'historique de chat de l'utilisateur
    """
    history = get_history(current_user.id)
    return StatusResponse(status="success", message=json.dumps(history, ensure_ascii=False))

@app.post("/api/v1/rag/ask", response_model=StatusResponse)
async def rag_ask(
    filename: str,
    question: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Endpoint RAG minimal : encode la question, retourne le chunk le plus proche du document
    """
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        query_emb = model.encode([question])[0].tolist()
    except Exception:
        return StatusResponse(status="error", message="Embeddings indisponibles (sentence-transformers non installé)")
    # Recherche ChromaDB si dispo
    best_chunk = None
    try:
        best_chunk = query_similar_chunk(current_user.id, filename, query_emb)
    except Exception:
        best_chunk = None
    if not best_chunk:
        from rag_retrieval import find_best_chunk
        best_chunk = find_best_chunk(current_user.id, filename, query_emb)
    from chat_history import save_chat
    save_chat(current_user.id, question, best_chunk)
    return StatusResponse(status="success", message=best_chunk)

@app.post("/api/v1/rag/llm", response_model=StatusResponse)
async def rag_llm(
    filename: str,
    question: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Génère une réponse à partir du chunk le plus pertinent et d'un LLM local (Ollama/OpenAI). Fallback sur chunk si LLM indisponible.
    """
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        query_emb = model.encode([question])[0].tolist()
    except Exception:
        return StatusResponse(status="error", message="Embeddings indisponibles (sentence-transformers non installé)")
    # Recherche du chunk le plus pertinent
    try:
        from vector_store import query_similar_chunk
        best_chunk = query_similar_chunk(current_user.id, filename, query_emb)
    except Exception:
        from rag_retrieval import find_best_chunk
        best_chunk = find_best_chunk(current_user.id, filename, query_emb)
    # Génération LLM (Ollama local via REST, fallback sur chunk)
    llm_answer = None
    try:
        import requests
        ollama_url = "http://localhost:11434/api/generate"
        payload = {"model": "llama2", "prompt": f"Contexte: {best_chunk}\nQuestion: {question}\nRéponds de façon concise."}
        r = requests.post(ollama_url, json=payload, timeout=10)
        if r.status_code == 200:
            llm_answer = r.json().get("response")
    except Exception:
        llm_answer = None
    answer = llm_answer or best_chunk or "Aucune réponse trouvée."
    # Ajout citation/source
    response = {
        "answer": answer,
        "source": best_chunk
    }
    from chat_history import save_chat
    save_chat(current_user.id, question, answer)
    return StatusResponse(status="success", message=json.dumps(response, ensure_ascii=False))

@app.post("/api/v1/rag/session", response_model=StatusResponse)
async def create_chat_session(
    name: str = None,
    current_user: UserResponse = Depends(get_current_user)
):
    session = create_session(current_user.id, name)
    return StatusResponse(status="success", message=json.dumps(session, ensure_ascii=False))

@app.get("/api/v1/rag/session", response_model=StatusResponse)
async def list_chat_sessions(current_user: UserResponse = Depends(get_current_user)):
    sessions = list_sessions(current_user.id)
    return StatusResponse(status="success", message=json.dumps(sessions, ensure_ascii=False))

@app.get("/api/v1/documents/processed", response_model=StatusResponse)
async def list_processed_documents(current_user: UserResponse = Depends(get_current_user)):
    """
    Liste les documents traités (présents dans data/embeddings.json)
    """
    from pathlib import Path
    import json
    data_dir = Path("data")
    embeddings_path = data_dir / "embeddings.json"
    docs = []
    if embeddings_path.exists():
        with open(embeddings_path, "r", encoding="utf-8") as f:
            all_embeddings = json.load(f)
        prefix = f"{current_user.id}_"
        docs = [k[len(prefix):] for k in all_embeddings.keys() if k.startswith(prefix)]
    return StatusResponse(status="success", message=json.dumps(docs, ensure_ascii=False))

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting AskRAG Document Ingestion Server...")
    print("📡 Server: http://localhost:8002")
    print("📚 Docs: http://localhost:8002/docs")
    print("🔍 Health: http://localhost:8002/health")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8002,
        log_level="info"
    )
