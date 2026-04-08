import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_root():
    print("Testing /...")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_root()
