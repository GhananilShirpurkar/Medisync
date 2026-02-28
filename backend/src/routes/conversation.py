"""
CONVERSATION API ROUTES
=======================
RESTful API endpoints for conversational pharmacy assistant.

Endpoints:
- POST /api/conversation/create - Create new conversation session
- POST /api/conversation - Send message and get response
- POST /api/conversation/cart/add - Add medicine to cart
- GET /api/conversation/{session_id} - Get conversation history
"""

from fastapi import APIRouter, HTTPException, status, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.services.conversation_service import ConversationService
from src.agents.front_desk_agent import FrontDeskAgent
from src.database import Database
from src.models import SymptomMedicineMapping, Medicine
from src.services.speech_service import transcribe_audio_from_bytes
from src.state import PharmacyState, OrderItem
from src.graph import agent_graph
from src.agents.fulfillment_agent import format_order_confirmation, fulfillment_agent
from src.services.confirmation_store import confirmation_store
from src.errors import ConfirmationRequiredError

router = APIRouter(prefix="/conversation", tags=["conversation"])

# Initialize services
conversation_service = ConversationService()
front_desk_agent = FrontDeskAgent()
db = Database()

from src.agents.identity_agent import IdentityAgent
identity_agent = IdentityAgent()

from src.services.observability_service import observe, langfuse_context


# ------------------------------------------------------------------
# REQUEST/RESPONSE MODELS
# ------------------------------------------------------------------

class CreateSessionRequest(BaseModel):
    """Request to create a new conversation session."""
    user_id: Optional[str] = None


class CreateSessionResponse(BaseModel):
    """Response with new session ID."""
    session_id: str
    created_at: str
    message: str = "Session created successfully"


class ConversationRequest(BaseModel):
    """Request to send a message in conversation."""
    session_id: str = Field(..., description="Session identifier")
    message: str = Field(..., min_length=1, max_length=1000, description="User message")


class MedicineRecommendation(BaseModel):
    """Medicine recommendation with details."""
    medicine_name: str
    price: float
    dosage: Optional[str] = None
    stock: int
    requires_prescription: bool
    indications: Optional[str] = None
    generic_equivalent: Optional[str] = None
    in_stock: bool


class ConversationResponse(BaseModel):
    """Response from conversation."""
    session_id: str
    message: str
    intent: Optional[str] = None
    recommendations: Optional[List[MedicineRecommendation]] = None
    needs_clarification: bool = False
    clarifying_question: Optional[str] = None
    patient_context: Optional[Dict[str, Any]] = None
    next_step: Optional[str] = None
    severity_assessment: Optional[Dict[str, Any]] = None  # NEW: Severity scoring
    client_action: Optional[str] = None  # NEW: Trigger client-side actions


class VoiceInputResponse(BaseModel):
    """Response from voice input."""
    session_id: str
    transcription: str
    transcription_confidence: float
    language: str
    message: str
    intent: Optional[str] = None
    recommendations: Optional[List[MedicineRecommendation]] = None
    needs_clarification: bool = False
    clarifying_question: Optional[str] = None
    patient_context: Optional[Dict[str, Any]] = None
    next_step: Optional[str] = None
    client_action: Optional[str] = None


class AddToCartRequest(BaseModel):
    """Request to add medicine to cart."""
    session_id: str
    medicine_name: str
    quantity: int = Field(default=1, ge=1, le=100)
    dosage: Optional[str] = None


class AddToCartResponse(BaseModel):
    """Response after adding to cart."""
    session_id: str
    message: str
    cart_items: List[Dict[str, Any]]
    total_items: int


class ConversationHistoryResponse(BaseModel):
    """Complete conversation history."""
    session_id: str
    user_id: str
    status: str
    intent: Optional[str] = None
    turn_count: int
    messages: List[Dict[str, Any]]
    created_at: str
    updated_at: str


class ConfirmOrderRequest(BaseModel):
    """Request to confirm or cancel a pending order."""
    session_id: str = Field(..., description="Session identifier")
    confirmation_token: str = Field(..., description="Token issued when gate was opened")
    user_response: str = Field(..., description="Must be 'YES' or 'NO'")


class ConfirmOrderResponse(BaseModel):
    """Response from the /confirm endpoint."""
    session_id: str
    status: str                          # confirmed | cancelled | expired | invalid
    message: str
    order_id: Optional[str] = None
    requires_pharmacist_override: bool = False


# ------------------------------------------------------------------
# ENDPOINTS
# ------------------------------------------------------------------

@router.post("/create", response_model=CreateSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(request: CreateSessionRequest):
    """
    Create a new conversation session.
    
    This initializes a new conversation with the pharmacy assistant.
    """
    try:
        session_id = conversation_service.create_session(request.user_id)
        
        # Add welcome message
        conversation_service.add_message(
            session_id=session_id,
            role="assistant",
            content="Hello! I'm your MediSync pharmacy assistant. How can I help you today?",
            agent_name="front_desk"
        )
        
        return CreateSessionResponse(
            session_id=session_id,
            created_at=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )


@router.post("", response_model=ConversationResponse)
@observe()
async def send_message(request: ConversationRequest):
    """
    Send a message in conversation and get AI response.
    
    This is the main conversational endpoint that:
    1. Classifies user intent
    2. Extracts patient context
    3. Generates recommendations or asks clarifying questions
    4. Routes to appropriate agents
    """
    try:
        from src.services.observability_service import trace_manager

        # Set langfuse trace properties
        langfuse_context.update_current_trace(
            session_id=request.session_id,
            name="send_message"
        )

        # Validate session exists
        session = conversation_service.get_session(request.session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        # ------------------------------------------------------------------
        # ORDER CONFIRMATION INTERCEPT
        # Check before anything else — user is replying YES/NO to a pending order
        # ------------------------------------------------------------------
        if confirmation_store.is_pending(request.session_id):
            pending = confirmation_store.get_pending(request.session_id)
            user_reply = request.message.strip().upper()
            conversation_service.add_message(
                session_id=request.session_id,
                role="user",
                content=request.message
            )
            if user_reply == 'YES':
                # Consume atomically — prevents double execution
                entry = confirmation_store.consume(
                    request.session_id, pending["token"]
                )
                if entry:
                    pending_state = PharmacyState(**entry["pending_pharmacy_state"])
                    # Set the confirmation flag so fulfillment_agent passes the gate
                    pending_state.confirmation_confirmed = True
                    pending_state.conversation_phase = "fulfillment_executing"
                    conversation_service.transition_phase(
                        request.session_id, "fulfillment_executing"
                    )
                    try:
                        final_state = fulfillment_agent(pending_state)
                        import traceback
                        logger.error(f"FULFILLMENT TRACEBACK: {traceback.format_exc()}")
                        response_message = format_order_confirmation(final_state)
                        conversation_service.transition_phase(
                            request.session_id, "completed"
                        )
                    except ConfirmationRequiredError:
                        response_message = "Order could not be processed. Please try again."
                else:
                    response_message = "Order already processed or expired."
                conversation_service.add_message(
                    session_id=request.session_id,
                    role='assistant',
                    content=response_message,
                    agent_name='fulfillment'
                )
                await trace_manager.emit(
                    session_id=request.session_id,
                    agent_name='FRONT_DESK',
                    step_name='Order confirmed — processing',
                    action_type='response',
                    status='completed',
                    details={'message': response_message}
                )
                return ConversationResponse(
                    session_id=request.session_id,
                    message=response_message,
                    intent='purchase',
                    needs_clarification=False,
                    next_step='order_complete'
                )
            elif user_reply == 'NO':
                confirmation_store.cancel(request.session_id)
                conversation_service.transition_phase(
                    request.session_id, "collecting_items"
                )
                response_message = "Order cancelled. How else can I help you?"
                conversation_service.add_message(
                    session_id=request.session_id,
                    role='assistant',
                    content=response_message,
                    agent_name='front_desk'
                )
                return ConversationResponse(
                    session_id=request.session_id,
                    message=response_message,
                    intent='purchase',
                    needs_clarification=False,
                    next_step='cancelled'
                )
            else:
                response_message = "Please reply *YES* to confirm your order or *NO* to cancel."
                conversation_service.add_message(
                    session_id=request.session_id,
                    role='assistant',
                    content=response_message,
                    agent_name='front_desk'
                )
                return ConversationResponse(
                    session_id=request.session_id,
                    message=response_message,
                    intent='purchase',
                    needs_clarification=True,
                    next_step='awaiting_confirmation'
                )

        # Trace: Start
        await trace_manager.emit(
            session_id=request.session_id,
            agent_name="API Gateway",
            step_name="Received message",
            action_type="event",
            status="started",
            details={"message": request.message[:100]}
        )

        # Add user message to conversation
        conversation_service.add_message(
            session_id=request.session_id,
            role="user",
            content=request.message
        )

        # Get conversation history
        messages = conversation_service.get_messages(request.session_id)

        # Check if this is a confirmation to a previous recommendation
        message_lower = request.message.lower().strip()
        confirmation_words = ["yes", "yeah", "yep", "ok", "okay", "sure", "हाँ", "ठीक"]
        is_confirmation = message_lower in confirmation_words

        # Check if previous assistant message had recommendations
        if is_confirmation and len(messages) >= 2:
            last_assistant_msg = None
            for msg in reversed(messages):
                if msg.get("role") == "assistant":
                    last_assistant_msg = msg
                    break

            if last_assistant_msg and last_assistant_msg.get("content"):
                content = last_assistant_msg.get("content", "")
                if "add it to your cart" in content.lower() or "would you like to add" in content.lower():
                    import re
                    medicine_match = re.search(r"(?:I found|Did you mean '?)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", content)
                    if medicine_match:
                        medicine_name = medicine_match.group(1).strip("'")
                        response_message = f"Great! I've noted {medicine_name} for your order. "
                        response_message += "Would you like to add anything else, or shall we proceed to checkout?"

                        conversation_service.add_message(
                            session_id=request.session_id,
                            role="assistant",
                            content=response_message,
                            agent_name="fulfillment"
                        )

                        return ConversationResponse(
                            session_id=request.session_id,
                            message=response_message,
                            intent="purchase",
                            recommendations=None,
                            needs_clarification=False,
                            patient_context={},
                            next_step="checkout"
                        )

        # Step 0: Identity Resolution
        session_user_id = session.get("user_id")
        is_returning_user = session_user_id and session_user_id.startswith("PID-")
        
        # Check if the user ID itself is a phone number (from landing page)
        is_phone_id = session_user_id and not is_returning_user and identity_agent.extract_phone_number(session_user_id)
        
        phone_number = None
        # Only scan if we don't already have a PID or a Phone ID
        if not is_returning_user:
            if is_phone_id:
                phone_number = identity_agent.extract_phone_number(session_user_id)
            else:
                await trace_manager.emit(
                    session_id=request.session_id,
                    agent_name="Identity Agent",
                    step_name="Thinking: Recognizing who is speaking to me...",
                    action_type="thinking",
                    status="started"
                )
                phone_number = identity_agent.extract_phone_number(request.message)

        if phone_number and not is_returning_user:
            patient_info = identity_agent.resolve_identity(phone_number)
            pid = patient_info["pid"]
            formatted_phone = patient_info["phone"]
            is_new = patient_info["is_new"]

            await trace_manager.emit(
                session_id=request.session_id,
                agent_name="Identity Agent",
                step_name="Thinking: Successfully recognized you!",
                action_type="tool_use",
                status="completed",
                details={"pid": pid, "is_new": is_new}
            )

            conversation_service.update_session(
                session_id=request.session_id,
                user_id=pid,
                patient_context={"pid": pid, "phone": formatted_phone, "name": patient_info.get("name")}
            )

            from src.internal_events import event_manager, PATIENT_IDENTIFIED
            import asyncio
            asyncio.create_task(event_manager.emit(PATIENT_IDENTIFIED, {
                "pid": pid,
                "phone": formatted_phone,
                "source": "conversation",
                "session_id": request.session_id
            }))

            async def send_opening_message(pid: str, phone: str, session_id: str):
                patient = db.resolve_patient(phone)
                orders = patient.get('orders', [])
                
                if orders:
                    last_item = orders[-1].get('items', [{}])[0].get('name', 'your last order')
                    opening = f"Welcome back. Last visit you ordered {last_item}. What brings you in today?"
                else:
                    opening = "Welcome to MediSync. Please describe your symptoms or tell me which medicine you need."
                
                await trace_manager.emit(
                    session_id=session_id,
                    agent_name="FRONT_DESK",
                    step_name="Thinking: Preparing a warm welcome...",
                    action_type="response",
                    status="completed",
                    details={"message": opening}
                )

            asyncio.create_task(send_opening_message(pid, formatted_phone, request.session_id))

            welcome_msg = ""
            if is_new:
                welcome_msg = f"Thanks! I've registered you with Patient ID: {pid}. "
                welcome_msg += "I've linked your phone for WhatsApp notifications."
            else:
                welcome_msg = f"Welcome back, {patient_info.get('name') or pid}. "

            welcome_msg += "\nHow can I help you today?"

            conversation_service.add_message(
                session_id=request.session_id,
                role="assistant",
                content=welcome_msg,
                agent_name="identity_agent"
            )

            return ConversationResponse(
                session_id=request.session_id,
                message=welcome_msg,
                intent="identity_resolved",
                patient_context=patient_info,
                next_step="intake"
            )
        elif not is_returning_user:
            # We already emitted "Scan for Phone Number" started, so emit completed
            await trace_manager.emit(
                session_id=request.session_id,
                agent_name="Identity Agent",
                step_name="Thinking: Recognizing who is speaking to me...",
                action_type="thinking",
                status="completed",
                details={"found": False}
            )
        else:
            # Already a returning user, skip emitting Scan trace entirely to keep UI clean
            pass

        # Step 1: Classify intent
        await trace_manager.emit(
            session_id=request.session_id,
            agent_name="Front Desk Agent",
            step_name="Thinking: Analyzing your request to understand how to help...",
            action_type="thinking",
            status="started"
        )

        intent_result = front_desk_agent.classify_intent(
            message=request.message,
            conversation_history=messages
        )

        await trace_manager.emit(
            session_id=request.session_id,
            agent_name="Front Desk Agent",
            step_name="Thinking: Analyzing your request to understand how to help...",
            action_type="decision",
            status="completed",
            details={"intent": intent_result.get("intent"), "language": intent_result.get("language")}
        )

        intent = intent_result.get("intent", "symptom")
        
        # Inherit previous intent if the user is answering a clarifying question
        # (e.g. they say "20" or "for last 5 days", which misclassifies as 'refill' or 'generic_help')
        previous_intent = session.get("intent")
        if previous_intent == "symptom" and intent != "symptom":
            # Check if the last assistant message was a symptom-related question
            last_assistant = next(
                (m for m in reversed(messages) if m.get("role") == "assistant"), None
            )
            symptom_flow_keywords = [
                "how long", "duration", "severity", "symptoms",
                "experiencing", "feeling", "describe", "pain",
                "sorry to hear", "tell me more"
            ]
            is_symptom_followup = last_assistant and any(
                kw in (last_assistant.get("content", "")).lower()
                for kw in symptom_flow_keywords
            )
            if is_symptom_followup or intent in ["unknown", "greeting", "generic_help", "refill"] or intent_result.get("confidence", 1.0) < 0.5:
                print(f"DEBUG: Inheriting previous intent: {previous_intent} (was {intent} with confidence {intent_result.get('confidence')})")
                intent = previous_intent
        
        # Check for client-side triggers
        client_action = None
        if intent == "prescription_upload":
            client_action = "OPEN_CAMERA"
        
        # Step 2: Extract patient context
        print("DEBUG: calling extract_patient_context...")
        patient_context = front_desk_agent.extract_patient_context(
            message=request.message,
            conversation_history=messages
        )
        print(f"DEBUG: context extracted: {patient_context}")
        
        # Update session with intent and context
        conversation_service.update_session(
            session_id=request.session_id,
            intent=intent,
            patient_context=patient_context
        )

        # Trace: Context Extraction
        await trace_manager.emit(
            session_id=request.session_id,
            agent_name="Front Desk Agent",
            step_name="Thinking: Gathering relevant details from our conversation...",
            action_type="tool_use",
            status="completed",
            details={"patient_context": patient_context}
        )
        
        # Special handling for prescription upload - skip clarification and return immediately
        if intent == "prescription_upload":
            # ... (omitted for brevity, assume unchanged logic flow) ...
            client_action = "OPEN_CAMERA" # Re-declare for clarity in snippet context if needed, but context here is safe
            response_message = "📸 Camera opened! Please show your prescription to the camera."
            
            conversation_service.add_message(
                session_id=request.session_id,
                role="assistant",
                content=response_message,
                agent_name="front_desk"
            )

            # Trace: Final response
            await trace_manager.emit(
                session_id=request.session_id,
                agent_name="ORCHESTRATOR",
                step_name="Responding with your camera...",
                action_type="response",
                status="completed"
            )

            # Trace: Complete API Gateway
            await trace_manager.emit(
                session_id=request.session_id,
                agent_name="API Gateway",
                step_name="Waiting for response",
                action_type="event",
                status="completed"
            )
            
            return ConversationResponse(
                session_id=request.session_id,
                message=response_message,
                intent=intent,
                needs_clarification=False,
                patient_context=patient_context,
                next_step="capture_prescription",
                client_action=client_action
            )
        
        # Step 3: Check if clarification needed
        turn_count = session.get("turn_count", 0)
        print(f"DEBUG: calling generate_clarifying_question (turn {turn_count})...")
        clarifying_question = front_desk_agent.generate_clarifying_question(
            intent=intent,
            message=request.message,
            patient_context=patient_context,
            turn_count=turn_count,
            language=intent_result.get("language", "en"),
            conversation_history=messages
        )
        print(f"DEBUG: clarifying_question response: {clarifying_question[:50] if clarifying_question else 'None'}")
        
        if clarifying_question:
            # Ask clarifying question
            conversation_service.add_message(
                session_id=request.session_id,
                role="assistant",
                content=clarifying_question,
                agent_name="front_desk"
            )

            # Trace: Clarification
            await trace_manager.emit(
                session_id=request.session_id,
                agent_name="Front Desk Agent",
                step_name="Thinking: I need a bit more info to be sure...",
                action_type="response",
                status="completed",
                details={"question": clarifying_question}
            )

            # Trace: Final response
            await trace_manager.emit(
                session_id=request.session_id,
                agent_name="ORCHESTRATOR",
                step_name="Responding with a clarification question...",
                action_type="response",
                status="completed"
            )

            # Trace: Complete API Gateway
            await trace_manager.emit(
                session_id=request.session_id,
                agent_name="API Gateway",
                step_name="Waiting for response",
                action_type="event",
                status="completed"
            )
            
            return ConversationResponse(
                session_id=request.session_id,
                message=clarifying_question,
                intent=intent,
                needs_clarification=True,
                clarifying_question=clarifying_question,
                patient_context=patient_context,
                next_step="clarification",
                client_action=client_action
            )
        
        # Step 4: Assess severity (NEW - Severity Scoring Feature)
        severity_assessment = None
        if intent == "symptom" and not clarifying_question:
            # Only assess severity after clarifying questions are done
            from src.agents.severity_scorer import assess_severity
            
            # Get full conversation history
            all_messages = conversation_service.get_messages(request.session_id)
            
            # Combine all user messages for severity assessment
            combined_symptoms = " ".join([
                msg.get("content", "") 
                for msg in all_messages 
                if msg.get("role") == "user"
            ])
            
            # Assess severity
            severity_assessment = assess_severity(
                symptoms=combined_symptoms,
                patient_context=patient_context,
                conversation_history=all_messages
            )
            
            # Log severity assessment
            conversation_service.add_message(
                session_id=request.session_id,
                role="system",
                content=f"Severity assessed: {severity_assessment['severity_score']}/10 - {severity_assessment['risk_level']}",
                agent_name="severity_scorer",
                extra_data=severity_assessment
            )

            # Trace: Severity Assessment
            await trace_manager.emit(
                session_id=request.session_id,
                agent_name="Medical Agent",
                step_name="Thinking: Evaluating the urgency of your situation...",
                action_type="decision",
                status="completed",
                details={"severity": severity_assessment['severity_score'], "risk": severity_assessment['risk_level']}
            )
            
            # Check if emergency routing needed
            if severity_assessment["route"] == "EMERGENCY_ALERT":
                emergency_message = f"""EMERGENCY ALERT

Based on your symptoms, this appears to be a medical emergency.

Severity: {severity_assessment['severity_score']}/10 (Critical)
Risk Level: {severity_assessment['risk_level'].upper()}

IMMEDIATE ACTION REQUIRED:
- Call emergency services (108/102) immediately
- Go to nearest emergency room
- Do not wait for medication

Red Flags Detected:
"""
                for flag in severity_assessment["red_flags_detected"]:
                    emergency_message += f"- {flag}\n"
                
                emergency_message += "\nThis is not a situation for over-the-counter medication. Please seek emergency medical care immediately."
                
                conversation_service.add_message(
                    session_id=request.session_id,
                    role="assistant",
                    content=emergency_message,
                    agent_name="severity_scorer"
                )
                
                return ConversationResponse(
                    session_id=request.session_id,
                    message=emergency_message,
                    intent=intent,
                    recommendations=None,
                    needs_clarification=False,
                    patient_context=patient_context,
                    next_step="emergency_referral",
                    severity_assessment=severity_assessment
                )
            
            elif severity_assessment["route"] == "DOCTOR_REFERRAL":
                # Do NOT block — let Step 5 generate OTC recommendations.
                # The referral note will be prepended to the recommendation message.
                # Headache + mild fever should still get medicine suggestions.
                pass

        
        # Step 5: Generate recommendations based on intent
        if intent == "symptom":
            # Get full conversation history to extract all symptoms mentioned
            all_messages = conversation_service.get_messages(request.session_id)
            
            # Combine recent, relevant user messages — filter out noise
            noise_words = {"yes", "no", "ok", "okay", "hello", "hi", "hey", "thanks", "thank you"}
            user_msgs = [
                msg.get("content", "") for msg in all_messages
                if msg.get("role") == "user"
                and len(msg.get("content", "").strip()) > 3
                and msg.get("content", "").strip().lower() not in noise_words
            ]
            combined_symptoms = " ".join(user_msgs[-3:])[:500]  # Last 3 relevant, truncated
            
            # Find medicines for symptoms
            recommendations = await _get_symptom_recommendations(
                combined_symptoms,  # Pass all user messages, not just current one
                patient_context
            )
            
            if recommendations:
                # Only extract medicine items when user named specific medicines (not symptoms)
                extracted_map = {}
                if intent != "symptom":
                    extracted = front_desk_agent.extract_medicine_items(request.message)
                    extracted_map = {
                        item.medicine_name.lower(): item for item in extracted
                }
                order_items = []
                for r in recommendations:
                    ex = extracted_map.get(r.medicine_name.lower())
                    order_items.append(OrderItem(
                        medicine_name=r.medicine_name,
                        dosage=ex.dosage if ex else r.dosage,
                        quantity=ex.quantity if ex else 1,
                    ))

                state = PharmacyState(
                    user_id=session.get("user_id") or request.session_id,
                    session_id=request.session_id,
                    whatsapp_phone=patient_context.get("phone") or session.get("whatsapp_phone"),
                    user_message=request.message,
                    intent=intent,
                    extracted_items=order_items
                )
                state.trace_metadata["front_desk"] = {"patient_context": patient_context}

                # -- Build replacement context summary (Block 3→4 injection) --
                replacement_info = None
                replacement_lines = []
                has_replacement = False
                for rep in state.replacement_pending:
                    if rep.get("replacement_found"):
                        has_replacement = True
                        override_note = " ⚠️ Requires pharmacist review." if rep.get("requires_pharmacist_override") else ""
                        replacement_lines.append(
                            f"⚠️ *{rep['original']}* unavailable.\n"
                            f"   Suggested replacement: *{rep['suggested']}*"
                            f" ({rep['reasoning']}).{override_note}"
                        )
                        replacement_info = rep   # pass to store for audit

                if has_replacement:
                    state.conversation_phase = "replacement_suggested"
                    conversation_service.transition_phase(
                        request.session_id, "replacement_suggested"
                    )

                # Build confirmation message
                items_lines = []
                total = 0.0
                for item in order_items:
                    med_data = db.get_medicine(item.medicine_name)
                    price = med_data.get('price', 0) if med_data else 0
                    line_total = price * item.quantity
                    total += line_total
                    dosage_str = f" {item.dosage}" if item.dosage else ""
                    items_lines.append(
                        f"  \u2022 {item.medicine_name}{dosage_str} \u00d7 {item.quantity} \u2014 \u20b9{line_total:.2f}"
                    )

                header = ""
                if replacement_lines:
                    header = "\n".join(replacement_lines) + "\n\n"

                confirmation_message = (
                    header
                    + "Please confirm your order:\n\n"
                    + "\n".join(items_lines)
                    + f"\n\nTotal: \u20b9{total:.2f}\n\n"
                    "Reply *YES* to confirm or *NO* to cancel."
                )

                # Open the confirmation gate
                state.conversation_phase = "awaiting_confirmation"
                token = confirmation_store.create(
                    session_id=request.session_id,
                    state_dict=state.model_dump(),
                    replacement_info=replacement_info,
                )
                state.confirmation_token = token
                conversation_service.transition_phase(
                    request.session_id, "awaiting_confirmation"
                )

                conversation_service.add_message(
                    session_id=request.session_id,
                    role="assistant",
                    content=confirmation_message,
                    agent_name="FRONT_DESK"
                )

                await trace_manager.emit(
                    session_id=request.session_id,
                    agent_name="FRONT_DESK",
                    step_name="Responding with order confirmation...",
                    action_type="response",
                    status="completed",
                    details={"message": confirmation_message}
                )
                await trace_manager.emit(
                    session_id=request.session_id,
                    agent_name="API Gateway",
                    step_name="Waiting for response",
                    action_type="event",
                    status="completed"
                )

                return ConversationResponse(
                    session_id=request.session_id,
                    message=confirmation_message,
                    intent=intent,
                    recommendations=recommendations,
                    needs_clarification=True,
                    patient_context=patient_context,
                    next_step="awaiting_confirmation",
                    severity_assessment=severity_assessment
                )
            else:
                response_message = "I couldn't find suitable medicines for your symptoms. Could you describe your symptoms in more detail?"
                
                conversation_service.add_message(
                    session_id=request.session_id,
                    role="assistant",
                    content=response_message,
                    agent_name="front_desk"
                )

                # Trace: Final response
                await trace_manager.emit(
                    session_id=request.session_id,
                    agent_name="ORCHESTRATOR",
                    step_name="Responding with a request for more details...",
                    action_type="response",
                    status="completed"
                )
                
                # Trace: Complete API Gateway
                await trace_manager.emit(
                    session_id=request.session_id,
                    agent_name="API Gateway",
                    step_name="Waiting for response",
                    action_type="event",
                    status="completed"
                )

                return ConversationResponse(
                    session_id=request.session_id,
                    message=response_message,
                    intent=intent,
                    needs_clarification=True,
                    patient_context=patient_context,
                    next_step="clarification"
                )
        
        elif intent == "known_medicine":
            # Search for specific medicine
            medicine_name = _extract_medicine_name(request.message)
            
            # Check if it's a generic request
            if not medicine_name:
                response_message = "I'd be happy to help you find the right medicine! Could you tell me:\n\n"
                response_message += "1. What symptoms are you experiencing? OR\n"
                response_message += "2. Which specific medicine are you looking for?\n\n"
                response_message += "For example: 'I have a headache' or 'I need Paracetamol'"
                
                conversation_service.add_message(
                    session_id=request.session_id,
                    role="assistant",
                    content=response_message,
                    agent_name="front_desk"
                )

                # Trace: Final response
                await trace_manager.emit(
                    session_id=request.session_id,
                    agent_name="ORCHESTRATOR",
                    step_name="Responding with helpful guidance...",
                    action_type="response",
                    status="completed"
                )
                
                # Trace: Complete API Gateway
                await trace_manager.emit(
                    session_id=request.session_id,
                    agent_name="API Gateway",
                    step_name="Waiting for response",
                    action_type="event",
                    status="completed"
                )

                return ConversationResponse(
                    session_id=request.session_id,
                    message=response_message,
                    intent="symptom",  # Redirect to symptom intent
                    needs_clarification=True,
                    patient_context=patient_context,
                    next_step="clarification"
                )
            
            # Check if it's an information query
            message_lower = request.message.lower()
            info_keywords = ["used for", "uses of", "tell me about", "information about", 
                           "how does", "what does", "what is", "what are"]
            is_info_query = any(keyword in message_lower for keyword in info_keywords)
            
            medicine = db.get_medicine(medicine_name)
            
            if medicine:
                # Check if this was a fuzzy match
                is_fuzzy_match = medicine.get("fuzzy_match", False)
                searched_name = medicine.get("searched_name", medicine_name)
                
                # Use Inventory Service for smart checks
                from src.services.inventory_service import InventoryService
                inventory_service = InventoryService()
                
                # Check availability (handles OOS + Substitutes)
                availability = inventory_service.check_availability([{"name": medicine["name"], "quantity": 1}])
                item_status = availability["items"][0]
                
                # Get complementary recommendations
                recommendations_list = inventory_service.get_complementary_recommendations([{"name": medicine["name"]}])
                
                recommendation = MedicineRecommendation(
                    medicine_name=medicine["name"],
                    price=medicine["price"],
                    dosage=None,
                    stock=medicine["stock"],
                    requires_prescription=medicine["requires_prescription"],
                    indications=medicine.get("indications"),
                    generic_equivalent=medicine.get("generic_equivalent"),
                    in_stock=medicine["stock"] > 0
                )
                
                # Build response message based on query type
                if is_info_query:
                    # Information query - provide details about the medicine
                    response_message = f"{medicine['name']} is used for:\n\n"
                    
                    if medicine.get("indications"):
                        response_message += f"{medicine['indications']}\n\n"
                    else:
                        response_message += "General pain relief and fever reduction.\n\n"
                    
                    response_message += f"Price: ₹{medicine['price']}\n"
                    
                    if medicine["requires_prescription"]:
                        response_message += "⚠️ This medicine requires a prescription.\n"
                    
                    if medicine["stock"] > 0:
                        response_message += f"\nCurrently in stock ({medicine['stock']} available). Would you like to order it?"
                    else:
                        response_message += "\nCurrently out of stock."
                        if item_status.get("alternatives"):
                            alt_names = [alt['name'] for alt in item_status['alternatives']]
                            response_message += f"\n💡 We have these alternatives available: {', '.join(alt_names)}"
                        elif medicine.get("generic_equivalent"):
                            response_message += f" Alternative: {medicine['generic_equivalent']}"
                else:
                    # Purchase query - show availability
                    if is_fuzzy_match:
                        # Fuzzy match - ask for confirmation
                        response_message = f"Did you mean '{medicine['name']}'? "
                        
                        if medicine.get("similarity"):
                            # Show similarity if available
                            similarity_pct = int(medicine["similarity"] * 100)
                            response_message += f"(I found a {similarity_pct}% match for '{searched_name}')\n\n"
                        else:
                            response_message += f"(I couldn't find '{searched_name}' exactly)\n\n"
                        
                        response_message += f"Price: ₹{medicine['price']}. "
                    else:
                        # Exact match
                        response_message = f"I found {medicine['name']}. Price: ₹{medicine['price']}. "
                    
                    if medicine["requires_prescription"]:
                        response_message += "This medicine requires a prescription. "
                    
                    if item_status["available"]:
                        response_message += f"In stock ({medicine['stock']} available). Would you like to add it to your cart?"
                        
                        # Add Bundling Recommendations
                        if recommendations_list:
                            rec = recommendations_list[0] # Take top recommendation
                            response_message += f"\n\n💡 **Pharmacist Tip:** Since you're buying {medicine['name']}, I recommend adding **{rec['medicine']}** {rec['reason'].lower()}"
                    else:
                        response_message += "Currently out of stock. "
                        if item_status.get("alternatives"):
                            alt = item_status['alternatives'][0] # Take best alternative
                            response_message += f"\n\n🔄 **Substitute Available:** We have **{alt['name']}** (₹{alt['price']}) which is a generic equivalent. Would you like that instead?"
                            
                            # Update recommendation object to point to the substitute? 
                            # Maybe clearer to keep original intent but offer substitute in text.
                        elif medicine.get("generic_equivalent"):
                            response_message += f"Alternative: {medicine['generic_equivalent']}"
                
                if not is_info_query and not is_fuzzy_match:
                    # Extract quantity/dosage from user message
                    extracted = front_desk_agent.extract_medicine_items(request.message)
                    qty = 1
                    dosage_val = None
                    if extracted:
                        qty = extracted[0].quantity
                        dosage_val = extracted[0].dosage

                    order_items = [
                        OrderItem(
                            medicine_name=medicine["name"],
                            dosage=dosage_val,
                            quantity=qty
                        )
                    ]

                    state = PharmacyState(
                        user_id=session.get("user_id") or request.session_id,
                        session_id=request.session_id,
                        whatsapp_phone=patient_context.get("phone") or session.get("whatsapp_phone"),
                        user_message=request.message,
                        intent=intent,
                        extracted_items=order_items
                    )
                    state.trace_metadata["front_desk"] = {"patient_context": patient_context}

                    # Build confirmation message (look up price from DB)
                    price = medicine.get('price', 0)
                    line_total = price * qty
                    dosage_str = f" {dosage_val}" if dosage_val else ""
                    items_text = f"  \u2022 {medicine['name']}{dosage_str} \u00d7 {qty} \u2014 \u20b9{line_total:.2f}"
                    confirmation_message = (
                        f"Please confirm your order:\n\n{items_text}\n\n"
                        f"Total: \u20b9{line_total:.2f}\n\n"
                        "Reply *YES* to confirm or *NO* to cancel."
                    )

                    # Open the confirmation gate with idempotency token
                    state.conversation_phase = "awaiting_confirmation"
                    token = confirmation_store.create(
                        session_id=request.session_id,
                        state_dict=state.model_dump(),
                    )
                    state.confirmation_token = token
                    conversation_service.transition_phase(
                        request.session_id, "awaiting_confirmation"
                    )
                    response_message = confirmation_message
                    conversation_service.add_message(
                        session_id=request.session_id,
                        role="assistant",
                        content=response_message,
                        agent_name="FRONT_DESK"
                    )
                else:
                    # For info queries or fuzzy matches, stay conversational/seek clarification
                    conversation_service.add_message(
                        session_id=request.session_id,
                        role="assistant",
                        content=response_message,
                        agent_name="inventory",
                        extra_data={
                            "medicine": medicine,
                            "fuzzy_match": is_fuzzy_match,
                            "info_query": is_info_query,
                            "recommendations": recommendations_list
                        }
                    )

                # Trace: Final response
                await trace_manager.emit(
                    session_id=request.session_id,
                    agent_name="FRONT_DESK" if (not is_info_query and not is_fuzzy_match) else "ORCHESTRATOR",
                    step_name="Responding with medicine details...",
                    action_type="response",
                    status="completed"
                )

                # Trace: Complete API Gateway
                await trace_manager.emit(
                    session_id=request.session_id,
                    agent_name="API Gateway",
                    step_name="Waiting for response",
                    action_type="event",
                    status="completed"
                )

                return ConversationResponse(
                    session_id=request.session_id,
                    message=response_message,
                    intent=intent,
                    recommendations=[recommendation],
                    needs_clarification=True if (not is_info_query and not is_fuzzy_match) else (is_fuzzy_match and not is_info_query),
                    patient_context=patient_context,
                    next_step="awaiting_confirmation" if (not is_info_query and not is_fuzzy_match) else ("add_to_cart" if not is_fuzzy_match else "confirm_medicine")
                )
            else:
                response_message = f"I couldn't find '{medicine_name}' in our inventory. Could you check the spelling or try a different medicine?"
                
                conversation_service.add_message(
                    session_id=request.session_id,
                    role="assistant",
                    content=response_message,
                    agent_name="inventory"
                )
                
                # Trace: Complete API Gateway
                await trace_manager.emit(
                    session_id=request.session_id,
                    agent_name="API Gateway",
                    step_name="Waiting for response",
                    action_type="event",
                    status="completed"
                )

                return ConversationResponse(
                    session_id=request.session_id,
                    message=response_message,
                    intent=intent,
                    needs_clarification=True,
                    patient_context=patient_context,
                    next_step="clarification"
                )
        
        elif intent == "prescription_upload":
            response_message = "Please upload your prescription image using the camera button or file upload. I'll validate it and process your order."
            
            conversation_service.add_message(
                session_id=request.session_id,
                role="assistant",
                content=response_message,
                agent_name="front_desk"
            )
            
            # Trace: Complete API Gateway
            await trace_manager.emit(
                session_id=request.session_id,
                agent_name="API Gateway",
                step_name="Waiting for response",
                action_type="event",
                status="completed"
            )
            
            return ConversationResponse(
                session_id=request.session_id,
                message=response_message,
                intent=intent,
                needs_clarification=False,
                patient_context=patient_context,
                next_step="upload_prescription"
            )
        
        elif intent == "refill":
            response_message = "I can help you refill your previous order. Let me check your order history..."
            
            conversation_service.add_message(
                session_id=request.session_id,
                role="assistant",
                content=response_message,
                agent_name="proactive_intelligence"
            )
            
            # Trace: Complete API Gateway
            await trace_manager.emit(
                session_id=request.session_id,
                agent_name="API Gateway",
                step_name="Waiting for response",
                action_type="event",
                status="completed"
            )

            return ConversationResponse(
                session_id=request.session_id,
                message=response_message,
                intent=intent,
                needs_clarification=False,
                patient_context=patient_context,
                next_step="refill_order"
            )
        
        else:
            # Default response
            # Check if we have a PID yet. If not, ask for phone number to register.
            current_session = conversation_service.get_session(request.session_id)
            user_id = current_session.get("user_id")
            
            is_guest = not user_id or user_id.startswith("sess_") or user_id.startswith("anon_")
            
            response_message = "I'm here to help! "
            
            if is_guest and turn_count > 1:
                 response_message += "By the way, may I have your phone number to set up a patient ID for refill reminders? "
                 response_message += "Otherwise, just describe your symptoms or what you're looking for."
            else:
                response_message += "You can describe your symptoms, ask for a specific medicine, or upload a prescription."
            
            conversation_service.add_message(
                session_id=request.session_id,
                role="assistant",
                content=response_message,
                agent_name="front_desk"
            )
            
            # Trace: Complete API Gateway
            await trace_manager.emit(
                session_id=request.session_id,
                agent_name="API Gateway",
                step_name="Waiting for response",
                action_type="event",
                status="completed"
            )

            # Trace: Complete API Gateway
            await trace_manager.emit(
                session_id=request.session_id,
                agent_name="API Gateway",
                step_name="Waiting for response",
                action_type="event",
                status="completed"
            )

            return ConversationResponse(
                session_id=request.session_id,
                message=response_message,
                intent=intent,
                needs_clarification=True,
                patient_context=patient_context,
                next_step="clarification"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Conversation error: {str(e)}"
        )


# ------------------------------------------------------------------
# CONFIRMATION GATE ENDPOINT
# ------------------------------------------------------------------

@router.post("/confirm", response_model=ConfirmOrderResponse)
async def confirm_order(request: ConfirmOrderRequest):
    """
    Explicit YES/NO confirmation gate for pending orders.

    This endpoint is the canonical trigger for fulfillment. It:
    - Validates the session + idempotency token
    - Enforces the 5-minute TTL
    - On YES: transitions state → fulfillment_executing → completed
    - On NO:  transitions state → collecting_items
    - Idempotent: second YES with same token returns order_id without re-executing

    The fulfillment_agent hard gate (ConfirmationRequiredError) ensures
    that even a direct graph invocation cannot bypass this step.
    """
    from src.services.observability_service import trace_manager

    # Validate session
    session = conversation_service.get_session(request.session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    user_response = request.user_response.strip().upper()
    if user_response not in ("YES", "NO"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="user_response must be 'YES' or 'NO'"
        )

    if user_response == "NO":
        confirmation_store.cancel(request.session_id)
        conversation_service.transition_phase(request.session_id, "collecting_items")
        conversation_service.add_message(
            session_id=request.session_id,
            role="assistant",
            content="Order cancelled. How else can I help you?",
            agent_name="front_desk"
        )
        return ConfirmOrderResponse(
            session_id=request.session_id,
            status="cancelled",
            message="Order cancelled. How else can I help you?"
        )

    # --- YES path ---
    # Try to consume (atomic: first call succeeds, subsequent calls return None)
    entry = confirmation_store.consume(request.session_id, request.confirmation_token)

    if entry is None:
        # Either expired or token mismatch
        pending = confirmation_store.get_pending(request.session_id)
        if pending is None:
            # Truly expired
            return ConfirmOrderResponse(
                session_id=request.session_id,
                status="expired",
                message="Confirmation link has expired (5-minute limit). Please start a new order."
            )
        else:
            # Token mismatch
            return ConfirmOrderResponse(
                session_id=request.session_id,
                status="invalid",
                message="Invalid confirmation token. Please use the token provided with your order summary."
            )

    # Hydrate state and set the confirmation flag
    pending_state = PharmacyState(**entry["pending_pharmacy_state"])
    pending_state.confirmation_confirmed = True
    pending_state.conversation_phase = "fulfillment_executing"

    conversation_service.transition_phase(request.session_id, "fulfillment_executing")

    replacement_info = entry.get("replacement_info") or {}
    requires_override = bool(replacement_info.get("requires_pharmacist_override", False))

    await trace_manager.emit(
        session_id=request.session_id,
        agent_name="ORCHESTRATOR",
        step_name="Order confirmed — executing fulfillment",
        action_type="event",
        status="started",
        details={"token": request.confirmation_token}
    )

    try:
        final_state = fulfillment_agent(pending_state)
        response_message = format_order_confirmation(final_state)
        conversation_service.transition_phase(request.session_id, "completed")

        conversation_service.add_message(
            session_id=request.session_id,
            role="assistant",
            content=response_message,
            agent_name="fulfillment"
        )

        await trace_manager.emit(
            session_id=request.session_id,
            agent_name="ORCHESTRATOR",
            step_name="Fulfillment complete",
            action_type="response",
            status="completed",
            details={"order_id": final_state.order_id}
        )

        return ConfirmOrderResponse(
            session_id=request.session_id,
            status="confirmed",
            message=response_message,
            order_id=final_state.order_id,
            requires_pharmacist_override=requires_override
        )

    except ConfirmationRequiredError:
        # Should never happen — state.confirmation_confirmed was just set True
        return ConfirmOrderResponse(
            session_id=request.session_id,
            status="invalid",
            message="Internal error: confirmation gate raised unexpectedly. Please contact support."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fulfillment failed: {str(e)}"
        )


@router.post("/voice", response_model=VoiceInputResponse)
async def voice_input(
    session_id: str,
    audio: UploadFile = File(..., description="Audio file (WAV, MP3, WebM, etc.)")
):
    """
    Process voice input and get AI response.
    
    This endpoint:
    1. Transcribes audio using Whisper
    2. Processes transcription through conversation pipeline
    3. Returns both transcription and AI response
    
    Supported formats: WAV, MP3, WebM, OGG, FLAC
    Max file size: 10 MB
    
    Args:
        session_id: Session identifier (query parameter)
        audio: Audio file upload
    """
    try:
        # Validate session exists
        session = conversation_service.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Validate file size (10MB max)
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
        audio_bytes = await audio.read()
        
        if len(audio_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Audio file too large. Max size: {MAX_FILE_SIZE / 1024 / 1024}MB"
            )
        
        from src.services.observability_service import trace_manager

        # Determine audio format from filename
        audio_format = audio.filename.split('.')[-1].lower() if audio.filename else "wav"

        # Trace: Start
        await trace_manager.emit(
            session_id=session_id,
            agent_name="API Gateway",
            step_name="Received voice message",
            action_type="event",
            status="started",
            details={"filename": audio.filename}
        )

        # Transcribe audio
        print(f"\n🎤 Transcribing audio ({len(audio_bytes)} bytes, format: {audio_format})...")
        await trace_manager.emit(
            session_id=session_id,
            agent_name="Whisper Agent",
            step_name="Thinking: Listening to your voice...",
            action_type="thinking",
            status="started"
        )
        transcription_result = transcribe_audio_from_bytes(audio_bytes, format=audio_format)
        
        if not transcription_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Transcription failed: {transcription_result.get('error', 'Unknown error')}"
            )
        
        transcription = transcription_result["transcription"]
        
        await trace_manager.emit(
            session_id=session_id,
            agent_name="Whisper Agent",
            step_name="Thinking: Listening to your voice...",
            action_type="tool_use",
            status="completed",
            details={"transcription": transcription, "confidence": transcription_result.get("language_probability", 1.0)}
        )

        if not transcription or len(transcription.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No speech detected in audio. Please try again."
            )
        
        print(f"✅ Transcription: '{transcription}'")
        
        # Add transcription as user message
        conversation_service.add_message(
            session_id=session_id,
            role="user",
            content=transcription,
            extra_data={
                "input_type": "voice",
                "transcription_confidence": transcription_result.get("language_probability", 0.0),
                "language": transcription_result.get("language", "en"),
                "duration": transcription_result.get("duration", 0.0)
            }
        )
        
        # Get conversation history
        messages = conversation_service.get_messages(session_id)
        
        # ── Identity Resolution (same as text route) ─────────────────
        # Ensures voice users get a PID so switching to text doesn't re-greet
        session_user_id = session.get("user_id")
        is_returning_user = session_user_id and session_user_id.startswith("PID-")
        
        if not is_returning_user:
            phone_number = None
            is_phone_id = session_user_id and identity_agent.extract_phone_number(session_user_id)
            if is_phone_id:
                phone_number = identity_agent.extract_phone_number(session_user_id)
            
            if phone_number:
                patient_info = identity_agent.resolve_identity(phone_number)
                pid = patient_info["pid"]
                conversation_service.update_session(
                    session_id=session_id,
                    user_id=pid,
                    patient_context={"pid": pid, "phone": patient_info["phone"], "name": patient_info.get("name")}
                )
                print(f"🆔 Voice call: resolved identity → {pid}")
        
        # Step 1: Classify intent
        await trace_manager.emit(
            session_id=session_id,
            agent_name="Front Desk Agent",
            step_name="Thinking: Analyzing your request to understand how to help...",
            action_type="thinking",
            status="started"
        )
        intent_result = front_desk_agent.classify_intent(
            message=transcription,
            conversation_history=messages
        )
        await trace_manager.emit(
            session_id=session_id,
            agent_name="Front Desk Agent",
            step_name="Thinking: Analyzing your request to understand how to help...",
            action_type="decision",
            status="completed",
            details={"intent": intent_result.get("intent"), "language": intent_result.get("language")}
        )
        
        intent = intent_result.get("intent", "symptom")
        
        # ── Intent Inheritance (same as text route) ──────────────────
        # If user was discussing symptoms and now says something vague, keep the symptom flow
        previous_intent = session.get("intent")
        if previous_intent == "symptom" and intent != "symptom":
            last_assistant = next(
                (m for m in reversed(messages) if m.get("role") == "assistant"), None
            )
            symptom_flow_keywords = [
                "how long", "duration", "severity", "symptoms",
                "experiencing", "feeling", "describe", "pain",
                "sorry to hear", "tell me more"
            ]
            is_symptom_followup = last_assistant and any(
                kw in (last_assistant.get("content", "")).lower()
                for kw in symptom_flow_keywords
            )
            if is_symptom_followup or intent in ["unknown", "greeting", "generic_help", "refill"] or intent_result.get("confidence", 1.0) < 0.5:
                print(f"🧠 Voice: inheriting previous intent '{previous_intent}' (was '{intent}')")
                intent = previous_intent
        
        # Check for client-side triggers
        client_action = None
        if intent == "prescription_upload":
            client_action = "OPEN_CAMERA"
        
        # Step 2: Extract patient context
        patient_context = front_desk_agent.extract_patient_context(
            message=transcription,
            conversation_history=messages
        )
        await trace_manager.emit(
            session_id=session_id,
            agent_name="Front Desk Agent",
            step_name="Thinking: Gathering relevant details from our conversation...",
            action_type="tool_use",
            status="completed",
            details={"patient_context": patient_context}
        )
        
        # Update session
        conversation_service.update_session(
            session_id=session_id,
            intent=intent,
            patient_context=patient_context
        )
        
        # Special handling for prescription upload - skip clarification and return immediately
        if intent == "prescription_upload":
            response_message = "📸 Camera opened! Please show your prescription to the camera."
            
            conversation_service.add_message(
                session_id=session_id,
                role="assistant",
                content=response_message,
                agent_name="front_desk"
            )

            # Trace: Complete API Gateway
            await trace_manager.emit(
                session_id=session_id,
                agent_name="API Gateway",
                step_name="Waiting for response",
                action_type="event",
                status="completed"
            )
            
            return VoiceInputResponse(
                session_id=session_id,
                transcription=transcription,
                transcription_confidence=transcription_result.get("language_probability", 0.0),
                language=transcription_result.get("language", "en"),
                message=response_message,
                intent=intent,
                needs_clarification=False,
                patient_context=patient_context,
                next_step="capture_prescription",
                client_action=client_action
            )
        
        # Step 3: Check if clarification needed
        await trace_manager.emit(
            session_id=session_id,
            agent_name="Front Desk Agent",
            step_name="Ask Clarification",
            action_type="thinking",
            status="started"
        )
        turn_count = session.get("turn_count", 0)
        clarifying_question = front_desk_agent.generate_clarifying_question(
            intent=intent,
            message=transcription,
            patient_context=patient_context,
            turn_count=turn_count,
            language=transcription_result.get("language", "en"),
            conversation_history=messages
        )
        
        if clarifying_question:
            # Ask clarifying question
            await trace_manager.emit(
                session_id=session_id,
                agent_name="Front Desk Agent",
                step_name="Ask Clarification",
                action_type="decision",
                status="completed",
                details={"question": clarifying_question}
            )
            conversation_service.add_message(
                session_id=session_id,
                role="assistant",
                content=clarifying_question,
                agent_name="front_desk"
            )

            # Trace: Final response
            await trace_manager.emit(
                session_id=session_id,
                agent_name="ORCHESTRATOR",
                step_name="Responding with a clarification question...",
                action_type="response",
                status="completed"
            )

            # Trace: Complete API Gateway
            await trace_manager.emit(
                session_id=session_id,
                agent_name="API Gateway",
                step_name="Waiting for response",
                action_type="event",
                status="completed"
            )
            
            return VoiceInputResponse(
                session_id=session_id,
                transcription=transcription,
                transcription_confidence=transcription_result.get("language_probability", 0.0),
                language=transcription_result.get("language", "en"),
                message=clarifying_question,
                intent=intent,
                needs_clarification=True,
                clarifying_question=clarifying_question,
                patient_context=patient_context,
                next_step="clarification",
                client_action=client_action
            )
        
        # Step 4: Generate recommendations based on intent
        if intent == "symptom":
            # Use ALL user messages for symptom matching (not just current transcription)
            all_messages = conversation_service.get_messages(session_id)
            # Filter relevant symptom messages to remove conversational noise
            user_msgs = [
                msg.get("content", "") for msg in messages
                if msg.get("role") == "user"
                and len(msg.get("content", "").strip()) > 3
                and msg.get("content", "").strip().lower() not in ("yes", "no", "ok", "hello", "hi", "hey")
            ]
            combined_symptoms = " ".join(user_msgs[-3:])  # Last 3 relevant messages only
            
            # Truncate to prevent token overflow (Fix 8)       
            recommendations = await _get_symptom_recommendations(
                combined_symptoms,
                patient_context
            )
            await trace_manager.emit(
                session_id=session_id,
                agent_name="Medical Agent",
                step_name="Find Medicines",
                action_type="tool_use",
                status="completed",
                details={"found": len(recommendations) if recommendations else 0}
            )
            
            if recommendations:
                # NEW: Pipeline Integration - Create PharmacyState and run the graph
                order_items = [
                    OrderItem(
                        medicine_name=r.medicine_name,
                        dosage=r.dosage,
                        quantity=1
                    ) for r in recommendations
                ]
                
                state = PharmacyState(
                    user_id=session.get("user_id") or session_id,
                    session_id=session_id,
                    whatsapp_phone=patient_context.get("phone") or session.get("whatsapp_phone"),
                    user_message=transcription,
                    intent=intent,
                    extracted_items=order_items
                )
                state.trace_metadata["front_desk"] = {"patient_context": patient_context}
                
                # Run through full LangGraph pipeline
                result = await agent_graph.ainvoke(state)
                final_state = PharmacyState(**result) if isinstance(result, dict) else result
                response_message = format_order_confirmation(final_state)
                
                conversation_service.add_message(
                    session_id=session_id,
                    role="assistant",
                    content=response_message,
                    agent_name="orchestrator",
                    extra_data={
                        "recommendations": [r.dict() for r in recommendations],
                        "pipeline_result": final_state.dict(exclude={"trace_metadata"})
                    }
                )

                # Trace: Final response
                await trace_manager.emit(
                    session_id=session_id,
                    agent_name="ORCHESTRATOR",
                    step_name="Responding with validated recommendations...",
                    action_type="response",
                    status="completed"
                )

                # Trace: Complete API Gateway
                await trace_manager.emit(
                    session_id=session_id,
                    agent_name="API Gateway",
                    step_name="Waiting for response",
                    action_type="event",
                    status="completed"
                )
                
                return VoiceInputResponse(
                    session_id=session_id,
                    transcription=transcription,
                    transcription_confidence=transcription_result.get("language_probability", 0.0),
                    language=transcription_result.get("language", "en"),
                    message=response_message,
                    intent=intent,
                    recommendations=recommendations,
                    needs_clarification=False,
                    patient_context=patient_context,
                    next_step="add_to_cart"
                )
            else:
                response_message = "I couldn't find suitable medicines for your symptoms. Could you describe your symptoms in more detail?"
                
                conversation_service.add_message(
                    session_id=session_id,
                    role="assistant",
                    content=response_message,
                    agent_name="front_desk"
                )

                # Trace: Final response
                await trace_manager.emit(
                    session_id=session_id,
                    agent_name="ORCHESTRATOR",
                    step_name="Responding with a request for more details...",
                    action_type="response",
                    status="completed"
                )
                
                # Trace: Complete API Gateway
                await trace_manager.emit(
                    session_id=session_id,
                    agent_name="API Gateway",
                    step_name="Waiting for response",
                    action_type="event",
                    status="completed"
                )
                
                return VoiceInputResponse(
                    session_id=session_id,
                    transcription=transcription,
                    transcription_confidence=transcription_result.get("language_probability", 0.0),
                    language=transcription_result.get("language", "en"),
                    message=response_message,
                    intent=intent,
                    needs_clarification=True,
                    patient_context=patient_context,
                    next_step="clarification"
                )
        
        elif intent == "known_medicine":
            # Search for specific medicine
            await trace_manager.emit(
                session_id=session_id,
                agent_name="Inventory Agent",
                step_name="Check Availability",
                action_type="tool_use",
                status="started"
            )
            medicine_name = _extract_medicine_name(transcription)
            medicine = db.get_medicine(medicine_name)
            await trace_manager.emit(
                session_id=session_id,
                agent_name="Inventory Agent",
                step_name="Check Availability",
                action_type="tool_use",
                status="completed",
                details={"found": medicine is not None, "medicine": medicine_name}
            )
            
            if medicine:
                # NEW: Pipeline Integration for direct purchases
                order_items = [
                    OrderItem(
                        medicine_name=medicine["name"],
                        dosage=None, # Will be inferred by validator
                        quantity=1
                    )
                ]
                
                state = PharmacyState(
                    user_id=session.get("user_id") or session_id,
                    session_id=session_id,
                    whatsapp_phone=patient_context.get("phone") or session.get("whatsapp_phone"),
                    user_message=transcription,
                    intent=intent,
                    extracted_items=order_items
                )
                state.trace_metadata["front_desk"] = {"patient_context": patient_context}
                
                # Run through full LangGraph pipeline
                result = await agent_graph.ainvoke(state)
                final_state = PharmacyState(**result) if isinstance(result, dict) else result
                response_message = format_order_confirmation(final_state)
                
                recommendation = MedicineRecommendation(
                    medicine_name=medicine["name"],
                    price=medicine["price"],
                    dosage=None,
                    stock=medicine["stock"],
                    requires_prescription=medicine["requires_prescription"],
                    indications=medicine.get("indications"),
                    generic_equivalent=medicine.get("generic_equivalent"),
                    in_stock=medicine["stock"] > 0
                )
                
                conversation_service.add_message(
                    session_id=session_id,
                    role="assistant",
                    content=response_message,
                    agent_name="orchestrator",
                    extra_data={
                        "medicine": medicine,
                        "pipeline_result": final_state.dict(exclude={"trace_metadata"})
                    }
                )

                # Trace: Complete API Gateway
                await trace_manager.emit(
                    session_id=session_id,
                    agent_name="API Gateway",
                    step_name="Waiting for response",
                    action_type="event",
                    status="completed"
                )
                
                return VoiceInputResponse(
                    session_id=session_id,
                    transcription=transcription,
                    transcription_confidence=transcription_result.get("language_probability", 0.0),
                    language=transcription_result.get("language", "en"),
                    message=response_message,
                    intent=intent,
                    recommendations=[recommendation],
                    needs_clarification=False,
                    patient_context=patient_context,
                    next_step="add_to_cart"
                )
            else:
                response_message = f"I couldn't find '{medicine_name}' in our inventory. Could you check the spelling or try a different medicine?"
                
                conversation_service.add_message(
                    session_id=session_id,
                    role="assistant",
                    content=response_message,
                    agent_name="inventory"
                )
                
                # Trace: Complete API Gateway
                await trace_manager.emit(
                    session_id=session_id,
                    agent_name="API Gateway",
                    step_name="Receive Voice",
                    action_type="event",
                    status="completed"
                )
                
                return VoiceInputResponse(
                    session_id=session_id,
                    transcription=transcription,
                    transcription_confidence=transcription_result.get("language_probability", 0.0),
                    language=transcription_result.get("language", "en"),
                    message=response_message,
                    intent=intent,
                    needs_clarification=True,
                    patient_context=patient_context,
                    next_step="clarification"
                )

        elif intent == "prescription_upload":
            response_message = "I see. I've opened the camera for you. Please show me your prescription."
            
            conversation_service.add_message(
                session_id=session_id,
                role="assistant",
                content=response_message,
                agent_name="front_desk"
            )
            
            return VoiceInputResponse(
                session_id=session_id,
                transcription=transcription,
                transcription_confidence=transcription_result.get("language_probability", 0.0),
                language=transcription_result.get("language", "en"),
                message=response_message,
                intent=intent,
                needs_clarification=False,
                patient_context=patient_context,
                next_step="capture_prescription",
                client_action="OPEN_CAMERA"
            )
        
        else:
            # Default response for other intents
            response_message = "I heard you! I'm here to help with symptoms, specific medicines, or prescription uploads."
            
            conversation_service.add_message(
                session_id=session_id,
                role="assistant",
                content=response_message,
                agent_name="front_desk"
            )
            
            return VoiceInputResponse(
                session_id=session_id,
                transcription=transcription,
                transcription_confidence=transcription_result.get("language_probability", 0.0),
                language=transcription_result.get("language", "en"),
                message=response_message,
                intent=intent,
                needs_clarification=True,
                patient_context=patient_context,
                next_step="clarification"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"CRITICAL ERROR in voice_input: {str(e)}", exc_info=True)
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Voice input error: {str(e)}"
        )


@router.post("/cart/add", response_model=AddToCartResponse)
async def add_to_cart(request: AddToCartRequest):
    """
    Add medicine to cart.
    
    This adds a medicine to the session's cart for later checkout.
    """
    try:
        # Validate session
        session = conversation_service.get_session(request.session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Validate medicine exists and in stock
        medicine = db.get_medicine(request.medicine_name)
        if not medicine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Medicine '{request.medicine_name}' not found"
            )
        
        if medicine["stock"] < request.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock. Available: {medicine['stock']}"
            )
        
        # Add to cart (store in session metadata)
        cart_item = {
            "medicine_name": medicine["name"],
            "quantity": request.quantity,
            "dosage": request.dosage,
            "price": medicine["price"],
            "requires_prescription": medicine["requires_prescription"],
            "added_at": datetime.now().isoformat()
        }
        
        # Store cart in message
        conversation_service.add_message(
            session_id=request.session_id,
            role="system",
            content=f"Added {request.medicine_name} x{request.quantity} to cart",
            extra_data={"cart_item": cart_item, "action": "add_to_cart"}
        )
        
        # Get all cart items from messages
        messages = conversation_service.get_messages(request.session_id)
        cart_items = [
            msg["extra_data"]["cart_item"]
            for msg in messages
            if msg.get("extra_data", {}).get("action") == "add_to_cart"
        ]
        
        response_message = f"Added {request.medicine_name} x{request.quantity} to your cart. "
        
        if medicine["requires_prescription"]:
            response_message += "Note: This medicine requires a prescription. "
        
        response_message += f"Total items in cart: {len(cart_items)}"
        
        # Add confirmation message
        conversation_service.add_message(
            session_id=request.session_id,
            role="assistant",
            content=response_message,
            agent_name="inventory"
        )
        
        return AddToCartResponse(
            session_id=request.session_id,
            message=response_message,
            cart_items=cart_items,
            total_items=len(cart_items)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add to cart: {str(e)}"
        )


@router.get("/{session_id}", response_model=ConversationHistoryResponse)
async def get_conversation_history(session_id: str):
    """
    Get complete conversation history.
    
    Returns all messages and session metadata.
    """
    try:
        history = conversation_service.get_conversation_history(session_id)
        
        if not history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        session = history["session"]
        messages = history["messages"]
        
        return ConversationHistoryResponse(
            session_id=session["session_id"],
            user_id=session["user_id"],
            status=session["status"],
            intent=session.get("intent"),
            turn_count=session["turn_count"],
            messages=messages,
            created_at=session["created_at"],
            updated_at=session["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation history: {str(e)}"
        )


# ------------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------------

async def _get_symptom_recommendations(
    message: str,
    patient_context: Dict
) -> List[MedicineRecommendation]:
    """
    Get medicine recommendations based on symptoms.

    Two-pass approach:
    1. Fast keyword pass via SymptomMedicineMapping table
    2. Semantic fallback using sentence-transformer cosine similarity
       against medicine indications when keyword pass returns < 2 results
    """
    from src.db_config import get_db_context
    from src.services import llm_service

    # --- Clean up noisy combined conversation into a concise list of symptoms ---
    prompt = f"""Extract ONLY the core medical symptoms from the following conversation text.
Do not include ages, durations, feelings, greetings, or conversational filler.
Return them as a simple comma-separated list. If no clear symptoms exist, return "unknown".

Text: {message}
Symptoms:"""
    
    try:
        text_resp, _ = llm_service._generate_text_with_hybrid_fallback(
            prompt=prompt,
            is_json=False,
            temperature=0.0
        )
        cleaned_symptoms_text = text_resp.strip().lower()
        print(f"SYMPTOM RECS: Cleaned raw input '{message[:50]}...' into '{cleaned_symptoms_text}'")
    except Exception as e:
        print(f"SYMPTOM RECS: Failed to clean symptoms via LLM: {e}")
        cleaned_symptoms_text = message
        
    # Use the cleaned text for the rest of the matching logic
    message = cleaned_symptoms_text

    # ── Normalise message ──────────────────────────────────────────────
    message_lower = message.lower()

    symptom_synonyms = {
        "stomach ache": "stomach pain",
        "stomachache": "stomach pain",
        "tummy ache": "stomach pain",
        "belly ache": "stomach pain",
        "head ache": "headache",
        "throwing up": "vomiting",
        "can't sleep": "insomnia",
        "cannot sleep": "insomnia",
        # Hinglish
        "bukhar": "fever",
        "sir dard": "headache",
        "sar dard": "headache",
        "dard": "pain",
        "khasi": "cough",
        "zukam": "cold",
        "nazla": "cold",
        "pet dard": "stomach pain",
    }
    for synonym, standard in symptom_synonyms.items():
        if synonym in message_lower:
            message_lower = message_lower.replace(synonym, standard)

    message_normalized = message_lower.replace(" ", "")

    recommendations: List[MedicineRecommendation] = []
    seen_medicines: set = set()

    # ── Pass 1: Semantic Search (Primary) ──────────────────────────────
    try:
        from src.services.semantic_search_service import semantic_search_service
        from src.db_config import get_db_context
        
        if semantic_search_service.enabled:
            # 0.35 is a good baseline for SentenceTransformers
            individual_symptoms = [s.strip() for s in message.split(',')] if ',' in message else [message]
            
            for symp in individual_symptoms:
                if not symp or symp == "unknown": continue
                    
                semantic_results = semantic_search_service.search(
                    symp, top_k=5, threshold=0.35
                )
                
                if semantic_results:
                    added = 0
                    with get_db_context() as db_session:
                        for med_name, score in semantic_results:
                            if med_name in seen_medicines:
                                continue
                                
                            medicine = db_session.query(Medicine).filter(
                                Medicine.name.ilike(f"%{med_name}%"),
                                Medicine.stock > 0
                            ).first()
                            
                            if medicine:
                                seen_medicines.add(medicine.name)
                                recommendations.append(
                                    MedicineRecommendation(
                                        medicine_name=medicine.name,
                                        price=medicine.price,
                                        dosage=None,
                                        stock=medicine.stock,
                                        requires_prescription=medicine.requires_prescription,
                                        indications=medicine.indications,
                                        generic_equivalent=medicine.generic_equivalent,
                                        in_stock=medicine.stock > 0,
                                    )
                                )
                                added += 1
                                if len(recommendations) >= 3:
                                    break
                    best_score = semantic_results[0][1] if semantic_results else 0.0
                    print(
                        f"SYMPTOM RECS: Pass 1 (semantic) for '{symp}' added {added} result(s) "
                        f"(best score={best_score:.3f})"
                    )
                    if len(recommendations) >= 3:
                        break

    except Exception as e:
        print(f"SYMPTOM RECS: Semantic pass failed: {e}")

    # ── Pass 2: Keyword matching fallback (Noisy table) ────────────────
    if len(recommendations) < 3:
        try:
            with get_db_context() as db_session:
                import re
                mappings = db_session.query(SymptomMedicineMapping).all()

                for mapping in mappings:
                    symptom_normalized = mapping.symptom.replace(" ", "")
                    # Use strictly word boundaries to prevent generic substring matches 
                    pattern = r'\b' + re.escape(mapping.symptom) + r'\b'
                    
                    if re.search(pattern, message_lower):
                        medicine = db_session.query(Medicine).filter(
                            Medicine.id == mapping.medicine_id,
                            Medicine.stock > 0
                        ).first()

                        if medicine:
                            if medicine.name not in seen_medicines:
                                seen_medicines.add(medicine.name)
                                recommendations.append(
                                    MedicineRecommendation(
                                        medicine_name=medicine.name,
                                        price=medicine.price,
                                        dosage=None,
                                        stock=medicine.stock,
                                        requires_prescription=medicine.requires_prescription,
                                        indications=medicine.indications,
                                        generic_equivalent=medicine.generic_equivalent,
                                        in_stock=medicine.stock > 0,
                                    )
                                )
                                if len(recommendations) >= 3:
                                    break

            print(f"SYMPTOM RECS: Pass 2 (keyword fallback) found total {len(recommendations)} result(s)")
        except Exception as e:
            print(f"SYMPTOM RECS: Pass 2 (keyword fallback) failed: {e}")

    return recommendations[:3]


def _format_recommendations_message(recommendations: List[MedicineRecommendation]) -> str:
    """Format medicine recommendations as a message."""
    
    message = "Based on your symptoms, I recommend:\n\n"
    
    for i, rec in enumerate(recommendations, 1):
        message += f"{i}. {rec.medicine_name} - ₹{rec.price}\n"
        
        if rec.indications:
            message += f"   Used for: {rec.indications[:100]}...\n"
        
        if rec.requires_prescription:
            message += "   ⚠️ Requires prescription\n"
        
        if not rec.in_stock:
            message += "   ❌ Out of stock"
            if rec.generic_equivalent:
                message += f" (Alternative: {rec.generic_equivalent})"
            message += "\n"
        else:
            message += f"   ✅ In stock ({rec.stock} available)\n"
        
        message += "\n"
    
    message += "Would you like to add any of these to your cart?"
    
    return message


def _extract_medicine_name(message: str) -> Optional[str]:
    """
    Extract medicine name from message.

    Strategy:
    1. Fast stop-word filter — works for clear requests like "I need Paracetamol"
    2. Semantic fallback via sentence-transformer similarity against DB medicine names
       — handles indirect/natural phrasing like "do you have something like ibuprofen"
    """
    generic_terms = {
        "medicine", "medicines", "medication", "medications",
        "drug", "drugs", "pills", "tablets", "capsules",
    }
    stop_words = {
        "i", "need", "want", "have", "do", "you", "the", "a", "an", "for",
        "some", "any", "what", "is", "are", "used", "tell", "me", "about",
        "information", "how", "does", "work", "uses", "of", "get", "give",
        "can", "could", "please", "looking", "stock", "available", "buy",
        "sell", "carry", "something", "like", "similar", "to",
    }

    message_lower = message.lower().strip()
    words = message_lower.split()

    # If message is purely generic ("I need medicine"), bail early
    content_words = [
        w for w in words
        if w not in stop_words and w not in {"i", "need", "want", "have", "do", "you", "the", "a", "an", "for", "some", "any"}
    ]
    if content_words and all(w in generic_terms for w in content_words):
        return None

    # ── Fast path: stop-word filter ────────────────────────────────────
    medicine_words = [
        w for w in words
        if w not in stop_words and w not in generic_terms and len(w) > 2
    ]
    if medicine_words:
        candidate = " ".join(medicine_words).title()
        # Quick DB check to see if this candidate actually exists
        try:
            from src.database import Database
            db_check = Database()
            result = db_check.get_medicine(candidate)
            if result:
                print(f"EXTRACT: Fast path found '{result['name']}' for '{candidate}'")
                return result["name"]
        except Exception:
            pass
        # If it's a short phrase (1-2 words), return it anyway so the 
        # inventory logic can say "I couldn't find 'X'" instead of hallucinating.
        # But if it's a long sentence of missed stopwords, fall through to semantic extraction.
        if len(medicine_words) <= 2:
            print(f"EXTRACT: Fast path short candidate '{candidate}' (DB check skipped/failed)")
            return candidate
            
        print(f"EXTRACT: Fast path long candidate '{candidate}' failed DB check. Falling to semantic.")

    # ── Semantic fallback ──────────────────────────────────────────────
    try:
        from src.services.intent_classifier import extract_medicine_name_semantic
        semantic_result = extract_medicine_name_semantic(message, threshold=0.55)
        if semantic_result:
            print(f"EXTRACT: Semantic path found '{semantic_result}'")
            return semantic_result
    except Exception as e:
        print(f"EXTRACT: Semantic fallback failed: {e}")

    return None
