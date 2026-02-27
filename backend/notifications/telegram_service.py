"""
TELEGRAM NOTIFICATION SERVICE
==============================
Clean notification service for Telegram bot.

IMPORTANT:
- This is an OUTPUT channel only
- No AI logic here
- No conversation handling
- Only sends notifications
- Graceful failure handling

Responsibilities:
1. Send order confirmations
2. Send digital bills (PDF)
3. Send prescription summaries
4. Send status updates
"""

import os
import logging
from typing import Dict, Optional, List
from datetime import datetime
import asyncio
from telegram import Bot
from telegram.error import TelegramError

logger = logging.getLogger(__name__)

# Initialize Telegram bot
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = Bot(token=TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else None


class TelegramNotificationService:
    """
    Telegram notification service for MediSync.
    
    Sends structured notifications about orders, bills, and prescriptions.
    """
    
    def __init__(self):
        """Initialize Telegram notification service."""
        self.bot = bot
        self.enabled = bot is not None
        
        if not self.enabled:
            logger.warning("Telegram bot not configured - notifications disabled")
    
    async def send_order_confirmation(
        self,
        telegram_user_id: str,
        order: Dict
    ) -> Optional[int]:
        """
        Send order confirmation notification.
        
        Args:
            telegram_user_id: User's Telegram ID
            order: Order details dict
            
        Returns:
            Message ID if successful, None if failed
        """
        if not self.enabled:
            logger.warning("Telegram not enabled - skipping order confirmation")
            return None
        
        try:
            # Format order confirmation message
            message = self._format_order_confirmation(order)
            
            # Send message
            result = await self.bot.send_message(
                chat_id=telegram_user_id,
                text=message,
                parse_mode='HTML'
            )
            
            logger.info(f"Order confirmation sent to {telegram_user_id}: order_id={order.get('order_id')}")
            
            # Log notification
            self._log_notification(
                telegram_user_id=telegram_user_id,
                message_type="order_confirmation",
                order_id=order.get('order_id'),
                success=True,
                message_id=result.message_id
            )
            
            return result.message_id
            
        except TelegramError as e:
            logger.error(f"Failed to send order confirmation: {e}")
            self._log_notification(
                telegram_user_id=telegram_user_id,
                message_type="order_confirmation",
                order_id=order.get('order_id'),
                success=False,
                error=str(e)
            )
            return None
        except Exception as e:
            logger.error(f"Unexpected error sending order confirmation: {e}")
            return None
    
    async def send_prescription_summary(
        self,
        telegram_user_id: str,
        order: Dict,
        prescription: Dict
    ) -> Optional[int]:
        """
        Send prescription summary notification.
        
        Args:
            telegram_user_id: User's Telegram ID
            order: Order details dict
            prescription: Prescription details dict
            
        Returns:
            Message ID if successful, None if failed
        """
        if not self.enabled:
            logger.warning("Telegram not enabled - skipping prescription summary")
            return None
        
        try:
            # Format prescription summary message
            message = self._format_prescription_summary(order, prescription)
            
            # Send message
            result = await self.bot.send_message(
                chat_id=telegram_user_id,
                text=message,
                parse_mode='HTML'
            )
            
            logger.info(f"Prescription summary sent to {telegram_user_id}: order_id={order.get('order_id')}")
            
            # Log notification
            self._log_notification(
                telegram_user_id=telegram_user_id,
                message_type="prescription_summary",
                order_id=order.get('order_id'),
                success=True,
                message_id=result.message_id
            )
            
            return result.message_id
            
        except TelegramError as e:
            logger.error(f"Failed to send prescription summary: {e}")
            self._log_notification(
                telegram_user_id=telegram_user_id,
                message_type="prescription_summary",
                order_id=order.get('order_id'),
                success=False,
                error=str(e)
            )
            return None
        except Exception as e:
            logger.error(f"Unexpected error sending prescription summary: {e}")
            return None
    
    async def send_bill_pdf(
        self,
        telegram_user_id: str,
        order: Dict,
        pdf_path: Optional[str] = None
    ) -> Optional[int]:
        """
        Send digital bill as PDF or formatted text.
        
        Args:
            telegram_user_id: User's Telegram ID
            order: Order details dict
            pdf_path: Path to PDF file (optional)
            
        Returns:
            Message ID if successful, None if failed
        """
        if not self.enabled:
            logger.warning("Telegram not enabled - skipping bill")
            return None
        
        try:
            # If PDF exists, send as document
            if pdf_path and os.path.exists(pdf_path):
                with open(pdf_path, 'rb') as pdf_file:
                    result = await self.bot.send_document(
                        chat_id=telegram_user_id,
                        document=pdf_file,
                        caption=f"🧾 Invoice for Order #{order.get('order_id')}"
                    )
                
                logger.info(f"Bill PDF sent to {telegram_user_id}: order_id={order.get('order_id')}")
            else:
                # Fallback to formatted text bill
                message = self._format_text_bill(order)
                result = await self.bot.send_message(
                    chat_id=telegram_user_id,
                    text=message,
                    parse_mode='HTML'
                )
                
                logger.info(f"Text bill sent to {telegram_user_id}: order_id={order.get('order_id')}")
            
            # Log notification
            self._log_notification(
                telegram_user_id=telegram_user_id,
                message_type="bill",
                order_id=order.get('order_id'),
                success=True,
                message_id=result.message_id
            )
            
            return result.message_id
            
        except TelegramError as e:
            logger.error(f"Failed to send bill: {e}")
            self._log_notification(
                telegram_user_id=telegram_user_id,
                message_type="bill",
                order_id=order.get('order_id'),
                success=False,
                error=str(e)
            )
            return None
        except Exception as e:
            logger.error(f"Unexpected error sending bill: {e}")
            return None
    
    async def send_status_update(
        self,
        telegram_user_id: str,
        order_id: str,
        status: str,
        message: Optional[str] = None
    ) -> Optional[int]:
        """
        Send order status update notification.
        
        Args:
            telegram_user_id: User's Telegram ID
            order_id: Order ID
            status: Status code (packed, out_for_delivery, ready, cancelled)
            message: Optional custom message
            
        Returns:
            Message ID if successful, None if failed
        """
        if not self.enabled:
            logger.warning("Telegram not enabled - skipping status update")
            return None
        
        try:
            # Format status update message
            formatted_message = self._format_status_update(order_id, status, message)
            
            # Send message
            result = await self.bot.send_message(
                chat_id=telegram_user_id,
                text=formatted_message,
                parse_mode='HTML'
            )
            
            logger.info(f"Status update sent to {telegram_user_id}: order_id={order_id}, status={status}")
            
            # Log notification
            self._log_notification(
                telegram_user_id=telegram_user_id,
                message_type="status_update",
                order_id=order_id,
                success=True,
                message_id=result.message_id
            )
            
            return result.message_id
            
        except TelegramError as e:
            logger.error(f"Failed to send status update: {e}")
            self._log_notification(
                telegram_user_id=telegram_user_id,
                message_type="status_update",
                order_id=order_id,
                success=False,
                error=str(e)
            )
            return None
        except Exception as e:
            logger.error(f"Unexpected error sending status update: {e}")
            return None
    
    # ------------------------------------------------------------------
    # MESSAGE FORMATTING
    # ------------------------------------------------------------------
    
    def _format_order_confirmation(self, order: Dict) -> str:
        """Format order confirmation message."""
        
        order_id = order.get('order_id', 'N/A')
        patient_name = order.get('patient_name', 'Customer')
        items = order.get('items', [])
        total = order.get('total_amount', 0)
        estimated_time = order.get('estimated_pickup_time', '30 minutes')
        
        message = f"""🧾 <b>MediSync Order Confirmed</b>

<b>Order ID:</b> {order_id}
<b>Patient:</b> {patient_name}

<b>Medicines:</b>
"""
        
        for item in items:
            medicine_name = item.get('medicine_name', 'Unknown')
            quantity = item.get('quantity', 1)
            price = item.get('price', 0)
            message += f"• {medicine_name} x{quantity} - ₹{price}\n"
        
        message += f"""
<b>Total:</b> ₹{total}
<b>Pickup Time:</b> {estimated_time}

<b>Status:</b> Pharmacy Notified ✅

Thank you for using MediSync!
"""
        
        return message
    
    def _format_prescription_summary(self, order: Dict, prescription: Dict) -> str:
        """Format prescription summary message."""
        
        order_id = order.get('order_id', 'N/A')
        doctor_name = prescription.get('doctor_name', 'Not specified')
        diagnosis = prescription.get('diagnosis', 'Not specified')
        medicines = prescription.get('medicines', [])
        
        message = f"""📄 <b>Prescription Summary</b>

<b>Order ID:</b> {order_id}
<b>Doctor:</b> {doctor_name}
<b>Diagnosis:</b> {diagnosis}

<b>Prescribed Medicines:</b>
"""
        
        for med in medicines:
            name = med.get('name', 'Unknown')
            dosage = med.get('dosage', 'As directed')
            duration = med.get('duration', 'As prescribed')
            message += f"• {name}\n  Dosage: {dosage}\n  Duration: {duration}\n\n"
        
        message += """<b>Validated by:</b> MediSync Medical Agent ✅

Please follow your doctor's instructions carefully.
"""
        
        return message
    
    def _format_text_bill(self, order: Dict) -> str:
        """Format text bill (fallback if PDF fails)."""
        
        order_id = order.get('order_id', 'N/A')
        patient_name = order.get('patient_name', 'Customer')
        items = order.get('items', [])
        total = order.get('total_amount', 0)
        date = order.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M'))
        
        message = f"""🧾 <b>INVOICE</b>

<b>MediSync Pharmacy</b>
AI-Powered Healthcare Solutions

━━━━━━━━━━━━━━━━━━━━━━

<b>Invoice ID:</b> INV-{order_id}
<b>Order ID:</b> {order_id}
<b>Patient:</b> {patient_name}
<b>Date:</b> {date}

━━━━━━━━━━━━━━━━━━━━━━

<b>ITEMS:</b>

"""
        
        subtotal = 0
        for item in items:
            medicine_name = item.get('medicine_name', 'Unknown')
            quantity = item.get('quantity', 1)
            price = item.get('price', 0)
            item_total = quantity * price
            subtotal += item_total
            
            message += f"{medicine_name}\n"
            message += f"  Qty: {quantity} × ₹{price} = ₹{item_total}\n\n"
        
        tax = subtotal * 0.05  # 5% tax
        total_with_tax = subtotal + tax
        
        message += f"""━━━━━━━━━━━━━━━━━━━━━━

<b>Subtotal:</b> ₹{subtotal:.2f}
<b>Tax (5%):</b> ₹{tax:.2f}
<b>TOTAL:</b> ₹{total_with_tax:.2f}

━━━━━━━━━━━━━━━━━━━━━━

Thank you for choosing MediSync!
"""
        
        return message
    
    def _format_status_update(self, order_id: str, status: str, custom_message: Optional[str] = None) -> str:
        """Format status update message."""
        
        status_icons = {
            "confirmed": "✅",
            "packed": "📦",
            "out_for_delivery": "🚚",
            "ready_for_pickup": "✅",
            "delivered": "✅",
            "cancelled": "❌"
        }
        
        status_messages = {
            "confirmed": "Order Confirmed",
            "packed": "Order Packed",
            "out_for_delivery": "Out for Delivery",
            "ready_for_pickup": "Ready for Pickup",
            "delivered": "Delivered",
            "cancelled": "Order Cancelled"
        }
        
        icon = status_icons.get(status, "📋")
        status_text = status_messages.get(status, status.replace('_', ' ').title())
        
        message = f"""{icon} <b>{status_text}</b>

<b>Order ID:</b> {order_id}
"""
        
        if custom_message:
            message += f"\n{custom_message}\n"
        
        message += "\nThank you for using MediSync!"
        
        return message
    
    # ------------------------------------------------------------------
    # LOGGING
    # ------------------------------------------------------------------
    
    def _log_notification(
        self,
        telegram_user_id: str,
        message_type: str,
        order_id: Optional[str] = None,
        success: bool = True,
        message_id: Optional[int] = None,
        error: Optional[str] = None
    ):
        """
        Log notification attempt.
        
        This should be stored in database for audit trail.
        For now, just logging to console.
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "telegram_user_id": telegram_user_id,
            "message_type": message_type,
            "order_id": order_id,
            "success": success,
            "message_id": message_id,
            "error": error
        }
        
        if success:
            logger.info(f"Notification logged: {log_entry}")
        else:
            logger.error(f"Notification failed: {log_entry}")


# ------------------------------------------------------------------
# SYNCHRONOUS WRAPPERS (for non-async contexts)
# ------------------------------------------------------------------

def send_order_confirmation_sync(telegram_user_id: str, order: Dict) -> Optional[int]:
    """Synchronous wrapper for send_order_confirmation."""
    service = TelegramNotificationService()
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(
            service.send_order_confirmation(telegram_user_id, order)
        )
    except RuntimeError:
        # If no event loop, create one
        return asyncio.run(service.send_order_confirmation(telegram_user_id, order))


def send_prescription_summary_sync(telegram_user_id: str, order: Dict, prescription: Dict) -> Optional[int]:
    """Synchronous wrapper for send_prescription_summary."""
    service = TelegramNotificationService()
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(
            service.send_prescription_summary(telegram_user_id, order, prescription)
        )
    except RuntimeError:
        return asyncio.run(service.send_prescription_summary(telegram_user_id, order, prescription))


def send_bill_pdf_sync(telegram_user_id: str, order: Dict, pdf_path: Optional[str] = None) -> Optional[int]:
    """Synchronous wrapper for send_bill_pdf."""
    service = TelegramNotificationService()
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(
            service.send_bill_pdf(telegram_user_id, order, pdf_path)
        )
    except RuntimeError:
        return asyncio.run(service.send_bill_pdf(telegram_user_id, order, pdf_path))


def send_status_update_sync(telegram_user_id: str, order_id: str, status: str, message: Optional[str] = None) -> Optional[int]:
    """Synchronous wrapper for send_status_update."""
    service = TelegramNotificationService()
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(
            service.send_status_update(telegram_user_id, order_id, status, message)
        )
    except RuntimeError:
        return asyncio.run(service.send_status_update(telegram_user_id, order_id, status, message))
