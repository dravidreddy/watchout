"""
User Deletion Service for DPDP Act Complete Right to Erasure
Handles cascade deletion across all collections.
"""
from datetime import datetime, timezone
from typing import Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongo import MongoDB
from app.services.consent_service import ConsentService


class UserDeletionService:
    """
    Handle complete user data deletion per DPDP Act Right to Erasure.
    Deletes user data from ALL collections and services.
    """
    
    @staticmethod
    async def delete_user_completely(user_id: str) -> Dict[str, Any]:
        """
        Delete ALL user data across all collections.
        This is irreversible and required for DPDP Act compliance.
        
        Args:
            user_id: Firebase UID of user to delete
        
        Returns:
            Dictionary with deletion statistics
        """
        db: AsyncIOMotorDatabase = MongoDB.get_db()
        stats = {}
        
        # 1. Delete user profile
        users_collection = db["users"]
        result = await users_collection.delete_one({"firebase_id": user_id})
        stats["user_profile"] = result.deleted_count
        
        # 2. Delete all trips
        trips_collection = db["trips"]
        result = await trips_collection.delete_many({"user_id": user_id})
        stats["trips"] = result.deleted_count

        # 3. Delete all chat messages (primary chat history collection)
        messages_collection = db["messages"]
        result = await messages_collection.delete_many({"user_id": user_id})
        stats["messages"] = result.deleted_count

        # 4. Delete all conversations (legacy collection)
        conversations_collection = db["conversations"]
        result = await conversations_collection.delete_many({"user_id": user_id})
        stats["conversations"] = result.deleted_count

        # 5. Delete vector memories
        memories_collection = db["memories"]
        result = await memories_collection.delete_many({"user_id": user_id})
        stats["memories"] = result.deleted_count
        
        # 6. Delete consent records (keep for audit trail or delete per policy)
        # For now, we keep consent records for legal audit trail
        consent_collection = ConsentService.get_collection()
        result = await consent_collection.update_many(
            {"user_id": user_id},
            {"$set": {"data_deleted": True, "deletion_timestamp": datetime.now(timezone.utc)}}
        )
        stats["consents_marked"] = result.modified_count
        
        # 7. Anonymize payment records (CANNOT delete for financial audit)
        payments_collection = db["payments"]
        result = await payments_collection.update_many(
            {"user_id": user_id},
            {
                "$set": {
                    "user_id": "DELETED_USER",
                    "anonymized": True,
                    "anonymized_at": datetime.now(timezone.utc)
                }
            }
        )
        stats["payments_anonymized"] = result.modified_count
        
        # 8. Delete user preferences
        preferences_collection = db["user_preferences"]
        result = await preferences_collection.delete_many({"user_id": user_id})
        stats["preferences"] = result.deleted_count
        
        # 9. Log deletion for compliance audit trail
        deletion_logs_collection = db["deletion_logs"]
        await deletion_logs_collection.insert_one({
            "user_id": user_id,
            "deleted_at": datetime.now(timezone.utc),
            "stats": stats,
            "deletion_method": "user_request"
        })
        
        return stats
    
    @staticmethod
    async def verify_deletion(user_id: str) -> Dict[str, bool]:
        """
        Verify that user data has been completely deleted.
        
        Args:
            user_id: Firebase UID to check
        
        Returns:
            Dictionary showing if data exists in each collection
        """
        db: AsyncIOMotorDatabase = MongoDB.get_db()
        
        checks = {}
        
        # Check each collection
        checks["user_profile"] = await db["users"].count_documents({"firebase_id": user_id}) > 0
        checks["trips"] = await db["trips"].count_documents({"user_id": user_id}) > 0
        checks["messages"] = await db["messages"].count_documents({"user_id": user_id}) > 0
        checks["conversations"] = await db["conversations"].count_documents({"user_id": user_id}) > 0
        checks["memories"] = await db["memories"].count_documents({"user_id": user_id}) > 0
        checks["preferences"] = await db["user_preferences"].count_documents({"user_id": user_id}) > 0
        
        # Payments and consents should be anonymized, not deleted
        checks["payments_anonymized"] = await db["payments"].count_documents({
            "user_id": user_id,  # Original user_id should not exist
            "anonymized": {"$ne": True}
        }) == 0
        
        return checks
