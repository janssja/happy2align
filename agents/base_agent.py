"""
Basis agent klasse voor alle agents in het systeem
"""

from typing import Dict, Any, Optional, List
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from agents.config import OPENAI_API_KEY, DEFAULT_MODEL, DEFAULT_TEMPERATURE

class BaseAgent:
    """Basis agent klasse met gedeelde functionaliteit"""
    
    def __init__(self, model_name: str = DEFAULT_MODEL):
        """Initialiseer de agent met een specifiek model"""
        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=DEFAULT_TEMPERATURE,
            api_key=OPENAI_API_KEY
        )
        self.context: Dict[str, Any] = {}
        self.system_prompt: str = ""
        self.conversation_history: List[Dict[str, str]] = []
    
    async def process(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Verwerk een bericht en geef een response terug"""
        raise NotImplementedError("Subclasses moeten deze methode implementeren")
    
    def update_context(self, new_context: Dict[str, Any]) -> None:
        """Update de context van de agent"""
        self.context.update(new_context)
    
    def clear_context(self) -> None:
        """Wis de context van de agent"""
        self.context.clear()
        
    def _format_messages(self, system_prompt: str, user_input: str) -> List[Dict[str, str]]:
        """Formatteer de berichten voor de LLM"""
        return [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_input)
        ]
        
    def add_to_history(self, role: str, content: str) -> None:
        """Voeg een bericht toe aan de gespreksgeschiedenis"""
        self.conversation_history.append({"role": role, "content": content})
        
    def get_context(self) -> str:
        """Haal de gespreksgeschiedenis op als string"""
        return "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.conversation_history])
        
    def clear_history(self) -> None:
        """Wis de gespreksgeschiedenis"""
        self.conversation_history.clear() 