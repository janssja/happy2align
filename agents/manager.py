"""
Agent Manager using centralized LLM client
"""

from typing import List, Dict, Optional
from .router import RouterAgent
from .requirement_refiner import RequirementRefiner
from .workflow_generator import WorkflowGenerator
from .tom_helper import ToMHelper
from agents.llm_client import llm_client
import asyncio
import logging

logger = logging.getLogger(__name__)

class AgentManager:
    def __init__(self, model_name: str = None):
        self.router = RouterAgent(model_name)
        self.requirement_refiner = RequirementRefiner(model_name)
        self.workflow_generator = WorkflowGenerator(model_name)
        self.tom_helper = ToMHelper(model_name)
        self.llm_client = llm_client  # Use centralized client
        
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
        
        # Agent status tracking
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
        try:
            agent_type = await self.router.route_query(user_input)
            self.router_status = "active"
        except Exception as e:
            logger.error(f"Router failed: {e}")
            self.router_status = "error"
            agent_type = "RequirementRefiner"  # Default fallback
            
        self.context["current_agent"] = agent_type
        self.active_agent = agent_type
        
        # Get sentiment and expertise level
        self.tom_helper_status = "waiting"
        try:
            sentiment = await self.tom_helper.detect_sentiment(user_input)
            expertise = await self.tom_helper.estimate_expertise(user_input, "software development")
            self.tom_helper_status = "active"
            self.context["sentiments"].append(sentiment)
            self.context["expertise"].append(expertise)
        except Exception as e:
            logger.error(f"ToM helpers failed: {e}")
            self.tom_helper_status = "error"
            sentiment = "NEUTRAL"
            expertise = "INTERMEDIATE"
        
        # Process via appropriate agent
        response = None
        
        if agent_type == "RequirementRefiner":
            self.requirement_refiner_status = "waiting"
            try:
                response = await self.requirement_refiner.process(user_input, self.context)
                self.requirement_refiner_status = "active"
                self.context["questions"].append(self.context.get("question", "What are your main requirements?"))
                if "requirements_complete" not in response:
                    self.context["requirements"].append(response)
                self.context["round"] = self.context.get("round", 1) + 1
            except Exception as e:
                self.requirement_refiner_status = "error"
                logger.error(f"RequirementRefiner failed: {e}")
                response = "Er ging iets mis bij het verfijnen van de requirements. Probeer het opnieuw."
                
        elif agent_type == "WorkflowRefiner":
            self.workflow_generator_status = "waiting"
            try:
                response = await self.workflow_generator.process(user_input, self.context)
                self.workflow_generator_status = "active"
            except Exception as e:
                self.workflow_generator_status = "error"
                logger.error(f"WorkflowGenerator failed: {e}")
                response = "Er ging iets mis bij het genereren van de workflow. Probeer het opnieuw."
        else:
            response = "Onbekende agent: " + str(agent_type)
        
        # Add response to conversation history
        self.conversation_history.append({"role": "assistant", "content": response})
        
        # Get status overview
        status = self.get_status()
        
        return {
            "response": response,
            "active_agent": self.active_agent,
            "context": self.context,
            "history": self.conversation_history,
            "status": status,
            "sentiment": sentiment,
            "expertise": expertise
        }

    def get_status(self) -> Dict[str, any]:
        """Get current status of all agents"""
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
    
    async def health_check(self) -> Dict[str, any]:
        """Check health of all components"""
        # Use centralized client's health check
        llm_health = await self.llm_client.health_check()
        
        return {
            "manager": "healthy",
            "llm_client": llm_health,
            "agents": {
                "router": "ready",
                "requirement_refiner": "ready",
                "workflow_generator": "ready",
                "tom_helper": "ready"
            }
        }