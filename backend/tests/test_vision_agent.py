"""
VISION AGENT TEST SUITE
========================
Tests for prescription image processing and parsing.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import from the agents module (not the agents package)
from src.vision_agent import vision_agent

from src.state import PharmacyState


def test_vision_agent_with_mock_image():
    """Test vision agent with mock OCR response."""
    print("\n" + "="*60)
    print("VISION AGENT TEST SUITE")
    print("="*60)
    
    # Initialize state
    state = PharmacyState(
        user_id="test_user_123",
        user_message="Process my prescription"
    )
    
    # Test with mock image (OCR service will return mock data)
    print("\n=== Testing Vision Agent with Mock Image ===")
    test_image_path = "test_prescription.jpg"
    
    result_state = vision_agent(state, test_image_path, use_mock=True)
    
    # Verify results
    print(f"Prescription uploaded: {result_state.prescription_uploaded}")
    print(f"Prescription verified: {result_state.prescription_verified}")
    print(f"Extracted items count: {len(result_state.extracted_items)}")
    
    if result_state.extracted_items:
        print("\nExtracted Medicines:")
        for item in result_state.extracted_items:
            print(f"  - {item.medicine_name} ({item.dosage})")
    
    if result_state.trace_metadata.get("vision_agent"):
        metadata = result_state.trace_metadata["vision_agent"]
        print(f"\nConfidence Scores:")
        print(f"  OCR: {metadata.get('ocr_confidence', 0):.2f}")
        print(f"  LLM: {metadata.get('llm_confidence', 0):.2f}")
        print(f"  Overall: {metadata.get('overall_confidence', 0):.2f}")
        
        print(f"\nPrescription Details:")
        print(f"  Patient: {metadata.get('patient_name')}")
        print(f"  Doctor: {metadata.get('doctor_name')}")
        print(f"  Date: {metadata.get('date')}")
        print(f"  Signature: {metadata.get('signature_present')}")
        
        if metadata.get('notes'):
            print(f"  Notes: {metadata.get('notes')}")
    
    if result_state.safety_issues:
        print(f"\nSafety Issues/Warnings:")
        for issue in result_state.safety_issues:
            print(f"  ⚠️  {issue}")
    
    # Assertions
    assert result_state.prescription_uploaded or not result_state.prescription_verified, \
        "If not uploaded, should not be verified"
    assert len(result_state.extracted_items) > 0, "Should extract at least one medicine"
    assert "vision_agent" in result_state.trace_metadata, "Should have trace metadata"
    
    print("\n✅ Vision agent test passed")
    
    return result_state


def test_vision_agent_confidence_levels():
    """Test vision agent handles different confidence levels correctly."""
    print("\n=== Testing Confidence Level Handling ===")
    
    # This test verifies the agent's decision logic based on confidence
    # In production, different images would yield different confidence scores
    
    state = PharmacyState(user_id="test_user")
    result = vision_agent(state, "test_image.jpg", use_mock=True)
    
    metadata = result.trace_metadata.get("vision_agent", {})
    overall_confidence = metadata.get("overall_confidence", 0)
    
    print(f"Overall confidence: {overall_confidence:.2f}")
    
    if overall_confidence >= 0.9:
        print("✅ High confidence - Auto-verified")
        assert result.prescription_verified, "Should be verified at high confidence"
    elif overall_confidence >= 0.7:
        print("⚠️  Medium confidence - Needs review")
        assert not result.prescription_verified, "Should not be auto-verified at medium confidence"
        assert result.prescription_uploaded, "Should still be uploaded"
    else:
        print("❌ Low confidence - Re-capture needed")
        assert not result.prescription_verified, "Should not be verified at low confidence"
    
    print("✅ Confidence level handling test passed")


def test_vision_agent_state_preservation():
    """Test that vision agent preserves existing state data."""
    print("\n=== Testing State Preservation ===")
    
    # Create state with existing data
    state = PharmacyState(
        user_id="test_user_456",
        user_message="Original message",
        intent="purchase",
        language="en"
    )
    
    # Process prescription
    result = vision_agent(state, "test_image.jpg", use_mock=True)
    
    # Verify original data is preserved
    assert result.user_id == "test_user_456", "Should preserve user_id"
    assert result.user_message == "Original message", "Should preserve user_message"
    assert result.intent == "purchase", "Should preserve intent"
    assert result.language == "en", "Should preserve language"
    
    print("✅ State preservation test passed")


def test_vision_agent_error_handling():
    """Test vision agent handles errors gracefully."""
    print("\n=== Testing Error Handling ===")
    
    state = PharmacyState(user_id="test_user")
    
    # Test with non-existent file (should handle gracefully with mock)
    result = vision_agent(state, "nonexistent_file.jpg", use_mock=True)
    
    # Should still return valid state
    assert isinstance(result, PharmacyState), "Should return valid state"
    assert isinstance(result.safety_issues, list), "Should have safety_issues list"
    
    print("✅ Error handling test passed")


if __name__ == "__main__":
    print("\n🧪 Running Vision Agent Tests...\n")
    
    try:
        # Run all tests
        test_vision_agent_with_mock_image()
        test_vision_agent_confidence_levels()
        test_vision_agent_state_preservation()
        test_vision_agent_error_handling()
        
        print("\n" + "="*60)
        print("✅ ALL VISION AGENT TESTS PASSED")
        print("="*60)
        print("\n💡 Note: Using mock responses (Gemini API may not be configured)")
        print("   To use real API, set GEMINI_API_KEY in .env\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
