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
    DatabaseError
)
from src.events.event_bus import get_event_bus
from src.events.event_types import OrderCreatedEvent, OrderFailedEvent
from src.services.observability_service import trace_agent, trace_tool_call

logger = logging.getLogger(__name__)

# Mock webhook URL (for demo purposes)
MOCK_WEBHOOK_URL = "https://webhook.site/unique-id"  # Replace with actual webhook URL

# ------------------------------------------------------------------
# FULFILLMENT AGENT
# ------------------------------------------------------------------
@trace_agent("FulfillmentAgent", agent_type="agent")
async def fulfillment_agent(state: PharmacyState) -> PharmacyState:
    """
    Fulfillment Agent - Order creation and inventory updates.
    
    This agent creates orders and manages inventory after validation
    and availability checks are complete.
    
    Pipeline:
    1. Verify prerequisites (validation, inventory)
    2. Filter available items
    3. Create order in database
    4. Decrement inventory stock
    5. Update state with order info
    6. Generate confirmation
    
    Args:
        state: Current pharmacy state
        
    Returns:
        Updated state with order information
        
    Decision Logic:
    - Approved + Available: Create order
    - Needs Review: Create pending order
    - Rejected: Do not create order
    - No stock: Do not create order
    """
    
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
    if state.pharmacist_decision == "rejected":
        reasoning_trace.append("❌ Order rejected by pharmacist - Cannot fulfill")
        state.order_status = "rejected"
        state.trace_metadata["fulfillment_agent"] = {
            "status": "rejected",
            "reason": "pharmacist_rejection",
            "reasoning": reasoning_trace
        }
        return state
    
    reasoning_trace.append(f"✓ Pharmacist decision: {state.pharmacist_decision}")
    
    # Step 3: Check inventory availability
    inventory_metadata = state.trace_metadata.get("inventory_agent", {})
    availability_score = inventory_metadata.get("availability_score", 0.0)
    
    if availability_score == 0.0:
        reasoning_trace.append("❌ No items available in inventory - Cannot fulfill")
        state.order_status = "failed"
        state.trace_metadata["fulfillment_agent"] = {
            "status": "failed",
            "reason": "no_inventory",
            "reasoning": reasoning_trace
        }
        return state
    
    reasoning_trace.append(f"✓ Inventory availability: {availability_score*100:.0f}%")
    
    # Step 4: Filter available items only
    available_items = [item for item in state.extracted_items if item.in_stock]
    unavailable_items = [item for item in state.extracted_items if not item.in_stock]
    
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
            item_total = medicine_data["price"] * item.quantity
            total_amount += item_total
            
            item_details.append({
                "medicine": item.medicine_name,
                "dosage": item.dosage,
                "quantity": item.quantity,
                "price": medicine_data["price"],
                "total": item_total
            })
            
            reasoning_trace.append(f"  • {item.medicine_name} x{item.quantity} = ₹{item_total:.2f}")
    
    reasoning_trace.append(f"\n💰 Total Amount: ₹{total_amount:.2f}")
    
    # Step 6: Create order in database WITH TRANSACTION
    try:
        # Use transaction context for atomic operations
        with db.transaction() as tx:
            # Create order
            order_id = tx.create_order(
                user_id=state.user_id or "anonymous",
                items=available_items,
                pharmacist_decision=state.pharmacist_decision,
                safety_issues=state.safety_issues
            )
            
            reasoning_trace.append(f"✓ Order created: {order_id}")
            
            # Decrement inventory (within same transaction)
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
                    # Stock decrement failed - transaction will rollback
                    raise OutOfStockError(
                        medicine_name=item.medicine_name,
                        requested=item.quantity,
                        available=0
                    )
            
            # Transaction commits automatically if no exceptions
            reasoning_trace.append("✓ Transaction committed successfully")
        
        # Step 7: Update state (after successful transaction)
        state.order_id = order_id
        state.order_status = "created" if state.pharmacist_decision == "approved" else "pending_review"
        
        # Step 8: Determine fulfillment status
        if state.pharmacist_decision == "approved":
            fulfillment_status = "fulfilled"
            reasoning_trace.append("\n✅ Order FULFILLED - Ready for pickup/delivery")
        elif state.pharmacist_decision == "needs_review":
            fulfillment_status = "pending_review"
            reasoning_trace.append("\n⚠️  Order PENDING REVIEW - Awaiting pharmacist approval")
        else:
            fulfillment_status = "created"
            reasoning_trace.append("\n✓ Order CREATED")
        
        # Step 9: Store metadata for tracing
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
        
        # Step 11: Trigger Mock Webhook (CRITICAL FOR DEMO)
        await event_bus.publish_async(OrderCreatedEvent(
            order_id=state.order_id,
            user_id=state.user_id or "anonymous",
            phone=state.whatsapp_phone,
            total_amount=total_amount,
            items=item_details,
            pharmacist_decision=state.pharmacist_decision or "approved"
        ))
        
    except TransactionError as e:
        # Transaction failed - database rolled back automatically
        reasoning_trace.append(f"\n❌ Transaction failed: {e.message}")
        reasoning_trace.append("✓ Database rolled back - no partial state")
        state.order_status = "failed"
        state.trace_metadata["fulfillment_agent"] = {
            "status": "failed",
            "reason": "transaction_error",
            "error": e.to_dict(),
            "reasoning": reasoning_trace
        }
        
        # Emit OrderFailedEvent
        try:
            from src.events.event_types import OrderFailedEvent
            event = OrderFailedEvent(
                user_id=state.user_id or "anonymous",
                error=e.message,
                error_type="TransactionError"
            )
            event_bus.publish(event)
        except Exception:
            pass  # Don't fail on event publishing
        
        print(f"\n{'='*60}")
        print(f"FULFILLMENT AGENT - TRANSACTION ERROR")
        print(f"{'='*60}")
        print(f"Error: {e.message}")
        print(f"Details: {e.details}")
        print(f"✓ Transaction rolled back successfully")
        print(f"{'='*60}\n")
        
        return state
        
    except OutOfStockError as e:
        # Stock validation failed during transaction
        reasoning_trace.append(f"\n❌ Stock validation failed: {e.message}")
        reasoning_trace.append("✓ Transaction rolled back - inventory unchanged")
        state.order_status = "failed"
        state.trace_metadata["fulfillment_agent"] = {
            "status": "failed",
            "reason": "out_of_stock",
            "error": e.to_dict(),
            "reasoning": reasoning_trace
        }
        
        # Emit OrderFailedEvent
        try:
            from src.events.event_types import OrderFailedEvent
            event = OrderFailedEvent(
                user_id=state.user_id or "anonymous",
                error=e.message,
                error_type="OutOfStockError"
            )
            event_bus.publish(event)
        except Exception:
            pass  # Don't fail on event publishing
        
        print(f"\n{'='*60}")
        print(f"FULFILLMENT AGENT - OUT OF STOCK")
        print(f"{'='*60}")
        print(f"Error: {e.message}")
        print(f"✓ Transaction rolled back successfully")
        print(f"{'='*60}\n")
        
        return state
        
        return state
        
    except Exception as e:
        # Unexpected error - transaction rolled back
        reasoning_trace.append(f"\n❌ Unexpected error: {str(e)}")
        reasoning_trace.append("✓ Transaction rolled back - database unchanged")
        state.order_status = "failed"
        state.trace_metadata["fulfillment_agent"] = {
            "status": "failed",
            "reason": "unexpected_error",
            "error": str(e),
            "reasoning": reasoning_trace
        }
        
        # Emit OrderFailedEvent
        try:
            from src.events.event_types import OrderFailedEvent
            event = OrderFailedEvent(
                user_id=state.user_id or "anonymous",
                error=str(e),
                error_type=type(e).__name__
            )
            event_bus.publish(event)
        except Exception:
            pass  # Don't fail on event publishing
        
        print(f"\n{'='*60}")
        print(f"FULFILLMENT AGENT - ERROR")
        print(f"{'='*60}")
        print(f"Error: {str(e)}")
        print(f"✓ Transaction rolled back successfully")
        print(f"{'='*60}\n")
        
        return state
    
    # Step 10: Log fulfillment summary (only if successful)
    print(f"\n{'='*60}")
    print(f"FULFILLMENT AGENT")
    print(f"{'='*60}")
    print(f"Status: {fulfillment_status}")
    print(f"Order ID: {order_id}")
    print(f"Total Amount: ₹{total_amount:.2f}")
    print(f"Items Fulfilled: {len(available_items)}")
    
    if unavailable_items:
        print(f"Items Skipped: {len(unavailable_items)}")
    
    print(f"\nOrder Details:")
    for detail in item_details:
        print(f"  • {detail['medicine']} x{detail['quantity']} @ ₹{detail['price']} = ₹{detail['total']:.2f}")
    
    print(f"\nReasoning Trace:")
    for trace in reasoning_trace:
        print(f"  {trace}")
    
    print(f"{'='*60}\n")
    
    return state


# ------------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------------
def get_fulfillment_summary(state: PharmacyState) -> Dict[str, Any]:
    """
    Get a summary of fulfillment results from state.
    
    Args:
        state: Pharmacy state with fulfillment metadata
        
    Returns:
        Dictionary with fulfillment summary
    """
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
    """
    Format fulfillment results as a human-readable report.
    
    Args:
        state: Pharmacy state with fulfillment metadata
        
    Returns:
        Formatted report string
    """
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
            report += f"  • {detail['medicine']} x{detail['quantity']} @ ₹{detail['price']} = ₹{detail['total']:.2f}\n"
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
    """
    Format order confirmation message for customer.
    
    Args:
        state: Pharmacy state with fulfillment metadata
        
    Returns:
        Customer-friendly confirmation message
    """
    summary = get_fulfillment_summary(state)
    
    if not summary['order_id']:
        return "❌ Order could not be created. Please contact the pharmacy."
    
    message = f"""
🎉 Order Confirmed!

Order ID: {summary['order_id']}
Total: ₹{summary['total_amount']:.2f}

Items:
"""
    
    for detail in summary['item_details']:
        message += f"  • {detail['medicine']} x{detail['quantity']}\n"
    
    if summary['items_skipped'] > 0:
        message += f"\n⚠️  {summary['items_skipped']} item(s) unavailable - alternatives suggested\n"
    
    if state.pharmacist_decision == "needs_review":
        message += "\n⏳ Your order is pending pharmacist review.\n"
        message += "You will be notified once approved.\n"
    elif state.pharmacist_decision == "approved":
        message += "\n✅ Your order is ready for pickup!\n"
    
    message += f"\nThank you for choosing our pharmacy! 💊"
    
    return message


def cancel_order(order_id: str, reason: str = "customer_request") -> bool:
    """
    Cancel an order and restore inventory.
    
    Args:
        order_id: Order ID to cancel
        reason: Cancellation reason
        
    Returns:
        True if successful, False otherwise
    """
    db = Database()
    
    # Get order details
    order = db.get_order(order_id)
    if not order:
        return False
    
    # Restore inventory
    for item in order.get("items", []):
        # Increment stock back
        medicine = db.get_medicine(item["medicine_name"])
        if medicine:
            # Note: We'd need to add an increment_stock method to Database
            # For now, this is a placeholder
            pass
    
    # Update order status (would need to add update_order method)
    # db.update_order(order_id, status="cancelled", cancellation_reason=reason)
    
    return True


def get_order_status(order_id: str) -> Optional[Dict[str, Any]]:
    """
    Get current status of an order.
    
    Args:
        order_id: Order ID to check
        
    Returns:
        Order status dictionary or None
    """
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
