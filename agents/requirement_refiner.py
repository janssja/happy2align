"""
Requirement Refiner agent die helpt bij het verfijnen van requirements
"""

from typing import List, Dict, Optional, Any
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferMemory
from .base_agent import BaseAgent
import json
from agents.config import REQUIREMENT_REFINER_SYSTEM_PROMPT, DEFAULT_MODEL
import logging
import asyncio

class RequirementRefiner(BaseAgent):
    """Agent die helpt bij het verfijnen van requirements"""

    def __init__(self, model_name: str = DEFAULT_MODEL):
        """Initialiseer de requirement refiner agent"""
        super().__init__(model_name)
        self.system_prompt = REQUIREMENT_REFINER_SYSTEM_PROMPT

    async def process(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """Verfijn de requirements op basis van de gebruikersinput"""
        if not context:
            context = {
                "subtopic": "initial_requirements",
                "question": "Wat zijn je belangrijkste requirements?",
                "round": 1,
                "requirements": [],
                "questions": [],
                "answers": []
            }

        # Voeg het gebruikersbericht toe aan de geschiedenis en context
        self.add_to_history("user", user_input)
        context.setdefault("answers", []).append(user_input)

        if context["round"] >= 5:
            return "Maximum aantal vragen bereikt voor dit subtopic. Ga door naar het volgende subtopic."

        # Voeg de huidige vraag toe aan de context (indien aanwezig)
        if context.get("question"):
            context.setdefault("questions", []).append(context["question"])

        # Voeg de huidige lijst van requirements toe aan de prompt
        requirements_str = "\n".join(f"- {req}" for req in context.get("requirements", []))
        questions_str = "\n".join(f"Q: {q}" for q in context.get("questions", []))
        answers_str = "\n".join(f"A: {a}" for a in context.get("answers", []))
        history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.conversation_history])

        # System prompt bevat alles
        system_message = self.system_prompt + "\n\nHuidige requirements:\n" + requirements_str + "\n\nVolledige gespreksgeschiedenis:\n" + history_str + "\n\nAlle vragen tot nu toe:\n" + questions_str + "\n\nAlle antwoorden tot nu toe:\n" + answers_str
        messages = self._format_messages(system_message, user_input)

        # Debug: print prompt info
        print(f"[AGENT] Start LLM-call met user_input: {user_input}")
        print(f"[AGENT] Lengte volledige geschiedenis: {len(history_str)} karakters")
        print(f"[AGENT] System prompt (eerste 200): {system_message[:200]}...")
        print(f"[AGENT] Messages: {messages}")

        try:
            # Timeout van 30 seconden op de LLM-call
            response = await asyncio.wait_for(self.llm.agenerate([messages]), timeout=30)
            logging.info(f"LLM response: {response}")
            print(f"[AGENT] LLM-call afgerond, response: {response}")
            response_text = response.generations[0][0].text.strip()

            # Probeer requirements uit het antwoord te halen (simpele extractie, evt. verbeteren)
            if "requirements_complete" not in response_text:
                # Voeg het hele antwoord toe als requirement (of parseer met regex/LLM)
                context.setdefault("requirements", []).append(response_text)
        except asyncio.TimeoutError:
            logging.error("LLM-call timeout! Probeer opnieuw met o4-mini-2025-04-16.")
            print("[AGENT] LLM-call timeout! Probeer opnieuw met o4-mini-2025-04-16.")
            # Probeer opnieuw met alternatief model
            try:
                from openai import OpenAI
                from agents.config import OPENAI_API_KEY
                # Bouw het messages-formaat om naar OpenAI formaat
                openai_messages = []
                for msg in messages:
                    if hasattr(msg, 'content') and hasattr(msg, 'type'):
                        role = 'system' if msg.type == 'system' else 'user'
                        openai_messages.append({"role": role, "content": msg.content})
                    elif isinstance(msg, dict):
                        role = msg.get('role', 'user')
                        openai_messages.append({"role": role, "content": msg.get('content', '')})
                client = OpenAI(api_key=OPENAI_API_KEY)
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: client.chat.completions.create(
                        model="o4-mini-2025-04-16",
                        messages=openai_messages
                    )
                )
                response_text = response.choices[0].message.content.strip()
                logging.info(f"LLM response (alt model, openai): {response_text}")
                print(f"[AGENT] LLM-call afgerond met alt model (openai), response: {response_text}")
                if "requirements_complete" not in response_text:
                    context.setdefault("requirements", []).append(response_text)
            except Exception as e:
                logging.error(f"Fout bij LLM-call met alt model (openai): {e}")
                print(f"Fout bij LLM-call met alt model (openai): {e}")
                response_text = "De AI deed er te lang over om te antwoorden, zelfs met een alternatief model. Probeer het later opnieuw."
        except Exception as e:
            logging.error(f"Fout bij LLM-call: {e}")
            print(f"Fout bij LLM-call: {e}")
            response_text = "Er ging iets mis bij het genereren van een antwoord. Probeer het opnieuw."

        # Fallback als de response leeg is
        if not response_text:
            response_text = "Ik heb je bericht ontvangen, maar kon geen antwoord genereren. Kun je het anders formuleren?"

        # Voeg de response toe aan de geschiedenis
        self.add_to_history("assistant", response_text)

        return response_text 