"""
NOTIFICATION EVENT HANDLER
===========================
Event subscriber for sending notifications.

This handler reacts to domain events and sends appropriate notifications.
It's decoupled from the main workflow - failures don't block order processing.
"""

import logging
from typing import Optional
from datetime import datetime
import json
from pathlib import Path

from src.events.event_types import (
    OrderCreatedEvent,
    OrderRejectedEvent,
    PrescriptionValidatedEvent,
    Event
)
from src.events.event_bus import EventBus
from src.services.whatsapp_service import (
    send_order_notification,
    send_prescription_status
)
from src.errors import NotificationError

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# EVENT HANDLERS
# ------------------------------------------------------------------

def handle_order_created(event: OrderCreatedEvent):
    """
    Handle OrderCreatedEvent - send order confirmation.
    
    Args:
        event: OrderCreatedEvent instance
    """
    logger.info(f"Handling OrderCreatedEvent: {event.order_id}")
    
    try:
        # Determine order status for notification
        if getattr(event, 'pharmacist_decision', None) == "approved":
            order_status = "confirmed"
        elif getattr(event, 'pharmacist_decision', None) == "needs_review":
            order_status = "pending_review"
        else:
            order_status = "processing"
        
        # Sent notification using the correct service method
        # Use event.phone directly (it contains the patient's number)
        chat_id = event.phone
        
        # RE-ENABLING: Essential for Voice users who may not go through web checkout
        result = send_order_notification(
            chat_id=chat_id,
            order_id=event.order_id,
            items=event.items,
            total_amount=event.total_amount,
            status=order_status
        )
        
        if result.get("success"):
            logger.info(f"Order notification sent for {event.order_id}")
            _log_notification(event, "order_confirmation", "sent")
        else:
            logger.warning(f"Order notification failed for {event.order_id}: {result.get('error')}")
            _log_notification(event, "order_confirmation", "failed", result.get("error"))
            
    except Exception as e:
        logger.error(f"Error handling OrderCreatedEvent: {e}", exc_info=True)
        _log_notification(event, "order_confirmation", "error", str(e))


def handle_order_rejected(event: OrderRejectedEvent):
    """
    Handle OrderRejectedEvent - send rejection notification.
    
    Args:
        event: OrderRejectedEvent instance
    """
    logger.info(f"Handling OrderRejectedEvent for user: {event.user_id}")
    
    try:
        # Send rejection notification
        result = send_prescription_status(
            chat_id=event.user_id,
            status="rejected",
            details=event.reason
        )
        
        if result.get("success"):
            logger.info(f"Rejection notification sent to {event.user_id}")
            _log_notification(event, "order_rejection", "sent")
        else:
            logger.warning(f"Rejection notification failed for {event.user_id}: {result.get('error')}")
            _log_notification(event, "order_rejection", "failed", result.get("error"))
            
    except Exception as e:
        logger.error(f"Error handling OrderRejectedEvent: {e}", exc_info=True)
        _log_notification(event, "order_rejection", "error", str(e))


def handle_prescription_validated(event: PrescriptionValidatedEvent):
    """
    Handle PrescriptionValidatedEvent - send validation status.
    
    Args:
        event: PrescriptionValidatedEvent instance
    """
    logger.info(f"Handling PrescriptionValidatedEvent for user: {event.user_id}")
    
    try:
        # Determine prescription status
        if event.decision == "approved":
            prescription_status = "verified"
            details = "Your prescription has been approved."
        elif event.decision == "needs_review":
            prescription_status = "needs_review"
            details = "Our pharmacist is reviewing your prescription."
        elif event.decision == "rejected":
            prescription_status = "rejected"
            # Include first safety issue as detail
            details = event.safety_issues[0] if event.safety_issues else "Please contact pharmacy for details."
        else:
            prescription_status = "processing"
            details = "Your prescription is being processed."
        
        # Send notification
        result = send_prescription_status(
            chat_id=event.user_id,
            status=prescription_status,
            details=details
        )
        
        if result.get("success"):
            logger.info(f"Prescription status sent to {event.user_id}")
            _log_notification(event, "prescription_status", "sent")
        else:
            logger.warning(f"Prescription status failed for {event.user_id}: {result.get('error')}")
            _log_notification(event, "prescription_status", "failed", result.get("error"))
            
    except Exception as e:
        logger.error(f"Error handling PrescriptionValidatedEvent: {e}", exc_info=True)
        _log_notification(event, "prescription_status", "error", str(e))


# ------------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------------

def _log_notification(
    event: Event,
    notification_type: str,
    status: str,
    error: Optional[str] = None
):
    """
    Log notification to file for audit purposes.
    
    Args:
        event: Event that triggered notification
        notification_type: Type of notification
        status: Status (sent | failed | error)
        error: Error message if failed
    """
    # Create logs directory if it doesn't exist
    import os
    log_dir = Path(os.getcwd()) / "backend" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create log file path (one file per day)
    log_file = log_dir / f"notifications_{datetime.now().strftime('%Y-%m-%d')}.jsonl"
    
    # Prepare log entry
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "event_type": type(event).__name__,
        "event_id": event.event_id,
        "notification_type": notification_type,
        "status": status,
        "error": error,
        "event_data": event.data
    }
    
    # Append to log file (JSONL format)
    try:
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        logger.error(f"Failed to write notification log: {e}")


# ------------------------------------------------------------------
# REGISTRATION
# ------------------------------------------------------------------

def register_notification_handlers(event_bus: EventBus):
    """
    Register all notification handlers with the event bus.
    
    Args:
        event_bus: EventBus instance
    """
    event_bus.subscribe(OrderCreatedEvent, handle_order_created)
    event_bus.subscribe(OrderRejectedEvent, handle_order_rejected)
    event_bus.subscribe(PrescriptionValidatedEvent, handle_prescription_validated)
    
    logger.info("Notification handlers registered")
