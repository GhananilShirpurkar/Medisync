import asyncio
import uuid
import logging
from datetime import datetime
from typing import Dict, Any

from src.services.fusion_calculator import FusionCalculator

logger = logging.getLogger(__name__)

class OrchestratorAgent:
    def __init__(self, session_id: str, trace_manager):
        self.session_id = session_id
        self.trace_manager = trace_manager
        self.calculator = FusionCalculator(session_id)
        
        # We simulate being a WebSocket so that TraceManager.emit broadcasts to us.
        # Ensure we don't accidentally get dropped by throwing exceptions.
        pass
        
    async def send_json(self, event: Dict[str, Any]):
        """
        Duck-typed method to act like a WebSocket connection.
        TraceManager will call this when broadcasting to the session.
        """
        agent = event.get("agent", "")
        # Do not process our own events to prevent infinite loops
        if agent == "ORCHESTRATOR":
            return
            
        try:
            changed = self.calculator.process_event(event)
            status = event.get("status", "")
            
            # Emit a fusion update if scores changed
            if changed:
                await self._emit_fusion_update("running")
                
            # Emit final session closed event if halted or fully completed
            if status in ["failed", "rejected"] or "failed" in event.get("type", ""):
                await self._emit_session_closed("halted")
            elif status == "completed" and agent == "Fulfillment":
                await self._emit_session_closed("complete")
                
        except Exception as e:
            logger.error(f"OrchestratorAgent failed on event processing: {e}", exc_info=True)

    async def _emit_fusion_update(self, status: str):
        state = self.calculator.get_fusion_state()
        event_id = str(uuid.uuid4())
        
        payload = {
            "id": event_id,
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "agent": "ORCHESTRATOR",
            "step": "fusion_update",
            "type": "fusion",
            "status": status,
            "details": {
                "safety_confidence": state.safety_confidence,
                "fulfillment_confidence": state.fulfillment_confidence,
                "dominant_mode": state.dominant_mode,
                "pipeline_phase": state.pipeline_phase,
                "alert_level": state.alert_level,
                "contributing_scores": state.contributing_scores,
                "halt_reason": state.halt_reason
            },
            "parent_id": None
        }
        
        # Directly store and broadcast without recursively re-triggering ourselves
        self.trace_manager.traces.setdefault(self.session_id, []).append(payload)
        
        # We need to broadcast to all ACTUAL websockets, but NOT to ourselves
        dead_connections = []
        for ws in self.trace_manager.connections.get(self.session_id, []):
            if ws is self:
                continue
            try:
                await ws.send_json(payload)
            except Exception as e:
                logger.warning(f"Failed to send Orchestrator trace to ws: {e}")
                dead_connections.append(ws)
                
        for ws in dead_connections:
            self.trace_manager.disconnect(self.session_id, ws)
            
    async def _emit_session_closed(self, status: str):
        state = self.calculator.get_fusion_state()
        event_id = str(uuid.uuid4())
        
        # Wait a moment to ensure it lands AFTER the failure/completion event
        await asyncio.sleep(0.1)
        
        payload = {
            "id": event_id,
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "agent": "ORCHESTRATOR",
            "step": "session_closed",
            "type": "fusion",
            "status": status,
            "details": {
                "final_safety_confidence": state.safety_confidence,
                "final_fulfillment_confidence": state.fulfillment_confidence,
                "alert_level": state.alert_level,
                "halt_reason": state.halt_reason,
                "total_agents_fired": len(self.calculator.agents_completed),
                # Hardcode session duration for now or compute it
                "session_duration_ms": 4200 
            },
            "parent_id": None
        }
        
        self.trace_manager.traces.setdefault(self.session_id, []).append(payload)
        
        dead_connections = []
        for ws in self.trace_manager.connections.get(self.session_id, []):
            if ws is self:
                continue
            try:
                await ws.send_json(payload)
            except Exception as e:
                dead_connections.append(ws)
                
        for ws in dead_connections:
            self.trace_manager.disconnect(self.session_id, ws)
