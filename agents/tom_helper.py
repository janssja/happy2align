"""
Theory of Mind Helper Agent for Happy 2 Align
Provides ToM capabilities like sentiment detection and expertise estimation.
"""

from typing import Dict, Literal
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from .config import OPENAI_API_KEY, DEFAULT_MODEL

class ToMHelper:
    def __init__(self, model_name: str = DEFAULT_MODEL):
        self.llm = ChatOpenAI(
            model_name=model_name,
            openai_api_key=OPENAI_API_KEY
        )
        self.sentiment_prompt = ChatPromptTemplate.from_messages([
            ("system", """Analyze the sentiment of the following text. Return one of: POSITIVE, NEUTRAL, NEGATIVE, or MIXED.
Text: {text}"""),
            ("human", "What is the sentiment?")
        ])
        
        self.expertise_prompt = ChatPromptTemplate.from_messages([
            ("system", """Based on the following text, estimate the user's expertise level in the given domain.
Return one of: BEGINNER, INTERMEDIATE, EXPERT.

Domain: {domain}
Text: {text}"""),
            ("human", "What is the expertise level?")
        ])

    async def detect_sentiment(self, text: str) -> Literal["POSITIVE", "NEUTRAL", "NEGATIVE", "MIXED"]:
        """Detect the sentiment of a given text."""
        response = await self.llm.ainvoke(
            self.sentiment_prompt.format_messages(text=text)
        )
        return response.content.strip()

    async def estimate_expertise(self, text: str, domain: str) -> Literal["BEGINNER", "INTERMEDIATE", "EXPERT"]:
        """Estimate the user's expertise level in a given domain."""
        response = await self.llm.ainvoke(
            self.expertise_prompt.format_messages(text=text, domain=domain)
        )
        return response.content.strip() 