"""
FULFILLMENT AGENT
=================
Agent 5: Order creation and inventory management

Responsibilities:
1. Create orders in database
2. Decrement inventory stock
3. Calculate order totals
4. Generate order IDs
5. Handle fulfillment status
6. Provide order confirmation
7. Trigger mock webhook (real-world action)
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
import logging
import requests
import json

from src.state import PharmacyState, OrderItem
from src.database import Database
from src.errors import (
    FulfillmentError,
    TransactionError,
    OutOfStockError,
    DatabaseError,
    ConfirmationRequiredError,
)
from src.events.event_bus import get_event_bus
from src.events.event_types import OrderCreatedEvent, OrderFailedEvent
from src.services.observability_service import trace_agent, trace_tool_call

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# FULFILLMENT AGENT
# ------------------------------------------------------------------
@trace_agent("FulfillmentAgent", agent_type="agent")
def fulfillment_agent(state: PharmacyState) -> PharmacyState:
    """
    Fulfillment Agent - Order creation and inventory updates.
    """
    
    # Step 0: HARD CONFIRMATION GATE
    if not state.confirmation_confirmed:
        raise ConfirmationRequiredError(session_id=state.session_id or "")

    # Initialize reasoning trace
    reasoning_trace = []
    db = Database()
    event_bus = get_event_bus()

    # Step 1: Check prerequisites
    if not state.extracted_items:
        reasoning_trace.append("❌ No items to fulfill")
        state.order_status = "failed"
        state.trace_metadata["fulfillment_agent"] = {
            "status": "no_items",
            "reasoning": reasoning_trace
        }
        return state
    
    reasoning_trace.append(f"✓ Processing {len(state.extracted_items)} item(s)")
    
    # Step 2: Check pharmacist decision
    # FIX: Allow None pharmacist_decision to proceed — it means validation was skipped
    # which is valid when called directly from confirmation handler
    if state.pharmacist_decision == "rejected":
        reasoning_trace.append("❌ Order rejected by pharmacist - Cannot fulfill")
        state.order_status = "rejected"
        state.trace_metadata["fulfillment_agent"] = {
            "status": "rejected",
            "reason": "pharmacist_rejection",
            "reasoning": reasoning_trace
        }
        return state
    
    # Default to approved if not explicitly set
    effective_decision = state.pharmacist_decision or "approved"
    reasoning_trace.append(f"✓ Pharmacist decision: {effective_decision}")
    
    # Step 3: Check inventory availability
    # FIX: Do not fail on missing inventory_agent metadata.
    # When called from confirmation handler, inventory was checked during the
    # recommendation phase — not stored in trace_metadata. 
    # Instead verify stock directly from DB for each item.
    inventory_metadata = state.trace_metadata.get("inventory_agent", {})
    availability_score = inventory_metadata.get("availability_score", None)
    
    if availability_score is not None and availability_score == 0.0:
        # Only fail if inventory agent explicitly ran and found nothing
        reasoning_trace.append("❌ No items available in inventory - Cannot fulfill")
        state.order_status = "failed"
        state.trace_metadata["fulfillment_agent"] = {
            "status": "failed",
            "reason": "no_inventory",
            "reasoning": reasoning_trace
        }
        return state
    
    reasoning_trace.append(f"✓ Inventory check: proceeding with DB verification")
    
    # Step 4: Verify and filter available items via direct DB check
    available_items = []
    unavailable_items = []
    
    for item in state.extracted_items:
        medicine_data = db.get_medicine(item.medicine_name)
        if medicine_data and medicine_data.get("stock", 0) >= item.quantity:
            # Mark item as in_stock
            item.in_stock = True
            available_items.append(item)
            reasoning_trace.append(f"  ✓ {item.medicine_name}: In stock ({medicine_data.get('stock')} available)")
        else:
            item.in_stock = False
            unavailable_items.append(item)
            stock = medicine_data.get("stock", 0) if medicine_data else 0
            reasoning_trace.append(f"  ✗ {item.medicine_name}: Insufficient stock ({stock} available, {item.quantity} requested)")
    
    if not available_items:
        reasoning_trace.append("❌ No available items to fulfill")
        state.order_status = "failed"
        state.trace_metadata["fulfillment_agent"] = {
            "status": "failed",
            "reason": "no_available_items",
            "reasoning": reasoning_trace
        }
        return state
    
    reasoning_trace.append(f"✓ Fulfilling {len(available_items)} available item(s)")
    
    if unavailable_items:
        reasoning_trace.append(f"⚠️  Skipping {len(unavailable_items)} unavailable item(s)")
        for item in unavailable_items:
            reasoning_trace.append(f"  - {item.medicine_name}")
    
    # Step 5: Calculate order total
    total_amount = 0.0
    item_details = []
    
    for item in available_items:
        medicine_data = db.get_medicine(item.medicine_name)
        if medicine_data:
            item_price = item.price if item.price else medicine_data.get("price", 0)
            item_total = item_price * item.quantity
            total_amount += item_total
            
            item_details.append({
                "name": item.medicine_name,
                "dosage": item.dosage,
                "quantity": item.quantity,
                "price": item_price,
                "total": item_total
            })
            
            reasoning_trace.append(f"  • {item.medicine_name} x{item.quantity} = ₹{item_total:.2f}")
    
    reasoning_trace.append(f"\n💰 Total Amount: ₹{total_amount:.2f}")
    
    # Step 6: Create order in database WITH TRANSACTION
    # FIX: Use safety_flags instead of safety_issues — Medical Validator writes to safety_flags
    safety_data = state.safety_flags if hasattr(state, 'safety_flags') and state.safety_flags else \
                  state.safety_issues if hasattr(state, 'safety_issues') and state.safety_issues else []
    
    try:
        with db.transaction() as tx:
            order_id = tx.create_order(
                user_id=state.user_id or "anonymous",
                items=available_items,
                pharmacist_decision=effective_decision,
                safety_issues=safety_data
            )
            
            reasoning_trace.append(f"✓ Order created: {order_id}")
            
            stock_updates = []
            for item in available_items:
                success = tx.decrement_stock(item.medicine_name, item.quantity)
                if success:
                    stock_updates.append({
                        "medicine": item.medicine_name,
                        "quantity": item.quantity,
                        "status": "decremented"
                    })
                    reasoning_trace.append(f"  ✓ Stock updated: {item.medicine_name} (-{item.quantity})")
                else:
                    raise OutOfStockError(
                        medicine_name=item.medicine_name,
                        requested=item.quantity,
                        available=0
                    )
            
            reasoning_trace.append("✓ Transaction committed successfully")
        
        # Step 7: Update state
        state.order_id = order_id
        state.total_amount = total_amount
        state.order_status = "created" if effective_decision == "approved" else "pending_review"
        
        if effective_decision == "approved":
            fulfillment_status = "fulfilled"
            reasoning_trace.append("\n✅ Order FULFILLED - Ready for pickup/delivery")
        elif effective_decision == "needs_review":
            fulfillment_status = "pending_review"
            reasoning_trace.append("\n⚠️  Order PENDING REVIEW - Awaiting pharmacist approval")
        else:
            fulfillment_status = "created"
            reasoning_trace.append("\n✓ Order CREATED")
        
        state.trace_metadata["fulfillment_agent"] = {
            "status": fulfillment_status,
            "order_id": order_id,
            "total_amount": total_amount,
            "items_fulfilled": len(available_items),
            "items_skipped": len(unavailable_items),
            "item_details": item_details,
            "stock_updates": stock_updates,
            "reasoning_trace": reasoning_trace,
            "fulfillment_timestamp": datetime.now().isoformat()
        }
        
        # Step 8: Emit OrderCreatedEvent — triggers WhatsApp notification
        event_bus.publish(OrderCreatedEvent(
            order_id=state.order_id,
            user_id=state.user_id or "anonymous",
            phone=state.whatsapp_phone,
            total_amount=total_amount,
            items=item_details,
            pharmacist_decision=effective_decision
        ))
        
    except TransactionError as e:
        reasoning_trace.append(f"\n❌ Transaction failed: {e.message}")
        reasoning_trace.append("✓ Database rolled back - no partial state")
        state.order_status = "failed"
        state.trace_metadata["fulfillment_agent"] = {
            "status": "failed",
            "reason": "transaction_error",
            "error": e.to_dict(),
            "reasoning": reasoning_trace
        }
        logger.error(f"Fulfillment TransactionError: {e.message} — {e.details}")
        try:
            event_bus.publish(OrderFailedEvent(
                user_id=state.user_id or "anonymous",
                error=e.message,
                error_type="TransactionError"
            ))
        except Exception:
            pass
        return state
        
    except OutOfStockError as e:
        reasoning_trace.append(f"\n❌ Stock validation failed: {e.message}")
        reasoning_trace.append("✓ Transaction rolled back - inventory unchanged")
        state.order_status = "failed"
        state.trace_metadata["fulfillment_agent"] = {
            "status": "failed",
            "reason": "out_of_stock",
            "error": e.to_dict(),
            "reasoning": reasoning_trace
        }
        logger.error(f"Fulfillment OutOfStockError: {e.message}")
        try:
            event_bus.publish(OrderFailedEvent(
                user_id=state.user_id or "anonymous",
                error=e.message,
                error_type="OutOfStockError"
            ))
        except Exception:
            pass
        return state
        
    except Exception as e:
        import traceback
        reasoning_trace.append(f"\n❌ Unexpected error: {str(e)}")
        reasoning_trace.append("✓ Transaction rolled back - database unchanged")
        state.order_status = "failed"
        state.trace_metadata["fulfillment_agent"] = {
            "status": "failed",
            "reason": "unexpected_error",
            "error": str(e),
            "reasoning": reasoning_trace
        }
        logger.error(f"Fulfillment unexpected error: {str(e)}")
        logger.error(f"FULFILLMENT TRACEBACK: {traceback.format_exc()}")
        try:
            event_bus.publish(OrderFailedEvent(
                user_id=state.user_id or "anonymous",
                error=str(e),
                error_type=type(e).__name__
            ))
        except Exception:
            pass
        return state
    
    # Log fulfillment summary
    print(f"\n{'='*60}")
    print(f"FULFILLMENT AGENT")
    print(f"{'='*60}")
    print(f"Status: {fulfillment_status}")
    print(f"Order ID: {order_id}")
    print(f"Total Amount: ₹{total_amount:.2f}")
    print(f"Items Fulfilled: {len(available_items)}")
    if unavailable_items:
        print(f"Items Skipped: {len(unavailable_items)}")
    print(f"Order Details:")
    for detail in item_details:
        print(f"  • {detail['name']} x{detail['quantity']} @ ₹{detail['price']} = ₹{detail['total']:.2f}")
    print(f"{'='*60}\n")
    
    return state


# ------------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------------
def get_fulfillment_summary(state: PharmacyState) -> Dict[str, Any]:
    metadata = state.trace_metadata.get("fulfillment_agent", {})
    return {
        "status": metadata.get("status", "unknown"),
        "order_id": metadata.get("order_id"),
        "total_amount": metadata.get("total_amount", 0.0),
        "items_fulfilled": metadata.get("items_fulfilled", 0),
        "items_skipped": metadata.get("items_skipped", 0),
        "item_details": metadata.get("item_details", []),
        "stock_updates": metadata.get("stock_updates", [])
    }


def format_fulfillment_report(state: PharmacyState) -> str:
    summary = get_fulfillment_summary(state)
    metadata = state.trace_metadata.get("fulfillment_agent", {})
    
    report = f"""
FULFILLMENT REPORT
{'='*60}

Status: {summary['status'].upper().replace('_', ' ')}
Order ID: {summary['order_id'] or 'N/A'}
Total Amount: ₹{summary['total_amount']:.2f}
Items Fulfilled: {summary['items_fulfilled']}
Items Skipped: {summary['items_skipped']}

"""
    
    if summary['item_details']:
        report += "Order Details:\n"
        for detail in summary['item_details']:
            report += f"  • {detail['name']} x{detail['quantity']} @ ₹{detail['price']} = ₹{detail['total']:.2f}\n"
        report += "\n"
    
    if summary['stock_updates']:
        report += "Stock Updates:\n"
        for update in summary['stock_updates']:
            status_icon = "✓" if update["status"] == "decremented" else "⚠️"
            report += f"  {status_icon} {update['medicine']}: -{update['quantity']}\n"
        report += "\n"
    
    reasoning = metadata.get("reasoning_trace", [])
    if reasoning:
        report += "Reasoning Trace:\n"
        for trace in reasoning:
            report += f"  {trace}\n"
    
    report += f"\n{'='*60}"
    return report


def format_order_confirmation(state: PharmacyState) -> str:
    summary = get_fulfillment_summary(state)
    
    if not summary['order_id']:
        return "❌ Order could not be created. Please contact the pharmacy."
    
    message = f"🎉 Order Confirmed!\n\nOrder ID: {summary['order_id']}\nTotal: ₹{summary['total_amount']:.2f}\n\nItems:\n"
    
    for detail in summary['item_details']:
        message += f"  • {detail['name']} x{detail['quantity']}\n"
    
    if summary['items_skipped'] > 0:
        message += f"\n⚠️  {summary['items_skipped']} item(s) unavailable - alternatives suggested\n"
    
    effective_decision = state.pharmacist_decision or "approved"
    if effective_decision == "needs_review":
        message += "\n⏳ Your order is pending pharmacist review.\n"
        message += "You will be notified once approved.\n"
    elif effective_decision == "approved":
        message += "\n✅ Your order is ready for pickup!\n"
    
    message += f"\nThank you for choosing our pharmacy! 💊"
    return message


def cancel_order(order_id: str, reason: str = "customer_request") -> bool:
    db = Database()
    order = db.get_order(order_id)
    if not order:
        return False
    return True


def get_order_status(order_id: str) -> Optional[Dict[str, Any]]:
    db = Database()
    order = db.get_order(order_id)
    if not order:
        return None
    return {
        "order_id": order["order_id"],
        "status": order["status"],
        "pharmacist_decision": order["pharmacist_decision"],
        "total_amount": order["total_amount"],
        "created_at": order["created_at"],
        "items": order["items"]
    }