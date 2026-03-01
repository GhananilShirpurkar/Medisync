"""
FRONT DESK AGENT
================
Conversational intake and routing agent.

Responsibilities:
- Intent classification (symptom / known_medicine / refill / prescription_upload)
- Extract patient context (age, allergies, duration)
- Maintain session memory
- Route to appropriate downstream agent
- Log structured conversation summary
- Multi-language support (Hindi, English, Hinglish, Marathi)
"""

from typing import Dict, List, Optional
from src.services import llm_service
from src.services.intent_classifier import classify_intent
from src.services.language_service import (
    detect_language, 
    get_system_prompt, 
    normalize_medicine_name,
    translate_symptom
)
from src.state import OrderItem

class FrontDeskAgent:
    """
    Front desk agent for conversational intake and routing.
    
    This is the entry point for all user conversations.
    """
    
    def __init__(self):
        """Initialize front desk agent."""
        pass
    
    def classify_intent(self, message: str, conversation_history: List[Dict] = None) -> Dict:
        """
        Classify user intent from message using semantic similarity.
        
        Args:
            message: User message
            conversation_history: Previous messages in conversation
            
        Returns:
            Dict with intent and confidence:
            {
                "intent": "symptom" | "known_medicine" | "refill" | "prescription_upload",
                "confidence": 0.0-1.0,
                "reasoning": "explanation"
            }
        """
        # Use semantic classifier for better accuracy
        result = classify_intent(message)
        
        return result
    
    def extract_patient_context(self, message: str, conversation_history: List[Dict] = None) -> Dict:
        """
        Extract patient context from conversation.
        
        Args:
            message: Current user message
            conversation_history: Previous messages
            
        Returns:
            Dict with patient context:
            {
                "age": int or None,
                "allergies": List[str],
                "existing_conditions": List[str],
                "symptom_duration": str or None,
                "symptom_severity": str or None
            }
        """
        # Build conversation context
        context = ""
        if conversation_history:
            for msg in conversation_history[-20:]:  # Last 20 messages to support elderly/longer conversations
                role = msg.get("role", "user")
                content = msg.get("content", "")
                context += f"{role}: {content}\n"
        
        context += f"user: {message}\n"
        
        prompt = f"""Extract patient context from this conversation.

Conversation:
{context}

Extract the following information (use null if not mentioned):
- age: patient's age (number or null)
- allergies: list of allergies mentioned (empty list if none)
- existing_conditions: list of medical conditions mentioned (empty list if none)
- symptom_duration: how long symptoms have lasted (string or null)
- symptom_severity: severity of symptoms - "mild", "moderate", "severe" (string or null)

Respond in JSON format:
{{
    "age": null or number,
    "allergies": [],
    "existing_conditions": [],
    "symptom_duration": null or string,
    "symptom_severity": null or string
}}"""
        
        response = llm_service.parse_structured(prompt)
        return response
    
    def extract_medicine_items(self, message: str, language: str = "en") -> List[OrderItem]:
        """
        Extract medicine items (name, quantity, dosage) from user message using LLM.

        Uses the structured extraction prompt in llm_service to handle:
        - "I need 2 paracetamol"       → quantity: 2, dosage: null
        - "paracetamol 500mg"           → quantity: 1, dosage: "500mg"
        - "3 strips of ibuprofen 400mg" → quantity: 3, dosage: "400mg"
        
        Supports multi-language input (Hindi, Marathi, Hinglish).

        Returns:
            List of OrderItem with extracted medicine_name, quantity, dosage.
            quantity defaults to 1 if not mentioned.
        """
        extraction = llm_service.call_llm_extract(message)
        items = []
        for raw in extraction.get("items", []):
            if not raw.get("medicine_name"):
                continue
            
            # Normalize medicine name across languages
            normalized_name = normalize_medicine_name(raw["medicine_name"])
            
            items.append(OrderItem(
                medicine_name=normalized_name,
                quantity=int(raw.get("quantity") or 1),
                dosage=raw.get("dosage") or None,
            ))
        return items

    def generate_clarifying_question(
        self,
        intent: str,
        message: str,
        patient_context: Dict,
        turn_count: int,
        language: str = "en",
        conversation_history: List[Dict] = None
    ) -> Optional[str]:
        """
        Generate clarifying question if needed.

        Rules:
        - known_medicine: NEVER ask a clarifying question — go straight to lookup.
        - symptom, turn 0, empty context: ask one clarifying question via LLM.
        - symptom, turn >= 1 OR context present: skip LLM, return None immediately
          so recommendations are shown without delay.
        - All other intents: skip LLM.

        Args:
            intent: Classified intent
            message: User message
            patient_context: Extracted patient context
            turn_count: Number of conversation turns so far
            language: Detected language code (default: "en")
            conversation_history: List of conversation messages

        Returns:
            Clarifying question string or None if no clarification needed
        """
        # ── known_medicine: never ask clarifying questions ────────────────
        if intent == "known_medicine":
            return None

        # ── greeting or generic_help: always ask for details ──────────────
        if intent in ("greeting", "generic_help"):
            return "How can I help you today? Please tell me your symptoms or the medicine you are looking for."

        # ── symptom: allow multi-turn clarification up to a limit ─────────
        if intent == "symptom":
            # Let the LLM intelligently decide when to recommend by generating 'READY_TO_RECOMMEND'
            pass

        # ── All other intents: skip LLM ───────────────────────────────────
        if intent not in ("symptom",):
            return None

        # ── LLM clarification (symptom, turn 0, no context) ──────────────
        context_str = "None yet"
        if patient_context:
            context_str = ", ".join([f"{k}: {v}" for k, v in patient_context.items() if v])

        # Use language-aware system prompt
        formatted_system_prompt = get_system_prompt(language, context_str)

        response_text = llm_service.call_llm_chat(
            formatted_system_prompt, message, history=conversation_history
        )

        if "READY_TO_RECOMMEND" in response_text:
            return None

        return response_text
    
    def route_to_agent(self, intent: str, patient_context: Dict) -> str:
        """
        Determine which agent to route to next.
        
        Args:
            intent: Classified intent
            patient_context: Patient context
            
        Returns:
            Agent name to route to
        """
        routing_map = {
            "symptom": "medical_validation",  # Symptom → MedicalValidation
            "known_medicine": "medical_validation",  # Known medicine → MedicalValidation
            "refill": "proactive_intelligence",  # Refill → ProactiveIntelligence
            "prescription_upload": "vision",  # Prescription → Vision (OCR)
        }
        
        return routing_map.get(intent, "medical_validation")
    
    def create_conversation_summary(
        self,
        intent: str,
        patient_context: Dict,
        messages: List[Dict]
    ) -> Dict:
        """
        Create structured conversation summary.
        
        Args:
            intent: Classified intent
            patient_context: Patient context
            messages: All conversation messages
            
        Returns:
            Structured summary dict
        """
        return {
            "intent": intent,
            "patient_context": patient_context,
            "turn_count": len([m for m in messages if m.get("role") == "user"]),
            "summary": f"User intent: {intent}. Context: {patient_context}",
            "next_agent": self.route_to_agent(intent, patient_context)
        }
