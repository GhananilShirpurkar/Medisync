import asyncio
import json
import logging
import uuid
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import WebSocket

# Try importing Langfuse for tracing
try:
    from langfuse.decorators import observe, langfuse_context
    HAS_LANGFUSE = True
    # Verify environment
    if not os.environ.get("LANGFUSE_PUBLIC_KEY") or not os.environ.get("LANGFUSE_SECRET_KEY"):
        print("⚠️  Warning: Langfuse Keys are missing from environment.")
    else:
        print("✅ Langfuse instrumentation enabled and keys found.")
except ImportError:
    HAS_LANGFUSE = False
    print("⚠️  Warning: langfuse package not installed. Tracing is disabled.")
    
    # Dummy mock decorators if not installed
    def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
        
    class MockLangfuseContext:
        def update_current_observation(self, **kwargs): pass
        def update_current_trace(self, **kwargs): pass
        def flush(self): pass
    langfuse_context = MockLangfuseContext()

# Standard logging
logger = logging.getLogger(__name__)

class TraceManager:
    """
    Singleton for managing distributed traces and streaming them to WebSockets.
    Implements a pub/sub pattern for real-time frontend updates.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TraceManager, cls).__new__(cls)
            cls._instance.connections: Dict[str, List[WebSocket]] = {}
            cls._instance.traces: Dict[str, List[Dict[str, Any]]] = {}
        return cls._instance

    async def connect(self, session_id: str, websocket: WebSocket):
        """Connect a frontend client to a session stream."""
        await websocket.accept()
        if session_id not in self.connections:
            self.connections[session_id] = []
            
            # Start Orchestrator exactly once per session
            try:
                from src.agents.orchestrator_agent import OrchestratorAgent
                orchestrator = OrchestratorAgent(session_id, self)
                self.connections[session_id].append(orchestrator)
                logger.info(f"OrchestratorAgent attached to session {session_id}")
            except Exception as e:
                logger.error(f"Failed to attach OrchestratorAgent: {e}")
                
        self.connections[session_id].append(websocket)
        
        # Send existing history for this session if available
        if session_id in self.traces:
            for trace in self.traces[session_id]:
                await websocket.send_json(trace)
                
        logger.info(f"WebSocket connected for session {session_id}")

    def disconnect(self, session_id: str, websocket: WebSocket):
        """Disconnect a client."""
        if session_id in self.connections:
            if websocket in self.connections[session_id]:
                self.connections[session_id].remove(websocket)

    async def emit(self, 
                   session_id: str, 
                   agent_name: str, 
                   step_name: str, 
                   action_type: str, 
                   status: str, 
                   details: Dict[str, Any] = None,
                   parent_id: Optional[str] = None):
        """
        Emit a structured trace event.
        
        Args:
            session_id: The conversation session ID
            agent_name: Name of the agent (e.g., "FrontDesk", "Inventory")
            step_name: Human readable step (e.g., "Classifying Intent")
            action_type: "thinking" | "tool_use" | "decision" | "response" | "error"
            status: "started" | "running" | "completed" | "failed"
            details: JSON-serializable details object (inputs, outputs, tool args)
            parent_id: Optional UUID to link substeps
        """
        event_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        event = {
            "id": event_id,
            "session_id": session_id,
            "timestamp": timestamp,
            "agent": agent_name,
            "step": step_name,
            "type": action_type,
            "status": status,
            "details": details or {},
            "parent_id": parent_id
        }
        
        # 1. Store locally (Lite persistence layer)
        if session_id not in self.traces:
            self.traces[session_id] = []
        self.traces[session_id].append(event)
        
        # 2. Log to console (Deep formatted)
        self._log_to_console(event)
        
        # Ensure Orchestrator Agent is always attached, even before WS connects
        # to prevent missing traces during the race condition on session startup
        if session_id not in self.connections:
            self.connections[session_id] = []
            try:
                from src.orchestrator_models import FusionState
                from src.agents.orchestrator_agent import OrchestratorAgent
                # Check if it's already there (though we just created the list)
                orchestrator = OrchestratorAgent(session_id, self)
                self.connections[session_id].append(orchestrator)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Failed to attach OrchestratorAgent inline: {e}")

        # Artificial delay to stagger UI rendering for a perceived "real-time" streaming feel
        import asyncio
        if status == "started":
            await asyncio.sleep(0.3)
        elif status == "completed":
            await asyncio.sleep(0.5)
        elif status == "running":
            await asyncio.sleep(0.1)

        # 3. Stream to WebSockets
        if session_id in self.connections:
            # Broadcast to all connected clients for this session
            dead_connections = []
            
            for ws in self.connections[session_id]:
                try:
                    # OrchestratorAgent uses duck typing for 'send_json' but doesn't need sleep
                    if hasattr(ws, 'session_id') and type(ws).__name__ == "OrchestratorAgent":
                        # Fast-path for internal agent
                        await ws.send_json(event)
                    else:
                        await ws.send_json(event)
                except Exception as e:
                    logger.warning(f"Failed to send trace to ws: {e}")
                    dead_connections.append(ws)
            
            # Cleanup dead connections
            for ws in dead_connections:
                self.disconnect(session_id, ws)

    def _log_to_console(self, event: Dict[str, Any]):
        """Pretty print trace to console."""
        icon = {
            "thinking": "🧠",
            "tool_use": "🛠️",
            "decision": "🤔",
            "response": "🗣️",
            "error": "❌",
            "event": "⚡"
        }.get(event["type"], "ℹ️")
        
        if event["status"] == "failed":
            icon = "❌"
        elif event["status"] == "completed":
            icon = "✅"
            
        print(f"{icon} [{event['agent']}] {event['step']} ({event['status']}): {str(event.get('details', ''))[:100]}...")

# Global Instance
trace_manager = TraceManager()

# ─── Backward-compatible Aliases (used by agents pre-Phase 6) ────────────────
#
# Agents previously used @trace_agent and @trace_tool_call decorators
# from this module. We keep them as lightweight pass-through wrappers
# so existing code doesn't need to change.
#
def trace_agent(agent_name: str, agent_type: str = "agent"):
    """
    Decorator that identifies an agent function.
    Handles both sync and async agent functions.
    """
    def decorator(func):
        import functools
        import asyncio
        
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
        else:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def trace_tool_call(tool_name: str, tool_type: str = "tool"):
    """
    Decorator that identifies a tool/function call within an agent.
    Handles both sync and async functions.
    """
    def decorator(func):
        import functools
        import asyncio
        
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
        else:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
        return wrapper
    return decorator


# Legacy singleton alias (used in older test files)
observability_service = trace_manager

