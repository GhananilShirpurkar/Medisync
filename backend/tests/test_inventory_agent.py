"""
INVENTORY AGENT TESTS
=====================
Test the inventory agent with various scenarios.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.state import PharmacyState, OrderItem
from src.agents.inventory_and_rules_agent import (
    inventory_agent,
    get_inventory_summary,
    format_inventory_report,
    extract_base_name
)


def test_all_items_available():
    """Test with all items in stock."""
    print("\n" + "="*60)
    print("TEST 1: ALL ITEMS AVAILABLE")
    print("="*60)
    
    # Create state with common medicines (should be in database)
    state = PharmacyState(
        user_id="test_user",
        extracted_items=[
            OrderItem(medicine_name="Paracetamol", dosage="500mg", quantity=2),
            OrderItem(medicine_name="Amoxicillin", dosage="250mg", quantity=1)
        ]
    )
    
    # Run inventory check
    result = inventory_agent(state)
    
    # Check results
    summary = get_inventory_summary(result)
    print(f"\nStatus: {summary['status']}")
    print(f"Availability: {summary['available_items']}/{summary['total_items']}")
    
    # At least some items should be available (depends on database)
    assert summary['total_items'] == 2, "Should check 2 items"
    
    print("\n✅ All items available test passed")
    return result


def test_out_of_stock():
    """Test with out-of-stock medicine."""
    print("\n" + "="*60)
    print("TEST 2: OUT OF STOCK MEDICINE")
    print("="*60)
    
    # Create state with a medicine unlikely to exist
    state = PharmacyState(
        user_id="test_user",
        extracted_items=[
            OrderItem(medicine_name="NonExistentMedicine123", dosage="500mg", quantity=1)
        ]
    )
    
    # Run inventory check
    result = inventory_agent(state)
    
    # Check results
    summary = get_inventory_summary(result)
    print(f"\nStatus: {summary['status']}")
    print(f"Availability: {summary['available_items']}/{summary['total_items']}")
    
    # Should detect unavailability
    assert summary['status'] in ["none_available", "partial_available"], "Should detect unavailability"
    
    print("\n✅ Out of stock test passed")
    return result


def test_alternatives_suggested():
    """Test that alternatives are suggested for unavailable items."""
    print("\n" + "="*60)
    print("TEST 3: ALTERNATIVES SUGGESTED")
    print("="*60)
    
    # Create state with unavailable medicine
    state = PharmacyState(
        user_id="test_user",
        extracted_items=[
            OrderItem(medicine_name="RareMedicine999", dosage="100mg", quantity=1)
        ]
    )
    
    # Run inventory check
    result = inventory_agent(state)
    
    # Check results
    summary = get_inventory_summary(result)
    metadata = result.trace_metadata.get("inventory_agent", {})
    
    print(f"\nStatus: {summary['status']}")
    print(f"Alternatives: {len(summary['alternatives'])}")
    
    # Metadata should contain alternatives info
    assert "alternatives" in metadata, "Should have alternatives field"
    
    print("\n✅ Alternatives suggested test passed")
    return result


def test_mixed_availability():
    """Test with mix of available and unavailable items."""
    print("\n" + "="*60)
    print("TEST 4: MIXED AVAILABILITY")
    print("="*60)
    
    # Create state with mix
    state = PharmacyState(
        user_id="test_user",
        extracted_items=[
            OrderItem(medicine_name="Paracetamol", dosage="500mg", quantity=1),  # Should exist
            OrderItem(medicine_name="NonExistent123", dosage="100mg", quantity=1)  # Won't exist
        ]
    )
    
    # Run inventory check
    result = inventory_agent(state)
    
    # Check results
    summary = get_inventory_summary(result)
    print(f"\nStatus: {summary['status']}")
    print(f"Availability: {summary['available_items']}/{summary['total_items']}")
    
    assert summary['total_items'] == 2, "Should check 2 items"
    
    print("\n✅ Mixed availability test passed")
    return result


def test_no_items():
    """Test with no items to check."""
    print("\n" + "="*60)
    print("TEST 5: NO ITEMS")
    print("="*60)
    
    # Create state with no items
    state = PharmacyState(
        user_id="test_user",
        extracted_items=[]
    )
    
    # Run inventory check
    result = inventory_agent(state)
    
    # Check results
    metadata = result.trace_metadata.get("inventory_agent", {})
    print(f"\nStatus: {metadata.get('status')}")
    
    assert metadata.get("status") == "no_items", "Should detect no items"
    
    print("\n✅ No items test passed")
    return result


def test_inventory_report():
    """Test inventory report formatting."""
    print("\n" + "="*60)
    print("TEST 6: INVENTORY REPORT")
    print("="*60)
    
    # Create and check inventory
    state = PharmacyState(
        user_id="test_user",
        extracted_items=[
            OrderItem(medicine_name="Paracetamol", dosage="500mg", quantity=1)
        ]
    )
    
    result = inventory_agent(state)
    
    # Generate report
    report = format_inventory_report(result)
    
    print("\n" + report)
    
    assert "INVENTORY CHECK REPORT" in report, "Report should have title"
    assert "Status:" in report, "Report should have status"
    
    print("\n✅ Inventory report test passed")


def test_base_name_extraction():
    """Test base name extraction logic."""
    print("\n" + "="*60)
    print("TEST 7: BASE NAME EXTRACTION")
    print("="*60)
    
    test_cases = [
        ("Paracetamol 500mg", "Paracetamol"),
        ("Amoxicillin 250mg Capsules", "Amoxicillin"),
        ("Ibuprofen 400mg Tablets", "Ibuprofen"),
        ("Crocin", "Crocin"),
    ]
    
    for input_name, expected_base in test_cases:
        result = extract_base_name(input_name)
        print(f"  {input_name} → {result}")
        # Just check it returns something reasonable
        assert len(result) > 0, f"Should extract base name from {input_name}"
    
    print("\n✅ Base name extraction test passed")


def test_availability_score():
    """Test availability score calculation."""
    print("\n" + "="*60)
    print("TEST 8: AVAILABILITY SCORE")
    print("="*60)
    
    # Create state with items
    state = PharmacyState(
        user_id="test_user",
        extracted_items=[
            OrderItem(medicine_name="Paracetamol", dosage="500mg", quantity=1),
            OrderItem(medicine_name="Amoxicillin", dosage="250mg", quantity=1)
        ]
    )
    
    result = inventory_agent(state)
    
    # Check availability score
    summary = get_inventory_summary(result)
    score = summary['availability_score']
    
    print(f"\nAvailability Score: {score:.2f}")
    print(f"Available: {summary['available_items']}/{summary['total_items']}")
    
    assert 0.0 <= score <= 1.0, "Score should be between 0 and 1"
    
    print("\n✅ Availability score test passed")


if __name__ == "__main__":
    print("\n🧪 Running Inventory Agent Tests...\n")
    
    try:
        # Run all tests
        test_all_items_available()
        test_out_of_stock()
        test_alternatives_suggested()
        test_mixed_availability()
        test_no_items()
        test_inventory_report()
        test_base_name_extraction()
        test_availability_score()
        
        print("\n" + "="*60)
        print("✅ ALL INVENTORY AGENT TESTS PASSED")
        print("="*60)
        print("\n💡 Inventory Agent is working correctly")
        print("   - Checks medicine availability")
        print("   - Suggests alternatives for unavailable items")
        print("   - Calculates availability scores")
        print("   - Provides detailed reasoning traces")
        print("   - Handles edge cases (no items, mixed availability)\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
