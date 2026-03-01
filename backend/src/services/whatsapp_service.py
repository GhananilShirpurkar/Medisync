from twilio.rest import Client
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        self.client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )
        self.from_number = os.getenv("TWILIO_WHATSAPP_FROM")

    def _format_number(self, phone: str) -> str:
        # Strips any existing prefix, normalizes to whatsapp:+91XXXXXXXXXX
        phone = str(phone).strip().replace(" ", "").replace("-", "")
        # If the frontend sent digits without '+', we add it
        if not phone.startswith("+"):
            if len(phone) == 10:
                phone = f"+91{phone}" # Default to India if exactly 10 digits
            else:
                phone = f"+{phone}"  # Assume it already has a country code prefix (e.g., 1415...)
        if not phone.startswith("whatsapp:"):
            phone = f"whatsapp:{phone}"
        return phone

    def send_message(self, phone: str, message: str) -> Dict[str, Any]:
        try:
            msg = self.client.messages.create(
                from_=self.from_number,
                to=self._format_number(phone),
                body=message
            )
            return {
                "success": True,
                "message_id": msg.sid,
                "chat_id": phone,
                "method": "whatsapp"
            }
        except Exception as e:
            logger.error(f"WhatsApp send failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "method": "whatsapp"
            }

    def send_order_notification(self, chat_id: str, order_id: str, items: list, 
                               total_amount: float, status: str = "confirmed") -> Dict[str, Any]:
        status_emoji = {
            "confirmed": "✅",
            "ready": "📦",
            "delivered": "🎉",
            "cancelled": "❌"
        }.get(status, "ℹ️")
        
        items_text = "\n".join([f"• {item.get('name', 'Unknown')} x{item.get('quantity', 1)}" for item in items])
        
        message = (
            f"{status_emoji} *Order {status.title()}*\n\n"
            f"*Order ID:* `{order_id}`\n\n"
            f"*Items:*\n{items_text}\n\n"
            f"*Total:* ₹{total_amount:.2f}\n\n"
            f"Thank you for choosing MediSync Pharmacy!"
        )
        return self.send_message(chat_id, message)

    def send_prescription_status(self, chat_id: str, status: str, details: Optional[str] = None) -> Dict[str, Any]:
        status_messages = {
            "verified": "✅ *Prescription Verified*\n\nYour prescription has been reviewed and approved.",
            "needs_review": "⏳ *Prescription Under Review*\n\nOur pharmacist is reviewing your prescription.",
            "rejected": "❌ *Prescription Rejected*\n\nYour prescription could not be verified."
        }
        message = status_messages.get(status, "ℹ️ Prescription status updated")
        if details:
            message += f"\n\n*Details:* {details}"
        return self.send_message(chat_id, message)

    def send_refill_reminder(self, chat_id: str, medicine_name: str, days_remaining: int) -> Dict[str, Any]:
        message = (
            f"💊 *Refill Reminder*\n\n"
            f"Your *{medicine_name}* supply is running low — approximately {days_remaining} days remaining.\n"
            f"Reply or visit to reorder.\n\n"
            f"— MediSync Pharmacy"
        )
        return self.send_message(chat_id, message)

# Global instance
whatsapp_service = WhatsAppService()

# Export functions for API compatibility with whatsapp_service
def send_message(chat_id: str, text: str, **kwargs) -> Dict[str, Any]:
    return whatsapp_service.send_message(chat_id, text)

def send_order_notification(chat_id: str, order_id: str, items: list, 
                          total_amount: float, status: str = "confirmed") -> Dict[str, Any]:
    return whatsapp_service.send_order_notification(chat_id, order_id, items, total_amount, status)

def send_prescription_status(chat_id: str, status: str, details: Optional[str] = None) -> Dict[str, Any]:
    return whatsapp_service.send_prescription_status(chat_id, status, details)

def send_refill_reminder(chat_id: str, medicine_name: str, days_remaining: int) -> Dict[str, Any]:
    return whatsapp_service.send_refill_reminder(chat_id, medicine_name, days_remaining)

def mock_notification(chat_id: str, message: str) -> Dict[str, Any]:
    print(f"\n📱 WHATSAPP NOTIFICATION (MOCK)")
    print(f"To: {chat_id}")
    print(f"Message:\n{message}")
    return {"success": True, "method": "whatsapp_mock"}
