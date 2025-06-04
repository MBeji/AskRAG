"""
Test complet de l'API AskRAG avec tous les endpoints
"""
import asyncio
import aiohttp
import json
from datetime import datetime

BASE_URL = "http://localhost:8002"

async def test_api():
    """Test complet de l'API"""
    print("🧪 Test API AskRAG Complète")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        
        # 1. Test root endpoint
        print("\n1️⃣ Test root endpoint")
        async with session.get(f"{BASE_URL}/") as resp:
            data = await resp.json()
            print(f"✅ Root: {data['message']} - {data['status']}")
            print(f"📊 Stats: {data['stats']}")
        
        # 2. Test health check
        print("\n2️⃣ Test health check")
        async with session.get(f"{BASE_URL}/health") as resp:
            data = await resp.json()
            print(f"✅ Health: {data['status']}")
            print(f"💾 Database: {data['database']['type']} - {data['database']['status']}")
        
        # 3. Test API v1 health
        print("\n3️⃣ Test API v1 health")
        async with session.get(f"{BASE_URL}/api/v1/health") as resp:
            data = await resp.json()
            print(f"✅ API v1 Health: {data['status']} - v{data['api_version']}")
        
        # 4. Test database stats
        print("\n4️⃣ Test database stats")
        async with session.get(f"{BASE_URL}/api/v1/database/stats") as resp:
            data = await resp.json()
            print(f"✅ Database stats: {data['total_users']} users, {data['total_documents']} documents")
        
        # 5. Test users list
        print("\n5️⃣ Test users list")
        async with session.get(f"{BASE_URL}/api/v1/users/") as resp:
            data = await resp.json()
            print(f"✅ Users found: {len(data)}")
            for user in data:
                print(f"   👤 {user['full_name']} ({user['email']})")
        
        # 6. Test documents list
        print("\n6️⃣ Test documents list")
        async with session.get(f"{BASE_URL}/api/v1/documents/") as resp:
            data = await resp.json()
            print(f"✅ Documents found: {len(data)}")
            for doc in data:
                print(f"   📄 {doc['title']} ({doc['file_type']}) - {doc['processing_status']}")
        
        # 7. Test create new user
        print("\n7️⃣ Test create new user")
        new_user = {
            "email": "test@example.com",
            "username": "testuser",
            "full_name": "Test User",
            "password": "testpass123"
        }
        async with session.post(f"{BASE_URL}/api/v1/users/", json=new_user) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"✅ User created: {data['full_name']} (ID: {data['id']})")
                test_user_id = data['id']
            else:
                error = await resp.text()
                print(f"❌ Failed to create user: {error}")
                test_user_id = None
        
        # 8. Test create new document
        print("\n8️⃣ Test create new document")
        new_doc = {
            "filename": "test-doc.txt",
            "title": "Document de test",
            "content": "Ceci est un document de test créé via l'API.",
            "file_type": "txt",
            "file_size": 1024,
            "file_path": "/uploads/test-doc.txt",
            "user_id": test_user_id if test_user_id else "1",
            "tags": ["test", "api"],
            "metadata": {"created_via": "api_test"}
        }
        async with session.post(f"{BASE_URL}/api/v1/documents/", json=new_doc) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"✅ Document created: {data['title']} (ID: {data['id']})")
                test_doc_id = data['id']
            else:
                error = await resp.text()
                print(f"❌ Failed to create document: {error}")
                test_doc_id = None
        
        # 9. Test get specific user
        if test_user_id:
            print("\n9️⃣ Test get specific user")
            async with session.get(f"{BASE_URL}/api/v1/users/{test_user_id}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ User details: {data['full_name']} - Active: {data['is_active']}")
                else:
                    print(f"❌ Failed to get user: {await resp.text()}")
        
        # 10. Test document search
        if test_doc_id:
            print("\n🔟 Test document search")
            async with session.get(f"{BASE_URL}/api/v1/documents/{test_doc_id}/search?query=test") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ Search result: Found={data['found']}")
                    if data['found']:
                        print(f"   📄 Preview: {data['content_preview']}")
                else:
                    print(f"❌ Search failed: {await resp.text()}")
        
        print("\n🎉 Test API complet terminé!")

async def test_error_handling():
    """Test la gestion d'erreurs"""
    print("\n🔧 Test gestion d'erreurs")
    print("=" * 30)
    
    async with aiohttp.ClientSession() as session:
        
        # Test user not found
        async with session.get(f"{BASE_URL}/api/v1/users/nonexistent") as resp:
            if resp.status == 404:
                print("✅ User not found handled correctly")
            else:
                print(f"❌ Unexpected status for nonexistent user: {resp.status}")
        
        # Test document not found
        async with session.get(f"{BASE_URL}/api/v1/documents/nonexistent") as resp:
            if resp.status == 404:
                print("✅ Document not found handled correctly")
            else:
                print(f"❌ Unexpected status for nonexistent document: {resp.status}")
        
        # Test duplicate user email
        duplicate_user = {
            "email": "admin@askrag.com",  # Email already exists
            "username": "admin2",
            "full_name": "Admin 2",
            "password": "testpass123"
        }
        async with session.post(f"{BASE_URL}/api/v1/users/", json=duplicate_user) as resp:
            if resp.status == 400:
                print("✅ Duplicate email handled correctly")
            else:
                print(f"❌ Unexpected status for duplicate email: {resp.status}")

if __name__ == "__main__":
    print("🚀 Démarrage des tests...")
    print("⚠️  Assurez-vous que l'API tourne sur le port 8002")
    print("💡 Commande: python app_complete.py")
    print()
    
    try:
        asyncio.run(test_api())
        asyncio.run(test_error_handling())
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        print("💡 Vérifiez que l'API est démarrée sur http://localhost:8002")
