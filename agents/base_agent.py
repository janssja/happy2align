"""
Simplified Base Agent using centralized LLM client
"""

from typing import Dict, Any, Optional, List, Union
from langchain.schema import HumanMessage, SystemMessage
from agents.llm_client import llm_client
import logging

logger = logging.getLogger(__name__)

class BaseAgent:
    """Base agent class using centralized LLM client"""
    
    def __init__(self, model_name: str = None):
        """Initialize the agent"""
        self.llm_client = llm_client
        self.context: Dict[str, Any] = {}
        self.system_prompt: str = ""
        self.conversation_history: List[Dict[str, str]] = []
        self.model_name = model_name  # For specific model overrides if needed
    
    async def process(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Process a message - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement this method")
    
    async def call_llm(self, messages: List[Union[SystemMessage, HumanMessage]], **kwargs) -> str:
        """
        Call LLM using centralized client
        
        Args:
            messages: List of messages
            **kwargs: Additional arguments for the LLM
            
        Returns:
            Response text from the LLM
        """
        return await self.llm_client.call_async(messages, **kwargs)
    
    def call_llm_sync(self, messages: List[Union[SystemMessage, HumanMessage]], **kwargs) -> str:
        """
        Synchronous call to LLM using centralized client
        
        Args:
            messages: List of messages
            **kwargs: Additional arguments for the LLM
            
        Returns:
            Response text from the LLM
        """
        return self.llm_client.call_sync(messages, **kwargs)
    
    def update_context(self, new_context: Dict[str, Any]) -> None:
        """Update the agent's context"""
        self.context.update(new_context)
    
    def clear_context(self) -> None:
        """Clear the agent's context"""
        self.context.clear()
        
    def _format_messages(self, system_prompt: str, user_input: str) -> List[Union[SystemMessage, HumanMessage]]:
        """Format messages for the LLM"""
        return [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_input)
        ]
        
    def add_to_history(self, role: str, content: str) -> None:
        """Add a message to conversation history"""
        self.conversation_history.append({"role": role, "content": content})
        
    def get_context(self) -> str:
        """Get conversation history as string"""
        return "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.conversation_history])
        
    def clear_history(self) -> None:
        """Clear conversation history"""
        self.conversation_history.clear()