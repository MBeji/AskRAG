"""
Simple Integration Test for AskRAG - Step 17.2
"""

import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

print("🚀 AskRAG Integration Tests - Step 17.2")
print("=" * 50)

# Test 1: Core Component Imports
print("\n📦 Testing Core Component Imports...")
import_results = {}

try:
    from app.core.rag_pipeline import RAGPipeline
    print("✅ RAGPipeline import: SUCCESS")
    import_results['RAGPipeline'] = True
except Exception as e:
    print(f"❌ RAGPipeline import: FAILED - {e}")
    import_results['RAGPipeline'] = False

try:
    from app.core.document_extractor import DocumentExtractor
    print("✅ DocumentExtractor import: SUCCESS")
    import_results['DocumentExtractor'] = True
except Exception as e:
    print(f"❌ DocumentExtractor import: FAILED - {e}")
    import_results['DocumentExtractor'] = False

try:
    from app.core.text_chunker import TextChunker
    print("✅ TextChunker import: SUCCESS")
    import_results['TextChunker'] = True
except Exception as e:
    print(f"❌ TextChunker import: FAILED - {e}")
    import_results['TextChunker'] = False

try:
    from app.core.optimized_embeddings import OptimizedEmbeddingService
    print("✅ OptimizedEmbeddingService import: SUCCESS")
    import_results['OptimizedEmbeddingService'] = True
except Exception as e:
    print(f"❌ OptimizedEmbeddingService import: FAILED - {e}")
    import_results['OptimizedEmbeddingService'] = False

# Test 2: FastAPI Basic Test
print("\n🌐 Testing FastAPI Basic Functionality...")
try:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    
    app = FastAPI(title="AskRAG Test")
    
    @app.get("/health")
    def health():
        return {"status": "healthy"}
    
    client = TestClient(app)
    response = client.get("/health")
    
    if response.status_code == 200:
        print("✅ FastAPI basic functionality: SUCCESS")
        fastapi_test = True
    else:
        print(f"❌ FastAPI response error: {response.status_code}")
        fastapi_test = False
        
except Exception as e:
    print(f"❌ FastAPI basic functionality: FAILED - {e}")
    fastapi_test = False

# Test 3: Document Processing
print("\n📄 Testing Document Processing...")
try:
    import tempfile
    from pathlib import Path
    
    # Create test file
    temp_dir = tempfile.mkdtemp()
    test_file = Path(temp_dir) / "test.txt"
    test_content = "This is a test document for integration testing."
    test_file.write_text(test_content)
    
    if import_results.get('DocumentExtractor', False):
        extractor = DocumentExtractor()
        content = extractor.extract_content(str(test_file))
        
        if content and content.strip() and "integration testing" in content:
            print("✅ Document processing: SUCCESS")
            doc_processing = True
        else:
            print(f"❌ Document processing: Content extraction failed - got: '{content}'")
            doc_processing = False
    else:
        print("⚠️  Document processing: Skipped (DocumentExtractor not available)")
        doc_processing = None
        
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)
    
except Exception as e:
    print(f"❌ Document processing: FAILED - {e}")
    doc_processing = False

# Test 4: Text Chunking
print("\n✂️  Testing Text Chunking...")
try:
    if import_results.get('TextChunker', False):
        chunker = TextChunker()
        test_text = "This is a test text for chunking. " * 20  # Make it longer to ensure chunking
        chunks = chunker.chunk_text(test_text)
        
        if chunks and len(chunks) > 0 and any(chunk.strip() for chunk in chunks):
            print(f"✅ Text chunking: SUCCESS - {len(chunks)} chunks created")
            text_chunking = True
        else:
            print(f"❌ Text chunking: No valid chunks created - got: {chunks}")
            text_chunking = False
    else:
        print("⚠️  Text chunking: Skipped (TextChunker not available)")
        text_chunking = None
        
except Exception as e:
    print(f"❌ Text chunking: FAILED - {e}")
    text_chunking = False

# Test 5: Cache Operations
print("\n🗄️  Testing Cache Operations...")
try:
    from app.utils.cache import CacheManager
    
    cache = CacheManager()
    cache.set("test_key", {"data": "test_value"})
    result = cache.get("test_key")
    
    if result and result.get("data") == "test_value":
        print("✅ Cache operations: SUCCESS")
        cache_test = True
    else:
        print("❌ Cache operations: Data mismatch")
        cache_test = False
        
except Exception as e:
    print(f"❌ Cache operations: FAILED - {e}")
    cache_test = False

# Summary
print("\n" + "=" * 50)
print("📊 INTEGRATION TEST SUMMARY")
print("=" * 50)

# Count successful tests
successful_imports = sum(import_results.values())
total_imports = len(import_results)
print(f"Core Components: {successful_imports}/{total_imports} imported successfully")

other_tests = [fastapi_test, doc_processing, text_chunking, cache_test]
successful_other = sum(1 for test in other_tests if test is True)
total_other = sum(1 for test in other_tests if test is not None)

print(f"Functionality Tests: {successful_other}/{total_other} passed")

# Overall score
total_successful = successful_imports + successful_other
total_tests = total_imports + total_other
overall_score = total_successful / total_tests if total_tests > 0 else 0

print(f"Overall Score: {total_successful}/{total_tests} ({overall_score:.1%})")

# Final assessment
if overall_score >= 0.8:
    print("🎉 Assessment: EXCELLENT - System is highly functional")
elif overall_score >= 0.6:
    print("✅ Assessment: GOOD - System is well functional")
elif overall_score >= 0.4:
    print("⚠️  Assessment: ACCEPTABLE - System has basic functionality")
else:
    print("❌ Assessment: NEEDS IMPROVEMENT - System has limited functionality")

print("\n✨ AskRAG Step 17.2 Integration Tests Complete!")
print("=" * 50)
