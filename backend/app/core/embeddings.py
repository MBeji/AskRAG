"""
Service d'Embeddings - Génération de vecteurs avec OpenAI
Étape 14.3: Service d'embeddings centralisé
"""

import openai
import os
import logging
import time
from typing import List, Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
import numpy as np


class EmbeddingService:
    """
    Service centralisé pour la génération d'embeddings
    Support OpenAI embeddings avec gestion d'erreurs et cache
    """
    
    def __init__(self, 
                 model_name: str = "text-embedding-3-small",
                 api_key: str = None):
        """
        Initialise le service d'embeddings
          Args:
            model_name: Modèle OpenAI à utiliser
            api_key: Clé API OpenAI (utilise env si None)
        """
        self.model_name = model_name
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        
        # Mode test pour le développement
        self.test_mode = (self.api_key and self.api_key.startswith('sk-test-')) or os.getenv('ENVIRONMENT') == 'development'
        
        if not self.api_key and not self.test_mode:
            raise ValueError("OPENAI_API_KEY manquante")
        
        # Clé par défaut pour le mode test
        if self.test_mode and not self.api_key:
            self.api_key = 'sk-test-development-mode'
        
        # Configuration OpenAI seulement si ce n'est pas le mode test
        if not self.test_mode:
            openai.api_key = self.api_key
            self.client = openai.OpenAI(api_key=self.api_key)
        else:
            self.client = None
            self.logger = logging.getLogger(__name__)
            self.logger.warning("Mode test activé - embeddings simulés")
        
        self.logger = logging.getLogger(__name__)
        
        # Cache simple en mémoire
        self._cache = {}
        self._cache_hits = 0
        self._total_requests = 0
        
        # Configuration du modèle
        self.embedding_dimension = self._get_model_dimension()
        
        self.logger.info(f"EmbeddingService initialisé: {model_name}")
    
    def _get_model_dimension(self) -> int:
        """Retourne la dimension des embeddings selon le modèle"""
        model_dimensions = {
            'text-embedding-3-small': 1536,
            'text-embedding-3-large': 3072,
            'text-embedding-ada-002': 1536
        }
        return model_dimensions.get(self.model_name, 1536)
    
    def _get_cache_key(self, text: str) -> str:
        """Génère une clé de cache pour un texte"""
        import hashlib
        return hashlib.md5(f"{self.model_name}:{text}".encode()).hexdigest()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def _call_openai_api(self, text: str) -> List[float]:
        """
        Appel API OpenAI avec retry automatique
        
        Args:
            text: Texte à embedder
            
        Returns:
            List[float]: Vecteur d'embedding
        """
        try:
            response = self.client.embeddings.create(
                model=self.model_name,
                input=text,
                encoding_format="float"
            )
            
            embedding = response.data[0].embedding
            
            self.logger.debug(f"Embedding généré: {len(embedding)} dimensions")
            return embedding
            
        except Exception as e:
            self.logger.error(f"Erreur API OpenAI: {e}")
            raise
    
    def get_embedding(self, text: str, use_cache: bool = True) -> List[float]:
        """
        Génère un embedding pour un texte
        
        Args:
            text: Texte à embedder
            use_cache: Utiliser le cache si disponible
            
        Returns:
            List[float]: Vecteur d'embedding
        """
        if not text or not text.strip():
            raise ValueError("Texte vide fourni")
        
        # Nettoyer le texte
        text = text.strip()
        
        self._total_requests += 1
        
        # Vérifier le cache
        cache_key = self._get_cache_key(text)
        if use_cache and cache_key in self._cache:
            self._cache_hits += 1
            self.logger.debug("Embedding récupéré du cache")
            return self._cache[cache_key]
          # Générer l'embedding
        try:
            if self.test_mode:
                # Mode test - générer un embedding simulé
                embedding = self._generate_test_embedding(text)
            else:
                # Mode production - appeler l'API OpenAI
                embedding = self._call_openai_api(text)
            
            # Stocker dans le cache
            if use_cache:
                self._cache[cache_key] = embedding
            
            return embedding
            
        except Exception as e:
            self.logger.error(f"Erreur génération embedding: {e}")
            raise
    
    def get_embeddings_batch(self, 
                           texts: List[str], 
                           batch_size: int = 100,
                           use_cache: bool = True) -> List[List[float]]:
        """
        Génère des embeddings par batch
        
        Args:
            texts: Liste de textes à embedder
            batch_size: Taille des batches
            use_cache: Utiliser le cache si disponible
            
        Returns:
            List[List[float]]: Liste d'embeddings
        """
        if not texts:
            return []
        
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_embeddings = []
            
            for text in batch_texts:
                try:
                    embedding = self.get_embedding(text, use_cache)
                    batch_embeddings.append(embedding)
                except Exception as e:
                    self.logger.error(f"Erreur embedding batch pour '{text[:50]}...': {e}")
                    # Ajouter un vecteur zéro en cas d'erreur
                    batch_embeddings.append([0.0] * self.embedding_dimension)
            
            embeddings.extend(batch_embeddings)
            
            # Pause entre les batches pour éviter le rate limiting
            if i + batch_size < len(texts):
                time.sleep(0.1)
        
        self.logger.info(f"Batch embeddings généré: {len(embeddings)} éléments")
        return embeddings
    
    def compute_similarity(self, 
                          embedding1: List[float], 
                          embedding2: List[float]) -> float:
        """
        Calcule la similarité cosinus entre deux embeddings
        
        Args:
            embedding1: Premier vecteur
            embedding2: Deuxième vecteur
            
        Returns:
            float: Score de similarité [-1, 1]
        """
        try:
            # Convertir en arrays numpy
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calcul similarité cosinus
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            self.logger.error(f"Erreur calcul similarité: {e}")
            return 0.0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques du cache
        
        Returns:
            Dict: Statistiques d'utilisation
        """
        cache_rate = (self._cache_hits / self._total_requests * 100) if self._total_requests > 0 else 0
        
        return {
            'total_requests': self._total_requests,
            'cache_hits': self._cache_hits,
            'cache_rate': f"{cache_rate:.1f}%",
            'cache_size': len(self._cache),
            'model_name': self.model_name,
            'embedding_dimension': self.embedding_dimension
        }
    
    def clear_cache(self):
        """Vide le cache d'embeddings"""
        self._cache.clear()
        self._cache_hits = 0
        self._total_requests = 0
        self.logger.info("Cache d'embeddings vidé")
    
    def _generate_test_embedding(self, text: str) -> List[float]:
        """
        Génère un embedding de test basé sur le hash du texte
        Pour le développement sans clé API valide
        
        Args:
            text: Texte à embedder
            
        Returns:
            List[float]: Vecteur d'embedding simulé
        """
        import hashlib
        import numpy as np
        
        # Utiliser le hash du texte comme seed pour la reproductibilité
        hash_value = hashlib.md5(text.encode()).hexdigest()
        seed = int(hash_value[:8], 16)
        np.random.seed(seed)
        
        # Générer un vecteur aléatoire de la bonne dimension
        dimension = self.get_dimension()
        embedding = np.random.normal(0, 1, dimension).tolist()
        
        # Normaliser pour ressembler à des embeddings réels
        norm = np.linalg.norm(embedding)
        embedding = [x / norm for x in embedding]
        
        self.logger.debug(f"Embedding test généré: {len(embedding)} dimensions")
        return embedding

# Instance globale pour la compatibilité
# This instance uses default model "text-embedding-3-small" and API key from env.
# embedding_service = EmbeddingService()
# For Step 12, we'll create a function that uses settings from config.py for model name.

from app.core.config import settings as app_settings # Import app_settings

# Initialize a global service instance using settings from config.py
# This ensures that the model name and API key from the central config are used.
# Note: This will be initialized at module load time.
# If settings depend on .env files not yet loaded at this point for some reason,
# defer instantiation or ensure .env is loaded prior to this module.
# Given current setup, BaseSettings in config.py loads .env.
try:
    global_embedding_service = EmbeddingService(
        model_name=app_settings.EMBEDDING_MODEL_NAME,
        api_key=app_settings.OPENAI_API_KEY
    )
except ValueError as e:
    # Handle cases where API key might be missing and not in test mode
    logging.getLogger(__name__).error(f"Failed to initialize Global EmbeddingService: {e}")
    global_embedding_service = None

async def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generates embeddings for a list of text chunks using the global EmbeddingService.
    """
    if global_embedding_service is None:
        # This can happen if OPENAI_API_KEY is not set and ENVIRONMENT is not 'development'
        logging.getLogger(__name__).error("EmbeddingService not initialized. Cannot generate embeddings.")
        # Depending on desired behavior, either raise an exception or return empty lists/errors.
        # For now, let's raise an error or return a list of empty embeddings matching input length.
        # This should ideally be caught upstream.
        raise RuntimeError("EmbeddingService not available. Check OPENAI_API_KEY.")

    if not texts:
        return []

    try:
        # The existing EmbeddingService.get_embeddings_batch handles batching internally if needed,
        # but its primary interface is List[str] -> List[List[float]] for a single "batch" call from user.
        # It also has its own retry logic.
        embeddings = global_embedding_service.get_embeddings_batch(texts=texts, use_cache=True) # Use batch method
        return embeddings
    except Exception as e:
        logging.getLogger(__name__).error(f"Error generating embeddings: {e}")
        # Handle specific OpenAI API errors if necessary, or re-raise
        # For now, return list of empty lists to match expected output structure on error
        # Or re-raise to let the caller handle it. Let's re-raise for now.
        raise
