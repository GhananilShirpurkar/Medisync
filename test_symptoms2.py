import requests
import json

base_url = "http://localhost:8000/api/conversation"

try:
    print("Creating session...")
    resp = requests.post(f"{base_url}/create", json={})
    resp.raise_for_status()
    session_id = resp.json()["session_id"]
    
    # 1. "my knee is hurting really bad"
    print("\nSending: my knee is hurting really bad")
    resp = requests.post(f"{base_url}", json={"session_id": session_id, "message": "my knee is hurting really bad"})
    print("Status:", resp.status_code)
    try:
        print("Response:", json.dumps(resp.json(), indent=2))
    except:
        print("Text:", resp.text)
    
except Exception as e:
    print("Error:", e)
