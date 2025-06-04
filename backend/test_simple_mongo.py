"""
Simple MongoDB connection test
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def test_mongodb():
    """Test basic MongoDB connection"""
    try:
        print("🔍 Testing MongoDB connection...")
        
        # MongoDB connection string
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        database_name = os.getenv("DATABASE_NAME", "askrag_db")
        
        print(f"Connecting to: {mongodb_url}")
        print(f"Database: {database_name}")
        
        # Create client
        client = AsyncIOMotorClient(mongodb_url)
        
        # Test connection with ping
        await client.admin.command('ping')
        print("✅ MongoDB ping successful!")
        
        # Get database
        db = client[database_name]
        
        # Test a simple operation
        test_collection = db.test_collection
        
        # Insert a test document
        result = await test_collection.insert_one({"test": "hello", "timestamp": "2024"})
        print(f"✅ Inserted test document with ID: {result.inserted_id}")
        
        # Find the document
        doc = await test_collection.find_one({"_id": result.inserted_id})
        print(f"✅ Found document: {doc}")
        
        # Delete the test document
        await test_collection.delete_one({"_id": result.inserted_id})
        print("✅ Cleaned up test document")
        
        # Close connection
        client.close()
        print("✅ Connection closed successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ MongoDB test failed: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

async def main():
    print("🚀 Starting simple MongoDB test...\n")
    success = await test_mongodb()
    
    if success:
        print("\n🎉 MongoDB is working correctly!")
    else:
        print("\n❌ MongoDB test failed. Check if MongoDB is installed and running.")
        print("\nTo install MongoDB Community Server:")
        print("1. Download from: https://www.mongodb.com/try/download/community")
        print("2. Install and start the MongoDB service")
        print("3. Default connection: mongodb://localhost:27017")

if __name__ == "__main__":
    asyncio.run(main())
