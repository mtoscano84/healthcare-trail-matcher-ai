import os
import re
import json
import asyncio
from litellm import acompletion

# Set environment variables for local testing
os.environ["MCP_URL"] = "http://localhost:5000"
os.environ["OLLAMA_URL"] = "http://localhost:11434"

# Define the tool declarations for Gemma 4 as per official documentation
tool_declarations = """
<|tool>declaration:search_patients_by_condition{description:"Finds patients who have been diagnosed with a specific condition (keyword search).",parameters:{properties:{condition_keyword:{description:"The condition to search for (e.g., Asthma, Diabetes).",type:"STRING"}},required:["condition_keyword"],type:"OBJECT"} }<tool|>
<|tool>declaration:get_patient_profile{description:"Retrieves demographic details and general description of a patient by their patient_id.",parameters:{properties:{patient_id:{description:"The unique ID of the patient (e.g., P0001).",type:"STRING"}},required:["patient_id"],type:"OBJECT"} }<tool|>
<|tool>declaration:get_patient_conditions{description:"Retrieves all recorded diagnoses and conditions for a specific patient.",parameters:{properties:{patient_id:{description:"The unique ID of the patient (e.g., P0001).",type:"STRING"}},required:["patient_id"],type:"OBJECT"} }<tool|>
<|tool>declaration:get_patient_treatments{description:"Retrieves all medications prescribed to a specific patient.",parameters:{properties:{patient_id:{description:"The unique ID of the patient (e.g., P0001).",type:"STRING"}},required:["patient_id"],type:"OBJECT"} }<tool|>
"""

# Construct the system prompt with the declarations
system_prompt = f"""You are an expert medical assistant specializing in matching patients to clinical trials.
Your goal is to help find eligible patients for a given clinical trial description.
You MUST use the available tools to access patient data.

{tool_declarations}

To call a tool, you MUST output: <|tool_call>call:tool_name{{param:value}}<tool_call|>
"""

async def main():
    prompt = "Find all patients who have been diagnosed with Diabetes."
    print(f"User: {prompt}")
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    
    print("Sending request to Gemma 4 via Ollama...")
    response = await acompletion(
        model="ollama/gemma4:e2b",
        messages=messages,
        api_base="http://localhost:11434",
        extra_body={"skip_special_tokens": False}
    )
    
    output = response.choices[0].message.content
    print(f"\nModel Raw Response:\n{output}")
    
    # Parse tool calls using the regex from Gemma 4 docs
    tool_calls = re.findall(r"<\|tool_call>call:(\w+)\{(.*?)\}<tool_call\|>", output, re.DOTALL)
    
    if tool_calls:
        print(f"\n!!! Tool Call Detected !!!")
        for name, args in tool_calls:
            print(f"Tool Name: {name}")
            print(f"Raw Arguments: {args}")
            
            # Extract argument value (handling the special <|"|> string wrappers if present)
            # Example: condition_keyword:<|"|>Diabetes<|"|>
            val_match = re.search(r'condition_keyword:(?:<\|"\|>)?([^<,}]+)(?:<\|"\|>)?', args)
            if val_match:
                condition = val_match.group(1).strip()
                print(f"Parsed Argument 'condition_keyword': {condition}")
                
                print(f"\n[ACTION] I would now call the MCP tool '{name}' with condition='{condition}'")
                print("To complete the loop, we would send the tool output back to the model.")
            else:
                print("Could not parse arguments.")
    else:
        print("\nNo tool calls detected in the special Gemma format.")

if __name__ == "__main__":
    asyncio.run(main())
