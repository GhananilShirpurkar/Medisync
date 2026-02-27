"""
EVENT HANDLERS
==============
Event subscribers that react to domain events.
"""

from src.events.handlers.notification_handler import (
    handle_order_created,
    handle_order_rejected,
    handle_prescription_validated,
    register_notification_handlers
)

__all__ = [
    "handle_order_created",
    "handle_order_rejected",
    "handle_prescription_validated",
    "register_notification_handlers"
]
