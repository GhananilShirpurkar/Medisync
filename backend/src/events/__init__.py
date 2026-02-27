"""
EVENT SYSTEM
============
Event-driven architecture components for decoupled communication.
"""

from src.events.event_bus import EventBus, get_event_bus
from src.events.event_types import (
    Event,
    OrderCreatedEvent,
    OrderRejectedEvent,
    PrescriptionValidatedEvent,
    InventoryCheckedEvent,
    NotificationEvent
)

__all__ = [
    "EventBus",
    "get_event_bus",
    "Event",
    "OrderCreatedEvent",
    "OrderRejectedEvent",
    "PrescriptionValidatedEvent",
    "InventoryCheckedEvent",
    "NotificationEvent"
]
