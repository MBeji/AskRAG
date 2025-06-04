"""
Document management endpoints
"""
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from app.models.document import Document, DocumentCreate, DocumentUpdate, DocumentResponse
from app.db.repositories.mock_repositories import get_mock_document_repository

router = APIRouter()

@router.post("/", response_model=DocumentResponse)
async def create_document(
    document: DocumentCreate,
    doc_repo = Depends(get_mock_document_repository)
):
    """Create a new document"""
    try:
        created_doc = await doc_repo.create(document)
        return DocumentResponse(
            id=str(created_doc.id),
            filename=created_doc.filename,
            title=created_doc.title,
            file_type=created_doc.file_type,
            file_size=created_doc.file_size,
            upload_date=created_doc.upload_date,
            user_id=created_doc.user_id,
            chunk_count=created_doc.chunk_count,
            processing_status=created_doc.processing_status,
            tags=created_doc.tags,
            metadata=created_doc.metadata
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    user_id: str = None,
    doc_repo = Depends(get_mock_document_repository)
):
    """List documents"""
    if user_id:
        documents = await doc_repo.get_by_user(user_id, skip=skip, limit=limit)
    else:
        documents = await doc_repo.list(skip=skip, limit=limit)
    
    return [
        DocumentResponse(
            id=str(doc.id),
            filename=doc.filename,
            title=doc.title,
            file_type=doc.file_type,
            file_size=doc.file_size,
            upload_date=doc.upload_date,
            user_id=doc.user_id,
            chunk_count=doc.chunk_count,
            processing_status=doc.processing_status,
            tags=doc.tags,
            metadata=doc.metadata
        ) for doc in documents
    ]

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    doc_repo = Depends(get_mock_document_repository)
):
    """Get a specific document"""
    document = await doc_repo.get_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentResponse(
        id=str(document.id),
        filename=document.filename,
        title=document.title,
        file_type=document.file_type,
        file_size=document.file_size,
        upload_date=document.upload_date,
        user_id=document.user_id,
        chunk_count=document.chunk_count,
        processing_status=document.processing_status,
        tags=document.tags,
        metadata=document.metadata
    )

@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    document_update: DocumentUpdate,
    doc_repo = Depends(get_mock_document_repository)
):
    """Update a document"""
    document = await doc_repo.update(document_id, document_update)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentResponse(
        id=str(document.id),
        filename=document.filename,
        title=document.title,
        file_type=document.file_type,
        file_size=document.file_size,
        upload_date=document.upload_date,
        user_id=document.user_id,
        chunk_count=document.chunk_count,
        processing_status=document.processing_status,
        tags=document.tags,
        metadata=document.metadata
    )

@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    doc_repo = Depends(get_mock_document_repository)
):
    """Delete a document"""
    success = await doc_repo.delete(document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document deleted successfully"}

@router.get("/{document_id}/search")
async def search_document(
    document_id: str,
    query: str,
    doc_repo = Depends(get_mock_document_repository)
):
    """Search within a specific document"""
    document = await doc_repo.get_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Simple text search in content
    if query.lower() in document.content.lower():
        return {
            "document_id": document_id,
            "query": query,
            "found": True,
            "content_preview": document.content[:200] + "..."
        }
    else:
        return {
            "document_id": document_id,
            "query": query,
            "found": False,
            "content_preview": None
        }
