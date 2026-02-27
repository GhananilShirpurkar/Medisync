"""
FULFILLMENT AGENT TESTS
=======================
Test the fulfillment agent with various scenarios.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.state import PharmacyState, OrderItem
from src.agents.fulfillment_agent import (
    fulfillment_agent,
    get_fulfillment_summary,
    format_fulfillment_report,
    format_order_confirmation
)
from src.database import Database


def test_successful_fulfillment(test_db):
    """Test successful order fulfillment."""
    print("\n" + "="*60)
    print("TEST 1: SUCCESSFUL FULFILLMENT")
    print("="*60)
    
    # Create state with approved prescription and available items
    state = PharmacyState(
        user_id="test_user_001",
        pharmacist_decision="approved",
        prescription_verified=True,
        extracted_items=[
            OrderItem(medicine_name="Paracetamol", dosage="500mg", quantity=2, in_stock=True),
            OrderItem(medicine_name="Vitamin C", dosage="1000mg", quantity=1, in_stock=True)
        ]
    )
    
    # Add inventory metadata
    state.trace_metadata["inventory_agent"] = {
        "availability_score": 1.0,
        "available_items": 2,
        "total_items": 2
    }
    
    # Run fulfillment
    result = fulfillment_agent(state)
    
    # Check results
    summary = get_fulfillment_summary(result)
    print(f"\nStatus: {summary['status']}")
    print(f"Order ID: {summary['order_id']}")
    print(f"Total: ₹{summary['total_amount']:.2f}")
    
    assert result.order_id is not None, "Should create order ID"
    assert result.order_status in ["created", "fulfilled"], "Should have valid status"
    assert summary['items_fulfilled'] == 2, "Should fulfill 2 items"
    
    print("\n✅ Successful fulfillment test passed")
    return result


def test_rejected_order():
    """Test order rejected by pharmacist."""
    print("\n" + "="*60)
    print("TEST 2: REJECTED ORDER")
    print("="*60)
    
    # Create state with rejected prescription
    state = PharmacyState(
        user_id="test_user_002",
        pharmacist_decision="rejected",
        prescription_verified=False,
        safety_issues=["Expired prescription"],
        extracted_items=[
            OrderItem(medicine_name="Paracetamol", dosage="500mg", quantity=1, in_stock=True)
        ]
    )
    
    # Run fulfillment
    result = fulfillment_agent(state)
    
    # Check results
    metadata = result.trace_metadata.get("fulfillment_agent", {})
    print(f"\nStatus: {metadata.get('status')}")
    print(f"Order Status: {result.order_status}")
    
    assert result.order_status == "rejected", "Should reject order"
    assert result.order_id is None, "Should not create order"
    
    print("\n✅ Rejected order test passed")
    return result


def test_no_inventory():
    """Test when no items are available."""
    print("\n" + "="*60)
    print("TEST 3: NO INVENTORY")
    print("="*60)
    
    # Create state with approved but no stock
    state = PharmacyState(
        user_id="test_user_003",
        pharmacist_decision="approved",
        extracted_items=[
            OrderItem(medicine_name="Paracetamol", dosage="500mg", quantity=1, in_stock=False)
        ]
    )
    
    # Add inventory metadata showing no availability
    state.trace_metadata["inventory_agent"] = {
        "availability_score": 0.0,
        "available_items": 0,
        "total_items": 1
    }
    
    # Run fulfillment
    result = fulfillment_agent(state)
    
    # Check results
    metadata = result.trace_metadata.get("fulfillment_agent", {})
    print(f"\nStatus: {metadata.get('status')}")
    print(f"Order Status: {result.order_status}")
    
    assert result.order_status == "failed", "Should fail due to no inventory"
    assert result.order_id is None, "Should not create order"
    
    print("\n✅ No inventory test passed")
    return result


def test_partial_fulfillment(test_db):
    """Test partial fulfillment (some items unavailable)."""
    print("\n" + "="*60)
    print("TEST 4: PARTIAL FULFILLMENT")
    print("="*60)
    
    # Create state with mixed availability
    state = PharmacyState(
        user_id="test_user_004",
        pharmacist_decision="approved",
        extracted_items=[
            OrderItem(medicine_name="Paracetamol", dosage="500mg", quantity=1, in_stock=True),
            OrderItem(medicine_name="NonExistent", dosage="100mg", quantity=1, in_stock=False)
        ]
    )
    
    # Add inventory metadata
    state.trace_metadata["inventory_agent"] = {
        "availability_score": 0.5,
        "available_items": 1,
        "total_items": 2
    }
    
    # Run fulfillment
    result = fulfillment_agent(state)
    
    # Check results
    summary = get_fulfillment_summary(result)
    print(f"\nStatus: {summary['status']}")
    print(f"Items Fulfilled: {summary['items_fulfilled']}")
    print(f"Items Skipped: {summary['items_skipped']}")
    
    assert summary['items_fulfilled'] == 1, "Should fulfill 1 item"
    assert summary['items_skipped'] == 1, "Should skip 1 item"
    
    print("\n✅ Partial fulfillment test passed")
    return result


def test_pending_review(test_db):
    """Test order pending pharmacist review."""
    print("\n" + "="*60)
    print("TEST 5: PENDING REVIEW")
    print("="*60)
    
    # Create state with needs_review decision
    state = PharmacyState(
        user_id="test_user_005",
        pharmacist_decision="needs_review",
        safety_issues=["Controlled substance detected"],
        extracted_items=[
            OrderItem(medicine_name="Paracetamol", dosage="500mg", quantity=1, in_stock=True)
        ]
    )
    
    # Add inventory metadata
    state.trace_metadata["inventory_agent"] = {
        "availability_score": 1.0,
        "available_items": 1,
        "total_items": 1
    }
    
    # Run fulfillment
    result = fulfillment_agent(state)
    
    # Check results
    summary = get_fulfillment_summary(result)
    print(f"\nStatus: {summary['status']}")
    print(f"Order Status: {result.order_status}")
    
    assert result.order_id is not None, "Should create order"
    assert result.order_status == "pending_review", "Should be pending review"
    
    print("\n✅ Pending review test passed")
    return result


def test_no_items():
    """Test with no items to fulfill."""
    print("\n" + "="*60)
    print("TEST 6: NO ITEMS")
    print("="*60)
    
    # Create state with no items
    state = PharmacyState(
        user_id="test_user_006",
        pharmacist_decision="approved",
        extracted_items=[]
    )
    
    # Run fulfillment
    result = fulfillment_agent(state)
    
    # Check results
    metadata = result.trace_metadata.get("fulfillment_agent", {})
    print(f"\nStatus: {metadata.get('status')}")
    
    assert metadata.get("status") == "no_items", "Should detect no items"
    assert result.order_status == "failed", "Should fail"
    
    print("\n✅ No items test passed")
    return result


def test_fulfillment_report():
    """Test fulfillment report formatting."""
    print("\n" + "="*60)
    print("TEST 7: FULFILLMENT REPORT")
    print("="*60)
    
    # Create and fulfill an order
    state = PharmacyState(
        user_id="test_user_007",
        pharmacist_decision="approved",
        extracted_items=[
            OrderItem(medicine_name="Paracetamol", dosage="500mg", quantity=1, in_stock=True)
        ]
    )
    
    state.trace_metadata["inventory_agent"] = {
        "availability_score": 1.0,
        "available_items": 1,
        "total_items": 1
    }
    
    result = fulfillment_agent(state)
    
    # Generate report
    report = format_fulfillment_report(result)
    
    print("\n" + report)
    
    assert "FULFILLMENT REPORT" in report, "Report should have title"
    assert "Order ID:" in report, "Report should have order ID"
    
    print("\n✅ Fulfillment report test passed")


def test_order_confirmation(test_db):
    """Test order confirmation message."""
    print("\n" + "="*60)
    print("TEST 8: ORDER CONFIRMATION")
    print("="*60)
    
    # Create and fulfill an order
    state = PharmacyState(
        user_id="test_user_008",
        pharmacist_decision="approved",
        extracted_items=[
            OrderItem(medicine_name="Paracetamol", dosage="500mg", quantity=2, in_stock=True)
        ]
    )
    
    state.trace_metadata["inventory_agent"] = {
        "availability_score": 1.0,
        "available_items": 1,
        "total_items": 1
    }
    
    result = fulfillment_agent(state)
    
    # Generate confirmation
    confirmation = format_order_confirmation(result)
    
    print("\n" + confirmation)
    
    assert "Order Confirmed" in confirmation, "Should have confirmation message"
    assert "Order ID:" in confirmation, "Should have order ID"
    
    print("\n✅ Order confirmation test passed")


def test_stock_decrement(test_db):
    """Test that stock is actually decremented."""
    print("\n" + "="*60)
    print("TEST 9: STOCK DECREMENT")
    print("="*60)
    
    db = test_db
    
    # Get initial stock
    medicine = db.get_medicine("Paracetamol")
    if not medicine:
        print("⚠️  Paracetamol not in database, skipping test")
        return
    
    initial_stock = medicine["stock"]
    print(f"\nInitial stock: {initial_stock}")
    
    # Create and fulfill order
    state = PharmacyState(
        user_id="test_user_009",
        pharmacist_decision="approved",
        extracted_items=[
            OrderItem(medicine_name="Paracetamol", dosage="500mg", quantity=2, in_stock=True)
        ]
    )
    
    state.trace_metadata["inventory_agent"] = {
        "availability_score": 1.0,
        "available_items": 1,
        "total_items": 1
    }
    
    result = fulfillment_agent(state)
    
    # Check stock after
    medicine_after = db.get_medicine("Paracetamol")
    final_stock = medicine_after["stock"]
    print(f"Final stock: {final_stock}")
    print(f"Decremented: {initial_stock - final_stock}")
    
    assert final_stock == initial_stock - 2, "Stock should be decremented by 2"
    
    print("\n✅ Stock decrement test passed")


if __name__ == "__main__":
    print("\n🧪 Running Fulfillment Agent Tests...\n")
    
    try:
        # Run all tests
        test_successful_fulfillment()
        test_rejected_order()
        test_no_inventory()
        test_partial_fulfillment()
        test_pending_review()
        test_no_items()
        test_fulfillment_report()
        test_order_confirmation()
        test_stock_decrement()
        
        print("\n" + "="*60)
        print("✅ ALL FULFILLMENT AGENT TESTS PASSED")
        print("="*60)
        print("\n💡 Fulfillment Agent is working correctly")
        print("   - Creates orders in database")
        print("   - Decrements inventory stock")
        print("   - Handles rejected orders")
        print("   - Manages partial fulfillment")
        print("   - Generates order confirmations")
        print("   - Provides detailed reasoning traces\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
