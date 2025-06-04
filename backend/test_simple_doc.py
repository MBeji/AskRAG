"""
Simple test for document service
"""
import sys
from pathlib import Path

print("Starting simple test...")

try:
    # Add project root to path
    project_root = Path(__file__).parent
    sys.path.append(str(project_root))
    print(f"Added to path: {project_root}")
    
    # Test import
    from app.core.config import get_settings
    print("✅ Config import successful")
    
    settings = get_settings()
    print(f"✅ Settings loaded - Upload dir: {settings.UPLOAD_DIR}")
    
    # Test dependencies
    try:
        import pdfplumber
        print("✅ pdfplumber available")
    except ImportError as e:
        print(f"❌ pdfplumber error: {e}")
    
    try:
        from docx import Document
        print("✅ python-docx available")
    except ImportError as e:
        print(f"❌ python-docx error: {e}")
    
    print("Test completed successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
