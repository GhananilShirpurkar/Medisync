"""
CLINICAL REASONING TESTS
========================
Test the new clinical reasoning engine components: ATC parsing, Contraindications and Interactions.
"""

import sys
from pathlib import Path
import pytest

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.clinical_models import ClinicalContext
from src.services.atc_service import ATCService
from src.services.contraindication_service import ContraindicationService
from src.services.interaction_service import InteractionService


def test_atc_hierarchy_parsing():
    """Test that ATC codes are correctly split into their 5 levels."""
    print("\n" + "="*60)
    print("TEST 1: ATC HIERARCHY PARSING")
    print("="*60)
    
    # Example: N02BE01 (Paracetamol)
    # N = Nervous System
    # 02 = Analgesics
    # B = Other Analgesics and Antipyretics
    # E = Anilides
    # 01 = Paracetamol
    
    result = ATCService.get_atc_hierarchy("N02BE01")
    assert result["level_1"] == "N"
    assert result["level_2"] == "N02"
    assert result["level_3"] == "N02B"
    assert result["level_4"] == "N02BE"
    assert result["level_5"] == "N02BE01"
    
def test_atc_same_molecule():
    """Test molecule matching based on full ATC (Level 5)."""
    # Identical codes
    assert ATCService.are_same_molecule("N02BE01", "N02BE01") is True
    # Different molecules in same class
    assert ATCService.are_same_molecule("A10BA02", "A10BA03") is False


def test_atc_same_class():
    """Test chemical class matching based on Level 4 ATC."""
    # Metformin (A10BA02) and another Biguanide (A10BA03)
    assert ATCService.are_same_class("A10BA02", "A10BA03") is True
    # Metformin (A10BA02) and a Sulfonylurea (A10BB01)
    assert ATCService.are_same_class("A10BA02", "A10BB01") is False


def test_contraindication_safe():
    """Test that a patient with no contraindications passes."""
    context = ClinicalContext(
        comorbidities=["Mild Hypertension"],
        allergies=[],
        pregnancy_status="Not Pregnant"
    )
    
    # Paracetamol (N02BE01)
    violations = ContraindicationService.check_contraindications("N02BE01", context)
    assert len(violations) == 0


def test_contraindication_comorbidity_ulcer():
    """Test that peptic ulcer blocks NSAIDs."""
    context = ClinicalContext(
        comorbidities=["peptic_ulcer"],
        allergies=[],
        pregnancy_status="Not Pregnant"
    )
    
    # Diclofenac (M01AB05)
    violations = ContraindicationService.check_contraindications("M01AB05", context)
    
    # The migration script added peptic_ulcer rule for M01A
    assert len(violations) > 0
    assert violations[0]["severity"] == "absolute"
    assert violations[0]["condition"] == "peptic_ulcer"


def test_contraindication_comorbidity_asthma():
    """Test that asthma blocks Ibuprofen (M01AE01)."""
    context = ClinicalContext(
        comorbidities=["asthma"],
        allergies=[],
        pregnancy_status="Not Pregnant"
    )
    
    # Ibuprofen (M01AE01)
    violations = ContraindicationService.check_contraindications("M01AE01", context)
    
    # The migration script added an asthma rule for M01AE
    assert len(violations) > 0
    assert violations[0]["severity"] == "relative"


def test_interaction_service():
    """Test basic drug-drug interaction checking."""
    from src.db_config import get_db_context
    from src.models import Medicine
    import uuid
    
    # Needs to match the hardcoded rule ("N02BA", "B01AA")
    with get_db_context() as db:
        if not db.query(Medicine).filter(Medicine.name == "Mock Warfarin").first():
            db.add(Medicine(name="Mock Warfarin", atc_code="B01AA03", price=10.0, stock=100))
            db.commit()

    context = ClinicalContext(
        current_medications=["Mock Warfarin"]
    )
    
    # Proposing Aspirin (N02BA01) against Warfarin
    interactions = InteractionService.check_interactions("Aspirin", "N02BA01", context.current_medications)
    
    assert len(interactions) > 0
    assert interactions[0]["severity"] == "major"
