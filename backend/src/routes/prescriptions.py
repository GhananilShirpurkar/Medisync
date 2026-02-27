"""
PRESCRIPTION ROUTES
===================
API endpoints for prescription processing.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

from src.services.prescription_service import PrescriptionService
from src.errors import ValidationError, InfrastructureError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/prescriptions", tags=["prescriptions"])


# Request/Response Models
class MedicineItem(BaseModel):
    """Medicine item in prescription."""
    medicine_name: str = Field(..., description="Name of the medicine")
    dosage: Optional[str] = Field(None, description="Dosage (e.g., 500mg)")
    quantity: int = Field(1, ge=1, description="Quantity to dispense")


class ProcessPrescriptionRequest(BaseModel):
    """Request to process a prescription."""
    user_id: str = Field(..., description="User/patient ID")
    items: List[MedicineItem] = Field(..., description="List of medicines")
    whatsapp_phone: Optional[str] = Field(None, description="WhatsApp number for notifications")


class ValidatePrescriptionRequest(BaseModel):
    """Request to validate a prescription."""
    user_id: str = Field(..., description="User/patient ID")
    items: List[MedicineItem] = Field(..., description="List of medicines")


class PrescriptionResponse(BaseModel):
    """Response from prescription processing."""
    status: str = Field(..., description="Processing status")
    order_id: Optional[str] = Field(None, description="Order ID if created")
    pharmacist_decision: Optional[str] = Field(None, description="Pharmacist decision")
    safety_issues: List[str] = Field(default_factory=list, description="Safety concerns")
    order_status: Optional[str] = Field(None, description="Order status")
    fulfillment: Optional[dict] = Field(None, description="Fulfillment details")
    inventory: Optional[dict] = Field(None, description="Inventory details")


class ValidationResponse(BaseModel):
    """Response from prescription validation."""
    valid: bool = Field(..., description="Whether prescription is valid")
    decision: str = Field(..., description="Validation decision")
    safety_issues: List[str] = Field(default_factory=list, description="Safety concerns")
    risk_score: float = Field(..., description="Risk score (0-1)")
    reasoning: List[str] = Field(default_factory=list, description="Reasoning trace")


# Initialize service
prescription_service = PrescriptionService()


# Routes
@router.post("/upload", response_model=PrescriptionResponse, status_code=status.HTTP_200_OK)
async def process_prescription(request: ProcessPrescriptionRequest):
    """
    Process a prescription through the complete workflow.
    
    This endpoint:
    1. Validates the prescription
    2. Checks inventory availability
    3. Creates an order if approved
    4. Sends notifications
    
    Returns order details and processing status.
    """
    try:
        # Convert Pydantic models to dicts
        items = [item.dict() for item in request.items]
        
        # Process prescription
        result = prescription_service.process_prescription(
            user_id=request.user_id,
            extracted_items=items,
            whatsapp_phone=request.whatsapp_phone
        )
        
        return result
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except InfrastructureError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error processing prescription: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/validate", response_model=ValidationResponse, status_code=status.HTTP_200_OK)
async def validate_prescription(request: ValidatePrescriptionRequest):
    """
    Validate a prescription without creating an order.
    
    This endpoint only runs medical validation checks
    and returns the validation result.
    
    Useful for:
    - Pre-validation before order creation
    - Checking prescription safety
    - Getting risk assessment
    """
    try:
        # Convert Pydantic models to dicts
        items = [item.dict() for item in request.items]
        
        # Validate prescription
        result = prescription_service.validate_prescription(
            user_id=request.user_id,
            extracted_items=items
        )
        
        return result
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error validating prescription: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{order_id}/status", status_code=status.HTTP_200_OK)
async def get_prescription_status(order_id: str):
    """
    Get the status of a prescription/order.
    
    Returns current order status and details.
    """
    try:
        result = prescription_service.get_prescription_status(order_id)
        return result
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error getting prescription status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
