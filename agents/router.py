"""
Router Agent for Happy 2 Align with timeout and fallback support
"""

from typing import Literal, Dict, Any
from langchain.prompts import ChatPromptTemplate
from .config import DEFAULT_MODEL
from .base_agent import BaseAgent
import logging

logger = logging.getLogger(__name__)

class RouterAgent(BaseAgent):
    def __init__(self, model_name: str = DEFAULT_MODEL):
        super().__init__(model_name)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a router agent in a multi-agent AI assistant. Based on the user's message and the current context, decide whether the query is:
- about refining or clarifying requirements → return "RequirementRefiner"
- about modifying or improving a generated workflow → return "WorkflowRefiner"

Only return one word: RequirementRefiner or WorkflowRefiner."""),
            ("human", "{user_input}")
        ])

    async def process(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """Route the user query to the appropriate agent with timeout handling."""
        try:
            # Format messages
            messages = self.prompt.format_messages(user_input=user_input)
            
            # Call LLM with timeout and fallback
            response = await self._call_llm_with_timeout(messages, use_fallback=True)
            
            # Validate response
            agent_type = response.strip()
            if agent_type not in ["RequirementRefiner", "WorkflowRefiner"]:
                logger.warning(f"Invalid router response: {agent_type}, defaulting to RequirementRefiner")
                return "RequirementRefiner"
            
            return agent_type
            
        except TimeoutError:
            # Bij timeout, kijk naar context om te beslissen
            logger.error("Router timeout, using context-based decision")
            if context and context.get('current_workflow'):
                return "WorkflowRefiner"
            return "RequirementRefiner"
            
        except Exception as e:
            logger.error(f"Router error: {str(e)}, defaulting to RequirementRefiner")
            return "RequirementRefiner"

    async def route_query(self, user_input: str) -> Literal["RequirementRefiner", "WorkflowRefiner"]:
        """Legacy method for backward compatibility."""
        return await self.process(user_input)

# Create a singleton instance
_router = RouterAgent()

# Export the route_query function
async def route_query(user_input: str) -> Literal["RequirementRefiner", "WorkflowRefiner"]:
    """Route a user query to the appropriate agent."""
    return await _router.route_query(user_input)