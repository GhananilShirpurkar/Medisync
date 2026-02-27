"""
TELEGRAM NOTIFICATION SERVICE
==============================
Send notifications via Telegram Bot API
Zero cost | Offline-capable
"""

import os
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


# ------------------------------------------------------------------
# SEND MESSAGE
# ------------------------------------------------------------------
def send_message(chat_id: str, text: str, parse_mode: str = "Markdown") -> Dict[str, Any]:
    """
    Send a text message to a Telegram user.
    
    Args:
        chat_id: Telegram chat ID (user ID or group ID)
        text: Message text (supports Markdown or HTML)
        parse_mode: "Markdown" or "HTML" (default: Markdown)
        
    Returns:
        Dictionary with success status and message details
        
    Example:
        result = send_message("123456789", "Your order is ready!")
    """
    if not TELEGRAM_BOT_TOKEN:
        return {
            "success": False,
            "error": "TELEGRAM_BOT_TOKEN not configured",
            "method": "telegram"
        }
    
    try:
        url = f"{TELEGRAM_API_URL}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("ok"):
            return {
                "success": True,
                "message_id": data["result"]["message_id"],
                "chat_id": chat_id,
                "method": "telegram"
            }
        else:
            return {
                "success": False,
                "error": data.get("description", "Unknown error"),
                "method": "telegram"
            }
            
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Request timeout",
            "method": "telegram"
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e),
            "method": "telegram"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "method": "telegram"
        }


# ------------------------------------------------------------------
# SEND ORDER NOTIFICATION
# ------------------------------------------------------------------
def send_order_notification(
    chat_id: str,
    order_id: str,
    items: list,
    total_amount: float,
    status: str = "confirmed"
) -> Dict[str, Any]:
    """
    Send order confirmation/update notification.
    
    Args:
        chat_id: Telegram chat ID
        order_id: Order ID
        items: List of order items
        total_amount: Total order amount
        status: Order status (confirmed, ready, delivered)
        
    Returns:
        Dictionary with success status
    """
    # Format items list
    items_text = "\n".join([
        f"• {item.get('name', 'Unknown')} x{item.get('quantity', 1)}"
        for item in items
    ])
    
    # Status emoji
    status_emoji = {
        "confirmed": "✅",
        "ready": "📦",
        "delivered": "🎉",
        "cancelled": "❌"
    }.get(status, "ℹ️")
    
    # Build message
    message = f"""
{status_emoji} *Order {status.title()}*

*Order ID:* `{order_id}`

*Items:*
{items_text}

*Total:* ₹{total_amount:.2f}

Thank you for your order!
"""
    
    return send_message(chat_id, message.strip())


# ------------------------------------------------------------------
# SEND PRESCRIPTION STATUS
# ------------------------------------------------------------------
def send_prescription_status(
    chat_id: str,
    status: str,
    details: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send prescription verification status.
    
    Args:
        chat_id: Telegram chat ID
        status: Status (verified, needs_review, rejected)
        details: Additional details or reason
        
    Returns:
        Dictionary with success status
    """
    status_messages = {
        "verified": "✅ *Prescription Verified*\n\nYour prescription has been verified by our pharmacist.",
        "needs_review": "⏳ *Prescription Under Review*\n\nOur pharmacist is reviewing your prescription. You'll be notified shortly.",
        "rejected": "❌ *Prescription Rejected*\n\nYour prescription could not be verified."
    }
    
    message = status_messages.get(status, "ℹ️ Prescription status updated")
    
    if details:
        message += f"\n\n*Details:* {details}"
    
    return send_message(chat_id, message)


# ------------------------------------------------------------------
# SEND REFILL REMINDER
# ------------------------------------------------------------------
def send_refill_reminder(
    chat_id: str,
    medicine_name: str,
    days_remaining: int
) -> Dict[str, Any]:
    """
    Send medication refill reminder.
    
    Args:
        chat_id: Telegram chat ID
        medicine_name: Name of medicine
        days_remaining: Days of supply remaining
        
    Returns:
        Dictionary with success status
    """
    message = f"""
🔔 *Refill Reminder*

Your *{medicine_name}* supply is running low.

*Days remaining:* {days_remaining}

Would you like to reorder?
"""
    
    return send_message(chat_id, message.strip())


# ------------------------------------------------------------------
# GET BOT INFO
# ------------------------------------------------------------------
def get_bot_info() -> Dict[str, Any]:
    """
    Get information about the bot.
    
    Returns:
        Dictionary with bot details
    """
    if not TELEGRAM_BOT_TOKEN:
        return {
            "success": False,
            "error": "TELEGRAM_BOT_TOKEN not configured"
        }
    
    try:
        url = f"{TELEGRAM_API_URL}/getMe"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("ok"):
            bot = data["result"]
            return {
                "success": True,
                "bot_id": bot["id"],
                "bot_username": bot["username"],
                "bot_name": bot.get("first_name", ""),
                "can_read_messages": bot.get("can_read_all_group_messages", False)
            }
        else:
            return {
                "success": False,
                "error": data.get("description", "Unknown error")
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ------------------------------------------------------------------
# MOCK NOTIFICATION (for testing)
# ------------------------------------------------------------------
def mock_notification(chat_id: str, message: str) -> Dict[str, Any]:
    """
    Mock notification for testing without Telegram API.
    
    Args:
        chat_id: Telegram chat ID
        message: Message text
        
    Returns:
        Mock success response
    """
    print(f"\n📱 TELEGRAM NOTIFICATION (MOCK)")
    print(f"To: {chat_id}")
    print(f"Message:\n{message}")
    print("=" * 60)
    
    return {
        "success": True,
        "message_id": "mock_12345",
        "chat_id": chat_id,
        "method": "telegram_mock",
        "note": "Mock notification - Telegram bot not configured"
    }
