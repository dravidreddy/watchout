"""
Structured logging configuration for agent orchestration.
Uses structlog for better observability and debugging.
"""
import logging
import sys
from typing import Any
import structlog
from structlog.processors import JSONRenderer, TimeStamper, add_log_level
from structlog.stdlib import ProcessorFormatter


def configure_logging(log_level: str = "INFO") -> None:
    """
    Configure structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    formatter = ProcessorFormatter(
        processor=JSONRenderer(),
        foreign_pre_chain=[
            add_log_level,
            TimeStamper(fmt="iso"),
        ],
    )
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


# Agent-specific logging utilities
class AgentLogger:
    """Wrapper for agent-specific structured logging."""
    
    def __init__(self, agent_name: str):
        self.logger = get_logger(f"agent.{agent_name}")
        self.agent_name = agent_name
    
    def agent_start(self, message: str, **kwargs: Any) -> None:
        """Log agent execution start."""
        self.logger.info(
            "agent_execution_start",
            agent=self.agent_name,
            message=message,
            **kwargs
        )
    
    def agent_complete(self, duration_ms: float, **kwargs: Any) -> None:
        """Log agent execution completion."""
        self.logger.info(
            "agent_execution_complete",
            agent=self.agent_name,
            duration_ms=duration_ms,
            **kwargs
        )
    
    def agent_error(self, error: Exception, **kwargs: Any) -> None:
        """Log agent execution error."""
        self.logger.error(
            "agent_execution_error",
            agent=self.agent_name,
            error=str(error),
            error_type=type(error).__name__,
            **kwargs
        )
    
    def llm_call(self, prompt_tokens: int, completion_tokens: int, 
                 model: str, duration_ms: float, **kwargs: Any) -> None:
        """Log LLM API call metrics."""
        self.logger.info(
            "llm_api_call",
            agent=self.agent_name,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            duration_ms=duration_ms,
            **kwargs
        )
    
    def orchestration_plan(self, agents: list, parallel: bool, 
                          reasoning: str, **kwargs: Any) -> None:
        """Log orchestration planning decision."""
        self.logger.info(
            "orchestration_plan",
            agent=self.agent_name,
            agents_selected=agents,
            parallel_execution=parallel,
            reasoning=reasoning,
            **kwargs
        )
    
    def vector_search(self, query: str, results_count: int, 
                     duration_ms: float, **kwargs: Any) -> None:
        """Log vector search operation."""
        self.logger.info(
            "vector_search",
            agent=self.agent_name,
            query_length=len(query),
            results_count=results_count,
            duration_ms=duration_ms,
            **kwargs
        )
