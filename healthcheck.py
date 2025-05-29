import asyncio
from agents.llm_client import llm_client

async def check_health():
    health = await llm_client.health_check()
    print(health)

if __name__ == "__main__":
    asyncio.run(check_health())