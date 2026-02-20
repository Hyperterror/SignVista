
import httpx
import json

base_url = "http://127.0.0.1:8000"
reg_url = f"{base_url}/api/auth/register"

def test():
    # 1. Register
    payload = {
        "name": "Verification User",
        "email": "verify@example.com",
        "phone": "9998881111",
        "password": "password123",
        "preferred_language": "en"
    }
    
    print(f"Registering...")
    with httpx.Client() as client:
        r = client.post(reg_url, json=payload)
        print(f"Reg Status: {r.status_code}")
        if r.status_code != 200:
            print(f"Error: {r.text}")
            return
            
        data = r.json()
        token = data["access_token"]
        session_id = data["sessionId"]
        print(f"Registered! Session: {session_id}")
        
        # 2. Get Profile
        profile_url = f"{base_url}/api/profile/{session_id}"
        print(f"Fetching Profile from {profile_url}...")
        headers = {"Authorization": f"Bearer {token}"}
        r2 = client.get(profile_url, headers=headers)
        print(f"Profile Status: {r2.status_code}")
        print(f"Profile Response: {json.dumps(r2.json(), indent=2)}")

if __name__ == "__main__":
    test()
