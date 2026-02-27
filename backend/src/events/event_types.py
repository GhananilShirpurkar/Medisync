"""
EVENT TYPES
===========
Domain event definitions for the pharmacy system.

Events represent things that have happened in the system.
They are immutable and carry all necessary data.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


# ------------------------------------------------------------------
# BASE EVENT
# ------------------------------------------------------------------

class Event(BaseModel):
    """
    Base event class.
    
    All domain events inherit from this class.
    Events are immutable records of things that happened.
    """
    
    event_id: str = Field(default_factory=lambda: f"evt_{datetime.now().timestamp()}")
    event_type: str
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        frozen = True  # Immutable


# ------------------------------------------------------------------
# PRESCRIPTION EVENTS
# ------------------------------------------------------------------

class PrescriptionUploadedEvent(Event):
    """Prescription image uploaded by user."""
    
    event_type: str = "prescription.uploaded"
    user_id: str
    image_path: Optional[str] = None


class PrescriptionValidatedEvent(Event):
    """Prescription validated by medical validation agent."""
    
    event_type: str = "prescription.validated"
    user_id: str
    decision: str  # approved | rejected | needs_review
    safety_issues: List[str]


# ------------------------------------------------------------------
# INVENTORY EVENTS
# ------------------------------------------------------------------

class InventoryCheckedEvent(Event):
    """Inventory checked for prescription items."""
    
    event_type: str = "inventory.checked"
    user_id: str
    availability_score: float
    items_available: int
    items_total: int


class StockReservedEvent(Event):
    """Stock reserved for an order."""
    
    event_type: str = "inventory.reserved"
    medicine_name: str
    quantity: int
    reservation_id: str


# ------------------------------------------------------------------
# ORDER EVENTS
# ------------------------------------------------------------------

class OrderCreatedEvent(Event):
    """Order successfully created."""
    
    event_type: str = "order.created"
    order_id: str
    user_id: str
    phone: Optional[str] = None
    total_amount: float
    items: List[Dict[str, Any]]
    pharmacist_decision: str


class OrderRejectedEvent(Event):
    """Order rejected due to validation or inventory issues."""
    
    event_type: str = "order.rejected"
    user_id: str
    phone: Optional[str] = None
    reason: str
    details: Dict[str, Any]


class OrderFailedEvent(Event):
    """Order processing failed due to system error."""
    
    event_type: str = "order.failed"
    user_id: str
    phone: Optional[str] = None
    error: str
    error_type: str


# ------------------------------------------------------------------
# NOTIFICATION EVENTS
# ------------------------------------------------------------------

class NotificationEvent(Event):
    """Generic notification event."""
    
    event_type: str = "notification.send"
    user_id: str
    notification_type: str
    message: str
    priority: str  # low | medium | high | critical


# ------------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------------

def create_order_created_event(
    order_id: str,
    user_id: str,
    phone: Optional[str],
    total_amount: float,
    items: List[Dict[str, Any]],
    pharmacist_decision: str
) -> OrderCreatedEvent:
    """
    Factory function to create OrderCreatedEvent.
    
    Args:
        order_id: Order ID
        user_id: User ID
        total_amount: Total order amount
        items: List of order items
        pharmacist_decision: Pharmacist decision
        
    Returns:
        OrderCreatedEvent instance
    """
    return OrderCreatedEvent(
        order_id=order_id,
        user_id=user_id,
        phone=phone,
        total_amount=total_amount,
        items=items,
        pharmacist_decision=pharmacist_decision
    )


def create_order_rejected_event(
    user_id: str,
    reason: str,
    details: Optional[Dict[str, Any]] = None
) -> OrderRejectedEvent:
    """
    Factory function to create OrderRejectedEvent.
    
    Args:
        user_id: User ID
        reason: Rejection reason
        details: Additional details
        
    Returns:
        OrderRejectedEvent instance
    """
    return OrderRejectedEvent(
        user_id=user_id,
        reason=reason,
        details=details
    )