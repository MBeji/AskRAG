"""
VectorStore Core - Configuration et gestion de FAISS pour RAG
Étape 14.2: Service de vectorisation avancé
"""

import faiss
import numpy as np
import os
import json
import pickle
import hashlib
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from pathlib import Path

from .embeddings import EmbeddingService


class VectorStore:
    """
    Service de gestion des vecteurs avec FAISS
    Support des index, métadonnées et recherche sémantique
    """
    
    def __init__(self, 
                 collection_name: str = "askrag_documents",
                 persist_directory: str = None,
                 dimension: int = 1536):  # Dimension OpenAI embeddings
        """
        Initialise le VectorStore avec FAISS
        
        Args:
            collection_name: Nom de la collection
            persist_directory: Répertoire de persistance des données
            dimension: Dimension des vecteurs d'embedding
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory or os.getenv('FAISS_PERSIST_DIRECTORY', './faiss_db')
        self.dimension = dimension
        
        # Configuration FAISS
        self.index = None
        self.documents = {}  # Stockage des documents et métadonnées
        self.id_mapping = {}  # Mapping ID -> index FAISS
        self.embedding_service = EmbeddingService()
        
        self.logger = logging.getLogger(__name__)
        
        # Chemins de fichiers
        self.index_path = Path(self.persist_directory) / f"{collection_name}.index"
        self.docs_path = Path(self.persist_directory) / f"{collection_name}_docs.json"
        self.mapping_path = Path(self.persist_directory) / f"{collection_name}_mapping.json"
        
        # Initialisation
        self._initialize_faiss()
    
    def _initialize_faiss(self):
        """Initialise l'index FAISS"""
        try:
            # Créer le répertoire si nécessaire
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # Charger l'index existant ou en créer un nouveau
            if self.index_path.exists():
                self._load_index()
            else:
                self._create_new_index()
            
            self.logger.info(f"FAISS initialisé: {self.collection_name}, dimension: {self.dimension}")
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation FAISS: {e}")
            raise
    
    def _create_new_index(self):
        """Crée un nouvel index FAISS"""
        # Index FAISS avec recherche par similarité cosinus
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner Product pour cosinus
        
        # Initialiser les structures de données
        self.documents = {}
        self.id_mapping = {}
    
    def _load_index(self):
        """Charge un index FAISS existant"""
        try:
            # Charger l'index FAISS
            self.index = faiss.read_index(str(self.index_path))
            
            # Charger les documents
            if self.docs_path.exists():
                with open(self.docs_path, 'r', encoding='utf-8') as f:
                    self.documents = json.load(f)
            else:
                self.documents = {}
            
            # Charger le mapping
            if self.mapping_path.exists():
                with open(self.mapping_path, 'r', encoding='utf-8') as f:
                    self.id_mapping = json.load(f)
            else:
                self.id_mapping = {}
                
            self.logger.info(f"Index FAISS chargé: {self.index.ntotal} vecteurs")
            
        except Exception as e:
            self.logger.error(f"Erreur chargement index FAISS: {e}")
            self._create_new_index()
    
    def _save_index(self):
        """Sauvegarde l'index FAISS et les métadonnées"""
        try:
            # Sauvegarder l'index FAISS
            faiss.write_index(self.index, str(self.index_path))
            
            # Sauvegarder les documents
            with open(self.docs_path, 'w', encoding='utf-8') as f:
                json.dump(self.documents, f, ensure_ascii=False, indent=2)
            
            # Sauvegarder le mapping
            with open(self.mapping_path, 'w', encoding='utf-8') as f:
                json.dump(self.id_mapping, f, indent=2)
                
            self.logger.debug("Index FAISS sauvegardé")
            
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde FAISS: {e}")
    
    def add_document(self, 
                    content: str, 
                    metadata: Dict[str, Any] = None,
                    document_id: str = None) -> str:
        """
        Ajoute un document au VectorStore
        
        Args:
            content: Contenu textuel du document
            metadata: Métadonnées associées
            document_id: ID unique du document (généré si None)
            
        Returns:
            str: ID du document ajouté
        """
        try:
            # Générer un ID unique si non fourni
            if document_id is None:
                document_id = hashlib.md5(
                    f"{content[:200]}{datetime.now().isoformat()}".encode()
                ).hexdigest()
            
            # Générer l'embedding
            embedding = self.embedding_service.get_embedding(content)
            
            # Normaliser l'embedding pour la similarité cosinus
            embedding_np = np.array([embedding], dtype=np.float32)
            faiss.normalize_L2(embedding_np)
            
            # Ajouter à l'index FAISS
            faiss_idx = self.index.ntotal
            self.index.add(embedding_np)
            
            # Stocker les métadonnées
            doc_metadata = metadata or {}
            doc_metadata.update({
                'id': document_id,
                'content': content,
                'added_at': datetime.now().isoformat(),
                'embedding_model': self.embedding_service.model_name
            })
            
            self.documents[document_id] = doc_metadata
            self.id_mapping[document_id] = faiss_idx
            
            # Sauvegarder
            self._save_index()
            
            self.logger.debug(f"Document ajouté: {document_id}")
            return document_id
            
        except Exception as e:
            self.logger.error(f"Erreur ajout document: {e}")
            raise
    
    def search(self, 
              query: str, 
              k: int = 5,
              score_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Recherche sémantique dans le VectorStore
        
        Args:
            query: Texte de recherche
            k: Nombre de résultats maximum
            score_threshold: Seuil de similarité minimum
            
        Returns:
            List[Dict]: Résultats avec métadonnées et scores
        """
        try:
            if self.index.ntotal == 0:
                return []
            
            # Générer l'embedding de la requête
            query_embedding = self.embedding_service.get_embedding(query)
            
            # Normaliser pour la similarité cosinus
            query_np = np.array([query_embedding], dtype=np.float32)
            faiss.normalize_L2(query_np)
            
            # Recherche FAISS
            scores, indices = self.index.search(query_np, min(k, self.index.ntotal))
            
            # Traiter les résultats
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1 or score < score_threshold:
                    continue
                
                # Trouver le document correspondant
                doc_id = None
                for d_id, f_idx in self.id_mapping.items():
                    if f_idx == idx:
                        doc_id = d_id
                        break
                
                if doc_id and doc_id in self.documents:
                    result = {
                        'id': doc_id,
                        'content': self.documents[doc_id].get('content', ''),
                        'metadata': self.documents[doc_id],
                        'score': float(score)
                    }
                    results.append(result)
            
            # Trier par score décroissant
            results.sort(key=lambda x: x['score'], reverse=True)
            
            self.logger.debug(f"Recherche: {len(results)} résultats pour '{query[:50]}...'")
            return results
            
        except Exception as e:
            self.logger.error(f"Erreur recherche: {e}")
            return []
    
    def delete_document(self, document_id: str) -> bool:
        """
        Supprime un document du VectorStore
        
        Args:
            document_id: ID du document à supprimer
            
        Returns:
            bool: True si suppression réussie
        """
        try:
            if document_id not in self.documents:
                return False
            
            # FAISS ne permet pas la suppression directe
            # On marque le document comme supprimé
            if document_id in self.documents:
                del self.documents[document_id]
            
            if document_id in self.id_mapping:
                del self.id_mapping[document_id]
            
            # Sauvegarder
            self._save_index()
            
            self.logger.debug(f"Document supprimé: {document_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur suppression document: {e}")
            return False
    
    def get_collection_info(self) -> Dict[str, Any]:
        """
        Récupère les informations sur la collection
        
        Returns:
            Dict: Informations de la collection
        """
        return {
            'name': self.collection_name,
            'count': len(self.documents),
            'index_size': self.index.ntotal if self.index else 0,
            'dimension': self.dimension,
            'persist_directory': self.persist_directory
        }
    
    def reset_collection(self) -> bool:
        """
        Remet à zéro la collection
        
        Returns:
            bool: True si reset réussi
        """
        try:
            # Créer un nouvel index
            self._create_new_index()
            
            # Supprimer les fichiers de persistance
            for path in [self.index_path, self.docs_path, self.mapping_path]:
                if path.exists():
                    path.unlink()
            
            self.logger.info(f"Collection reset: {self.collection_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur reset collection: {e}")
            return False


# Instance globale pour la compatibilité
vector_store = VectorStore()
