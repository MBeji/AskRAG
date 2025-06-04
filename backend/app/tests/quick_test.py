import sys
import os
print("🚀 Simple Integration Test Check")

# Test 1: Basic imports
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from app.core.rag_pipeline import RAGPipeline
    print("✅ RAGPipeline: SUCCESS")
except Exception as e:
    print(f"❌ RAGPipeline: {e}")

try:
    from app.core.document_extractor import DocumentExtractor
    print("✅ DocumentExtractor: SUCCESS")
except Exception as e:
    print(f"❌ DocumentExtractor: {e}")

print("✨ Basic test complete")
