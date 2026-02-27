"""
ORDER ROUTES
============
API endpoints for order management.
"""

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

from src.services.order_service import OrderService
from src.errors import ValidationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orders", tags=["orders"])


# Response Models
class OrderItem(BaseModel):
    """Order item details."""
    medicine_name: str
    dosage: Optional[str]
    quantity: int
    price: float


class OrderResponse(BaseModel):
    """Order details response."""
    order_id: str
    user_id: str
    status: str
    pharmacist_decision: Optional[str]
    safety_issues: List[str]
    total_amount: float
    created_at: str
    items: List[dict]


class OrderSummaryResponse(BaseModel):
    """Order summary response."""
    order_id: str
    status: str
    total_amount: float
    total_items: int
    total_quantity: int
    created_at: str
    pharmacist_decision: Optional[str]


# Initialize service
order_service = OrderService()


# Routes
@router.get("/{order_id}", response_model=OrderResponse, status_code=status.HTTP_200_OK)
async def get_order(order_id: str):
    """
    Get order details by ID.
    
    Returns complete order information including:
    - Order status
    - Items ordered
    - Total amount
    - Pharmacist decision
    - Safety issues (if any)
    """
    try:
        result = order_service.get_order(order_id)
        return result
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error getting order: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{order_id}/summary", response_model=OrderSummaryResponse, status_code=status.HTTP_200_OK)
async def get_order_summary(order_id: str):
    """
    Get order summary.
    
    Returns a condensed view of order information
    suitable for list displays.
    """
    try:
        result = order_service.get_order_summary(order_id)
        return result
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error getting order summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/user/{user_id}", status_code=status.HTTP_200_OK)
async def get_user_orders(
    user_id: str,
    limit: int = Query(10, ge=1, le=100, description="Maximum number of orders"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """
    Get orders for a specific user.
    
    Supports pagination with limit and offset parameters.
    """
    try:
        result = order_service.get_user_orders(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        return result
        
    except Exception as e:
        logger.error(f"Unexpected error getting user orders: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
