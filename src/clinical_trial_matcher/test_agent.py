import os
# Set environment variables for local testing before importing agent
os.environ["MCP_URL"] = "http://localhost:5000"
os.environ["OLLAMA_URL"] = "http://localhost:11434"

import asyncio
from src.clinical_trial_matcher.agent import root_agent
from google.adk.runners import InMemoryRunner
from google.genai.types import Part, UserContent

async def main():
    print("Initializing runner...")
    runner = InMemoryRunner(agent=root_agent)
    
    # Enable auto creation of sessions as suggested by the error
    runner.auto_create_session = True
    
    message = "Find all patients who have been diagnosed with Diabetes."
    print(f"Sending message: {message}")
    
    content = UserContent(parts=[Part(text=message)])
    
    print("\n--- Starting Event Stream ---")
    async for event in runner.run_async(session_id="test_session", user_id="test_user", new_message=content):
        print(f"\nEvent Type: {type(event)}")
        
        # Print content if available
        if hasattr(event, 'content') and event.content:
            if isinstance(event.content, str):
                print(f"Content: {event.content}")
            elif hasattr(event.content, 'parts'):
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        print(f"Text: {part.text}")
                    elif hasattr(part, 'tool_call') and part.tool_call:
                        print(f"!!! TOOL CALL DETECTED !!!")
                        print(f"Tool: {part.tool_call.name}")
                        print(f"Args: {part.tool_call.args}")
        
        # Print error if available
        if hasattr(event, 'error_message') and event.error_message:
            print(f"Error: {event.error_message}")

if __name__ == "__main__":
    asyncio.run(main())
