"""
Service de Chunking Intelligent de Documents
Étape 14.6: Découpage intelligent de texte pour RAG
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ChunkStrategy(Enum):
    """Stratégies de découpage de texte"""
    SENTENCE = "sentence"           # Par phrases
    PARAGRAPH = "paragraph"         # Par paragraphes
    FIXED_SIZE = "fixed_size"       # Taille fixe
    SEMANTIC = "semantic"           # Sémantique (sections)
    HYBRID = "hybrid"               # Hybride (combiné)


@dataclass
class ChunkMetadata:
    """Métadonnées d'un chunk"""
    chunk_id: str
    source_document: str
    chunk_index: int
    start_position: int
    end_position: int
    chunk_type: str
    word_count: int
    char_count: int
    overlap_chars: int = 0


class TextChunker:
    """
    Service de découpage intelligent de texte
    Optimisé pour la recherche sémantique et le RAG
    """
    
    def __init__(self,
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200,
                 min_chunk_size: int = 100,
                 strategy: ChunkStrategy = ChunkStrategy.HYBRID):
        """
        Initialise le chunker
        
        Args:
            chunk_size: Taille maximale des chunks en caractères
            chunk_overlap: Chevauchement entre chunks en caractères
            min_chunk_size: Taille minimale d'un chunk
            strategy: Stratégie de découpage
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.strategy = strategy
        
        self.logger = logging.getLogger(__name__)
        
        # Patterns regex pour le découpage
        self._init_patterns()
        
        self.logger.info(f"TextChunker initialisé - Stratégie: {strategy.value}")
    
    def _init_patterns(self):
        """Initialise les patterns regex pour le découpage"""
        # Séparateurs de phrases
        self.sentence_pattern = re.compile(
            r'(?<=[.!?])\s+(?=[A-Z])|(?<=[.!?])\s*\n+\s*(?=[A-Z])',
            re.MULTILINE
        )
        
        # Séparateurs de paragraphes
        self.paragraph_pattern = re.compile(r'\n\s*\n+', re.MULTILINE)
        
        # Sections (titres)
        self.section_pattern = re.compile(
            r'(?:^|\n)(?:#{1,6}\s+.*|[A-Z][^.!?]*:(?:\s|$)|.*\n[-=]{3,})',
            re.MULTILINE
        )
        
        # Séparateurs logiques (listes, etc.)
        self.logical_pattern = re.compile(
            r'(?:^|\n)(?:[-*+•]\s+|[0-9]+\.\s+|[a-z]\)\s+)',
            re.MULTILINE
        )
    
    def chunk_text(self, 
                  text: str,
                  document_id: str = "document",
                  metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Découpe un texte en chunks
        
        Args:
            text: Texte à découper
            document_id: Identifiant du document source
            metadata: Métadonnées additionnelles
            
        Returns:
            List[Dict]: Liste des chunks avec métadonnées
        """
        if not text or not text.strip():
            return []
        
        text = text.strip()
        metadata = metadata or {}
        
        try:
            # Choisir la stratégie de découpage
            if self.strategy == ChunkStrategy.SENTENCE:
                chunks = self._chunk_by_sentences(text)
            elif self.strategy == ChunkStrategy.PARAGRAPH:
                chunks = self._chunk_by_paragraphs(text)
            elif self.strategy == ChunkStrategy.FIXED_SIZE:
                chunks = self._chunk_by_fixed_size(text)
            elif self.strategy == ChunkStrategy.SEMANTIC:
                chunks = self._chunk_by_semantic_sections(text)
            else:  # HYBRID
                chunks = self._chunk_hybrid(text)
            
            # Ajouter les métadonnées
            processed_chunks = []
            for i, (chunk_text, start_pos, end_pos) in enumerate(chunks):
                if len(chunk_text.strip()) < self.min_chunk_size:
                    continue
                
                chunk_metadata = ChunkMetadata(
                    chunk_id=f"{document_id}_chunk_{i}",
                    source_document=document_id,
                    chunk_index=i,
                    start_position=start_pos,
                    end_position=end_pos,
                    chunk_type=self.strategy.value,
                    word_count=len(chunk_text.split()),
                    char_count=len(chunk_text),
                    overlap_chars=self._calculate_overlap(i, chunks)
                )
                
                chunk_data = {
                    'content': chunk_text.strip(),
                    'metadata': {
                        **metadata,
                        **chunk_metadata.__dict__
                    }
                }
                
                processed_chunks.append(chunk_data)
            
            self.logger.debug(f"Texte découpé en {len(processed_chunks)} chunks")
            return processed_chunks
            
        except Exception as e:
            self.logger.error(f"Erreur chunking: {e}")
            return []
    
    def _chunk_by_sentences(self, text: str) -> List[Tuple[str, int, int]]:
        """Découpe par phrases avec regroupement"""
        sentences = self.sentence_pattern.split(text)
        chunks = []
        current_chunk = ""
        start_pos = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Vérifier si ajouter cette phrase dépasse la limite
            potential_chunk = current_chunk + " " + sentence if current_chunk else sentence
            
            if len(potential_chunk) <= self.chunk_size:
                current_chunk = potential_chunk
            else:
                # Sauvegarder le chunk actuel s'il n'est pas vide
                if current_chunk:
                    end_pos = start_pos + len(current_chunk)
                    chunks.append((current_chunk, start_pos, end_pos))
                    start_pos = max(0, end_pos - self.chunk_overlap)
                
                # Commencer un nouveau chunk
                current_chunk = sentence
        
        # Ajouter le dernier chunk
        if current_chunk:
            end_pos = start_pos + len(current_chunk)
            chunks.append((current_chunk, start_pos, end_pos))
        
        return chunks
    
    def _chunk_by_paragraphs(self, text: str) -> List[Tuple[str, int, int]]:
        """Découpe par paragraphes avec regroupement"""
        paragraphs = self.paragraph_pattern.split(text)
        chunks = []
        current_chunk = ""
        start_pos = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # Vérifier si ajouter ce paragraphe dépasse la limite
            potential_chunk = current_chunk + "\n\n" + paragraph if current_chunk else paragraph
            
            if len(potential_chunk) <= self.chunk_size:
                current_chunk = potential_chunk
            else:
                # Sauvegarder le chunk actuel
                if current_chunk:
                    end_pos = start_pos + len(current_chunk)
                    chunks.append((current_chunk, start_pos, end_pos))
                    start_pos = max(0, end_pos - self.chunk_overlap)
                
                # Si le paragraphe est trop long, le découper
                if len(paragraph) > self.chunk_size:
                    sub_chunks = self._chunk_by_fixed_size(paragraph)
                    for sub_chunk, sub_start, sub_end in sub_chunks:
                        chunks.append((sub_chunk, start_pos + sub_start, start_pos + sub_end))
                    start_pos = chunks[-1][2] - self.chunk_overlap if chunks else 0
                    current_chunk = ""
                else:
                    current_chunk = paragraph
        
        # Ajouter le dernier chunk
        if current_chunk:
            end_pos = start_pos + len(current_chunk)
            chunks.append((current_chunk, start_pos, end_pos))
        
        return chunks
    
    def _chunk_by_fixed_size(self, text: str) -> List[Tuple[str, int, int]]:
        """Découpe par taille fixe avec respect des mots"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            
            # Ajuster pour ne pas couper les mots
            if end < len(text):
                # Chercher le dernier espace avant la limite
                while end > start and text[end] not in ' \n\t':
                    end -= 1
                
                # Si on n'a pas trouvé d'espace, prendre la limite
                if end == start:
                    end = min(start + self.chunk_size, len(text))
            
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append((chunk_text, start, end))
            
            # Prochaine position avec overlap
            start = max(start + 1, end - self.chunk_overlap)
        
        return chunks
    
    def _chunk_by_semantic_sections(self, text: str) -> List[Tuple[str, int, int]]:
        """Découpe par sections sémantiques (titres, etc.)"""
        # Trouver les séparateurs de sections
        matches = list(self.section_pattern.finditer(text))
        
        if not matches:
            # Pas de sections détectées, utiliser les paragraphes
            return self._chunk_by_paragraphs(text)
        
        chunks = []
        start_pos = 0
        
        for i, match in enumerate(matches):
            section_start = match.start()
            
            # Texte avant cette section
            if section_start > start_pos:
                before_text = text[start_pos:section_start].strip()
                if before_text and len(before_text) >= self.min_chunk_size:
                    chunks.append((before_text, start_pos, section_start))
            
            # Trouver la fin de cette section
            if i < len(matches) - 1:
                section_end = matches[i + 1].start()
            else:
                section_end = len(text)
            
            section_text = text[section_start:section_end].strip()
            
            # Si la section est trop longue, la subdiviser
            if len(section_text) > self.chunk_size:
                sub_chunks = self._chunk_by_paragraphs(section_text)
                for sub_chunk, sub_start, sub_end in sub_chunks:
                    chunks.append((sub_chunk, section_start + sub_start, section_start + sub_end))
            else:
                if len(section_text) >= self.min_chunk_size:
                    chunks.append((section_text, section_start, section_end))
            
            start_pos = section_end
        
        return chunks
    
    def _chunk_hybrid(self, text: str) -> List[Tuple[str, int, int]]:
        """Stratégie hybride combinant plusieurs approches"""
        # Essayer d'abord par sections sémantiques
        semantic_chunks = self._chunk_by_semantic_sections(text)
        
        # Si on a des chunks trop longs, les redécouper
        final_chunks = []
        
        for chunk_text, start_pos, end_pos in semantic_chunks:
            if len(chunk_text) <= self.chunk_size:
                final_chunks.append((chunk_text, start_pos, end_pos))
            else:
                # Redécouper par paragraphes puis par phrases si nécessaire
                para_chunks = self._chunk_by_paragraphs(chunk_text)
                
                for para_chunk, para_start, para_end in para_chunks:
                    if len(para_chunk) <= self.chunk_size:
                        final_chunks.append((
                            para_chunk,
                            start_pos + para_start,
                            start_pos + para_end
                        ))
                    else:
                        # Dernier recours: découpage par taille fixe
                        fixed_chunks = self._chunk_by_fixed_size(para_chunk)
                        for fixed_chunk, fixed_start, fixed_end in fixed_chunks:
                            final_chunks.append((
                                fixed_chunk,
                                start_pos + para_start + fixed_start,
                                start_pos + para_start + fixed_end
                            ))
        
        return final_chunks
    
    def _calculate_overlap(self, chunk_index: int, chunks: List[Tuple[str, int, int]]) -> int:
        """Calcule le chevauchement pour un chunk donné"""
        if chunk_index == 0:
            return 0
        
        current_start = chunks[chunk_index][1]
        previous_end = chunks[chunk_index - 1][2]
        
        return max(0, previous_end - current_start)
    
    def get_chunk_stats(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcule les statistiques des chunks"""
        if not chunks:
            return {}
        
        char_counts = [chunk['metadata']['char_count'] for chunk in chunks]
        word_counts = [chunk['metadata']['word_count'] for chunk in chunks]
        
        return {
            'total_chunks': len(chunks),
            'avg_char_count': sum(char_counts) / len(char_counts),
            'min_char_count': min(char_counts),
            'max_char_count': max(char_counts),
            'avg_word_count': sum(word_counts) / len(word_counts),
            'strategy': self.strategy.value,
            'chunk_size_limit': self.chunk_size,
            'overlap_size': self.chunk_overlap
        }


# Instance globale
text_chunker = TextChunker()
