"""
Watchout Backend - Chat Routes with SSE Streaming
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional
import json
import asyncio
import time  # For heartbeat tracking
from datetime import datetime
import uuid

from app.core.firebase_auth import verify_firebase_token
from app.models.memory import ChatRequest, ChatMessage, MessageRole
from app.db.mongo import conversations_collection, trips_collection
from app.agents.supervisor import SupervisorAgent
from app.services.conversation_manager import ConversationManager
from app.services.itinerary_parser import itinerary_parser
from app.core.rate_limiter import limiter, RateLimits

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/stream")
@limiter.limit(RateLimits.CHAT_STREAM)
async def stream_chat(
    request: Request,
    chat_request: ChatRequest,
    token_data: dict = Depends(verify_firebase_token)
):
    """Stream chat response using Server-Sent Events."""
    
    # === SECURITY: Input Safety Check ===
    from app.agents.reviewer import ReviewerAgent
    reviewer = ReviewerAgent()
    
    safety_check = await reviewer.review_input(chat_request.message)
    
    if safety_check["recommended_action"] == "block":
        return JSONResponse(
            status_code=400,
            content={
                "error": "Message blocked for safety reasons",
                "issues": safety_check["issues"],
                "severity": safety_check["severity"],
                "message": "Your message appears to contain unsafe content. Please rephrase and try again."
            }
        )
    
    # Log warnings but allow processing
    if safety_check["recommended_action"] == "warn":
        print(f"⚠️  Safety warning for user {token_data['uid'][:8]}: {safety_check['issues']}")
    
    # === Continue with normal processing ===
    user_id = token_data["uid"]  # First 8 chars for logging
    
    # Generate trip_id if not provided
    trip_id = chat_request.trip_id or f"trip_{uuid.uuid4().hex[:12]}"
    
    # Store user message for later transactional save
    user_message_content = chat_request.message
    
    # Build comprehensive context with history (include existing messages for context)
    context = await ConversationManager.build_agent_context(
        trip_id=trip_id,
        user_id=user_id,
        current_message=chat_request.message,
        include_history=True,
        history_limit=15
    )
    
    async def event_generator():
        supervisor = SupervisorAgent()
        
        response_parts = []
        data_events = []
        agents_used = []
        
        # Event ID and heartbeat tracking for resilient streaming
        event_id = 0
        last_heartbeat = time.time()
        
        try:
            async for event in supervisor.process_message(
                user_id=user_id,
                message=chat_request.message,
                trip_context=context,
                conversation_history=context.get("conversation_history", [])
            ):
                event_type = event.get("type", "token")
                event_id += 1  # Increment for each event
                
                if event_type == "token":
                    content = event.get("content", "")
                    response_parts.append(content)
                    yield f"id: {event_id}\ndata: {json.dumps({'type': 'token', 'content': content})}\n\n"
                    last_heartbeat = time.time()
                
                elif event_type == "status":
                    agent = event.get("agent", "")
                    if agent and agent not in agents_used:
                        agents_used.append(agent)
                    yield f"id: {event_id}\ndata: {json.dumps({'type': 'status', 'status': event.get('status', ''), 'agent': agent})}\n\n"
                    last_heartbeat = time.time()
                
                elif event_type == "data":
                    data_events.append(event)
                    # Safely serialize data - handle Pydantic models
                    raw_data = event.get("data")
                    try:
                        if hasattr(raw_data, "model_dump"):
                            # Pydantic v2
                            serializable_data = raw_data.model_dump()
                        elif hasattr(raw_data, "dict"):
                            # Pydantic v1
                            serializable_data = raw_data.dict()
                        else:
                            serializable_data = raw_data
                        yield f"id: {event_id}\ndata: {json.dumps({'type': 'data', 'data_type': event.get('data_type'), 'data': serializable_data})}\n\n"
                    except Exception as e:
                        # Fallback - send error for this data event
                        yield f"id: {event_id}\ndata: {json.dumps({'type': 'data', 'data_type': event.get('data_type'), 'data': None, 'error': str(e)})}\n\n"
                    last_heartbeat = time.time()
                    
                    # If preferences were extracted, update trip
                    if event.get("data_type") == "preferences":
                        prefs = event.get("data", {})
                        if prefs and isinstance(prefs, dict):
                            await ConversationManager.update_trip_preferences(
                                trip_id, user_id, prefs
                            )
                
                elif event_type == "tool_start":
                    yield f"id: {event_id}\ndata: {json.dumps({'type': 'tool_start', 'tool': event.get('tool_name')})}\n\n"
                    last_heartbeat = time.time()
                
                elif event_type == "tool_end":
                    yield f"id: {event_id}\ndata: {json.dumps({'type': 'tool_end', 'tool': event.get('tool_name'), 'result': event.get('tool_output')})}\n\n"
                    last_heartbeat = time.time()
                
                elif event_type == "done":
                    # Save user + assistant response atomically with transaction
                    full_response = "".join(response_parts)
                    if full_response.strip():
                        try:
                            await ConversationManager.save_message_pair(
                                trip_id=trip_id,
                                user_id=user_id,
                                user_message=user_message_content,
                                assistant_message=full_response,
                                assistant_metadata={
                                    "agents_used": agents_used,
                                    "is_complete": event.get("is_complete", False)
                                }
                            )
                        except Exception as save_error:
                            print(f"Transaction failed, using fallback: {save_error}")
                            # Fallback to individual saves if transaction fails
                            await ConversationManager.save_message(
                                trip_id=trip_id,
                                user_id=user_id,
                                role="user",
                                content=user_message_content
                            )
                            await ConversationManager.save_message(
                                trip_id=trip_id,
                                user_id=user_id,
                                role="assistant",
                                content=full_response,
                                metadata={
                                    "agents_used": agents_used,
                                    "is_complete": event.get("is_complete", False)
                                }
                            )
                    
                    yield f"id: {event_id}\ndata: {json.dumps({'type': 'done', 'is_complete': event.get('is_complete', False), 'trip_id': trip_id})}\n\n"
                    last_heartbeat = time.time()
                    
                    # 3. Extract structured itinerary data after response is complete
                    try:
                        history = await ConversationManager.get_history(trip_id, user_id, limit=20)
                        itinerary_data = await itinerary_parser.parse_conversation(history)
                        if itinerary_data:
                            event_id += 1
                            yield f"id: {event_id}\ndata: {json.dumps({'type': 'itinerary', 'itinerary': itinerary_data})}\n\n"
                    except Exception as e:
                        print(f"Itinerary extraction error: {e}")
                
                elif event_type == "error":
                    yield f"id: {event_id}\ndata: {json.dumps({'type': 'error', 'error': event.get('error', 'Unknown error')})}\n\n"
                    last_heartbeat = time.time()
                
                # Send heartbeat if no events in 15 seconds (prevents proxy timeouts)
                if time.time() - last_heartbeat > 15:
                    yield ": heartbeat\n\n"  # SSE comment line
                    last_heartbeat = time.time()
                
                await asyncio.sleep(0.01)
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            # Save error response
            await ConversationManager.save_message(
                trip_id=trip_id,
                user_id=user_id,
                role="assistant",
                content=f"I encountered an error: {str(e)}",
                metadata={"error": True}
            )
            event_id += 1
            yield f"id: {event_id}\ndata: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/message")
@limiter.limit(RateLimits.CHAT_MESSAGE)
async def send_message(
    request: Request,
    chat_request: ChatRequest,
    token_data: dict = Depends(verify_firebase_token)
):
    """Send a message and get a non-streaming response."""
    user_id = token_data["uid"]
    
    # Generate trip_id if not provided
    trip_id = chat_request.trip_id or f"trip_{uuid.uuid4().hex[:12]}"
    
    # Save user message
    await ConversationManager.save_message(
        trip_id=trip_id,
        user_id=user_id,
        role="user",
        content=chat_request.message
    )
    
    # Build context with history
    context = await ConversationManager.build_agent_context(
        trip_id=trip_id,
        user_id=user_id,
        current_message=chat_request.message
    )
    
    supervisor = SupervisorAgent()
    
    response_parts = []
    data_results = []
    agents_used = []
    
    async for event in supervisor.process_message(
        user_id=user_id,
        message=chat_request.message,
        trip_context=context,
        conversation_history=context.get("conversation_history", [])
    ):
        if event.get("type") == "token":
            response_parts.append(event.get("content", ""))
        elif event.get("type") == "data":
            data_results.append(event)
            # Update preferences if extracted
            if event.get("data_type") == "preferences":
                prefs = event.get("data", {})
                if prefs:
                    await ConversationManager.update_trip_preferences(
                        trip_id, user_id, prefs
                    )
        elif event.get("type") == "status":
            agent = event.get("agent", "")
            if agent and agent not in agents_used:
                agents_used.append(agent)
    
    full_response = "".join(response_parts)
    
    # Save assistant response
    if full_response.strip():
        await ConversationManager.save_message(
            trip_id=trip_id,
            user_id=user_id,
            role="assistant",
            content=full_response,
            metadata={"agents_used": agents_used}
        )
    
    return {
        "response": full_response,
        "data": data_results,
        "trip_id": trip_id,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/history/{trip_id}")
async def get_history(
    trip_id: str,
    limit: int = 20,
    token_data: dict = Depends(verify_firebase_token)
):
    """Get conversation history for a specific trip."""
    user_id = token_data["uid"]
    
    history = await ConversationManager.get_history(
        trip_id=trip_id,
        user_id=user_id,
        limit=limit
    )
    
    return {"messages": history}


@router.post("/cancel")
async def cancel_stream(
    trip_id: str,
    token_data: dict = Depends(verify_firebase_token)
):
    """Cancel an ongoing streaming response for a trip."""
    user_id = token_data["uid"]
    
    supervisor = SupervisorAgent()
    cancelled = await supervisor.cancel_task(user_id)
    
    return {"cancelled": cancelled, "trip_id": trip_id}


@router.get("/conversations")
async def list_conversations(
    token_data: dict = Depends(verify_firebase_token)
):
    """List all conversations for current user, excluding saved trips."""
    user_id = token_data["uid"]
    convos = conversations_collection()
    
    # Only return conversations NOT saved as trips
    conversations = []
    cursor = convos.find({
        "user_id": user_id,
        "$or": [
            {"saved_as_trip": {"$exists": False}},
            {"saved_as_trip": False}
        ]
    }).sort("updated_at", -1).limit(50)
    
    async for conv in cursor:
        # Generate title from first user message if not set
        title = conv.get("title")
        if not title and conv.get("messages"):
            first_msg = next((m for m in conv["messages"] if m.get("role") == "user"), None)
            if first_msg:
                content = first_msg.get("content", "")
                title = content[:50] + "..." if len(content) > 50 else content
        
        conversations.append({
            "_id": str(conv["_id"]) if "_id" in conv else conv["trip_id"],
            "trip_id": conv["trip_id"],
            "title": title or "Untitled Chat",
            "created_at": conv.get("created_at").isoformat() if conv.get("created_at") else None,
            "updated_at": conv.get("updated_at").isoformat() if conv.get("updated_at") else None,
            "message_count": len(conv.get("messages", []))
        })
    
    return conversations


@router.post("/conversations/{trip_id}/save-as-trip")
async def save_conversation_as_trip(
    trip_id: str,
    token_data: dict = Depends(verify_firebase_token)
):
    """Save a conversation as a trip and mark it."""
    user_id = token_data["uid"]
    convos = conversations_collection()
    trips = trips_collection()
    
    # Get the conversation
    conversation = await convos.find_one({"trip_id": trip_id, "user_id": user_id})
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Check if already saved as trip
    if conversation.get("saved_as_trip"):
        raise HTTPException(status_code=400, detail="Conversation already saved as trip")
    
    # Extract title from messages
    title = conversation.get("title")
    if not title and conversation.get("messages"):
        first_msg = next((m for m in conversation["messages"] if m.get("role") == "user"), None)
        if first_msg:
            content = first_msg.get("content", "")
            title = content[:50] + "..." if len(content) > 50 else content
    
    # Create trip from conversation (check if trip already exists)
    existing_trip = await trips.find_one({"_id": trip_id, "user_id": user_id})
    
    if not existing_trip:
        # Create new trip
        trip_doc = {
            "_id": trip_id,
            "user_id": user_id,
            "title": title or "Saved Chat",
            "cities": [],
            "num_days": 5,
            "num_travelers": 1,
            "status": "planning",
            "is_public": False,
            "created_at": conversation.get("created_at", datetime.utcnow()),
            "updated_at": datetime.utcnow()
        }
        await trips.insert_one(trip_doc)
    
    # Mark conversation as saved_as_trip
    await convos.update_one(
        {"trip_id": trip_id, "user_id": user_id},
        {"$set": {"saved_as_trip": True, "updated_at": datetime.utcnow()}}
    )
    
    return {"trip_id": trip_id, "status": "saved_as_trip"}


@router.delete("/conversations/{trip_id}")
async def delete_conversation(
    trip_id: str,
    token_data: dict = Depends(verify_firebase_token)
):
    """Delete a conversation that hasn't been saved as trip."""
    user_id = token_data["uid"]
    convos = conversations_collection()
    
    # Check if conversation exists and is not saved as trip
    conversation = await convos.find_one({"trip_id": trip_id, "user_id": user_id})
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conversation.get("saved_as_trip"):
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete conversation that has been saved as a trip. Delete the trip instead."
        )
    
    # Delete the conversation
    result = await convos.delete_one({"trip_id": trip_id, "user_id": user_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {"status": "deleted"}


@router.post("/conversations/{trip_id}/share")
async def share_conversation(
    trip_id: str,
    token_data: dict = Depends(verify_firebase_token)
):
    """Generate a shareable link for a conversation."""
    user_id = token_data["uid"]
    convos = conversations_collection()
    
    # Get the conversation
    conversation = await convos.find_one({"trip_id": trip_id, "user_id": user_id})
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Generate or get sharing_id
    sharing_id = conversation.get("sharing_id")
    if not sharing_id:
        sharing_id = uuid.uuid4().hex
        await convos.update_one(
            {"trip_id": trip_id, "user_id": user_id},
            {
                "$set": {
                    "sharing_id": sharing_id,
                    "is_public": True,
                    "updated_at": datetime.utcnow()
                }
            }
        )
    
    return {"sharing_id": sharing_id, "url": f"/shared/chat/{sharing_id}"}


@router.delete("/history/{trip_id}")
async def clear_chat_history(
    trip_id: str,
    token_data: dict = Depends(verify_firebase_token)
):
    """Clear chat history for a trip."""
    user_id = token_data["uid"]
    
    success = await ConversationManager.clear_conversation(
        trip_id=trip_id,
        user_id=user_id
    )
    
    return {"status": "cleared" if success else "not_found"}
