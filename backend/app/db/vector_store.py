"""
Watchout Backend - Atlas Vector Search
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    _ST_AVAILABLE = True
except ImportError:
    SentenceTransformer = None  # type: ignore
    _ST_AVAILABLE = False

from app.db.mongo import memories_collection
from app.core.config import settings


class VectorStore:
    """
    Vector store using MongoDB Atlas Vector Search.
    Handles embedding generation and semantic search.
    """
    
    _model = None
    _embedding_dim: int = 384  # all-MiniLM-L6-v2 dimension
    
    @classmethod
    def get_model(cls):
        """Get or initialize the embedding model."""
        if not _ST_AVAILABLE:
            return None
        if cls._model is None:
            # Using a lightweight model for fast embeddings
            cls._model = SentenceTransformer("all-MiniLM-L6-v2")
        return cls._model
    
    @classmethod
    def generate_embedding(cls, text: str) -> List[float]:
        """Generate embedding for a text string."""
        model = cls.get_model()
        if model is None:
            return []  # No embeddings without sentence-transformers
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    @classmethod
    async def store_memory(
        cls,
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
        embedding = cls.generate_embedding(content)
        
        document = {
            "user_id": user_id,
            "content": content,
            "type": memory_type,
            "embedding": embedding,
            "metadata": metadata or {},
            "created_at": datetime.utcnow()
        }
        
        collection = memories_collection()
        result = await collection.insert_one(document)
        return str(result.inserted_id)
    
    @classmethod
    async def search_memories(
        cls,
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
        query_embedding = cls.generate_embedding(query)
        
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
            print(f"Vector search failed, falling back to text search: {e}")
            return await cls._fallback_search(user_id, query, memory_type, limit)
    
    @classmethod
    async def _fallback_search(
        cls,
        user_id: str,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Fallback text search when vector search is not available."""
        collection = memories_collection()
        
        filter_query = {"user_id": user_id}
        if memory_type:
            filter_query["type"] = memory_type
        
        # Simple text-based search
        filter_query["content"] = {"$regex": query, "$options": "i"}
        
        cursor = collection.find(
            filter_query,
            {"embedding": 0}  # Exclude embedding from results
        ).sort("created_at", -1).limit(limit)
        
        results = await cursor.to_list(length=limit)
        
        # Add a mock score for consistency
        for result in results:
            result["score"] = 0.5
        
        return results
    
    @classmethod
    async def delete_user_memories(cls, user_id: str) -> int:
        """Delete all memories for a user (for GDPR/data deletion)."""
        collection = memories_collection()
        result = await collection.delete_many({"user_id": user_id})
        return result.deleted_count
    
    @classmethod
    async def get_recent_memories(
        cls,
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
    return VectorStore
