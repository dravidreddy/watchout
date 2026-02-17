"""
Enhanced Supervisor Agent Example
Demonstrates how to integrate TypedDict, structured logging, and retry logic
into the existing supervisor agent.

This is a reference implementation showing the recommended patterns.
You can gradually migrate your existing supervisor.py to use these patterns.
"""
from typing import Dict, Any, Optional, List
import asyncio
import time

from app.agents.base import BaseAgent
from app.models.agent_types import (
    TravelPreferences,
    AgentContext,
    OrchestrationPlan,
    AgentResponse,
    StreamEvent
)
from app.core.logging_config import AgentLogger
from app.core.retry_utils import with_retry, with_timeout, LLM_RETRY_CONFIG


class EnhancedSupervisorAgent(BaseAgent):
    """
    Enhanced supervisor with type safety, logging, and retry logic.
    """
    
    def __init__(self):
        super().__init__(
            name="Enhanced Travel Supervisor",
            description="Supervisor agent with production-grade enhancements",
            model_type="main"
        )
        # Structured logging
        self.logger = AgentLogger("supervisor")
    
    @with_timeout(30.0)  # 30s timeout for orchestration planning
    @with_retry(**LLM_RETRY_CONFIG)  # Retry with exponential backoff
    async def _plan_orchestration(
        self,
        message: str,
        preferences: TravelPreferences,
        memories: List[Dict],
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> OrchestrationPlan:
        """
        Enhanced orchestration planning with logging and retries.
        
        Returns:
            OrchestrationPlan TypedDict with agents, parallel flag, and reasoning
        """
        start_time = time.time()
        
        self.logger.agent_start(
            message=message,
            preferences_count=len(preferences),
            memories_count=len(memories)
        )
        
        # Your existing LLM call logic here
        # ... (same as current implementation)
        
        # Example result
        plan: OrchestrationPlan = {
            "agents": ["itinerary", "food", "stay"],
            "parallel": True,
            "reasoning": "User has complete preferences, can plan full itinerary"
        }
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Log the orchestration plan
        self.logger.orchestration_plan(
            agents=plan["agents"],
            parallel=plan["parallel"],
            reasoning=plan["reasoning"],
            duration_ms=duration_ms
        )
        
        return plan
    
    async def _run_single_agent_enhanced(
        self,
        agent_name: str,
        message: str,
        context: AgentContext
    ) -> Optional[AgentResponse]:
        """
        Enhanced single agent runner with logging and metrics.
        
        Returns:
            AgentResponse TypedDict with standardized structure
        """
        start_time = time.time()
        
        self.logger.agent_start(
            message=f"Running {agent_name} agent",
            agent=agent_name
        )
        
        try:
            # Your existing agent execution logic
            # agent = self.agents.get(agent_name)
            # result = await agent.run(message, context)
            
            # Example result with TypedDict
            result: AgentResponse = {
                "response": "Sample response from agent",
                "itinerary": None,
                "is_complete": True
            }
            
            duration_ms = (time.time() - start_time) * 1000
            
            self.logger.agent_complete(
                duration_ms=duration_ms,
                agent=agent_name,
                has_structured_data=bool(result.get("itinerary"))
            )
            
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            self.logger.agent_error(
                error=e,
                agent=agent_name,
                duration_ms=duration_ms
            )
            
            # Return error response
            return {
                "response": f"Error in {agent_name}: {str(e)}",
                "is_complete": False
            }
    
    async def _run_agents_parallel_enhanced(
        self,
        agent_names: List[str],
        message: str,
        context: AgentContext
    ) -> tuple[Dict[str, str], Dict[str, Any]]:
        """
        Enhanced parallel execution with better logging.
        """
        start_time = time.time()
        
        self.logger.agent_start(
            message="Starting parallel agent execution",
            agents=agent_names,
            agent_count=len(agent_names)
        )
        
        # Create tasks
        tasks = [
            self._run_single_agent_enhanced(agent_name, message, context)
            for agent_name in agent_names
        ]
        
        # Execute in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        responses: Dict[str, str] = {}
        structured_data: Dict[str, Any] = {}
        
        for agent_name, result in zip(agent_names, results):
            if isinstance(result, Exception):
                self.logger.agent_error(
                    error=result,
                    agent=agent_name
                )
                responses[agent_name] = f"Error: {str(result)}"
            elif result:
                responses[agent_name] = result.get("response", "")
                # Collect structured data
                for key in ["itinerary", "weather", "restaurants"]:
                    if result.get(key):
                        structured_data[key] = result[key]
        
        duration_ms = (time.time() - start_time) * 1000
        
        self.logger.agent_complete(
            duration_ms=duration_ms,
            agents=agent_names,
            successful_agents=len([r for r in results if not isinstance(r, Exception)]),
            failed_agents=len([r for r in results if isinstance(r, Exception)])
        )
        
        return responses, structured_data


# Example usage showing type safety benefits
async def example_usage():
    """Demonstrates type-safe usage of enhanced supervisor."""
    supervisor = EnhancedSupervisorAgent()
    
    # Type-safe preferences (IDE will autocomplete fields!)
    preferences: TravelPreferences = {
        "destinations": ["Goa", "Mumbai"],
        "duration_days": 5,
        "num_travelers": 2,
        "budget_range": "moderate",
        "travel_vibe": "relaxation"
    }
    
    # Type-safe context
    context: AgentContext = {
        "preferences": preferences,
        "memories": [],
        "conversation_history": []
    }
    
    # Type-safe orchestration plan
    plan: OrchestrationPlan = await supervisor._plan_orchestration(
        message="Plan a 5-day trip to Goa",
        preferences=preferences,
        memories=[],
        conversation_history=[]
    )
    
    print(f"Selected agents: {plan['agents']}")
    print(f"Parallel execution: {plan['parallel']}")
    print(f"Reasoning: {plan['reasoning']}")


if __name__ == "__main__":
    # Configure logging before running
    from app.core.logging_config import configure_logging
    configure_logging(log_level="INFO")
    
    asyncio.run(example_usage())
