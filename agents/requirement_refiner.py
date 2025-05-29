"""
Requirement Refiner agent using centralized LLM client
"""

from typing import List, Dict, Optional, Any
from .base_agent import BaseAgent
from agents.config import REQUIREMENT_REFINER_SYSTEM_PROMPT
import logging

logger = logging.getLogger(__name__)

class RequirementRefiner(BaseAgent):
    """Agent that helps refine requirements"""

    def __init__(self, model_name: str = None):
        """Initialize the requirement refiner agent"""
        super().__init__(model_name)
        self.system_prompt = REQUIREMENT_REFINER_SYSTEM_PROMPT

    async def process(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """Refine requirements based on user input"""
        if not context:
            context = {
                "subtopic": "initial_requirements",
                "question": "Wat zijn je belangrijkste requirements?",
                "round": 1,
                "requirements": [],
                "questions": [],
                "answers": []
            }

        # Add user message to history and context
        self.add_to_history("user", user_input)
        context.setdefault("answers", []).append(user_input)

        if context["round"] >= 5:
            return "Maximum aantal vragen bereikt voor dit subtopic. Ga door naar het volgende subtopic."

        # Add current question to context if present
        if context.get("question"):
            context.setdefault("questions", []).append(context["question"])

        # Build context strings
        requirements_str = "\n".join(f"- {req}" for req in context.get("requirements", []))
        questions_str = "\n".join(f"Q: {q}" for q in context.get("questions", []))
        answers_str = "\n".join(f"A: {a}" for a in context.get("answers", []))
        history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.conversation_history])

        # Build complete system message
        system_message = (
            f"{self.system_prompt}\n\n"
            f"Huidige requirements:\n{requirements_str}\n\n"
            f"Volledige gespreksgeschiedenis:\n{history_str}\n\n"
            f"Alle vragen tot nu toe:\n{questions_str}\n\n"
            f"Alle antwoorden tot nu toe:\n{answers_str}"
        )
        
        messages = self._format_messages(system_message, user_input)

        logger.info(f"[RequirementRefiner] Processing with round {context['round']}")

        try:
            # Use centralized LLM client with automatic fallback
            response_text = await self.call_llm(messages)
            
            # Extract requirements from response if needed
            if "requirements_complete" not in response_text:
                context.setdefault("requirements", []).append(response_text)
                
        except Exception as e:
            logger.error(f"Error in RequirementRefiner: {e}")
            response_text = "Er ging iets mis bij het genereren van een antwoord. Probeer het opnieuw."

        # Fallback if response is empty
        if not response_text:
            response_text = "Ik heb je bericht ontvangen, maar kon geen antwoord genereren. Kun je het anders formuleren?"

        # Add response to history
        self.add_to_history("assistant", response_text)

        return response_text