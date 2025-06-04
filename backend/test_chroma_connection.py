#!/usr/bin/env python3
"""
Test de connexion ChromaDB
Étape 14.2.4
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.vector_store import VectorStore
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_chroma_connection():
    """Test la connexion à ChromaDB"""
    try:
        logger.info("🔍 Test de connexion ChromaDB...")
        
        # Initialiser le VectorStore
        vector_store = VectorStore()
        
        # Tester la connexion
        collection = vector_store.get_collection()
        logger.info(f"✅ Collection ChromaDB créée: {collection.name}")
        
        # Tester l'ajout d'un document test
        test_doc = {
            "id": "test_doc_1",
            "content": "Ceci est un document de test pour vérifier la connexion ChromaDB.",
            "metadata": {
                "filename": "test.txt",
                "file_type": "text/plain",
                "uploaded_at": "2025-05-30T10:00:00Z"
            }
        }
        
        # Générer un embedding test
        embedding = vector_store.embedding_service.get_embedding(test_doc["content"])
        logger.info(f"✅ Embedding généré: {len(embedding)} dimensions")
        
        # Ajouter le document
        vector_store.add_document(
            doc_id=test_doc["id"],
            content=test_doc["content"],
            metadata=test_doc["metadata"]
        )
        logger.info("✅ Document test ajouté au vector store")
        
        # Tester la recherche
        results = vector_store.search("document test", k=1)
        logger.info(f"✅ Recherche effectuée: {len(results)} résultats trouvés")
        
        if results and len(results) > 0:
            logger.info(f"✅ Premier résultat: {results[0]['content'][:50]}...")
        
        # Nettoyer
        vector_store.delete_document(test_doc["id"])
        logger.info("✅ Document test supprimé")
        
        logger.info("🎉 Test de connexion ChromaDB RÉUSSI !")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test ChromaDB: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_chroma_connection()
    sys.exit(0 if success else 1)
