"""Start script for running all SUVI sub-agents as A2A servers."""

import asyncio
from aiohttp import web
from agents.text_agent.agent import TextAgent
from agents.code_agent.agent import CodeAgent
from agents.browser_agent.agent import BrowserAgent
from agents.search_agent.agent import SearchAgent
from agents.memory_agent.agent import MemoryAgent
from agents.data_agent.agent import DataAgent

async def start_all_agents():
    print("🚀 Booting SUVI Sub-Agents as A2A Servers...")
    
    # Initialize all agents
    agents = [
        TextAgent(port=8002),
        CodeAgent(port=8003),
        BrowserAgent(port=8004),
        SearchAgent(port=8005),
        MemoryAgent(port=8006),
        DataAgent(port=8007)
    ]
    
    # Start all A2A servers concurrently
    runners = await asyncio.gather(*(agent.start_server() for agent in agents))
    
    print("
✅ All agents are online and listening:")
    print(" - TextAgent:    http://localhost:8002")
    print(" - CodeAgent:    http://localhost:8003")
    print(" - BrowserAgent: http://localhost:8004")
    print(" - SearchAgent:  http://localhost:8005")
    print(" - MemoryAgent:  http://localhost:8006")
    print(" - DataAgent:    http://localhost:8007")
    
    # Keep the main thread alive
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(start_all_agents())
    except KeyboardInterrupt:
        print("
🛑 Shutting down SUVI agents...")
