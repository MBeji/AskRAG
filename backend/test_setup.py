"""
Simple test script to verify the FastAPI application setup.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

try:
    from app.main import app
    print("✅ FastAPI app imported successfully!")
    print(f"✅ App title: {app.title}")
    print("✅ Basic structure is working!")
    
    # Test configuration
    from app.core.config import settings
    print(f"✅ Settings loaded: {settings.PROJECT_NAME}")
    print(f"✅ Environment: {settings.ENVIRONMENT}")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n🚀 Ready to start the FastAPI server!")
print("Run: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
