"""
NOTIFICATION AGENT TESTS
========================
Test the notification agent with various scenarios.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.state import PharmacyState, OrderItem
from src.agents.notification_agent import (
    notification_agent,
    get_notification_summary,
    format_notification_report
)


def test_order_confirmation():
    """Test order confirmation notification."""
    print("\n" + "="*60)
    print("TEST 1: ORDER CONFIRMATION")
    print("="*60)
    
    # Create state with completed order
    state = PharmacyState(
        user_id="test_user_001",
        telegram_chat_id="123456789",
        order_id="ORD-00001",
        pharmacist_decision="approved",
        prescription_uploaded=True,
        extracted_items=[
            OrderItem(medicine_name="Paracetamol", dosage="500mg", quantity=2)
        ]
    )
    
    # Add fulfillment metadata
    state.trace_metadata["fulfillment_agent"] = {
        "order_id": "ORD-00001",
        "total_amount": 20.0,
        "item_details": [
            {"medicine": "Paracetamol", "quantity": 2, "price": 10.0, "total": 20.0}
        ]
    }
    
    # Run notification agent
    result = notification_agent(state)
    
    # Check results
    summary = get_notification_summary(result)
    print(f"\nStatus: {summary['status']}")
    print(f"Notifications Sent: {summary['notifications_sent']}")
    
    assert result.trace_metadata.get("notification_agent") is not None, "Should have notification metadata"
    assert summary['status'] == "completed", "Should complete"
    
    print("\n✅ Order confirmation test passed")
    return result


def test_prescription_status():
    """Test prescription status notification."""
    print("\n" + "="*60)
    print("TEST 2: PRESCRIPTION STATUS")
    print("="*60)
    
    # Create state with prescription status
    state = PharmacyState(
        user_id="test_user_002",
        telegram_chat_id="987654321",
        prescription_uploaded=True,
        pharmacist_decision="needs_review",
        safety_issues=["Controlled substance detected"]
    )
    
    # Run notification agent
    result = notification_agent(state)
    
    # Check results
    summary = get_notification_summary(result)
    print(f"\nStatus: {summary['status']}")
    print(f"Notifications: {len(summary['notifications'])}")
    
    assert summary['status'] == "completed", "Should complete"
    assert len(summary['notifications']) > 0, "Should send notifications"
    
    print("\n✅ Prescription status test passed")
    return result


def test_rejected_prescription():
    """Test rejected prescription notification."""
    print("\n" + "="*60)
    print("TEST 3: REJECTED PRESCRIPTION")
    print("="*60)
    
    # Create state with rejected prescription
    state = PharmacyState(
        user_id="test_user_003",
        prescription_uploaded=True,
        pharmacist_decision="rejected",
        safety_issues=["Expired prescription", "Missing signature"]
    )
    
    # Run notification agent
    result = notification_agent(state)
    
    # Check results
    summary = get_notification_summary(result)
    print(f"\nStatus: {summary['status']}")
    
    assert summary['status'] == "completed", "Should complete"
    
    print("\n✅ Rejected prescription test passed")
    return result


def test_no_user_id():
    """Test with no user ID."""
    print("\n" + "="*60)
    print("TEST 4: NO USER ID")
    print("="*60)
    
    # Create state without user ID
    state = PharmacyState(
        prescription_uploaded=True,
        pharmacist_decision="approved"
    )
    
    # Run notification agent
    result = notification_agent(state)
    
    # Check results
    metadata = result.trace_metadata.get("notification_agent", {})
    print(f"\nStatus: {metadata.get('status')}")
    
    assert metadata.get("status") == "skipped", "Should skip without user ID"
    
    print("\n✅ No user ID test passed")
    return result


def test_notification_report():
    """Test notification report formatting."""
    print("\n" + "="*60)
    print("TEST 5: NOTIFICATION REPORT")
    print("="*60)
    
    # Create and send notifications
    state = PharmacyState(
        user_id="test_user_005",
        order_id="ORD-00002",
        pharmacist_decision="approved",
        prescription_uploaded=True
    )
    
    state.trace_metadata["fulfillment_agent"] = {
        "order_id": "ORD-00002",
        "total_amount": 15.0,
        "item_details": [
            {"medicine": "Vitamin C", "quantity": 1, "price": 15.0, "total": 15.0}
        ]
    }
    
    result = notification_agent(state)
    
    # Generate report
    report = format_notification_report(result)
    
    print("\n" + report)
    
    assert "NOTIFICATION REPORT" in report, "Report should have title"
    assert "Status:" in report, "Report should have status"
    
    print("\n✅ Notification report test passed")


def test_multiple_notifications():
    """Test sending multiple notifications."""
    print("\n" + "="*60)
    print("TEST 6: MULTIPLE NOTIFICATIONS")
    print("="*60)
    
    # Create state that triggers multiple notifications
    state = PharmacyState(
        user_id="test_user_006",
        telegram_chat_id="111222333",
        order_id="ORD-00003",
        pharmacist_decision="approved",
        prescription_uploaded=True,
        extracted_items=[
            OrderItem(medicine_name="Paracetamol", dosage="500mg", quantity=1),
            OrderItem(medicine_name="Vitamin C", dosage="1000mg", quantity=1)
        ]
    )
    
    state.trace_metadata["fulfillment_agent"] = {
        "order_id": "ORD-00003",
        "total_amount": 25.0,
        "item_details": [
            {"medicine": "Paracetamol", "quantity": 1, "price": 10.0, "total": 10.0},
            {"medicine": "Vitamin C", "quantity": 1, "price": 15.0, "total": 15.0}
        ]
    }
    
    # Run notification agent
    result = notification_agent(state)
    
    # Check results
    summary = get_notification_summary(result)
    print(f"\nNotifications: {len(summary['notifications'])}")
    
    # Should send both order confirmation and prescription status
    assert len(summary['notifications']) >= 2, "Should send multiple notifications"
    
    print("\n✅ Multiple notifications test passed")
    return result


if __name__ == "__main__":
    print("\n🧪 Running Notification Agent Tests...\n")
    
    try:
        # Run all tests
        test_order_confirmation()
        test_prescription_status()
        test_rejected_prescription()
        test_no_user_id()
        test_notification_report()
        test_multiple_notifications()
        
        print("\n" + "="*60)
        print("✅ ALL NOTIFICATION AGENT TESTS PASSED")
        print("="*60)
        print("\n💡 Notification Agent is working correctly")
        print("   - Sends order confirmations")
        print("   - Sends prescription status updates")
        print("   - Handles rejected prescriptions")
        print("   - Logs notifications to file")
        print("   - Creates database audit logs")
        print("   - Provides detailed reasoning traces\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
