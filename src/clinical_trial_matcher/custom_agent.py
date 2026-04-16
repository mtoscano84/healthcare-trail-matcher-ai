import os
import re
import json
import asyncio
import logging
import httpx

# Enable debug logging
logging.basicConfig(level=logging.INFO)

# Set environment variables for local testing
os.environ["MCP_URL"] = "http://localhost:5000"
os.environ["OLLAMA_URL"] = "http://localhost:11434"

# Define the tools in OpenAI format for Ollama /api/chat
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_patients_by_condition",
            "description": "Finds patients who have been diagnosed with a specific condition (keyword search).",
            "parameters": {
                "type": "object",
                "properties": {
                    "condition_keyword": {
                        "type": "string",
                        "description": "The condition to search for (e.g., Asthma, Diabetes)."
                    }
                },
                "required": ["condition_keyword"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_patient_profile",
            "description": "Retrieves demographic details and general description of a patient by their patient_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {
                        "type": "string",
                        "description": "The unique ID of the patient (e.g., P0001)."
                    }
                },
                "required": ["patient_id"]
            }
        }
    }
]

async def main():
    print("User: Find all patients who have been diagnosed with Diabetes.")
    print("Sending request to Ollama /api/chat with tools...")
    
    messages = [
        {"role": "system", "content": "You are an expert medical assistant specializing in matching patients to clinical trials. You MUST use the available tools to access patient data."},
        {"role": "user", "content": "Find all patients who have been diagnosed with Diabetes."}
    ]
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "gemma4:e2b",
                "messages": messages,
                "tools": tools,
                "stream": False
            },
            timeout=300.0
        )
        
    if response.status_code != 200:
        print(f"Error from Ollama: {response.status_code} - {response.text}")
        return
        
    res_json = response.json()
    print(f"\nFull JSON Response from Ollama:\n{json.dumps(res_json, indent=2)}")
    
    message = res_json.get("message", {})
    content = message.get("content", "")
    tool_calls = message.get("tool_calls", [])
    
    if tool_calls:
        print(f"\n!!! Tool Call Detected !!!")
        for tool_call in tool_calls:
            function = tool_call.get("function", {})
            name = function.get("name")
            args = function.get("arguments")
            print(f"Tool Name: {name}")
            print(f"Arguments: {args}")
            
            if name == "search_patients_by_condition":
                condition = args.get("condition_keyword")
                print(f"\n[ACTION] I would now call the MCP tool '{name}' with condition='{condition}'")
    elif content:
        print(f"\nModel Response Content:\n{content}")
    else:
        print("\nNo content and no tool calls returned.")


if __name__ == "__main__":
    asyncio.run(main())
