"""
Test rapide des composants - Version simplifiée
"""
import asyncio
from app.db.mock_database import get_mock_database
from app.db.repositories.mock_repositories import MockUserRepository, MockDocumentRepository

async def test_components():
    print("🧪 Test rapide des composants")
    print("=" * 40)
    
    # Test 1: Mock Database
    print("\n1️⃣ Test Mock Database")
    db = get_mock_database()
    print(f"✅ Database initialized: {type(db).__name__}")
    
    # Test 2: User Repository (legacy methods)
    print("\n2️⃣ Test User Repository")
    user_repo = MockUserRepository()
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "full_name": "Test User",
        "password": "testpass123"
    }
    
    user = await user_repo.create_user(user_data)
    print(f"✅ User created: {user['full_name']} ({user['email']})")
    
    # Test 3: Document Repository (legacy methods)
    print("\n3️⃣ Test Document Repository")
    doc_repo = MockDocumentRepository()
    doc_data = {
        "filename": "test.txt",
        "title": "Document de test",
        "content": "Contenu du document de test",
        "file_type": "txt",
        "file_size": 1024,
        "file_path": "/uploads/test.txt",
        "user_id": user["_id"]
    }
    
    document = await doc_repo.create_document(doc_data)
    print(f"✅ Document created: {document['title']}")
    
    # Test 4: List data
    print("\n4️⃣ Test Lists")
    users = await user_repo.get_all_users()
    documents = await doc_repo.get_all_documents()
    print(f"✅ Found {len(users)} users and {len(documents)} documents")
    
    # Test 5: Save data
    print("\n5️⃣ Test Save Data")
    db.save_to_file()
    print("✅ Data saved to mock_database.json")
    
    print("\n🎉 Tous les tests sont passés!")

if __name__ == "__main__":
    asyncio.run(test_components())
