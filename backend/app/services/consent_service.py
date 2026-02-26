"""
Consent Service for DPDP Act Compliance
Handles consent recording, retrieval, and withdrawal.
"""
from datetime import datetime, timezone
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorCollection

from app.db.mongo import MongoDB
from app.models.consent import ConsentRecord


class ConsentService:
    """Service for managing user consent per DPDP Act requirements."""
    
    @staticmethod
    def get_collection() -> AsyncIOMotorCollection:
        """Get the consents collection."""
        db = MongoDB.get_db()
        return db["user_consents"]
    
    @staticmethod
    async def record_consent(
        user_id: str,
        purpose: str,
        consented: bool,
        ip_address: str,
        user_agent: str,
        purpose_version: str = "1.0"
    ) -> str:
        """
        Record user consent for a specific purpose.
        
        Args:
            user_id: Firebase UID
            purpose: Purpose of data processing
            consented: Whether user consented
            ip_address: User's IP address
            user_agent: User's browser user agent
            purpose_version: Version of T&C (default: 1.0)
        
        Returns:
            Inserted document ID
        """
        collection = ConsentService.get_collection()
        
        record = {
            "user_id": user_id,
            "purpose": purpose,
            "purpose_version": purpose_version,
            "consented": consented,
            "consent_timestamp": datetime.now(timezone.utc),
            "ip_address": ip_address,
            "user_agent": user_agent,
            "withdrawal_timestamp": None
        }
        
        result = await collection.insert_one(record)
        return str(result.inserted_id)
    
    @staticmethod
    async def check_consent(user_id: str, purpose: str) -> bool:
        """
        Check if user has active consent for a purpose.
        
        Args:
            user_id: Firebase UID
            purpose: Purpose to check
        
        Returns:
            True if user has active consent, False otherwise
        """
        collection = ConsentService.get_collection()
        
        consent = await collection.find_one({
            "user_id": user_id,
            "purpose": purpose,
            "consented": True,
            "withdrawal_timestamp": None
        })
        
        return consent is not None
    
    @staticmethod
    async def get_all_consents(user_id: str) -> dict[str, bool]:
        """
        Get all active consents for a user.
        
        Args:
            user_id: Firebase UID
        
        Returns:
            Dictionary mapping purpose to consent status
        """
        collection = ConsentService.get_collection()
        
        # Get all consent records for user
        cursor = collection.find({"user_id": user_id})
        records = await cursor.to_list(length=100)
        
        # Build consent map (latest record per purpose)
        consent_map = {}
        for record in records:
            purpose = record["purpose"]
            # Only count as active if consented=True and not withdrawn
            is_active = (
                record["consented"] and 
                record.get("withdrawal_timestamp") is None
            )
            consent_map[purpose] = is_active
        
        return consent_map
    
    @staticmethod
    async def withdraw_consent(user_id: str, purpose: str) -> bool:
        """
        Withdraw user consent for a specific purpose.
        
        Args:
            user_id: Firebase UID
            purpose: Purpose to withdraw
        
        Returns:
            True if consent was withdrawn, False if not found
        """
        collection = ConsentService.get_collection()
        
        result = await collection.update_one(
            {
                "user_id": user_id,
                "purpose": purpose,
                "consented": True,
                "withdrawal_timestamp": None
            },
            {
                "$set": {"withdrawal_timestamp": datetime.now(timezone.utc)}
            }
        )
        
        return result.modified_count > 0
    
    @staticmethod
    async def get_consent_history(
        user_id: str, 
        purpose: Optional[str] = None
    ) -> list[dict]:
        """
        Get full consent history for audit trail.
        
        Args:
            user_id: Firebase UID
            purpose: Optional specific purpose to filter by
        
        Returns:
            List of consent records
        """
        collection = ConsentService.get_collection()
        
        query = {"user_id": user_id}
        if purpose:
            query["purpose"] = purpose
        
        cursor = collection.find(query).sort("consent_timestamp", -1)
        records = await cursor.to_list(length=100)
        
        return records
    
    @staticmethod
    async def create_indexes():
        """Create database indexes for performance."""
        collection = ConsentService.get_collection()
        
        # Index on user_id + purpose for fast lookups
        await collection.create_index([("user_id", 1), ("purpose", 1)])
        
        # Index on consent_timestamp for audit queries
        await collection.create_index([("consent_timestamp", -1)])
        
        # Index on user_id for getting all user consents
        await collection.create_index([("user_id", 1)])
