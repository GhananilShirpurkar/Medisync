"""
SEVERITY SCORING MODULE
=======================
Clinical triage capability for symptom severity assessment.

Responsibilities:
1. AI assigns severity score (1-10)
2. Identifies red flags
3. Determines recommended action
4. Provides confidence score

Architecture:
- AI provides advisory severity score
- Deterministic routing based on thresholds
- Emergency override for critical symptoms
"""

from typing import Dict, List, Optional
from src.services.llm_service import parse_structured
import logging

logger = logging.getLogger(__name__)

# Emergency red flags that trigger immediate escalation
EMERGENCY_RED_FLAGS = [
    "chest pain",
    "difficulty breathing",
    "unconscious",
    "seizure",
    "heavy bleeding",
    "stroke",
    "severe allergic reaction",
    "anaphylaxis",
    "heart attack",
    "can't breathe",
    "choking"
]

# Severity thresholds for deterministic routing
SEVERITY_THRESHOLDS = {
    "OTC_RECOMMENDATION": (1, 3),      # 1-3: Mild, self-limiting
    "PHARMACIST_CONSULT": (4, 6),     # 4-6: Moderate, needs consultation
    "DOCTOR_REFERRAL": (7, 8),        # 7-8: Serious, doctor required
    "EMERGENCY_ALERT": (9, 10)        # 9-10: Critical, emergency care
}


def assess_severity(
    symptoms: str,
    patient_context: Dict,
    conversation_history: List[Dict] = None
) -> Dict:
    """
    Assess symptom severity using AI + deterministic rules.
    
    Args:
        symptoms: User's symptom description
        patient_context: Patient age, allergies, conditions
        conversation_history: Previous messages for context
        
    Returns:
        Dict with severity assessment:
        {
            "severity_score": int (1-10),
            "risk_level": str,
            "red_flags_detected": List[str],
            "recommended_action": str,
            "confidence": float,
            "route": str (deterministic),
            "reasoning": str
        }
    """
    
    # Step 1: Get AI severity assessment
    ai_assessment = _get_ai_severity_score(symptoms, patient_context, conversation_history)
    
    # Step 2: Check for emergency red flags (deterministic override)
    emergency_override = _check_emergency_red_flags(symptoms, ai_assessment["red_flags_detected"])
    
    if emergency_override:
        # Override AI score if emergency detected
        ai_assessment["severity_score"] = max(ai_assessment["severity_score"], 9)
        ai_assessment["risk_level"] = "critical"
        ai_assessment["recommended_action"] = "emergency"
        logger.warning(f"Emergency override triggered: {emergency_override}")
    
    # Step 3: Apply deterministic routing based on severity score
    route = _determine_route(ai_assessment["severity_score"])
    
    # Step 4: Combine AI assessment with deterministic routing
    result = {
        **ai_assessment,
        "route": route,
        "emergency_override": emergency_override is not None,
        "routing_logic": "deterministic_threshold"
    }
    
    logger.info(f"Severity assessment: score={result['severity_score']}, route={route}")
    
    return result


def _get_ai_severity_score(
    symptoms: str,
    patient_context: Dict,
    conversation_history: List[Dict] = None
) -> Dict:
    """
    Use Gemini 2.5 Flash to assess severity.
    
    Returns structured JSON with severity analysis.
    """
    
    # Build context
    context_str = f"Symptoms: {symptoms}\n"
    
    if patient_context.get("age"):
        context_str += f"Age: {patient_context['age']}\n"
    
    if patient_context.get("allergies"):
        context_str += f"Allergies: {', '.join(patient_context['allergies'])}\n"
    
    if patient_context.get("existing_conditions"):
        context_str += f"Conditions: {', '.join(patient_context['existing_conditions'])}\n"
    
    if patient_context.get("symptom_duration"):
        context_str += f"Duration: {patient_context['symptom_duration']}\n"
    
    # Add conversation history for context
    if conversation_history:
        recent_messages = conversation_history[-5:]  # Last 5 messages
        context_str += "\nConversation:\n"
        for msg in recent_messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            context_str += f"{role}: {content}\n"
    
    # System instruction for severity scoring
    prompt = f"""You are a clinical triage assistant. Given user symptoms, analyze severity and return ONLY valid JSON in the following format:

{{
    "severity_score": integer (1-10),
    "risk_level": "low" | "moderate" | "high" | "critical",
    "red_flags_detected": [list of strings],
    "recommended_action": "otc" | "pharmacist" | "doctor" | "emergency",
    "confidence": float (0.0 - 1.0),
    "reasoning": "brief explanation"
}}

Severity Guidelines:
1-3: Mild, self-limiting symptoms (common cold, minor headache, mild indigestion)
4-6: Moderate, needs pharmacist consultation (persistent fever, moderate pain, prolonged symptoms)
7-8: Serious, doctor consultation required (high fever >3 days, severe pain, concerning symptoms)
9-10: Critical, emergency care required (chest pain, breathing difficulty, severe bleeding)

Red Flags (must set severity >= 8):
- Chest pain or pressure
- Difficulty breathing or shortness of breath
- Unconsciousness or altered mental state
- Seizures
- Heavy bleeding
- Severe allergic reaction
- Stroke symptoms (facial drooping, arm weakness, speech difficulty)
- Severe abdominal pain
- High fever with stiff neck

Patient Context:
{context_str}

Return ONLY JSON. No explanation text outside JSON."""

    try:
        # Call LLM for structured output
        response = parse_structured(prompt)
        
        # Validate response structure
        required_fields = ["severity_score", "risk_level", "red_flags_detected", "recommended_action", "confidence"]
        for field in required_fields:
            if field not in response:
                logger.error(f"Missing field in AI response: {field}")
                return _get_default_assessment()
        
        # Validate severity score range
        if not isinstance(response["severity_score"], int) or not (1 <= response["severity_score"] <= 10):
            logger.error(f"Invalid severity score: {response.get('severity_score')}")
            response["severity_score"] = 5  # Default to moderate
        
        # Validate risk level
        valid_risk_levels = ["low", "moderate", "high", "critical"]
        if response["risk_level"] not in valid_risk_levels:
            logger.error(f"Invalid risk level: {response.get('risk_level')}")
            response["risk_level"] = "moderate"
        
        # Validate recommended action
        valid_actions = ["otc", "pharmacist", "doctor", "emergency"]
        if response["recommended_action"] not in valid_actions:
            logger.error(f"Invalid recommended action: {response.get('recommended_action')}")
            response["recommended_action"] = "pharmacist"
        
        # Ensure red_flags_detected is a list
        if not isinstance(response["red_flags_detected"], list):
            response["red_flags_detected"] = []
        
        # Ensure confidence is float between 0 and 1
        if not isinstance(response["confidence"], (int, float)) or not (0 <= response["confidence"] <= 1):
            response["confidence"] = 0.7
        
        return response
        
    except Exception as e:
        logger.error(f"Error in AI severity assessment: {e}")
        return _get_default_assessment()


def _check_emergency_red_flags(symptoms: str, ai_red_flags: List[str]) -> Optional[str]:
    """
    Check for emergency red flags in symptoms or AI-detected flags.
    
    Returns the first emergency flag found, or None.
    """
    symptoms_lower = symptoms.lower()
    
    # Check symptoms text
    for flag in EMERGENCY_RED_FLAGS:
        if flag in symptoms_lower:
            return flag
    
    # Check AI-detected red flags
    for ai_flag in ai_red_flags:
        ai_flag_lower = ai_flag.lower()
        for emergency_flag in EMERGENCY_RED_FLAGS:
            if emergency_flag in ai_flag_lower:
                return ai_flag
    
    return None


def _determine_route(severity_score: int) -> str:
    """
    Deterministic routing based on severity score thresholds.
    
    AI cannot override these thresholds.
    """
    if severity_score <= 3:
        return "OTC_RECOMMENDATION"
    elif severity_score <= 6:
        return "PHARMACIST_CONSULT"
    elif severity_score <= 8:
        return "DOCTOR_REFERRAL"
    else:
        return "EMERGENCY_ALERT"


def _get_default_assessment() -> Dict:
    """
    Return default assessment if AI fails.
    
    Defaults to moderate severity for safety.
    """
    return {
        "severity_score": 5,
        "risk_level": "moderate",
        "red_flags_detected": [],
        "recommended_action": "pharmacist",
        "confidence": 0.5,
        "reasoning": "Default assessment due to AI error"
    }


def get_urgency_display(severity_score: int, risk_level: str) -> Dict:
    """
    Get UI display information for urgency indicator.
    
    Returns badge color, text, and icon.
    """
    if severity_score <= 3:
        return {
            "badge_color": "green",
            "badge_text": "Low Risk",
            "icon": "✓",
            "description": "Mild symptoms - OTC medication recommended"
        }
    elif severity_score <= 6:
        return {
            "badge_color": "orange",
            "badge_text": "Moderate",
            "icon": "⚠",
            "description": "Moderate symptoms - Pharmacist consultation recommended"
        }
    elif severity_score <= 8:
        return {
            "badge_color": "red",
            "badge_text": "High Risk",
            "icon": "⚠⚠",
            "description": "Serious symptoms - Doctor consultation required"
        }
    else:
        return {
            "badge_color": "red-flashing",
            "badge_text": "EMERGENCY",
            "icon": "🚨",
            "description": "Critical symptoms - Seek emergency care immediately"
        }


def format_severity_report(assessment: Dict) -> str:
    """
    Format severity assessment as human-readable report.
    """
    urgency = get_urgency_display(assessment["severity_score"], assessment["risk_level"])
    
    report = f"""
SEVERITY ASSESSMENT
{'='*60}

Severity Score: {assessment['severity_score']}/10
Risk Level: {assessment['risk_level'].upper()}
Urgency: {urgency['badge_text']} {urgency['icon']}
Recommended Action: {assessment['recommended_action'].upper()}
Confidence: {assessment['confidence']:.0%}

"""
    
    if assessment.get("red_flags_detected"):
        report += "⚠️  Red Flags Detected:\n"
        for flag in assessment["red_flags_detected"]:
            report += f"  • {flag}\n"
        report += "\n"
    
    if assessment.get("emergency_override"):
        report += "🚨 EMERGENCY OVERRIDE ACTIVATED\n\n"
    
    report += f"Route: {assessment['route']}\n"
    report += f"Routing Logic: {assessment.get('routing_logic', 'deterministic')}\n"
    
    if assessment.get("reasoning"):
        report += f"\nReasoning: {assessment['reasoning']}\n"
    
    report += f"\n{urgency['description']}\n"
    report += f"{'='*60}"
    
    return report
