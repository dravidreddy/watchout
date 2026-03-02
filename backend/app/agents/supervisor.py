"""
Watchout Backend - Supervisor Agent (LLM-Powered Orchestrator)

Production-grade Supervisor:
- True cancellation (asyncio.Task cancel)
- Strict orchestration planning JSON
- Parallel agent execution with dependency control
- Streaming events: status, token, tool_start/tool_end, data, done, cancelled
- Friendly travel-agent personality
"""

from __future__ import annotations

from typing import Dict, Any, Optional, AsyncGenerator, List, Tuple
import asyncio
import json
import logging
import time
import uuid as _uuid_mod

logger = logging.getLogger(__name__)

from app.agents.base import BaseAgent
from app.agents.clarification import ClarificationAgent
from app.agents.itinerary import ItineraryAgent
from app.agents.route import RouteAgent
from app.agents.transportation import TransportationAgent
from app.agents.stay import StayAgent
from app.agents.food import FoodAgent
from app.agents.weather import WeatherAgent
from app.db.vector_store import VectorStore


ALLOWED_AGENTS = {
    "clarification",
    "itinerary",
    "route",
    "transportation",
    "stay",
    "food",
    "weather",
}

CRITICAL_FIELDS = [
    "origin_city",
    "destinations_or_region",
    "duration_days",
    "num_travelers",
    "budget_range",
    "pace",
    "travel_vibe",
    "travel_style",
]


class SupervisorAgent(BaseAgent):
    """
    LLM-powered orchestrator for travel planning.

    Responsibilities:
    - Decide next action (smalltalk / clarify / plan / refine)
    - Execute relevant specialist agents (parallel when safe)
    - Stream a curated final response like a human travel agent
    - Emit structured data for frontend rendering
    - Cancel old tasks safely per user
    """

    def __init__(self):
        super().__init__(
            name="Watchout Supervisor",
            description=(
                "You are Watchout, the lead Indian travel agent. "
                "You orchestrate specialists and speak warmly to users."
            ),
            model_type="main",
        )

        self.agents = {
            "clarification": ClarificationAgent(),
            "itinerary": ItineraryAgent(),
            "route": RouteAgent(),
            "transportation": TransportationAgent(),
            "stay": StayAgent(),
            "food": FoodAgent(),
            "weather": WeatherAgent(),
        }

        self.vector_store = VectorStore()

        # Per-user active request cancellation (local asyncio task tracking)
        self._user_lock: Dict[str, asyncio.Lock] = {}
        self._active_task: Dict[str, asyncio.Task] = {}
        self._active_cancel_event: Dict[str, asyncio.Event] = {}
        self._active_request_id: Dict[str, str] = {}

        # AR3: lazy Redis client (shared cancellation across instances)
        self._redis = None

    # ---------------------------------------------------------------------
    # Prompt injection defence
    # ---------------------------------------------------------------------
    _INJECTION_PATTERNS = [
        "ignore previous instructions",
        "ignore all instructions",
        "ignore your instructions",
        "forget your instructions",
        "you are now",
        "you must now",
        "act as",
        "pretend you are",
        "system prompt",
        "developer mode",
        "jailbreak",
        "[inst]", "[/inst]",
        "</system>", "<system>",
        "</s>",
        "disregard all",
        "override instructions",
    ]

    def _sanitize_for_prompt(self, text: str, max_len: int = 2000) -> str:
        """
        Sanitize user input before embedding it in an LLM prompt.
        - Truncates to max_len to limit context injection
        - Replaces known prompt injection patterns with [filtered]
        Does NOT alter semantics for genuine travel queries.
        """
        sanitized = text[:max_len]
        lower = sanitized.lower()
        for pattern in self._INJECTION_PATTERNS:
            if pattern in lower:
                # Case-insensitive replace
                import re as _re
                sanitized = _re.sub(
                    _re.escape(pattern),
                    "[filtered]",
                    sanitized,
                    flags=_re.IGNORECASE,
                )
                lower = sanitized.lower()
        return sanitized

    # -------------------------------------------------------------------------
    # AR3: Redis-backed cross-instance cancellation
    # -------------------------------------------------------------------------
    async def _get_redis(self):
        """Lazy-init shared Redis client for cross-instance cancel signals."""
        if self._redis is not None:
            return self._redis
        try:
            import redis.asyncio as aioredis  # type: ignore
            from app.core.config import settings
            url = settings.redis_url or "redis://localhost:6379"
            self._redis = aioredis.from_url(url, decode_responses=True)
            return self._redis
        except Exception as exc:
            logger.warning("Redis unavailable — falling back to local cancel events: %s", exc)
            return None

    async def _set_cancel_signal(self, user_id: str, request_id: str) -> None:
        """Write a cancel signal to Redis (TTL 60 s)."""
        r = await self._get_redis()
        if r:
            try:
                await r.setex(f"cancel:{user_id}:{request_id}", 60, "1")
            except Exception:
                pass  # Redis write failure is non-fatal

    async def _is_redis_cancelled(self, user_id: str, request_id: str) -> bool:
        """Check Redis for a cancel signal for this specific request."""
        r = await self._get_redis()
        if not r:
            return False
        try:
            return bool(await r.exists(f"cancel:{user_id}:{request_id}"))
        except Exception:
            return False

    async def _clear_cancel_signal(self, user_id: str, request_id: str) -> None:
        """Remove the cancel Redis key after the stream is done."""
        r = await self._get_redis()
        if r:
            try:
                await r.delete(f"cancel:{user_id}:{request_id}")
            except Exception:
                pass

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    async def process_message(
        self,
        user_id: str,
        message: str,
        trip_context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Entry point used by FastAPI streaming endpoint.

        Yields events:
        - status
        - token
        - tool_start/tool_end
        - data
        - done
        - cancelled
        """

        if user_id not in self._user_lock:
            self._user_lock[user_id] = asyncio.Lock()

        async with self._user_lock[user_id]:
            # Cancel any previous active task
            if user_id in self._active_task:
                old_task = self._active_task[user_id]
                cancel_event = self._active_cancel_event.get(user_id)
                if cancel_event:
                    cancel_event.set()

                # AR3: also signal via Redis so other instances cancel their streams
                old_req_id = self._active_request_id.get(user_id)
                if old_req_id:
                    await self._set_cancel_signal(user_id, old_req_id)

                if not old_task.done():
                    old_task.cancel()

                yield {
                    "type": "status",
                    "agent": "Supervisor",
                    "status": "I got your new message — stopping the previous request ✋",
                }

            # Create new cancel event and request ID
            cancel_event = asyncio.Event()
            request_id = _uuid_mod.uuid4().hex   # AR3: unique per-request ID
            self._active_cancel_event[user_id] = cancel_event
            self._active_request_id[user_id] = request_id

            # We run internal logic inside a task so it can be cancelled
            task = asyncio.create_task(
                self._run_streaming_pipeline(
                    user_id=user_id,
                    request_id=request_id,
                    message=message,
                    trip_context=trip_context or {},
                    conversation_history=conversation_history or [],
                    cancel_event=cancel_event,
                )
            )
            self._active_task[user_id] = task

        # Stream events from the task
        try:
            async for event in await task:
                yield event
        except asyncio.CancelledError:
            yield {
                "type": "cancelled",
                "message": "Request cancelled.",
            }
        finally:
            # Cleanup (only if this task is still the active one)
            if self._active_task.get(user_id) is task:
                self._active_task.pop(user_id, None)
                self._active_cancel_event.pop(user_id, None)
                self._active_request_id.pop(user_id, None)
                self._user_lock.pop(user_id, None)
            # AR3: clean up the Redis cancel key
            await self._clear_cancel_signal(user_id, request_id)

    # ---------------------------------------------------------------------
    # Internal streaming pipeline
    # ---------------------------------------------------------------------
    async def _run_streaming_pipeline(
        self,
        user_id: str,
        request_id: str,        # AR3: needed for Redis cancel key lookup
        message: str,
        trip_context: Dict[str, Any],
        conversation_history: List[Dict[str, Any]],
        cancel_event: asyncio.Event,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        This is a generator factory.
        We return an async generator so the outer task can stream.
        """

        async def _is_cancelled() -> bool:
            """AR3: Check both local event and Redis signal."""
            if cancel_event.is_set():
                return True
            return await self._is_redis_cancelled(user_id, request_id)

        async def gen() -> AsyncGenerator[Dict[str, Any], None]:
            preferences = trip_context.get("preferences", {}) or {}

            # Phase 3: Merge profile-level preferences so the AI never re-asks
            # what was already answered during onboarding / mood selection.
            # Keys populated by the frontend from user.preferences are:
            #   travel_style, budget_range, food_preferences, interests,
            #   current_mood, travel_vibe
            # These are already included in preferences via trip_context, so we
            # just ensure empty values don't overwrite the real ones.
            profile_prefs = {
                k: v for k, v in (trip_context.get("profile", {}) or {}).items()
                if v and k not in preferences
            }
            preferences = {**profile_prefs, **preferences}

            # 1) Memory retrieval
            yield {
                "type": "status",
                "agent": "Memory",
                "status": "Recalling your travel style… 🧠",
            }
            memories = await self._get_relevant_memories(user_id, message)

            if await _is_cancelled():
                yield {"type": "cancelled", "message": "Cancelled."}
                return

            # 2) Orchestration planning (LLM)
            yield {
                "type": "status",
                "agent": "Supervisor",
                "status": "Thinking about the best next step… ✨",
            }
            plan = await self._plan_orchestration(
                message=message,
                preferences=preferences,
                memories=memories,
                conversation_history=conversation_history,
                timezone_id=trip_context.get("timezone_id", "UTC")
            )

            if await _is_cancelled():
                yield {"type": "cancelled", "message": "Cancelled."}
                return

            intent = plan.get("intent", "clarify")
            agents = plan.get("agents", [])
            parallel = bool(plan.get("parallel", False))
            missing_fields = plan.get("missing_fields", [])

            # 3) Smalltalk: respond directly (no agents)
            if intent == "smalltalk":
                async for t in self._stream_smalltalk_response(message, preferences):
                    yield {"type": "token", "content": t}
                yield {"type": "done", "is_complete": True}
                return

            # 4) Clarification: run clarification agent (stream)
            if intent == "clarify" or "clarification" in agents:
                yield {
                    "type": "tool_start",
                    "tool": "clarification",
                }
                yield {
                    "type": "status",
                    "agent": "Clarification",
                    "status": "Quickly understanding your trip… 🧳",
                }

                # Clarification agent should return:
                # {
                #   "assistant_message": "...",
                #   "preferences": {...},
                #   "missing_fields": [...],
                #   "is_complete": bool
                # }
                result = await self.agents["clarification"].run(
                    message,
                    {
                        "preferences": preferences,
                        "memories": memories,
                        "conversation_history": conversation_history,
                        "missing_fields": missing_fields,
                        "timezone_id": trip_context.get("timezone_id", "UTC")
                    },
                )

                yield {"type": "tool_end", "tool": "clarification"}

                assistant_message = result.get("assistant_message") or result.get("response") or ""
                new_preferences = result.get("preferences") or result.get("extracted_preferences") or {}
                is_complete = bool(result.get("is_complete", False))
                new_missing = result.get("missing_fields", [])

                # Update merged preferences
                merged_preferences = {**preferences, **(new_preferences or {})}

                # Stream the clarification message
                async for chunk in self._stream_text(assistant_message):
                    if cancel_event.is_set():
                        yield {"type": "cancelled", "message": "Cancelled."}
                        return
                    yield {"type": "token", "content": chunk}

                # Send structured preferences update
                yield {
                    "type": "data",
                    "data_type": "preferences",
                    "data": merged_preferences,
                }
                yield {
                    "type": "data",
                    "data_type": "missing_fields",
                    "data": new_missing,
                }

                # Phase 4: When all requirements are complete, emit a confirmation
                # card instead of immediately generating the itinerary.
                # The frontend renders a verification card, and the user's next
                # message ("yes" / "looks good" / etc.) triggers intent==plan.
                if is_complete:
                    yield {
                        "type": "data",
                        "data_type": "confirmation_required",
                        "data": merged_preferences,
                    }

                yield {"type": "done", "is_complete": is_complete}
                return

            # 5) Planning pipeline (itinerary first, then parallel)
            # Ensure itinerary runs first if requested (after weather)
            if "itinerary" not in agents:
                agents = ["itinerary"] + agents

            # Remove invalid agents
            agents = [a for a in agents if a in ALLOWED_AGENTS and a != "clarification"]
            
            all_results: Dict[str, Dict[str, Any]] = {}

            # AR8: Run weather before itinerary to provide weather context
            weather_data = None
            if "weather" in agents:
                yield {"type": "status", "agent": "Supervisor", "status": "Checking forecasts for your destinations… ☁️"}
                weather_res = await self._run_agent_with_events(
                    agent_name="weather",
                    message=message,
                    preferences=preferences,
                    memories=memories,
                    conversation_history=conversation_history,
                    cancel_event=cancel_event,
                    timezone_id=trip_context.get("timezone_id", "UTC")
                )
                all_results["weather"] = weather_res
                weather_data = weather_res.get("data")
                agents.remove("weather")

            # Run itinerary first (dependency)
            yield {"type": "status", "agent": "Supervisor", "status": "Building your trip plan… 🗺️"}
            itinerary_result = await self._run_agent_with_events(
                agent_name="itinerary",
                message=message,
                preferences=preferences,
                memories=memories,
                conversation_history=conversation_history,
                cancel_event=cancel_event,
                weather_data=weather_data,
                timezone_id=trip_context.get("timezone_id", "UTC")
            )

            if await _is_cancelled():
                yield {"type": "cancelled", "message": "Cancelled."}
                return

            # Collect structured data
            all_results["itinerary"] = itinerary_result
            itinerary_data = itinerary_result.get("data", {}) or itinerary_result
            
            # AR7: Run Reviewer/Critic Agent on the generated itinerary
            if itinerary_data and not itinerary_result.get("error"):
                yield {"type": "status", "agent": "Reviewer", "status": "Validating itinerary constraints… 🔍"}
                from app.agents.reviewer import ReviewerAgent
                reviewer = ReviewerAgent()
                review_result = await reviewer.review_itinerary(itinerary_data)
                
                if not review_result.get("is_feasible", True):
                    logger.warning("Itinerary failed validation: %s", review_result.get("issues"))
                    # Append warning to itinerary_data so it is surfaced
                    itinerary_data["reviewer_warnings"] = review_result.get("issues", [])
                    # The planner can now weave these warnings in or the UI can show them
                    yield {
                        "type": "status",
                        "agent": "Reviewer",
                        "status": "Found some impractical timings. Adjusting recommendations… ⚠️"
                    }

            # AR5: Track degraded agents so we can alert the user
            degraded_agents = []
            if itinerary_result.get("error"):
                degraded_agents.append("itinerary")

            # Decide dependent agents
            remaining_agents = [a for a in agents if a != "itinerary"]

            # If itinerary has cities/days, we can run other agents
            if remaining_agents:
                if parallel:
                    yield {
                        "type": "status",
                        "agent": "Supervisor",
                        "status": "Now I’ll fetch routes, stays, food & weather in parallel… ⚡",
                    }
                    parallel_results = await self._run_agents_parallel(
                        agent_names=remaining_agents,
                        message=message,
                        preferences=preferences,
                        memories=memories,
                        conversation_history=conversation_history,
                        cancel_event=cancel_event,
                        itinerary_data=itinerary_data,
                        weather_data=weather_data,
                        timezone_id=trip_context.get("timezone_id", "UTC")
                    )
                    all_results.update(parallel_results)
                    # AR5: collect failed parallel agents
                    for a, r in parallel_results.items():
                        if isinstance(r, dict) and r.get("error"):
                            degraded_agents.append(a)
                else:
                    for agent_name in remaining_agents:
                        res = await self._run_agent_with_events(
                            agent_name=agent_name,
                            message=message,
                            preferences=preferences,
                            memories=memories,
                            conversation_history=conversation_history,
                            cancel_event=cancel_event,
                            itinerary_data=itinerary_data,
                            weather_data=weather_data,
                            timezone_id=trip_context.get("timezone_id", "UTC")
                        )
                        all_results[agent_name] = res
                        # AR5: collect failed sequential agents
                        if isinstance(res, dict) and res.get("error"):
                            degraded_agents.append(agent_name)

            if await _is_cancelled():
                yield {"type": "cancelled", "message": "Cancelled."}
                return

            # AR5: Surface partial failures before streaming the woven response
            if degraded_agents:
                logger.warning("Degraded agents in this request: %s", degraded_agents)
                yield {
                    "type": "degraded_service",
                    "agents": degraded_agents,
                    "message": (
                        "Some travel information could not be retrieved "
                        f"({', '.join(degraded_agents)}). "
                        "The response may be incomplete."
                    ),
                }

            # 6) Weave final response (stream)
            yield {"type": "status", "agent": "Supervisor", "status": "Putting everything together… 🧾"}

            agent_responses_text = self._format_agent_outputs_for_weaver(all_results)

            async for token in self._stream_weaved_response(
                user_message=message,
                preferences=preferences,
                conversation_history=conversation_history,
                agent_outputs=agent_responses_text,
                timezone_id=trip_context.get("timezone_id", "UTC")
            ):
                if await _is_cancelled():
                    yield {"type": "cancelled", "message": "Cancelled."}
                    return
                yield {"type": "token", "content": token}

            # 7) Emit structured data per agent (for UI rendering)
            for agent_name, result in all_results.items():
                data = result.get("data") if isinstance(result, dict) else None
                if data:
                    yield {
                        "type": "data",
                        "data_type": agent_name,
                        "data": data,
                    }

            yield {"type": "done", "is_complete": True}

        return gen()

    # ---------------------------------------------------------------------
    # Agent execution helpers
    # ---------------------------------------------------------------------
    async def _run_agent_with_events(
        self,
        agent_name: str,
        message: str,
        preferences: Dict[str, Any],
        memories: List[Dict[str, Any]],
        conversation_history: List[Dict[str, Any]],
        cancel_event: asyncio.Event,
        itinerary_data: Optional[Dict[str, Any]] = None,
        weather_data: Optional[Dict[str, Any]] = None,
        timezone_id: str = "UTC"
    ) -> Dict[str, Any]:
        """
        Runs one agent with tool_start/tool_end events.
        """
        if agent_name not in self.agents:
            return {"response": "", "data": {}, "error": f"Unknown agent: {agent_name}"}

        start = time.time()
        try:
            # Per-agent timeout — prevents a slow / hung agent from blocking the stream forever (AR4)
            result = await asyncio.wait_for(
                self.agents[agent_name].run(
                    message,
                    {
                        "preferences": preferences,
                        "memories": memories,
                        "conversation_history": conversation_history,
                        "itinerary_data": itinerary_data,
                        "weather_data": weather_data,
                        "timezone_id": timezone_id
                    },
                ),
                timeout=30.0,
            )
            elapsed = round(time.time() - start, 2)

            # Normalize output
            return {
                "response": result.get("response", ""),
                "data": result.get("data", result),
                "latency_sec": elapsed,
            }
        except asyncio.TimeoutError:
            logger.error("Agent '%s' timed out after 30s — returning degraded result", agent_name)
            return {"response": "", "data": {}, "error": "agent_timeout"}
        except asyncio.CancelledError:
            return {"response": "", "data": {}, "error": "cancelled"}
        except Exception as e:
            return {"response": "", "data": {}, "error": str(e)}

    async def _run_agents_parallel(
        self,
        agent_names: List[str],
        message: str,
        preferences: Dict[str, Any],
        memories: List[Dict[str, Any]],
        conversation_history: List[Dict[str, Any]],
        cancel_event: asyncio.Event,
        itinerary_data: Optional[Dict[str, Any]] = None,
        weather_data: Optional[Dict[str, Any]] = None,
        timezone_id: str = "UTC"
    ) -> Dict[str, Dict[str, Any]]:
        """
        Runs multiple agents in parallel safely.
        """
        safe_agents = [a for a in agent_names if a in self.agents]

        async def run_one(a: str) -> Tuple[str, Dict[str, Any]]:
            # Emit tool events from inside result (we can't yield here)
            res = await self._run_agent_with_events(
                agent_name=a,
                message=message,
                preferences=preferences,
                memories=memories,
                conversation_history=conversation_history,
                cancel_event=cancel_event,
                itinerary_data=itinerary_data,
                weather_data=weather_data,
                timezone_id=timezone_id
            )
            return a, res

        tasks = [asyncio.create_task(run_one(a)) for a in safe_agents]

        results: Dict[str, Dict[str, Any]] = {}
        done = await asyncio.gather(*tasks, return_exceptions=True)

        for item in done:
            if isinstance(item, Exception):
                continue
            agent_name, res = item
            results[agent_name] = res

        return results

    # ---------------------------------------------------------------------
    # LLM orchestration planning
    # ---------------------------------------------------------------------
    async def _plan_orchestration(
        self,
        message: str,
        preferences: Dict[str, Any],
        memories: List[Dict[str, Any]],
        conversation_history: List[Dict[str, Any]],
        timezone_id: str = "UTC"
    ) -> Dict[str, Any]:
        """
        Uses LLM to decide:
        - intent
        - missing fields
        - which agents to call
        - parallel or not
        """

        history_text = self._format_history(conversation_history)
        
        from datetime import datetime, timezone
        try:
            from zoneinfo import ZoneInfo
            tz = ZoneInfo(timezone_id)
        except Exception:
            tz = timezone.utc
        current_time_str = datetime.now(tz).strftime("%A, %Y-%m-%d %H:%M %Z")

        prompt = f"""You are the planning brain of Watchout, an Indian travel AI.
Read the conversation carefully. Your job is to decide what action to take NEXT — not to answer the user directly.

ALLOWED_AGENTS = {sorted(list(ALLOWED_AGENTS))}
CRITICAL_FIELDS = {CRITICAL_FIELDS}

DECISION RULES:
- If the user is greeting, thanking, or making small talk → intent = "smalltalk", agents = []
- If the conversation history already has a field (destination, duration, travelers, etc.), do NOT mark it as missing — even if the structured preferences dict doesn't show it yet. Read the history carefully.
- Only trigger intent = "clarify" when truly critical fields (especially destination or duration) are MISSING and CANNOT be inferred from context clues in the conversation
- If the user says "plan my trip" / "let's go" / "make the itinerary" and you have destination + duration → intent = "plan"
- If the user asks to change/update/regenerate a part of the plan → intent = "refine"
- Vibe, pace, and travel_style CAN be inferred from language clues ("chill beach trip" → relaxed + beach; "me and my wife" → couple/romantic) — do NOT ask for these if they can be inferred
- Prefer parallel = true when weather, route, food, stay can run alongside each other (they are independent after itinerary)
- Only run agents the user actually needs — don't always run ALL agents, match to the specific request

CONTEXT:
Current user time: {current_time_str}
Conversation so far:
{history_text}

User just said: "{self._sanitize_for_prompt(message)}"

Already known about the user:
{json.dumps(preferences, ensure_ascii=False)}

User memories:
{json.dumps(memories, ensure_ascii=False)}

Output ONLY valid JSON matching exactly this structure:
{{
  "intent": "smalltalk|clarify|plan|refine",
  "should_clarify": true/false,
  "missing_fields": [],
  "agents": [],
  "parallel": true/false,
  "priority": [],
  "notes": ""
}}
"""

        schema = {
            "type": "object",
            "properties": {
                "intent": {"type": "string"},
                "should_clarify": {"type": "boolean"},
                "missing_fields": {"type": "array", "items": {"type": "string"}},
                "agents": {"type": "array", "items": {"type": "string"}},
                "parallel": {"type": "boolean"},
                "priority": {"type": "array", "items": {"type": "string"}},
                "notes": {"type": "string"},
            },
            "required": ["intent", "agents", "parallel", "missing_fields", "should_clarify"],
        }

        try:
            result = await self.generate_structured(prompt, schema)
            if not result:
                raise ValueError("Empty orchestration plan")

            # Clean invalid agent names
            agents = [a for a in result.get("agents", []) if a in ALLOWED_AGENTS]
            result["agents"] = agents

            # Compute missing fields deterministically too (backup)
            missing = self._compute_missing_fields(preferences)
            if missing and "clarification" not in agents:
                # If missing critical fields, force clarification
                result["intent"] = "clarify"
                result["should_clarify"] = True
                result["missing_fields"] = missing
                result["agents"] = ["clarification"]
                result["parallel"] = False

            return result

        except Exception:
            # fallback
            missing = self._compute_missing_fields(preferences)
            if missing:
                return {
                    "intent": "clarify",
                    "should_clarify": True,
                    "missing_fields": missing,
                    "agents": ["clarification"],
                    "parallel": False,
                    "priority": ["clarification"],
                    "notes": "Fallback clarify due to missing fields",
                }

            return {
                "intent": "plan",
                "should_clarify": False,
                "missing_fields": [],
                "agents": ["itinerary", "route", "stay", "food", "weather"],
                "parallel": True,
                "priority": ["itinerary", "route", "stay", "food", "weather"],
                "notes": "Fallback plan",
            }

    def _compute_missing_fields(self, preferences: Dict[str, Any]) -> List[str]:
        missing = []
        for f in CRITICAL_FIELDS:
            val = preferences.get(f)
            # For destinations_or_region, also check the 'destinations' key used by clarification agent
            if f == "destinations_or_region":
                val = val or preferences.get("destinations")
                # If user said "surprise me", destinations = ["agent_surprise"] — treat as satisfied
                if isinstance(val, list) and "agent_surprise" in val:
                    continue
                if preferences.get("destination_open"):
                    continue
            if not val:
                missing.append(f)
        return missing

    # ---------------------------------------------------------------------
    # Response weaving (LLM)
    # ---------------------------------------------------------------------
    async def _stream_weaved_response(
        self,
        user_message: str,
        preferences: Dict[str, Any],
        conversation_history: List[Dict[str, Any]],
        agent_outputs: str,
        timezone_id: str = "UTC"
    ) -> AsyncGenerator[str, None]:
        """
        Weaves multiple agent outputs into a human-like travel agent response.
        """

        history_text = self._format_history(conversation_history)

        user_name = preferences.get("name") or "there"
        vibe = preferences.get("travel_vibe", [])
        vibe_str = ", ".join(vibe) if isinstance(vibe, list) else str(vibe)

        from datetime import datetime, timezone
        try:
            from zoneinfo import ZoneInfo
            tz = ZoneInfo(timezone_id)
        except Exception:
            tz = timezone.utc
        current_time_str = datetime.now(tz).strftime("%A, %Y-%m-%d %H:%M %Z")

        prompt = f"""You are Watchout — India's warmest, most knowledgeable travel companion. You've just received research from your specialist team. Write the final message to the user.

PERSONA:
- Match the user's energy: if they're excited ("I can't wait!"), be enthusiastic back; if they're cautious ("I'm worried about safety"), be reassuring first
- Reference their actual preferences back to them ("Since you love beaches and hate crowds...")
- Use emojis naturally — only where they genuinely add warmth and energy, not as a checklist
- Short paragraphs, mobile-friendly, bold the most important info (names, times, costs)
- If the plan is COMPLETE, celebrate it and offer a clear next action (save it, refine a day, get hotel options)
- If the plan is PARTIAL, be upfront: "I've got your day-plan ready! Want me to also find hotels and transport?"
- Do NOT end every single message with a question — sometimes just deliver the goods and let them respond
- Speak like you're texting your well-travelled cousin from Bangalore who knows every shortcut

TONE CALIBRATION:
- Use Indian context naturally where relevant ("auto-rickshaws are perfect for short hops in Mysuru")
- Acknowledge the user by name if known
- Never mention internal agents, tools, or system details

CONTEXT:
Current user time: {current_time_str}
User's name: {user_name}
User's vibe: {vibe_str}
Conversation so far:
{history_text}

User just asked: "{self._sanitize_for_prompt(user_message)}"

Known preferences:
{json.dumps(preferences, ensure_ascii=False)}

Research from specialists:
{agent_outputs}

Write the final user-facing message now. Make it feel human, warm, and expert — like it came from your best-travelled friend.
"""

        try:
            async for chunk in self.stream(prompt):
                yield chunk
        except Exception:
            yield "I’m sorry — I hit a small issue while putting this together. Could you please try again?"

    # ---------------------------------------------------------------------
    # Smalltalk response
    # ---------------------------------------------------------------------
    async def _stream_smalltalk_response(
        self,
        message: str,
        preferences: Dict[str, Any],
    ) -> AsyncGenerator[str, None]:
        """
        Smalltalk response should be short and human.
        """

        name = preferences.get("name") or "there"

        known_destination = preferences.get("destinations") or preferences.get("destinations_or_region")
        dest_str = f"to {known_destination[0]}" if isinstance(known_destination, list) and known_destination else (f"to {known_destination}" if known_destination else "")

        prompt = f"""You are Watchout, India's friendliest travel companion. The user just said something casual.

User said: "{message}"
User name: {name}
What you know about them: {json.dumps(preferences)}

Respond in 1–3 lines. Be warm and natural, like texting a friend:
- If greeting → say hi warmly{f', maybe mention their trip {dest_str}' if dest_str else ''}, then naturally invite them to talk travel (NOT the robotic "Are you planning a trip?" — make it organic)
- If thanking → accept graciously and offer to help further with their trip
- If venting/complaining about travel → empathize briefly, then pivot to how you can help fix it
- If just chatting → engage warmly, then naturally invite them to plan something together

Do NOT use stiff transitions. Do NOT ask the word-for-word question "Are you planning a trip?" — weave travel naturally into your reply.
"""

        async for chunk in self.stream(prompt):
            yield chunk

    # ---------------------------------------------------------------------
    # Utility helpers
    # ---------------------------------------------------------------------
    def _format_history(self, conversation_history: List[Dict[str, Any]]) -> str:
        if not conversation_history:
            return "No previous messages."

        # Increased context from 10 to 50 messages to prevent forgetting early details
        recent = conversation_history[-50:]
        lines = []
        for msg in recent:
            role = msg.get("role", "user").upper()
            content = (msg.get("content") or "")[:500]
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    def _format_agent_outputs_for_weaver(self, all_results: Dict[str, Dict[str, Any]]) -> str:
        """
        Converts agent results into readable text for the response weaver.
        """
        blocks = []
        for agent_name, result in all_results.items():
            if not isinstance(result, dict):
                continue
            response = (result.get("response") or "").strip()
            data = result.get("data") or {}
            err = result.get("error")

            block = f"### {agent_name.upper()} RESULT\n"
            if err:
                block += f"ERROR: {err}\n"
            if response:
                block += f"RESPONSE:\n{response}\n"
            if data:
                # Keep data short to avoid prompt bloat
                short_data = json.dumps(data, ensure_ascii=False)[:4000]
                block += f"DATA (partial):\n{short_data}\n"
            blocks.append(block)

        return "\n\n".join(blocks) if blocks else "No specialist outputs."

    async def _stream_text(self, text: str) -> AsyncGenerator[str, None]:
        """
        Streams plain text in small chunks (fallback).
        Prefer real LLM streaming, but this is safe for non-streamed agent output.
        """
        if not text:
            return
        words = text.split()
        for w in words:
            yield w + " "
            await asyncio.sleep(0.005)

    async def _get_relevant_memories(self, user_id: str, query: str) -> List[Dict[str, Any]]:
        try:
            return await self.vector_store.search_memories(user_id=user_id, query=query, limit=5)
        except Exception:
            return []

    async def cancel_user_task(self, user_id: str) -> bool:
        """
        Explicitly cancel the active task for a user.
        """
        if user_id in self._user_lock:
            async with self._user_lock[user_id]:
                if user_id in self._active_cancel_event:
                    self._active_cancel_event[user_id].set()
                
                if user_id in self._active_task:
                    self._active_task[user_id].cancel()
                    return True
        return False
        
    # ---------------------------------------------------------------------
    # Compatibility methods (for unit tests)
    # ---------------------------------------------------------------------
    async def run(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        context = context or {}
        user_id = context.get("user_id", "test_user")

        response_tokens = []
        structured_data = {}

        async for event in self.process_message(
            user_id=user_id,
            message=user_input,
            trip_context=context,
            conversation_history=context.get("conversation_history") or [],
        ):
            if event.get("type") == "token":
                response_tokens.append(event.get("content", ""))
            elif event.get("type") == "data":
                structured_data[event.get("data_type")] = event.get("data")

        return {
            "response": "".join(response_tokens),
            "data": structured_data,
        }

# Singleton instance
_supervisor_instance = None

def get_supervisor() -> SupervisorAgent:
    """Get or create singleton supervisor instance."""
    global _supervisor_instance
    if _supervisor_instance is None:
        _supervisor_instance = SupervisorAgent()
    return _supervisor_instance
