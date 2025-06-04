"""
Test MongoDB avec simulation en mémoire pour le développement
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

class MockMongoDB:
    """Simulation de MongoDB en mémoire pour le développement"""
    
    def __init__(self):
        self.data: Dict[str, List[Dict]] = {
            "users": [],
            "documents": [],
            "chat_sessions": []
        }
        self.counters = {"users": 0, "documents": 0, "chat_sessions": 0}
    
    def get_collection(self, name: str):
        """Obtenir une collection simulée"""
        if name not in self.data:
            self.data[name] = []
        return MockCollection(self, name)
    
    def insert_one(self, collection: str, document: Dict) -> str:
        """Insérer un document"""
        if collection not in self.data:
            self.data[collection] = []
        
        # Générer un ID simple
        self.counters[collection] += 1
        doc_id = f"{collection}_{self.counters[collection]:06d}"
        
        document["_id"] = doc_id
        document["created_at"] = datetime.utcnow().isoformat()
        
        self.data[collection].append(document.copy())
        return doc_id
    
    def find_one(self, collection: str, query: Dict) -> Optional[Dict]:
        """Trouver un document"""
        if collection not in self.data:
            return None
        
        for doc in self.data[collection]:
            match = True
            for key, value in query.items():
                if key not in doc or doc[key] != value:
                    match = False
                    break
            if match:
                return doc.copy()
        return None
    
    def find(self, collection: str, query: Dict = None) -> List[Dict]:
        """Trouver plusieurs documents"""
        if collection not in self.data:
            return []
        
        if query is None:
            return [doc.copy() for doc in self.data[collection]]
        
        results = []
        for doc in self.data[collection]:
            match = True
            for key, value in query.items():
                if key not in doc or doc[key] != value:
                    match = False
                    break
            if match:
                results.append(doc.copy())
        return results
    
    def count_documents(self, collection: str, query: Dict = None) -> int:
        """Compter les documents"""
        return len(self.find(collection, query))
    
    def delete_one(self, collection: str, query: Dict) -> bool:
        """Supprimer un document"""
        if collection not in self.data:
            return False
        
        for i, doc in enumerate(self.data[collection]):
            match = True
            for key, value in query.items():
                if key not in doc or doc[key] != value:
                    match = False
                    break
            if match:
                del self.data[collection][i]
                return True
        return False
    
    def save_to_file(self, filename: str):
        """Sauvegarder en fichier JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, default=str)
    
    def load_from_file(self, filename: str):
        """Charger depuis un fichier JSON"""
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                self.data = json.load(f)

class MockCollection:
    """Collection simulée"""
    
    def __init__(self, db: MockMongoDB, name: str):
        self.db = db
        self.name = name
    
    def insert_one(self, document: Dict):
        """Insérer un document"""
        doc_id = self.db.insert_one(self.name, document)
        return type('InsertResult', (), {'inserted_id': doc_id})()
    
    def find_one(self, query: Dict = None):
        """Trouver un document"""
        return self.db.find_one(self.name, query or {})
    
    def find(self, query: Dict = None):
        """Trouver des documents"""
        return self.db.find(self.name, query or {})
    
    def count_documents(self, query: Dict = None):
        """Compter des documents"""
        return self.db.count_documents(self.name, query or {})
    
    def delete_one(self, query: Dict):
        """Supprimer un document"""
        success = self.db.delete_one(self.name, query)
        return type('DeleteResult', (), {'deleted_count': 1 if success else 0})()

def test_mock_mongodb():
    """Test de la simulation MongoDB"""
    print("🧪 Test MongoDB Mock")
    print("=" * 40)
    
    # Créer la base simulée
    mock_db = MockMongoDB()
    
    # Test users collection
    users = mock_db.get_collection("users")
    
    # Insérer un utilisateur
    user_data = {
        "email": "admin@askrag.com",
        "username": "admin",
        "full_name": "Administrator",
        "is_active": True
    }
    
    result = users.insert_one(user_data)
    print(f"✅ Utilisateur créé avec ID: {result.inserted_id}")
    
    # Rechercher l'utilisateur
    found_user = users.find_one({"email": "admin@askrag.com"})
    print(f"✅ Utilisateur trouvé: {found_user['full_name']}")
    
    # Test documents collection
    documents = mock_db.get_collection("documents")
    
    doc_data = {
        "filename": "test.pdf",
        "title": "Document de test",
        "content": "Contenu du document",
        "user_id": result.inserted_id
    }
    
    doc_result = documents.insert_one(doc_data)
    print(f"✅ Document créé avec ID: {doc_result.inserted_id}")
    
    # Statistiques
    user_count = users.count_documents()
    doc_count = documents.count_documents()
    
    print(f"📊 Statistiques:")
    print(f"   Utilisateurs: {user_count}")
    print(f"   Documents: {doc_count}")
    
    # Sauvegarder
    data_file = "data/mock_database.json"
    os.makedirs("data", exist_ok=True)
    mock_db.save_to_file(data_file)
    print(f"💾 Données sauvegardées dans: {data_file}")
    
    print("\n🎉 Test Mock MongoDB réussi!")
    return True

if __name__ == "__main__":
    test_mock_mongodb()
