"""
TELEGRAM PIPELINE INTEGRATION
==============================
Clean separation: Telegram bot → Agent pipeline
"""

from typing import Dict, Any
from src.state import PharmacyState
from src.vision_agent import vision_agent, pharmacist_agent, front_desk_agent
from src.agents import fulfillment_agent
from src.agents.medical_validator_agent import medical_validation_agent
from src.services.telegram_service import send_order_notification


# ------------------------------------------------------------------
# TEXT MESSAGE PROCESSING
# ------------------------------------------------------------------
async def process_text_message(
    user_id: str,
    telegram_chat_id: str,
    message: str
) -> Dict[str, Any]:
    """
    Process text message through agent pipeline.
    
    Pipeline:
    1. Front Desk Agent (intent + extraction)
    2. Pharmacist Agent (validation)
    3. Fulfillment Agent (order creation)
    4. Notification (Telegram)
    
    Args:
        user_id: User ID
        telegram_chat_id: Telegram chat ID for notifications
        message: User message text
        
    Returns:
        Response dictionary with message and status
    """
    try:
        # Initialize state
        state = PharmacyState(
            user_id=user_id,
            telegram_chat_id=telegram_chat_id,
            user_message=message
        )
        
        # Step 1: Front Desk Agent (intent classification + extraction)
        state = front_desk_agent(state)
        
        # Check intent
        if state.intent == "unknown":
            return {
                "success": True,
                "message": "I didn't understand that. Can you rephrase?",
                "state": state
            }
        
        if state.intent == "inquiry":
            return {
                "success": True,
                "message": "I can help with medicine information. What would you like to know?",
                "state": state
            }
        
        # Step 2: Medical Validation Agent (if prescription uploaded)
        if state.prescription_uploaded:
            state = medical_validation_agent(state)
            
            # Check validation result
            if state.pharmacist_decision == "rejected":
                issues_text = "\n".join([f"• {issue}" for issue in state.safety_issues])
                return {
                    "success": False,
                    "message": f"❌ *Prescription Rejected:*\n\n{issues_text}",
                    "state": state
                }
            
            if state.pharmacist_decision == "needs_review":
                issues_text = "\n".join([f"• {issue}" for issue in state.safety_issues])
                return {
                    "success": True,
                    "message": f"⏳ *Prescription Needs Review:*\n\n{issues_text}\n\nA pharmacist will review shortly.",
                    "state": state
                }
        
        # Step 3: Pharmacist Agent (inventory validation)
        if state.extracted_items:
            state = pharmacist_agent(state)
            
            # Check for safety issues
            if state.safety_issues:
                issues_text = "\n".join([f"• {issue}" for issue in state.safety_issues])
                return {
                    "success": False,
                    "message": f"⚠️ *Safety Issues Detected:*\n\n{issues_text}",
                    "state": state
                }
            
            # Step 4: Fulfillment Agent (order creation)
            if state.pharmacist_decision == "approved":
                state = fulfillment_agent(state)
                
                # Send notification
                if state.order_id and telegram_chat_id:
                    pass # Notification is handled by the caller or separate service to avoid recursion
                
                return {
                    "success": True,
                    "message": f"✅ *Order Confirmed!*\n\nOrder ID: `{state.order_id}`",
                    "state": state
                }
        
        return {
            "success": True,
            "message": "I'm processing your request...",
            "state": state
        }
        
    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        return {
            "success": False,
            "message": "Sorry, something went wrong. Please try again.",
            "error": str(e)
        }


# ------------------------------------------------------------------
# TELEGRAM COMMAND PROCESSING
# ------------------------------------------------------------------
async def process_telegram_command(
    user_id: str,
    telegram_chat_id: str,
    command: str,
    args: str = ""
) -> Dict[str, Any]:
    """
    Process specific Telegram commands.
    """
    from src.agents.identity_agent import IdentityAgent
    identity_agent = IdentityAgent()

    if command == "/start":
        # Check if already linked
        pid = identity_agent.get_pid_by_telegram(telegram_chat_id)
        
        if pid:
            return {
                "success": True,
                "message": f"Welcome back! You are linked to Patient ID: `{pid}`.\n\nYou will receive order updates here as well as refill reminders.",
                "state": None
            }
        else:
            # Need to link. Ask for phone number.
            return {
                "success": True,
                "message": (
                    "Welcome to Medisync! 🏥\n\n"
                    "To link your account and receive updates, please share your phone number.\n"
                    "You can type it (e.g., 9876543210) or use the button below."
                ),
                "state": None,
                "require_contact": True  # Signal to frontend/bot to show contact button
            }
            
    return {
        "success": False,
        "message": "Unknown command.",
        "state": None
    }

async def process_telegram_contact(
    telegram_chat_id: str,
    phone_number: str,
    first_name: str
) -> Dict[str, Any]:
    """
    Handle contact sharing from Telegram.
    """
    from src.agents.identity_agent import IdentityAgent
    identity_agent = IdentityAgent()
    
    # 1. Resolve identity (find existing patient or create new)
    # The normalization is handled inside resolve_identity via identity_agent logic usually, 
    # but let's ensure we pass it cleanly.
    normalized_phone = identity_agent._normalize_phone(phone_number)
    
    patient_info = identity_agent.resolve_identity(normalized_phone, name=first_name)
    pid = patient_info["pid"]
    
    # 2. Link Telegram ID
    identity_agent.link_telegram(pid, telegram_chat_id)
    
    # Emit PATIENT_IDENTIFIED event
    from src.internal_events import event_manager, PATIENT_IDENTIFIED
    await event_manager.emit(PATIENT_IDENTIFIED, {
        "pid": pid,
        "phone": normalized_phone,
        "source": "telegram",
        "telegram_id": telegram_chat_id
    })
    
    return {
        "success": True,
        "message": f"✅ *Successfully Linked!*\n\nYour Patient ID is `{pid}`.\n\nYou will now receive real-time updates for your medicine orders and refill reminders here.",
        "state": None
    }


# ------------------------------------------------------------------
# PRESCRIPTION IMAGE PROCESSING
# ------------------------------------------------------------------
async def process_prescription_image(
    user_id: str,
    telegram_chat_id: str,
    image_path: str
) -> Dict[str, Any]:
    """
    Process prescription image through vision agent.
    
    Pipeline:
    1. Vision Agent (OCR + parsing)
    2. Pharmacist Agent (validation)
    3. Fulfillment Agent (order creation)
    4. Notification (Telegram)
    
    Args:
        user_id: User ID
        telegram_chat_id: Telegram chat ID
        image_path: Path to prescription image
        
    Returns:
        Response dictionary
    """
    try:
        # Initialize state
        state = PharmacyState(
            user_id=user_id,
            telegram_chat_id=telegram_chat_id
        )
        
        # Step 1: Vision Agent (OCR + parsing)
        state = vision_agent(state, image_path, use_mock=False)
        
        # Check if prescription was uploaded
        if not state.prescription_uploaded:
            return {
                "success": False,
                "message": "⚠️ Could not process prescription image. Please try again with a clearer photo.",
                "state": state
            }
        
        # Step 2: Medical Validation Agent
        state = medical_validation_agent(state)
        
        # Check validation status
        validation_metadata = state.trace_metadata.get("medical_validator", {})
        validation_status = validation_metadata.get("status", "unknown")
        risk_score = validation_metadata.get("risk_score", 0.0)
        
        # Check verification status
        if state.pharmacist_decision == "approved":
            message = f"""
✅ *Prescription Approved*

Found {len(state.extracted_items)} medicine(s):
"""
            for item in state.extracted_items:
                message += f"\n• {item.medicine_name}"
                if item.dosage:
                    message += f" ({item.dosage})"
            
            message += f"\n\n*Risk Score:* {risk_score:.2f}"
            
            # Continue with inventory validation
            state = pharmacist_agent(state)
            
            if state.pharmacist_decision == "approved":
                state = fulfillment_agent(state)
                message += f"\n\n*Order ID:* `{state.order_id}`"
            
            return {
                "success": True,
                "message": message,
                "state": state
            }
        
        elif state.pharmacist_decision == "needs_review":
            # Needs review
            issues = "\n".join([f"• {issue}" for issue in state.safety_issues])
            return {
                "success": True,
                "message": f"⏳ *Prescription Under Review*\n\n{issues}\n\nA pharmacist will review shortly.",
                "state": state
            }
        else:
            # Rejected
            issues = "\n".join([f"• {issue}" for issue in state.safety_issues])
            return {
                "success": False,
                "message": f"❌ *Prescription Rejected*\n\n{issues}",
                "state": state
            }
        
    except Exception as e:
        print(f"❌ Vision pipeline error: {e}")
        return {
            "success": False,
            "message": "Sorry, could not process prescription. Please try again.",
            "error": str(e)
        }


# ------------------------------------------------------------------
# VOICE MESSAGE PROCESSING
# ------------------------------------------------------------------
async def process_voice_message(
    user_id: str,
    telegram_chat_id: str,
    audio_path: str
) -> Dict[str, Any]:
    """
    Process voice message through speech agent.
    
    Pipeline:
    1. Speech Agent (transcription)
    2. Front Desk Agent (intent + extraction)
    3. Pharmacist Agent (validation)
    4. Fulfillment Agent (order creation)
    
    Args:
        user_id: User ID
        telegram_chat_id: Telegram chat ID
        audio_path: Path to audio file
        
    Returns:
        Response dictionary
    """
    try:
        from src.services.speech_service import transcribe_audio
        
        # Step 1: Transcribe audio
        transcription_result = transcribe_audio(audio_path)
        
        if not transcription_result.get("success"):
            return {
                "success": False,
                "message": "⚠️ Could not transcribe voice message. Please try again.",
                "error": transcription_result.get("error")
            }
        
        transcription = transcription_result.get("transcription", "")
        
        # Step 2: Process as text message
        result = await process_text_message(
            user_id=user_id,
            telegram_chat_id=telegram_chat_id,
            message=transcription
        )
        
        # Add transcription to response
        result["transcription"] = transcription
        result["message"] = f"🎤 _{transcription}_\n\n{result['message']}"
        
        return result
        
    except Exception as e:
        print(f"❌ Voice pipeline error: {e}")
        return {
            "success": False,
            "message": "Sorry, could not process voice message. Please try again.",
            "error": str(e)
        }
