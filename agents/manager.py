"""
Agent Manager for Happy 2 Align
Coordinates all agents and manages the conversation flow.
"""

from typing import List, Dict, Optional
from .router import RouterAgent
from .requirement_refiner import RequirementRefiner
from .workflow_generator import WorkflowGenerator
from .tom_helper import ToMHelper
import asyncio
from openai import OpenAI
from agents.config import OPENAI_API_KEY

class AgentManager:
    def __init__(self, model_name: str = "gpt-4"):
        self.router = RouterAgent(model_name)
        self.requirement_refiner = RequirementRefiner(model_name)
        self.workflow_generator = WorkflowGenerator(model_name)
        self.tom_helper = ToMHelper(model_name)
        self.conversation_history: List[Dict[str, str]] = []
        self.context: Dict[str, any] = {
            "requirements": [],
            "questions": [],
            "answers": [],
            "sentiments": [],
            "expertise": [],
            "current_agent": None,
            "round": 1
        }
        self.active_agent = None
        # Voeg status per agent toe
        self.router_status = "inactive"
        self.requirement_refiner_status = "inactive"
        self.workflow_generator_status = "inactive"
        self.tom_helper_status = "inactive"

    async def process_query(self, user_input: str, context: Optional[Dict[str, any]] = None) -> Dict[str, any]:
        """Process a user query through the appropriate agents."""
        # Add user input to conversation history
        self.conversation_history.append({"role": "user", "content": user_input})
        self.context["answers"].append(user_input)
        
        # Route the query
        self.router_status = "waiting"
        agent_type = await self.router.route_query(user_input)
        self.router_status = "active"
        self.context["current_agent"] = agent_type
        self.active_agent = agent_type
        
        # Get sentiment and expertise level
        self.tom_helper_status = "waiting"
        sentiment = await self.tom_helper.detect_sentiment(user_input)
        expertise = await self.tom_helper.estimate_expertise(user_input, "software development")
        self.tom_helper_status = "active"
        self.context["sentiments"].append(sentiment)
        self.context["expertise"].append(expertise)
        
        # Verwerk via juiste agent met fallback
        response = None
        if agent_type == "RequirementRefiner":
            self.requirement_refiner_status = "waiting"
            try:
                response = await asyncio.wait_for(self.requirement_refiner.process(user_input, self.context), timeout=30)
                self.requirement_refiner_status = "active"
                self.context["questions"].append(self.context.get("question", "What are your main requirements?"))
                if "requirements_complete" not in response:
                    self.context["requirements"].append(response)
                self.context["round"] = self.context.get("round", 1) + 1
            except asyncio.TimeoutError:
                self.requirement_refiner_status = "error"
                response = await self._fallback_openai_call(user_input, self.context, agent_type)
            except Exception as e:
                self.requirement_refiner_status = "error"
                response = f"Fout bij RequirementRefiner: {e}"
        elif agent_type == "WorkflowRefiner":
            self.workflow_generator_status = "waiting"
            try:
                response = await asyncio.wait_for(self.workflow_generator.process(user_input, self.context), timeout=30)
                self.workflow_generator_status = "active"
            except asyncio.TimeoutError:
                self.workflow_generator_status = "error"
                response = await self._fallback_openai_call(user_input, self.context, agent_type)
            except Exception as e:
                self.workflow_generator_status = "error"
                response = f"Fout bij WorkflowGenerator: {e}"
        else:
            response = "Onbekende agent: " + str(agent_type)
        
        # Add response to conversation history
        self.conversation_history.append({"role": "assistant", "content": response})
        
        # Statusoverzicht
        status = self.get_status()
        return {
            "response": response,
            "active_agent": self.active_agent,
            "context": self.context,
            "history": self.conversation_history,
            "status": status
        }

    async def _fallback_openai_call(self, user_input, context, agent_type):
        try:
            # Bouw prompt op zoals in de agent
            if agent_type == "RequirementRefiner":
                from agents.requirement_refiner import REQUIREMENT_REFINER_SYSTEM_PROMPT
                requirements_str = "\n".join(f"- {req}" for req in context.get("requirements", []))
                questions_str = "\n".join(f"Q: {q}" for q in context.get("questions", []))
                answers_str = "\n".join(f"A: {a}" for a in context.get("answers", []))
                history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.conversation_history])
                system_message = REQUIREMENT_REFINER_SYSTEM_PROMPT + "\n\nHuidige requirements:\n" + requirements_str + "\n\nVolledige gespreksgeschiedenis:\n" + history_str + "\n\nAlle vragen tot nu toe:\n" + questions_str + "\n\nAlle antwoorden tot nu toe:\n" + answers_str
            else:
                from agents.config import WORKFLOW_GENERATOR_SYSTEM_PROMPT
                system_message = WORKFLOW_GENERATOR_SYSTEM_PROMPT
            openai_messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_input}
            ]
            client = OpenAI(api_key=OPENAI_API_KEY)
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.chat.completions.create(
                    model="o4-mini-2025-04-16",
                    messages=openai_messages
                )
            )
            response_text = response.choices[0].message.content.strip()
            return response_text
        except Exception as e:
            return f"De fallback AI deed er te lang over of faalde: {e}"

    def get_status(self) -> Dict[str, any]:
        return {
            "manager": "active",
            "router": self.router_status,
            "requirement_refiner": self.requirement_refiner_status,
            "workflow_generator": self.workflow_generator_status,
            "tom_helper": self.tom_helper_status,
            "active_agent": self.active_agent,
            "context": self.context,
            "history": self.conversation_history
        } 