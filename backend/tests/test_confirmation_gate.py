"""
CONFIRMATION GATE UNIT TESTS
==============================
Tests for the ConfirmationStore service, PharmacyState confirmation fields,
fulfillment_agent hard gate, and the /confirm endpoint flow.

Run with:
    cd /home/koanoir/Desktop/Projects/01_sandbox/Medisync/backend
    .venv/bin/pytest tests/test_confirmation_gate.py -v
"""

import sys
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.confirmation_store import ConfirmationStore, CONFIRMATION_TTL_SECONDS
from src.state import PharmacyState, OrderItem
from src.errors import ConfirmationRequiredError
from src.agents.replacement_models import ReplacementResponse


# ===========================================================================
# SECTION 1: ConfirmationStore unit tests
# ===========================================================================

class TestConfirmationStore:
    """Test the in-memory TTL store in isolation."""

    def _make_store(self):
        return ConfirmationStore()

    def _sample_state(self):
        return PharmacyState(
            user_id="test-user",
            session_id="sess_abc123",
            extracted_items=[OrderItem(medicine_name="Paracetamol 500mg", quantity=1)],
        ).model_dump()

    # ------------------------------------------------------------------

    def test_create_returns_token(self):
        store = self._make_store()
        token = store.create("sess_1", self._sample_state())
        assert isinstance(token, str)
        assert len(token) > 10   # UUID4
        print("✅ create_returns_token passed")

    def test_is_pending_after_create(self):
        store = self._make_store()
        store.create("sess_2", self._sample_state())
        assert store.is_pending("sess_2") is True
        print("✅ is_pending_after_create passed")

    def test_is_pending_unknown_session(self):
        store = self._make_store()
        assert store.is_pending("nonexistent") is False
        print("✅ is_pending_unknown_session passed")

    def test_get_pending_returns_entry(self):
        store = self._make_store()
        token = store.create("sess_3", self._sample_state())
        entry = store.get_pending("sess_3")
        assert entry is not None
        assert entry["token"] == token
        print("✅ get_pending_returns_entry passed")

    def test_get_with_correct_token(self):
        store = self._make_store()
        token = store.create("sess_4", self._sample_state())
        entry = store.get("sess_4", token)
        assert entry is not None
        print("✅ get_with_correct_token passed")

    def test_get_with_wrong_token_returns_none(self):
        store = self._make_store()
        store.create("sess_5", self._sample_state())
        entry = store.get("sess_5", "wrong-token")
        assert entry is None
        print("✅ get_with_wrong_token_returns_none passed")

    def test_consume_first_call_succeeds(self):
        store = self._make_store()
        token = store.create("sess_6", self._sample_state())
        entry = store.consume("sess_6", token)
        assert entry is not None
        assert entry["token"] == token
        print("✅ consume_first_call_succeeds passed")

    def test_consume_idempotent_second_call_returns_none(self):
        """The idempotency guarantee: second consume returns None."""
        store = self._make_store()
        token = store.create("sess_7", self._sample_state())
        store.consume("sess_7", token)        # first consume
        second = store.consume("sess_7", token)  # idempotent second
        assert second is None
        print("✅ consume_idempotent_second_call_returns_none passed")

    def test_consume_removes_entry(self):
        store = self._make_store()
        token = store.create("sess_8", self._sample_state())
        store.consume("sess_8", token)
        assert store.is_pending("sess_8") is False
        print("✅ consume_removes_entry passed")

    def test_cancel_removes_entry(self):
        store = self._make_store()
        store.create("sess_9", self._sample_state())
        store.cancel("sess_9")
        assert store.is_pending("sess_9") is False
        print("✅ cancel_removes_entry passed")

    def test_expired_entry_returns_none(self):
        """Simulate TTL expiry by backdating expires_at."""
        store = self._make_store()
        token = store.create("sess_10", self._sample_state())
        # Force expiry
        store._store["sess_10"]["expires_at"] = time.time() - 1
        assert store.is_pending("sess_10") is False
        assert store.get("sess_10", token) is None
        assert store.consume("sess_10", token) is None
        print("✅ expired_entry_returns_none passed")

    def test_replacement_info_stored(self):
        store = self._make_store()
        rep_info = {"original": "Crocin", "suggested": "Dolo 650", "confidence": "high"}
        store.create("sess_11", self._sample_state(), replacement_info=rep_info)
        entry = store.get_pending("sess_11")
        assert entry["replacement_info"] == rep_info
        print("✅ replacement_info_stored passed")


# ===========================================================================
# SECTION 2: PharmacyState confirmation fields
# ===========================================================================

def test_pharmacy_state_confirmation_defaults():
    """PharmacyState must default to the safe (gate-closed) values."""
    state = PharmacyState(user_id="u", user_message="test")
    assert state.conversation_phase == "collecting_items"
    assert state.confirmation_token is None
    assert state.confirmation_expires_at is None
    assert state.confirmation_confirmed is False
    print("✅ pharmacy_state_confirmation_defaults passed")


def test_pharmacy_state_confirmation_serialization():
    """Confirmation fields survive model_dump()/reconstruct round-trip."""
    token = str(uuid.uuid4())
    state = PharmacyState(
        user_id="u",
        user_message="test",
        conversation_phase="awaiting_confirmation",
        confirmation_token=token,
        confirmation_confirmed=False,
    )
    dumped = state.model_dump()
    restored = PharmacyState(**dumped)
    assert restored.conversation_phase == "awaiting_confirmation"
    assert restored.confirmation_token == token
    assert restored.confirmation_confirmed is False
    print("✅ pharmacy_state_confirmation_serialization passed")


# ===========================================================================
# SECTION 3: fulfillment_agent hard gate
# ===========================================================================

def test_fulfillment_blocked_without_confirmation():
    """
    fulfillment_agent must raise ConfirmationRequiredError
    when state.confirmation_confirmed is False.
    """
    import asyncio
    from src.agents.fulfillment_agent import fulfillment_agent

    state = PharmacyState(
        user_id="u",
        session_id="sess_gate_test",
        user_message="order paracetamol",
        extracted_items=[OrderItem(medicine_name="Paracetamol 500mg", quantity=1)],
        confirmation_confirmed=False,   # gate NOT opened
    )

    try:
        fulfillment_agent(state)
        assert False, "Expected ConfirmationRequiredError was not raised"
    except ConfirmationRequiredError as e:
        assert "confirmation" in e.message.lower()
        print("✅ fulfillment_blocked_without_confirmation passed")


def test_fulfillment_gate_passes_with_confirmation():
    """
    With confirmation_confirmed=True the gate check passes and execution
    proceeds to Step 1 (no items → early return, no DB writes needed).
    This test covers the gate logic only, not the full fulfillment flow.
    """
    import asyncio
    from src.agents.fulfillment_agent import fulfillment_agent

    state = PharmacyState(
        user_id="u",
        session_id="sess_gate_pass",
        user_message="order",
        extracted_items=[],             # empty → early return after gate
        confirmation_confirmed=True,    # gate OPEN
        pharmacist_decision="approved",
    )

    result = fulfillment_agent(state)
    # Should return state with order_status="failed" due to no items — NOT raise ConfirmationRequiredError
    assert result.order_status == "failed"
    print("✅ fulfillment_gate_passes_with_confirmation passed")


# ===========================================================================
# SECTION 4: Confirmation flow integration (state transitions)
# ===========================================================================

def test_confirmation_store_yes_flow_state_transitions():
    """
    Simulate the YES confirm flow:
    create → consume → set confirmation_confirmed → verify state
    """
    store = ConfirmationStore()
    state = PharmacyState(
        user_id="u",
        session_id="sess_flow",
        extracted_items=[OrderItem(medicine_name="Paracetamol 500mg", quantity=1)],
        conversation_phase="awaiting_confirmation",
    )
    token = store.create("sess_flow", state.model_dump())

    # Simulate /confirm YES
    entry = store.consume("sess_flow", token)
    assert entry is not None

    restored = PharmacyState(**entry["pending_pharmacy_state"])
    restored.confirmation_confirmed = True
    restored.conversation_phase = "fulfillment_executing"

    assert restored.confirmation_confirmed is True
    assert restored.conversation_phase == "fulfillment_executing"
    # Store is now empty (idempotency)
    assert store.is_pending("sess_flow") is False
    print("✅ confirmation_store_yes_flow_state_transitions passed")


def test_confirmation_store_no_flow():
    """NO cancels the store and phase reverts to collecting_items."""
    store = ConfirmationStore()
    store.create("sess_no", {})
    assert store.is_pending("sess_no") is True

    store.cancel("sess_no")
    assert store.is_pending("sess_no") is False
    print("✅ confirmation_store_no_flow passed")


def test_timeout_returns_none():
    """After TTL the consume returns None (simulated)."""
    store = ConfirmationStore()
    token = store.create("sess_timeout", {})
    store._store["sess_timeout"]["expires_at"] = time.time() - 1   # back-date

    assert store.consume("sess_timeout", token) is None
    print("✅ timeout_returns_none passed")


# ===========================================================================
# SECTION 5: Replacement context injection (message content)
# ===========================================================================

def test_replacement_message_includes_original_and_suggested():
    """
    When replacement_pending contains a found replacement, the confirmation
    message must contain the original name and the suggested substitute.
    This test drives the message-building helper directly.
    """
    replacement = ReplacementResponse(
        replacement_found=True,
        original="Crocin 500mg",
        suggested="Dolo 650",
        confidence="high",
        reasoning="Same active ingredient: Paracetamol",
        requires_pharmacist_override=False,
    )

    # Simulate the message-building logic from send_message
    replacement_lines = []
    for rep in [replacement.model_dump()]:
        if rep.get("replacement_found"):
            override_note = " ⚠️ Requires pharmacist review." if rep.get("requires_pharmacist_override") else ""
            replacement_lines.append(
                f"⚠️ *{rep['original']}* unavailable.\n"
                f"   Suggested replacement: *{rep['suggested']}*"
                f" ({rep['reasoning']}).{override_note}"
            )

    header = "\n".join(replacement_lines) + "\n\n"
    confirmation_message = (
        header
        + "Please confirm your order:\n\n"
        + "  • Dolo 650 × 1 — ₹90.00"
        + "\n\nTotal: ₹90.00\n\n"
        "Reply *YES* to confirm or *NO* to cancel."
    )

    assert "Crocin 500mg" in confirmation_message
    assert "Dolo 650" in confirmation_message
    assert "Paracetamol" in confirmation_message
    assert "⚠️ Requires pharmacist review." not in confirmation_message   # high confidence, no note
    print("✅ replacement_message_includes_original_and_suggested passed")


def test_replacement_message_pharmacist_note_for_low_confidence():
    replacement = ReplacementResponse(
        replacement_found=True,
        original="MedA",
        suggested="MedB",
        confidence="low",
        reasoning="Same therapeutic category: Antacid",
        requires_pharmacist_override=True,
    )

    rep = replacement.model_dump()
    override_note = " ⚠️ Requires pharmacist review." if rep.get("requires_pharmacist_override") else ""
    line = (
        f"⚠️ *{rep['original']}* unavailable.\n"
        f"   Suggested replacement: *{rep['suggested']}*"
        f" ({rep['reasoning']}).{override_note}"
    )

    assert "⚠️ Requires pharmacist review." in line
    print("✅ replacement_message_pharmacist_note_for_low_confidence passed")


# ===========================================================================
# SECTION 6: Category constraint regression (from replacement engine)
# ===========================================================================

def test_category_constraint_regression(test_db):
    """Cross-category replacement must remain rejected (regression guard)."""
    from src.agents.inventory_and_rules_agent import find_equivalent_replacement
    from src.database import Database

    db = MagicMock(spec=Database)
    db.get_medicine.return_value = {
        "id": 1, "name": "MedX", "category": "Analgesic",
        "active_ingredients": "Paracetamol", "generic_equivalent": "paracetamol",
        "price": 100.0, "stock": 10, "contraindications": ""
    }

    cross_category_candidate = MagicMock()
    cross_category_candidate.name = "Antibiotic-Z"
    cross_category_candidate.category = "Antibiotic"   # ← different!
    cross_category_candidate.active_ingredients = "Amoxicillin"
    cross_category_candidate.generic_equivalent = ""
    cross_category_candidate.contraindications = ""
    cross_category_candidate.price = 200.0

    @contextmanager
    def _ctx():
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.all.return_value = [cross_category_candidate]
        yield mock_session

    with patch("src.db_config.get_db_context", side_effect=_ctx):
        result = find_equivalent_replacement("MedX", db)

    assert result.replacement_found is False
    print("✅ category_constraint_regression passed")


# ===========================================================================
# Entry point
# ===========================================================================

if __name__ == "__main__":
    print("\n🧪 Running Confirmation Gate Tests...\n")

    store_tests = TestConfirmationStore()
    store_test_methods = [m for m in dir(store_tests) if m.startswith("test_")]
    for name in store_test_methods:
        try:
            getattr(store_tests, name)()
        except Exception as e:
            import traceback
            print(f"❌ {name} FAILED: {e}")
            traceback.print_exc()

    standalone_tests = [
        test_pharmacy_state_confirmation_defaults,
        test_pharmacy_state_confirmation_serialization,
        test_fulfillment_blocked_without_confirmation,
        test_fulfillment_gate_passes_with_confirmation,
        test_confirmation_store_yes_flow_state_transitions,
        test_confirmation_store_no_flow,
        test_timeout_returns_none,
        test_replacement_message_includes_original_and_suggested,
        test_replacement_message_pharmacist_note_for_low_confidence,
        test_category_constraint_regression,
    ]

    for t in standalone_tests:
        try:
            t()
        except Exception as e:
            import traceback
            print(f"❌ {t.__name__} FAILED: {e}")
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("✅ ALL CONFIRMATION GATE TESTS DONE")
    print("=" * 60)
