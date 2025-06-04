# Minimal RAG retrieval module
import json
from pathlib import Path
from typing import List
import numpy as np

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def find_best_chunk(user_id: str, filename: str, query_embedding: list) -> str:
    """
    Recherche le chunk le plus proche du query_embedding pour un document donné
    """
    embeddings_path = Path("data") / "embeddings.json"
    if not embeddings_path.exists():
        return "Aucun embedding disponible."
    with open(embeddings_path, "r", encoding="utf-8") as f:
        all_embeddings = json.load(f)
    key = f"{user_id}_{filename}"
    doc = all_embeddings.get(key)
    if not doc or not doc.get("embeddings"):
        return "Pas d'embeddings pour ce document."
    best_idx = int(np.argmax([cosine_similarity(query_embedding, emb) for emb in doc["embeddings"]]))
    return doc["chunks"][best_idx]
