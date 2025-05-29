"""
FastAPI application for Happy 2 Align
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uvicorn
from agents.router_agent import RouterAgent
from agents.requirement_refiner import RequirementRefiner
from agents.workflow_generator import WorkflowGenerator

app = FastAPI(title="Happy 2 Align API")

class UserInput(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None

class AgentResponse(BaseModel):
    response: str
    next_agent: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

router_agent = RouterAgent()
requirement_refiner = RequirementRefiner()
workflow_generator = WorkflowGenerator()

@app.post("/process", response_model=AgentResponse)
async def process_input(user_input: UserInput):
    try:
        # Route the input to the appropriate agent
        agent_type = await router_agent.process(user_input.message)
        
        if agent_type == "RequirementRefiner":
            response = await requirement_refiner.process(user_input.message, user_input.context)
            return AgentResponse(
                response=response,
                next_agent="WorkflowGenerator" if "requirements_complete" in response else None,
                context=user_input.context
            )
        elif agent_type == "WorkflowRefiner":
            response = await workflow_generator.process(user_input.message, user_input.context)
            return AgentResponse(
                response=response,
                next_agent=None,
                context=user_input.context
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid agent type")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 