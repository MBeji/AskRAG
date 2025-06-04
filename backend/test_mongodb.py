"""
Test MongoDB connection and database functionality
"""
import asyncio
import sys
import logging
from pathlib import Path

# Add app directory to path
sys.path.append(str(Path(__file__).parent / "app"))

from app.db.connection import connect_to_mongo, close_mongo_connection, get_database
from app.db.init_db import check_database_connection, init_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_connection():
    """Test MongoDB connection"""
    try:
        print("🔍 Testing MongoDB connection...")
        
        # Test basic connection
        result = await check_database_connection()
        if result:
            print("✅ MongoDB connection successful!")
        else:
            print("❌ MongoDB connection failed!")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False


async def test_database_operations():
    """Test basic database operations"""
    try:
        print("\n🔍 Testing database operations...")
        
        # Connect to database
        await connect_to_mongo()
        db = get_database()
        
        # Test collection operations
        test_collection = db["test_collection"]
        
        # Insert test document
        test_doc = {"name": "test", "status": "testing"}
        result = await test_collection.insert_one(test_doc)
        print(f"✅ Insert test document: {result.inserted_id}")
        
        # Find test document
        found_doc = await test_collection.find_one({"_id": result.inserted_id})
        print(f"✅ Found test document: {found_doc['name']}")
        
        # Delete test document
        delete_result = await test_collection.delete_one({"_id": result.inserted_id})
        print(f"✅ Deleted test document: {delete_result.deleted_count} documents")
        
        # Clean up test collection
        await db.drop_collection("test_collection")
        print("✅ Cleaned up test collection")
        
        await close_mongo_connection()
        return True
        
    except Exception as e:
        print(f"❌ Database operations test failed: {e}")
        await close_mongo_connection()
        return False


async def test_repositories():
    """Test repository functionality"""
    try:
        print("\n🔍 Testing repository functionality...")
        
        # Import repositories here to avoid import issues
        from app.db.repositories import UserRepository, DocumentRepository, ChatRepository
        from app.models.user import UserCreate
        
        await connect_to_mongo()
        
        # Test user repository
        user_repo = UserRepository()
        test_user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            password="test123",
            bio="Test user for repository testing"
        )
        
        # Check if user exists (from previous tests)
        existing_user = await user_repo.get_by_email("test@example.com")
        if existing_user:
            await user_repo.delete(str(existing_user.id))
            print("✅ Cleaned up existing test user")
        
        # Create test user
        test_user = await user_repo.create(test_user_data, "hashed_password_123")
        print(f"✅ Created test user: {test_user.email}")
        
        # Get user by ID
        found_user = await user_repo.get_by_id(str(test_user.id))
        print(f"✅ Found user by ID: {found_user.username}")
        
        # Clean up
        await user_repo.delete(str(test_user.id))
        print("✅ Cleaned up test user")
        
        await close_mongo_connection()
        return True
        
    except Exception as e:
        print(f"❌ Repository test failed: {e}")
        await close_mongo_connection()
        return False


async def main():
    """Run all tests"""
    print("🚀 Starting MongoDB tests...\n")
    
    tests = [
        ("MongoDB Connection", test_connection),
        ("Database Operations", test_database_operations),
        ("Repository Functionality", test_repositories),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Testing: {test_name}")
        print('='*50)
        
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print('='*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! MongoDB is ready to use.")
    else:
        print("⚠️  Some tests failed. Check the logs above.")


if __name__ == "__main__":
    asyncio.run(main())