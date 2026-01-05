from agents import Agent, Runner
import asyncio
import os
from pydantic import BaseModel

class ToolOutput(BaseModel):
    file_path: str

def dummy_tool() -> ToolOutput:
    return ToolOutput(file_path="test.txt")

async def main():
    agent = Agent(name="test", tools=[dummy_tool])
    result = await Runner.run(agent, "use dummy tool")
    print(f"Attributes of result: {dir(result)}")
    if hasattr(result, 'steps'):
        print(f"Steps: {result.steps}")
    if hasattr(result, 'turns'):
        print(f"Turns: {result.turns}")
    if hasattr(result, 'history'):
        print(f"History: {result.history}")

if __name__ == "__main__":
    os.environ["OPENAI_API_KEY"] = "sk-dummy" # Just for introspection of the object structure if it fails early
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Caught expected or unexpected error: {type(e).__name__}: {e}")
        # Even if it fails due to API key, we might see the Traceback or object attributes if we get far enough
