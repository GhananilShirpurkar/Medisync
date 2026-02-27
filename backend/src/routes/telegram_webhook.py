from fastapi import APIRouter, Request, HTTPException
import logging

from src.telegram_pipeline import process_telegram_command, process_telegram_contact, process_text_message
from src.services.telegram_service import send_message

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    """
    Endpoint strictly for receiving Telegram webhook updates.
    """
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # We only care about message updates
    if "message" not in data:
        return {"status": "ignored", "reason": "not a message"}

    msg = data["message"]
    chat_id = str(msg.get("chat", {}).get("id"))
    
    if not chat_id:
        return {"status": "ignored", "reason": "no chat_id"}

    # 1. Handle Contact Sharing (User clicking "Share Phone Number" after /start)
    if "contact" in msg:
        contact = msg["contact"]
        phone_number = contact.get("phone_number")
        first_name = contact.get("first_name", "User")
        
        # Verify the contact shared belongs to the user who sent it
        if str(contact.get("user_id")) == str(msg.get("from", {}).get("id")):
            result = await process_telegram_contact(chat_id, phone_number, first_name)
            send_message(chat_id, result["message"])
            return {"status": "success", "action": "contact_linked"}
        else:
            send_message(chat_id, "⚠️ Please use the 'Share Contact' button to share your own phone number.")
            return {"status": "ignored", "reason": "foreign_contact"}

    # 2. Handle Text Commands & Messages
    text = msg.get("text", "")
    if not text:
        return {"status": "ignored", "reason": "empty_text"}

    if text.startswith("/start"):
        # Process command
        result = await process_telegram_command(user_id="telegram_user", telegram_chat_id=chat_id, command="/start")
        
        if result.get("require_contact"):
            # Send message with a special Request Contact keyboard
            # We use the raw Telegram API format for keyboards via our send_message utility
            import requests
            import os
            
            token = os.environ.get("TELEGRAM_BOT_TOKEN")
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            
            payload = {
                "chat_id": chat_id,
                "text": result["message"],
                "parse_mode": "Markdown",
                "reply_markup": {
                    "keyboard": [
                        [{"text": "📱 Share Phone Number", "request_contact": True}]
                    ],
                    "resize_keyboard": True,
                    "one_time_keyboard": True
                }
            }
            requests.post(url, json=payload)
            return {"status": "success", "action": "command_processed"}
            
        else:
            send_message(chat_id, result["message"])
            return {"status": "success", "action": "command_processed"}
        
    # Default: Treat as normal conversation
    # A fully fleshed out system would resolve user_id prior, but here we just pass "telegram_user"
    # as the pipeline can parse intents.
    result = await process_text_message(user_id="telegram_user", telegram_chat_id=chat_id, message=text)
    send_message(chat_id, result["message"])

    return {"status": "success"}
