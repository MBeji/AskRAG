# Minimal ChromaDB vector store integration
from pathlib import Path
import os

try:
    import chromadb
    from chromadb.config import Settings
    chroma_client = chromadb.Client(Settings(
        persist_directory=str(Path("data/chroma_db"))
    ))
except ImportError:
    chroma_client = None

COLLECTION_PREFIX = "askrag_user_"

def add_document_embeddings(user_id: str, filename: str, chunks: list, embeddings: list):
    if not chroma_client or not embeddings:
        return False
    collection_name = COLLECTION_PREFIX + str(user_id)
    collection = chroma_client.get_or_create_collection(collection_name)
    ids = [f"{filename}_{i}" for i in range(len(chunks))]
    collection.add(
        embeddings=embeddings,
        documents=chunks,
        ids=ids,
        metadatas=[{"filename": filename, "chunk_id": i} for i in range(len(chunks))]
    )
    chroma_client.persist()
    return True

def query_similar_chunk(user_id: str, filename: str, query_embedding: list):
    if not chroma_client:
        return None
    collection_name = COLLECTION_PREFIX + str(user_id)
    collection = chroma_client.get_or_create_collection(collection_name)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=1,
        where={"filename": filename}
    )
    if results and results.get("documents"):
        return results["documents"][0][0]
    return None
