"""
Watchout Backend - Chat Routes
Handles real-time streaming chat via the Hybrid MCP Orchestrator.
"""
import json
import asyncio
from typing import Dict, Any, AsyncGenerator
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Body, Request, BackgroundTasks, Response
from fastapi.responses import StreamingResponse

from app.core.rate_limiter import limiter, RateLimits
from app.core.firebase_auth import verify_firebase_token
from app.db.mongo import get_database
from app.models.chat import ChatRequest, ChatResponse
from app.core.token_limiter import current_user_id, check_trip_limit
from app.prompts import build_trip_title_prompt

router = APIRouter()


def _get_orchestrator_or_503():
    """Lazy-load orchestrator so MCP import issues don't crash entire app startup."""
    try:
        from app.mcp.orchestrator import get_orchestrator
        return get_orchestrator()
    except Exception as exc:
        logger.error("MCP orchestrator unavailable: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="Trip planning service is temporarily unavailable",
        )


async def _generate_trip_title(itinerary: dict, preferences: dict) -> str:
    """Generate a creative, descriptive trip title using Groq LLM.

    Examples:
      "🕉️ Spiritual Sanctuaries of Maharashtra — 10-Day Odyssey"
      "💑 Romantic Rendezvous in Goa — 5 Days of Bliss"
      "🏕️  Wilderness & Waterfalls: Kerala Adventure (7 Days)"
    Falls back to a template if Groq is unreachable.
    """
    cities = itinerary.get("cities", [])
    num_days = itinerary.get("num_days", "")
    vibe = (
        preferences.get("travel_style")
        or preferences.get("vibe")
        or preferences.get("mood")
        or ""
    )
    city_str = " → ".join(cities) if cities else "India"

    # Template fallback by travel style
    style_lower = (vibe or "").lower()
    if "spirit" in style_lower or "pilgrim" in style_lower or "temple" in style_lower:
        fallback = f"🕉️ Sacred Journey through {city_str} — {num_days} Days"
    elif "romantic" in style_lower or "honeymoon" in style_lower or "couple" in style_lower:
        fallback = f"💑 Romantic Escape to {city_str} — {num_days} Days"
    elif "adventure" in style_lower or "trek" in style_lower or "hike" in style_lower:
        fallback = f"🏕️ {num_days}-Day Adventure in {city_str}"
    elif "budget" in style_lower or "backpack" in style_lower:
        fallback = f"🎒 Backpacker's Guide to {city_str} — {num_days} Days"
    elif "luxury" in style_lower or "premium" in style_lower:
        fallback = f"✨ Luxury Escape to {city_str} — {num_days} Days"
    elif "family" in style_lower:
        fallback = f"👨‍👩‍👧 Family Fun in {city_str} — {num_days} Days"
    else:
        fallback = f"{city_str} — {num_days}-Day Exploration"

    try:
        from groq import AsyncGroq
        from app.core.config import settings
        groq = AsyncGroq(api_key=settings.groq_api_key)
        prompt = build_trip_title_prompt(num_days=num_days, city_str=city_str, vibe=vibe)
        resp = await groq.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=40,
            temperature=0.85,
        )
        title = resp.choices[0].message.content.strip().strip('"').strip("'")
        if title and len(title) <= 80:
            return title
    except Exception as exc:
        logger.warning("AI title generation failed, using template: %s", exc)

    return fallback




@router.post("/stream")
@limiter.limit("10/minute")
async def stream_chat(
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    chat_request: ChatRequest = Body(...),
    user_payload: Dict[str, Any] = Depends(verify_firebase_token)
):
    """
    Stream chat response from the Supervisor Agent directly.
    No Redis/worker required — supervisor runs inline in this coroutine.
    """
    user_id = user_payload.get("uid")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user")

    # Set contextvar for token-capping
    current_user_id.set(user_id)

    # ── 1. Load trip context + conversation history ──────────────────────────
    db = await get_database()
    trip_data: Dict[str, Any] = {}
    history = []

    if chat_request.trip_id:
        trip = await db.trips.find_one(
            {"trip_id": chat_request.trip_id, "user_id": user_id}
        )
        if trip:
            trip_data = dict(trip)
            trip_data["preferences"] = trip.get("preferences", {})
            # Restore the state machine phase from DB so context survives across sessions
            trip_data["trip_state"] = trip.get("trip_state", "gathering")

        trip_data["timezone_id"] = request.headers.get("x-timezone-id", "UTC")
        trip_data["timezone_offset"] = request.headers.get("x-timezone-offset", "0")

        # Load the 50 most recent messages (oldest-first for LLM context)
        cursor = db.messages.find(
            {"trip_id": chat_request.trip_id, "user_id": user_id}
        ).sort("created_at", -1).limit(50)
        history = await cursor.to_list(length=50)
        history.reverse()

        # ── Touch last_accessed_at to reset 90-day TTL clock ──────────────
        if history:
            await db.messages.update_many(
                {"trip_id": chat_request.trip_id, "user_id": user_id},
                {"$set": {"last_accessed_at": datetime.now(timezone.utc)}}
            )
    else:
        # Enforce free-tier trip limit
        await check_trip_limit(user_id)

        import uuid
        chat_request.trip_id = str(uuid.uuid4())

        await db.trips.insert_one({
            "trip_id": chat_request.trip_id,
            "user_id": user_id,
            "title": "New Conversation",
            "status": "draft",
            "is_trip": False,
            "trip_state": "gathering",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "preferences": {},
            "timezone_id": request.headers.get("x-timezone-id", "UTC"),
            "timezone_offset": request.headers.get("x-timezone-offset", "0"),
        })

    # ── 2. Merge profile preferences from the frontend ───────────────────────
    # The frontend sends trip_context.preferences built from the user's profile
    # (budget, mood, travel style, food preferences, etc.).  We merge them so
    # the orchestrator never re-asks what was answered during onboarding.
    if chat_request.trip_context:
        incoming_prefs = chat_request.trip_context.get("preferences") or {}
        existing_prefs = trip_data.get("preferences") or {}
        # Existing trip-level prefs are more specific → they win on conflict
        trip_data["preferences"] = {**incoming_prefs, **existing_prefs}
        trip_data.setdefault("timezone_id", request.headers.get("x-timezone-id", "UTC"))

    # ── 3. Save the user message immediately ─────────────────────────────────
    # We persist BEFORE streaming so the message is never lost even if the
    # stream fails halfway through.
    now = datetime.now(timezone.utc)
    await db.messages.insert_one({
        "trip_id": chat_request.trip_id,
        "user_id": user_id,
        "role": "user",
        "content": chat_request.message,
        "created_at": now,
        "last_accessed_at": now,
    })

    # Auto-set trip title from the first user message (replaces "New Conversation")
    is_first_message = len(history) == 0
    if is_first_message:
        auto_title = chat_request.message[:60].strip()
        if len(chat_request.message) > 60:
            auto_title += "…"
        background_tasks.add_task(
            lambda t=chat_request.trip_id, uid=user_id, title=auto_title: (
                db.trips.update_one(
                    {"trip_id": t, "user_id": uid, "title": "New Conversation"},
                    {"$set": {"title": title, "updated_at": datetime.now(timezone.utc)}}
                )
            )
        )

    # ── 4. Build streaming response ──────────────────────────────────────────

    async def _heartbeat(interval: float = 15.0) -> AsyncGenerator[str, None]:
        """Emit SSE comment lines to keep long-lived connections alive."""
        while True:
            await asyncio.sleep(interval)
            yield ": heartbeat\n\n"

    async def event_generator() -> AsyncGenerator[str, None]:
        """Stream events from the MCP Orchestrator."""
        collected_preferences: Dict[str, Any] = {}
        itinerary_data: Dict[str, Any] | None = None
        trip_state: str | None = None
        assistant_tokens: list[str] = []   # accumulate for persistence

        try:
            orchestrator = _get_orchestrator_or_503()
            async for event in orchestrator.process(
                user_id=user_id,
                message=chat_request.message,
                trip_context=trip_data,
                conversation_history=history,
            ):
                # ── Collect assistant response tokens ─────────────────────
                if event.get("type") == "token" and event.get("content"):
                    assistant_tokens.append(event["content"])

                # ── Persist preferences IMMEDIATELY (avoids context loss) ──
                if event.get("type") == "data":
                    dt = event.get("data_type")
                    if dt == "preferences" and event.get("data"):
                        collected_preferences = event["data"]
                        try:
                            existing_doc = await db.trips.find_one(
                                {"trip_id": chat_request.trip_id}, {"preferences": 1}
                            ) or {}
                            existing_prefs = existing_doc.get("preferences") or {}
                            merged_prefs = {**existing_prefs, **collected_preferences}
                            await db.trips.update_one(
                                {"trip_id": chat_request.trip_id, "user_id": user_id},
                                {"$set": {
                                    "preferences": merged_prefs,
                                    "updated_at": datetime.now(timezone.utc),
                                }},
                            )
                        except Exception as exc:
                            logger.warning("Preference save failed: %s", exc)
                    elif dt == "trip_state" and event.get("data"):
                        # Persist the phase transition so next turn restores it
                        trip_state = event["data"].get("state")
                        try:
                            await db.trips.update_one(
                                {"trip_id": chat_request.trip_id, "user_id": user_id},
                                {"$set": {
                                    "trip_state": trip_state,
                                    "updated_at": datetime.now(timezone.utc),
                                }},
                            )
                        except Exception as exc:
                            logger.warning("State save failed: %s", exc)
                    elif dt == "itinerary" and event.get("data"):
                        itinerary_data = event["data"]

                # On done: persist itinerary + assistant message in background
                if event.get("type") == "done":
                    event["trip_id"] = chat_request.trip_id
                    final_state = event.get("trip_state") or trip_state
                    full_assistant_response = "".join(assistant_tokens)

                    async def _save_turn(
                        trip_id=chat_request.trip_id,
                        uid=user_id,
                        itin=itinerary_data,
                        state=final_state,
                        assistant_msg=full_assistant_response,
                    ):
                        try:
                            done_now = datetime.now(timezone.utc)
                            # Save assistant message
                            if assistant_msg:
                                await db.messages.insert_one({
                                    "trip_id": trip_id,
                                    "user_id": uid,
                                    "role": "assistant",
                                    "content": assistant_msg,
                                    "created_at": done_now,
                                    "last_accessed_at": done_now,
                                })

                            # Save itinerary to trip document
                            if itin:
                                fields = {
                                    "itinerary": itin,
                                    "is_trip": True,
                                    "status": "planned",
                                    "updated_at": done_now,
                                }
                                if state:
                                    fields["trip_state"] = state

                                # ── Generate creative AI title ──────────────
                                fields["title"] = await _generate_trip_title(itin, trip_data.get("preferences", {}))

                                await db.trips.update_one(
                                    {"trip_id": trip_id, "user_id": uid},
                                    {"$set": fields},
                                )

                            else:
                                # Still update timestamp even without itinerary
                                await db.trips.update_one(
                                    {"trip_id": trip_id, "user_id": uid},
                                    {"$set": {"updated_at": done_now}},
                                )
                        except Exception as exc:
                            logger.warning("Turn save failed: %s", exc)

                    background_tasks.add_task(_save_turn)

                yield f"data: {json.dumps(event)}\n\n"

                if await request.is_disconnected():
                    break

        except asyncio.CancelledError:
            yield f"data: {json.dumps({'type': 'cancelled', 'message': 'Request cancelled.'})}\n\n"
        except Exception as e:
            logger.error(
                "Orchestrator stream error for user %s: %s", user_id, e, exc_info=True
            )
            yield f"data: {json.dumps({'type': 'error', 'error': str(e) or repr(e)})}\n\n"


    async def merged_generator() -> AsyncGenerator[str, None]:
        """Interleave SSE events with periodic heartbeat comments."""
        hb_iter = _heartbeat().__aiter__()
        ev_iter = event_generator().__aiter__()

        ev_exhausted = False
        pending_hb: asyncio.Task | None = None
        pending_ev: asyncio.Task | None = None

        try:
            while not ev_exhausted:
                if pending_hb is None:
                    pending_hb = asyncio.ensure_future(hb_iter.__anext__())
                if pending_ev is None:
                    pending_ev = asyncio.ensure_future(ev_iter.__anext__())

                done, _ = await asyncio.wait(
                    {pending_hb, pending_ev}, return_when=asyncio.FIRST_COMPLETED
                )

                if pending_ev in done:
                    try:
                        yield pending_ev.result()
                    except StopAsyncIteration:
                        ev_exhausted = True
                    pending_ev = None

                if pending_hb in done:
                    if not ev_exhausted:
                        try:
                            yield pending_hb.result()
                        except StopAsyncIteration:
                            pass
                    pending_hb = None
        finally:
            for t in [pending_hb, pending_ev]:
                if t and not t.done():
                    t.cancel()

    return StreamingResponse(merged_generator(), media_type="text/event-stream")


@router.get("/conversations")
async def list_conversations(
    user_payload: Dict[str, Any] = Depends(verify_firebase_token)
):
    """
    List all chat conversations (Trips) for the user.
    Returns list of conversations with their latest message.
    """
    user_id = user_payload.get("uid")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user")

    db = await get_database()

    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$sort": {"updated_at": -1}},
        {"$limit": 50},
        {
            "$lookup": {
                "from": "messages",
                "let": {"tid": "$trip_id"},
                "pipeline": [
                    {"$match": {"$expr": {"$and": [
                        {"$eq": ["$trip_id", "$$tid"]},
                        {"$eq": ["$user_id", user_id]},
                    ]}}},
                    {"$sort": {"created_at": -1}},
                    {"$limit": 1},
                    {"$project": {"_id": 0, "role": 1, "content": 1, "created_at": 1}},
                ],
                "as": "last_message",
            }
        },
        {
            "$project": {
                "_id": {"$toString": "$_id"},
                "trip_id": 1,
                "title": 1,
                "is_trip": 1,
                "created_at": 1,
                "updated_at": 1,
                "last_message": {"$arrayElemAt": ["$last_message", 0]},
            }
        },
    ]

    conversations = await db.trips.aggregate(pipeline).to_list(length=50)
    return conversations


@router.get("/conversations/{trip_id}/messages")
async def get_trip_messages(
    trip_id: str,
    user_payload: Dict[str, Any] = Depends(verify_firebase_token)
):
    """Get all messages for a specific conversation/trip."""
    user_id = user_payload.get("uid")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user")

    db = await get_database()

    trip = await db.trips.find_one({"trip_id": trip_id, "user_id": user_id})
    if not trip:
        raise HTTPException(status_code=404, detail="Conversation not found")

    cursor = db.messages.find(
        {"trip_id": trip_id, "user_id": user_id}
    ).sort("created_at", 1)

    messages = await cursor.to_list(length=1000)
    for msg in messages:
        msg["_id"] = str(msg["_id"])
    return messages


@router.delete("/conversations/{trip_id}")
async def delete_conversation(
    trip_id: str,
    user_payload: Dict[str, Any] = Depends(verify_firebase_token)
):
    """Delete a conversation and its messages."""
    user_id = user_payload.get("uid")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user")

    db = await get_database()

    try:
        from bson import ObjectId
        query_conditions = [{"trip_id": trip_id}, {"_id": trip_id}]
        try:
            query_conditions.append({"_id": ObjectId(trip_id)})
        except Exception:
            pass
            
        query = {"$or": query_conditions, "user_id": user_id}
    except Exception:
        query = {"trip_id": trip_id, "user_id": user_id}

    trip = await db.trips.find_one(query)
    if not trip:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await db.trips.delete_one({"_id": trip["_id"]})
    await db.messages.delete_many({"trip_id": trip.get("trip_id") or str(trip["_id"])})
    return {"status": "deleted"}


@router.delete("/conversations/{trip_id}/messages/{message_id}")
async def delete_message(
    trip_id: str,
    message_id: str,
    user_payload: Dict[str, Any] = Depends(verify_firebase_token)
):
    """Delete a single message from a conversation."""
    from bson import ObjectId
    user_id = user_payload.get("uid")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user")

    db = await get_database()

    # Verify trip ownership (IDOR guard)
    trip = await db.trips.find_one({"trip_id": trip_id, "user_id": user_id})
    if not trip:
        raise HTTPException(status_code=404, detail="Conversation not found")

    try:
        result = await db.messages.delete_one({
            "_id": ObjectId(message_id),
            "trip_id": trip_id,
            "user_id": user_id,
        })
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid message ID")

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Message not found")

    return {"status": "deleted"}


@router.patch("/conversations/{trip_id}/messages/{message_id}")
async def edit_message(
    trip_id: str,
    message_id: str,
    body: Dict[str, Any] = Body(...),
    user_payload: Dict[str, Any] = Depends(verify_firebase_token)
):
    """Edit the content of a user message."""
    from bson import ObjectId
    user_id = user_payload.get("uid")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user")

    new_content = (body.get("content") or "").strip()
    if not new_content:
        raise HTTPException(status_code=400, detail="Content cannot be empty")

    db = await get_database()

    # Verify trip ownership (IDOR guard)
    trip = await db.trips.find_one({"trip_id": trip_id, "user_id": user_id})
    if not trip:
        raise HTTPException(status_code=404, detail="Conversation not found")

    try:
        result = await db.messages.update_one(
            {
                "_id": ObjectId(message_id),
                "trip_id": trip_id,
                "user_id": user_id,
                "role": "user",   # only user messages can be edited
            },
            {"$set": {
                "content": new_content,
                "edited_at": datetime.now(timezone.utc),
            }}
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid message ID")

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Message not found or cannot be edited")

    return {"status": "updated", "content": new_content}



@router.post("/cancel")
async def cancel_chat(
    user_payload: Dict[str, Any] = Depends(verify_firebase_token)
):
    """Explicitly cancel any active generation for this user."""
    user_id = user_payload.get("uid")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user")

    orchestrator = _get_orchestrator_or_503()
    cancelled = await orchestrator.cancel_user_task(user_id)
    return {"status": "cancelled", "success": cancelled}


@router.post("/conversations/{trip_id}/save-as-trip")
async def save_as_trip(
    trip_id: str,
    user_payload: Dict[str, Any] = Depends(verify_firebase_token)
):
    """
    Promote a chat conversation to a saved trip.
    Sets is_trip=True so it shows up on the Trips page.
    """
    user_id = user_payload.get("uid")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user")

    db = await get_database()

    result = await db.trips.update_one(
        {"trip_id": trip_id, "user_id": user_id},
        {"$set": {"is_trip": True, "updated_at": datetime.now(timezone.utc)}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {"status": "saved", "trip_id": trip_id}


@router.post("/conversations/{trip_id}/share")
async def share_conversation(
    request: Request,
    trip_id: str,
    user_payload: Dict[str, Any] = Depends(verify_firebase_token)
):
    """Share a conversation — generates a unique sharing URL."""
    user_id = user_payload.get("uid")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user")

    db = await get_database()

    trip = await db.trips.find_one({"trip_id": trip_id, "user_id": user_id})
    if not trip:
        raise HTTPException(status_code=404, detail="Conversation not found")

    sharing_id = trip.get("sharing_id")
    if not sharing_id:
        import uuid
        import base64
        sharing_id = base64.urlsafe_b64encode(uuid.uuid4().bytes).decode("utf-8").rstrip("=")

        result = await db.trips.update_one(
            {"trip_id": trip_id, "user_id": user_id},
            {"$set": {
                "is_public": True,
                "sharing_id": sharing_id,
                "updated_at": datetime.now(timezone.utc),
            }}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Conversation not found")

    from app.core.config import settings
    base_url = settings.frontend_url or "http://localhost:3000"
    sharing_url = f"{base_url}/shared/{sharing_id}"

    return {
        "sharing_url": sharing_url,
        "sharing_id": sharing_id,
        "status": "shared",
        "trip_id": trip_id,
    }
