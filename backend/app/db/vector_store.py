"""
Watchout Backend - Atlas Vector Search
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import asyncio
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import logging

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    _ST_AVAILABLE = True
except ImportError:
    SentenceTransformer = None  # type: ignore
    _ST_AVAILABLE = False

# Thread pool for CPU-bound embedding — keeps asyncio event loop unblocked (AR1)
_EMBED_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="embed")

from app.db.mongo import memories_collection
from app.core.config import settings


class VectorStore:
    """
    Vector store using MongoDB Atlas Vector Search.
    Handles embedding generation and semantic search.
    """
    
    _model = None
    _embedding_dim: int = 384  # all-MiniLM-L6-v2 dimension
    
    def __init__(self):
        """Initialize VectorStore."""
        # Warm up model if needed
        self.get_model()
    
    @classmethod
    def get_model(cls):
        """Get or initialize the embedding model."""
        if not _ST_AVAILABLE:
            return None
        if cls._model is None:
            # Using a lightweight model for fast embeddings
            cls._model = SentenceTransformer("all-MiniLM-L6-v2")
        return cls._model
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding (synchronous — use generate_embedding_async in async contexts)."""
        model = self.get_model()
        if model is None:
            return []  # No embeddings without sentence-transformers
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    async def generate_embedding_async(self, text: str) -> List[float]:
        """
        Async wrapper — runs SentenceTransformer.encode() in a thread pool.

        SentenceTransformer.encode() is CPU-bound (numpy matmul). Calling it
        directly in a coroutine blocks the entire asyncio event loop, which
        freezes all concurrent SSE streams. This offloads the work to a
        dedicated 2-thread executor so the event loop stays responsive (AR1).
        """
        model = self.get_model()
        if model is None:
            return []
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _EMBED_EXECUTOR,
            lambda: model.encode(text, convert_to_numpy=True).tolist(),
        )
    
    async def store_memory(
        self,
        user_id: str,
        content: str,
        memory_type: str = "preference",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a memory with its embedding.
        
        Args:
            user_id: User's Firebase UID
            content: The text content to store
            memory_type: Type of memory (preference, trip_note, conversation, etc.)
            metadata: Additional metadata to store
        
        Returns:
            The inserted document ID
        """
        # Use async embedding to avoid blocking the event loop (AR1)
        embedding = await self.generate_embedding_async(content)
        
        document = {
            "user_id": user_id,
            "content": content,
            "type": memory_type,
            "embedding": embedding,
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc)
        }
        
        collection = memories_collection()
        result = await collection.insert_one(document)
        return str(result.inserted_id)
    
    async def search_memories(
        self,
        user_id: str,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar memories using vector similarity.
        
        Args:
            user_id: User's Firebase UID
            query: The search query
            memory_type: Optional filter by memory type
            limit: Maximum number of results
        
        Returns:
            List of matching memories with similarity scores
        """
        query_embedding = self.generate_embedding(query)
        
        # Build the vector search pipeline
        # Note: This requires Atlas Vector Search index to be configured
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "memory_vector_index",
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": limit * 10,
                    "limit": limit,
                    "filter": {"user_id": user_id}
                }
            },
            {
                "$project": {
                    "content": 1,
                    "type": 1,
                    "metadata": 1,
                    "created_at": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]
        
        # Add type filter if specified
        if memory_type:
            pipeline[0]["$vectorSearch"]["filter"]["type"] = memory_type
        
        collection = memories_collection()
        
        try:
            results = await collection.aggregate(pipeline).to_list(length=limit)
            return results
        except Exception as e:
            # Fallback to simple text search if vector search is not configured
            logger.warning("Vector search failed, falling back to text search: %s", e)
            return await self._fallback_search(user_id, query, memory_type, limit)
    
    async def _fallback_search(
        self,
        user_id: str,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Text-search fallback when vector search is unavailable.

        Uses MongoDB $text operator (backed by a text index on `content`)
        instead of $regex to prevent ReDoS via catastrophic backtracking.
        Query is capped at 200 chars as an additional guard.
        """
        collection = memories_collection()

        # Truncate query — prevents abusive long regex-like strings
        safe_query = query[:200].strip()
        if not safe_query:
            return []

        filter_query: Dict[str, Any] = {
            "user_id": user_id,
            "$text": {"$search": safe_query},
        }
        if memory_type:
            filter_query["type"] = memory_type

        cursor = collection.find(
            filter_query,
            {
                "embedding": 0,
                "score": {"$meta": "textScore"},
            }
        ).sort(
            [("score", {"$meta": "textScore"})]
        ).limit(limit)

        results = await cursor.to_list(length=limit)

        # Normalise score field for consistency with vector search results
        for result in results:
            result["score"] = result.get("score", 0.5)

        return results
    
    async def delete_user_memories(self, user_id: str) -> int:
        """Delete all memories for a user (for GDPR/data deletion)."""
        collection = memories_collection()
        result = await collection.delete_many({"user_id": user_id})
        return result.deleted_count
    
    async def get_recent_memories(
        self,
        user_id: str,
        limit: int = 10,
        memory_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get most recent memories for a user."""
        collection = memories_collection()
        
        filter_query = {"user_id": user_id}
        if memory_type:
            filter_query["type"] = memory_type
        
        cursor = collection.find(
            filter_query,
            {"embedding": 0}
        ).sort("created_at", -1).limit(limit)
        
        return await cursor.to_list(length=limit)


# Convenience function for dependency injection
async def get_vector_store() -> VectorStore:
    """Get vector store instance."""
    return VectorStore()
