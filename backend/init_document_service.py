"""
Initialization script for document service
Creates necessary directories and validates setup
"""
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

print("🚀 Initializing Document Service...")

try:
    from app.services.document_service import DocumentService
    from app.core.config import get_settings
    
    # Get settings
    settings = get_settings()
    print(f"📁 Upload directory: {settings.UPLOAD_DIR}")
    print(f"📏 Max file size: {settings.MAX_UPLOAD_SIZE} bytes")
    
    # Create document service
    doc_service = DocumentService()
    print(f"✅ Document service created")
    print(f"✅ Upload directory: {doc_service.upload_dir}")
    
    # Test file processing capabilities
    print("\n🔧 Testing file processing capabilities:")
    
    # Test PDF processing
    try:
        import pdfplumber
        print("✅ PDF processing: Available (pdfplumber)")
    except ImportError:
        print("❌ PDF processing: Not available")
    
    # Test Word document processing
    try:
        from docx import Document
        print("✅ Word document processing: Available (python-docx)")
    except ImportError:
        print("❌ Word document processing: Not available")
    
    # Test character encoding detection
    try:
        import chardet
        print("✅ Character encoding detection: Available (chardet)")
    except ImportError:
        print("❌ Character encoding detection: Not available")
    
    print("\n🎉 Document service initialization complete!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
