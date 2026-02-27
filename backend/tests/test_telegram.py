import sys
import os
import asyncio
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.telegram_pipeline import process_telegram_command, process_telegram_contact
from src.database import Database
from src.models import Patient
from src.db_config import get_db_context

async def test_telegram_integration():
    print("\n--- Testing Telegram Integration ---")
    
    # Mock Telegram Chat ID
    chat_id = "123456789"
    user_id = "test_user_1"
    phone_number = "+919999988888"
    
    # 1. Test /start (Unlinked)
    print("Testing /start command (Unlinked)...")
    result = await process_telegram_command(user_id, chat_id, "/start")
    print(f"Result: {result['message']}")
    assert result["require_contact"] is True
    
    # 2. Test Contact Sharing (Linking)
    print("\nTesting Contact Sharing...")
    result = await process_telegram_contact(chat_id, phone_number, "Telegram Tester")
    print(f"Result: {result['message']}")
    assert "Successfully Linked" in result["message"]
    
    # Verify in DB
    with get_db_context() as session:
        patient = session.query(Patient).filter(Patient.telegram_id == chat_id).first()
        assert patient is not None
        assert patient.phone == phone_number
        pid = patient.user_id
        print(f"Database verification passed. PID: {pid}")
        
    # 3. Test /start (Linked)
    print("\nTesting /start command (Linked)...")
    result = await process_telegram_command(user_id, chat_id, "/start")
    print(f"Result: {result['message']}")
    assert pid in result["message"]
    assert "Welcome back" in result["message"]
    
    print("\nTelegram Integration Test Passed!")

if __name__ == "__main__":
    try:
        asyncio.run(test_telegram_integration())
    except Exception as e:
        print(f"Test Failed: {e}")
        import traceback
        traceback.print_exc()
