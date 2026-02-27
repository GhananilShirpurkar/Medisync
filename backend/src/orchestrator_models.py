from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class FusionState:
    session_id: str
    safety_confidence: float        # 0.0 - 1.0
    fulfillment_confidence: float   # 0.0 - 1.0
    dominant_mode: str              # "safety" | "fulfillment"
    pipeline_phase: str             # "intake" | "validation" | "inventory" | "fulfillment" | "complete" | "halted"
    contributing_scores: Dict[str, Any]  # breakdown of what fed into each score
    last_event_agent: str
    last_event_type: str
    alert_level: str                # "nominal" | "warn" | "critical"
    halt_reason: Optional[str]
