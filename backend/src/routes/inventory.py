"""
INVENTORY ROUTES
================
API endpoints for inventory management.
"""

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

from src.services.inventory_service import InventoryService
from src.errors import ValidationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inventory", tags=["inventory"])


# Request/Response Models
class MedicineResponse(BaseModel):
    """Medicine details response."""
    id: int
    name: str
    category: str
    manufacturer: str
    price: float
    stock: int
    requires_prescription: bool
    description: Optional[str]
    dosage_form: Optional[str]
    strength: Optional[str]
    active_ingredients: Optional[str]
    side_effects: Optional[str]
    indications: Optional[str]
    generic_equivalent: Optional[str]
    contraindications: Optional[str]


class AvailabilityCheckRequest(BaseModel):
    """Request to check availability."""
    items: List[dict] = Field(..., description="List of items to check")


class AvailabilityResponse(BaseModel):
    """Availability check response."""
    availability_score: float
    available_items: int
    total_items: int
    items: List[dict]


# Initialize service
inventory_service = InventoryService()


# Routes
@router.get("/medicine/{name}", response_model=MedicineResponse, status_code=status.HTTP_200_OK)
async def get_medicine(name: str):
    """
    Get medicine details by name.
    
    Returns complete medicine information including:
    - Stock level
    - Price
    - Category
    - Prescription requirement
    """
    try:
        result = inventory_service.get_medicine(name)
        return result
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error getting medicine: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/check-availability", response_model=AvailabilityResponse, status_code=status.HTTP_200_OK)
async def check_availability(request: AvailabilityCheckRequest):
    """
    Check availability for multiple items.
    
    Returns availability status for each item including:
    - Stock levels
    - Availability score
    - Reasons for unavailability
    """
    try:
        result = inventory_service.check_availability(request.items)
        return result
        
    except Exception as e:
        logger.error(f"Unexpected error checking availability: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/search", status_code=status.HTTP_200_OK)
async def search_medicines(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results")
):
    """
    Search medicines by name.
    
    Returns list of medicines matching the search query.
    """
    try:
        results = inventory_service.search_medicines(query=q, limit=limit)
        return {"results": results, "count": len(results)}
        
    except Exception as e:
        logger.error(f"Unexpected error searching medicines: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/low-stock", status_code=status.HTTP_200_OK)
async def get_low_stock_items(
    threshold: int = Query(10, ge=1, description="Stock threshold")
):
    """
    Get medicines with low stock.
    
    Returns list of medicines below the specified stock threshold.
    """
    try:
        results = inventory_service.get_low_stock_items(threshold=threshold)
        return {"items": results, "count": len(results)}
        
    except Exception as e:
        logger.error(f"Unexpected error getting low stock items: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
