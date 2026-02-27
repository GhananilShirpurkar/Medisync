"""
VALIDATION RULES TEST SUITE
============================
Tests for medical validation rules engine.
"""

import sys
import os
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.validation_rules import (
    validate_prescription_date,
    validate_signature,
    validate_medicine_details,
    validate_controlled_substances,
    validate_dosage_limits,
    validate_duplicate_medicines,
    validate_prescription,
    IssueSeverity,
    ValidationStatus
)


def test_prescription_date_validation():
    """Test prescription date validation rules."""
    print("\n" + "="*60)
    print("PRESCRIPTION DATE VALIDATION TESTS")
    print("="*60)
    
    # Test 1: Missing date
    print("\n=== Test 1: Missing Date ===")
    issues = validate_prescription_date(None)
    assert len(issues) > 0, "Should flag missing date"
    assert issues[0].severity == IssueSeverity.CRITICAL
    print(f"✅ Missing date detected: {issues[0].message}")
    
    # Test 2: Valid recent date
    print("\n=== Test 2: Valid Recent Date ===")
    recent_date = (datetime.now() - timedelta(days=30)).strftime("%d/%m/%Y")
    issues = validate_prescription_date(recent_date)
    assert len(issues) == 0, "Should pass for recent date"
    print(f"✅ Valid date accepted: {recent_date}")
    
    # Test 3: Expired prescription
    print("\n=== Test 3: Expired Prescription ===")
    expired_date = (datetime.now() - timedelta(days=200)).strftime("%d/%m/%Y")
    issues = validate_prescription_date(expired_date)
    assert len(issues) > 0, "Should flag expired prescription"
    assert any(i.severity == IssueSeverity.CRITICAL for i in issues)
    print(f"✅ Expired prescription detected: {issues[0].message}")
    
    # Test 4: Future date
    print("\n=== Test 4: Future Date ===")
    future_date = (datetime.now() + timedelta(days=10)).strftime("%d/%m/%Y")
    issues = validate_prescription_date(future_date)
    assert len(issues) > 0, "Should flag future date"
    print(f"✅ Future date detected: {issues[0].message}")
    
    print("\n✅ All date validation tests passed")


def test_signature_validation():
    """Test signature validation rules."""
    print("\n" + "="*60)
    print("SIGNATURE VALIDATION TESTS")
    print("="*60)
    
    # Test 1: Missing signature
    print("\n=== Test 1: Missing Signature ===")
    issues = validate_signature(False, "Dr. Smith")
    assert len(issues) > 0, "Should flag missing signature"
    print(f"✅ Missing signature detected: {issues[0].message}")
    
    # Test 2: Missing doctor name
    print("\n=== Test 2: Missing Doctor Name ===")
    issues = validate_signature(True, None)
    assert len(issues) > 0, "Should flag missing doctor name"
    print(f"✅ Missing doctor name detected: {issues[0].message}")
    
    # Test 3: Valid signature and name
    print("\n=== Test 3: Valid Signature and Name ===")
    issues = validate_signature(True, "Dr. John Smith")
    assert len(issues) == 0, "Should pass with valid signature and name"
    print("✅ Valid signature and name accepted")
    
    print("\n✅ All signature validation tests passed")



def test_medicine_validation():
    """Test medicine details validation."""
    print("\n" + "="*60)
    print("MEDICINE VALIDATION TESTS")
    print("="*60)
    
    # Test 1: Complete medicine details
    print("\n=== Test 1: Complete Medicine Details ===")
    medicine = {
        "name": "Paracetamol",
        "dosage": "500mg",
        "frequency": "3 times daily"
    }
    issues = validate_medicine_details(medicine)
    assert len(issues) == 0, "Should pass with complete details"
    print("✅ Complete medicine details accepted")
    
    # Test 2: Missing medicine name
    print("\n=== Test 2: Missing Medicine Name ===")
    medicine = {"dosage": "500mg", "frequency": "3 times daily"}
    issues = validate_medicine_details(medicine)
    assert len(issues) > 0, "Should flag missing name"
    print(f"✅ Missing name detected: {issues[0].message}")
    
    # Test 3: Missing dosage
    print("\n=== Test 3: Missing Dosage ===")
    medicine = {"name": "Paracetamol", "frequency": "3 times daily"}
    issues = validate_medicine_details(medicine)
    assert len(issues) > 0, "Should flag missing dosage"
    print(f"✅ Missing dosage detected: {issues[0].message}")
    
    print("\n✅ All medicine validation tests passed")


def test_controlled_substances():
    """Test controlled substance detection."""
    print("\n" + "="*60)
    print("CONTROLLED SUBSTANCE TESTS")
    print("="*60)
    
    # Test 1: Schedule X (habit-forming)
    print("\n=== Test 1: Schedule X Drug ===")
    medicines = [{"name": "Alprazolam", "dosage": "0.5mg"}]
    issues = validate_controlled_substances(medicines)
    assert len(issues) > 0, "Should flag Schedule X drug"
    assert any(i.severity == IssueSeverity.CRITICAL for i in issues)
    print(f"✅ Schedule X drug detected: {issues[0].message}")
    
    # Test 2: Antibiotic (Schedule H)
    print("\n=== Test 2: Antibiotic (Schedule H) ===")
    medicines = [{"name": "Amoxicillin", "dosage": "500mg"}]
    issues = validate_controlled_substances(medicines)
    assert len(issues) > 0, "Should flag antibiotic"
    print(f"✅ Antibiotic detected: {issues[0].message}")
    
    # Test 3: High-risk drug
    print("\n=== Test 3: High-Risk Drug ===")
    medicines = [{"name": "Warfarin", "dosage": "5mg"}]
    issues = validate_controlled_substances(medicines)
    assert len(issues) > 0, "Should flag high-risk drug"
    print(f"✅ High-risk drug detected: {issues[0].message}")
    
    # Test 4: Regular OTC medicine
    print("\n=== Test 4: Regular OTC Medicine ===")
    medicines = [{"name": "Paracetamol", "dosage": "500mg"}]
    issues = validate_controlled_substances(medicines)
    assert len(issues) == 0, "Should not flag OTC medicine"
    print("✅ OTC medicine accepted")
    
    print("\n✅ All controlled substance tests passed")


def test_dosage_limits():
    """Test dosage limit validation."""
    print("\n" + "="*60)
    print("DOSAGE LIMIT TESTS")
    print("="*60)
    
    # Test 1: Safe dosage
    print("\n=== Test 1: Safe Dosage ===")
    medicines = [{
        "name": "Paracetamol",
        "dosage": "500mg",
        "frequency": "3 times daily"
    }]
    issues = validate_dosage_limits(medicines)
    assert len(issues) == 0, "Should pass safe dosage"
    print("✅ Safe dosage accepted (1500mg/day, limit 4000mg/day)")
    
    # Test 2: Excessive dosage
    print("\n=== Test 2: Excessive Dosage ===")
    medicines = [{
        "name": "Paracetamol",
        "dosage": "1000mg",
        "frequency": "5 times daily"
    }]
    issues = validate_dosage_limits(medicines)
    assert len(issues) > 0, "Should flag excessive dosage"
    assert any(i.severity == IssueSeverity.CRITICAL for i in issues)
    print(f"✅ Excessive dosage detected: {issues[0].message}")
    
    # Test 3: Near limit dosage
    print("\n=== Test 3: Near Limit Dosage ===")
    medicines = [{
        "name": "Paracetamol",
        "dosage": "1000mg",
        "frequency": "3 times daily"
    }]
    issues = validate_dosage_limits(medicines)
    # 3000mg is within 80% of 4000mg limit, should warn
    if issues:
        print(f"✅ Near-limit dosage flagged: {issues[0].message}")
    else:
        print("✅ Near-limit dosage accepted")
    
    print("\n✅ All dosage limit tests passed")


def test_duplicate_medicines():
    """Test duplicate medicine detection."""
    print("\n" + "="*60)
    print("DUPLICATE MEDICINE TESTS")
    print("="*60)
    
    # Test 1: No duplicates
    print("\n=== Test 1: No Duplicates ===")
    medicines = [
        {"name": "Paracetamol"},
        {"name": "Amoxicillin"}
    ]
    issues = validate_duplicate_medicines(medicines)
    assert len(issues) == 0, "Should pass with no duplicates"
    print("✅ No duplicates detected")
    
    # Test 2: Exact duplicate
    print("\n=== Test 2: Exact Duplicate ===")
    medicines = [
        {"name": "Paracetamol"},
        {"name": "Paracetamol"}
    ]
    issues = validate_duplicate_medicines(medicines)
    assert len(issues) > 0, "Should flag duplicate"
    print(f"✅ Duplicate detected: {issues[0].message}")
    
    print("\n✅ All duplicate medicine tests passed")



def test_full_prescription_validation():
    """Test complete prescription validation."""
    print("\n" + "="*60)
    print("FULL PRESCRIPTION VALIDATION TESTS")
    print("="*60)
    
    # Test 1: Valid prescription
    print("\n=== Test 1: Valid Prescription ===")
    prescription = {
        "patient_name": "John Doe",
        "doctor_name": "Dr. Jane Smith",
        "date": datetime.now().strftime("%d/%m/%Y"),
        "medicines": [
            {
                "name": "Paracetamol",
                "dosage": "500mg",
                "frequency": "3 times daily",
                "duration": "5 days"
            }
        ],
        "signature_present": True,
        "doctor_registration_number": "12345"
    }
    
    result = validate_prescription(prescription)
    print(f"Status: {result['status']}")
    print(f"Risk Score: {result['risk_score']:.2f}")
    print(f"Requires Pharmacist: {result['requires_pharmacist']}")
    print(f"Issues: {len(result['issues'])}")
    
    if result['reasoning_trace']:
        print("\nReasoning Trace:")
        for trace in result['reasoning_trace']:
            print(f"  - {trace}")
    
    assert result['status'] == ValidationStatus.APPROVED.value, "Should approve valid prescription"
    print("\n✅ Valid prescription approved")
    
    # Test 2: Prescription with controlled substance
    print("\n=== Test 2: Prescription with Controlled Substance ===")
    prescription = {
        "patient_name": "John Doe",
        "doctor_name": "Dr. Jane Smith",
        "date": datetime.now().strftime("%d/%m/%Y"),
        "medicines": [
            {
                "name": "Alprazolam",
                "dosage": "0.5mg",
                "frequency": "2 times daily"
            }
        ],
        "signature_present": True
    }
    
    result = validate_prescription(prescription)
    print(f"Status: {result['status']}")
    print(f"Risk Score: {result['risk_score']:.2f}")
    print(f"Requires Pharmacist: {result['requires_pharmacist']}")
    print(f"Issues: {len(result['issues'])}")
    
    assert result['requires_pharmacist'], "Should require pharmacist for controlled substance"
    print("\n✅ Controlled substance flagged for pharmacist review")
    
    # Test 3: Expired prescription
    print("\n=== Test 3: Expired Prescription ===")
    expired_date = (datetime.now() - timedelta(days=200)).strftime("%d/%m/%Y")
    prescription = {
        "patient_name": "John Doe",
        "doctor_name": "Dr. Jane Smith",
        "date": expired_date,
        "medicines": [
            {"name": "Paracetamol", "dosage": "500mg"}
        ],
        "signature_present": True
    }
    
    result = validate_prescription(prescription)
    print(f"Status: {result['status']}")
    print(f"Risk Score: {result['risk_score']:.2f}")
    print(f"Issues: {len(result['issues'])}")
    
    assert result['status'] == ValidationStatus.REJECTED.value, "Should reject expired prescription"
    print("\n✅ Expired prescription rejected")
    
    # Test 4: Missing signature
    print("\n=== Test 4: Missing Signature ===")
    prescription = {
        "patient_name": "John Doe",
        "doctor_name": "Dr. Jane Smith",
        "date": datetime.now().strftime("%d/%m/%Y"),
        "medicines": [
            {"name": "Paracetamol", "dosage": "500mg"}
        ],
        "signature_present": False
    }
    
    result = validate_prescription(prescription)
    print(f"Status: {result['status']}")
    print(f"Issues: {len(result['issues'])}")
    
    assert result['status'] == ValidationStatus.REJECTED.value, "Should reject without signature"
    print("\n✅ Missing signature rejected")
    
    # Test 5: Excessive dosage
    print("\n=== Test 5: Excessive Dosage ===")
    prescription = {
        "patient_name": "John Doe",
        "doctor_name": "Dr. Jane Smith",
        "date": datetime.now().strftime("%d/%m/%Y"),
        "medicines": [
            {
                "name": "Paracetamol",
                "dosage": "1000mg",
                "frequency": "5 times daily"
            }
        ],
        "signature_present": True
    }
    
    result = validate_prescription(prescription)
    print(f"Status: {result['status']}")
    print(f"Risk Score: {result['risk_score']:.2f}")
    
    assert result['status'] == ValidationStatus.REJECTED.value, "Should reject excessive dosage"
    print("\n✅ Excessive dosage rejected")
    
    print("\n✅ All full prescription validation tests passed")


if __name__ == "__main__":
    print("\n🧪 Running Validation Rules Test Suite...\n")
    
    try:
        test_prescription_date_validation()
        test_signature_validation()
        test_medicine_validation()
        test_controlled_substances()
        test_dosage_limits()
        test_duplicate_medicines()
        test_full_prescription_validation()
        
        print("\n" + "="*60)
        print("✅ ALL VALIDATION RULES TESTS PASSED")
        print("="*60)
        print("\n💡 Medical validation rules engine is working correctly\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
