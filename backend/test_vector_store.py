"""
Test script for ChromaDB Vector Store Service
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

import asyncio
import logging
from app.services.vector_store import get_vector_store

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_vector_store():
    """Test ChromaDB vector store functionality"""
    print("🧪 Testing ChromaDB Vector Store...")
    
    # Get vector store instance
    vector_store = get_vector_store()
    
    # Test 1: Health check
    print("\n1️⃣ Testing health check...")
    health = vector_store.health_check()
    print(f"Health status: {health}")
    
    if health["status"] != "healthy":
        print("❌ ChromaDB not healthy, stopping tests")
        return False
    
    # Test 2: Create collection
    print("\n2️⃣ Testing collection creation...")
    test_user_id = "test_user_123"
    collection = vector_store.get_or_create_collection(test_user_id)
    
    if collection:
        print(f"✅ Collection created: {vector_store._get_collection_name(test_user_id)}")
    else:
        print("❌ Failed to create collection")
        return False
    
    # Test 3: Add test embeddings
    print("\n3️⃣ Testing embedding storage...")
    test_chunks = [
        "This is the first test chunk about machine learning.",
        "This is the second test chunk about artificial intelligence.",
        "This is the third test chunk about vector databases."
    ]
    
    # Create dummy embeddings (normally would come from embedding model)
    test_embeddings = [
        [0.1, 0.2, 0.3, 0.4, 0.5] * 20,  # 100 dimensions
        [0.2, 0.3, 0.4, 0.5, 0.6] * 20,
        [0.3, 0.4, 0.5, 0.6, 0.7] * 20
    ]
    
    test_doc_id = "test_document_001"
    success = vector_store.add_document_embeddings(
        user_id=test_user_id,
        document_id=test_doc_id,
        chunks=test_chunks,
        embeddings=test_embeddings,
        metadata={"filename": "test.txt", "type": "test"}
    )
    
    if success:
        print(f"✅ Added {len(test_chunks)} chunks to vector store")
    else:
        print("❌ Failed to add embeddings")
        return False
    
    # Test 4: Search similar chunks
    print("\n4️⃣ Testing similarity search...")
    query_embedding = [0.15, 0.25, 0.35, 0.45, 0.55] * 20  # Similar to first chunk
    
    similar_chunks = vector_store.search_similar_chunks(
        user_id=test_user_id,
        query_embedding=query_embedding,
        n_results=2
    )
    
    if similar_chunks:
        print(f"✅ Found {len(similar_chunks)} similar chunks:")
        for i, chunk in enumerate(similar_chunks):
            print(f"   {i+1}. Similarity: {chunk['similarity_score']:.3f}")
            print(f"      Text: {chunk['chunk_text'][:50]}...")
    else:
        print("❌ No similar chunks found")
        return False
    
    # Test 5: Collection statistics
    print("\n5️⃣ Testing collection statistics...")
    stats = vector_store.get_collection_stats(test_user_id)
    
    if stats:
        print(f"✅ Collection stats: {stats}")
    else:
        print("❌ Failed to get collection stats")
    
    # Test 6: Delete document
    print("\n6️⃣ Testing document deletion...")
    delete_success = vector_store.delete_document(test_user_id, test_doc_id)
    
    if delete_success:
        print(f"✅ Document {test_doc_id} deleted successfully")
    else:
        print("❌ Failed to delete document")
    
    # Final stats
    print("\n7️⃣ Final collection statistics...")
    final_stats = vector_store.get_collection_stats(test_user_id)
    print(f"Final stats: {final_stats}")
    
    print("\n🎉 ChromaDB Vector Store tests completed!")
    return True

if __name__ == "__main__":
    try:
        success = test_vector_store()
        if success:
            print("\n✅ All tests passed!")
        else:
            print("\n❌ Some tests failed!")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        logger.exception("Test error details:")
