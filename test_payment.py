import asyncio
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database import get_db_context
from src.models import Order, Patient
from src.services.payment_service import payment_service
from src.services.whatsapp_service import whatsapp_service
import uuid

# Monkey-patch whatsapp_service to use our mock
def mock_send(phone, message):
    print(f"MOCK WHATSAPP FIRED: To {phone}\n{message}")
    return {"success": True}

whatsapp_service.send_message = mock_send

async def main():
    # Setup test data
    with get_db_context() as session:
        # Create a test patient
        uid = f"PT-{uuid.uuid4().hex[:6]}"
        patient = Patient(user_id=uid, phone="+919876543210", name="Test User")
        session.add(patient)
        
        # Create a test order
        oid = f"ORD-TEST-{uuid.uuid4().hex[:4]}"
        order = Order(order_id=oid, user_id=uid, status="pending", total_amount=150.0)
        session.add(order)
        session.commit()
        
    print(f"Created order {oid} for patient {uid}")

    # Initiate payment
    result = payment_service.initiate_payment(oid, 150.0, "test_idempotency_xyz")
    pid = result["payment_id"]
    print(f"Initiated payment: {pid}")

    # Process payment
    print("Mock confirming payment...")
    # we'll wait less in the script by substituting the sleep
    await payment_service.mock_confirm_payment(pid)
    
if __name__ == "__main__":
    asyncio.run(main())
