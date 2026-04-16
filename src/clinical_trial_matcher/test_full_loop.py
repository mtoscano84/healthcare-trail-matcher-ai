import os
import re
import json
import asyncio
import httpx
from mcp.client.sse import sse_client
from mcp import ClientSession

async def execute_mcp_tool(name, arguments):
    url = os.environ.get("MCP_URL", "http://localhost:5000")
    print(f"\n[ACTION] Attempting to call MCP tool '{name}' with arguments: {arguments}")
    
    try:
        async with sse_client(url) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                print("Connected to MCP server.")
                
                # Call the tool
                result = await session.call_tool(name, arguments)
                print(f"MCP Tool Result: {result}")
                return result
    except Exception as e:
        print(f"Error calling MCP tool: {e}")
        return None

async def main():
    # 1. Call Ollama
    print("User: Find all patients who have been diagnosed with Diabetes.")
    print("Sending request to Ollama...")
    
    messages = [
        {"role": "system", "content": """You are an expert medical assistant specializing in matching patients to clinical trials.
You MUST use the available tools to access patient data.

To call a tool, you MUST output a JSON object with the following structure:
```json
{
  "name": "tool_name",
  "parameters": {
    "param_name": "value"
  }
}
```
Do NOT output any text before or after the JSON object when calling a tool.

AVAILABLE TOOLS:
- `search_patients_by_condition` (condition_keyword): Search for patients with a specific condition.
- `get_patient_profile` (patient_id): Get the profile of a specific patient.
"""},
        {"role": "user", "content": "Find all patients who have been diagnosed with Diabetes."}
    ]
    
    ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{ollama_url}/api/chat",
            json={
                "model": "gemma4:e2b",
                "messages": messages,
                "stream": False
            },
            timeout=300.0
        )
        
    if response.status_code != 200:
        print(f"Error from Ollama: {response.status_code} - {response.text}")
        return
        
    res_json = response.json()
    message = res_json.get("message", {})
    content = message.get("content", "")
    
    print(f"\nModel Response Content:\n{content}")
    
    # 2. Parse JSON from content
    json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
        try:
            tool_call = json.loads(json_str)
            name = tool_call.get("name")
            params = tool_call.get("parameters", {})
            
            print(f"\nParsed Tool Call: {name}")
            print(f"Parameters: {params}")
            
            # 3. Execute Tool
            await execute_mcp_tool(name, params)
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {e}")
    else:
        print("No JSON block found in response.")

if __name__ == "__main__":
    asyncio.run(main())
