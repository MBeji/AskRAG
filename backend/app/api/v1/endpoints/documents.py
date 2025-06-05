from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from typing import List, Optional
from beanie import PydanticObjectId # For type hinting doc_id in path

from app.models.user import User as UserModel # Beanie User model
from app.models.document import Document as DocumentModel # Beanie Document model
from app.schemas.document import DocumentOut # Pydantic schema for responses
from app.services.auth_service import get_current_active_user
from app.services.document_service import (
    save_uploaded_file,
    list_documents_for_user,
    get_document_by_id
)

router = APIRouter()

@router.post("/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_new_document(
    file: UploadFile = File(...),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Upload a new document.
    The file will be saved, and its metadata stored in the database.
    """
    try:
        document_db = await save_uploaded_file(file=file, uploader=current_user)
        # Convert DocumentModel (Beanie) to DocumentOut (Pydantic schema) for response
        return DocumentOut.model_validate(document_db) # Pydantic v2
    except HTTPException as e:
        # Re-raise HTTPExceptions (e.g., from file validation)
        raise e
    except Exception as e:
        # Catch any other errors during file processing
        # Log the error e for debugging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the file: {str(e)}"
        )

@router.get("/", response_model=List[DocumentOut])
async def get_user_documents(
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    List all documents uploaded by the current user.
    """
    documents_db = await list_documents_for_user(user=current_user)
    # Convert list of DocumentModel to list of DocumentOut
    return [DocumentOut.model_validate(doc) for doc in documents_db]

@router.get("/{doc_id}", response_model=DocumentOut)
async def get_specific_document(
    doc_id: PydanticObjectId, # Use PydanticObjectId for path param validation/conversion
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Get a specific document by its ID.
    Ensures the document belongs to the current user.
    """
    document_db = await get_document_by_id(doc_id=doc_id, user=current_user)
    if not document_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or you do not have permission to access it."
        )
    return DocumentOut.model_validate(document_db)

# Optional: Add a delete endpoint as per common CRUD operations
# @router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_user_document(
#     doc_id: PydanticObjectId,
#     current_user: UserModel = Depends(get_current_active_user)
# ):
#     """
#     Delete a specific document by its ID.
#     Ensures the document belongs to the current user.
#     """
#     document = await get_document_by_id(doc_id=doc_id, user=current_user)
#     if not document:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Document not found or you do not have permission to delete it."
#         )
    
#     # Delete from DB (Beanie)
#     await document.delete()
    
#     # Delete file from filesystem (add this to document_service if not there)
#     # from app.services.document_service import delete_physical_file
#     # if document.file_path:
#     #     await delete_physical_file(document.file_path)

#     return Response(status_code=status.HTTP_204_NO_CONTENT)
