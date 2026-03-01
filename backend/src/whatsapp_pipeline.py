from typing import Dict, Any
import os
import httpx
import logging
from src.state import PharmacyState, OrderItem
from src.vision_agent import vision_agent, pharmacist_agent, front_desk_agent
from src.agents import fulfillment_agent
from src.agents.medical_validator_agent import medical_validation_agent
from src.agents.identity_agent import IdentityAgent
from src.services.whatsapp_service import whatsapp_service
from src.internal_events import event_manager, PATIENT_IDENTIFIED
from src.database import Database
from src.db_config import get_db_context
from src.models import RefillPrediction
from src.graph import agent_graph

logger = logging.getLogger(__name__)

class WhatsAppPipeline:
    def __init__(self):
        self.identity_agent = IdentityAgent()
        self.db = Database()  # BUG 1 FIX: self.db was never instantiated

    async def handle_text(self, phone: str, text: str):
        """
        Process text message through agent pipeline.
        Supports multi-language (Hindi, English, Hinglish, Marathi).
        """
        try:
            # Detect language from user message
            from src.services.language_service import detect_language
            detected_language = detect_language(text)
            logger.info(f"WhatsApp message from {phone} in language: {detected_language}")
            
            # 1. Resolve Identity
            patient = self.db.resolve_patient(phone)  # BUG 1 FIX: was calling non-existent get_pid_by_telegram
            pid = patient.get("pid") or patient.get("id")

            if not pid:
                if text.upper() == "YES":
                    patient_info = self.db.resolve_patient(phone, create_if_missing=True) \
                        if "create_if_missing" in self.db.resolve_patient.__code__.co_varnames \
                        else self.db.resolve_patient(phone)
                    pid = patient_info.get("pid") or patient_info.get("id")

                    await event_manager.emit(PATIENT_IDENTIFIED, {
                        "pid": pid,
                        "phone": phone,
                        "source": "whatsapp"
                    })
                    
                    # Send welcome message in detected language
                    from src.services.language_service import get_template
                    welcome_msg = get_template("greeting", detected_language)
                    welcome_msg = f"✅ *Successfully Linked!*\n\nYour Patient ID is `{pid}`.\n{welcome_msg}"

                    await whatsapp_service.send_message(phone, welcome_msg)
                    return
                else:
                    welcome_msg = (
                        "Welcome to MediSync 💊\n\n"
                        f"To get started, please confirm your phone number is {phone} "
                        "and we'll link your patient record automatically.\n\n"
                        "Reply YES to confirm or send your correct number."
                    )
                    await whatsapp_service.send_message(phone, welcome_msg)
                    return

            # 2. Check for pending refill confirmation (YES → auto-place order)
            if text.strip().upper() == 'YES' and pid:
                with get_db_context() as db:
                    pending_refill = db.query(RefillPrediction).filter(
                        RefillPrediction.user_id == pid,
                        RefillPrediction.reminder_sent == True,
                        RefillPrediction.refill_confirmed == False
                    ).order_by(RefillPrediction.predicted_depletion_date.asc()).first()

                    if pending_refill:
                        refill_state = PharmacyState(
                            user_id=pid,
                            whatsapp_phone=phone,
                            user_message=f"refill {pending_refill.medicine_name}",
                            extracted_items=[OrderItem(
                                medicine_name=pending_refill.medicine_name,
                                quantity=1
                            )]
                        )
                        result = await agent_graph.ainvoke(refill_state)
                        final_state = PharmacyState(**result) if isinstance(result, dict) else result

                        pending_refill.refill_confirmed = True
                        db.commit()

                        await whatsapp_service.send_message(
                            phone,
                            f"✅ *Refill order placed!*\n\n"
                            f"Order ID: `{final_state.order_id}`\n"
                            f"Medicine: {pending_refill.medicine_name}\n\n"
                            f"Please collect at the counter.\n\u2014 MediSync"
                        )
                        return  # Handled — skip normal pipeline

            # 3. Process through Agents
            state = PharmacyState(
                user_id=pid,
                whatsapp_phone=phone,
                user_message=text,
                language=detected_language  # Set detected language in state
            )

            # BUG 2 FIX: front_desk_agent, pharmacist_agent, fulfillment_agent are
            # synchronous functions — removed incorrect await calls
            state = front_desk_agent(state)

            if state.intent == "unknown":
                await whatsapp_service.send_message(phone, "I didn't understand that. Can you rephrase?")
                return

            if state.extracted_items:
                state = pharmacist_agent(state)

                if state.safety_issues:
                    issues_text = "\n".join([f"• {issue}" for issue in state.safety_issues])
                    await whatsapp_service.send_message(
                        phone,
                        f"⚠️ *Safety Issues Detected:*\n\n{issues_text}"
                    )
                    return

                if state.pharmacist_decision == "approved":
                    state = fulfillment_agent(state)
                    await whatsapp_service.send_message(
                        phone,
                        f"✅ *Order Confirmed!*\n\nOrder ID: `{state.order_id}`"
                    )
                    return

            await whatsapp_service.send_message(phone, "I'm processing your request...")

        except Exception as e:
            logger.error(f"WhatsApp pipeline error: {e}", exc_info=True)  # BUG 3 FIX: added exc_info=True so full traceback appears in logs
            await whatsapp_service.send_message(phone, "Sorry, something went wrong. Please try again.")

    async def _download_media(self, media_url: str) -> bytes:
        """Download media from Twilio using Auth."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                media_url,
                auth=(
                    os.getenv("TWILIO_ACCOUNT_SID"),
                    os.getenv("TWILIO_AUTH_TOKEN")
                )
            )
            response.raise_for_status()
            return response.content

    async def handle_image(self, phone: str, media_url: str):
        """Process prescription image."""
        try:
            image_bytes = await self._download_media(media_url)

            temp_path = f"temp_whatsapp_{phone}.jpg"
            with open(temp_path, "wb") as f:
                f.write(image_bytes)

            # BUG 4 FIX: was calling non-existent get_pid_by_telegram
            # resolve_patient returns a dict — extract pid correctly
            patient = self.db.resolve_patient(phone)
            pid = patient.get("pid") or patient.get("id")

            state = PharmacyState(user_id=pid, whatsapp_phone=phone)

            state = vision_agent(state, temp_path, use_mock=False)
            os.remove(temp_path)

            if not state.prescription_uploaded:
                await whatsapp_service.send_message(
                    phone,
                    "⚠️ Could not process prescription image. Please try again with a clearer photo."
                )
                return

            state = medical_validation_agent(state)

            if state.pharmacist_decision == "approved":
                message = "✅ *Prescription Approved*\n\nFound medicines:"
                for item in state.extracted_items:
                    message += f"\n• {item.medicine_name}"

                state = pharmacist_agent(state)
                if state.pharmacist_decision == "approved":
                    state = fulfillment_agent(state)
                    message += f"\n\n*Order ID:* `{state.order_id}`"

                await whatsapp_service.send_message(phone, message)

            elif state.pharmacist_decision == "needs_review":
                issues = "\n".join([f"• {issue}" for issue in state.safety_issues])
                await whatsapp_service.send_message(
                    phone,
                    f"⏳ *Prescription Under Review*\n\n{issues}\n\nA pharmacist will review shortly."
                )
            else:
                issues = "\n".join([f"• {issue}" for issue in state.safety_issues])
                await whatsapp_service.send_message(
                    phone,
                    f"❌ *Prescription Rejected*\n\n{issues}"
                )

        except Exception as e:
            logger.error(f"WhatsApp vision pipeline error: {e}", exc_info=True)
            await whatsapp_service.send_message(phone, "Sorry, could not process prescription. Please try again.")

    async def handle_voice(self, phone: str, media_url: str):
        """Process voice message."""
        try:
            audio_bytes = await self._download_media(media_url)

            temp_path = f"temp_whatsapp_{phone}.ogg"
            with open(temp_path, "wb") as f:
                f.write(audio_bytes)

            from src.services.speech_service import transcribe_audio
            transcription_result = transcribe_audio(temp_path)
            os.remove(temp_path)

            if not transcription_result.get("success"):
                await whatsapp_service.send_message(
                    phone,
                    "⚠️ Could not transcribe voice message. Please try again."
                )
                return

            transcription = transcription_result.get("transcription", "")
            await self.handle_text(phone, transcription)

        except Exception as e:
            logger.error(f"WhatsApp voice pipeline error: {e}", exc_info=True)
            await whatsapp_service.send_message(phone, "Sorry, could not process voice message. Please try again.")