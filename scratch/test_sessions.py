import requests

print("Testing direct connect without session ID...")
r1 = requests.post("http://127.0.0.1:8000/connect", json={"url": "http://127.0.0.1:8001/sse"})
print(f"Status: {r1.status_code}, Response: {r1.json()}")
assert r1.status_code == 400

print("\nTesting connect with User A...")
headers_a = {"x-session-id": "user-a"}
r2 = requests.post("http://127.0.0.1:8000/connect", json={"url": "http://127.0.0.1:8001/sse"}, headers=headers_a)
print(f"Status: {r2.status_code}, Response: {r2.json()}")
assert r2.status_code == 200

print("\nTesting tools with User B before connect...")
headers_b = {"x-session-id": "user-b"}
r3 = requests.get("http://127.0.0.1:8000/tools", headers=headers_b)
print(f"Status: {r3.status_code}, Response: {r3.json()}")
assert r3.status_code == 400

print("\nTesting tools with User A...")
r4 = requests.get("http://127.0.0.1:8000/tools", headers=headers_a)
print(f"Status: {r4.status_code}, Response: {r4.json()}")
assert r4.status_code == 200

print("\nAll Multi-Tenant API Tests Passed!")
