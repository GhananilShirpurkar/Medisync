"""
PRESCRIPTION API ROUTES
=======================
Endpoints for prescription image upload and processing.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, status, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging

from ..agents.vision_agent import VisionAgent
from ..services.orchestration_service import OrchestrationService
from ..services.conversation_service import ConversationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/prescription", tags=["prescription"])

# Initialize services
vision_agent = VisionAgent()
orchestration_service = OrchestrationService()
conversation_service = ConversationService()


# ------------------------------------------------------------------
# REQUEST/RESPONSE MODELS
# ------------------------------------------------------------------

class PrescriptionUploadResponse(BaseModel):
    """Response from prescription upload."""
    session_id: str
    extraction_status: str  # "success" | "failed" | "partial"
    patient_info: Optional[Dict[str, Any]] = None
    medicines: List[Dict[str, Any]] = []
    validation_results: Optional[Dict[str, Any]] = None
    inventory_check: Optional[Dict[str, Any]] = None
    message: str


# ------------------------------------------------------------------
# ENDPOINTS
# ------------------------------------------------------------------

@router.post("/upload", response_model=PrescriptionUploadResponse)
async def upload_prescription(
    session_id: str = Query(..., description="Session identifier"),
    image: UploadFile = File(..., description="Prescription image (JPEG, PNG)")
):
    """
    Upload and process prescription image.
    
    This endpoint:
    1. Receives prescription image
    2. Extracts data using Vision Agent
    3. Validates medicines using Medical Agent
    4. Checks inventory using Inventory Agent
    5. Returns consolidated results
    
    Args:
        session_id: Session identifier
        image: Prescription image file
        
    Returns:
        Consolidated processing results
    """
    try:
        # Validate session
        session = conversation_service.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Read image bytes
        image_bytes = await image.read()
        
        logger.info(f"Processing prescription for session {session_id}, size: {len(image_bytes)} bytes")
        
        # Process through orchestration service
        result = await orchestration_service.process_prescription(
            image_bytes=image_bytes,
            session_id=session_id
        )
        
        # Determine status
        extraction_status = "success" if result["extraction"]["success"] else "failed"
        
        # Base medicines from extraction
        extracted_data = result["extraction"].get("data", {}) if result["extraction"]["success"] else {}
        extracted_medicines = extracted_data.get("medicines", [])
        
        # PERSIST VISION CONTEXT TO SESSION
        # This ensures name, age, etc. extracted from prescription are remembered
        if extracted_data:
            pc_to_save = {
                "age": extracted_data.get("patient_age"),
                "allergies": extracted_data.get("allergies", []),
                "existing_conditions": extracted_data.get("conditions", []),
                "patient_name": extracted_data.get("patient_name")
            }
            conversation_service.update_session(session_id, patient_context=pc_to_save)
            if extracted_data.get("patient_name"):
                conversation_service.update_session(session_id, user_id=extracted_data.get("patient_name"))

        # Enrich medicines with inventory data for the frontend
        inventory_items = {
            item["medicine"].lower(): item 
            for item in result.get("inventory", {}).get("items", [])
        }
        
        enriched_medicines = []
        for med in extracted_medicines:
            name = med.get("name", "").lower()
            inv = inventory_items.get(name, {})
            
            enriched_med = {
                **med,
                "available": inv.get("available", False),
                "price": inv.get("price", 0),
                "substitute": inv.get("substitute")
            }
            enriched_medicines.append(enriched_med)
            
        # Build final response object
        response_data = {
            "session_id": session_id,
            "extraction_status": extraction_status,
            "patient_info": result["extraction"].get("data", {}) if result["extraction"]["success"] else None,
            "medicines": enriched_medicines,
            "validation_results": result.get("validation"),
            "inventory_check": result.get("inventory"),
            "message": _generate_response_message(result)
        }
        
        # Add to conversation history
        conversation_service.add_message(
            session_id=session_id,
            role="assistant",
            content=response_data["message"],
            agent_name="vision",
            extra_data={
                "prescription_data": result["extraction"].get("data"),
                "validation": result.get("validation"),
                "inventory": result.get("inventory")
            }
        )
        
        return PrescriptionUploadResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prescription upload error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process prescription: {str(e)}"
        )


# ------------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------------

def _generate_response_message(result: Dict[str, Any]) -> str:
    """Generate user-friendly response message."""
    
    if not result["extraction"]["success"]:
        return "❌ I couldn't read the prescription clearly. Please try again with better lighting."
    
    data = result["extraction"]["data"]
    medicines = data.get("medicines", [])
    
    if not medicines:
        return "⚠️ I couldn't find any medicines in the prescription. Please check the image."
    
    # Build message
    message_parts = ["✅ Prescription processed successfully!\n"]
    
    # Patient info
    if data.get("patient_name"):
        message_parts.append(f"Patient: {data['patient_name']}")
    if data.get("doctor_name"):
        message_parts.append(f"Doctor: {data['doctor_name']}")
    
    # Medicines
    message_parts.append(f"\n📋 Found {len(medicines)} medicine(s):")
    for i, med in enumerate(medicines, 1):
        med_line = f"{i}. {med['name']}"
        if med.get('dosage'):
            med_line += f" - {med['dosage']}"
        if med.get('frequency'):
            med_line += f" ({med['frequency']})"
        message_parts.append(med_line)
    
    # Inventory check
    inventory = result.get("inventory", {})
    if inventory.get("available"):
        message_parts.append(f"\n✓ All medicines are in stock!")
    elif inventory.get("partial"):
        message_parts.append(f"\n⚠️ Some medicines are out of stock. Alternatives suggested.")
    
    # Validation warnings
    validation = result.get("validation", {})
    if validation.get("warnings"):
        message_parts.append(f"\n⚠️ {len(validation['warnings'])} warning(s) - please review.")
    
    return "\n".join(message_parts)
