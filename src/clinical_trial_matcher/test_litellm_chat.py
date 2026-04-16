import os
import asyncio
from litellm import acompletion

# Set environment variables for local testing
os.environ["OLLAMA_URL"] = "http://localhost:11434"

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
    }
]

async def main():
    print("Testing LiteLLM with ollama_chat/ prefix...")
    try:
        response = await acompletion(
            model="ollama_chat/gemma4:e2b",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. You MUST use the available tools."},
                {"role": "user", "content": "Find all patients who have been diagnosed with Diabetes."}
            ],
            tools=tools,
            api_base="http://localhost:11434"
        )
        print(f"\nResponse received from LiteLLM:")
        print(response)
        
        message = response.choices[0].message
        if hasattr(message, 'tool_calls') and message.tool_calls:
            print("\n!!! Success! Tool calls detected in LiteLLM response !!!")
            print(message.tool_calls)
        else:
            print("\nNo tool calls detected in LiteLLM response.")
            
    except Exception as e:
        print(f"\nError occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
