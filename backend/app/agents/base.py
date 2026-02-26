"""
Watchout Backend - Base Agent
Uses Groq API with two models:
- Main model (gpt-oss-120b): For reasoning and itinerary generation
- Fast model (compound-mini): For quick UI tasks and simple operations
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncGenerator, Literal, List
import json
import logging
import asyncio
from groq import Groq, AsyncGroq
import openai
from opentelemetry import trace

logger = logging.getLogger(__name__)

# Tracer for OB2
tracer = trace.get_tracer(__name__)


from app.core.config import settings
from app.core.token_limiter import check_token_cap, increment_token_usage

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
        
    @classmethod
    def get_openai_client(cls) -> openai.AsyncClient:
        """SC1: Get fallback OpenAI client."""
        if not hasattr(cls, '_openai_client'):
            cls._openai_client = openai.AsyncClient(api_key=settings.openai_api_key)
        return cls._openai_client
    
    @property
    def model_name(self) -> str:
        """Get the model name based on model type."""
        if self.model_type == "main":
            return settings.groq_main_model
        return settings.groq_fast_model
        
    @property
    def fallback_model_name(self) -> str:
        """SC1: Get OpenAI fallback model name."""
        if self.model_type == "main":
            return "gpt-4o"
        return "gpt-4o-mini"
    
    def get_system_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """
        AI1: Get the system prompt, supporting A/B testing dynamically.
        Uses context['trip_id'] hashing to keep users mapped to a consistent prompt version.
        """
        
        # A/B Test Routing
        use_variant_b = False
        language = "English"
        if context:
            if settings.ff_ab_test_prompts and "trip_id" in context:
                # Deterministic bucket assignment based on trip ID
                import hashlib
                trip_hash = int(hashlib.md5(context["trip_id"].encode()).hexdigest(), 16)
                use_variant_b = trip_hash % 2 == 1
                
            if "preferences" in context:
                prefs = context.get("preferences", {})
                # Make sure it's a dict, handling edge cases where it's parsed as something else
                if isinstance(prefs, dict):
                    language = prefs.get("language", "English")
                elif hasattr(prefs, "language"):
                    language = prefs.language
                    
        base_prompt = f"""You are "Watchout" — India's most trusted AI travel companion. You were born in the bylanes of Bengaluru, watched sunrises in Spiti, eaten chaat at Chowpatty, and navigated the chaos of Old Delhi bazaars. You speak like a well-travelled Indian friend: warm, knowledgeable, never condescending.

CRITICAL INSTRUCTION: You MUST formulate your outgoing responses entirely in {language}, except for proper nouns like city names or restaurant names. Maintain the persona but adapt the language accordingly.

PERSONA RULES:
- Speak in a warm, conversational tone as if texting a close friend who asked for travel help
- Address users by name whenever you know it; reference what they've already told you — never ask something they already answered
- Celebrate their choices ("Goa in December? Perfect timing!")
- Share insider knowledge ("Avoid Mall Road in Shimla after 4 PM — total gridlock")
- Never be robotic or list-heavy unless the user explicitly asks for a structured plan

INDIA EXPERTISE:
- "Budget" = ₹800–₹2,500/night (OYO, hostels, dharamshalas). "Mid-range" = ₹2,500–₹8,000. "Luxury" = ₹12,000+
- Distances are deceptive — "100 km" in the hills can mean 4 hours of driving
- Seasons deeply affect travel: Monsoon (Jul–Sep) floods coastal Kerala, Coorg, Mumbai. North India winters (Dec–Jan) freeze hill stations. Rajasthan summers (Apr–Jun) are brutal
- India has extraordinary regional diversity — be specific about local culture, cuisine, and customs, never generic
- Rush hours in all major cities: 8–10 AM and 5–8 PM — schedule travel outside these windows
- Always flag genuine safety concerns (altitude sickness in Ladakh, night travel on isolated bus routes, flash floods in monsoon treks)

OPERATIONAL RULES:
- Never make up prices, train numbers, or hotel names. If your tool returned no data, say so honestly and give a genuine human estimate with caveats ("trains typically cost ₹300–₹800 in sleeper class — check IRCTC for exact fares")
- Do NOT expose internal agent names, tool names, or system architecture to the user
- Structured output (JSON, tables) is for internal agent-to-agent communication only — the user always gets a warm, readable, human response
- When data is incomplete, be transparent and offer a clear path forward"""

        variant_b_additions = """
EMPATHY MODE ACTIVE:
- Always ask one light, clarifying question at the end to keep the conversation going unless the user is done modifying the trip.
- Mirror the user's excitement level exactly."""

        if use_variant_b:
            logger.debug("AI1: Using Prompt Variant B for trip: %s", context.get("trip_id"))
            return base_prompt + variant_b_additions
            
        return base_prompt
    
    # ------------------------------------------------------------------------------------------
    # AI2: Model Drift Detection
    # ------------------------------------------------------------------------------------------
    def _detect_model_drift(self, content: str, expected_type: str = "text") -> None:
        """
        AI2: Monitor the LLM response for classic failure modes indicating model degradation.
        Emits log warnings that Datadog/Grafana can alert on if freq > threshold.
        """
        if not content:
            return
            
        lower_content = content.lower()
        
        # 1. Hallucination / Apology Loops
        if "as an ai language model" in lower_content or "i cannot assist" in lower_content:
            logger.warning("AI2_DRIFT: Rejection phrase detected in %s", self.name)
            
        # 2. Syntax breakdown on JSON requests
        if expected_type == "json":
            if not content.strip().startswith("{") and not content.strip().startswith("["):
                logger.error("AI2_DRIFT: JSON preamble hallucination detected in %s (Starts with text instead of bracket)", self.name)
        
        # 3. Excessive repetition (token stutter limits)
        words = content.split()
        if len(words) > 20:
            for i in range(len(words) - 5):
                # Check if a 5-word sequence repeats immediately
                seq1 = words[i:i+5]
                seq2 = words[i+5:i+10]
                if seq1 == seq2:
                    logger.warning("AI2_DRIFT: Repetition stutter detected in %s", self.name)
                    break
    
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
    
    # Hard token caps — prevent runaway generation and protect Groq rate limits
    _MAX_TOKENS_STREAM: int = 2048
    _MAX_TOKENS_COMPLETE: int = 4096
    _MAX_TOKENS_STRUCTURED: int = 4096

    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        OB4: Approximate cost tracking based on Groq pricing (USD).
        Llama-3.1-8b: $0.05 / 1M prompt, $0.08 / 1M completion
        Llama-3.3-70b: $0.59 / 1M prompt, $0.79 / 1M completion
        """
        model = self.model_name.lower()
        if "70b" in model:
            return (prompt_tokens * 0.59 / 1_000_000) + (completion_tokens * 0.79 / 1_000_000)
        elif "8b" in model:
            return (prompt_tokens * 0.05 / 1_000_000) + (completion_tokens * 0.08 / 1_000_000)
        return 0.0  # Fallback


    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        json_mode: bool = False
    ) -> str:
        """
        Send a chat completion request to Groq (with OpenAI fallback).
        Always enforces a hard token cap to prevent runaway generation.
        """
        effective_max = min(max_tokens, self._MAX_TOKENS_COMPLETE) if max_tokens else self._MAX_TOKENS_COMPLETE
        
        # SC1/SC2: Define the primary Groq call
        async def _call_groq():
            await check_token_cap()
            client = self.get_async_client()
            params = {
                "model": self.model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": effective_max,
            }
            if json_mode:
                params["response_format"] = {"type": "json_object"}
            
            with tracer.start_as_current_span(f"{self.name}.chat_completion") as span:
                span.set_attribute("llm.agent", self.name)
                span.set_attribute("llm.provider", "groq")
                span.set_attribute("llm.model", self.model_name)
                
                response = await client.chat.completions.create(**params)
                
                p_tokens = response.usage.prompt_tokens if response.usage else 0
                c_tokens = response.usage.completion_tokens if response.usage else 0
                cost = self._calculate_cost(p_tokens, c_tokens)
                
                # OB3/OB4: Track tokens and cost
                span.set_attribute("llm.usage.prompt_tokens", p_tokens)
                span.set_attribute("llm.usage.completion_tokens", c_tokens)
                span.set_attribute("llm.cost.usd", cost)
                
                await increment_token_usage(p_tokens, c_tokens)
                
                content = response.choices[0].message.content or ""
                self._detect_model_drift(content, expected_type="json" if json_mode else "text")
                return content
                
        # SC1: Define the fallback OpenAI call
        async def _call_openai():
            client = self.get_openai_client()
            params = {
                "model": self.fallback_model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": effective_max,
            }
            if json_mode:
                params["response_format"] = {"type": "json_object"}
                
            with tracer.start_as_current_span(f"{self.name}.chat_completion_fallback") as span:
                span.set_attribute("llm.agent", self.name)
                span.set_attribute("llm.provider", "openai")
                span.set_attribute("llm.model", self.fallback_model_name)
                
                response = await client.chat.completions.create(**params)
                
                p_tokens = response.usage.prompt_tokens if response.usage else 0
                c_tokens = response.usage.completion_tokens if response.usage else 0
                await increment_token_usage(p_tokens, c_tokens)
                
                return response.choices[0].message.content

        try:
            # Attempt Groq
            return await _call_groq()
        except Exception as e:
            logger.warning("Groq API Error (%s): %s", self.name, e)
            try:
                # Immediate fallback on Groq 5xx errors even if breaker isn't fully open yet
                return await _call_openai()
            except Exception as e2:
                logger.error("Fallback OpenAI API Error (%s): %s", self.name, e2)
                return ""

        # Honour caller cap but never exceed the class hard limit
        effective_max = min(max_tokens, self._MAX_TOKENS_COMPLETE) if max_tokens else self._MAX_TOKENS_COMPLETE

        params = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": effective_max,
        }

        if json_mode:
            params["response_format"] = {"type": "json_object"}

        try:
            with tracer.start_as_current_span(f"{self.name}.chat_completion") as span:
                span.set_attribute("llm.agent", self.name)
                span.set_attribute("llm.model", self.model_name)
                
                response = await client.chat.completions.create(**params)
                
                # OB3/OB4: Track tokens and cost
                p_tokens = response.usage.prompt_tokens if response.usage else 0
                c_tokens = response.usage.completion_tokens if response.usage else 0
                cost = self._calculate_cost(p_tokens, c_tokens)
                
                span.set_attribute("llm.usage.prompt_tokens", p_tokens)
                span.set_attribute("llm.usage.completion_tokens", c_tokens)
                span.set_attribute("llm.cost.usd", cost)
                
                await increment_token_usage(p_tokens, c_tokens)
                
                logger.info("Agent %s chat_completion tokens: prompt=%d completion=%d cost=$%.6f", 
                            self.name, p_tokens, c_tokens, cost)
                
                return response.choices[0].message.content
        except Exception as e:
            logger.warning("Groq API Error (%s): %s", self.name, e)
            return ""

    async def stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """
        Stream response tokens from Groq (with OpenAI fallback).
        Always enforces _MAX_TOKENS_STREAM to cap cost and prevent runaway responses.
        """
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": prompt}
        ]

        # SC1/SC2: Primary Groq Stream
        async def _stream_groq() -> AsyncGenerator[str, None]:
            await check_token_cap()
            client = self.get_async_client()
            with tracer.start_as_current_span(f"{self.name}.stream") as span:
                span.set_attribute("llm.agent", self.name)
                span.set_attribute("llm.provider", "groq")
                span.set_attribute("llm.model", self.model_name)
                
                stream = await client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.7,
                    stream=True,
                    stream_options={"include_usage": True},
                    max_tokens=self._MAX_TOKENS_STREAM,
                )
                
                full_content = []
                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        content_piece = chunk.choices[0].delta.content
                        full_content.append(content_piece)
                        yield content_piece
                        
                    if hasattr(chunk, "x_groq") and getattr(chunk.x_groq, "usage", None):
                        usage = chunk.x_groq.usage
                        cost = self._calculate_cost(usage.prompt_tokens, usage.completion_tokens)
                        span.set_attribute("llm.usage.prompt_tokens", usage.prompt_tokens)
                        span.set_attribute("llm.cost.usd", cost)
                        
                        await increment_token_usage(usage.prompt_tokens, usage.completion_tokens)
                        
                self._detect_model_drift("".join(full_content), expected_type="text")

        # SC1: Fallback OpenAI Stream
        async def _stream_openai() -> AsyncGenerator[str, None]:
            client = self.get_openai_client()
            with tracer.start_as_current_span(f"{self.name}.stream_fallback") as span:
                span.set_attribute("llm.agent", self.name)
                span.set_attribute("llm.provider", "openai")
                span.set_attribute("llm.model", self.fallback_model_name)
                
                stream = await client.chat.completions.create(
                    model=self.fallback_model_name,
                    messages=messages,
                    temperature=0.7,
                    stream=True,
                    stream_options={"include_usage": True},
                    max_tokens=self._MAX_TOKENS_STREAM,
                )
                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content

        # Execute — stream Groq, fall back to OpenAI on any error
        try:
            async for token in _stream_groq():
                yield token
        except Exception as e:
            logger.warning("Groq stream error (%s): %s — falling back to OpenAI", self.name, e)
            try:
                async for token in _stream_openai():
                    yield token
            except Exception as e2:
                logger.error("OpenAI stream fallback error (%s): %s", self.name, e2)
                yield ""


    async def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Generate strict JSON output matching a schema (with OpenAI fallback).
        """
        system_prompt = self.get_system_prompt()
        system_prompt += f"\n\nOUTPUT JSON FORMAT:\n{json.dumps(schema, indent=2)}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        async def _generate_groq() -> str:
            await check_token_cap()
            client = self.get_async_client()
            with tracer.start_as_current_span(f"{self.name}.generate_structured") as span:
                span.set_attribute("llm.agent", self.name)
                span.set_attribute("llm.provider", "groq")
                
                response = await client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.2,
                    response_format={"type": "json_object"},
                    max_tokens=self._MAX_TOKENS_STRUCTURED,
                )
                p_tokens = response.usage.prompt_tokens if response.usage else 0
                c_tokens = response.usage.completion_tokens if response.usage else 0
                span.set_attribute("llm.cost.usd", self._calculate_cost(p_tokens, c_tokens))
                
                await increment_token_usage(p_tokens, c_tokens)
                
                content = response.choices[0].message.content or "{}"
                self._detect_model_drift(content, expected_type="json")
                return content
                
        async def _generate_openai() -> str:
            client = self.get_openai_client()
            with tracer.start_as_current_span(f"{self.name}.generate_structured_fallback") as span:
                span.set_attribute("llm.agent", self.name)
                span.set_attribute("llm.provider", "openai")
                
                response = await client.chat.completions.create(
                    model=self.fallback_model_name,
                    messages=messages,
                    temperature=0.2,
                    response_format={"type": "json_object"},
                    max_tokens=self._MAX_TOKENS_STRUCTURED,
                )
                
                p_tokens = response.usage.prompt_tokens if response.usage else 0
                c_tokens = response.usage.completion_tokens if response.usage else 0
                await increment_token_usage(p_tokens, c_tokens)
                
                return response.choices[0].message.content or "{}"

        # Execute
        try:
            content = await _generate_groq()
        except Exception as e:
            logger.warning("Groq API Error (%s): %s", self.name, e)
            try:
                content = await _generate_openai()
            except Exception: return None

        if not content:
            return None

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning("Structured Generation Parse Error (%s)", self.name)
            return None
