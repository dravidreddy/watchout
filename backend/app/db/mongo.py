"""
Watchout Backend - MongoDB Connection
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import asyncio
import logging

logger = logging.getLogger(__name__)
import certifi

from app.core.config import settings


class MongoDB:
    """MongoDB connection manager using Motor async driver."""
    
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    
    @classmethod
    async def connect(cls) -> None:
        """Connect to MongoDB Atlas."""
        if cls.client is not None:
            return
        
        try:
            cls.client = AsyncIOMotorClient(
                settings.mongodb_uri,
                maxPoolSize=50,
                minPoolSize=10,
                serverSelectionTimeoutMS=5000,
                tlsCAFile=certifi.where()
            )
            
            # Verify connection
            await cls.client.admin.command("ping")
            
            cls.db = cls.client[settings.mongodb_db_name]
            logger.info("Connected to MongoDB: %s", settings.mongodb_db_name)
            
            # Create indexes
            await cls._create_indexes()
            
        except Exception as e:
            logger.error("Failed to connect to MongoDB: %s", e)
            import sys
            sys.exit(1)
    
    @classmethod
    async def disconnect(cls) -> None:
        """Disconnect from MongoDB."""
        if cls.client is not None:
            cls.client.close()
            cls.client = None
            cls.db = None
            logger.info("Disconnected from MongoDB")
    
    @classmethod
    async def _create_indexes(cls) -> None:
        """Create necessary database indexes."""
        if cls.db is None:
            return
        
        # Users collection indexes
        await cls.db.users.create_index("firebase_id", unique=True)
        await cls.db.users.create_index("email")
        
        # Destinations collection indexes
        await cls.db.destinations.create_index([("location", "2dsphere")])
        await cls.db.destinations.create_index([("name", "text"), ("category", "text")])
        
        # Trips collection indexes
        await cls.db.trips.create_index("user_id")
        await cls.db.trips.create_index([("user_id", 1), ("created_at", -1)])
        await cls.db.trips.create_index([
            ("title", "text"),
            ("cities", "text")
        ])
        
        # Messages collection indexes (Chat History)
        await cls.db.messages.create_index("trip_id")
        await cls.db.messages.create_index([("trip_id", 1), ("created_at", -1)])
        
        # Conversations collection indexes (Legacy/Unused?)
        # await cls.db.conversations.create_index("trip_id")
        # await cls.db.conversations.create_index([("trip_id", 1), ("timestamp", -1)])
        
        # Memory collection indexes (for vector search)
        await cls.db.memories.create_index("user_id")
        await cls.db.memories.create_index([("user_id", 1), ("type", 1)])
        # Text index on memories.content — required for the $text-based _fallback_search
        # (replaces the $regex approach that was vulnerable to ReDoS)
        await cls.db.memories.create_index(
            [("content", "text")],
            default_language="english",
            background=True,
        )

        # Compound index for IDOR-fixed message queries (trip_id + user_id)
        await cls.db.messages.create_index([("trip_id", 1), ("user_id", 1), ("created_at", -1)])

        # TTL index — messages expire 90 days after last_accessed_at.
        # Each conversation open refreshes last_accessed_at, so the clock resets on every visit.
        # A conversation untouched for 90 days is automatically deleted.
        await cls.db.messages.create_index(
            "last_accessed_at",
            expireAfterSeconds=7_776_000,  # 90 days = 90 × 24 × 3600
            name="messages_ttl_90d",
            sparse=True,                   # skip docs that don't have this field yet
        )
        
        # Places cache with TTL (expires after 24 hours)
        await cls.db.places_cache.create_index("place_id", unique=True)
        await cls.db.places_cache.create_index(
            "cached_at",
            expireAfterSeconds=86400  # 24 hours
        )
        
        # Payments collection
        await cls.db.payments.create_index("user_id")
        await cls.db.payments.create_index("razorpay_order_id", unique=True, sparse=True)
        
        # Sharing collection — unique index for shared trip lookups
        await cls.db.trips.create_index("sharing_id", unique=True, sparse=True)
        
        logger.info("Database indexes created successfully")
    
    @classmethod
    def get_db(cls) -> AsyncIOMotorDatabase:
        """Get database instance."""
        if cls.db is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return cls.db
    
    @classmethod
    def get_collection(cls, name: str):
        """Get a specific collection."""
        return cls.get_db()[name]


# Convenience functions
async def get_database() -> AsyncIOMotorDatabase:
    """Dependency for getting database in routes."""
    return MongoDB.get_db()


def users_collection():
    """Get users collection."""
    return MongoDB.get_collection("users")


def trips_collection():
    """Get trips collection."""
    return MongoDB.get_collection("trips")


def conversations_collection():
    """Get conversations collection."""
    return MongoDB.get_collection("conversations")


def memories_collection():
    """Get memories collection (for vector search)."""
    return MongoDB.get_collection("memories")


def places_cache_collection():
    """Get places cache collection."""
    return MongoDB.get_collection("places_cache")


def payments_collection():
    """Get payments collection."""
    return MongoDB.get_collection("payments")
