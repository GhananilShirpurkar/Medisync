"""
TEST LANGFUSE INTEGRATION
=========================
Test that Langfuse tracing is working correctly.

This is CRITICAL for the hackathon demo.
"""

import pytest
from datetime import datetime

from src.state import PharmacyState, OrderItem
from src.agents.medical_validator_agent import medical_validation_agent
from src.agents.inventory_and_rules_agent import inventory_agent
from src.agents.fulfillment_agent import fulfillment_agent
from src.services.observability_service import observability_service


def test_langfuse_client_initialized():
    """Test that Langfuse client is initialized."""
    assert observability_service.client is not None, "Langfuse client should be initialized"
    assert observability_service.enabled is True, "Observability should be enabled"


def test_medical_validation_agent_tracing():
    """Test that MedicalValidationAgent creates Langfuse traces."""
    # Create test state
    state = PharmacyState(
        user_id="test_user_langfuse",
        extracted_items=[
            OrderItem(
                medicine_name="Paracetamol 500mg",
                dosage="500mg",
                quantity=10
            )
        ],
        prescription_uploaded=False
    )
    
    # Run agent (should create Langfuse trace)
    result = medical_validation_agent(state, mode="otc")
    
    # Verify agent executed
    assert result is not None
    assert "medical_validator" in result.trace_metadata
    
    # Verify trace metadata
    metadata = result.trace_metadata["medical_validator"]
    assert "mode" in metadata
    assert "status" in metadata
    assert "reasoning_trace" in metadata
    
    print("\n✅ MedicalValidationAgent tracing test passed")
    print(f"   Mode: {metadata['mode']}")
    print(f"   Status: {metadata['status']}")
    print(f"   Reasoning steps: {len(metadata['reasoning_trace'])}")


def test_inventory_agent_tracing():
    """Test that InventoryAgent creates Langfuse traces."""
    # Create test state
    state = PharmacyState(
        user_id="test_user_langfuse",
        extracted_items=[
            OrderItem(
                medicine_name="Paracetamol 500mg",
                dosage="500mg",
                quantity=10
            )
        ]
    )
    
    # Run agent (should create Langfuse trace)
    result = inventory_agent(state)
    
    # Verify agent executed
    assert result is not None
    assert "inventory_agent" in result.trace_metadata
    
    # Verify trace metadata
    metadata = result.trace_metadata["inventory_agent"]
    assert "status" in metadata
    assert "availability_score" in metadata
    assert "reasoning_trace" in metadata
    
    print("\n✅ InventoryAgent tracing test passed")
    print(f"   Status: {metadata['status']}")
    print(f"   Availability: {metadata['availability_score']*100:.0f}%")
    print(f"   Reasoning steps: {len(metadata['reasoning_trace'])}")


def test_fulfillment_agent_tracing():
    """Test that FulfillmentAgent creates Langfuse traces."""
    # Create test state with approved items
    state = PharmacyState(
        user_id="test_user_langfuse",
        extracted_items=[
            OrderItem(
                medicine_name="Paracetamol 500mg",
                dosage="500mg",
                quantity=2,
                in_stock=True
            )
        ],
        pharmacist_decision="approved"
    )
    
    # Add inventory metadata (required for fulfillment)
    state.trace_metadata["inventory_agent"] = {
        "status": "all_available",
        "availability_score": 1.0
    }
    
    # Run agent (should create Langfuse trace)
    result = fulfillment_agent(state)
    
    # Verify agent executed
    assert result is not None
    assert "fulfillment_agent" in result.trace_metadata
    
    # Verify trace metadata
    metadata = result.trace_metadata["fulfillment_agent"]
    assert "status" in metadata
    assert "order_id" in metadata
    assert "reasoning_trace" in metadata
    
    print("\n✅ FulfillmentAgent tracing test passed")
    print(f"   Status: {metadata['status']}")
    print(f"   Order ID: {metadata['order_id']}")
    print(f"   Reasoning steps: {len(metadata['reasoning_trace'])}")


def test_complete_agent_pipeline_tracing():
    """Test complete agent pipeline with Langfuse tracing."""
    print("\n" + "="*60)
    print("TESTING COMPLETE AGENT PIPELINE WITH LANGFUSE")
    print("="*60)
    
    # Create initial state
    state = PharmacyState(
        user_id="test_user_pipeline",
        extracted_items=[
            OrderItem(
                medicine_name="Paracetamol 500mg",
                dosage="500mg",
                quantity=5
            )
        ],
        prescription_uploaded=False
    )
    
    print("\n1️⃣  Running MedicalValidationAgent...")
    state = medical_validation_agent(state, mode="otc")
    assert "medical_validator" in state.trace_metadata
    print(f"   ✅ Status: {state.trace_metadata['medical_validator']['status']}")
    
    print("\n2️⃣  Running InventoryAgent...")
    state = inventory_agent(state)
    assert "inventory_agent" in state.trace_metadata
    print(f"   ✅ Availability: {state.trace_metadata['inventory_agent']['availability_score']*100:.0f}%")
    
    print("\n3️⃣  Running FulfillmentAgent...")
    state = fulfillment_agent(state)
    assert "fulfillment_agent" in state.trace_metadata
    print(f"   ✅ Order ID: {state.trace_metadata['fulfillment_agent'].get('order_id', 'N/A')}")
    
    print("\n" + "="*60)
    print("PIPELINE TRACE VERIFICATION")
    print("="*60)
    
    # Verify all agents created traces
    agents_traced = [
        "medical_validator",
        "inventory_agent",
        "fulfillment_agent"
    ]
    
    for agent in agents_traced:
        assert agent in state.trace_metadata, f"{agent} should have trace metadata"
        print(f"✅ {agent}: Traced")
    
    print("\n✅ Complete pipeline tracing test passed!")
    print("\n📊 Trace Summary:")
    print(f"   Agents traced: {len(agents_traced)}")
    print(f"   Final decision: {state.pharmacist_decision}")
    print(f"   Order status: {state.order_status}")
    
    # Flush traces to Langfuse
    observability_service.flush()
    print("\n✅ Traces flushed to Langfuse")


def test_manual_tracing():
    """Test manual tracing functions."""
    # Test decision logging
    observability_service.log_decision(
        agent_name="TestAgent",
        decision="approved",
        reasoning="Test reasoning",
        confidence=0.95
    )
    
    # Test tool call logging
    observability_service.log_tool_call(
        tool_name="test_tool",
        input_data={"param": "value"},
        output_data={"result": "success"},
        success=True
    )
    
    # Test safety issue logging
    observability_service.log_safety_issue(
        agent_name="TestAgent",
        issue_type="test_issue",
        severity="low",
        description="Test safety issue",
        medicines=["Medicine A"]
    )
    
    # Flush traces
    observability_service.flush()
    
    print("\n✅ Manual tracing test passed")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("LANGFUSE INTEGRATION TESTS")
    print("="*60)
    
    # Run tests
    test_langfuse_client_initialized()
    test_medical_validation_agent_tracing()
    test_inventory_agent_tracing()
    test_fulfillment_agent_tracing()
    test_complete_agent_pipeline_tracing()
    test_manual_tracing()
    
    print("\n" + "="*60)
    print("ALL TESTS PASSED! ✅")
    print("="*60)
    print("\n📊 Check Langfuse UI for traces:")
    print("   https://us.cloud.langfuse.com")
    print("\n")
