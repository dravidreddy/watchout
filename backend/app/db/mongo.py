"""
Watchout Backend - MongoDB Connection
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import asyncio
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
            print(f"Connected to MongoDB: {settings.mongodb_db_name}")
            
            # Create indexes
            await cls._create_indexes()
            
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise
    
    @classmethod
    async def disconnect(cls) -> None:
        """Disconnect from MongoDB."""
        if cls.client is not None:
            cls.client.close()
            cls.client = None
            cls.db = None
            print("Disconnected from MongoDB")
    
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
        
        # Conversations collection indexes
        await cls.db.conversations.create_index("trip_id")
        await cls.db.conversations.create_index([("trip_id", 1), ("timestamp", -1)])
        
        # Memory collection indexes (for vector search)
        await cls.db.memories.create_index("user_id")
        await cls.db.memories.create_index([("user_id", 1), ("type", 1)])
        
        # Places cache with TTL (expires after 24 hours)
        await cls.db.places_cache.create_index("place_id", unique=True)
        await cls.db.places_cache.create_index(
            "cached_at",
            expireAfterSeconds=86400  # 24 hours
        )
        
        # Payments collection
        await cls.db.payments.create_index("user_id")
        await cls.db.payments.create_index("razorpay_order_id", unique=True, sparse=True)
        
        print("Database indexes created successfully")
    
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
