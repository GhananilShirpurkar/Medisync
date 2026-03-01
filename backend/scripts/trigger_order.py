from src.state import PharmacyState, OrderItem
from src.agents.fulfillment_agent import fulfillment_agent
from src.events.event_bus import get_event_bus
from src.events.handlers.notification_handler import register_notification_handlers
import time

def trigger_test_order():
    # Register handlers for this process
    event_bus = get_event_bus()
    register_notification_handlers(event_bus)
    
    state = PharmacyState(
        user_id="PID-001002",
        session_id="test_session_" + str(int(time.time())),
        whatsapp_phone="9067939108", # Using a sample phone
        extracted_items=[
            OrderItem(medicine_name="Paracetamol Plus", quantity=2, price=148.83, dosage="500mg")
        ],
        confirmation_confirmed=True,
        pharmacist_decision="approved"
    )
    
    print("Triggering fulfillment_agent...")
    new_state = fulfillment_agent(state)
    print(f"Order created: {new_state.order_id}")
    print(f"Order status: {new_state.order_status}")

if __name__ == "__main__":
    trigger_test_order()
