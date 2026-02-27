"""
FRONT DESK AGENT
================
Conversational intake and routing agent.

Responsibilities:
- Intent classification (symptom / known_medicine / refill / prescription_upload / greeting / uncertain)
- Extract patient context (age, allergies, duration, severity)
- Maintain structured conversation logic
- Generate clarification questions using policy rules
- Route to appropriate downstream agent
- Log structured conversation summary

Architecture Pattern:
- Intent as Source of Truth
- Policy-driven clarification
- Stateless but deterministic routing
"""

from typing import Dict, List, Optional
from src.services import llm_service
from src.services.intent_classifier import classify_intent


# ==========================
# CONSTANTS
# ==========================

INTENT_CONFIDENCE_THRESHOLD = 0.6

GREETING_MESSAGE = (
    "Hello! I'm your AI pharmacy assistant. "
    "How can I help you today?\n\n"
    "नमस्ते! मैं आपका AI फार्मेसी सहायक हूँ। "
    "मैं आपकी कैसे मदद कर सकता हूँ?"
)

ASK_SYMPTOMS_MESSAGE = (
    "Could you please describe your symptoms?\n\n"
    "कृपया अपने लक्षण बताएं।"
)

ASK_DURATION_MESSAGE = (
    "How long have you been experiencing these symptoms?\n\n"
    "यह तकलीफ कब से है?"
)

ASK_SEVERITY_MESSAGE = (
    "Would you describe the symptoms as mild, moderate, or severe?\n\n"
    "क्या यह हल्का, मध्यम या गंभीर है?"
)

HINDI_SUPPORT_MESSAGE = (
    "हाँ बिल्कुल! मैं हिंदी में बात कर सकता हूँ। "
    "आप अपनी समस्या बताएं।"
)


# ==========================
# FRONT DESK AGENT
# ==========================

class FrontDeskAgent:
    """
    Front desk agent for conversational intake and routing.

    This is the entry point for all user conversations.
    """

    # --------------------------------------------------
    # INTENT CLASSIFICATION
    # --------------------------------------------------

    def classify_intent(
        self,
        message: str,
        conversation_history: List[Dict] = None
    ) -> Dict:
        """
        Classify user intent using semantic classifier.

        Returns:
            {
                "intent": str,
                "confidence": float,
                "reasoning": str
            }

        Design Principle:
        - Intent is the single source of truth.
        - If confidence is low, mark as 'uncertain'.
        """

        result = classify_intent(message)

        if result.get("confidence", 0) < INTENT_CONFIDENCE_THRESHOLD:
            return {
                "intent": "uncertain",
                "confidence": result.get("confidence", 0),
                "reasoning": "Low confidence classification"
            }

        return result


    # --------------------------------------------------
    # LANGUAGE DETECTION
    # --------------------------------------------------

    def detect_language_preference(self, message: str) -> Optional[str]:
        """
        Detect if user explicitly requests Hindi.
        """
        message_lower = message.lower()

        hindi_keywords = [
            "hindi", "हिंदी", "हिन्दी",
            "hindi me", "hindi mein",
            "english nahi", "nahi aata"
        ]

        if any(keyword in message_lower for keyword in hindi_keywords):
            return "hindi"

        return None


    # --------------------------------------------------
    # CONTEXT EXTRACTION
    # --------------------------------------------------

    def extract_patient_context(
        self,
        message: str,
        conversation_history: List[Dict] = None
    ) -> Dict:
        """
        Extract structured patient context using LLM.

        Returns:
            {
                "age": int or None,
                "allergies": List[str],
                "existing_conditions": List[str],
                "symptom_duration": str or None,
                "symptom_severity": str or None
            }
        """

        context = ""

        if conversation_history:
            for msg in conversation_history[-5:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                context += f"{role}: {content}\n"

        context += f"user: {message}\n"

        prompt = f"""
Extract patient context from this conversation.

Conversation:
{context}

Extract:
- age
- allergies
- existing_conditions
- symptom_duration
- symptom_severity (mild/moderate/severe)

Respond strictly in JSON:
{{
    "age": null or number,
    "allergies": [],
    "existing_conditions": [],
    "symptom_duration": null or string,
    "symptom_severity": null or string
}}
"""

        return llm_service.parse_structured(prompt)


    # --------------------------------------------------
    # CLARIFICATION POLICY
    # --------------------------------------------------

    def generate_clarifying_question(
        self,
        intent: str,
        patient_context: Dict,
        message: str,
        turn_count: int
    ) -> Optional[str]:
        """
        Policy-driven clarification engine.

        Rules:
        - Greeting → greet
        - Uncertain → ask for symptoms
        - Symptom → ensure duration & severity
        - Max 3 clarification turns
        """

        if turn_count >= 4:
            return None

        # Language override
        language = self.detect_language_preference(message)
        if language == "hindi":
            return HINDI_SUPPORT_MESSAGE

        # Greeting intent
        if intent == "greeting":
            return GREETING_MESSAGE

        # Uncertain intent
        if intent == "uncertain":
            return ASK_SYMPTOMS_MESSAGE

        # Symptom clarification policy
        if intent == "symptom":

            if not patient_context.get("symptom_duration"):
                return ASK_DURATION_MESSAGE

            if not patient_context.get("symptom_severity"):
                return ASK_SEVERITY_MESSAGE

        return None


    # --------------------------------------------------
    # ROUTING
    # --------------------------------------------------

    def route_to_agent(self, intent: str) -> str:
        """
        Determine downstream agent based on intent.
        """

        routing_map = {
            "symptom": "medical_validation",
            "known_medicine": "medical_validation",
            "refill": "proactive_intelligence",
            "prescription_upload": "vision",
            "greeting": "none",
            "uncertain": "none"
        }

        return routing_map.get(intent, "medical_validation")


    # --------------------------------------------------
    # SUMMARY
    # --------------------------------------------------

    def create_conversation_summary(
        self,
        intent: str,
        patient_context: Dict,
        messages: List[Dict]
    ) -> Dict:
        """
        Create structured conversation summary.
        """

        turn_count = len([m for m in messages if m.get("role") == "user"])

        return {
            "intent": intent,
            "patient_context": patient_context,
            "turn_count": turn_count,
            "summary": f"User intent: {intent}. Context: {patient_context}",
            "next_agent": self.route_to_agent(intent)
        }