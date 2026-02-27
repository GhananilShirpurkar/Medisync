import sys
import os
import asyncio

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.identity_agent import IdentityAgent
from src.database import Database
from src.models import Patient
from src.db_config import get_db_context

def test_identity_resolution():
    print("\n--- Testing Identity Resolution ---")
    agent = IdentityAgent()
    db = Database()
    
    # Test Phone Extraction
    text = "My phone is 9876543210 thanks"
    phone = agent.extract_phone_number(text)
    print(f"Input: '{text}' -> Extracted: {phone}")
    assert phone == "+919876543210"
    
    # Test Resolution (New Patient)
    print("Resolving identity for new number...")
    patient_info = agent.resolve_identity(phone, name="Test User")
    print(f"Resolved: {patient_info}")
    
    pid = patient_info["pid"]
    assert pid.startswith("PT")
    assert patient_info["is_new"] == True or patient_info["is_new"] == False # Might be False if run multiple times
    
    # Verify in DB
    with get_db_context() as session:
        patient = session.query(Patient).filter(Patient.user_id == pid).first()
        assert patient is not None
        assert patient.phone == phone
        print("Database verification passed.")
        
    # Test Resolution (Existing Patient)
    print("Resolving identity for SAME number...")
    patient_info_2 = agent.resolve_identity(phone)
    print(f"Resolved: {patient_info_2}")
    
    assert patient_info_2["pid"] == pid
    assert patient_info_2["is_new"] == False
    
    print("Identity Resolution Test Passed!")

if __name__ == "__main__":
    try:
        test_identity_resolution()
    except Exception as e:
        print(f"Test Failed: {e}")
        import traceback
        traceback.print_exc()
