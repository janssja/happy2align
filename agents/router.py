"""
Router Agent for Happy 2 Align
Routes user queries to the appropriate specialized agent.
"""

from typing import Literal
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from .config import OPENAI_API_KEY, DEFAULT_MODEL

class RouterAgent:
    def __init__(self, model_name: str = DEFAULT_MODEL):
        self.llm = ChatOpenAI(
            model_name=model_name,
            openai_api_key=OPENAI_API_KEY
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a router agent in a multi-agent AI assistant. Based on the user's message and the current context, decide whether the query is:
- about refining or clarifying requirements → return "RequirementRefiner"
- about modifying or improving a generated workflow → return "WorkflowRefiner"

Only return one word: RequirementRefiner or WorkflowRefiner."""),
            ("human", "{user_input}")
        ])

    async def route_query(self, user_input: str) -> Literal["RequirementRefiner", "WorkflowRefiner"]:
        """Route the user query to the appropriate agent."""
        response = await self.llm.ainvoke(self.prompt.format_messages(user_input=user_input))
        return response.content.strip()

# Create a singleton instance
_router = RouterAgent()

# Export the route_query function
async def route_query(user_input: str) -> Literal["RequirementRefiner", "WorkflowRefiner"]:
    """Route a user query to the appropriate agent."""
    return await _router.route_query(user_input) 