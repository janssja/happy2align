from agents.prompts import (
    ROUTER_PROMPT, REQUIREMENT_REFINER_PROMPT, WORKFLOW_GENERATOR_PROMPT,
    WORKFLOW_REFINER_PROMPT, TOPIC_DECOMPOSER_PROMPT, EXPERTISE_TOM_PROMPT, SENTIMENT_TOM_PROMPT
)

import re

class Orchestrator:
    def __init__(self, llm):
        self.llm = llm  # Bijvoorbeeld een LangChain LLM of OpenAI client

    def run_conversation(self, user_input, conversation_history=None, current_workflow=None):
        conversation_history = conversation_history or []
        # 1. Router
        router_decision = self.route(user_input, conversation_history)
        if router_decision == "RequirementRefiner":
            # 2. Topic Decomposer
            subtopics = self.decompose_topics(user_input)
            requirements = []
            for subtopic in subtopics:
                for question in subtopic["questions"]:
                    # 3. Requirement Refiner
                    answer = self.refine_requirement(subtopic["title"], question, conversation_history)
                    conversation_history.append({"role": "user", "content": answer})
                    # 4. ToM Helpers na elk antwoord
                    expertise = self.estimate_expertise(conversation_history)
                    sentiment = self.detect_sentiment(conversation_history, answer)
                    requirements.append({"subtopic": subtopic["title"], "answer": answer, "expertise": expertise, "sentiment": sentiment})
            # 5. Workflow Generator
            workflow = self.generate_workflow(requirements)
            return {
                "type": "workflow",
                "workflow": workflow,
                "requirements": requirements,
                "history": conversation_history
            }
        elif router_decision == "WorkflowRefiner":
            # 6. Workflow Refiner
            updated_workflow = self.refine_workflow(current_workflow, user_input)
            return {
                "type": "workflow_refined",
                "workflow": updated_workflow,
                "history": conversation_history
            }
        else:
            return {"error": "Router kon geen pad bepalen."}

    def route(self, user_input, context):
        prompt = ROUTER_PROMPT.format(user_input=user_input)
        return self.llm.invoke(prompt).content.strip()

    def decompose_topics(self, user_request):
        prompt = TOPIC_DECOMPOSER_PROMPT.format(user_request=user_request)
        output = self.llm.invoke(prompt).content
        # Parseer subtopics en vragen uit de output
        subtopics = []
        current = None
        for line in output.splitlines():
            line = line.strip()
            m = re.match(r"- Subtopic \d+: (.+)", line)
            if m:
                if current:
                    subtopics.append(current)
                current = {"title": m.group(1), "questions": []}
            elif line.startswith("- Q") or line.startswith("Q"):
                q = line.split(":", 1)[-1].strip()
                if current and q:
                    current["questions"].append(q)
        if current:
            subtopics.append(current)
        return subtopics

    def refine_requirement(self, subtopic, question, conversation):
        # conversation is een lijst van dicts, maak er een string van
        conv_str = "\n".join(f"{msg['role']}: {msg['content']}" for msg in conversation)
        prompt = REQUIREMENT_REFINER_PROMPT.format(subtopic=subtopic, question=question, conversation=conv_str)
        return self.llm.invoke(prompt).content.strip()

    def generate_workflow(self, requirements):
        # requirements is een lijst van dicts, maak er een string van
        req_str = "\n".join(f"- {r['subtopic']}: {r['answer']}" for r in requirements)
        prompt = WORKFLOW_GENERATOR_PROMPT.format(requirements=req_str)
        output = self.llm.invoke(prompt).content
        # Parseer als lijst van stappen
        steps = [line.strip() for line in output.splitlines() if line.strip() and line[0].isdigit()]
        return steps

    def refine_workflow(self, workflow, modification):
        # workflow is een lijst van stappen
        workflow_str = "\n".join(workflow)
        prompt = WORKFLOW_REFINER_PROMPT.format(workflow=workflow_str, modification=modification)
        output = self.llm.invoke(prompt).content
        steps = [line.strip() for line in output.splitlines() if line.strip() and line[0].isdigit()]
        return steps

    def estimate_expertise(self, conversation):
        conv_str = "\n".join(f"{msg['role']}: {msg['content']}" for msg in conversation)
        prompt = EXPERTISE_TOM_PROMPT.format(conversation=conv_str)
        return self.llm.invoke(prompt).content.strip()

    def detect_sentiment(self, conversation, latest_message):
        conv_str = "\n".join(f"{msg['role']}: {msg['content']}" for msg in conversation)
        prompt = SENTIMENT_TOM_PROMPT.format(conversation=conv_str, latest_message=latest_message)
        return self.llm.invoke(prompt).content.strip()

    # Voeg hier de orchestratie-flow toe volgens de MVP-logica
    # (zie jouw conceptuele flow in de prompt) 