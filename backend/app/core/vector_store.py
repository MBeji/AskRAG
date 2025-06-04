import faiss
import numpy as np
import os
import pickle # For saving/loading the doc_id_map
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any

from app.core.config import settings # Import global app settings
import logging

logger = logging.getLogger(__name__)

class FaissVectorStore:
    def __init__(self, index_path: str = settings.FAISS_INDEX_PATH, dimension: int = settings.FAISS_INDEX_DIMENSION):
        self.index_path_str: str = index_path
        self.index_path: Path = Path(index_path)
        self.map_path: Path = Path(f"{index_path}.map")
        self.dimension: int = dimension
        
        self.index: Optional[faiss.Index] = None
        # Using faiss.Index here which is a base type. Will be IndexIDMap.
        # self.index: Optional[faiss.IndexIDMap] = None # More specific type
        
        self.doc_id_map: Dict[int, str] = {} # Maps FAISS int ID to our custom string chunk_id
        
        self.load_index()

    def load_index(self) -> None:
        """Loads the FAISS index and document ID map from disk if they exist."""
        try:
            if self.index_path.exists() and self.map_path.exists():
                self.index = faiss.read_index(self.index_path_str)
                with open(self.map_path, "rb") as f:
                    self.doc_id_map = pickle.load(f)
                logger.info(f"FAISS index and map loaded from {self.index_path_str}. Index size: {self.index.ntotal if self.index else 0} vectors.")
            else:
                logger.info("No existing FAISS index found. Initializing a new one.")
                # Use IndexIDMap to map our own int IDs to vectors
                # This allows easier association if FAISS internal IDs change or are not sequential.
                # However, add_with_ids requires contiguous int64 IDs.
                # For simplicity with add_with_ids, we might just use IndexFlatL2 and manage sequential IDs.
                # Let's use IndexIDMap with faiss.IndexFlatL2 as the underlying index.
                # This allows us to control the integer IDs we add.
                base_index = faiss.IndexFlatL2(self.dimension)
                self.index = faiss.IndexIDMap(base_index)
                # self.index = faiss.IndexFlatL2(self.dimension) # Simpler if we manage IDs externally or don't need stable IDs
                self.doc_id_map = {}
        except Exception as e:
            logger.error(f"Error loading FAISS index: {e}. Initializing a new index.")
            base_index = faiss.IndexFlatL2(self.dimension)
            self.index = faiss.IndexIDMap(base_index)
            self.doc_id_map = {}

    def save_index(self) -> None:
        """Saves the FAISS index and document ID map to disk."""
        if self.index is None:
            logger.error("No FAISS index to save.")
            return

        try:
            self.index_path.parent.mkdir(parents=True, exist_ok=True) # Ensure directory exists
            faiss.write_index(self.index, self.index_path_str)
            with open(self.map_path, "wb") as f:
                pickle.dump(self.doc_id_map, f)
            logger.info(f"FAISS index and map saved to {self.index_path_str}. Index size: {self.index.ntotal} vectors.")
        except Exception as e:
            logger.error(f"Error saving FAISS index: {e}")

    def add_embeddings(self, embeddings: List[List[float]], document_chunk_ids: List[str]) -> List[int]:
        """
        Adds embeddings to the FAISS index and updates the ID map.
        Args:
            embeddings: List of embedding vectors.
            document_chunk_ids: List of corresponding unique string identifiers for each document chunk.
        Returns:
            List of integer IDs assigned by FAISS to the added embeddings.
        """
        if self.index is None:
            logger.error("FAISS index not initialized. Cannot add embeddings.")
            raise RuntimeError("FAISS index not initialized.")
        if not embeddings:
            return []
        if len(embeddings) != len(document_chunk_ids):
            raise ValueError("Number of embeddings must match number of document_chunk_ids.")

        embeddings_np = np.array(embeddings).astype('float32')
        
        # Generate unique integer IDs for FAISS.
        # These should be new, unique int64 IDs not already in the index.
        # A simple way is to start from current ntotal if IndexIDMap is used carefully,
        # or use a global counter, or ensure document_chunk_ids are mapped to unique integers.
        # For IndexIDMap, we provide our own int64 IDs.

        # Let's generate sequential integer IDs for this batch.
        # These IDs need to be unique across all additions to the index.
        # A robust way is to use a counter or ensure document_chunk_ids can be mapped to unique integers.
        # For now, we'll use a simple approach: find the max current ID in doc_id_map keys and increment.
        # This assumes FAISS IDs given by us are what are stored in doc_id_map.keys()

        current_max_id = -1
        if self.doc_id_map: # Check if map is not empty
            current_max_id = max(self.doc_id_map.keys()) if self.doc_id_map else -1
            
        faiss_ids = [i for i in range(current_max_id + 1, current_max_id + 1 + len(embeddings))]
        faiss_ids_np = np.array(faiss_ids, dtype=np.int64)

        self.index.add_with_ids(embeddings_np, faiss_ids_np)

        for i, faiss_id_val in enumerate(faiss_ids):
            self.doc_id_map[faiss_id_val] = document_chunk_ids[i]
            
        logger.info(f"Added {len(embeddings)} embeddings to FAISS index. New total: {self.index.ntotal}")
        return faiss_ids # Return the list of FAISS integer IDs used.

    def search(self, query_embedding: List[float], k: int = 5) -> Tuple[List[float], List[str]]:
        """
        Searches for the k nearest neighbors to the query_embedding.
        Args:
            query_embedding: The embedding vector of the query.
            k: Number of nearest neighbors to retrieve.
        Returns:
            A tuple containing:
                - List of distances/scores.
                - List of corresponding MongoDB document chunk identifiers.
        """
        if self.index is None or self.index.ntotal == 0:
            logger.warning("FAISS index is not initialized or empty. Cannot perform search.")
            return [], []

        query_embedding_np = np.array([query_embedding]).astype('float32')
        
        # Ensure k is not greater than the number of items in the index
        actual_k = min(k, self.index.ntotal)
        if actual_k == 0: # Should not happen if ntotal > 0, but as safeguard
             return [], []

        distances, faiss_indices = self.index.search(query_embedding_np, actual_k)
        
        # faiss_indices are the integer IDs we added with add_with_ids
        retrieved_doc_chunk_ids = [self.doc_id_map.get(idx, "ID_NOT_FOUND") for idx in faiss_indices[0] if idx != -1]

        # Filter out "ID_NOT_FOUND" if any (should not happen with IndexIDMap if managed correctly)
        # And ensure distances correspond
        valid_distances = []
        final_ids = []
        for i, idx in enumerate(faiss_indices[0]):
            if idx != -1 and self.doc_id_map.get(idx) is not None:
                final_ids.append(self.doc_id_map[idx])
                valid_distances.append(float(distances[0][i]))

        return valid_distances, final_ids

# Global instance of the vector store, loaded at app startup (see main.py)
# The actual loading of index from disk happens in __init__
try:
    vector_store = FaissVectorStore()
except Exception as e:
    logger.error(f"Failed to initialize global FaissVectorStore: {e}")
    vector_store = None # Or handle more gracefully

# To ensure the directory exists when the module is loaded, if vector_store is global
# This is also done in save_index, but good to have early for load_index.
# if vector_store and vector_store.index_path:
#    vector_store.index_path.parent.mkdir(parents=True, exist_ok=True)
