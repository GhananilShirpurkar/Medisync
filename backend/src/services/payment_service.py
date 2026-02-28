import uuid
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from src.database import Database
from src.db_config import get_db_context
from src.models import Payment, Order
from src.utils.qr_generator import generate_upi_qr_data_uri
from src.services.whatsapp_service import whatsapp_service
from src.state import PharmacyState

logger = logging.getLogger(__name__)

class PaymentService:
    def __init__(self):
        self.db = Database()
        # FIX BUG 2: In-memory idempotency cache (60 second TTL)
        self._idempotency_cache = {}  # {idempotency_key: (payment_id, timestamp)}

    def _cleanup_expired_cache(self):
        """Remove expired idempotency keys (older than 60 seconds)."""
        now = datetime.utcnow()
        expired_keys = [
            key for key, (_, timestamp) in self._idempotency_cache.items()
            if (now - timestamp).total_seconds() > 60
        ]
        for key in expired_keys:
            del self._idempotency_cache[key]

    def initiate_payment(self, order_id: str, amount: float, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        """
        FIX BUG 2: Idempotent payment initiation.
        
        If idempotency_key is provided and matches an existing payment within 60 seconds,
        returns the existing payment instead of creating a duplicate.
        """
        # Cleanup expired cache entries
        self._cleanup_expired_cache()
        
        # Check idempotency cache
        if idempotency_key and idempotency_key in self._idempotency_cache:
            cached_payment_id, _ = self._idempotency_cache[idempotency_key]
            logger.info(f"Idempotency hit for key {idempotency_key}, returning existing payment {cached_payment_id}")
            
            # Return existing payment
            with get_db_context() as session:
                existing_payment = session.query(Payment).filter(Payment.id == cached_payment_id).first()
                if existing_payment:
                    return {
                        "payment_id": existing_payment.id,
                        "qr_code_data": existing_payment.qr_code_data,
                        "status": existing_payment.status,
                        "amount": existing_payment.amount,
                        "order_id": existing_payment.order_id,
                        "idempotency_key": idempotency_key
                    }
        
        # Check for existing pending/processing payment for this order (database-level check)
        with get_db_context() as session:
            existing_payment = session.query(Payment).filter(
                Payment.order_id == order_id,
                Payment.status.in_(["pending", "processing"])
            ).first()
            
            if existing_payment:
                logger.info(f"Found existing pending payment {existing_payment.id} for order {order_id}")
                # Cache it if we have an idempotency key
                if idempotency_key:
                    self._idempotency_cache[idempotency_key] = (existing_payment.id, datetime.utcnow())
                
                return {
                    "payment_id": existing_payment.id,
                    "qr_code_data": existing_payment.qr_code_data,
                    "status": existing_payment.status,
                    "amount": existing_payment.amount,
                    "order_id": existing_payment.order_id,
                    "idempotency_key": idempotency_key
                }
        
        # Create new payment
        payment_id = f"pay_{uuid.uuid4().hex[:12]}"
        qr_data = generate_upi_qr_data_uri(amount, order_id)
        
        with get_db_context() as session:
            new_payment = Payment(
                id=payment_id,
                order_id=order_id,
                amount=amount,
                status="pending",
                method="mock_upi_qr",
                qr_code_data=qr_data
            )
            session.add(new_payment)
            session.commit()
        
        # Cache the new payment
        if idempotency_key:
            self._idempotency_cache[idempotency_key] = (payment_id, datetime.utcnow())
            logger.info(f"Cached new payment {payment_id} with idempotency key {idempotency_key}")
            
        return {
            "payment_id": payment_id,
            "qr_code_data": qr_data,
            "status": "pending",
            "amount": amount,
            "order_id": order_id,
            "idempotency_key": idempotency_key
        }

    def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        with get_db_context() as session:
            payment = session.query(Payment).filter(Payment.id == payment_id).first()
            if not payment:
                return {"error": "Payment not found"}
            
            return {
                "payment_id": payment.id,
                "status": payment.status,
                "transaction_id": payment.transaction_id,
                "amount": payment.amount
            }

    async def mock_confirm_payment(self, payment_id: str):
        """
        Simulates a 9-second payment processing delay and then confirms.
        """
        logger.info(f"⏳ Starting 9-second mock confirmation for {payment_id}")
        await asyncio.sleep(9)
        
        txn_id = f"TXN{uuid.uuid4().hex[:12].upper()}"
        
        with get_db_context() as session:
            payment = session.query(Payment).filter(Payment.id == payment_id).first()
            if not payment:
                logger.error(f"Payment {payment_id} not found during mock confirmation")
                return
            
            payment.status = "success"
            payment.transaction_id = txn_id
            payment.paid_at = datetime.utcnow()
            
            # Also update order status
            order = session.query(Order).filter(Order.order_id == payment.order_id).first()
            if order:
                order.status = "fulfilled"
                
            session.commit()
            logger.info(f"✅ Mock Payment SUCCESS for {payment_id} | Txn: {txn_id}")
            
            # TRIGGER WHATSAPP NOTIFICATION
            # In a real flow, this might be handled by an event consumer
            self._send_success_notification(payment.order_id, payment.amount, txn_id)

    def _send_success_notification(self, order_id: str, amount: float, txn_id: str):
        # Fetch order details to send a rich notification
        from src.models import Patient
        with get_db_context() as session:
            order = session.query(Order).filter(Order.order_id == order_id).first()
            if not order:
                return
            
            patient = session.query(Patient).filter(Patient.user_id == order.user_id).first()
            phone = patient.phone if patient else None
            
            if not phone:
                # Fallback to session phone or default for demo
                phone = "9067939108" 
            
            items_list = []
            for item in order.items:
                items_list.append({
                    "name": item.medicine_name,
                    "quantity": item.quantity
                })

            # Format message
            items_text = "\n".join([f"• {i['name']} × {i['quantity']}" for i in items_list])
            message = (
                f"Your MediSync order is confirmed! 💊\n\n"
                f"*Order ID:* `{order_id}`\n"
                f"*Items:*\n{items_text}\n"
                f"*Amount Paid:* ₹{amount:.2f}\n"
                f"*Transaction ID:* `{txn_id}`\n"
                f"*Pharmacy:* MediSync Main\n"
                f"*Estimated pickup:* 15 mins\n\n"
                f"Show this message at counter.\n"
                f"Reply HELP for support."
            )
            
            whatsapp_service.send_message(phone, message)
            logger.info(f"📱 WhatsApp receipt sent for Order {order_id}")

payment_service = PaymentService()
