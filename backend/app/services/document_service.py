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
