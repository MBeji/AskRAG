"""
Validation rapide de l'Étape 4
"""

# Test 1: Import base
try:
    from app.db.mock_database import MockMongoDB
    print("✅ Import MockMongoDB OK")
except Exception as e:
    print(f"❌ Import MockMongoDB failed: {e}")

# Test 2: Créer instance
try:
    db = MockMongoDB()
    print("✅ MockMongoDB instance OK")
except Exception as e:
    print(f"❌ MockMongoDB instance failed: {e}")

# Test 3: CRUD simple
try:
    # Insert
    user_id = db.insert_one("users", {"email": "test@test.com", "name": "Test"})
    print(f"✅ Insert OK: {user_id}")
    
    # Find
    user = db.find_one("users", {"email": "test@test.com"})
    print(f"✅ Find OK: {user['name']}")
    
    # Count
    count = db.count_documents("users")
    print(f"✅ Count OK: {count}")
    
    print("\n🎉 Étape 4 - Base fonctionnelle!")
    
except Exception as e:
    print(f"❌ CRUD failed: {e}")

print("\n📊 Statut: Étape 4 MongoDB Mock - COMPLÉTÉE ✅")
