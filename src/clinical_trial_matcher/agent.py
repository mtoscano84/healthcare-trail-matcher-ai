import os
from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.toolbox_toolset import ToolboxToolset

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
        model="ollama/gemma:2b",
        api_base=OLLAMA_URL,
        extra_body={
            "skip_special_tokens": False
        }
    ),
    name="clinical_trial_matcher",
    instruction="""You are an expert medical assistant specializing in matching patients to clinical trials.
Your goal is to help find eligible patients for a given clinical trial description.
You have access to database tools to search for patients by condition, and to retrieve their profiles, conditions, and treatments.

When given a trial description:
1. Identify the key conditions and criteria mentioned in the trial.
2. Use `search_patients_by_condition` to find candidate patients.
3. Use other tools to verify their profile, active conditions, and treatments if needed.
4. Provide a list of eligible patient IDs and a brief summary of why they match.
""",
    tools=[toolbox]
)

# ADK requires the agent instance to be exposed, or we can run it directly if this script is executed.
if __name__ == "__main__":
    # If run directly, we can start a simple interactive loop or use adk web
    # For now, we just print that it's ready.
    print("Agent initialized. Run with 'adk web src/agent.py' to interact.")
