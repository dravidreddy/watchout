import contextvars
import logging
from fastapi import HTTPException
from app.core.config import settings

logger = logging.getLogger(__name__)

# Context variable to hold the user_id for the current request
current_user_id: contextvars.ContextVar[str] = contextvars.ContextVar("current_user_id", default=None)

# Daily token limit per user
DAILY_TOKEN_LIMIT = 50000

async def check_token_cap() -> None:
    """
    Check if the current user has exceeded their daily token limit.
    Raises an HTTPException (429) if exceeded.
    """
    user_id = current_user_id.get()
    if not user_id or not settings.redis_url:
        return
        
    try:
        import redis.asyncio as aioredis  # type: ignore
        r = aioredis.from_url(settings.redis_url, decode_responses=True)
        key = f"token_usage:{user_id}:daily"
        
        current = await r.get(key)
        await r.close()
        
        if current and int(current) >= DAILY_TOKEN_LIMIT:
            logger.warning("User %s exceeded daily token limit of %d", user_id, DAILY_TOKEN_LIMIT)
            raise HTTPException(
                status_code=429,
                detail=f"Daily AI processing limit reached ({DAILY_TOKEN_LIMIT} tokens). Please try again tomorrow."
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error checking token cap for user %s: %s", user_id, e)


async def increment_token_usage(prompt_tokens: int, completion_tokens: int) -> None:
    """
    Increment the user's daily token usage by the total tokens used in the request.
    """
    user_id = current_user_id.get()
    if not user_id or not settings.redis_url:
        return
        
    total_tokens = prompt_tokens + completion_tokens
    if total_tokens <= 0:
        return
        
    try:
        import redis.asyncio as aioredis  # type: ignore
        r = aioredis.from_url(settings.redis_url, decode_responses=True)
        key = f"token_usage:{user_id}:daily"
        
        # Increment and set TTL if new (using pipeline for atomic execution)
        pipe = r.pipeline()
        pipe.incrby(key, total_tokens)
        
        # We only want to set expire if the key was just created.
        # Simplest way is let it expire 24h from first request.
        # A more precise way would be rounding to midnight, but 24h from first query is fine.
        pipe.expire(key, 86400, nx=True)
        
        await pipe.execute()
        await r.close()
        
    except Exception as e:
        logger.error("Error incrementing token usage for user %s: %s", user_id, e)

async def check_trip_limit(user_id: str) -> None:
    """
    Check if a free user has reached their 3-trip limit.
    Raises 403 HTTPException if the limit is exceeded.
    """
    from app.db.mongo import users_collection, trips_collection
    
    users = users_collection()
    user = await users.find_one({"firebase_id": user_id})
    if not user:
        return
        
    tier = user.get("subscription_tier", "free")
    if tier == "free":
        trips = trips_collection()
        # Count all trips for this user (both skeletal drafts and actual saved trips)
        count = await trips.count_documents({"user_id": user_id})
        if count >= 3:
            raise HTTPException(
                status_code=403,
                detail="Free tier limit reached (3 trips). Please upgrade your plan to continue planning more trips."
            )
