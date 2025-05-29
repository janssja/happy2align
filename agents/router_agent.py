"""
Router agent die berichten analyseert en doorstuurt naar de juiste agent
"""

from .base_agent import BaseAgent
from typing import Dict, Any, Literal
from agents.config import ROUTER_SYSTEM_PROMPT, DEFAULT_MODEL

class RouterAgent(BaseAgent):
    """Agent die berichten analyseert en doorstuurt naar de juiste agent"""
    
    VALID_AGENT_TYPES = ["RequirementRefiner", "WorkflowRefiner"]
    
    def __init__(self, model_name: str = DEFAULT_MODEL):
        """Initialiseer de router agent"""
        super().__init__(model_name)
        self.system_prompt = ROUTER_SYSTEM_PROMPT
    
    async def process(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """Analyseer het bericht en bepaal naar welke agent het moet"""
        messages = self._format_messages(self.system_prompt, user_input)
        response = await self.llm.agenerate([messages])
        agent_type = response.generations[0][0].text.strip()
        
        # Valideer het agent type
        if agent_type not in self.VALID_AGENT_TYPES:
            # Als het type niet geldig is, gebruik RequirementRefiner als default
            return "RequirementRefiner"
            
        return agent_type 