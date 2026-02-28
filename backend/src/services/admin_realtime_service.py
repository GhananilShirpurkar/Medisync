import asyncio
import logging
from typing import List, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

class AdminRealtimeManager:
    """
    Manages WebSocket connections for the admin dashboard and broadcasts system updates.
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._is_initialized = False

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Admin dashboard client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Admin dashboard client disconnected. Remaining: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected admin clients."""
        if not self.active_connections:
            return

        logger.debug(f"Broadcasting to {len(self.active_connections)} admin(s): {message.get('type')}")
        
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.append(connection)
        
        for dead in dead_connections:
            self.disconnect(dead)

    def initialize(self):
        """Subscribe to the global event bus to listen for relevant events."""
        if self._is_initialized:
            return
            
        try:
            from src.events.event_bus import get_event_bus
            from src.events.event_types import (
                OrderCreatedEvent, OrderRejectedEvent, 
                InventoryCheckedEvent, StockReservedEvent
            )
            
            bus = get_event_bus()
            
            # Helper to create async wrapper for sync handlers if needed
            # But the event_bus handles async handlers if they are async functions
            
            async def handle_order_created(event: OrderCreatedEvent):
                await self.broadcast({
                    "type": "ORDER_CREATED",
                    "data": {
                        "id": event.order_id,
                        "user_id": event.user_id,
                        "total": event.total_amount,
                        "items_count": len(event.items),
                        "timestamp": event.timestamp.isoformat()
                    }
                })

            async def handle_order_rejected(event: OrderRejectedEvent):
                await self.broadcast({
                    "type": "ORDER_REJECTED",
                    "data": {
                        "user_id": event.user_id,
                        "reason": event.reason,
                        "timestamp": event.timestamp.isoformat()
                    }
                })

            async def handle_stock_reserved(event: StockReservedEvent):
                await self.broadcast({
                    "type": "STOCK_UPDATED",
                    "data": {
                        "medicine_name": event.medicine_name,
                        "quantity": event.quantity,
                        "timestamp": event.timestamp.isoformat()
                    }
                })

            # Subscribe
            bus.subscribe(OrderCreatedEvent, handle_order_created)
            bus.subscribe(OrderRejectedEvent, handle_order_rejected)
            bus.subscribe(StockReservedEvent, handle_stock_reserved)
            
            self._is_initialized = True
            logger.info("AdminRealtimeManager initialized and subscribed to EventBus")
        except Exception as e:
            logger.error(f"Failed to initialize AdminRealtimeManager: {e}")

# Global singleton
admin_realtime_manager = AdminRealtimeManager()
