from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional

from src.services.payment_service import payment_service
from src.services.observability_service import trace_agent

router = APIRouter(tags=["Payment"])

class PaymentInitiateRequest(BaseModel):
    order_id: str
    amount: float
    idempotency_key: Optional[str] = None  # FIX BUG 2: Add idempotency key

class PaymentStatusResponse(BaseModel):
    payment_id: str
    status: str
    transaction_id: str | None = None
    amount: float

@router.post("/initiate", response_model=Dict[str, Any])
async def initiate_payment(req: PaymentInitiateRequest, background_tasks: BackgroundTasks):
    """
    Initiates a mock payment for an order.
    Starts a background task to simulate payment confirmation after 9 seconds.
    
    FIX BUG 2: Supports idempotency_key to prevent duplicate payments.
    """
    result = payment_service.initiate_payment(
        req.order_id, 
        req.amount,
        req.idempotency_key  # Pass idempotency key
    )
    
    # Simulate a 9-second mock confirmation in the background
    background_tasks.add_task(payment_service.mock_confirm_payment, result["payment_id"])
    
    return result

@router.get("/status/{payment_id}", response_model=PaymentStatusResponse)
async def get_payment_status(payment_id: str):
    """
    Polls for payment status.
    """
    result = payment_service.get_payment_status(payment_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@router.post("/mock-confirm/{payment_id}")
async def force_mock_confirm(payment_id: str):
    """
    Allows manual/forced confirmation for dev/demo purposes (bypasses 9s wait).
    """
    await payment_service.mock_confirm_payment(payment_id)
    return {"message": f"Payment {payment_id} successfully confirmed manually"}
