from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import List, Dict, Optional
from pydantic import BaseModel

import src.db_config
from src.models import Order, Medicine, Patient, OrderItem
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
