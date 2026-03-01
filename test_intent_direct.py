import sys
import asyncio
from src.agents.front_desk_agent import front_desk_agent
from src.services.conversation_service import conversation_service
import uuid

session_id = f"sess_{uuid.uuid4().hex[:16]}"
conversation_service.create_session(session_id, "TEST-USER")

print("\n--- TURN 1: 'i have a headache' ---")
msg1 = "i have a headache"
messages = conversation_service.get_messages(session_id)
intent_res1 = front_desk_agent.classify_intent(msg1, messages)
print(f"Initial intent: {intent_res1.get('intent')}")

ctx1 = front_desk_agent.extract_patient_context(msg1, messages)
conversation_service.update_session(session_id, intent_res1.get("intent"), ctx1)
conversation_service.add_message(session_id, "user", msg1)

q1 = front_desk_agent.generate_clarifying_question(
    intent=intent_res1.get("intent"),
    message=msg1,
    patient_context=ctx1,
    turn_count=1,
    language="en",
    conversation_history=conversation_service.get_messages(session_id)
)
print(f"AI: {q1}")
conversation_service.add_message(session_id, "assistant", q1)

print("\n--- TURN 2: 'i want paracetamol' ---")
msg2 = "i want paracetamol"
messages = conversation_service.get_messages(session_id)
intent_res2 = front_desk_agent.classify_intent(msg2, messages)
raw_intent = intent_res2.get("intent")
print(f"Raw from LLM: {raw_intent} (Confidence: {intent_res2.get('confidence', 1.0)})")

session = conversation_service.get_session(session_id)
previous_intent = session.get("intent")
intent = raw_intent

if previous_intent == "symptom" and intent != "symptom":
    print("Checking fallbacks...")
    if intent in ["unknown", "greeting", "generic_help", "refill"] or intent_res2.get("confidence", 1.0) < 0.5:
        print(f"FAILED - Inheriting previous intent: {previous_intent} (was {intent})")
        intent = previous_intent
    else:
        print(f"SUCCESS - Keeping high-confidence explicitly different intent: {intent}")

print(f"Final Resolved Intent: {intent}")

if intent == raw_intent:
    print("\n✅ Verification Passed: High confidence intent was not overridden.")
else:
    print("\n❌ Verification Failed: High confidence intent was overridden!")

print("--- TEST COMPLETE ---")
