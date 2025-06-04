"""
Service LLM - Étape 15.2
Gestion des appels aux modèles de langage (OpenAI GPT)
"""

import os
import logging
from typing import List, Dict, Any, Optional
import openai
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class LLMService:
    """Service pour l'intégration avec les modèles de langage"""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo", api_key: Optional[str] = None):
        """
        Initialise le service LLM
        
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
            self.client = openai.OpenAI(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("Mode test activé - réponses LLM simulées")
        
        # Configuration des prompts
        self.system_prompts = {
            'rag_response': """Tu es un assistant intelligent spécialisé dans l'analyse de documents.
Ton rôle est de répondre aux questions en te basant UNIQUEMENT sur les informations fournies dans le contexte.

Règles importantes :
1. Utilise SEULEMENT les informations du contexte fourni
2. Si l'information n'est pas dans le contexte, dis clairement que tu ne peux pas répondre
3. Cite tes sources en indiquant [Source X] quand tu utilises une information
4. Sois précis et factuel
5. Réponds en français de manière claire et structurée""",
            
            'document_summary': """Tu es un assistant spécialisé dans la synthèse de documents.
Ton rôle est de créer des résumés clairs et structurés du contenu fourni.

Règles :
1. Identifie les points clés du document
2. Structure le résumé de manière logique
3. Reste fidèle au contenu original
4. Utilise un langage clair et accessible""",
            
            'query_enhancement': """Tu es un assistant spécialisé dans l'amélioration des requêtes de recherche.
Ton rôle est d'améliorer et d'enrichir les questions pour optimiser la recherche sémantique.

Règles :
1. Garde l'intention originale de la question
2. Ajoute des synonymes et termes connexes
3. Reformule pour être plus spécifique si nécessaire
4. Reste dans la même langue que la question originale"""
        }
        
        # Limites de tokens par modèle
        self.token_limits = {
            'gpt-3.5-turbo': 4096,
            'gpt-3.5-turbo-16k': 16384,
            'gpt-4': 8192,
            'gpt-4-32k': 32768,
            'gpt-4-turbo': 128000
        }
        
        logger.info(f"Service LLM initialisé - Modèle: {self.model_name}, Mode test: {self.test_mode}")
    
    def get_token_limit(self) -> int:
        """Retourne la limite de tokens pour le modèle actuel"""
        return self.token_limits.get(self.model_name, 4096)
    
    def estimate_tokens(self, text: str) -> int:
        """Estime le nombre de tokens dans un texte (approximation)"""
        # Approximation simple: 1 token ≈ 0.75 mots en français
        words = len(text.split())
        return int(words / 0.75)
    
    def truncate_context(self, context: str, max_tokens: int = None) -> str:
        """Tronque le contexte pour respecter les limites de tokens"""
        if max_tokens is None:
            max_tokens = int(self.get_token_limit() * 0.6)  # 60% pour le contexte
        
        current_tokens = self.estimate_tokens(context)
        if current_tokens <= max_tokens:
            return context
        
        # Tronquer en gardant le début (plus important généralement)
        words = context.split()
        target_words = int(max_tokens * 0.75)
        truncated = ' '.join(words[:target_words])
        
        logger.warning(f"Contexte tronqué de {current_tokens} à {self.estimate_tokens(truncated)} tokens")
        return truncated + "... [contexte tronqué]"
    
    def _get_test_response(self, prompt_type: str, question: str, context: str = "") -> str:
        """Génère une réponse simulée pour les tests"""
        test_responses = {
            'rag_response': f"""Basé sur le contexte fourni, voici ma réponse à la question "{question}":

{context[:200] if context else "Pas de contexte fourni"}...

Cette réponse est générée en mode test. Dans un environnement de production, 
elle serait générée par {self.model_name}.

[Source 1] - Document de test""",
            
            'document_summary': f"""Résumé du document (mode test):

Points clés identifiés:
- Contenu principal: {context[:100] if context else "Contenu non spécifié"}...
- Structure: Document organisé en sections
- Thématiques: Basées sur le contenu fourni

Ce résumé est généré en mode test.""",
            
            'query_enhancement': f"""Question améliorée (mode test):
{question} - mots-clés associés recherche sémantique optimisée"""
        }
        
        return test_responses.get(prompt_type, f"Réponse test pour: {question}")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Génère une completion avec gestion des erreurs et retry
        
        Args:
            messages: Liste des messages (system, user, assistant)
            temperature: Contrôle la créativité (0.0 à 1.0)
            max_tokens: Limite de tokens pour la réponse
        
        Returns:
            Texte généré par le LLM
        """
        if self.test_mode:
            # En mode test, retourner une réponse simulée
            user_message = next((msg['content'] for msg in messages if msg['role'] == 'user'), "")
            return f"Réponse test pour: {user_message[:100]}..."
        
        try:
            # Calculer max_tokens si non spécifié
            if max_tokens is None:
                total_input_tokens = sum(self.estimate_tokens(msg['content']) for msg in messages)
                max_tokens = min(1000, self.get_token_limit() - total_input_tokens - 200)
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            content = response.choices[0].message.content
            logger.info(f"Completion générée - Tokens: ~{self.estimate_tokens(content)}")
            return content
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération: {e}")
            raise
    
    def generate_rag_response(
        self,
        question: str,
        context: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Génère une réponse RAG basée sur le contexte et la question
        
        Args:
            question: Question de l'utilisateur
            context: Contexte récupéré par la recherche sémantique
            conversation_history: Historique de conversation optionnel
        
        Returns:
            Dict avec la réponse et les métadonnées
        """
        if self.test_mode:
            return {
                'answer': self._get_test_response('rag_response', question, context),
                'model': self.model_name,
                'tokens_used': 150,
                'context_length': len(context),
                'test_mode': True
            }
        
        try:
            # Tronquer le contexte si nécessaire
            truncated_context = self.truncate_context(context)
            
            # Construire les messages
            messages = [
                {"role": "system", "content": self.system_prompts['rag_response']}
            ]
            
            # Ajouter l'historique si fourni
            if conversation_history:
                messages.extend(conversation_history[-4:])  # Garder les 4 derniers échanges
            
            # Ajouter la question actuelle avec le contexte
            user_content = f"""Contexte:
{truncated_context}

Question: {question}"""
            
            messages.append({"role": "user", "content": user_content})
            
            # Générer la réponse
            answer = self.generate_completion(messages, temperature=0.3)
            
            return {
                'answer': answer,
                'model': self.model_name,
                'tokens_used': self.estimate_tokens(answer),
                'context_length': len(truncated_context),
                'test_mode': False
            }
            
        except Exception as e:
            logger.error(f"Erreur génération réponse RAG: {e}")
            return {
                'answer': f"Désolé, je ne peux pas répondre à cette question pour le moment. Erreur: {str(e)}",
                'model': self.model_name,
                'tokens_used': 0,
                'context_length': len(context),
                'error': str(e),
                'test_mode': False
            }
    
    def summarize_document(self, content: str) -> Dict[str, Any]:
        """
        Génère un résumé d'un document
        
        Args:
            content: Contenu du document à résumer
        
        Returns:
            Dict avec le résumé et les métadonnées
        """
        if self.test_mode:
            return {
                'summary': self._get_test_response('document_summary', '', content),
                'model': self.model_name,
                'tokens_used': 100,
                'test_mode': True
            }
        
        try:
            # Tronquer le contenu si nécessaire
            truncated_content = self.truncate_context(content, max_tokens=3000)
            
            messages = [
                {"role": "system", "content": self.system_prompts['document_summary']},
                {"role": "user", "content": f"Résume ce document:\n\n{truncated_content}"}
            ]
            
            summary = self.generate_completion(messages, temperature=0.5)
            
            return {
                'summary': summary,
                'model': self.model_name,
                'tokens_used': self.estimate_tokens(summary),
                'test_mode': False
            }
            
        except Exception as e:
            logger.error(f"Erreur génération résumé: {e}")
            return {
                'summary': f"Impossible de générer un résumé. Erreur: {str(e)}",
                'model': self.model_name,
                'tokens_used': 0,
                'error': str(e),
                'test_mode': False
            }
    
    def enhance_query(self, query: str) -> Dict[str, Any]:
        """
        Améliore une requête pour optimiser la recherche sémantique
        
        Args:
            query: Requête originale
        
        Returns:
            Dict avec la requête améliorée
        """
        if self.test_mode:
            return {
                'enhanced_query': self._get_test_response('query_enhancement', query),
                'original_query': query,
                'model': self.model_name,
                'test_mode': True
            }
        
        try:
            messages = [
                {"role": "system", "content": self.system_prompts['query_enhancement']},
                {"role": "user", "content": f"Améliore cette requête pour la recherche sémantique: {query}"}
            ]
            
            enhanced = self.generate_completion(messages, temperature=0.3, max_tokens=200)
            
            return {
                'enhanced_query': enhanced,
                'original_query': query,
                'model': self.model_name,
                'test_mode': False
            }
            
        except Exception as e:
            logger.error(f"Erreur amélioration requête: {e}")
            return {
                'enhanced_query': query,  # Retourner la requête originale en cas d'erreur
                'original_query': query,
                'model': self.model_name,
                'error': str(e),
                'test_mode': False
            }

# Instance globale du service
llm_service = LLMService()
