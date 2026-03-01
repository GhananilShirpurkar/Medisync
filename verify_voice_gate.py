
import sys
import os
import asyncio
from fastapi.testclient import TestClient

# Mock transcription to avoid Whisper dependency in test
def mock_transcription(text):
    return {
        "success": True,
        "transcription": text,
        "language": "en",
        "language_probability": 0.99
    }

async def verify_flow():
    from src.main import app
    from src.routes.conversation import confirmation_store
    import uuid
    
    client = TestClient(app)
    session_id = f"test_voice_{uuid.uuid4().hex[:8]}"
    
    print(f"\n--- STEP 1: Symptom 'I have a headache' ---")
    # We can't easily mock the audio upload in TestClient for the bytes part without complex setup,
    # but we can mock the speech_service.transcribe_audio_from_bytes inside the route if we wanted.
    # For now, let's just test the logic by manually invoking the logic or checking the endpoint behavior if we can mock speech.
    
    # Actually, the easiest way to verify the fix is to check the code itself OR run a unit test that mocks the speech service.
    
    from unittest.mock import patch, MagicMock
    
    with patch("src.routes.conversation.transcribe_audio_from_bytes") as mock_transcribe:
        # 1. Symptom request
        mock_transcribe.return_value = mock_transcription("i have a headache")
        response1 = client.post(f"/conversation/voice/{session_id}", files={"audio": ("test.wav", b"fake_bytes")})
        print(f"Status: {response1.status_code}")
        print(f"Response: {response1.json().get('message')}")
        assert response1.status_code == 200
        
        # 2. Medicine request (Purchase Intent)
        print(f"\n--- STEP 2: Purchase 'I want paracetamol' ---")
        mock_transcribe.return_value = mock_transcription("i want paracetamol")
        response2 = client.post(f"/conversation/voice/{session_id}", files={"audio": ("test.wav", b"fake_bytes")})
        print(f"Status: {response2.status_code}")
        data2 = response2.json()
        print(f"Message: {data2.get('message')}")
        print(f"Next Step: {data2.get('next_step')}")
        
        # This should now return awaiting_confirmation instead of 500
        assert response2.status_code == 200
        assert data2.get("next_step") == "awaiting_confirmation"
        
        # 3. Confirm YES
        print(f"\n--- STEP 3: Confirm 'YES' ---")
        mock_transcribe.return_value = mock_transcription("YES")
        response3 = client.post(f"/conversation/voice/{session_id}", files={"audio": ("test.wav", b"fake_bytes")})
        print(f"Status: {response3.status_code}")
        data3 = response3.json()
        print(f"Message: {data3.get('message')}")
        print(f"Next Step: {data3.get('next_step')}")
        
        # This should now return order_complete
        assert response3.status_code == 200
        assert data3.get("next_step") == "order_complete"
        assert "confirmed" in data3.get("message").lower()

if __name__ == "__main__":
    # Ensure src is in path
    sys.path.insert(0, os.path.abspath(os.curdir))
    asyncio.run(verify_flow())
