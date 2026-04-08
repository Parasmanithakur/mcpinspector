import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_list_tools():
    print("Testing /tools...")
    response = requests.get(f"{BASE_URL}/tools")
    if response.status_code == 200:
        tools = response.json().get("tools", [])
        print(f"Successfully listed {len(tools)} tools.")
        for tool in tools:
            print(f" - {tool['name']}: {tool.get('description', 'No description')}")
        return tools
    else:
        print(f"Failed to list tools: {response.text}")
        return None

def test_call_tool(tool_name, arguments):
    print(f"\nTesting /call with tool '{tool_name}'...")
    payload = {
        "name": tool_name,
        "arguments": arguments
    }
    response = requests.post(f"{BASE_URL}/call", json=payload)
    if response.status_code == 200:
        print("Success!")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Failed to call tool: {response.text}")

if __name__ == "__main__":
    tools = test_list_tools()
    if tools:
        # Try to find a tool to call. 'get_greeting' is in our sample_server.py
        greeting_tool = next((t for t in tools if t['name'] == 'get_greeting'), None)
        if greeting_tool:
            test_call_tool("get_greeting", {"name": "Python User"})
        else:
            print("\n'get_greeting' tool not found, calling the first available tool.")
            first_tool = tools[0]
            test_call_tool(first_tool['name'], {"name": "Test"})
