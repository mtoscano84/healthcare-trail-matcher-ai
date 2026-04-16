import requests
import json

def test_mcp():
    url = "http://localhost:5000"
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "search_patients_by_condition",
            "arguments": {
                "condition_keyword": "Diabetes"
            }
        }
    }
    
    print(f"Sending JSON-RPC request to MCP server at {url}...")
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_mcp()
