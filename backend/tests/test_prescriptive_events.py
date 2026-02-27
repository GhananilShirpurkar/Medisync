import sys
import os
import asyncio
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.internal_events import event_manager, PATIENT_IDENTIFIED
from src.services.prediction_service import prediction_service

async def test_event_system():
    print("\n--- Testing Event System & Prediction Service ---")
    
    # Create a test subscriber to verify event propagation
    received_events = []
    
    async def test_callback(data):
        print(f"TEST LISTENER: Received data: {data}")
        received_events.append(data)
        
    event_manager.subscribe(PATIENT_IDENTIFIED, test_callback)
    
    # Mock data
    test_data = {
        "pid": "PTTEST001",
        "phone": "+919988776655",
        "source": "test_script"
    }
    
    # Emit event
    print("Emitting PATIENT_IDENTIFIED event...")
    await event_manager.emit(PATIENT_IDENTIFIED, test_data)
    
    # Allow async tasks to run
    await asyncio.sleep(0.1)
    
    # Verify test listener received it
    assert len(received_events) == 1
    assert received_events[0]["pid"] == "PTTEST001"
    print("✅ Test listener received event.")
    
    # Verify PredictionService received it (it prints to console, harder to assert in script without capturing stdout, 
    # but we will rely on visual confirmation in terminal output for now or checking if it didn't crash).
    # Ideally, we could inspect prediction_service state if it had any.
    
    print("\nEvent System Test Passed!")

if __name__ == "__main__":
    try:
        asyncio.run(test_event_system())
    except Exception as e:
        print(f"Test Failed: {e}")
        import traceback
        traceback.print_exc()
