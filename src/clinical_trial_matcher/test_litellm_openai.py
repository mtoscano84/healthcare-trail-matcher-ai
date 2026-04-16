import os
import asyncio
from litellm import acompletion

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
    print("Testing LiteLLM with custom_llm_provider='openai' pointing to Ollama /v1...")
    try:
        response = await acompletion(
            model="gemma4:e2b",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. You MUST use the available tools."},
                {"role": "user", "content": "Find all patients who have been diagnosed with Diabetes."}
            ],
            tools=tools,
            api_base="http://localhost:11434/v1",
            custom_llm_provider="openai",
            api_key="not-needed"
        )
        print(f"\nResponse received:")
        print(response)
        
        message = response.choices[0].message
        if hasattr(message, 'tool_calls') and message.tool_calls:
            print("\n!!! Success! Tool calls detected !!!")
            print(message.tool_calls)
        else:
            print("\nNo tool calls detected.")
            
    except Exception as e:
        print(f"\nError occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
