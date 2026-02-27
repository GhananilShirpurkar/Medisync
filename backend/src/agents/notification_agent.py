"""
NOTIFICATION AGENT
==================
Agent 6: Notifications and audit logging

Responsibilities:
1. Send order confirmations via Telegram
2. Send prescription status updates
3. Log all notifications for audit
4. Handle notification failures gracefully
5. Provide notification summary
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from pathlib import Path

from src.state import PharmacyState
from src.services.whatsapp_service import (
    send_order_notification,
    send_prescription_status,
    mock_notification
)
from src.database import Database


# ------------------------------------------------------------------
# NOTIFICATION AGENT
# ------------------------------------------------------------------
def notification_agent(state: PharmacyState) -> PharmacyState:
    """
    Notification Agent - Send notifications and log audit trail.
    
    This agent sends notifications to users and maintains an audit log
    of all communications.
    
    Pipeline:
    1. Check if notifications should be sent
    2. Send order confirmation (if order created)
    3. Send prescription status update
    4. Log notifications to file
    5. Update database audit log
    6. Update state with notification status
    
    Args:
        state: Current pharmacy state
        
    Returns:
        Updated state with notification status
        
    Decision Logic:
    - Order created: Send order confirmation
    - Prescription status: Send status update
    - Always: Log to audit trail
    """
    
    # Initialize reasoning trace
    reasoning_trace = []
    notifications_sent = []
    db = Database()
    
    # Step 1: Check if we should send notifications
    if not state.user_id:
        reasoning_trace.append("⚠️  No user ID - Skipping notifications")
        state.trace_metadata["notification_agent"] = {
            "status": "skipped",
            "reason": "no_user_id",
            "reasoning": reasoning_trace
        }
        return state
    
    reasoning_trace.append(f"✓ User ID: {state.user_id}")
    
    # Step 2: Determine phone number (use whatsapp_phone if available, else user_id)
    chat_id = state.whatsapp_phone or state.user_id
    reasoning_trace.append(f"✓ Recipient: {chat_id}")
    
    # Step 3: Send order confirmation if order was created
    if state.order_id:
        reasoning_trace.append(f"\n📦 Sending order confirmation for {state.order_id}")
        
        # Get order details from fulfillment metadata
        fulfillment_metadata = state.trace_metadata.get("fulfillment_agent", {})
        item_details = fulfillment_metadata.get("item_details", [])
        total_amount = fulfillment_metadata.get("total_amount", 0.0)
        
        # Format items for notification
        items = [
            {
                "name": item["medicine"],
                "quantity": item["quantity"]
            }
            for item in item_details
        ]
        
        # Determine order status for notification
        if state.pharmacist_decision == "approved":
            order_status = "confirmed"
        elif state.pharmacist_decision == "needs_review":
            order_status = "pending_review"
        else:
            order_status = "processing"
        
        # Send notification
        try:
            result = send_order_notification(
                chat_id=chat_id,
                order_id=state.order_id,
                items=items,
                total_amount=total_amount,
                status=order_status
            )
            
            if result.get("success"):
                reasoning_trace.append(f"  ✓ Order notification sent")
                notifications_sent.append({
                    "type": "order_confirmation",
                    "order_id": state.order_id,
                    "status": "sent",
                    "method": result.get("method", "whatsapp")
                })
            else:
                reasoning_trace.append(f"  ⚠️  Order notification failed: {result.get('error')}")
                notifications_sent.append({
                    "type": "order_confirmation",
                    "order_id": state.order_id,
                    "status": "failed",
                    "error": result.get("error")
                })
        except Exception as e:
            reasoning_trace.append(f"  ❌ Order notification error: {str(e)}")
            notifications_sent.append({
                "type": "order_confirmation",
                "status": "error",
                "error": str(e)
            })
    
    # Step 4: Send prescription status update
    if state.prescription_uploaded:
        reasoning_trace.append(f"\n💊 Sending prescription status update")
        
        # Determine prescription status
        if state.pharmacist_decision == "approved":
            prescription_status = "verified"
            details = "Your prescription has been approved."
        elif state.pharmacist_decision == "needs_review":
            prescription_status = "needs_review"
            details = "Our pharmacist is reviewing your prescription."
        elif state.pharmacist_decision == "rejected":
            prescription_status = "rejected"
            # Include first safety issue as detail
            details = state.safety_issues[0] if state.safety_issues else "Please contact pharmacy for details."
        else:
            prescription_status = "processing"
            details = "Your prescription is being processed."
        
        # Send notification
        try:
            result = send_prescription_status(
                chat_id=chat_id,
                status=prescription_status,
                details=details
            )
            
            if result.get("success"):
                reasoning_trace.append(f"  ✓ Prescription status sent")
                notifications_sent.append({
                    "type": "prescription_status",
                    "status": "sent",
                    "prescription_status": prescription_status,
                    "method": result.get("method", "whatsapp")
                })
            else:
                reasoning_trace.append(f"  ⚠️  Prescription status failed: {result.get('error')}")
                notifications_sent.append({
                    "type": "prescription_status",
                    "status": "failed",
                    "error": result.get("error")
                })
        except Exception as e:
            reasoning_trace.append(f"  ❌ Prescription status error: {str(e)}")
            notifications_sent.append({
                "type": "prescription_status",
                "status": "error",
                "error": str(e)
            })
    
    # Step 5: Log notifications to file
    log_notifications_to_file(state, notifications_sent)
    reasoning_trace.append(f"\n✓ Notifications logged to file")
    
    # Step 6: Add audit log to database (if order exists)
    if state.order_id:
        try:
            db.add_audit_log(
                order_id=state.order_id,
                agent_name="notification_agent",
                decision="notifications_sent",
                reasoning=f"Sent {len(notifications_sent)} notification(s)",
                extra_data={
                    "notifications": notifications_sent,
                    "chat_id": chat_id
                }
            )
            reasoning_trace.append(f"✓ Audit log created in database")
        except Exception as e:
            reasoning_trace.append(f"⚠️  Audit log failed: {str(e)}")
    
    # Step 7: Update state
    state.notifications_sent = len([n for n in notifications_sent if n.get("status") == "sent"]) > 0
    
    # Step 8: Store metadata for tracing
    state.trace_metadata["notification_agent"] = {
        "status": "completed",
        "notifications_sent": len([n for n in notifications_sent if n.get("status") == "sent"]),
        "notifications_failed": len([n for n in notifications_sent if n.get("status") in ["failed", "error"]]),
        "notifications": notifications_sent,
        "reasoning_trace": reasoning_trace,
        "notification_timestamp": datetime.now().isoformat()
    }
    
    # Step 9: Log notification summary
    print(f"\n{'='*60}")
    print(f"NOTIFICATION AGENT")
    print(f"{'='*60}")
    print(f"User: {state.user_id}")
    print(f"Chat ID: {chat_id}")
    print(f"Notifications Sent: {len([n for n in notifications_sent if n.get('status') == 'sent'])}")
    print(f"Notifications Failed: {len([n for n in notifications_sent if n.get('status') in ['failed', 'error']])}")
    
    if notifications_sent:
        print(f"\nNotifications:")
        for notif in notifications_sent:
            status_icon = "✓" if notif.get("status") == "sent" else "⚠️" if notif.get("status") == "failed" else "❌"
            print(f"  {status_icon} {notif['type']}: {notif.get('status')}")
    
    print(f"\nReasoning Trace:")
    for trace in reasoning_trace:
        print(f"  {trace}")
    
    print(f"{'='*60}\n")
    
    return state


# ------------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------------
def log_notifications_to_file(state: PharmacyState, notifications: List[Dict[str, Any]]):
    """
    Log notifications to a file for audit purposes.
    
    Args:
        state: Pharmacy state
        notifications: List of notification dictionaries
    """
    # Create logs directory if it doesn't exist
    # Use absolute path from current working directory
    import os
    log_dir = Path(os.getcwd()) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create log file path (one file per day)
    log_file = log_dir / f"notifications_{datetime.now().strftime('%Y-%m-%d')}.jsonl"
    
    # Prepare log entry
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user_id": state.user_id,
        "order_id": state.order_id,
        "pharmacist_decision": state.pharmacist_decision,
        "notifications": notifications
    }
    
    # Append to log file (JSONL format - one JSON object per line)
    try:
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"⚠️  Failed to write notification log: {e}")


def get_notification_summary(state: PharmacyState) -> Dict[str, Any]:
    """
    Get a summary of notification results from state.
    
    Args:
        state: Pharmacy state with notification metadata
        
    Returns:
        Dictionary with notification summary
    """
    metadata = state.trace_metadata.get("notification_agent", {})
    
    return {
        "status": metadata.get("status", "unknown"),
        "notifications_sent": metadata.get("notifications_sent", 0),
        "notifications_failed": metadata.get("notifications_failed", 0),
        "notifications": metadata.get("notifications", [])
    }


def format_notification_report(state: PharmacyState) -> str:
    """
    Format notification results as a human-readable report.
    
    Args:
        state: Pharmacy state with notification metadata
        
    Returns:
        Formatted report string
    """
    summary = get_notification_summary(state)
    metadata = state.trace_metadata.get("notification_agent", {})
    
    report = f"""
NOTIFICATION REPORT
{'='*60}

Status: {summary['status'].upper()}
Notifications Sent: {summary['notifications_sent']}
Notifications Failed: {summary['notifications_failed']}

"""
    
    if summary['notifications']:
        report += "Notification Details:\n"
        for notif in summary['notifications']:
            status_icon = "✓" if notif.get("status") == "sent" else "⚠️" if notif.get("status") == "failed" else "❌"
            report += f"  {status_icon} {notif['type']}: {notif.get('status')}\n"
            if notif.get("error"):
                report += f"     Error: {notif['error']}\n"
        report += "\n"
    
    reasoning = metadata.get("reasoning_trace", [])
    if reasoning:
        report += "Reasoning Trace:\n"
        for trace in reasoning:
            report += f"  {trace}\n"
    
    report += f"\n{'='*60}"
    
    return report
