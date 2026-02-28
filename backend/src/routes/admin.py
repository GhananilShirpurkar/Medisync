from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import List, Dict, Optional
from pydantic import BaseModel

import src.db_config
from src.db_config import get_db_context
from src.models import Order, Medicine, Patient, OrderItem, RefillPrediction
from src.database import Database

router = APIRouter(tags=["admin"])

# --- Schemas ---

class StatCard(BaseModel):
    label: str
    value: int

class AdminDashboardStats(BaseModel):
    stats: List[StatCard]
    recent_activity: List[Dict]

class OrderActionRequest(BaseModel):
    status: str  # approved, rejected

# --- Endpoints ---

@router.get("/stats")
def get_admin_stats():
    with src.db_config.get_db_context() as db:
        # 1. Total Orders
        total_orders = db.query(Order).count()
        
        # 2. Pending Orders
        pending_orders = db.query(Order).filter(Order.status == "pending").count()
        
        # 3. Low Stock Items
        low_stock_items = db.query(Medicine).filter(Medicine.stock < 10).count()
        
        # 4. Patients Today
        today = date.today()
        patients_today = db.query(Patient).filter(
            Patient.last_visit >= datetime.combine(today, datetime.min.time())
        ).count()
        
        # 5. Recent Activity (Latest 5 orders)
        recent_orders = db.query(Order).order_by(Order.created_at.desc()).limit(5).all()
        activity = []
        for order in recent_orders:
            patient = db.query(Patient).filter(Patient.user_id == order.user_id).first()
            # Get first medicine name for display
            first_item = db.query(OrderItem).filter(OrderItem.order_id == order.id).first()
            med_name = first_item.medicine_name if first_item else "Unknown"
            
            activity.append({
                "id": order.order_id,
                "patient": patient.name if patient else order.user_id,
                "medicine": med_name,
                "status": order.status.upper(),
                "time": order.created_at.strftime("%I:%M %p")
            })
            
        return {
            "stats": [
                {"label": "TOTAL ORDERS", "value": total_orders},
                {"label": "PENDING ORDERS", "value": pending_orders},
                {"label": "LOW STOCK ITEMS", "value": low_stock_items},
                {"label": "PATIENTS TODAY", "value": patients_today}
            ],
            "recent_activity": activity
        }

@router.get("/inventory")
def get_admin_inventory():
    with src.db_config.get_db_context() as db:
        medicines = db.query(Medicine).all()
        return [
            {
                "id": m.id,
                "name": m.name,
                "category": m.category,
                "stock": m.stock,
                "price": f"${m.price:.2f}",
                "status": "ACTIVE" if m.stock > 0 else "OUT OF STOCK"
            }
            for m in medicines
        ]

@router.get("/customers")
def get_admin_customers():
    with src.db_config.get_db_context() as db:
        patients = db.query(Patient).all()
        result = []
        for p in patients:
            # Mask phone for privacy in UI
            phone = p.phone if p.phone else "N/A"
            masked_phone = f"{phone[:6]}***{phone[-4:]}" if len(phone) > 10 else phone
            
            result.append({
                "id": p.user_id,
                "phone": masked_phone,
                "registered": p.created_at.strftime("%b %d, %Y") if p.created_at else "N/A",
                "orders": p.total_orders or 0,
                "lastVisit": p.last_visit.strftime("%b %d, %Y") if p.last_visit else "N/A"
            })
        return result

@router.get("/orders")
def get_admin_orders():
    with src.db_config.get_db_context() as db:
        orders = db.query(Order).order_by(Order.created_at.desc()).all()
        result = []
        for o in orders:
            items = db.query(OrderItem).filter(OrderItem.order_id == o.id).all()
            meds_summary = ", ".join([f"{i.medicine_name} ({i.quantity}x)" for i in items])
            
            result.append({
                "id": o.order_id,
                "patient": o.user_id,
                "medicines": meds_summary,
                "total": f"${o.total_amount:.2f}",
                "status": o.status.upper(),
                "date": o.created_at.strftime("%b %d, %Y") if o.created_at else "N/A"
            })
        return result

@router.get("/pending")
def get_admin_pending():
    with src.db_config.get_db_context() as db:
        orders = db.query(Order).filter(Order.status == "pending").order_by(Order.created_at.asc()).all()
        result = []
        now = datetime.utcnow()
        for o in orders:
            items = db.query(OrderItem).filter(OrderItem.order_id == o.id).all()
            meds_summary = ", ".join([f"{i.medicine_name} ({i.quantity}x)" for i in items])
            
            # Calculate waiting time
            wait_time = "N/A"
            if o.created_at:
                diff = now - o.created_at
                days = diff.days
                hours, remainder = divmod(diff.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                if days > 0:
                    wait_time = f"{days}d {hours}h"
                elif hours > 0:
                    wait_time = f"{hours}h {minutes}m"
                else:
                    wait_time = f"{minutes}m"
            
            result.append({
                "id": o.order_id,
                "patient": o.user_id,
                "waiting": wait_time,
                "medicines": meds_summary
            })
        return result

@router.post("/orders/{order_id}/action")
def order_action(order_id: str, req: OrderActionRequest):
    with src.db_config.get_db_context() as db:
        order = db.query(Order).filter(Order.order_id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if req.status == "approved":
            order.status = "fulfilled"
        elif req.status == "rejected":
            order.status = "cancelled"
        else:
            raise HTTPException(status_code=400, detail="Invalid status")
            
        db.commit()
        return {"status": "success", "new_status": order.status}


# ------------------------------------------------------------------
# REFILL ALERTS
# ------------------------------------------------------------------

@router.get("/refill-alerts")
def get_refill_alerts():
    """Return all unsent refill predictions sorted by urgency."""
    with get_db_context() as db:
        predictions = db.query(RefillPrediction).filter(
            RefillPrediction.reminder_sent == False
        ).order_by(RefillPrediction.predicted_depletion_date.asc()).all()

        now = datetime.now()
        alerts = []
        for p in predictions:
            if not p.predicted_depletion_date:
                continue
            days_left = (p.predicted_depletion_date - now).days
            if days_left <= 3:
                urgency = "urgent"
            elif days_left <= 7:
                urgency = "soon"
            else:
                urgency = "normal"
            alerts.append({
                "user_id": p.user_id,
                "medicine_name": p.medicine_name,
                "predicted_depletion_date": p.predicted_depletion_date.isoformat(),
                "days_until_depletion": days_left,
                "confidence": p.confidence,
                "urgency": urgency,
                "reminder_sent": p.reminder_sent,
                "refill_confirmed": getattr(p, 'refill_confirmed', False),
            })

        return {
            "alerts": alerts,
            "total": len(alerts),
            "urgent_count": sum(1 for a in alerts if a["urgency"] == "urgent")
        }


class SendRefillAlertRequest(BaseModel):
    user_id: str
    medicine_name: str


@router.post("/send-refill-alert")
async def send_refill_alert(req: SendRefillAlertRequest):
    """Manually trigger a WhatsApp refill reminder for a specific patient/medicine."""
    from src.agents.proactive_intelligence_agent import ProactiveIntelligenceAgent
    try:
        agent = ProactiveIntelligenceAgent()
        predictions = agent.generate_refill_predictions(req.user_id)
        target = next((p for p in predictions if p["medicine_name"].lower() == req.medicine_name.lower()), None)

        if not target:
            # Build a minimal prediction so we can still send the WhatsApp
            target = {
                "medicine_name": req.medicine_name,
                "days_until_depletion": 0,
                "urgency": "urgent",
                "should_notify": True,
                "confidence": 0.5,
                "predicted_depletion_date": datetime.now().isoformat()
            }

        await agent.trigger_refill_conversation(req.user_id, target)
        return {"status": "sent", "user_id": req.user_id, "medicine_name": req.medicine_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
