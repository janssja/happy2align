"""
Improved Orchestrator for Happy2Align
Implements the complete flow as specified in the conceptual design
"""

from agents.prompts import (
    ROUTER_PROMPT, REQUIREMENT_REFINER_PROMPT, WORKFLOW_GENERATOR_PROMPT,
    WORKFLOW_REFINER_PROMPT, TOPIC_DECOMPOSER_PROMPT, EXPERTISE_TOM_PROMPT, SENTIMENT_TOM_PROMPT
)
import re
import asyncio
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
import logging

logger = logging.getLogger(__name__)

class ImprovedOrchestrator:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.max_questions_per_subtopic = 5
        self.conversation_history = []
        
    async def run_conversation(self, user_input: str, conversation_history: Optional[List[Dict]] = None, 
                              current_workflow: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Main orchestration method that handles the complete flow
        """
        try:
            # Initialize conversation history if not provided
            if conversation_history is None:
                conversation_history = []
            self.conversation_history = conversation_history
            
            # Add user input to history
            self.conversation_history.append({"role": "user", "content": user_input})
            
            # Step 1: Route the query
            router_decision = await self._route(user_input)
            logger.info(f"Router decision: {router_decision}")
            
            if router_decision == "RequirementRefiner":
                return await self._handle_requirement_refinement(user_input)
            elif router_decision == "WorkflowRefiner":
                return await self._handle_workflow_refinement(user_input, current_workflow)
            else:
                return {
                    "error": f"Unknown router decision: {router_decision}",
                    "type": "error"
                }
                
        except Exception as e:
            logger.error(f"Orchestration error: {str(e)}")
            return {
                "error": str(e),
                "type": "error",
                "history": self.conversation_history
            }
    
    async def _route(self, user_input: str) -> str:
        """Route the query to the appropriate agent"""
        prompt = ROUTER_PROMPT.format(user_input=user_input)
        response = await self.llm.ainvoke(prompt)
        decision = response.content.strip()
        
        # Validate router output
        if decision not in ["RequirementRefiner", "WorkflowRefiner"]:
            # Default to RequirementRefiner for new conversations
            return "RequirementRefiner"
        return decision
    
    async def _handle_requirement_refinement(self, user_input: str) -> Dict[str, Any]:
        """Handle the requirement refinement flow"""
        # Step 2: Decompose topics
        subtopics = await self._decompose_topics(user_input)
        
        # Initialize requirements collection
        requirements = []
        all_questions_asked = []
        all_answers_received = []
        
        # Step 3: Process each subtopic
        for subtopic_idx, subtopic in enumerate(subtopics):
            subtopic_requirements = []
            
            # Process questions for this subtopic (max 5)
            for question_idx, question in enumerate(subtopic["questions"][:self.max_questions_per_subtopic]):
                # Check ToM before asking
                expertise = await self._estimate_expertise()
                sentiment = await self._detect_sentiment(user_input)
                
                # Ask clarifying question
                refined_question = await self._refine_question(
                    subtopic["title"], 
                    question, 
                    expertise,
                    sentiment
                )
                
                all_questions_asked.append(refined_question)
                
                # In a real implementation, this would wait for user response
                # For now, we'll return the question to be asked
                if subtopic_idx == 0 and question_idx == 0:
                    return {
                        "type": "question",
                        "question": refined_question,
                        "subtopic": subtopic["title"],
                        "subtopic_index": subtopic_idx,
                        "question_index": question_idx,
                        "total_subtopics": len(subtopics),
                        "expertise": expertise,
                        "sentiment": sentiment,
                        "history": self.conversation_history
                    }
        
        # Step 4: Generate workflow from requirements
        workflow = await self._generate_workflow(requirements)
        
        return {
            "type": "workflow",
            "workflow": workflow,
            "requirements": requirements,
            "questions_asked": all_questions_asked,
            "history": self.conversation_history
        }
    
    async def _handle_workflow_refinement(self, user_input: str, current_workflow: Optional[List[str]]) -> Dict[str, Any]:
        """Handle workflow refinement requests"""
        if not current_workflow:
            return {
                "type": "error",
                "error": "No current workflow to refine. Please create requirements first.",
                "history": self.conversation_history
            }
        
        refined_workflow = await self._refine_workflow(current_workflow, user_input)
        
        return {
            "type": "workflow_refined",
            "workflow": refined_workflow,
            "modification": user_input,
            "history": self.conversation_history
        }
    
    async def _decompose_topics(self, user_request: str) -> List[Dict[str, Any]]:
        """Decompose user request into subtopics with questions"""
        prompt = TOPIC_DECOMPOSER_PROMPT.format(user_request=user_request)
        response = await self.llm.ainvoke(prompt)
        output = response.content
        
        # Parse subtopics and questions
        subtopics = []
        current = None
        
        for line in output.splitlines():
            line = line.strip()
            # Match subtopic pattern
            subtopic_match = re.match(r"- Subtopic \d+: (.+)", line)
            if subtopic_match:
                if current:
                    subtopics.append(current)
                current = {"title": subtopic_match.group(1), "questions": []}
            # Match question pattern
            elif current and (line.startswith("- Q") or line.startswith("Q")):
                question = line.split(":", 1)[-1].strip()
                if question:
                    current["questions"].append(question)
        
        if current:
            subtopics.append(current)
        
        # Ensure we have at least one subtopic
        if not subtopics:
            subtopics = [{
                "title": "General Requirements",
                "questions": [
                    "What is the main goal of your project?",
                    "Who are the primary users?",
                    "What are the key features you need?",
                    "What is your timeline?",
                    "What are your technical constraints?"
                ]
            }]
        
        return subtopics
    
    async def _refine_question(self, subtopic: str, question: str, expertise: str, sentiment: str) -> str:
        """Refine a question based on ToM insights"""
        # Build conversation context
        conv_str = "\n".join(f"{msg['role']}: {msg['content']}" for msg in self.conversation_history)
        
        # Add ToM context to the prompt
        enhanced_prompt = f"""{REQUIREMENT_REFINER_PROMPT}

Current user expertise level: {expertise}
Current user sentiment: {sentiment}

Adjust your question complexity and tone accordingly:
- For BEGINNER: Use simple language and provide examples
- For INTERMEDIATE: Use standard technical terms
- For EXPERT: Be concise and technical

- For POSITIVE sentiment: Maintain enthusiasm
- For NEUTRAL sentiment: Be professional
- For NEGATIVE sentiment: Be empathetic and helpful"""
        
        prompt = enhanced_prompt.format(
            subtopic=subtopic,
            question=question,
            conversation=conv_str
        )
        
        response = await self.llm.ainvoke(prompt)
        return response.content.strip()
    
    async def _estimate_expertise(self) -> str:
        """Estimate user expertise based on conversation"""
        conv_str = "\n".join(f"{msg['role']}: {msg['content']}" for msg in self.conversation_history)
        prompt = EXPERTISE_TOM_PROMPT.format(conversation=conv_str)
        response = await self.llm.ainvoke(prompt)
        expertise = response.content.strip()
        
        # Validate expertise level
        if expertise not in ["BEGINNER", "INTERMEDIATE", "EXPERT"]:
            expertise = "INTERMEDIATE"  # Default
        
        return expertise
    
    async def _detect_sentiment(self, latest_message: str) -> str:
        """Detect sentiment from conversation"""
        conv_str = "\n".join(f"{msg['role']}: {msg['content']}" for msg in self.conversation_history)
        prompt = SENTIMENT_TOM_PROMPT.format(
            conversation=conv_str,
            latest_message=latest_message
        )
        response = await self.llm.ainvoke(prompt)
        sentiment = response.content.strip()
        
        # Validate sentiment
        if sentiment not in ["POSITIVE", "NEUTRAL", "NEGATIVE", "MIXED"]:
            sentiment = "NEUTRAL"  # Default
        
        return sentiment
    
    async def _generate_workflow(self, requirements: List[Dict[str, Any]]) -> List[str]:
        """Generate workflow from requirements"""
        # Format requirements for the prompt
        req_str = "\n".join(f"- {r.get('subtopic', 'General')}: {r.get('answer', '')}" for r in requirements)
        
        prompt = WORKFLOW_GENERATOR_PROMPT.format(requirements=req_str)
        response = await self.llm.ainvoke(prompt)
        output = response.content
        
        # Parse workflow steps
        steps = []
        for line in output.splitlines():
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-")):
                # Clean up the line
                step = re.sub(r"^\d+\.\s*", "", line)
                step = re.sub(r"^-\s*", "", step)
                if step:
                    steps.append(step)
        
        # Ensure we have at least some steps
        if not steps:
            steps = [
                "Define project objectives and scope",
                "Identify stakeholders and gather requirements",
                "Design system architecture",
                "Implement core functionality",
                "Test and validate the solution",
                "Deploy and monitor the system"
            ]
        
        return steps
    
    async def _refine_workflow(self, workflow: List[str], modification: str) -> List[str]:
        """Refine existing workflow based on user input"""
        workflow_str = "\n".join(f"{i+1}. {step}" for i, step in enumerate(workflow))
        
        prompt = WORKFLOW_REFINER_PROMPT.format(
            workflow=workflow_str,
            modification=modification
        )
        
        response = await self.llm.ainvoke(prompt)
        output = response.content
        
        # Parse refined workflow
        steps = []
        for line in output.splitlines():
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-")):
                step = re.sub(r"^\d+\.\s*", "", line)
                step = re.sub(r"^-\s*", "", step)
                if step:
                    steps.append(step)
        
        return steps if steps else workflow  # Fallback to original if parsing fails

# Synchronous wrapper for compatibility
class Orchestrator:
    """Synchronous wrapper for the ImprovedOrchestrator"""
    
    def __init__(self, llm):
        self.async_orchestrator = ImprovedOrchestrator(llm)
    
    def run_conversation(self, user_input: str, conversation_history: Optional[List[Dict]] = None,
                        current_workflow: Optional[List[str]] = None) -> Dict[str, Any]:
        """Synchronous wrapper for async orchestrator"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.async_orchestrator.run_conversation(user_input, conversation_history, current_workflow)
            )
        finally:
            loop.close()