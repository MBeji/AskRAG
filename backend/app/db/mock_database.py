"""
Base de données MongoDB simulée pour le développement
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

class MockMongoDB:
    """Simulation de MongoDB en mémoire pour le développement"""
    
    def __init__(self, data_file: str = "data/askrag_mock.json"):
        self.data_file = data_file
        self.data: Dict[str, List[Dict]] = {
            "users": [],
            "documents": [],
            "chat_sessions": []
        }
        self.counters = {"users": 0, "documents": 0, "chat_sessions": 0}
        self.load_from_file()
    
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
        if "created_at" not in document:
            document["created_at"] = datetime.now().isoformat()
        
        self.data[collection].append(document.copy())
        self.save_to_file()  # Auto-save
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
    
    def find(self, collection: str, query: Dict = None, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Trouver plusieurs documents"""
        if collection not in self.data:
            return []
        
        results = []
        if query is None:
            results = [doc.copy() for doc in self.data[collection]]
        else:
            for doc in self.data[collection]:
                match = True
                for key, value in query.items():
                    if key not in doc or doc[key] != value:
                        match = False
                        break
                if match:
                    results.append(doc.copy())
        
        # Apply skip and limit
        return results[skip:skip + limit] if limit else results[skip:]
    
    def count_documents(self, collection: str, query: Dict = None) -> int:
        """Compter les documents"""
        return len(self.find(collection, query, limit=None))
    
    def update_one(self, collection: str, query: Dict, update: Dict) -> bool:
        """Mettre à jour un document"""
        if collection not in self.data:
            return False
        
        for doc in self.data[collection]:
            match = True
            for key, value in query.items():
                if key not in doc or doc[key] != value:
                    match = False
                    break
            if match:
                # Apply $set operation
                if "$set" in update:
                    for key, value in update["$set"].items():
                        doc[key] = value
                doc["updated_at"] = datetime.now().isoformat()
                self.save_to_file()
                return True
        return False
    
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
                self.save_to_file()
                return True
        return False
    
    def save_to_file(self):
        """Sauvegarder en fichier JSON"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, default=str)
    
    def load_from_file(self):
        """Charger depuis un fichier JSON"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                # Update counters based on existing data
                for collection in self.data:
                    if self.data[collection]:
                        max_id = max([int(doc.get("_id", "0").split("_")[-1]) for doc in self.data[collection] if "_" in str(doc.get("_id", ""))])
                        self.counters[collection] = max_id
            except Exception:
                # If file is corrupted, start fresh
                pass

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
        """Trouver des documents avec curseur simulé"""
        return MockCursor(self.db, self.name, query or {})
    
    def count_documents(self, query: Dict = None):
        """Compter des documents"""
        return self.db.count_documents(self.name, query or {})
    
    def update_one(self, query: Dict, update: Dict):
        """Mettre à jour un document"""
        success = self.db.update_one(self.name, query, update)
        return type('UpdateResult', (), {'modified_count': 1 if success else 0})()
    
    def delete_one(self, query: Dict):
        """Supprimer un document"""
        success = self.db.delete_one(self.name, query)
        return type('DeleteResult', (), {'deleted_count': 1 if success else 0})()

class MockCursor:
    """Curseur simulé pour les requêtes"""
    
    def __init__(self, db: MockMongoDB, collection: str, query: Dict):
        self.db = db
        self.collection = collection
        self.query = query
        self.skip_count = 0
        self.limit_count = None
        self.sort_field = None
        self.sort_direction = 1
    
    def skip(self, count: int):
        """Skip documents"""
        self.skip_count = count
        return self
    
    def limit(self, count: int):
        """Limit results"""
        self.limit_count = count
        return self
    
    def sort(self, field: str, direction: int = 1):
        """Sort results"""
        self.sort_field = field
        self.sort_direction = direction
        return self
    
    async def to_list(self, length: int = None):
        """Convert to list (async)"""
        results = self.db.find(self.collection, self.query, self.skip_count, self.limit_count or length)
        
        # Apply sorting if specified
        if self.sort_field:
            reverse = self.sort_direction == -1
            results.sort(key=lambda x: x.get(self.sort_field, ""), reverse=reverse)
        
        return results

# Instance globale
mock_db = MockMongoDB()

def get_mock_database():
    """Obtenir l'instance de la base de données mock"""
    return mock_db
