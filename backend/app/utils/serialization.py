"""
Watchout Backend - Serialization Utilities

Common helpers for converting MongoDB documents to API-friendly dicts.
"""
from typing import Any, Dict, List
from motor.motor_asyncio import AsyncIOMotorCursor


def serialize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a MongoDB document for JSON serialization.
    Converts ObjectId _id to string.
    """
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


async def serialize_cursor(cursor: AsyncIOMotorCursor) -> List[Dict[str, Any]]:
    """
    Consume an async cursor and return serialized documents.
    """
    result = []
    async for doc in cursor:
        result.append(serialize_doc(doc))
    return result
