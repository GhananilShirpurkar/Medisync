"""
CONVERSATION SERVICE
====================
Manages conversation sessions and messages.

Responsibilities:
- Create and manage conversation sessions
- Store and retrieve messages
- Track conversation state
"""

import uuid
from typing import Dict, List, Optional
from datetime import datetime

from src.db_config import get_db_context
from src.models import ConversationSession, ConversationMessage
from src.state import PharmacyState

class ConversationService:
    """Service for managing conversations."""
    
    def create_session(self, user_id: Optional[str] = None) -> str:
        """
        Create a new conversation session.
        
        Args:
            user_id: Optional user ID
            
        Returns:
            session_id: Unique session identifier
        """
        session_id = f"sess_{uuid.uuid4().hex[:16]}"
        
        with get_db_context() as db:
            session = ConversationSession(
                session_id=session_id,
                user_id=user_id or f"guest_{uuid.uuid4().hex[:8]}",
                status="active",
                turn_count=0
            )
            db.add(session)
            db.commit()
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Get session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session dict or None
        """
        with get_db_context() as db:
            session = db.query(ConversationSession).filter(
                ConversationSession.session_id == session_id
            ).first()
            
            if not session:
                return None
            
            return {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "status": session.status,
                "intent": session.intent,
                "patient_age": session.patient_age,
                "patient_allergies": session.patient_allergies or [],
                "patient_conditions": session.patient_conditions or [],
                "whatsapp_phone": session.whatsapp_phone,
                
                # 🔥 NEW FIELDS
                "conversation_phase": session.conversation_phase,
                "last_medicine_discussed": session.last_medicine_discussed,
                "last_recommendations": session.last_recommendations or [],
                
                "turn_count": session.turn_count,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "updated_at": session.updated_at.isoformat() if session.updated_at else None,
            }
    
    def update_session(
        self,
        session_id: str,
        intent: Optional[str] = None,
        patient_context: Optional[Dict] = None,
        status: Optional[str] = None,
        user_id: Optional[str] = None  # NEW: Allow updating user_id (PID)
    ) -> bool:
        """
        Update session with new information.
        
        Args:
            session_id: Session identifier
            intent: Classified intent
            patient_context: Patient context dict
            status: Session status
            user_id: New user ID (PID)
            
        Returns:
            True if successful
        """
        with get_db_context() as db:
            session = db.query(ConversationSession).filter(
                ConversationSession.session_id == session_id
            ).first()
            
            if not session:
                return False
            
            if intent:
                session.intent = intent
            
            if user_id:
                session.user_id = user_id
            
            if patient_context:
                # Merge age only if non-null
                val_age = patient_context.get("age")
                if val_age:
                    session.patient_age = val_age
                
                # Merge lists instead of overwriting
                val_allergies = patient_context.get("allergies")
                if isinstance(val_allergies, list):
                    current_allergies = set(session.patient_allergies or [])
                    current_allergies.update(val_allergies)
                    session.patient_allergies = list(current_allergies)
                
                val_conditions = patient_context.get("existing_conditions")
                if isinstance(val_conditions, list):
                    current_conditions = set(session.patient_conditions or [])
                    current_conditions.update(val_conditions)
                    session.patient_conditions = list(current_conditions)
                
                # Update phone
                val_phone = patient_context.get("phone") or patient_context.get("whatsapp_phone")
                if val_phone:
                    session.whatsapp_phone = val_phone
                
                # Update symptom details
                val_duration = patient_context.get("symptom_duration")
                if val_duration:
                    session.patient_symptom_duration = val_duration
                
                val_severity = patient_context.get("symptom_severity")
                if val_severity:
                    session.patient_symptom_severity = val_severity
            
            if status:
                session.status = status
            
            session.updated_at = datetime.utcnow()
            db.commit()
            
            return True
    
    def update_phase(self, session_id: str, phase: str) -> bool:
        """
        Update the conversation phase.

        Args:
            session_id: Session identifier
            phase: New conversation phase

        Returns:
            True if successful
        """
        with get_db_context() as db:
            session = db.query(ConversationSession).filter(
                ConversationSession.session_id == session_id
            ).first()

            if not session:
                return False

            session.conversation_phase = phase
            session.updated_at = datetime.utcnow()
            db.commit()

            return True

    def transition_phase(self, session_id: str, new_phase: str) -> bool:
        """
        Transition conversation to a new phase with structured logging.

        Valid phases (state machine):
            collecting_items → replacement_suggested → awaiting_confirmation
            → fulfillment_executing → completed

        Also accepts: cancelled, intake, clarifying, recommending, ordering

        Args:
            session_id: Session identifier.
            new_phase:  Target phase string.

        Returns:
            True if the transition was persisted, False if session not found.
        """
        import logging
        logger = logging.getLogger(__name__)

        result = self.update_phase(session_id, new_phase)
        if result:
            logger.info(
                "Phase transition for session=%s → %s", session_id, new_phase
            )
        return result
    
    def update_last_medicine(self, session_id: str, medicine_name: str) -> bool:
        """
        Update the last medicine discussed.
        
        Args:
            session_id: Session identifier
            medicine_name: Name of the medicine
            
        Returns:
            True if successful
        """
        with get_db_context() as db:
            session = db.query(ConversationSession).filter(
                ConversationSession.session_id == session_id
            ).first()
            
            if not session:
                return False
            
            session.last_medicine_discussed = medicine_name
            session.updated_at = datetime.utcnow()
            db.commit()
            
            return True
    
    def update_recommendations(self, session_id: str, recommendations: List[str]) -> bool:
        """
        Update the last recommendations.
        
        Args:
            session_id: Session identifier
            recommendations: List of recommended medicine names
            
        Returns:
            True if successful
        """
        with get_db_context() as db:
            session = db.query(ConversationSession).filter(
                ConversationSession.session_id == session_id
            ).first()
            
            if not session:
                return False
            
            session.last_recommendations = recommendations
            session.updated_at = datetime.utcnow()
            db.commit()
            
            return True
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        agent_name: Optional[str] = None,
        extra_data: Optional[Dict] = None
    ) -> bool:
        """
        Add message to conversation.
        
        Args:
            session_id: Session identifier
            role: Message role (user, assistant, system)
            content: Message content
            agent_name: Agent that generated message (for assistant messages)
            extra_data: Additional structured data
            
        Returns:
            True if successful
        """
        with get_db_context() as db:
            # Get session
            session = db.query(ConversationSession).filter(
                ConversationSession.session_id == session_id
            ).first()
            
            if not session:
                return False
            
            # Create message
            message = ConversationMessage(
                session_id=session.id,
                role=role,
                content=content,
                agent_name=agent_name,
                extra_data=extra_data or {}
            )
            db.add(message)
            
            # Increment turn count for user messages
            if role == "user":
                session.turn_count += 1
                session.updated_at = datetime.utcnow()
            
            db.commit()
            
            return True
    
    def get_messages(self, session_id: str, limit: Optional[int] = None) -> List[Dict]:
        """
        Get messages for a session.
        
        Args:
            session_id: Session identifier
            limit: Optional limit on number of messages
            
        Returns:
            List of message dicts
        """
        with get_db_context() as db:
            # Get session
            session = db.query(ConversationSession).filter(
                ConversationSession.session_id == session_id
            ).first()
            
            if not session:
                return []
            
            # Get messages
            query = db.query(ConversationMessage).filter(
                ConversationMessage.session_id == session.id
            ).order_by(ConversationMessage.created_at)
            
            if limit:
                query = query.limit(limit)
            
            messages = query.all()
            
            return [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "agent_name": msg.agent_name,
                    "extra_data": msg.extra_data,
                    "created_at": msg.created_at.isoformat() if msg.created_at else None,
                }
                for msg in messages
            ]

    def process_message(self, session_id: str, user_message: str) -> Dict:
        """
        Phase-driven conversation orchestration.
        """
    
        session = self.get_session(session_id)
        if not session:
            return {"response": "Invalid session."}
    
        self.add_message(session_id, "user", user_message)
    
        intent = session.get("intent")
        phase = session.get("conversation_phase", "intake")
    
        # --------------------------------------------------
        # 1️⃣ GREETING
        # --------------------------------------------------
    
        if intent in ["greeting", None, "unknown"]:
            response = "Hello! How can I assist you today?"
            self.add_message(session_id, "assistant", response)
            return {"response": response}
    
        # --------------------------------------------------
        # 2️⃣ INQUIRY (Medicine Info Mode)
        # --------------------------------------------------
    
        if intent == "inquiry":
    
            from src.database import get_medicine
    
            medicine = get_medicine(user_message)
    
            if medicine:
                response = (
                    f"{medicine.name} is used for {medicine.indications}. "
                    f"Price: ₹{medicine.price}. "
                    f"{'In stock' if medicine.stock > 0 else 'Out of stock'}."
                )
    
                # Persist last discussed medicine
                self.update_last_medicine(session_id, medicine.name)
    
            else:
                response = "I couldn't find that medicine. Could you check the spelling?"
    
            self.update_phase(session_id, "intake")
            self.add_message(session_id, "assistant", response)
            return {"response": response}
    
        # --------------------------------------------------
        # 3️⃣ SYMPTOM → RECOMMENDATION MODE
        # --------------------------------------------------
    
        if intent == "symptom":
    
            from src.database import recommend_medicines_for_symptom
    
            recommendations = recommend_medicines_for_symptom(user_message)
    
            if not recommendations:
                response = "Could you describe your symptoms in more detail?"
                self.add_message(session_id, "assistant", response)
                return {"response": response}
    
            names = [m.name for m in recommendations]
    
            response = "Based on your symptoms, I recommend:\n"
            for med in recommendations:
                response += f"- {med.name} (₹{med.price})\n"
    
            # Persist recommendation memory
            self.update_recommendations(session_id, names)
            self.update_last_medicine(session_id, names[0])
            self.update_phase(session_id, "recommending")
    
            self.add_message(session_id, "assistant", response)
            return {"response": response}
    
        # --------------------------------------------------
        # 4️⃣ ORDERING MODE
        # --------------------------------------------------
    
        if phase == "recommending" and user_message.lower().strip() in [
            "order it", "order", "yes", "place order"
        ]:
    
            last_medicine = session.get("last_medicine_discussed")
    
            if not last_medicine:
                response = "Which medicine would you like to order?"
                self.add_message(session_id, "assistant", response)
                return {"response": response}
    
            # Build PharmacyState
            state = PharmacyState(
                user_id=session["user_id"],
                user_message=user_message,
                intent="purchase",
                extracted_items=[
                    {
                        "medicine_name": last_medicine,
                        "quantity": 1
                    }
                ]
            )
            
            # Lazy import to avoid circular dependency
            from src.graph import agent_graph
            result = agent_graph.invoke(state)
    
            response = f"Your order has been {result.order_status}."
    
            self.update_phase(session_id, "completed")
            self.add_message(session_id, "assistant", response)
    
            return {"response": response}
    
        # --------------------------------------------------
        # 5️⃣ DIRECT PURCHASE
        # --------------------------------------------------
    
        if intent == "purchase":
    
            state = PharmacyState(
                user_id=session["user_id"],
                user_message=user_message,
                intent="purchase"
            )
            
            # Lazy import to avoid circular dependency
            from src.graph import agent_graph
            result = agent_graph.invoke(state)
    
            response = f"Order {result.order_status}."
    
            self.update_phase(session_id, "completed")
            self.add_message(session_id, "assistant", response)
    
            return {"response": response}
    
        # --------------------------------------------------
        # 6️⃣ FALLBACK
        # --------------------------------------------------
    
        response = "Could you please clarify your request?"
        self.add_message(session_id, "assistant", response)
    
        return {"response": response}
    
    def get_conversation_history(self, session_id: str) -> Dict:
        """
        Get complete conversation history.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dict with session and messages
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        messages = self.get_messages(session_id)
        
        return {
            "session": session,
            "messages": messages
        }
    
    def close_session(self, session_id: str) -> bool:
        """
        Close a conversation session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful
        """
        return self.update_session(session_id, status="completed")