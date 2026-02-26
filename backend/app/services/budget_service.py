"""
Watchout Backend - Per-session & Daily Token Budget Service (AP2)

Uses Redis atomic INCRBY + EXPIRE to enforce:
  - Per-session cap: 100,000 tokens per trip conversation
  - Per-day cap:     200,000 tokens per user per calendar day

Keys are structured as:
  tokens:session:<user_id>:<trip_id>   (expires in 24 h)
  tokens:daily:<user_id>               (expires in 24 h)

Usage::

    from app.services.budget_service import check_and_consume_tokens
    from app.db.redis_client import get_redis

    allowed = await check_and_consume_tokens(
        redis=await get_redis(),
        user_id=user_id,
        trip_id=trip_id,
        tokens=estimated_tokens,
    )
    if not allowed:
        raise HTTPException(status_code=429, detail="token_budget_exceeded")
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Guard caps
# ──────────────────────────────────────────────
MAX_SESSION_TOKENS: int = 100_000   # per trip conversation
MAX_DAILY_TOKENS: int = 200_000     # per user per day
_KEY_TTL: int = 86_400              # 24 hours in seconds


async def check_and_consume_tokens(
    redis,                 # redis.asyncio.Redis
    user_id: str,
    trip_id: str,
    tokens: int,
    *,
    dry_run: bool = False,
) -> bool:
    """
    Atomically check and consume ``tokens`` from both the session and daily
    budgets.

    Args:
        redis:    An async Redis client instance.
        user_id:  Firebase UID of the authenticated user.
        trip_id:  The trip/conversation ID for the session cap.
        tokens:   Estimated number of tokens the upcoming LLM call will use.
        dry_run:  If True, check limits without incrementing counters.

    Returns:
        ``True``  if the request is within budget (tokens consumed if not dry_run).
        ``False`` if either limit would be exceeded (request should be blocked).
    """
    session_key = f"tokens:session:{user_id}:{trip_id}"
    daily_key = f"tokens:daily:{user_id}"

    if dry_run:
        session_total = int(await redis.get(session_key) or 0)
        daily_total = int(await redis.get(daily_key) or 0)
        within_session = (session_total + tokens) <= MAX_SESSION_TOKENS
        within_daily = (daily_total + tokens) <= MAX_DAILY_TOKENS
        return within_session and within_daily

    # Atomic pipeline: INCRBY + EXPIRE in a single round-trip
    async with redis.pipeline(transaction=True) as pipe:
        pipe.incrby(session_key, tokens)
        pipe.expire(session_key, _KEY_TTL)
        pipe.incrby(daily_key, tokens)
        pipe.expire(daily_key, _KEY_TTL)
        results = await pipe.execute()

    new_session_total: int = results[0]
    new_daily_total: int = results[2]

    within_session = new_session_total <= MAX_SESSION_TOKENS
    within_daily = new_daily_total <= MAX_DAILY_TOKENS

    if not within_session:
        logger.warning(
            "Session token budget exceeded: user=%s trip=%s total=%d",
            user_id, trip_id, new_session_total,
        )
    if not within_daily:
        logger.warning(
            "Daily token budget exceeded: user=%s total=%d",
            user_id, new_daily_total,
        )

    return within_session and within_daily


async def get_budget_status(
    redis,
    user_id: str,
    trip_id: str,
) -> dict:
    """
    Return current usage without consuming any tokens. Useful for a
    ``GET /budget`` endpoint or admin tooling.
    """
    session_key = f"tokens:session:{user_id}:{trip_id}"
    daily_key = f"tokens:daily:{user_id}"

    session_used = int(await redis.get(session_key) or 0)
    daily_used = int(await redis.get(daily_key) or 0)

    return {
        "session": {
            "used": session_used,
            "limit": MAX_SESSION_TOKENS,
            "remaining": max(0, MAX_SESSION_TOKENS - session_used),
        },
        "daily": {
            "used": daily_used,
            "limit": MAX_DAILY_TOKENS,
            "remaining": max(0, MAX_DAILY_TOKENS - daily_used),
        },
    }
