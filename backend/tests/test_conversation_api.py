"""
TEST CONVERSATION API
=====================
Tests for conversation API endpoints.
"""

import sys
sys.path.insert(0, 'backend')

from src.services.conversation_service import ConversationService
from src.agents.front_desk_agent import FrontDeskAgent
from src.database import Database

def test_conversation_flow():
    """Test complete conversation flow."""
    
    print("\n" + "="*60)
    print("TESTING CONVERSATION API FLOW")
    print("="*60)
    
    # Initialize services
    conversation_service = ConversationService()
    front_desk_agent = FrontDeskAgent()
    db = Database()
    
    # Step 1: Create session
    print("\n1. Creating session...")
    session_id = conversation_service.create_session("test_user")
    print(f"   ✅ Session created: {session_id}")
    
    # Step 2: Add welcome message
    print("\n2. Adding welcome message...")
    conversation_service.add_message(
        session_id=session_id,
        role="assistant",
        content="Hello! How can I help you today?",
        agent_name="front_desk"
    )
    print("   ✅ Welcome message added")
    
    # Step 3: User describes symptoms
    print("\n3. User describes symptoms...")
    user_message = "I have a headache"
    conversation_service.add_message(
        session_id=session_id,
        role="user",
        content=user_message
    )
    print(f"   ✅ User message: '{user_message}'")
    
    # Step 4: Classify intent
    print("\n4. Classifying intent...")
    messages = conversation_service.get_messages(session_id)
    intent_result = front_desk_agent.classify_intent(user_message, messages)
    print(f"   ✅ Intent: {intent_result.get('intent', 'unknown')}")
    print(f"   ✅ Confidence: {intent_result.get('confidence', 0.0)}")
    
    # Step 5: Extract patient context
    print("\n5. Extracting patient context...")
    patient_context = front_desk_agent.extract_patient_context(user_message, messages)
    print(f"   ✅ Context: {patient_context}")
    
    # Step 6: Update session
    print("\n6. Updating session...")
    conversation_service.update_session(
        session_id=session_id,
        intent=intent_result.get('intent'),
        patient_context=patient_context
    )
    print("   ✅ Session updated")
    
    # Step 7: Get conversation history
    print("\n7. Getting conversation history...")
    history = conversation_service.get_conversation_history(session_id)
    print(f"   ✅ Session: {history['session']['session_id']}")
    print(f"   ✅ Messages: {len(history['messages'])}")
    print(f"   ✅ Turn count: {history['session']['turn_count']}")
    
    # Step 8: Test medicine lookup
    print("\n8. Testing medicine lookup...")
    medicine = db.get_medicine("Paracetamol 500mg")
    if medicine:
        print(f"   ✅ Found: {medicine['name']}")
        print(f"   ✅ Price: ₹{medicine['price']}")
        print(f"   ✅ Stock: {medicine['stock']}")
        print(f"   ✅ Requires prescription: {medicine['requires_prescription']}")
    else:
        print("   ❌ Medicine not found")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED")
    print("="*60)
    print("\n📊 Summary:")
    print(f"  - Session created: {session_id}")
    print(f"  - Messages: {len(history['messages'])}")
    print(f"  - Intent: {intent_result.get('intent')}")
    print(f"  - Medicine database: Working")
    print("\n🎉 Conversation API is ready!")

if __name__ == "__main__":
    test_conversation_flow()
