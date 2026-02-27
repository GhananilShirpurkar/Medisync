from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.services.observability_service import trace_manager

router = APIRouter(prefix="/ws", tags=["streaming"])

@router.websocket("/trace/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for streaming real-time agent traces.
    Connect here to get the 'Manus AI' style live dashboard updates.
    """
    await trace_manager.connect(session_id, websocket)
    try:
        while True:
            # Keep connection alive, maybe handle client messages (like "pause", "stop")
            # For now, just a heartbeat listener
            data = await websocket.receive_text()
            # We could implement "pause" or "approve" logic here
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        trace_manager.disconnect(session_id, websocket)
