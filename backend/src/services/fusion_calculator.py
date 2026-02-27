from typing import Dict, Any, List, Optional
from src.orchestrator_models import FusionState

def weighted_average(scores_and_weights: List[tuple[Optional[float], float]]) -> float:
    # (score, weight)
    valid = [(s, w) for s, w in scores_and_weights if s is not None]
    total_weight = sum(w for s, w in valid)
    if total_weight == 0:
        return 0.0
    return sum(s * w for s, w in valid) / total_weight

class FusionCalculator:
    def __init__(self, session_id: str):
        self.session_id = session_id
        
        # Raw contributing scores (None means not yet collected)
        self.scores: Dict[str, Optional[float]] = {
            "intent_classification": None,
            "ocr_confidence": None,
            "severity_inverted": None,
            "contraindication_clear": 1.0, # Default safe until proven otherwise
            "inventory_match_score": None,
            "identity_resolution": None,
            "intent_extraction": None,
            "pipeline_completion": 0.0
        }
        
        self.total_agents_expected = 4
        self.agents_completed = set()
        self.pipeline_phase = "intake"
        self.halt_reason = None
        self.last_event_agent = "SYSTEM"
        self.last_event_type = "init"
        
    def process_event(self, event: Dict[str, Any]) -> bool:
        """Process an incoming trace event and update fusion scores. Returns True if a scoreable signal changed."""
        changed = False
        
        agent = event.get("agent", "")
        type_ = event.get("type", "")
        status = event.get("status", "")
        details = event.get("details", {})
        
        self.last_event_agent = agent
        self.last_event_type = type_
        
        # 1. Update Phase and Completion
        if status == "completed" and agent not in self.agents_completed:
            self.agents_completed.add(agent)
            old_completion = self.scores["pipeline_completion"]
            self.scores["pipeline_completion"] = min(1.0, len(self.agents_completed) / self.total_agents_expected)
            if self.scores["pipeline_completion"] != old_completion:
                changed = True
                
        # Phase tracking
        old_phase = self.pipeline_phase
        if agent in ["IdentityAgent", "FrontDesk"]:
            self.pipeline_phase = "intake"
        elif agent in ["VisionAgent", "MedicalValidator"]:
            self.pipeline_phase = "validation"
        elif agent == "Inventory":
            self.pipeline_phase = "inventory"
        elif agent == "Fulfillment":
            self.pipeline_phase = "fulfillment"
            
        if status in ["failed", "rejected"] or "failed" in type_:
            self.pipeline_phase = "halted"
            self.halt_reason = details.get("reason", details.get("error", f"{agent} Failed"))
            
        if status == "completed" and agent == "Fulfillment":
            self.pipeline_phase = "complete"

        if old_phase != self.pipeline_phase:
            changed = True
            
        # 2. Extract specific scores from event details
        
        # Identity
        if agent == "IdentityAgent" and "confidence" in details:
            self.scores["identity_resolution"] = details["confidence"]
            changed = True
            
        # Intent Classification & Extraction
        if agent == "FrontDesk":
            if "confidence" in details:
                self.scores["intent_classification"] = details["confidence"]
                self.scores["intent_extraction"] = details.get("confidence", 0.0) # often same
                changed = True
                
        # Vision / OCR
        if agent == "VisionAgent" and "confidence_score" in details:
            self.scores["ocr_confidence"] = details["confidence_score"]
            changed = True
        if agent == "MedicalValidator" and "reconstruction_confidence" in details:
            self.scores["ocr_confidence"] = details["reconstruction_confidence"]
            changed = True
            
        # Severity Scorer
        if "severity_score" in details:
            score = details["severity_score"]
            try:
                score_val = float(score)
                self.scores["severity_inverted"] = max(0.0, 1.0 - (score_val / 10.0))
                changed = True
            except (ValueError, TypeError):
                pass
                
        # Contraindications / Safety
        if agent == "MedicalValidator":
            if "safe_to_dispense" in details:
                safe = details["safe_to_dispense"]
                self.scores["contraindication_clear"] = 1.0 if safe else 0.0
                changed = True
            if "safety_issues" in details and details["safety_issues"]:
                # If there are safety issues, it's not clear
                self.scores["contraindication_clear"] = 0.0
                changed = True

        # Inventory match
        if agent == "Inventory":
            if "match_score" in details:
                self.scores["inventory_match_score"] = float(details["match_score"])
                changed = True
            elif "stock_status" in details: 
                # fallback heuristics
                if details["stock_status"] == "in_stock":
                    self.scores["inventory_match_score"] = 1.0
                elif details["stock_status"] == "substitute":
                    self.scores["inventory_match_score"] = 0.6
                elif details["stock_status"] == "out_of_stock":
                    self.scores["inventory_match_score"] = 0.0
                changed = True

        return changed
        
    def get_fusion_state(self) -> FusionState:
        # Safety Confidence
        safety_components = [
            (self.scores["intent_classification"], 0.20),
            (self.scores["ocr_confidence"], 0.15),
            (self.scores["severity_inverted"], 0.40),
            (self.scores["contraindication_clear"], 0.25)
        ]
        safety_confidence = weighted_average(safety_components)
        
        # Fulfillment Confidence
        fulfillment_components = [
            (self.scores["inventory_match_score"], 0.45),
            (self.scores["identity_resolution"], 0.20),
            (self.scores["intent_extraction"], 0.20),
            (self.scores["pipeline_completion"], 0.15)
        ]
        fulfillment_confidence = weighted_average(fulfillment_components)
        
        # Alert Level Logic
        safe = self.scores["contraindication_clear"] == 1.0
        severity_score = 0.0
        if self.scores["severity_inverted"] is not None:
            severity_score = (1.0 - self.scores["severity_inverted"]) * 10
            
        if safety_confidence < 0.30 or not safe:
            alert_level = "critical"
        elif safety_confidence < 0.60 or severity_score > 7:
            alert_level = "warn"
        else:
            alert_level = "nominal"
            
        # Dominant Mode
        if self.pipeline_phase in ["intake", "validation"]:
            dominant_mode = "safety"
        else:
            dominant_mode = "fulfillment"
            
        return FusionState(
            session_id=self.session_id,
            safety_confidence=round(safety_confidence, 2),
            fulfillment_confidence=round(fulfillment_confidence, 2),
            dominant_mode=dominant_mode,
            pipeline_phase=self.pipeline_phase,
            contributing_scores={k: round(v, 2) if v is not None else None for k, v in self.scores.items()},
            last_event_agent=self.last_event_agent,
            last_event_type=self.last_event_type,
            alert_level=alert_level,
            halt_reason=self.halt_reason
        )
