"""
PRESCRIPTION SERVICE
====================
Application service for prescription processing.

Pattern: Application Service Layer
- Coordinates between agents and domain logic
- Handles workflow orchestration
- Manages transactions
- Emits domain events
"""

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

from src.state import PharmacyState, OrderItem
from src.graph import agent_graph
from src.database import Database
from src.errors import ValidationError, InfrastructureError
from src.events.event_bus import get_event_bus
from src.events.event_types import PrescriptionValidatedEvent

logger = logging.getLogger(__name__)


class PrescriptionService:
    """
    Service for processing prescriptions through the agent workflow.
    
    Responsibilities:
    - Coordinate prescription validation workflow
    - Manage state transitions
    - Handle errors and emit events
    - Provide workflow status
    """
    
    def __init__(self):
        """Initialize prescription service."""
        self.db = Database()
        self.event_bus = get_event_bus()
    
    def process_prescription(
        self,
        user_id: str,
        extracted_items: List[Dict[str, Any]],
        whatsapp_phone: Optional[str] = None,
        auto_confirm: bool = False
    ) -> Dict[str, Any]:
        """
        Process a prescription through the complete workflow.
        
        Args:
            user_id: User/patient ID
            extracted_items: List of medicine items from prescription
            whatsapp_phone: Optional WhatsApp number for notifications
            auto_confirm: If True, skip confirmation gate and create order immediately
            
        Returns:
            Dictionary with processing results including confirmation_required flag
            
        Raises:
            ValidationError: If prescription validation fails
            InfrastructureError: If system error occurs
        """
        try:
            # Create initial state
            state = self._create_initial_state(
                user_id=user_id,
                extracted_items=extracted_items,
                whatsapp_phone=whatsapp_phone
            )
            
            logger.info(f"Processing prescription for user {user_id} with {len(extracted_items)} items")
            
            # Run through agent workflow (validation + inventory check)
            result_state = agent_graph.invoke(state)
            
            # Check if order should be auto-confirmed or needs user confirmation
            if auto_confirm or not whatsapp_phone:
                # Direct order creation (legacy behavior for non-WhatsApp flows)
                response = self._build_response(result_state)
            else:
                # Require confirmation for WhatsApp users
                response = self._build_response(result_state)
                response['confirmation_required'] = True
                response['message'] = "Please confirm your order by replying YES or NO"
                
                # Store pending state for confirmation
                from src.services.confirmation_store import confirmation_store
                session_id = f"prescription_{user_id}_{datetime.now().timestamp()}"
                token = confirmation_store.create(
                    session_id=session_id,
                    state_dict=result_state.model_dump() if hasattr(result_state, 'model_dump') else dict(result_state),
                    replacement_info=None
                )
                response['session_id'] = session_id
                response['confirmation_token'] = token
            
            logger.info(f"Prescription processed: {response['status']}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing prescription: {e}", exc_info=True)
            raise InfrastructureError(
                message=f"Failed to process prescription: {str(e)}",
                retry_after=30
            )
    
    def validate_prescription(
        self,
        user_id: str,
        extracted_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate prescription without creating an order.
        
        Args:
            user_id: User/patient ID
            extracted_items: List of medicine items
            
        Returns:
            Validation results
        """
        try:
            # Create state for validation only
            state = self._create_initial_state(
                user_id=user_id,
                extracted_items=extracted_items
            )
            
            # Run only medical validation
            from src.agents.medical_validator_agent import medical_validation_agent
            result_state = medical_validation_agent(state)
            
            # Build validation response
            validation_metadata = result_state.trace_metadata.get("medical_validator", {})
            
            return {
                "valid": result_state.pharmacist_decision == "approved",
                "decision": result_state.pharmacist_decision,
                "safety_issues": result_state.safety_issues,
                "risk_score": validation_metadata.get("risk_score", 0.0),
                "reasoning": validation_metadata.get("reasoning_trace", [])
            }
            
        except Exception as e:
            logger.error(f"Error validating prescription: {e}", exc_info=True)
            raise ValidationError(
                message=f"Validation failed: {str(e)}"
            )
    
    def get_prescription_status(self, order_id: str) -> Dict[str, Any]:
        """
        Get status of a prescription/order.
        
        Args:
            order_id: Order ID to check
            
        Returns:
            Order status information
        """
        order = self.db.get_order(order_id)
        
        if not order:
            raise ValidationError(f"Order {order_id} not found")
        
        return {
            "order_id": order["order_id"],
            "status": order["status"],
            "pharmacist_decision": order["pharmacist_decision"],
            "total_amount": order["total_amount"],
            "created_at": order["created_at"],
            "items": order["items"]
        }
    
    def _create_initial_state(
        self,
        user_id: str,
        extracted_items: List[Dict[str, Any]],
        whatsapp_phone: Optional[str] = None
    ) -> PharmacyState:
        """
        Create initial pharmacy state from request.
        
        Args:
            user_id: User ID
            extracted_items: List of medicine items
            whatsapp_phone: Optional WhatsApp number
            
        Returns:
            PharmacyState instance
        """
        # Convert dict items to OrderItem objects
        order_items = []
        for item in extracted_items:
            order_items.append(OrderItem(
                medicine_name=item.get("medicine_name", item.get("name")),
                dosage=item.get("dosage"),
                quantity=item.get("quantity", 1)
            ))
        
        return PharmacyState(
            user_id=user_id,
            whatsapp_phone=whatsapp_phone,
            extracted_items=order_items,
            prescription_uploaded=True
        )
    
    def _build_response(self, state: PharmacyState) -> Dict[str, Any]:
        """
        Build API response from final state.
        
        Args:
            state: Final pharmacy state
            
        Returns:
            Response dictionary
        """
        # Determine overall status
        if state.order_id:
            status = "completed"
        elif state.pharmacist_decision == "rejected":
            status = "rejected"
        elif state.order_status == "failed":
            status = "failed"
        else:
            status = "processing"
        
        # Build response
        response = {
            "status": status,
            "order_id": state.order_id,
            "pharmacist_decision": state.pharmacist_decision,
            "safety_issues": state.safety_issues,
            "order_status": state.order_status
        }
        
        # Add fulfillment details if available
        fulfillment_metadata = state.trace_metadata.get("fulfillment_agent", {})
        if fulfillment_metadata:
            response["fulfillment"] = {
                "total_amount": fulfillment_metadata.get("total_amount", 0.0),
                "items_fulfilled": fulfillment_metadata.get("items_fulfilled", 0),
                "items_skipped": fulfillment_metadata.get("items_skipped", 0),
                "item_details": fulfillment_metadata.get("item_details", [])
            }
        
        # Add inventory details if available
        inventory_metadata = state.trace_metadata.get("inventory_agent", {})
        if inventory_metadata:
            response["inventory"] = {
                "availability_score": inventory_metadata.get("availability_score", 0.0),
                "alternatives": inventory_metadata.get("alternatives", [])
            }
        
        return response
