"""
Payment Idempotency Service
Prevents duplicate payment processing
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from app.db.mongo import MongoDB
import hashlib
import json
from pymongo.errors import DuplicateKeyError


class IdempotencyService:
    """
    Handles idempotency for payment operations
    Prevents duplicate charges from retries or multiple clicks
    """
    
    COLLECTION_NAME = "payment_idempotency"
    TTL_HOURS = 24  # Idempotency keys expire after 24 hours
    
    @classmethod
    async def generate_key(cls, user_id: str, amount: int, metadata: Dict[str, Any]) -> str:
        """
        Generate a unique idempotency key based on payment parameters
        
        Args:
            user_id: User identifier
            amount: Payment amount in paise
            metadata: Additional payment metadata
            
        Returns:
            Idempotency key (SHA256 hash)
        """
        # Create deterministic string from payment parameters
        data = json.dumps({
            "user_id": user_id,
            "amount": amount,
            "metadata": sorted(metadata.items()) if metadata else []
        }, sort_keys=True)
        
        # Generate hash
        return hashlib.sha256(data.encode()).hexdigest()
    
    @classmethod
    async def check_and_store(
        cls, 
        idempotency_key: str, 
        user_id: str,
        request_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Check if idempotency key exists and store if new
        
        Args:
            idempotency_key: Unique key for this operation
            user_id: User making the request
            request_data: Payment request data
            
        Returns:
            Previous response if duplicate, None if new request
        """
        db = MongoDB.get_db()
        collection = db[cls.COLLECTION_NAME]
        
        # Store new idempotency record (without response initially). A unique index on
        # idempotency_key makes this atomic under concurrent requests.
        now = datetime.now(timezone.utc)
        try:
            await collection.insert_one({
                "idempotency_key": idempotency_key,
                "user_id": user_id,
                "request_data": request_data,
                "created_at": now,
                "expires_at": now + timedelta(hours=cls.TTL_HOURS),
                "status": "pending",
                "response": None
            })
            return None
        except DuplicateKeyError:
            existing = await collection.find_one({"idempotency_key": idempotency_key})
            if existing and existing.get("status") == "failed":
                # Allow retry by resetting the record
                await collection.update_one(
                    {"idempotency_key": idempotency_key},
                    {
                        "$set": {
                            "status": "pending",
                            "response": None,
                            "created_at": now,
                            "expires_at": now + timedelta(hours=cls.TTL_HOURS)
                        }
                    }
                )
                return None
            return existing.get("response") if existing else None

    
    @classmethod
    async def store_response(
        cls, 
        idempotency_key: str, 
        response_data: Dict[str, Any],
        status: str = "success"
    ) -> None:
        """
        Store the response for an idempotency key
        
        Args:
            idempotency_key: Unique key for this operation
            response_data: Payment response to cache
            status: Status of the operation (success/failed)
        """
        db = MongoDB.get_db()
        collection = db[cls.COLLECTION_NAME]
        
        await collection.update_one(
            {"idempotency_key": idempotency_key},
            {
                "$set": {
                    "response": response_data,
                    "status": status,
                    "completed_at": datetime.now(timezone.utc)
                }
            }
        )
    
    @classmethod
    async def cleanup_expired(cls) -> int:
        """
        Remove expired idempotency records
        
        Returns:
            Number of records deleted
        """
        db = MongoDB.get_db()
        collection = db[cls.COLLECTION_NAME]
        
        result = await collection.delete_many({
            "expires_at": {"$lt": datetime.now(timezone.utc)}
        })
        
        return result.deleted_count
    
    @classmethod
    async def get_by_key(cls, idempotency_key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve idempotency record by key
        
        Args:
            idempotency_key: Key to lookup
            
        Returns:
            Idempotency record or None
        """
        db = MongoDB.get_db()
        collection = db[cls.COLLECTION_NAME]
        
        return await collection.find_one({"idempotency_key": idempotency_key})
