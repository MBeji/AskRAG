"""
API v1 router configuration.
"""

from fastapi import APIRouter

# Import API endpoints
from app.api.v1.endpoints import auth, database, users, documents
from app.api.v1.endpoints import rag as rag_router_module # Import the module

api_router = APIRouter()

# Include authentication endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# Include database endpoints
api_router.include_router(database.router, prefix="/database", tags=["database"])

# Include user endpoints
api_router.include_router(users.router, prefix="/users", tags=["users"])

# Include document endpoints
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])

# Include RAG endpoints
api_router.include_router(rag_router_module.router, prefix="/rag", tags=["rag"])

# Health check endpoint for API v1
@api_router.get("/health")
async def api_health():
    """API v1 health check."""
    return {"status": "healthy", "api_version": "v1"}

# Additional endpoints now included:
# ✅ auth endpoints (implemented)
# ✅ users endpoints (implemented)
# ✅ documents endpoints (implemented)
# ✅ rag endpoints (Step 14 search endpoint added)
