from twilio.rest import Client
import os
import logging
from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

# Initialize Twilio client
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM")

class WhatsAppNotificationService:
    """
    WhatsApp notification service for MediSync using Twilio.
    """
    def __init__(self):
        self.enabled = all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM])
        if self.enabled:
            self.client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            self.from_number = TWILIO_WHATSAPP_FROM
        else:
            logger.warning("Twilio WhatsApp not configured - notifications disabled")

    def _format_number(self, phone: str) -> str:
        phone = str(phone).strip().replace(" ", "").replace("-", "")
        if not phone.startswith("+"):
            phone = f"+91{phone}"
        if not phone.startswith("whatsapp:"):
            phone = f"whatsapp:{phone}"
        return phone

    async def send_message(self, phone: str, message: str) -> Optional[str]:
        if not self.enabled:
            return None
        try:
            # Twilio's client is blocking, so we'll run it in a thread if needed,
            # but for now we'll just call it.
            msg = self.client.messages.create(
                from_=self.from_number,
                to=self._format_number(phone),
                body=message
            )
            return msg.sid
        except Exception as e:
            logger.error(f"WhatsApp send failed: {e}")
            return None

    async def send_order_confirmation(self, phone: str, order: Dict) -> Optional[str]:
        items_text = "\n".join([f"• {item.get('medicine_name', 'Unknown')} x{item.get('quantity', 1)}" for item in order.get('items', [])])
        message = (
            f"✅ *Order Confirmed*\n\n"
            f"Order ID: `{order.get('order_id')}`\n"
            f"Patient: {order.get('patient_name')}\n\n"
            f"Items:\n{items_text}\n\n"
            f"Total: ₹{order.get('total_amount'):.2f}\n"
            f"Estimated Pickup: {order.get('estimated_pickup_time', '30 mins')}\n\n"
            f"Thank you for choosing MediSync!"
        )
        return await self.send_message(phone, message)

    async def send_prescription_summary(self, phone: str, order: Dict, prescription: Dict) -> Optional[str]:
        meds_text = "\n".join([f"• {m.get('name')} ({m.get('dosage')})" for m in prescription.get('medicines', [])])
        message = (
            f"📋 *Prescription Summary*\n\n"
            f"Order ID: `{order.get('order_id')}`\n"
            f"Doctor: {prescription.get('doctor_name')}\n"
            f"Diagnosis: {prescription.get('diagnosis')}\n\n"
            f"Medicines:\n{meds_text}\n\n"
            f"Validated by MediSync Agent ✅"
        )
        return await self.send_message(phone, message)

    async def send_status_update(self, phone: str, order_id: str, status: str, custom_message: Optional[str] = None) -> Optional[str]:
        status_label = status.replace("_", " ").title()
        message = (
            f"🔔 *Order Status Update*\n\n"
            f"Order `{order_id}` is now: *{status_label}*\n"
        )
        if custom_message:
            message += f"\n{custom_message}\n"
        message += "\nThank you for using MediSync!"
        return await self.send_message(phone, message)

    async def send_bill_pdf(self, phone: str, order: Dict, pdf_path: Optional[str] = None) -> Optional[str]:
        # WhatsApp supports media via Twilio. For hackathon, we'll send text bill fallback.
        items_text = "\n".join([f"• {item.get('medicine_name')} x{item.get('quantity')} - ₹{item.get('price')*item.get('quantity')}" for item in order.get('items', [])])
        message = (
            f"🧾 *MediSync Invoice*\n\n"
            f"Order: #{order.get('order_id')}\n"
            f"Total: ₹{order.get('total_amount'):.2f}\n\n"
            f"Details:\n{items_text}\n\n"
            f"Thank you!"
        )
        return await self.send_message(phone, message)

# Synchronous Wrappers
def send_order_confirmation_sync(phone: str, order: Dict) -> Optional[str]:
    service = WhatsAppNotificationService()
    return asyncio.run(service.send_order_confirmation(phone, order))

def send_prescription_summary_sync(phone: str, order: Dict, prescription: Dict) -> Optional[str]:
    service = WhatsAppNotificationService()
    return asyncio.run(service.send_prescription_summary(phone, order, prescription))

def send_status_update_sync(phone: str, order_id: str, status: str, message: Optional[str] = None) -> Optional[str]:
    service = WhatsAppNotificationService()
    return asyncio.run(service.send_status_update(phone, order_id, status, message))

def send_bill_pdf_sync(phone: str, order: Dict, pdf_path: Optional[str] = None) -> Optional[str]:
    service = WhatsAppNotificationService()
    return asyncio.run(service.send_bill_pdf(phone, order, pdf_path))
