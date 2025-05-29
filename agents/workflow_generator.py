"""
Workflow Generator agent die helpt bij het genereren van workflows
"""

from typing import List, Dict, Any
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from .base_agent import BaseAgent
from agents.config import WORKFLOW_GENERATOR_SYSTEM_PROMPT, DEFAULT_MODEL

class WorkflowGenerator(BaseAgent):
    """Agent die helpt bij het genereren van workflows"""
    
    def __init__(self, model_name: str = DEFAULT_MODEL):
        """Initialiseer de workflow generator agent"""
        super().__init__(model_name)
        self.system_prompt = WORKFLOW_GENERATOR_SYSTEM_PROMPT

    async def process(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """Genereer een workflow op basis van de requirements"""
        if not context:
            context = {"requirements": user_input}
            
        messages = self._format_messages(self.system_prompt, user_input)
        response = await self.llm.agenerate([messages])
        return response.generations[0][0].text.strip() 