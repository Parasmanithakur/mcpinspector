import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_sse_connect():
    print("Testing /connect with SSE URL...")
    payload = {"url": "http://127.0.0.1:8001/sse"}
    response = requests.post(f"{BASE_URL}/connect", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print("\nTesting /tools after SSE connect...")
        response = requests.get(f"{BASE_URL}/tools")
        if response.status_code == 200:
            tools = response.json().get("tools", [])
            print(f"Successfully listed {len(tools)} tools.")
            for tool in tools:
                print(f" - {tool['name']}")
        else:
            print(f"Failed to list tools: {response.text}")

if __name__ == "__main__":
    test_sse_connect()
