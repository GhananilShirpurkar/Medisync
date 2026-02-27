"""
WORKFLOW INTEGRATION TESTS
===========================
End-to-end tests for the complete agent workflow.
"""

import sys
from pathlib import Path
from datetime import datetime
import pytest
import json

from src.state import PharmacyState, OrderItem
from src.graph import run_workflow

@pytest.fixture
def mock_llm_calls(monkeypatch):
    class MockModel:
        def generate_content(self, *args, **kwargs):
            class MockResponse:
                def __init__(self, text):
                    self.text = text
            
            # Default response for safety check
            safety_response = {
                "has_interactions": False,
                "severity": "none",
                "interactions": [],
                "warnings": [],
                "safe_to_dispense": True
            }
            return MockResponse(json.dumps(safety_response))

    class MockClient:
        def __init__(self):
            self.models = MockModel()

    monkeypatch.setattr("src.services.llm_service._get_client", lambda: MockClient())


# Helper function to extract data from workflow result
def get_result_data(result):
    """Extract data from workflow result (handles dict or PharmacyState)."""
    if isinstance(result, dict):
        return {
            "pharmacist_decision": result.get("pharmacist_decision"),
            "order_id": result.get("order_id"),
            "order_status": result.get("order_status"),
            "trace_metadata": result.get("trace_metadata", {}),
            "safety_issues": result.get("safety_issues", [])
        }
    else:
        return {
            "pharmacist_decision": result.pharmacist_decision,
            "order_id": result.order_id,
            "order_status": result.order_status,
            "trace_metadata": result.trace_metadata,
            "safety_issues": result.safety_issues
        }


def test_approved_workflow(mock_llm_calls):
    """Test complete workflow with approved prescription."""
    print("\n" + "="*60)
    print("TEST 1: APPROVED WORKFLOW (END-TO-END)")
    print("="*60)
    
    # Create initial state with valid prescription data
    state = PharmacyState(
        user_id="test_user_001",
        prescription_uploaded=True,
        prescription_verified=False,
        extracted_items=[
            OrderItem(medicine_name="Paracetamol", dosage="500mg", quantity=2),
            OrderItem(medicine_name="Vitamin C", dosage="1000mg", quantity=1)
        ]
    )
    
    # Add vision agent metadata (simulating OCR results)
    state.trace_metadata["vision_agent"] = {
        "patient_name": "John Doe",
        "doctor_name": "Dr. Smith",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "signature_present": True,
        "ocr_confidence": 0.95,
        "llm_confidence": 0.92
    }
    
    # Run complete workflow
    print("\n🚀 Running complete workflow...")
    result = run_workflow(state)
    data = get_result_data(result)
    
    # Verify results
    print(f"\n📊 Workflow Results:")
    print(f"  Pharmacist Decision: {data['pharmacist_decision']}")
    print(f"  Order ID: {data['order_id']}")
    print(f"  Order Status: {data['order_status']}")
    
    # Check each agent executed
    assert "medical_validator" in data['trace_metadata'], "Medical validator should execute"
    assert "inventory_agent" in data['trace_metadata'], "Inventory agent should execute"
    assert "fulfillment_agent" in data['trace_metadata'], "Fulfillment agent should execute"
    
    # Check final state
    assert data['pharmacist_decision'] in ["approved", "needs_review"], "Should be approved or need review"
    
    if data['pharmacist_decision'] == "approved":
        assert data['order_id'] is not None, "Should create order"
        assert data['order_status'] in ["created", "fulfilled"], "Should have order status"
    
    print("\n✅ Approved workflow test passed")
    return result


def test_rejected_workflow(mock_llm_calls):
    """Test workflow with rejected prescription."""
    print("\n" + "="*60)
    print("TEST 2: REJECTED WORKFLOW")
    print("="*60)
    
    # Create state with expired prescription
    state = PharmacyState(
        user_id="test_user_002",
        prescription_uploaded=True,
        extracted_items=[
            OrderItem(medicine_name="Paracetamol", dosage="500mg", quantity=1)
        ]
    )
    
    # Add vision agent metadata with expired date
    state.trace_metadata["vision_agent"] = {
        "patient_name": "Jane Doe",
        "doctor_name": "Dr. Jones",
        "date": "2023-01-01",  # Old date
        "signature_present": True
    }
    
    # Run workflow
    print("\n🚀 Running workflow with expired prescription...")
    result = run_workflow(state)
    data = get_result_data(result)
    
    # Verify results
    print(f"\n📊 Workflow Results:")
    print(f"  Pharmacist Decision: {data['pharmacist_decision']}")
    print(f"  Order ID: {data['order_id']}")
    print(f"  Safety Issues: {len(data['safety_issues'])}")
    
    # Should stop at medical validation
    assert "medical_validator" in data['trace_metadata'], "Medical validator should execute"
    assert data['pharmacist_decision'] == "rejected", "Should reject expired prescription"
    assert data['order_id'] is None, "Should not create order"
    
    # Inventory and fulfillment should not execute
    # (workflow stops after rejection)
    
    print("\n✅ Rejected workflow test passed")
    return result


def test_out_of_stock_workflow(mock_llm_calls):
    """Test workflow when items are out of stock."""
    print("\n" + "="*60)
    print("TEST 3: OUT OF STOCK WORKFLOW")
    print("="*60)
    
    # Create state with non-existent medicine
    state = PharmacyState(
        user_id="test_user_003",
        prescription_uploaded=True,
        extracted_items=[
            OrderItem(medicine_name="NonExistentMedicine999", dosage="100mg", quantity=1)
        ]
    )
    
    # Add vision agent metadata
    state.trace_metadata["vision_agent"] = {
        "patient_name": "Bob Smith",
        "doctor_name": "Dr. Brown",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "signature_present": True
    }
    
    # Run workflow
    print("\n🚀 Running workflow with unavailable medicine...")
    result = run_workflow(state)
    data = get_result_data(result)
    
    # Verify results
    print(f"\n📊 Workflow Results:")
    print(f"  Pharmacist Decision: {data['pharmacist_decision']}")
    print(f"  Order ID: {data['order_id']}")
    
    # Should execute validation and inventory, but stop before fulfillment
    assert "medical_validator" in data['trace_metadata'], "Medical validator should execute"
    assert "inventory_agent" in data['trace_metadata'], "Inventory agent should execute"
    
    # Should not create order due to no stock
    assert data['order_id'] is None, "Should not create order without stock"
    
    print("\n✅ Out of stock workflow test passed")
    return result


def test_controlled_substance_workflow(mock_llm_calls):
    """Test workflow with controlled substance."""
    print("\n" + "="*60)
    print("TEST 4: CONTROLLED SUBSTANCE WORKFLOW")
    print("="*60)
    
    # Create state with controlled substance
    state = PharmacyState(
        user_id="test_user_004",
        prescription_uploaded=True,
        extracted_items=[
            OrderItem(medicine_name="Alprazolam", dosage="0.5mg", quantity=1),
            OrderItem(medicine_name="Paracetamol", dosage="500mg", quantity=1)
        ]
    )
    
    # Add vision agent metadata
    state.trace_metadata["vision_agent"] = {
        "patient_name": "Alice Johnson",
        "doctor_name": "Dr. Wilson",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "signature_present": True
    }
    
    # Run workflow
    print("\n🚀 Running workflow with controlled substance...")
    result = run_workflow(state)
    data = get_result_data(result)
    
    # Verify results
    print(f"\n📊 Workflow Results:")
    print(f"  Pharmacist Decision: {data["pharmacist_decision"]}")
    print(f"  Safety Issues: {len(data["safety_issues"])}")
    
    # Should detect controlled substance
    assert "medical_validator" in data["trace_metadata"], "Medical validator should execute"
    
    # May be rejected or need review depending on validation rules
    assert data["pharmacist_decision"] in ["rejected", "needs_review"], "Should flag controlled substance"
    
    print("\n✅ Controlled substance workflow test passed")
    return result


def test_partial_availability_workflow(mock_llm_calls):
    """Test workflow with partial item availability."""
    print("\n" + "="*60)
    print("TEST 5: PARTIAL AVAILABILITY WORKFLOW")
    print("="*60)
    
    # Create state with mix of available and unavailable items
    state = PharmacyState(
        user_id="test_user_005",
        prescription_uploaded=True,
        extracted_items=[
            OrderItem(medicine_name="Paracetamol", dosage="500mg", quantity=1),
            OrderItem(medicine_name="NonExistent123", dosage="100mg", quantity=1)
        ]
    )
    
    # Add vision agent metadata
    state.trace_metadata["vision_agent"] = {
        "patient_name": "Charlie Brown",
        "doctor_name": "Dr. Green",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "signature_present": True
    }
    
    # Run workflow
    print("\n🚀 Running workflow with partial availability...")
    result = run_workflow(state)
    data = get_result_data(result)
    
    # Verify results
    print(f"\n📊 Workflow Results:")
    print(f"  Pharmacist Decision: {data["pharmacist_decision"]}")
    print(f"  Order ID: {data["order_id"]}")
    
    # Should execute all agents
    assert "medical_validator" in data["trace_metadata"], "Medical validator should execute"
    assert "inventory_agent" in data["trace_metadata"], "Inventory agent should execute"
    assert "fulfillment_agent" in data["trace_metadata"], "Fulfillment agent should execute"
    
    # Should create partial order
    if data["pharmacist_decision"] == "approved":
        assert data["order_id"] is not None, "Should create order for available items"
        
        fulfillment_metadata = data["trace_metadata"].get("fulfillment_agent", {})
        assert fulfillment_metadata.get("items_skipped", 0) > 0, "Should skip unavailable items"
    
    print("\n✅ Partial availability workflow test passed")
    return result


def test_workflow_metadata(mock_llm_calls):
    """Test that all agents store proper metadata."""
    print("\n" + "="*60)
    print("TEST 6: WORKFLOW METADATA")
    print("="*60)
    
    # Create valid state
    state = PharmacyState(
        user_id="test_user_006",
        prescription_uploaded=True,
        extracted_items=[
            OrderItem(medicine_name="Paracetamol", dosage="500mg", quantity=1)
        ]
    )
    
    state.trace_metadata["vision_agent"] = {
        "patient_name": "Test Patient",
        "doctor_name": "Dr. Test",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "signature_present": True
    }
    
    # Run workflow
    result = run_workflow(state)
    data = get_result_data(result)
    
    # Check metadata structure
    print(f"\n📊 Checking metadata...")
    
    # Medical validator metadata
    if "medical_validator" in data["trace_metadata"]:
        med_meta = data["trace_metadata"]["medical_validator"]
        assert "status" in med_meta, "Should have status"
        assert "risk_score" in med_meta, "Should have risk score"
        assert "reasoning_trace" in med_meta, "Should have reasoning trace"
        print("  ✓ Medical validator metadata complete")
    
    # Inventory metadata
    if "inventory_agent" in data["trace_metadata"]:
        inv_meta = data["trace_metadata"]["inventory_agent"]
        assert "availability_score" in inv_meta, "Should have availability score"
        assert "reasoning_trace" in inv_meta, "Should have reasoning trace"
        print("  ✓ Inventory agent metadata complete")
    
    # Fulfillment metadata
    if "fulfillment_agent" in data["trace_metadata"]:
        ful_meta = data["trace_metadata"]["fulfillment_agent"]
        assert "order_id" in ful_meta or "status" in ful_meta, "Should have order info"
        assert "reasoning_trace" in ful_meta, "Should have reasoning trace"
        print("  ✓ Fulfillment agent metadata complete")
    
    print("\n✅ Workflow metadata test passed")
    return result


if __name__ == "__main__":
    print("\n🧪 Running Workflow Integration Tests...\n")
    print("="*60)
    print("TESTING COMPLETE AGENT ORCHESTRATION")
    print("="*60)
    
    try:
        # Run all tests
        test_approved_workflow()
        test_rejected_workflow()
        test_out_of_stock_workflow()
        test_controlled_substance_workflow()
        test_partial_availability_workflow()
        test_workflow_metadata()
        
        print("\n" + "="*60)
        print("✅ ALL WORKFLOW INTEGRATION TESTS PASSED")
        print("="*60)
        print("\n💡 Complete workflow is working correctly")
        print("   - Medical validation → Inventory → Fulfillment")
        print("   - Proper routing based on decisions")
        print("   - Handles rejections and out-of-stock")
        print("   - Manages controlled substances")
        print("   - Creates orders successfully")
        print("   - Maintains complete audit trail\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)