"""
NOTIFICATIONS API ROUTES
========================
API endpoints for testing notification service.

These endpoints allow manual triggering of notifications for testing.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging

from notifications.whatsapp_service import (
    WhatsAppNotificationService,
    send_order_confirmation_sync,
    send_prescription_summary_sync,
    send_bill_pdf_sync,
    send_status_update_sync
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


# ------------------------------------------------------------------
# REQUEST MODELS
# ------------------------------------------------------------------

class OrderItem(BaseModel):
    """Order item model."""
    medicine_name: str
    quantity: int = 1
    price: float


class SendOrderConfirmationRequest(BaseModel):
    """Request to send order confirmation."""
    phone: str = Field(..., description="User's WhatsApp Number")
    order_id: str
    patient_name: str
    items: List[OrderItem]
    total_amount: float
    estimated_pickup_time: str = "30 minutes"


class SendPrescriptionSummaryRequest(BaseModel):
    """Request to send prescription summary."""
    phone: str
    order_id: str
    doctor_name: str
    diagnosis: str
    medicines: List[Dict[str, Any]]


class SendBillRequest(BaseModel):
    """Request to send bill."""
    phone: str
    order_id: str
    patient_name: str
    items: List[OrderItem]
    total_amount: float
    pdf_path: Optional[str] = None


class SendStatusUpdateRequest(BaseModel):
    """Request to send status update."""
    phone: str
    order_id: str
    status: str = Field(..., description="Status: confirmed, packed, out_for_delivery, ready_for_pickup, delivered, cancelled")
    message: Optional[str] = None


# ------------------------------------------------------------------
# ROUTES
# ------------------------------------------------------------------

@router.post("/order-confirmation", status_code=status.HTTP_200_OK)
async def send_order_confirmation(request: SendOrderConfirmationRequest):
    """
    Send order confirmation notification via WhatsApp.
    
    This endpoint is called after order is confirmed.
    """
    try:
        # Convert request to order dict
        order = {
            "order_id": request.order_id,
            "patient_name": request.patient_name,
            "items": [item.dict() for item in request.items],
            "total_amount": request.total_amount,
            "estimated_pickup_time": request.estimated_pickup_time
        }
        
        # Use async service directly (sync wrappers use asyncio.run which fails in FastAPI)
        service = WhatsAppNotificationService()
        message_id = await service.send_order_confirmation(request.phone, order)
        
        if message_id:
            return {
                "success": True,
                "message": "Order confirmation sent",
                "message_id": message_id
            }
        else:
            return {
                "success": False,
                "message": "Failed to send notification (check Twilio config and logs)"
            }
            
    except Exception as e:
        logger.error(f"Error sending order confirmation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send notification: {str(e)}"
        )


@router.post("/prescription-summary", status_code=status.HTTP_200_OK)
async def send_prescription_summary(request: SendPrescriptionSummaryRequest):
    """
    Send prescription summary notification via WhatsApp.
    
    This endpoint is called after prescription is validated.
    """
    try:
        # Convert request to dicts
        order = {"order_id": request.order_id}
        prescription = {
            "doctor_name": request.doctor_name,
            "diagnosis": request.diagnosis,
            "medicines": request.medicines
        }
        
        # Send notification
        message_id = send_prescription_summary_sync(
            request.phone,
            order,
            prescription
        )
        
        if message_id:
            return {
                "success": True,
                "message": "Prescription summary sent",
                "message_id": message_id
            }
        else:
            return {
                "success": False,
                "message": "Failed to send notification (check logs)"
            }
            
    except Exception as e:
        logger.error(f"Error sending prescription summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send notification: {str(e)}"
        )


@router.post("/bill", status_code=status.HTTP_200_OK)
async def send_bill(request: SendBillRequest):
    """
    Send digital bill via WhatsApp.
    
    Sends PDF if available, otherwise sends formatted text bill.
    """
    try:
        # Convert request to order dict
        order = {
            "order_id": request.order_id,
            "patient_name": request.patient_name,
            "items": [item.dict() for item in request.items],
            "total_amount": request.total_amount
        }
        
        # Send notification
        message_id = send_bill_pdf_sync(
            request.phone,
            order,
            request.pdf_path
        )
        
        if message_id:
            return {
                "success": True,
                "message": "Bill sent",
                "message_id": message_id
            }
        else:
            return {
                "success": False,
                "message": "Failed to send notification (check logs)"
            }
            
    except Exception as e:
        logger.error(f"Error sending bill: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send notification: {str(e)}"
        )


@router.post("/status-update", status_code=status.HTTP_200_OK)
async def send_status_update(request: SendStatusUpdateRequest):
    """
    Send order status update via WhatsApp.
    
    Valid statuses:
    - confirmed
    - packed
    - out_for_delivery
    - ready_for_pickup
    - delivered
    - cancelled
    """
    try:
        # Send notification
        message_id = send_status_update_sync(
            request.phone,
            request.order_id,
            request.status,
            request.message
        )
        
        if message_id:
            return {
                "success": True,
                "message": "Status update sent",
                "message_id": message_id
            }
        else:
            return {
                "success": False,
                "message": "Failed to send notification (check logs)"
            }
            
    except Exception as e:
        logger.error(f"Error sending status update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send notification: {str(e)}"
        )


@router.get("/test", status_code=status.HTTP_200_OK)
async def test_notification_service():
    """
    Test if notification service is configured correctly.
    """
    from notifications.whatsapp_service import WhatsAppNotificationService
    
    service = WhatsAppNotificationService()
    
    return {
        "whatsapp_enabled": service.enabled,
        "twilio_configured": service.enabled,
        "message": "Notification service is ready" if service.enabled else "Twilio WhatsApp not configured"
    }
