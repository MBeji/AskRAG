"""
Document ingestion and processing service
Handles file uploads, content extraction, and storage management
"""
import os
import uuid
import hashlib
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Tuple, BinaryIO
from datetime import datetime

from fastapi import UploadFile, HTTPException
import aiofiles
import aiofiles.os

from app.models.document import Document, DocumentCreate
from app.core.config import get_settings

settings = get_settings()

class DocumentService:
    """Service for document ingestion and processing"""
    
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.max_file_size = getattr(settings, 'MAX_FILE_SIZE', 10 * 1024 * 1024)  # 10MB default
        self.allowed_extensions = {
            '.txt', '.md', '.pdf', '.doc', '.docx', 
            '.json', '.csv', '.rtf', '.html', '.htm'
        }
        self.allowed_mime_types = {
            'text/plain', 'text/markdown', 'text/html', 'text/csv',
            'application/pdf', 'application/json',
            'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/rtf', 'application/octet-stream', 'application/binary'
        }
    
    async def ensure_upload_directory(self) -> None:
        """Create upload directory if it doesn't exist"""
        await aiofiles.os.makedirs(self.upload_dir, exist_ok=True)
    
    def validate_file(self, file: UploadFile) -> Tuple[bool, str]:
        """Validate uploaded file"""
        if not file.filename:
            return False, "No filename provided"
        
        # Check file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in self.allowed_extensions:
            return False, f"File extension {file_ext} not allowed. Allowed: {', '.join(self.allowed_extensions)}"
        
        # Check MIME type - but be more permissive for common generic types
        if file.content_type:
            # Allow generic MIME types like application/octet-stream if file extension is valid
            if (file.content_type not in self.allowed_mime_types and 
                file.content_type not in ['application/octet-stream', 'application/binary']):
                return False, f"MIME type {file.content_type} not supported for {file_ext} files"
        
        return True, "Valid file"
    
    def generate_safe_filename(self, original_filename: str, user_id: Optional[str] = None) -> str:
        """Generate a safe, unique filename"""
        # Get file extension
        file_ext = Path(original_filename).suffix.lower()
        
        # Create unique identifier
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        
        # Include user_id if provided
        if user_id:
            safe_name = f"{user_id}_{timestamp}_{unique_id}{file_ext}"
        else:
            safe_name = f"{timestamp}_{unique_id}{file_ext}"
        
        return safe_name
    
    async def save_uploaded_file(self, file: UploadFile, safe_filename: str) -> Tuple[str, int]:
        """Save uploaded file to disk"""
        await self.ensure_upload_directory()
        
        file_path = self.upload_dir / safe_filename
        file_size = 0
        
        try:
            async with aiofiles.open(file_path, 'wb') as buffer:
                while chunk := await file.read(1024):
                    file_size += len(chunk)
                    
                    # Check file size limit
                    if file_size > self.max_file_size:
                        await aiofiles.os.remove(file_path)
                        raise HTTPException(
                            status_code=413, 
                            detail=f"File too large. Max size: {self.max_file_size} bytes"
                        )
                    
                    await buffer.write(chunk)
        
        except Exception as e:
            # Clean up partial file
            try:            await aiofiles.os.remove(file_path)
            except:
                pass
            raise e
        
        return str(file_path), file_size
    
    async def extract_text_content(self, file_path: str, file_type: str) -> str:
        """Extract text content from uploaded file"""
        try:
            if file_type in ['.txt', '.md', '.html', '.htm', '.csv', '.rtf']:
                # Read text files directly
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                return content
            
            elif file_type == '.json':
                # Read JSON files
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                return f"JSON Content:\n{content}"
            
            elif file_type == '.pdf':
                # Extract PDF content using pdfplumber
                try:
                    import pdfplumber
                    text_content = []
                    with pdfplumber.open(file_path) as pdf:
                        for page in pdf.pages:
                            text = page.extract_text()
                            if text:
                                text_content.append(text)
                    
                    if text_content:
                        return "\n\n".join(text_content)
                    else:
                        return f"[PDF] File: {Path(file_path).name} - No extractable text found"
                except Exception as e:
                    return f"[PDF Error] File: {Path(file_path).name} - {str(e)}"
            
            elif file_type in ['.doc', '.docx']:
                # Extract Word document content
                try:
                    from docx import Document
                    doc = Document(file_path)
                    paragraphs = []
                    for paragraph in doc.paragraphs:
                        if paragraph.text.strip():
                            paragraphs.append(paragraph.text)
                    
                    if paragraphs:
                        return "\n\n".join(paragraphs)
                    else:
                        return f"[Word] File: {Path(file_path).name} - No extractable text found"
                except Exception as e:
                    return f"[Word Error] File: {Path(file_path).name} - {str(e)}"
            
            else:
                return f"[Unsupported Format] File: {Path(file_path).name} - Content extraction not yet supported"
        
        except Exception as e:
            return f"[Error] Could not extract content: {str(e)}"
    
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of file for deduplication"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
    
    async def process_uploaded_file(
        self, 
        file: UploadFile, 
        title: Optional[str] = None,
        tags: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> DocumentCreate:
        """Process an uploaded file and prepare document data"""
        
        # Validate file
        is_valid, error_msg = self.validate_file(file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Generate safe filename
        safe_filename = self.generate_safe_filename(file.filename, user_id)
        
        # Save file
        file_path, file_size = await self.save_uploaded_file(file, safe_filename)
        
        # Extract content
        file_ext = Path(file.filename).suffix.lower()
        content = await self.extract_text_content(file_path, file_ext)
        
        # Calculate file hash
        file_hash = self.calculate_file_hash(file_path)
        
        # Prepare document data
        document_data = DocumentCreate(
            filename=file.filename,
            title=title or Path(file.filename).stem,
            content=content,
            file_type=file_ext.lstrip('.'),
            file_size=file_size,
            file_path=file_path,
            user_id=user_id,
            tags=tags or [],
            metadata={
                'original_filename': file.filename,
                'content_type': file.content_type,
                'file_hash': file_hash,
                'upload_timestamp': datetime.utcnow().isoformat(),
                **(metadata or {})
            }
        )
        
        return document_data
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete a file from storage"""
        try:
            if os.path.exists(file_path):
                await aiofiles.os.remove(file_path)
                return True
            return False
        except Exception:
            return False
    
    async def get_storage_stats(self) -> Dict:
        """Get storage statistics"""
        try:
            total_size = 0
            file_count = 0
            
            if self.upload_dir.exists():
                for file_path in self.upload_dir.rglob('*'):
                    if file_path.is_file():
                        file_count += 1
                        total_size += file_path.stat().st_size
            
            return {
                'total_files': file_count,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'upload_directory': str(self.upload_dir)
            }
        except Exception as e:
            return {
                'error': str(e),
                'total_files': 0,
                'total_size_bytes': 0,
                'total_size_mb': 0,
                'upload_directory': str(self.upload_dir)
            }

# Singleton instance
document_service = DocumentService()

async def get_document_service() -> DocumentService:
    """Dependency to get document service"""
    return document_service

# --- New functions as per Step 10 requirements ---
from app.models.user import User as UserModel # Beanie User model
from app.models.document import Document as DocumentModel # Beanie Document model
from app.core.config import settings # Re-import for direct access if needed, or use existing 'settings'
from beanie import PydanticObjectId # For type hinting doc_id

# Ensure UPLOAD_DIR exists (can be called at app startup too)
# Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True) # Done by ensure_upload_directory

async def save_uploaded_file(file: UploadFile, uploader: UserModel) -> DocumentModel:
    """
    Validates, saves an uploaded file, and creates a DocumentDB record.
    """
    # Use existing document_service instance for validation and file operations
    # This is a temporary measure; ideally, DocumentService methods would be refactored
    # or these new functions would incorporate all logic if DocumentService is deprecated.

    # 1. Validate file type and basic properties (using DocumentService helpers)
    # Ensure filename is not None
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in settings.ALLOWED_EXTENSIONS: # Using settings directly
        raise HTTPException(
            status_code=400,
            detail=f"File extension {file_extension} not allowed. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # (Content-type validation can be tricky, often done more loosely or via magic bytes)

    # 2. Generate a secure filename
    # Use a simpler UUID-based filename for now, or adapt DocumentService.generate_safe_filename
    secure_filename = f"{uuid.uuid4()}{file_extension}"
    upload_dir = Path(settings.UPLOAD_DIR)
    await aiofiles.os.makedirs(upload_dir, exist_ok=True)
    file_path = upload_dir / secure_filename

    # 3. Save the file to UPLOAD_DIR, checking size
    file_size = 0
    try:
        async with aiofiles.open(file_path, 'wb') as buffer:
            while chunk := await file.read(8192): # Read in chunks
                file_size += len(chunk)
                if file_size > settings.MAX_UPLOAD_SIZE:
                    await aiofiles.os.remove(file_path) # Clean up partial file
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE / (1024*1024):.2f}MB"
                    )
                await buffer.write(chunk)
    except Exception as e:
        # Ensure cleanup if error occurs during write
        if await aiofiles.os.path.exists(file_path):
            await aiofiles.os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")


    # 4. Create DocumentModel instance
    doc_db = DocumentModel(
        filename=file.filename, # Original filename
        filename_on_disk=secure_filename, # Store the secure name used on disk
        content_type=file.content_type or "application/octet-stream",
        uploader_id=str(uploader.id),
        upload_date=datetime.utcnow(),
        status="pending_extraction", # Initial status before text extraction
        file_path=str(file_path.resolve()), # Store absolute path
        file_size=file_size,
        metadata={"original_filename": file.filename, "secure_filename": secure_filename}
    )

    # 5. Save initial DocumentModel to MongoDB
    await doc_db.insert()

    # 6. Perform synchronous text extraction
    try:
        # Import the global instance of DocumentExtractor
        from app.core.document_extractor import document_extractor as global_doc_extractor

        # Read the saved file content for extraction if extractor expects bytes,
        # or pass file_path if it can read from path.
        # The existing DocumentExtractor.extract_content can take file_path.
        extraction_result = global_doc_extractor.extract_content(
            file_path=str(file_path.resolve()),
            filename=secure_filename # or file.filename
        )

        if extraction_result.get('extraction_success', False):
            doc_db.extracted_text = extraction_result.get('content')
            doc_db.status = "text_extracted"
            # Update metadata if extractor provides more (e.g., page count for PDF)
            if 'metadata' in extraction_result and isinstance(extraction_result['metadata'], dict):
                doc_db.metadata.update(extraction_result['metadata'])
        else:
            doc_db.status = "failed_extraction"
            doc_db.processing_error = extraction_result.get('error', 'Unknown extraction error.')

        await doc_db.save() # Save updates (extracted_text, status, potentially new metadata)

        # 7. Perform synchronous chunking and embedding generation if text extraction was successful
        if doc_db.status == "text_extracted" and doc_db.extracted_text:
            try:
                from app.core.text_chunker import chunk_text_langchain
                from app.core.embeddings import generate_embeddings as gen_embeddings_func

                text_chunks = chunk_text_langchain(
                    doc_db.extracted_text,
                    chunk_size=settings.TEXT_CHUNK_SIZE,
                    chunk_overlap=settings.TEXT_CHUNK_OVERLAP
                )

                if text_chunks:
                    embeddings_list = await gen_embeddings_func(texts=text_chunks)

                    doc_db.chunks = []
                    for i, chunk_str in enumerate(text_chunks):
                        doc_db.chunks.append({
                            "chunk_text": chunk_str,
                            "embedding": embeddings_list[i],
                            "faiss_id": None # To be filled in Step 13
                        })

                    doc_db.status = "vectorized_pending_storage" # Embeddings generated, pending storage in FAISS
                    await doc_db.save() # Save chunks with embeddings before adding to FAISS

                    # Now add to FAISS
                    from app.core.vector_store import vector_store as global_vector_store
                    if global_vector_store is None:
                        raise RuntimeError("Vector store not available.")

                    chunk_embeddings = [chunk["embedding"] for chunk in doc_db.chunks]
                    # Create unique IDs for each chunk to map back from FAISS
                    # Format: "mongo_document_id:chunk_index"
                    document_chunk_ids = [f"{str(doc_db.id)}:{i}" for i in range(len(doc_db.chunks))]

                    faiss_ids = global_vector_store.add_embeddings(chunk_embeddings, document_chunk_ids)

                    # Update chunks with their FAISS IDs
                    for i, faiss_id_val in enumerate(faiss_ids):
                        if doc_db.chunks: # Type guard
                           doc_db.chunks[i]["faiss_id"] = faiss_id_val

                    global_vector_store.save_index() # Persist FAISS index and map
                    doc_db.status = "completed" # Or "vectorized_and_stored"
                else:
                    # No chunks produced, maybe text was too short or only whitespace
                    doc_db.status = "text_extracted" # Or a new status like "no_chunks_generated", effectively completed if no text.

                await doc_db.save() # Save the final state with FAISS IDs and updated status

            except Exception as emb_ex:
                # Log this error
                # print(f"Error during chunking/embedding for {doc_db.id}: {emb_ex}") # Replace with proper logging
                doc_db.status = "failed_vectorization"
                doc_db.processing_error = f"Chunking/Embedding error: {str(emb_ex)}"
                await doc_db.save()

    except Exception as e: # This outer try-except handles errors from file saving or initial text extraction
        # Log this error
        # print(f"Error during initial file processing for {doc_db.id if 'doc_db' in locals() else 'unknown_file'}: {e}")
        if 'doc_db' in locals() and doc_db.id: # If doc was already created
            doc_db.status = "failed_extraction" # Or a more generic "processing_failed"
            doc_db.processing_error = str(e)
            await doc_db.save()
        # If error happened before doc_db creation, it's raised by save_uploaded_file's earlier checks/io
        # Depending on policy, you might re-raise or just let the upload succeed with failed status
        # For now, if an error happened that wasn't an HTTPException from validation, it's caught here.
        # If it's an HTTPException (like size limit), it would have been raised already.

    return doc_db # Return the (potentially updated) document object

async def list_documents_for_user(user: UserModel) -> List[DocumentModel]:
    """
    Retrieves all documents uploaded by a specific user.
    """
    # Assuming uploader_id in DocumentModel is a string representation of User's ID.
    # If uploader_id stores PydanticObjectId, ensure comparison is correct.
    documents = await DocumentModel.find(DocumentModel.uploader_id == str(user.id)).to_list()
    return documents

async def get_document_by_id(doc_id: PydanticObjectId, user: UserModel) -> Optional[DocumentModel]:
    """
    Retrieves a specific document by its ID if it belongs to the user.
    """
    document = await DocumentModel.find_one(
        DocumentModel.id == doc_id,
        DocumentModel.uploader_id == str(user.id)
    )
    return document
