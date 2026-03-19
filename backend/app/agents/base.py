"""
Watchout Backend - Base Agent
Uses OpenAI API as primary with two models:
- Main model (gpt-4o): For reasoning and itinerary generation
- Fast model (gpt-4o-mini): For quick UI tasks and simple operations
Falls back to Groq (Llama) models if OpenAI is unavailable.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncGenerator, Literal, List
import json
import logging
import asyncio
import openai
from opentelemetry import trace

logger = logging.getLogger(__name__)

# Tracer for OB2
tracer = trace.get_tracer(__name__)


from app.core.config import settings
from app.core.token_limiter import check_token_cap, increment_token_usage
from app.prompts import build_base_system_prompt, build_structured_output_suffix

# Model type alias
ModelType = Literal["main", "fast"]


class BaseAgent(ABC):
    """Base class for all AI agents using OpenAI API (with Groq fallback)."""
    
    # Class-level clients (shared across all agents)
    _openai_client: Optional[openai.AsyncClient] = None
    
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
    def get_async_client(cls) -> openai.AsyncClient:
        """Get or create the async OpenAI client (primary)."""
        if cls._openai_client is None:
            cls._openai_client = openai.AsyncClient(api_key=settings.openai_api_key)
        return cls._openai_client
    
    @classmethod
    def get_groq_client(cls):
        """Get or create the async Groq client (fallback)."""
        if not hasattr(cls, '_groq_client') or cls._groq_client is None:
            from groq import AsyncGroq
            cls._groq_client = AsyncGroq(api_key=settings.groq_api_key)
        return cls._groq_client
    
    @property
    def model_name(self) -> str:
        """Get the primary (OpenAI) model name based on model type."""
        if self.model_type == "main":
            return settings.openai_main_model
        return settings.openai_fast_model
        
    @property
    def fallback_model_name(self) -> str:
        """Get Groq fallback model name."""
        if self.model_type == "main":
            return settings.groq_main_model
        return settings.groq_fast_model
    
    def get_system_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """
        AI1: Get the system prompt, supporting A/B testing dynamically.
        Uses context['trip_id'] hashing to keep users mapped to a consistent prompt version.
        """
        
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
                if isinstance(prefs, dict):
                    language = prefs.get("language", "English")
                elif hasattr(prefs, "language"):
                    language = prefs.language

        if use_variant_b:
            logger.debug("AI1: Using Prompt Variant B for trip: %s", context.get("trip_id"))

        return build_base_system_prompt(language=language, use_variant_b=use_variant_b)
    
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
    
    # Hard token caps — prevent runaway generation and protect rate limits
    _MAX_TOKENS_STREAM: int = 2048
    _MAX_TOKENS_COMPLETE: int = 4096
    _MAX_TOKENS_STRUCTURED: int = 4096

    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        OB4: Approximate cost tracking based on OpenAI pricing (USD).
        GPT-4o:      $2.50 / 1M prompt, $10.00 / 1M completion
        GPT-4o-mini: $0.15 / 1M prompt, $0.60 / 1M completion
        """
        model = self.model_name.lower()
        if "gpt-4o-mini" in model:
            return (prompt_tokens * 0.15 / 1_000_000) + (completion_tokens * 0.60 / 1_000_000)
        elif "gpt-4o" in model:
            return (prompt_tokens * 2.50 / 1_000_000) + (completion_tokens * 10.00 / 1_000_000)
        return 0.0  # Fallback


    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        json_mode: bool = False
    ) -> str:
        """
        Send a chat completion request to OpenAI (with Groq fallback).
        Always enforces a hard token cap to prevent runaway generation.
        """
        effective_max = min(max_tokens, self._MAX_TOKENS_COMPLETE) if max_tokens else self._MAX_TOKENS_COMPLETE
        
        # Primary OpenAI call
        async def _call_openai():
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
                span.set_attribute("llm.provider", "openai")
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
                
        # Fallback Groq call
        async def _call_groq():
            client = self.get_groq_client()
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
                span.set_attribute("llm.provider", "groq")
                span.set_attribute("llm.model", self.fallback_model_name)
                
                response = await client.chat.completions.create(**params)
                
                p_tokens = response.usage.prompt_tokens if response.usage else 0
                c_tokens = response.usage.completion_tokens if response.usage else 0
                await increment_token_usage(p_tokens, c_tokens)
                
                return response.choices[0].message.content

        try:
            # Attempt OpenAI (primary)
            return await _call_openai()
        except Exception as e:
            logger.warning("OpenAI API Error (%s): %s", self.name, e)
            try:
                # Immediate fallback to Groq on OpenAI errors
                return await _call_groq()
            except Exception as e2:
                logger.error("Fallback Groq API Error (%s): %s", self.name, e2)
                return ""

    async def stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """
        Stream response tokens from OpenAI (with Groq fallback).
        Always enforces _MAX_TOKENS_STREAM to cap cost and prevent runaway responses.
        """
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": prompt}
        ]

        # Primary OpenAI Stream
        async def _stream_openai() -> AsyncGenerator[str, None]:
            await check_token_cap()
            client = self.get_async_client()
            with tracer.start_as_current_span(f"{self.name}.stream") as span:
                span.set_attribute("llm.agent", self.name)
                span.set_attribute("llm.provider", "openai")
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
                        
                    # Track usage from the final chunk
                    if hasattr(chunk, "usage") and chunk.usage:
                        usage = chunk.usage
                        cost = self._calculate_cost(usage.prompt_tokens, usage.completion_tokens)
                        span.set_attribute("llm.usage.prompt_tokens", usage.prompt_tokens)
                        span.set_attribute("llm.cost.usd", cost)
                        
                        await increment_token_usage(usage.prompt_tokens, usage.completion_tokens)
                        
                self._detect_model_drift("".join(full_content), expected_type="text")

        # Fallback Groq Stream
        async def _stream_groq() -> AsyncGenerator[str, None]:
            client = self.get_groq_client()
            with tracer.start_as_current_span(f"{self.name}.stream_fallback") as span:
                span.set_attribute("llm.agent", self.name)
                span.set_attribute("llm.provider", "groq")
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

        # Execute — stream OpenAI, fall back to Groq on any error
        try:
            async for token in _stream_openai():
                yield token
        except Exception as e:
            logger.warning("OpenAI stream error (%s): %s — falling back to Groq", self.name, e)
            try:
                async for token in _stream_groq():
                    yield token
            except Exception as e2:
                logger.error("Groq stream fallback error (%s): %s", self.name, e2)
                yield ""


    async def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Generate strict JSON output matching a schema (with Groq fallback).
        """
        system_prompt = self.get_system_prompt()
        system_prompt += "\n\n" + build_structured_output_suffix(schema)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        async def _generate_openai() -> str:
            await check_token_cap()
            client = self.get_async_client()
            with tracer.start_as_current_span(f"{self.name}.generate_structured") as span:
                span.set_attribute("llm.agent", self.name)
                span.set_attribute("llm.provider", "openai")
                
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
                
        async def _generate_groq() -> str:
            client = self.get_groq_client()
            with tracer.start_as_current_span(f"{self.name}.generate_structured_fallback") as span:
                span.set_attribute("llm.agent", self.name)
                span.set_attribute("llm.provider", "groq")
                
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
            content = await _generate_openai()
        except Exception as e:
            logger.warning("OpenAI API Error (%s): %s", self.name, e)
            try:
                content = await _generate_groq()
            except Exception: return None

        if not content:
            return None

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning("Structured Generation Parse Error (%s)", self.name)
            return None
