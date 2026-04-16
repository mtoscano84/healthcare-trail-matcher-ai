import os
import logging
from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.toolbox_toolset import ToolboxToolset

# Enable debug logging to see traces in the terminal
logging.basicConfig(level=logging.DEBUG)

# Configure endpoints via environment variables for flexibility
# Defaults are for in-cluster communication
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://ollama.ai-inference.svc.cluster.local:11434")
MCP_URL = os.environ.get("MCP_URL", "http://mcp-toolbox.mcp-server.svc.cluster.local:5000")

print(f"Connecting to Ollama at: {OLLAMA_URL}")
print(f"Connecting to MCP Toolbox at: {MCP_URL}")

# 1. Initialize the Toolbox Toolset
# This connects to the standalone MCP server we deployed
toolbox = ToolboxToolset(
    server_url=MCP_URL,
    toolset_name="healthcare-toolset"
)

# 2. Initialize the Agent
# We use LiteLlm to connect to the OpenAI-compatible endpoint of Ollama
root_agent = Agent(
    model=LiteLlm(
        model="gemma4:e2b",
        api_base=f"{OLLAMA_URL}/v1",
        custom_llm_provider="openai",
        api_key="not-needed"
    ),
    name="clinical_trial_matcher",
    instruction="""You are an expert medical assistant specializing in matching patients to clinical trials.
Your goal is to help find eligible patients for a given clinical trial description.
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
- `search_patients_by_condition` (condition): Search for patients with a specific condition.
- `get_patient_profile` (patient_id): Get the profile of a specific patient.
- `get_patient_conditions` (patient_id)`: Get all conditions for a specific patient.
- `get_patient_treatments` (patient_id)`: Get all treatments for a specific patient.
""",
    tools=[toolbox]
)

# ADK requires the agent instance to be exposed, or we can run it directly if this script is executed.
if __name__ == "__main__":
    # If run directly, we can start a simple interactive loop or use adk web
    # For now, we just print that it's ready.
    print("Agent initialized. Run with 'adk web src/agent.py' to interact.")
