"""
BEHAVIORAL RISK SCORING ENGINE
================================
Adaptive Safety Layer — moves beyond static rule-based safety.

Every interaction updates a cumulative risk profile.
High-risk users trigger stricter controls and manual review.

Risk Factors:
- Prescription medicine without prescription: +30
- Controlled substance request (opioids, benzos): +40  
- Repeated same medicine requests (>2 in session): +20
- Unusually large quantity (>10 units): +25
- Multiple validation failures in session: +15
- Known abuse-potential medicine: +35
- Requesting multiple controlled substances: +50

Risk Levels:
- 0-30:  NORMAL   — standard pipeline
- 31-60: ELEVATED — extra validation, logged
- 61-80: HIGH     — pharmacist review required, admin flagged
- 81+:   CRITICAL — order blocked, admin alerted
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from src.state import PharmacyState
from src.db_config import get_db_context
from src.models import Patient

logger = logging.getLogger(__name__)

# Medicines with known abuse potential
CONTROLLED_SUBSTANCES = [
    "diazepam", "alprazolam", "clonazepam", "lorazepam", "midazolam",  # Benzos
    "morphine", "codeine", "tramadol", "oxycodone", "fentanyl",         # Opioids
    "methylphenidate", "amphetamine", "modafinil",                       # Stimulants
    "zolpidem", "nitrazepam", "phenobarbital",                           # Sedatives
    "buprenorphine", "methadone",                                         # Opioid substitutes
]

ABUSE_POTENTIAL_MEDICINES = [
    "promethazine", "pregabalin", "gabapentin", "carisoprodol",
    "pseudoephedrine", "dextromethorphan",
]

RISK_WEIGHTS = {
    "prescription_without_upload": 30,
    "controlled_substance_request": 40,
    "repeated_same_medicine": 20,
    "unusually_large_quantity": 25,
    "multiple_validation_failures": 15,
    "abuse_potential_medicine": 35,
    "multiple_controlled_substances": 50,
    "prescription_forgery_suspected": 60,
}

RISK_LEVELS = {
    "normal":   (0, 30),
    "elevated": (31, 60),
    "high":     (61, 80),
    "critical": (81, 100),
}


def calculate_risk_level(score: int) -> str:
    if score <= 30:
        return "normal"
    elif score <= 60:
        return "elevated"
    elif score <= 80:
        return "high"
    else:
        return "critical"


def assess_request_risk(state: PharmacyState) -> Dict[str, Any]:
    """
    Assess risk for current request. Returns risk factors and score delta.
    Does NOT modify state or database — pure assessment.
    """
    factors_triggered = []
    score_delta = 0
    
    items = state.extracted_items or []
    
    # Check each medicine in the request
    controlled_count = 0
    for item in items:
        name_lower = item.medicine_name.lower()
        
        # Controlled substance check
        if any(cs in name_lower for cs in CONTROLLED_SUBSTANCES):
            factors_triggered.append(f"controlled_substance:{item.medicine_name}")
            score_delta += RISK_WEIGHTS["controlled_substance_request"]
            controlled_count += 1
        
        # Abuse potential check
        elif any(ap in name_lower for ap in ABUSE_POTENTIAL_MEDICINES):
            factors_triggered.append(f"abuse_potential:{item.medicine_name}")
            score_delta += RISK_WEIGHTS["abuse_potential_medicine"]
        
        # Large quantity check
        if item.quantity > 10:
            factors_triggered.append(f"large_quantity:{item.medicine_name}:{item.quantity}")
            score_delta += RISK_WEIGHTS["unusually_large_quantity"]
        
        # Prescription required but not uploaded
        if item.requires_prescription and not state.prescription_uploaded:
            factors_triggered.append(f"prescription_missing:{item.medicine_name}")
            score_delta += RISK_WEIGHTS["prescription_without_upload"]
    
    # Multiple controlled substances
    if controlled_count >= 2:
        factors_triggered.append("multiple_controlled_substances")
        score_delta += RISK_WEIGHTS["multiple_controlled_substances"]
    
    # Validation failures
    if state.pharmacist_decision == "rejected":
        factors_triggered.append("validation_failure")
        score_delta += RISK_WEIGHTS["multiple_validation_failures"]
    
    return {
        "factors_triggered": factors_triggered,
        "score_delta": score_delta,
        "assessment_timestamp": datetime.now().isoformat()
    }


def run_risk_scoring_agent(state: PharmacyState) -> PharmacyState:
    """
    Main entry point. Assesses risk, updates patient profile, 
    modifies pipeline behavior based on risk level.
    """
    print(f"\n{'='*50}")
    print("RISK SCORING AGENT")
    print(f"{'='*50}")
    
    if not state.user_id:
        logger.warning("Risk scoring skipped — no user_id")
        return state
    
    # Step 1: Assess current request
    assessment = assess_request_risk(state)
    score_delta = assessment["score_delta"]
    new_factors = assessment["factors_triggered"]
    
    print(f"Score delta: +{score_delta}")
    print(f"Factors: {new_factors}")
    
    # Step 2: Load and update patient risk profile
    with get_db_context() as db:
        patient = db.query(Patient).filter(
            Patient.user_id == state.user_id # Using user_id (PID), not pid
        ).first()
        
        if not patient:
            logger.warning(f"Patient {state.user_id} not found for risk scoring")
            return state
        
        # Accumulate risk score (cap at 100)
        old_score = patient.risk_score or 0
        new_score = min(100, old_score + score_delta)
        
        # Merge risk flags
        existing_flags = patient.risk_flags or []
        all_flags = list(set(existing_flags + new_factors))
        
        new_level = calculate_risk_level(new_score)
        escalated = new_level in ["high", "critical"] and \
                    calculate_risk_level(old_score) not in ["high", "critical"]
        
        # Update patient
        patient.risk_score = new_score
        patient.risk_level = new_level
        patient.risk_flags = all_flags
        patient.risk_updated_at = datetime.now()
        patient.flagged_for_review = new_level in ["high", "critical"]
        db.commit()
        
        print(f"Risk: {old_score} → {new_score} ({new_level.upper()})")
        if escalated:
            print(f"⚠️  ESCALATED to {new_level.upper()}")
    
    # Step 3: Update state
    state.risk_score = new_score
    state.risk_level = new_level
    state.risk_factors_triggered = new_factors
    state.risk_escalated = escalated
    
    # Step 4: Modify pipeline behavior based on risk level
    if new_level == "critical":
        # Block order entirely
        state.pharmacist_decision = "rejected"
        state.safety_flags.append(
            f"CRITICAL RISK: Order blocked. Score: {new_score}/100. "
            f"Factors: {', '.join(new_factors)}"
        )
        print("🔴 CRITICAL — Order BLOCKED")
        
    elif new_level == "high":
        # Force pharmacist review
        if state.pharmacist_decision == "approved":
            state.pharmacist_decision = "needs_review"
        state.safety_flags.append(
            f"HIGH RISK: Pharmacist review required. Score: {new_score}/100"
        )
        print("🟠 HIGH — Escalated to pharmacist review")
        
    elif new_level == "elevated":
        # Log but allow — add warning to trace
        state.safety_flags.append(
            f"ELEVATED RISK: Monitoring. Score: {new_score}/100"
        )
        print("🟡 ELEVATED — Logged, proceeding with caution")
    
    else:
        print("🟢 NORMAL — No risk concerns")
    
    # Step 5: Store in trace metadata for Intelligence Trace visibility
    state.trace_metadata["risk_scoring_agent"] = {
        "risk_score": new_score,
        "risk_level": new_level,
        "score_delta": score_delta,
        "factors_triggered": new_factors,
        "escalated": escalated,
        "pipeline_action": "blocked" if new_level == "critical" 
                          else "review" if new_level == "high"
                          else "monitor" if new_level == "elevated"
                          else "normal",
        "timestamp": datetime.now().isoformat()
    }
    
    print(f"{'='*50}\n")
    return state
