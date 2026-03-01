import requests
import uuid

session_id = f"sess_{uuid.uuid4().hex[:16]}"

print("Starting verification for Medicine Extraction and Fulfillment Fixes...")

# Start a session
res = requests.post("http://localhost:8000/api/conversation/create", json={"user_id": session_id})
print(f"Session Created: {res.status_code}")

# Say "i have a headache"
payload1 = {
    "session_id": session_id,
    "message": "i have a headache",
    "is_voice": False
}
print(f"Sending Turn 1: '{payload1['message']}'")
res1 = requests.post("http://localhost:8000/api/conversation", json=payload1)
print(f"Turn 1 response code: {res1.status_code}")
if res1.status_code == 200:
    print(f"Intent matched: {res1.json().get('intent')}")
    print(f"AI Response: {res1.json().get('message')}\n")

# Say "i want paracetamol"
payload2 = {
    "session_id": session_id,
    "message": "i want paracetamol",
    "is_voice": False
}
print(f"Sending Turn 2: '{payload2['message']}'")
res2 = requests.post("http://localhost:8000/api/conversation", json=payload2)
print(f"Turn 2 response code: {res2.status_code}")
if res2.status_code == 200:
    print(f"Intent matched: {res2.json().get('intent')}")
    print(f"AI Response: {res2.json().get('message')}")
else:
    print(f"Error: {res2.text}")
