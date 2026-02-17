"""
Watchout Backend - Supervisor Agent (LLM-Powered Orchestrator)

This supervisor uses LLM to:
1. Decide which agents to invoke based on user message
2. Orchestrate multiple agents (parallel when possible)
3. Curate and merge all agent responses into a unified output
"""
from typing import Dict, Any, Optional, AsyncGenerator, List
import asyncio
import json

from app.agents.base import BaseAgent
from app.agents.clarification import ClarificationAgent
from app.agents.itinerary import ItineraryAgent
from app.agents.route import RouteAgent
from app.agents.transportation import TransportationAgent
from app.agents.stay import StayAgent
from app.agents.food import FoodAgent
from app.agents.weather import WeatherAgent
from app.db.vector_store import VectorStore


class SupervisorAgent(BaseAgent):
    """
    LLM-powered orchestrator for travel planning.
    Manages conversation flow, delegates to specialized agents,
    and curates unified responses.
    """
    
    def __init__(self):
        super().__init__(
            name="Travel Supervisor",
            description="""You are the lead travel planning coordinator.
Your role is to:
- Understand user travel requests
- Decide which specialized agents to invoke
- Merge all agent responses into a cohesive, helpful answer
- Maintain a friendly, enthusiastic personality""",
            model_type="main"  # Use main model for orchestration decisions
        )
        
        # Initialize specialized agents
        self.agents = {
            "clarification": ClarificationAgent(),
            "itinerary": ItineraryAgent(),
            "route": RouteAgent(),
            "transportation": TransportationAgent(),
            "stay": StayAgent(),
            "food": FoodAgent(),
            "weather": WeatherAgent(),
        }
        
        self.vector_store = VectorStore
        
        # Task tracking for cancellation (Priority 3)
        self.active_tasks: Dict[str, Dict[str, bool]] = {}  # Stores cancel flags
        self.task_locks: Dict[str, asyncio.Lock] = {}
    
    async def process_message(
        self,
        user_id: str,
        message: str,
        trip_context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process a user message using LLM-based orchestration with task cancellation support.
        
        If a user sends a new message while a previous one is processing, the old task
        is automatically cancelled to prevent state mixing.
        
        Args:
            user_id: User's Firebase UID
            message: Current user message
            trip_context: Trip preferences, itinerary, memories
            conversation_history: Previous messages for context
        
        Yields events with types:
        - status: Agent status updates
        - token: Response tokens
        - tool_start/tool_end: Tool invocations
        - data: Structured data (itinerary, routes, etc.)
        - done: Completion signal
        - cancelled: Previous request was cancelled
        """
        # Get or create lock for this user
        if user_id not in self.task_locks:
            self.task_locks[user_id] = asyncio.Lock()
        
        async with self.task_locks[user_id]:
            # Cancel any existing processing for this user
            if user_id in self.active_tasks:
                old_cancel_flag = self.active_tasks[user_id]
                old_cancel_flag["cancelled"] = True
                
                yield {
                    "type": "status",
                    "status": "Previous request cancelled",
                    "agent": "Supervisor"
                }
            
            # Process the message (no need to wrap in a task)
            generator = self._process_internal(user_id, message, trip_context, conversation_history)
            
            # Store the generator for potential cancellation
            # We can't cancel a generator directly, but we can track it
            cancel_flag = {"cancelled": False}
            self.active_tasks[user_id] = cancel_flag
            
            try:
                async for event in generator:
                    if cancel_flag.get("cancelled"):
                        yield {
                            "type": "cancelled",
                            "message": "Request was cancelled by user"
                        }
                        break
                    yield event
            except asyncio.CancelledError:
                cancel_flag["cancelled"] = True
                yield {
                    "type": "cancelled",
                    "message": "Request was cancelled by user"
                }
                raise
            finally:
                # Clean up task tracking
                if user_id in self.active_tasks:
                    del self.active_tasks[user_id]
    
    async def _process_internal(
        self,
        user_id: str,
        message: str,
        trip_context: Optional[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, Any]]]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Internal processing logic (separated for task cancellation).
        """
        trip_context = trip_context or {}
        conversation_history = conversation_history or []
        preferences = trip_context.get("preferences", {})
        
        # 1. Retrieve relevant memories
        yield {"type": "status", "status": "Recalling your preferences...", "agent": "Memory"}
        memories = await self._get_relevant_memories(user_id, message)
        
        # 2. Use LLM to determine orchestration plan
        yield {"type": "status", "status": "Planning your request...", "agent": "Supervisor"}
        orchestration_plan = await self._plan_orchestration(message, preferences, memories, conversation_history)
        
        agents_to_invoke = orchestration_plan.get("agents", ["clarification"])
        can_parallel = orchestration_plan.get("parallel", False)
        
        # 3. Check if clarification is needed - either to gather info or continue conversation
        # Key required fields to start planning
        required_fields = ["destinations", "duration_days", "num_travelers", "travel_vibe"]
        has_required_info = all(preferences.get(field) for field in required_fields)
        
        if "clarification" in agents_to_invoke or not has_required_info:
            yield {"type": "status", "status": "Understanding your travel plans...", "agent": "Clarification"}
            
            result = await self.agents["clarification"].run(message, {
                "extracted_preferences": preferences,
                "memories": memories,
                "conversation_history": conversation_history
            })
            
            # For clarification, we can stream directly (no merge needed)
            for token in result.get("response", "").split():
                yield {"type": "token", "content": token + " "}
                await asyncio.sleep(0.02)
            
            yield {
                "type": "data",
                "data_type": "preferences",
                "data": result.get("extracted_preferences", {})
            }
            
            yield {"type": "done", "is_complete": result.get("is_complete", False)}
            return
        
        # 4. Execute agents and collect responses
        agent_responses = {}
        structured_data = {}
        
        if can_parallel:
            # Run agents in parallel
            yield {"type": "status", "status": "Gathering information from multiple sources...", "agent": "Supervisor"}
            agent_responses, structured_data = await self._run_agents_parallel(
                agents_to_invoke, message, preferences, memories, conversation_history
            )
        else:
            # Run agents sequentially
            for agent_name in agents_to_invoke:
                if agent_name == "clarification":
                    continue  # Already handled above
                    
                yield {"type": "status", "status": f"Consulting {agent_name} specialist...", "agent": agent_name.title()}
                
                result = await self._run_single_agent(agent_name, message, preferences, memories, conversation_history)
                
                if result:
                    agent_responses[agent_name] = result.get("response", "")
                    # Collect any structured data
                    for key in ["itinerary", "raw_plan", "weather", "restaurants", "accommodations", "options", "route"]:
                        if result.get(key):
                            structured_data[key] = result[key]
        
        # 5. Curate and merge responses using LLM
        yield {"type": "status", "status": "Crafting your personalized response...", "agent": "Supervisor"}
        
        final_response = await self._curate_response(
            user_message=message,
            agent_responses=agent_responses,
            preferences=preferences,
            conversation_history=conversation_history
        )
        
        # 6. Stream the curated response by sentences (not words) to reduce layout shift
        import re
        
        # Split by sentence boundaries while preserving punctuation
        sentences = re.split(r'([.!?]+\s+)', final_response)
        for i in range(0, len(sentences), 2):
            sentence = sentences[i]
            punctuation = sentences[i + 1] if i + 1 < len(sentences) else ''
            complete_sentence = sentence + punctuation
            
            if complete_sentence.strip():
                yield {"type": "token", "content": complete_sentence}
                await asyncio.sleep(0.05)  # Slightly slower but smoother rendering
        
        # 7. Yield any structured data
        for data_type, data in structured_data.items():
            yield {"type": "data", "data_type": data_type, "data": data}
        
        yield {"type": "done", "is_complete": True}
    
    async def _plan_orchestration(
        self,
        message: str,
        preferences: Dict[str, Any],
        memories: List[Dict],
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Use LLM to determine which agents to invoke and how."""
        
        # Format recent conversation for context
        history_text = "No previous conversation."
        if conversation_history:
            recent = conversation_history[-8:]  # Include more history for better context
            history_lines = []
            for msg in recent:
                role = msg.get("role", "user").upper()
                content = msg.get("content", "")[:300]
                history_lines.append(f"{role}: {content}")
            history_text = "\n".join(history_lines)
        
        prompt = f"""Analyze this travel conversation and create an orchestration plan.

CONVERSATION HISTORY:
{history_text}

CURRENT USER MESSAGE: "{message}"

CURRENT EXTRACTED PREFERENCES: {json.dumps(preferences, indent=2) if preferences else "None yet"}

AVAILABLE AGENTS:
1. clarification - Gather user preferences through conversation (use when info is missing or user is providing/updating preferences)
2. itinerary - Create detailed day-by-day travel plans
3. weather - Get weather forecasts for destinations
4. stay - Find hotels and accommodations
5. food - Recommend restaurants and local cuisine
6. transportation - Find flights, trains, buses between cities
7. route - Calculate routes and directions

DECISION RULES:
- If ANY of these is missing: destination, duration, number of travelers, travel vibe -> use "clarification"
- If user is providing NEW information about their trip preferences -> use "clarification" to extract and update
- If user is correcting previous information -> use "clarification"
- For complete trip planning, use: weather, itinerary, stay, food, transportation
- For specific questions about a topic, use only relevant agents
- Multiple info-gathering agents (weather, food, stay) can run in parallel

IMPORTANT: Consider the ENTIRE conversation history when making this decision.

Return which agents to invoke and whether they can run in parallel."""

        schema = {
            "type": "object",
            "properties": {
                "agents": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of agent names to invoke"
                },
                "parallel": {
                    "type": "boolean",
                    "description": "Whether agents can run in parallel"
                },
                "reasoning": {
                    "type": "string",
                    "description": "Brief explanation of the decision"
                }
            }
        }
        
        try:
            result = await self.generate_structured(prompt, schema)
            if result:
                return result
        except Exception as e:
            print(f"Orchestration planning error: {e}")
        
        # Fallback to keyword-based classification
        return self._fallback_classify(message, preferences)
    
    def _fallback_classify(self, message: str, preferences: Dict) -> Dict[str, Any]:
        """Fallback keyword-based classification if LLM fails."""
        message_lower = message.lower()
        
        if not preferences.get("destinations"):
            return {"agents": ["clarification"], "parallel": False}
        
        if any(w in message_lower for w in ["plan", "itinerary", "trip"]):
            return {"agents": ["weather", "itinerary", "stay", "food"], "parallel": False}
        
        if any(w in message_lower for w in ["flight", "train", "bus", "transport"]):
            return {"agents": ["transportation"], "parallel": False}
        
        if any(w in message_lower for w in ["hotel", "stay", "accommodation"]):
            return {"agents": ["stay"], "parallel": False}
        
        if any(w in message_lower for w in ["food", "eat", "restaurant"]):
            return {"agents": ["food"], "parallel": False}
        
        if any(w in message_lower for w in ["weather", "rain", "temperature"]):
            return {"agents": ["weather"], "parallel": False}
        
        return {"agents": ["clarification"], "parallel": False}
    
    async def _run_single_agent(
        self,
        agent_name: str,
        message: str,
        preferences: Dict[str, Any],
        memories: List[Dict],
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        """Run a single agent with appropriate context."""
        
        agent = self.agents.get(agent_name)
        if not agent:
            return None
        
        destinations = preferences.get("destinations", [])
        city = destinations[0] if destinations else ""
        
        context = {
            "preferences": preferences,
            "memories": memories,
            "conversation_history": conversation_history or [],
            "city": city,
            "budget": preferences.get("budget_range"),
            "from_city": preferences.get("origin_city"),
            "to_city": city,
        }
        
        # Add agent-specific context
        if agent_name == "itinerary":
            context["places_data"] = {}
            context["weather_data"] = {}
        
        try:
            return await agent.run(message, context)
        except Exception as e:
            print(f"Agent {agent_name} error: {e}")
            return {"response": f"I had trouble getting {agent_name} information."}
    
    async def _run_agents_parallel(
        self,
        agent_names: List[str],
        message: str,
        preferences: Dict[str, Any],
        memories: List[Dict],
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> tuple[Dict[str, str], Dict[str, Any]]:
        """Run multiple agents in parallel and collect results."""
        
        tasks = []
        valid_agents = []
        
        for agent_name in agent_names:
            if agent_name != "clarification" and agent_name in self.agents:
                task = self._run_single_agent(agent_name, message, preferences, memories, conversation_history)
                tasks.append(task)
                valid_agents.append(agent_name)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        responses = {}
        structured_data = {}
        
        for agent_name, result in zip(valid_agents, results):
            if isinstance(result, Exception):
                responses[agent_name] = f"Error getting {agent_name} info."
            elif result:
                responses[agent_name] = result.get("response", "")
                # Collect structured data
                for key in ["itinerary", "raw_plan", "weather", "restaurants", "accommodations", "options", "route"]:
                    if result.get(key):
                        structured_data[key] = result[key]
        
        return responses, structured_data
    
    async def _curate_response(
        self,
        user_message: str,
        agent_responses: Dict[str, str],
        preferences: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Use LLM to merge agent responses into a unified, conversational output."""
        
        if not agent_responses:
            return "I'm having trouble processing your request. Could you please try again?"
        
        # If only one agent responded, return directly (small optimization)
        if len(agent_responses) == 1:
            return list(agent_responses.values())[0]
        
        responses_text = "\n\n".join([
            f"### {agent.upper()} AGENT:\n{response}"
            for agent, response in agent_responses.items()
        ])
        
        # Format conversation history
        history_text = "No previous conversation."
        if conversation_history:
            recent = conversation_history[-5:]  # Last 5 messages
            history_lines = []
            for msg in recent:
                role = msg.get("role", "user").upper()
                content = msg.get("content", "")[:300]
                history_lines.append(f"{role}: {content}")
            history_text = "\n".join(history_lines)
        
        prompt = f"""You are a friendly travel assistant. Merge these agent responses into ONE cohesive, 
conversational response for the user.

CONVERSATION HISTORY:
{history_text}

USER ASKED: "{user_message}"

USER PREFERENCES: {json.dumps(preferences, indent=2) if preferences else "Not specified"}

AGENT RESPONSES:
{responses_text}

GUIDELINES:
1. Be conversational, friendly, and enthusiastic about travel
2. Maintain continuity with the previous conversation
3. Create a unified narrative - don't list agents separately
4. Highlight the most important and exciting information first
5. Use bullet points for lists (activities, restaurants, etc.)
6. Include relevant emojis for a fun tone
7. Remove any redundant information
8. Keep it concise but comprehensive
9. Use Indian Rupees (INR) for prices
10. End with a helpful follow-up question or next step

Write a response that feels like advice from a knowledgeable friend:"""
        
        try:
            response = await self.chat_completion(
                prompt,
                temperature=0.7,
                max_tokens=2048
            )
            return response
        except Exception as e:
            print(f"Response curation error: {e}")
            # Fallback: concatenate responses
            return "\n\n".join(agent_responses.values())
    
    async def _get_relevant_memories(self, user_id: str, query: str) -> List[Dict]:
        """Retrieve relevant memories from vector store."""
        try:
            return await self.vector_store.search_memories(user_id, query, limit=5)
        except Exception:
            return []
    
    # Keep run method for compatibility with BaseAgent
    async def run(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Run the supervisor (for testing compatibility)."""
        context = context or {}
        
        responses = []
        data = {}
        
        async for event in self.process_message(
            user_id=context.get("user_id", "test_user"),
            message=user_input,
            trip_context=context
        ):
            if event.get("type") == "token":
                responses.append(event.get("content", ""))
            elif event.get("type") == "data":
                data[event.get("data_type")] = event.get("data")
        
        return {
            "response": "".join(responses),
            "data": data
        }
