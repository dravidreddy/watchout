"""
Retry utilities for resilient LLM API calls.
Implements exponential backoff with jitter for API failures.
"""
from typing import TypeVar, Callable, Any
from functools import wraps
import asyncio
import random
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log
)
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


# Common exceptions to retry
RETRYABLE_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    # Add provider-specific exceptions here when identified
)


def with_retry(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 10.0,
    exceptions: tuple = RETRYABLE_EXCEPTIONS
):
    """
    Decorator for retrying async functions with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time in seconds
        max_wait: Maximum wait time in seconds
        exceptions: Tuple of exceptions to retry on
    
    Example:
        @with_retry(max_attempts=3)
        async def call_llm_api():
            ...
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(exceptions),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO)
    )


def with_timeout(seconds: float):
    """
    Decorator for adding timeout to async functions.
    
    Args:
        seconds: Timeout duration in seconds
    
    Example:
        @with_timeout(30.0)
        async def slow_operation():
            ...
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=seconds
                )
            except asyncio.TimeoutError:
                logger.error(
                    f"Function {func.__name__} timed out after {seconds}s"
                )
                raise
        return wrapper
    return decorator


class CircuitBreaker:
    """
    Simple circuit breaker for API calls.
    Opens after consecutive failures and closes after timeout.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open
    
    async def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Async function to execute
            *args, **kwargs: Arguments for the function
        
        Returns:
            Function result
        
        Raises:
            Exception: If circuit is open
        """
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half_open"
            else:
                raise Exception(
                    f"Circuit breaker is OPEN. Too many failures. "
                    f"Try again after {self.recovery_timeout}s"
                )
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self) -> None:
        """Handle successful call."""
        self.failure_count = 0
        self.state = "closed"
    
    def _on_failure(self) -> None:
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = asyncio.get_event_loop().time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.error(
                f"Circuit breaker OPENED after {self.failure_count} failures"
            )
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return False
        
        current_time = asyncio.get_event_loop().time()
        return (current_time - self.last_failure_time) >= self.recovery_timeout


# Retry configuration for different operation types
LLM_RETRY_CONFIG = {
    "max_attempts": 3,
    "min_wait": 1.0,
    "max_wait": 10.0
}

VECTOR_SEARCH_RETRY_CONFIG = {
    "max_attempts": 2,
    "min_wait": 0.5,
    "max_wait": 5.0
}

DATABASE_RETRY_CONFIG = {
    "max_attempts": 3,
    "min_wait": 0.5,
    "max_wait": 5.0
}
