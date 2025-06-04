"""
Module de validation des entrées - Étape 16.3.1
Validation et nettoyage des données d'entrée pour les endpoints RAG
"""

import re
import logging
from typing import Any, Dict, List, Optional, Union, Tuple
from fastapi import HTTPException
from pydantic import BaseModel, validator
import html


class ValidationError(Exception):
    """Exception levée lors d'erreurs de validation."""
    pass


class InputValidator:
    """
    Validateur principal pour les entrées du système RAG
    """
    
    # Expressions régulières pour validation
    PATTERNS = {
        'session_id': re.compile(r'^[a-zA-Z0-9\-_]{8,64}$'),
        'user_id': re.compile(r'^[a-zA-Z0-9\-_]{1,50}$'),
        'document_id': re.compile(r'^[a-zA-Z0-9\-_]{1,100}$'),
        'filename': re.compile(r'^[a-zA-Z0-9\-_\.\s]{1,255}$'),
        'file_extension': re.compile(r'^\.[a-zA-Z0-9]{1,10}$')
    }
    
    # Tailles maximales autorisées
    LIMITS = {
        'query_max_length': 2000,
        'document_title_max_length': 500,
        'session_title_max_length': 200,
        'filename_max_length': 255,
        'file_size_max': 50 * 1024 * 1024,  # 50MB
        'chunks_max': 100,
        'search_results_max': 50
    }
    
    # Types de fichiers autorisés
    ALLOWED_FILE_TYPES = {
        '.pdf', '.docx', '.doc', '.txt', '.md', '.html', '.htm', '.rtf'
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_query(self, query: str) -> str:
        """
        Valide et nettoie une requête de recherche
        
        Args:
            query: Requête à valider
            
        Returns:
            Requête nettoyée
            
        Raises:
            ValidationError: Si la requête n'est pas valide
        """
        if not query or not isinstance(query, str):
            raise ValidationError("La requête ne peut pas être vide")
        
        # Nettoyer la requête
        cleaned_query = self._clean_text(query)
        
        # Vérifier la longueur
        if len(cleaned_query) > self.LIMITS['query_max_length']:
            raise ValidationError(
                f"La requête ne peut pas dépasser {self.LIMITS['query_max_length']} caractères"
            )
        
        if len(cleaned_query.strip()) < 3:
            raise ValidationError("La requête doit contenir au moins 3 caractères significatifs")
        
        # Vérifier que ce n'est pas uniquement des caractères spéciaux
        if not re.search(r'[a-zA-Z0-9àáâãäåæçèéêëìíîïðñòóôõöøùúûüýÿ]', cleaned_query):
            raise ValidationError("La requête doit contenir au moins un caractère alphanumérique")
        
        self.logger.debug(f"Requête validée: '{cleaned_query[:50]}...'")
        return cleaned_query
    
    def validate_session_id(self, session_id: Optional[str]) -> Optional[str]:
        """
        Valide un ID de session
        
        Args:
            session_id: ID de session à valider
            
        Returns:
            ID de session validé ou None
            
        Raises:
            ValidationError: Si l'ID n'est pas valide
        """
        if session_id is None:
            return None
        
        if not isinstance(session_id, str):
            raise ValidationError("L'ID de session doit être une chaîne de caractères")
        
        if not self.PATTERNS['session_id'].match(session_id):
            raise ValidationError(
                "L'ID de session doit contenir entre 8 et 64 caractères alphanumériques, tirets ou underscores"
            )
        
        return session_id
    
    def validate_user_id(self, user_id: str) -> str:
        """
        Valide un ID utilisateur
        
        Args:
            user_id: ID utilisateur à valider
            
        Returns:
            ID utilisateur validé
            
        Raises:
            ValidationError: Si l'ID n'est pas valide
        """
        if not user_id or not isinstance(user_id, str):
            raise ValidationError("L'ID utilisateur est requis")
        
        if not self.PATTERNS['user_id'].match(user_id):
            raise ValidationError(
                "L'ID utilisateur doit contenir entre 1 et 50 caractères alphanumériques, tirets ou underscores"
            )
        
        return user_id
    
    def validate_document_upload(self, filename: str, file_size: int, content_type: str = None) -> Dict[str, Any]:
        """
        Valide les paramètres d'upload d'un document
        
        Args:
            filename: Nom du fichier
            file_size: Taille du fichier en octets
            content_type: Type MIME du fichier
            
        Returns:
            Dictionnaire avec les paramètres validés
            
        Raises:
            ValidationError: Si les paramètres ne sont pas valides
        """
        if not filename or not isinstance(filename, str):
            raise ValidationError("Le nom de fichier est requis")
        
        # Nettoyer le nom de fichier
        cleaned_filename = self._clean_filename(filename)
        
        # Vérifier la longueur
        if len(cleaned_filename) > self.LIMITS['filename_max_length']:
            raise ValidationError(
                f"Le nom de fichier ne peut pas dépasser {self.LIMITS['filename_max_length']} caractères"
            )
        
        # Extraire l'extension
        if '.' not in cleaned_filename:
            raise ValidationError("Le fichier doit avoir une extension")
        
        file_extension = '.' + cleaned_filename.split('.')[-1].lower()
        
        # Vérifier le type de fichier
        if file_extension not in self.ALLOWED_FILE_TYPES:
            raise ValidationError(
                f"Type de fichier non supporté. Types autorisés: {', '.join(self.ALLOWED_FILE_TYPES)}"
            )
        
        # Vérifier la taille
        if file_size > self.LIMITS['file_size_max']:
            max_mb = self.LIMITS['file_size_max'] / (1024 * 1024)
            raise ValidationError(f"Le fichier ne peut pas dépasser {max_mb:.0f} MB")
        
        if file_size <= 0:
            raise ValidationError("Le fichier ne peut pas être vide")
        
        self.logger.debug(f"Document validé: {cleaned_filename} ({file_size} octets)")
        
        return {
            'filename': cleaned_filename,
            'file_extension': file_extension,
            'file_size': file_size,
            'content_type': content_type
        }
    
    def validate_search_parameters(self, limit: int, threshold: float, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Valide les paramètres de recherche
        
        Args:
            limit: Nombre de résultats demandés
            threshold: Seuil de similarité
            filters: Filtres de recherche
            
        Returns:
            Paramètres validés
            
        Raises:
            ValidationError: Si les paramètres ne sont pas valides
        """
        # Valider le nombre de résultats
        if not isinstance(limit, int) or limit < 1:
            raise ValidationError("Le nombre de résultats doit être un entier positif")
        
        if limit > self.LIMITS['search_results_max']:
            raise ValidationError(
                f"Le nombre de résultats ne peut pas dépasser {self.LIMITS['search_results_max']}"
            )
        
        # Valider le seuil
        if not isinstance(threshold, (int, float)) or threshold < 0.0 or threshold > 1.0:
            raise ValidationError("Le seuil de similarité doit être entre 0.0 et 1.0")
        
        # Valider les filtres
        validated_filters = {}
        if filters:
            if not isinstance(filters, dict):
                raise ValidationError("Les filtres doivent être un dictionnaire")
            
            # Valider chaque filtre
            for key, value in filters.items():
                if not isinstance(key, str):
                    raise ValidationError("Les clés de filtre doivent être des chaînes de caractères")
                
                # Nettoyer et valider les valeurs
                if isinstance(value, str):
                    validated_filters[key] = self._clean_text(value)
                else:
                    validated_filters[key] = value
        
        return {
            'limit': limit,
            'threshold': float(threshold),
            'filters': validated_filters
        }
    
    def validate_pagination_parameters(self, page: int, page_size: int) -> Tuple[int, int]:
        """
        Valide les paramètres de pagination
        
        Args:
            page: Numéro de page (base 1)
            page_size: Taille de page
            
        Returns:
            Tuple (page, page_size) validé
            
        Raises:
            ValidationError: Si les paramètres ne sont pas valides
        """
        if not isinstance(page, int) or page < 1:
            raise ValidationError("Le numéro de page doit être un entier >= 1")
        
        if not isinstance(page_size, int) or page_size < 1:
            raise ValidationError("La taille de page doit être un entier >= 1")
        
        if page_size > 100:
            raise ValidationError("La taille de page ne peut pas dépasser 100")
        
        return page, page_size
    
    def _clean_text(self, text: str) -> str:
        """
        Nettoie un texte en supprimant les caractères dangereux
        
        Args:
            text: Texte à nettoyer
            
        Returns:
            Texte nettoyé
        """
        if not text:
            return ""
        
        # Échapper les caractères HTML
        cleaned = html.escape(text)
        
        # Supprimer les caractères de contrôle dangereux
        cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', cleaned)
        
        # Normaliser les espaces
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Supprimer les espaces en début et fin
        cleaned = cleaned.strip()
        
        return cleaned
    
    def _clean_filename(self, filename: str) -> str:
        """
        Nettoie un nom de fichier
        
        Args:
            filename: Nom de fichier à nettoyer
            
        Returns:
            Nom de fichier nettoyé
        """
        if not filename:
            return ""
        
        # Supprimer les caractères dangereux
        cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Supprimer les caractères de contrôle
        cleaned = re.sub(r'[\x00-\x1F\x7F]', '', cleaned)
        
        # Normaliser les espaces
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Supprimer les espaces en début et fin
        cleaned = cleaned.strip()
        
        return cleaned


class HTTPValidationHelper:
    """
    Helper pour lever des HTTPException avec les bons codes d'erreur
    """
    
    @staticmethod
    def validate_or_400(func, *args, **kwargs):
        """
        Execute une fonction de validation et lève HTTPException 400 si erreur
        
        Args:
            func: Fonction de validation
            *args, **kwargs: Arguments à passer à la fonction
            
        Returns:
            Résultat de la fonction
            
        Raises:
            HTTPException: 400 Bad Request si validation échoue
        """
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logging.getLogger(__name__).error(f"Erreur validation inattendue: {e}")
            raise HTTPException(status_code=400, detail="Erreur de validation")


# Instance globale du validateur
input_validator = InputValidator()
validation_helper = HTTPValidationHelper()
