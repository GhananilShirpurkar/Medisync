"""
CONFIRMATION STORE
==================
In-memory TTL store for pending order confirmations.

Replaces the raw _confirmation_store dict in conversation.py with a
service class that enforces:
  - 5-minute TTL (entries silently expire)
  - UUID-based idempotency token (prevents double-execution)
  - Thread-safe-ish single-process semantics (no Redis needed in dev)

In production, swap the backing dict for Redis with SETEX/GETDEL.
"""

import time
import uuid
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

CONFIRMATION_TTL_SECONDS = 300  # 5 minutes


class ConfirmationStore:
    """
    In-process store for pending order confirmations.

    Lifecycle of an entry:
      create() → get() / is_pending() → consume() or cancel()

    Expired entries are lazily evicted on every read.
    """

    def __init__(self) -> None:
        # { session_id: { token, expires_at, pending_pharmacy_state, replacement_info } }
        self._store: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def create(
        self,
        session_id: str,
        state_dict: Dict[str, Any],
        replacement_info: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Open a new confirmation gate for session_id.

        Replaces any existing (possibly expired) entry for the session.

        Args:
            session_id: Conversation session identifier.
            state_dict:  PharmacyState.model_dump() snapshot to execute on YES.
            replacement_info: Optional replacement summary dict for message rendering.

        Returns:
            Opaque confirmation token (UUID4 string).
        """
        token = str(uuid.uuid4())
        self._store[session_id] = {
            "token": token,
            "expires_at": time.time() + CONFIRMATION_TTL_SECONDS,
            "pending_pharmacy_state": state_dict,
            "replacement_info": replacement_info,
        }
        logger.info(
            "Confirmation gate opened for session=%s token=%s ttl=%ds",
            session_id, token, CONFIRMATION_TTL_SECONDS,
        )
        return token

    def cancel(self, session_id: str) -> None:
        """Remove pending confirmation without executing fulfillment."""
        self._store.pop(session_id, None)
        logger.info("Confirmation cancelled for session=%s", session_id)

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def is_pending(self, session_id: str) -> bool:
        """Return True if a non-expired confirmation is waiting."""
        entry = self._get_live(session_id)
        return entry is not None

    def get_pending(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Return the live entry dict, or None if absent/expired."""
        return self._get_live(session_id)

    def get(self, session_id: str, token: str) -> Optional[Dict[str, Any]]:
        """
        Look up entry by session_id + token.

        Returns the entry dict on match, None if expired or token mismatch.
        """
        entry = self._get_live(session_id)
        if entry is None:
            return None
        if entry["token"] != token:
            logger.warning(
                "Token mismatch for session=%s (expected %s, got %s)",
                session_id, entry["token"], token,
            )
            return None
        return entry

    def consume(self, session_id: str, token: str) -> Optional[Dict[str, Any]]:
        """
        Atomically validate + remove entry (idempotent: second call returns None).

        Args:
            session_id: Session to consume.
            token:      Must match the token issued at create() time.

        Returns:
            Entry dict on first call, None on subsequent calls or mismatch/expiry.
        """
        entry = self.get(session_id, token)
        if entry is None:
            return None
        self._store.pop(session_id, None)
        logger.info(
            "Confirmation consumed for session=%s token=%s", session_id, token
        )
        return entry

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_live(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Return entry if present and not expired; evict stale entries."""
        entry = self._store.get(session_id)
        if entry is None:
            return None
        if time.time() > entry["expires_at"]:
            self._store.pop(session_id, None)
            logger.info(
                "Confirmation expired and evicted for session=%s", session_id
            )
            return None
        return entry


# ---------------------------------------------------------------------------
# Module-level singleton — import this everywhere
# ---------------------------------------------------------------------------
confirmation_store = ConfirmationStore()
