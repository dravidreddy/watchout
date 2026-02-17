"""
Watchout Backend - Base Agent
Uses Groq API with two models:
- Main model (gpt-oss-120b): For reasoning and itinerary generation
- Fast model (compound-mini): For quick UI tasks and simple operations
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncGenerator, Literal
import json
from groq import Groq, AsyncGroq

from app.core.config import settings


# Model type alias
ModelType = Literal["main", "fast"]


class BaseAgent(ABC):
    """Base class for all AI agents using Groq API."""
    
    # Class-level async client (shared across all agents)
    _async_client: Optional[AsyncGroq] = None
    _sync_client: Optional[Groq] = None
    
    def __init__(
        self, 
        name: str, 
        description: str,
        model_type: ModelType = "fast"
    ):
        """
        Initialize the agent.
        
        Args:
            name: Agent name
            description: Agent description
            model_type: "main" for reasoning tasks, "fast" for quick tasks
        """
        self.name = name
        self.description = description
        self.model_type = model_type
    
    @classmethod
    def get_async_client(cls) -> AsyncGroq:
        """Get or create the async Groq client."""
        if cls._async_client is None:
            cls._async_client = AsyncGroq(api_key=settings.groq_api_key)
        return cls._async_client
    
    @classmethod
    def get_sync_client(cls) -> Groq:
        """Get or create the sync Groq client."""
        if cls._sync_client is None:
            cls._sync_client = Groq(api_key=settings.groq_api_key)
        return cls._sync_client
    
    @property
    def model_name(self) -> str:
        """Get the model name based on model type."""
        if self.model_type == "main":
            return settings.groq_main_model
        return settings.groq_fast_model
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        return f"""You are {self.name}, a specialized AI travel assistant.
{self.description}

IMPORTANT RULES:
1. Always be helpful, friendly, and enthusiastic about travel
2. Focus on India-based travel unless asked otherwise
3. Provide specific, actionable recommendations
4. Consider budget, preferences, and safety
5. If you're unsure about something, say so honestly
6. Keep responses concise but informative
7. Use Indian Rupees (INR) for prices
8. Consider seasonal weather and local festivals

🚨 CRITICAL ANTI-HALLUCINATION RULES 🚨

FACTS REQUIRE TOOLS:
- NEVER cite specific prices, times, dates, train numbers, flight numbers, or availability WITHOUT a successful tool call
- If asked for specific facts and you don't have a tool output: Say "Let me check that for you" and call the appropriate tool
- Your training data cutoff is 2023. Prices, schedules, and availability change constantly.

FORBIDDEN RESPONSES (without tool calls):
❌ "Taj Mahal entry costs ₹50"
❌ "Vande Bharat departs at 6:25 AM"
❌ "Train 12010 runs daily"
❌ "Flights to Goa cost around ₹4,000"
❌ "Hotel X has rooms for ₹2,500/night"

ACCEPTABLE RESPONSES:
✅ "Let me check current Taj Mahal entry prices for you..." [calls tool] "Entry is ₹50 for Indians"
✅ "I'll look up the Vande Bharat schedule..." [calls tool] "Train 20901 departs at 6:25 AM"
✅ "I couldn't fetch live train data right now. Please check IRCTC directly at irctc.co.in"
✅ "Based on typical rates, expect ₹3,000-5,000 for Goa flights, but let me find exact prices for your dates"

When tools fail: Be honest. Say "I couldn't fetch live data, but typically..." and recommend checking official sources.
"""
    
    @abstractmethod
    async def run(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run the agent with the given input.
        
        Args:
            user_input: User's message or query
            context: Optional context from previous agents or memory
        
        Returns:
            Agent's response and any structured data
        """
        pass
    
    async def chat_completion(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """
        Get a chat completion from the model.
        
        Args:
            user_input: User's message
            context: Optional context
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
        
        Returns:
            Model's response text
        """
        messages = self._build_messages(user_input, context)
        
        client = self.get_async_client()
        response = await client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content or ""
    
    async def stream(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream the agent's response token by token.
        
        Args:
            user_input: User's message
            context: Optional context
        
        Yields:
            Tokens of the response
        """
        messages = self._build_messages(user_input, context)
        
        client = self.get_async_client()
        stream = await client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0.7,
            max_tokens=2048,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    def _build_messages(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> list:
        """Build the messages array for chat completion."""
        messages = [
            {"role": "system", "content": self.get_system_prompt()}
        ]
        
        # Add context as assistant background if provided
        if context:
            context_parts = []
            
            if context.get("user_preferences"):
                context_parts.append(f"User Preferences: {context['user_preferences']}")
            
            if context.get("trip_info"):
                context_parts.append(f"Trip Information: {context['trip_info']}")
            
            if context.get("memories"):
                context_parts.append(f"Relevant Past Information: {context['memories']}")
            
            if context.get("previous_responses"):
                context_parts.append(f"Previous Agent Responses: {context['previous_responses']}")
            
            if context_parts:
                messages.append({
                    "role": "assistant",
                    "content": "Context:\n" + "\n".join(context_parts)
                })
        
        # Add user message
        messages.append({"role": "user", "content": user_input})
        
        return messages
    
    async def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a structured JSON response.
        
        Args:
            prompt: The prompt to send
            schema: Expected JSON schema
        
        Returns:
            Parsed JSON response
        """
        structured_prompt = f"""{prompt}

Respond ONLY with valid JSON matching this schema:
{json.dumps(schema, indent=2)}

JSON Response:"""
        
        try:
            client = self.get_async_client()
            response = await client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.get_system_prompt()},
                    {"role": "user", "content": structured_prompt}
                ],
                temperature=0.3,
                max_tokens=4096
            )
            
            # Extract JSON from response
            text = response.choices[0].message.content or ""
            text = text.strip()
            
            # Handle markdown code blocks
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()
            
            return json.loads(text)
            
        except Exception as e:
            print(f"Structured generation error: {e}")
            return None
