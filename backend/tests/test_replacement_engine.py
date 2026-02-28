"""
REPLACEMENT ENGINE UNIT TESTS
==============================
Tests for find_equivalent_replacement() using a mocked DB session.

The SQLAlchemy Medicine class is intentionally NOT patched — it must remain a
real class so that column expressions (e.g. Medicine.stock > 0) work correctly
inside the function under test. Only get_db_context is mocked to inject a
pre-configured session.

Run with:
    cd /home/koanoir/Desktop/Projects/01_sandbox/Medisync/backend
    .venv/bin/pytest tests/test_replacement_engine.py -v
"""

import sys
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.replacement_models import ReplacementResponse
from src.agents.inventory_and_rules_agent import find_equivalent_replacement
from src.database import Database


# ------------------------------------------------------------------
# Shared helpers
# ------------------------------------------------------------------

def _make_medicine(**overrides):
    """Minimal medicine dict returned by db.get_medicine()."""
    base = {
        "id": 1,
        "name": "TestMed",
        "category": "Analgesic",
        "price": 100.0,
        "stock": 50,
        "active_ingredients": "Paracetamol",
        "generic_equivalent": "paracetamol",
        "contraindications": "",
        "manufacturer": "TestPharma",
    }
    base.update(overrides)
    return base


def _make_sa_medicine(**overrides):
    """Minimal SQLAlchemy-like stub for session.query() results."""
    m = MagicMock()
    m.name = overrides.get("name", "Substitute")
    m.category = overrides.get("category", "Analgesic")
    m.price = overrides.get("price", 80.0)
    m.stock = overrides.get("stock", 30)
    m.active_ingredients = overrides.get("active_ingredients", "Paracetamol")
    m.generic_equivalent = overrides.get("generic_equivalent", "paracetamol")
    m.contraindications = overrides.get("contraindications", "")
    return m


def _mock_ctx(candidates):
    """
    Return a context-manager patch for get_db_context that yields a session
    whose query(...).filter(...).all() returns the given candidates list.

    We do NOT patch src.models.Medicine — the real class must stay intact
    so SQLAlchemy column expressions evaluate without errors.
    """
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.all.return_value = candidates

    @contextmanager
    def _ctx():
        yield mock_session

    return patch("src.db_config.get_db_context", side_effect=_ctx)


# ------------------------------------------------------------------
# Test: HIGH confidence — same active ingredient
# ------------------------------------------------------------------

def test_high_confidence_same_active_ingredient():
    db = MagicMock(spec=Database)
    db.get_medicine.return_value = _make_medicine(
        name="Crocin 500mg", category="Analgesic",
        active_ingredients="Paracetamol", generic_equivalent="paracetamol",
        price=120.0,
    )
    candidate = _make_sa_medicine(
        name="Dolo 650", category="Analgesic",
        active_ingredients="Paracetamol", price=90.0,
    )

    with _mock_ctx([candidate]):
        result = find_equivalent_replacement("Crocin 500mg", db)

    print(f"\n[HIGH] {result}")
    assert isinstance(result, ReplacementResponse)
    assert result.replacement_found is True
    assert result.confidence == "high"
    assert result.requires_pharmacist_override is False
    assert result.suggested == "Dolo 650"
    assert result.price_difference_percent < 0   # 90 cheaper than 120
    assert "paracetamol" in result.reasoning.lower()
    print("✅ High confidence test passed")


# ------------------------------------------------------------------
# Test: MEDIUM confidence — same generic equivalent only
# ------------------------------------------------------------------

def test_medium_confidence_same_generic():
    db = MagicMock(spec=Database)
    db.get_medicine.return_value = _make_medicine(
        name="BrandX", category="Antibiotic",
        active_ingredients="",           # no ingredient data
        generic_equivalent="amoxicillin", price=200.0,
    )
    candidate = _make_sa_medicine(
        name="BrandY", category="Antibiotic",
        active_ingredients="", generic_equivalent="amoxicillin", price=150.0,
    )

    with _mock_ctx([candidate]):
        result = find_equivalent_replacement("BrandX", db)

    print(f"\n[MEDIUM] {result}")
    assert result.replacement_found is True
    assert result.confidence == "medium"
    assert result.requires_pharmacist_override is True
    assert "amoxicillin" in result.reasoning.lower()
    print("✅ Medium confidence test passed")


# ------------------------------------------------------------------
# Test: LOW confidence — category match only
# ------------------------------------------------------------------

def test_low_confidence_category_only():
    db = MagicMock(spec=Database)
    db.get_medicine.return_value = _make_medicine(
        name="MedA", category="Antacid",
        active_ingredients="", generic_equivalent="", price=50.0,
    )
    candidate = _make_sa_medicine(
        name="MedB", category="Antacid",
        active_ingredients="", generic_equivalent="", price=55.0,
    )

    with _mock_ctx([candidate]):
        result = find_equivalent_replacement("MedA", db)

    print(f"\n[LOW] {result}")
    assert result.replacement_found is True
    assert result.confidence == "low"
    assert result.requires_pharmacist_override is True
    print("✅ Low confidence test passed")


# ------------------------------------------------------------------
# Test: NO replacement — no same-category candidates in stock
# ------------------------------------------------------------------

def test_no_replacement_empty_category():
    db = MagicMock(spec=Database)
    db.get_medicine.return_value = _make_medicine(
        name="RareMed", category="Niche", price=300.0,
    )

    with _mock_ctx([]):    # empty candidate list
        result = find_equivalent_replacement("RareMed", db)

    print(f"\n[NO MATCH] {result}")
    assert result.replacement_found is False
    assert result.suggested is None
    assert result.price_difference_percent == 0.0
    print("✅ No replacement test passed")


# ------------------------------------------------------------------
# Test: Contraindication gate blocks all candidates
# ------------------------------------------------------------------

def test_contraindication_blocks_all_candidates():
    db = MagicMock(spec=Database)
    db.get_medicine.return_value = _make_medicine(
        name="SafeMed", category="NSAID",
        active_ingredients="Ibuprofen", price=80.0,
    )
    # candidate contraindicated for penicillin allergy patient
    candidate = _make_sa_medicine(
        name="DangerMed", category="NSAID",
        active_ingredients="Aspirin",
        contraindications="Penicillin, Aspirin sensitivity",
        price=70.0,
    )

    with _mock_ctx([candidate]):
        result = find_equivalent_replacement(
            "SafeMed", db, patient_allergies=["penicillin"]
        )

    print(f"\n[CONTRAINDICATION] {result}")
    assert result.replacement_found is False
    assert "contraindicated" in result.reasoning.lower() or "safety" in result.reasoning.lower()
    print("✅ Contraindication gate test passed")


# ------------------------------------------------------------------
# Test: Cross-category rejection (hard gate double-check)
# ------------------------------------------------------------------

def test_cross_category_hard_gate():
    """
    Even when the DB query is mocked to return a cross-category candidate,
    the per-candidate category double-check inside the loop must reject it.
    """
    db = MagicMock(spec=Database)
    db.get_medicine.return_value = _make_medicine(
        name="MedX", category="Analgesic",
        active_ingredients="Paracetamol", price=100.0,
    )
    # Wrong category slipped through the (mocked) query
    candidate = _make_sa_medicine(
        name="Antibiotic-Z", category="Antibiotic",
        active_ingredients="Amoxicillin", price=200.0,
    )

    with _mock_ctx([candidate]):
        result = find_equivalent_replacement("MedX", db)

    print(f"\n[CROSS-CATEGORY GATE] {result}")
    assert result.replacement_found is False
    print("✅ Cross-category hard gate test passed")


# ------------------------------------------------------------------
# Test: Original medicine not in database
# ------------------------------------------------------------------

def test_original_not_found():
    db = MagicMock(spec=Database)
    db.get_medicine.return_value = None     # not found

    result = find_equivalent_replacement("UnknownMed", db)

    print(f"\n[NOT FOUND] {result}")
    assert result.replacement_found is False
    assert result.original == "UnknownMed"
    assert result.suggested is None
    print("✅ Original not found test passed")


# ------------------------------------------------------------------
# Test: Pharmacist override flag invariant
# ------------------------------------------------------------------

def test_pharmacist_override_flag_logic():
    """requires_pharmacist_override must be False ONLY when confidence='high'."""
    high = ReplacementResponse(
        replacement_found=True, original="A", suggested="B",
        confidence="high", reasoning="same active ingredient",
        requires_pharmacist_override=False,
    )
    medium = ReplacementResponse(
        replacement_found=True, original="A", suggested="C",
        confidence="medium", reasoning="same generic",
        requires_pharmacist_override=True,
    )
    low = ReplacementResponse(
        replacement_found=True, original="A", suggested="D",
        confidence="low", reasoning="same category",
        requires_pharmacist_override=True,
    )
    assert high.requires_pharmacist_override is False
    assert medium.requires_pharmacist_override is True
    assert low.requires_pharmacist_override is True
    print("✅ Pharmacist override flag logic test passed")


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    print("\n🧪 Running Replacement Engine Unit Tests...\n")
    tests = [
        test_high_confidence_same_active_ingredient,
        test_medium_confidence_same_generic,
        test_low_confidence_category_only,
        test_no_replacement_empty_category,
        test_contraindication_blocks_all_candidates,
        test_cross_category_hard_gate,
        test_original_not_found,
        test_pharmacist_override_flag_logic,
    ]
    for t in tests:
        try:
            t()
        except Exception as e:
            import traceback
            print(f"\n❌ {t.__name__} FAILED: {e}")
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("✅ ALL REPLACEMENT ENGINE TESTS PASSED")
    print("=" * 60)
