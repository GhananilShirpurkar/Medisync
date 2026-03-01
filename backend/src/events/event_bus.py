"""
EVENT BUS
=========
In-memory pub/sub event bus for decoupled communication.

Pattern: Observer/Pub-Sub
- Publishers emit events without knowing subscribers
- Subscribers register handlers for event types
- Async execution prevents blocking
- Failures in one handler don't affect others
"""

from typing import Callable, Dict, List, Any, Type, Optional
from collections import defaultdict
import asyncio
import logging
from datetime import datetime

from src.events.event_types import Event

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# EVENT BUS
# ------------------------------------------------------------------

class EventBus:
    """
    In-memory event bus for pub/sub messaging.
    
    Features:
    - Type-based subscription
    - Async handler execution
    - Error isolation (one handler failure doesn't affect others)
    - Event history for debugging
    """
    
    def __init__(self, max_history: int = 1000):
        """
        Initialize event bus.
        
        Args:
            max_history: Maximum number of events to keep in history
        """
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._event_history: List[Dict[str, Any]] = []
        self._max_history = max_history
        self._stats = {
            "events_published": 0,
            "events_processed": 0,
            "handler_errors": 0
        }
    
    def subscribe(self, event_type: Type[Event], handler: Callable[[Event], None]):
        """
        Subscribe a handler to an event type.
        
        Args:
            event_type: Event class to subscribe to
            handler: Callable that takes an Event and returns None
            
        Example:
            bus.subscribe(OrderCreatedEvent, send_order_notification)
        """
        event_name = event_type.__name__
        if handler not in self._subscribers[event_name]:
            self._subscribers[event_name].append(handler)
            logger.info(f"Subscribed handler to {event_name}: {handler.__name__}")
        else:
            logger.debug(f"Handler {handler.__name__} already subscribed to {event_name}")
    
    def unsubscribe(self, event_type: Type[Event], handler: Callable[[Event], None]):
        """
        Unsubscribe a handler from an event type.
        
        Args:
            event_type: Event class to unsubscribe from
            handler: Handler to remove
        """
        event_name = event_type.__name__
        if handler in self._subscribers[event_name]:
            self._subscribers[event_name].remove(handler)
            logger.info(f"Unsubscribed handler from {event_name}: {handler.__name__}")
    
    def publish(self, event: Event):
        """
        Publish an event to all subscribers.
        
        Executes handlers synchronously but isolates errors.
        Each handler failure is logged but doesn't affect others.
        
        Args:
            event: Event instance to publish
        """
        event_name = type(event).__name__
        self._stats["events_published"] += 1
        
        # Add to history
        self._add_to_history(event)
        
        # Get subscribers for this event type
        handlers = self._subscribers.get(event_name, [])
        
        if not handlers:
            logger.debug(f"No subscribers for {event_name}")
            return
        
        logger.info(f"Publishing {event_name} to {len(handlers)} handler(s)")
        
        # Execute each handler with error isolation
        for handler in handlers:
            try:
                handler(event)
                self._stats["events_processed"] += 1
                logger.debug(f"Handler {handler.__name__} processed {event_name}")
            except Exception as e:
                self._stats["handler_errors"] += 1
                logger.error(
                    f"Handler {handler.__name__} failed for {event_name}: {e}",
                    exc_info=True
                )
    
    async def publish_async(self, event: Event):
        """
        Publish an event asynchronously.
        
        Handlers are executed concurrently without blocking.
        
        Args:
            event: Event instance to publish
        """
        event_name = type(event).__name__
        self._stats["events_published"] += 1
        
        # Add to history
        self._add_to_history(event)
        
        # Get subscribers for this event type
        handlers = self._subscribers.get(event_name, [])
        
        if not handlers:
            logger.debug(f"No subscribers for {event_name}")
            return
        
        logger.info(f"Publishing {event_name} to {len(handlers)} handler(s) (async)")
        
        # Execute handlers concurrently
        tasks = []
        for handler in handlers:
            task = asyncio.create_task(self._execute_handler_async(handler, event))
            tasks.append(task)
        
        # Wait for all handlers to complete
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _execute_handler_async(self, handler: Callable, event: Event):
        """
        Execute a handler asynchronously with error isolation.
        
        Args:
            handler: Handler function
            event: Event to pass to handler
        """
        event_name = type(event).__name__
        try:
            # Check if handler is async
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                # Run sync handler in executor
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, handler, event)
            
            self._stats["events_processed"] += 1
            logger.debug(f"Handler {handler.__name__} processed {event_name}")
        except Exception as e:
            self._stats["handler_errors"] += 1
            logger.error(
                f"Handler {handler.__name__} failed for {event_name}: {e}",
                exc_info=True
            )
    
    def _add_to_history(self, event: Event):
        """
        Add event to history for debugging.
        
        Args:
            event: Event to add
        """
        self._event_history.append({
            "event_type": type(event).__name__,
            "event_id": event.event_id,
            "timestamp": event.timestamp.isoformat(),
            "data": event.data
        })
        
        # Trim history if needed
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]
    
    def get_history(self, event_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get event history.
        
        Args:
            event_type: Filter by event type (optional)
            limit: Maximum number of events to return
            
        Returns:
            List of event dictionaries
        """
        history = self._event_history
        
        if event_type:
            history = [e for e in history if e["event_type"] == event_type]
        
        return history[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get event bus statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            **self._stats,
            "active_subscriptions": sum(len(handlers) for handlers in self._subscribers.values()),
            "event_types": list(self._subscribers.keys()),
            "history_size": len(self._event_history)
        }
    
    def clear_history(self):
        """Clear event history."""
        self._event_history.clear()
        logger.info("Event history cleared")
    
    def reset_stats(self):
        """Reset statistics."""
        self._stats = {
            "events_published": 0,
            "events_processed": 0,
            "handler_errors": 0
        }
        logger.info("Event bus statistics reset")


# ------------------------------------------------------------------
# SINGLETON INSTANCE
# ------------------------------------------------------------------

_event_bus_instance: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """
    Get the global event bus instance (singleton).
    
    Returns:
        EventBus instance
    """
    global _event_bus_instance
    if _event_bus_instance is None:
        _event_bus_instance = EventBus()
    # DEBUG: Log instance ID to detect multiple buses
    # print(f"DEBUG: EventBus instance ID: {id(_event_bus_instance)}")
    return _event_bus_instance


def reset_event_bus():
    """
    Reset the global event bus instance.
    
    Useful for testing.
    """
    global _event_bus_instance
    _event_bus_instance = None
