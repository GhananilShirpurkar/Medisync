"""
MEDICAL VALIDATION AGENT TESTS
===============================
Test the medical validation agent with various scenarios.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.state import PharmacyState, OrderItem
from src.agents.medical_validator_agent import (
    medical_validation_agent,
    get_validation_summary,
    format_validation_report
)


def test_valid_prescription():
    """Test with a valid prescription."""
    print("\n" + "="*60)
    print("TEST 1: VALID PRESCRIPTION")
    print("="*60)
    
    # Create state with valid prescription
    state = PharmacyState(
        user_id="test_user",
        prescription_uploaded=True,
        prescription_verified=False,
        extracted_items=[
            OrderItem(medicine_name="Paracetamol", dosage="500mg", quantity=2)
        ]
    )
    
    # Add vision agent metadata with complete prescription data
    state.trace_metadata["vision_agent"] = {
        "patient_name": "John Doe",
        "doctor_name": "Dr. Smith",
        "date": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
        "signature_present": True,
        "medicines": [
            {
                "name": "Paracetamol",
                "dosage": "500mg",
                "frequency": "3 times daily",
                "duration": "5 days"
            }
        ]
    }
    
    # Run validation
    result = medical_validation_agent(state)
    
    # Check results - should be approved or need review (not rejected)
    assert result.pharmacist_decision in ["approved", "needs_review"], f"Should be approved or need review, got {result.pharmacist_decision}"
    
    summary = get_validation_summary(result)
    print(f"\nStatus: {summary['status']}")
    print(f"Risk Score: {summary['risk_score']}")
    print(f"Decision: {summary['decision']}")
    
    print("\n✅ Valid prescription test passed")
    return result


def test_expired_prescription():
    """Test with an expired prescription."""
    print("\n" + "="*60)
    print("TEST 2: EXPIRED PRESCRIPTION")
    print("="*60)
    
    # Create state with expired prescription
    state = PharmacyState(
        user_id="test_user",
        prescription_uploaded=True,
        extracted_items=[
            OrderItem(medicine_name="Paracetamol", dosage="500mg", quantity=1)
        ]
    )
    
    # Add vision agent metadata with old date
    state.trace_metadata["vision_agent"] = {
        "patient_name": "John Doe",
        "doctor_name": "Dr. Smith",
        "date": (datetime.now() - timedelta(days=200)).strftime("%Y-%m-%d"),
        "signature_present": True
    }
    
    # Run validation
    result = medical_validation_agent(state)
    
    # Check results
    assert result.pharmacist_decision in ["rejected", "needs_review"], "Should be rejected or need review"
    
    summary = get_validation_summary(result)
    print(f"\nStatus: {summary['status']}")
    print(f"Issues: {summary['issues_count']}")
    
    print("\n✅ Expired prescription test passed")
    return result


def test_controlled_substance():
    """Test with controlled substance."""
    print("\n" + "="*60)
    print("TEST 3: CONTROLLED SUBSTANCE")
    print("="*60)
    
    # Create state with controlled substance
    state = PharmacyState(
        user_id="test_user",
        prescription_uploaded=True,
        extracted_items=[
            OrderItem(medicine_name="Alprazolam", dosage="0.5mg", quantity=1)
        ]
    )
    
    # Add vision agent metadata
    state.trace_metadata["vision_agent"] = {
        "patient_name": "John Doe",
        "doctor_name": "Dr. Smith",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "signature_present": True
    }
    
    # Run validation
    result = medical_validation_agent(state)
    
    # Check results - Schedule X controlled substances should be rejected (critical severity)
    # This is correct behavior for habit-forming drugs
    assert result.pharmacist_decision in ["rejected", "needs_review"], "Schedule X drugs should be rejected or need review"
    
    summary = get_validation_summary(result)
    print(f"\nStatus: {summary['status']}")
    print(f"Requires Pharmacist: {summary['requires_pharmacist']}")
    print(f"Risk Score: {summary['risk_score']}")
    
    print("\n✅ Controlled substance test passed")
    return result


def test_missing_signature():
    """Test with missing signature."""
    print("\n" + "="*60)
    print("TEST 4: MISSING SIGNATURE")
    print("="*60)
    
    # Create state without signature
    state = PharmacyState(
        user_id="test_user",
        prescription_uploaded=True,
        extracted_items=[
            OrderItem(medicine_name="Paracetamol", dosage="500mg", quantity=1)
        ]
    )
    
    # Add vision agent metadata without signature
    state.trace_metadata["vision_agent"] = {
        "patient_name": "John Doe",
        "doctor_name": "Dr. Smith",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "signature_present": False
    }
    
    # Run validation
    result = medical_validation_agent(state)
    
    # Check results
    assert result.pharmacist_decision in ["rejected", "needs_review"], "Should be rejected or need review"
    
    summary = get_validation_summary(result)
    print(f"\nStatus: {summary['status']}")
    print(f"Issues: {summary['issues_count']}")
    
    print("\n✅ Missing signature test passed")
    return result


def test_excessive_dosage():
    """Test with excessive dosage."""
    print("\n" + "="*60)
    print("TEST 5: EXCESSIVE DOSAGE")
    print("="*60)
    
    # Create state with excessive dosage
    state = PharmacyState(
        user_id="test_user",
        prescription_uploaded=True,
        extracted_items=[
            OrderItem(medicine_name="Paracetamol", dosage="2000mg", quantity=3)  # 6000mg/day exceeds 4000mg limit
        ]
    )
    
    # Add vision agent metadata
    state.trace_metadata["vision_agent"] = {
        "patient_name": "John Doe",
        "doctor_name": "Dr. Smith",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "signature_present": True
    }
    
    # Run validation
    result = medical_validation_agent(state)
    
    # Check results
    assert result.pharmacist_decision in ["rejected", "needs_review"], "Should be rejected or need review"
    
    summary = get_validation_summary(result)
    print(f"\nStatus: {summary['status']}")
    print(f"Risk Score: {summary['risk_score']}")
    
    print("\n✅ Excessive dosage test passed")
    return result


def test_no_prescription():
    """Test with no prescription uploaded."""
    print("\n" + "="*60)
    print("TEST 6: NO PRESCRIPTION")
    print("="*60)
    
    # Create state without prescription
    state = PharmacyState(
        user_id="test_user",
extracted_items=[
            OrderItem(medicine_name="Amoxicillin", dosage="500mg", quantity=1)
        ]
    )
    
    # Run validation
    result = medical_validation_agent(state)
    
    # Check results
    assert result.pharmacist_decision == "needs_review", "Should be needs_review"
    assert "[PRESCRIPTION REQUIRED]" in " ".join(result.safety_issues), "Should have prescription required issue"
    
    print(f"\nDecision: {result.pharmacist_decision}")
    print(f"Issues: {result.safety_issues}")
    
    print("\n✅ No prescription test passed")
    return result


def test_validation_report():
    """Test validation report formatting."""
    print("\n" + "="*60)
    print("TEST 7: VALIDATION REPORT")
    print("="*60)
    
    # Create and validate a prescription
    state = PharmacyState(
        user_id="test_user",
        prescription_uploaded=True,
        extracted_items=[
            OrderItem(medicine_name="Amoxicillin", dosage="500mg", quantity=1)
        ]
    )
    
    state.trace_metadata["vision_agent"] = {
        "patient_name": "John Doe",
        "doctor_name": "Dr. Smith",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "signature_present": True
    }
    
    result = medical_validation_agent(state)
    
    # Generate report
    report = format_validation_report(result)
    
    print("\n" + report)
    
    assert "MEDICAL VALIDATION REPORT" in report, "Report should have title"
    assert "Status:" in report, "Report should have status"
    
    # Check if drug interaction metadata is present
    metadata = result.trace_metadata.get("medical_validator", {})
    assert "drug_interactions" in metadata, "Should have drug interaction data"
    
    print("\n✅ Validation report test passed")


def test_drug_interactions():
    """Test drug interaction detection."""
    print("\n" + "="*60)
    print("TEST 8: DRUG INTERACTIONS")
    print("="*60)
    
    # Create state with interacting drugs (Aspirin + Ibuprofen)
    state = PharmacyState(
        user_id="test_user",
        prescription_uploaded=True,
        extracted_items=[
            OrderItem(medicine_name="Aspirin", dosage="100mg", quantity=1),
            OrderItem(medicine_name="Ibuprofen", dosage="400mg", quantity=1)
        ]
    )
    
    state.trace_metadata["vision_agent"] = {
        "patient_name": "John Doe",
        "doctor_name": "Dr. Smith",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "signature_present": True
    }
    
    result = medical_validation_agent(state)
    
    # Check results - should detect interaction
    metadata = result.trace_metadata.get("medical_validator", {})
    interaction_data = metadata.get("drug_interactions", {})
    
    print(f"\nHas Interactions: {interaction_data.get('has_interactions')}")
    print(f"Severity: {interaction_data.get('severity')}")
    print(f"Safe to Dispense: {interaction_data.get('safe_to_dispense')}")
    
    # Should detect interaction (rule-based fallback will catch this)
    assert interaction_data.get("has_interactions") == True, "Should detect NSAID interaction"
    
    print("\n✅ Drug interaction test passed")


if __name__ == "__main__":
    print("\n🧪 Running Medical Validation Agent Tests...\n")
    
    try:
        # Run all tests
        test_valid_prescription()
        test_expired_prescription()
        test_controlled_substance()
        test_missing_signature()
        test_excessive_dosage()
        test_no_prescription()
        test_validation_report()
        test_drug_interactions()
        
        print("\n" + "="*60)
        print("✅ ALL MEDICAL VALIDATION AGENT TESTS PASSED")
        print("="*60)
        print("\n💡 Medical Validation Agent is working correctly")
        print("   - Validates prescription fields")
        print("   - Detects controlled substances")
        print("   - Checks dosage limits")
        print("   - Detects drug interactions (LLM + rule-based)")
        print("   - Generates risk scores")
        print("   - Provides reasoning traces\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
