"""
LLM SAFETY CHECK TESTS
======================
Test the enhanced drug interaction checking functionality.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.state import OrderItem
from src.services.llm_service import call_llm_safety_check


def test_no_interactions():
    """Test with medicines that have no interactions."""
    print("\n" + "="*60)
    print("TEST 1: NO INTERACTIONS")
    print("="*60)
    
    items = [
        OrderItem(medicine_name="Paracetamol", dosage="500mg", quantity=1),
        OrderItem(medicine_name="Vitamin C", dosage="1000mg", quantity=1)
    ]
    
    result = call_llm_safety_check(items)
    
    print(f"\nHas Interactions: {result['has_interactions']}")
    print(f"Severity: {result['severity']}")
    print(f"Safe to Dispense: {result['safe_to_dispense']}")
    print(f"Warnings: {len(result['warnings'])}")
    
    assert result['has_interactions'] == False, "Should have no interactions"
    assert result['severity'] == "none", "Severity should be none"
    assert result['safe_to_dispense'] == True, "Should be safe to dispense"
    
    print("\n✅ No interactions test passed")


def test_duplicate_medicine():
    """Test with duplicate medicines."""
    print("\n" + "="*60)
    print("TEST 2: DUPLICATE MEDICINE")
    print("="*60)
    
    items = [
        OrderItem(medicine_name="Paracetamol", dosage="500mg", quantity=1),
        OrderItem(medicine_name="Paracetamol", dosage="500mg", quantity=1)
    ]
    
    result = call_llm_safety_check(items)
    
    print(f"\nHas Interactions: {result['has_interactions']}")
    print(f"Severity: {result['severity']}")
    print(f"Interactions: {len(result['interactions'])}")
    
    if result['interactions']:
        for interaction in result['interactions']:
            print(f"\n  Medicines: {interaction['medicines']}")
            print(f"  Severity: {interaction['severity']}")
            print(f"  Description: {interaction['description']}")
    
    assert result['has_interactions'] == True, "Should detect duplicate"
    assert len(result['interactions']) > 0, "Should have interaction entry"
    
    print("\n✅ Duplicate medicine test passed")


def test_nsaid_combination():
    """Test with multiple NSAIDs (moderate interaction)."""
    print("\n" + "="*60)
    print("TEST 3: MULTIPLE NSAIDs")
    print("="*60)
    
    items = [
        OrderItem(medicine_name="Aspirin", dosage="100mg", quantity=1),
        OrderItem(medicine_name="Ibuprofen", dosage="400mg", quantity=1)
    ]
    
    result = call_llm_safety_check(items)
    
    print(f"\nHas Interactions: {result['has_interactions']}")
    print(f"Severity: {result['severity']}")
    print(f"Safe to Dispense: {result['safe_to_dispense']}")
    
    if result['interactions']:
        for interaction in result['interactions']:
            print(f"\n  Medicines: {interaction['medicines']}")
            print(f"  Severity: {interaction['severity']}")
            print(f"  Description: {interaction['description']}")
            print(f"  Recommendation: {interaction['recommendation']}")
    
    assert result['has_interactions'] == True, "Should detect NSAID interaction"
    assert result['severity'] in ["moderate", "severe"], "Should be moderate or severe"
    
    print("\n✅ NSAID combination test passed")


def test_severe_interaction():
    """Test with severe interaction (benzodiazepine + opioid)."""
    print("\n" + "="*60)
    print("TEST 4: SEVERE INTERACTION")
    print("="*60)
    
    items = [
        OrderItem(medicine_name="Alprazolam", dosage="0.5mg", quantity=1),
        OrderItem(medicine_name="Tramadol", dosage="50mg", quantity=1)
    ]
    
    result = call_llm_safety_check(items)
    
    print(f"\nHas Interactions: {result['has_interactions']}")
    print(f"Severity: {result['severity']}")
    print(f"Safe to Dispense: {result['safe_to_dispense']}")
    
    if result['interactions']:
        for interaction in result['interactions']:
            print(f"\n  Medicines: {interaction['medicines']}")
            print(f"  Severity: {interaction['severity']}")
            print(f"  Description: {interaction['description']}")
            print(f"  Recommendation: {interaction['recommendation']}")
    
    assert result['has_interactions'] == True, "Should detect severe interaction"
    assert result['severity'] == "severe", "Should be severe"
    assert result['safe_to_dispense'] == False, "Should NOT be safe to dispense"
    
    print("\n✅ Severe interaction test passed")


def test_anticoagulant_nsaid():
    """Test with anticoagulant + NSAID (severe interaction)."""
    print("\n" + "="*60)
    print("TEST 5: ANTICOAGULANT + NSAID")
    print("="*60)
    
    items = [
        OrderItem(medicine_name="Warfarin", dosage="5mg", quantity=1),
        OrderItem(medicine_name="Aspirin", dosage="100mg", quantity=1)
    ]
    
    result = call_llm_safety_check(items)
    
    print(f"\nHas Interactions: {result['has_interactions']}")
    print(f"Severity: {result['severity']}")
    print(f"Safe to Dispense: {result['safe_to_dispense']}")
    
    if result['interactions']:
        for interaction in result['interactions']:
            print(f"\n  Medicines: {interaction['medicines']}")
            print(f"  Severity: {interaction['severity']}")
            print(f"  Description: {interaction['description']}")
    
    assert result['has_interactions'] == True, "Should detect interaction"
    assert result['severity'] == "severe", "Should be severe"
    
    print("\n✅ Anticoagulant + NSAID test passed")


def test_general_warnings():
    """Test that general warnings are provided."""
    print("\n" + "="*60)
    print("TEST 6: GENERAL WARNINGS")
    print("="*60)
    
    items = [
        OrderItem(medicine_name="Amoxicillin", dosage="500mg", quantity=1),
        OrderItem(medicine_name="Prednisolone", dosage="10mg", quantity=1)
    ]
    
    result = call_llm_safety_check(items)
    
    print(f"\nWarnings: {len(result['warnings'])}")
    for warning in result['warnings']:
        print(f"  - {warning}")
    
    assert len(result['warnings']) > 0, "Should have general warnings"
    
    print("\n✅ General warnings test passed")


def test_empty_list():
    """Test with empty medicine list."""
    print("\n" + "="*60)
    print("TEST 7: EMPTY LIST")
    print("="*60)
    
    items = []
    
    result = call_llm_safety_check(items)
    
    print(f"\nHas Interactions: {result['has_interactions']}")
    print(f"Safe to Dispense: {result['safe_to_dispense']}")
    
    assert result['has_interactions'] == False, "Should have no interactions"
    assert result['safe_to_dispense'] == True, "Should be safe"
    
    print("\n✅ Empty list test passed")


def test_result_structure():
    """Test that result has all required fields."""
    print("\n" + "="*60)
    print("TEST 8: RESULT STRUCTURE")
    print("="*60)
    
    items = [
        OrderItem(medicine_name="Paracetamol", dosage="500mg", quantity=1)
    ]
    
    result = call_llm_safety_check(items)
    
    # Check all required fields exist
    required_fields = [
        "has_interactions",
        "severity",
        "interactions",
        "warnings",
        "safe_to_dispense"
    ]
    
    for field in required_fields:
        assert field in result, f"Missing required field: {field}"
        print(f"✓ Field '{field}' present")
    
    # Check types
    assert isinstance(result['has_interactions'], bool), "has_interactions should be bool"
    assert isinstance(result['severity'], str), "severity should be string"
    assert isinstance(result['interactions'], list), "interactions should be list"
    assert isinstance(result['warnings'], list), "warnings should be list"
    assert isinstance(result['safe_to_dispense'], bool), "safe_to_dispense should be bool"
    
    print("\n✅ Result structure test passed")


if __name__ == "__main__":
    print("\n🧪 Running LLM Safety Check Tests...\n")
    
    try:
        # Run all tests
        test_no_interactions()
        test_duplicate_medicine()
        test_nsaid_combination()
        test_severe_interaction()
        test_anticoagulant_nsaid()
        test_general_warnings()
        test_empty_list()
        test_result_structure()
        
        print("\n" + "="*60)
        print("✅ ALL LLM SAFETY CHECK TESTS PASSED")
        print("="*60)
        print("\n💡 LLM Safety Check is working correctly")
        print("   - Detects drug-drug interactions")
        print("   - Identifies duplicate medicines")
        print("   - Classifies severity levels")
        print("   - Provides actionable recommendations")
        print("   - Falls back to rule-based check when LLM unavailable")
        print("\n📝 Note: Tests use rule-based fallback if GEMINI_API_KEY not set\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
