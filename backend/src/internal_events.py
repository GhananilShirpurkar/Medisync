import asyncio
from typing import Callable, Any, Dict, List
from collections import defaultdict

# Event Types
PATIENT_IDENTIFIED = "PATIENT_IDENTIFIED"
ORDER_COMPLETED = "ORDER_COMPLETED"

class EventManager:
    """
    Simple asynchronous event bus for decoupling components.
    """
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Any], Any]]] = defaultdict(list)

    def subscribe(self, event_type: str, callback: Callable[[Any], Any]):
        """Subscribe to an event type."""
        self._subscribers[event_type].append(callback)
        print(f"EVENT: Subscribed to {event_type} -> {callback.__name__}")

    async def emit(self, event_type: str, data: Any):
        """Emit an event to all subscribers."""
        if event_type not in self._subscribers:
            return
        
        print(f"EVENT: Emitting {event_type} with data: {data}")
        
        tasks = []
        for callback in self._subscribers[event_type]:
            if asyncio.iscoroutinefunction(callback):
                tasks.append(asyncio.create_task(callback(data)))
            else:
                # Run synchronous callbacks in executor to avoid blocking loop
                loop = asyncio.get_running_loop()
                tasks.append(loop.run_in_executor(None, callback, data))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

# Global instance
event_manager = EventManager()
