import logging
from typing import List, Dict, Any, Optional

from app.core.config import settings
from app.core.embeddings import generate_embeddings
from app.core.vector_store import vector_store # Global FAISS vector store instance
from app.models.user import User as UserModel # Beanie User model
from app.models.document import Document as DocumentModel # Beanie Document model
from beanie import PydanticObjectId # For converting string ID to ObjectId if necessary

logger = logging.getLogger(__name__)

async def semantic_search_in_documents(query: str, user: UserModel) -> List[Dict[str, Any]]:
    """
    Performs semantic search for a query across documents owned by the user.
    1. Generates embedding for the query.
    2. Searches FAISS vector store for relevant chunks.
    3. Retrieves chunk content and metadata from MongoDB.
    """
    if not query:
        return []

    try:
        # 1. Generate query embedding
        query_embedding_list = await generate_embeddings([query])
        if not query_embedding_list:
            logger.error("Failed to generate query embedding.")
            return []
        query_embedding = query_embedding_list[0]

        # 2. Perform search in FAISS
        # Ensure vector_store is initialized
        if vector_store is None:
            logger.error("Vector store is not initialized.")
            raise RuntimeError("Vector store not available")

        distances, faiss_doc_chunk_ids = vector_store.search(
            query_embedding=query_embedding,
            k=settings.SEARCH_TOP_K
        )

        if not faiss_doc_chunk_ids:
            logger.info(f"No relevant chunks found in FAISS for query: '{query}'")
            return []

        # 3. Retrieve chunk content and compile results
        results: List[Dict[str, Any]] = []

        # Keep track of already added mongo_doc_ids to avoid fetching same doc multiple times if not needed
        # Or, if chunks are small, fetching doc every time might be acceptable.
        # For now, simple fetch per chunk_id.

        for i, doc_chunk_id_str in enumerate(faiss_doc_chunk_ids):
            try:
                # Parse mongo_doc_id and chunk_idx from "mongo_doc_id:chunk_idx"
                parts = doc_chunk_id_str.split(':')
                if len(parts) != 2:
                    logger.warning(f"Invalid doc_chunk_id format: {doc_chunk_id_str}")
                    continue

                mongo_doc_id_str, chunk_idx_str = parts
                chunk_idx = int(chunk_idx_str)

                # Fetch DocumentModel from MongoDB
                # Important: Ensure document belongs to the user
                document = await DocumentModel.find_one(
                    DocumentModel.id == PydanticObjectId(mongo_doc_id_str), # Convert str to PydanticObjectId
                    DocumentModel.uploader_id == str(user.id) # Ensure user ownership
                )

                if document and document.chunks and 0 <= chunk_idx < len(document.chunks):
                    chunk_data = document.chunks[chunk_idx]
                    results.append({
                        "document_id": str(document.id),
                        "chunk_index": chunk_idx,
                        "chunk_text": chunk_data.get("chunk_text", ""),
                        "source_filename": document.filename, # Original filename
                        "score": distances[i] if i < len(distances) else None, # FAISS distance/score
                        # Add any other relevant metadata from document or chunk_data
                        "upload_date": document.upload_date,
                    })
                else:
                    logger.warning(f"Document or chunk not found, or access denied: doc_id={mongo_doc_id_str}, chunk_idx={chunk_idx}")

            except Exception as e:
                logger.error(f"Error processing chunk ID {doc_chunk_id_str}: {e}")
                continue # Skip this chunk if error

        # Optionally, sort results by score if not already sorted by FAISS (FAISS search returns sorted by distance)
        # results.sort(key=lambda x: x['score'], reverse=True) # If score is similarity (higher is better)
        # If score is distance (lower is better), it's already sorted.

        return results

    except RuntimeError as r_err: # Catch runtime error from vector store not available
        logger.error(f"Semantic search runtime error: {r_err}")
        # Depending on desired behavior, can re-raise or return empty
        raise # Re-raise to indicate a system level issue to the caller (API endpoint)

    except Exception as e:
        logger.error(f"An error occurred during semantic search for query '{query}': {e}")
        # Consider what to return or if to re-raise. For now, return empty list on general error.
        return []

async def get_answer_from_llm(query: str, user: UserModel) -> Dict[str, Any]:
    """
    Performs semantic search and then uses an LLM to generate an answer based on context.
    """
    if not query:
        return {"answer": "La question ne peut pas être vide.", "sources": []}

    logger.info(f"Getting LLM answer for query: '{query}' for user {user.id}")

    # 1. Perform semantic search to get relevant chunks
    try:
        retrieved_chunks = await semantic_search_in_documents(query=query, user=user)
    except Exception as e:
        logger.error(f"Error during semantic search phase for LLM answer generation: {e}")
        # Depending on the error (e.g., vector store down), might need specific handling
        # For now, treat as if no context was found.
        # This could also be raised as a 500 error from the endpoint.
        return {"answer": "Erreur lors de la recherche de documents pertinents.", "sources": []}


    if not retrieved_chunks:
        logger.info(f"No relevant chunks found for query: '{query}' during LLM answer generation.")
        return {"answer": "Je ne trouve pas d'information pertinente dans vos documents pour répondre à cette question.", "sources": []}

    # 2. Context is now the list of retrieved_chunks (List[Dict[str, Any]])
    # The llm_service.generate_answer_from_context will handle extracting text and building the context string.
    # No need to create context_strings here anymore.

    # if not context_strings: # This check is now effectively done by llm_service or if retrieved_chunks is empty
    #     logger.info(f"Relevant chunks found, but they contain no text for query: '{query}'")
    #     return {"answer": "Les documents pertinents trouvés ne contiennent pas de texte exploitable pour formuler une réponse.", "sources": retrieved_chunks}

    # 3. Call LLM service to generate answer
    try:
        from app.core.llm_service import generate_answer_from_context as llm_generate_answer

        # Pass the full retrieved_chunks list to the LLM service function
        answer = await llm_generate_answer(query=query, retrieved_chunks=retrieved_chunks)

        return {
            "answer": answer,
            "sources": retrieved_chunks # Return the same SearchResultItem structure
        }
    except RuntimeError as r_err: # Catch specific error if LLM service is not available
        logger.error(f"LLM service runtime error: {r_err}")
        raise # Re-raise to indicate a system level issue, will result in 500 at endpoint
    except Exception as e:
        logger.error(f"Error generating answer from LLM for query '{query}': {e}")
        # Return a generic error message, but still include sources if they were retrieved.
        return {"answer": "Désolé, une erreur s'est produite lors de la formulation de la réponse.", "sources": retrieved_chunks}
