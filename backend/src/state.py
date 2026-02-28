from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from src.clinical_models import ClinicalContext


# ============================================================
# DOMAIN MODELS
# ============================================================

class OrderItem(BaseModel):
    """
    A single medicine request extracted from user input.

    Owned by:
    - FrontDesk (extraction)
    - Pharmacist (validation)
    - Fulfillment (inventory + order)
    """

    medicine_name: str
    dosage: Optional[str] = None          # e.g. "500mg"
    quantity: int = 1

    # Filled later by downstream agents
    requires_prescription: Optional[bool] = None
    in_stock: Optional[bool] = None
    price: Optional[float] = None


# ============================================================
# GLOBAL SHARED STATE (LANGGRAPH MEMORY)
# ============================================================

class PharmacyState(BaseModel):
    """
    GLOBAL SHARED STATE
    -------------------
    This object is passed between all LangGraph nodes.

    Rules:
    - Agents may ONLY write fields defined here
    - Services NEVER touch this directly
    - This is the system contract
    """

    # --------------------------------------------------------
    # Conversation Context
    # --------------------------------------------------------
    user_id: Optional[str] = None
    session_id: Optional[str] = None        # Unique session ID for event tracking
    whatsapp_phone: Optional[str] = None    # For WhatsApp notifications
    user_message: Optional[str] = None
    language: Optional[str] = "en"         # en | hi | mixed
    intent: Optional[str] = None           # purchase | refill | inquiry | unknown

    # --------------------------------------------------------
    # Conversation Phase (Pre-Order Orchestration)
    # --------------------------------------------------------
    # (conversation_phase is defined under Confirmation Gate below)

    clarified_symptoms: Optional[str] = None
    last_medicine_discussed: Optional[str] = None
    last_recommendations: List[str] = Field(default_factory=list)
    
    # --------------------------------------------------------
    # Order Understanding (from FrontDesk)
    # --------------------------------------------------------
    extracted_items: List[OrderItem] = Field(default_factory=list)

    # --------------------------------------------------------
    # Safety & Validation (Pharmacist)
    # --------------------------------------------------------
    prescription_uploaded: bool = False
    validation_status: str = "pending"  # pending | valid | invalid | needs_review
    safety_flags: List[str] = Field(default_factory=list)
    pharmacist_decision: Optional[str] = None  # approved | rejected | needs_review
    safety_issues: List[str] = Field(default_factory=list)
    
    # NEW: Multi-turn clinical context accumulator
    clinical_context: ClinicalContext = Field(default_factory=ClinicalContext)
    turn_count: int = 0
    reasoning_history: List[Dict] = Field(default_factory=list)
    
    # --------------------------------------------------------
    # Proactive Intelligence (future agents)
    # --------------------------------------------------------
    proactive_trigger: bool = False
    predicted_depletion_date: Optional[str] = None

    # --------------------------------------------------------
    # Replacement Engine (Inventory Agent)
    # --------------------------------------------------------
    replacement_pending: List[Dict[str, Any]] = Field(default_factory=list)
    # Each entry is a ReplacementResponse-shaped dict keyed by original medicine name.

    # --------------------------------------------------------
    # Confirmation Gate (State Machine)
    # --------------------------------------------------------
    conversation_phase: str = "collecting_items"
    # intake | clarifying | recommending | ordering | collecting_items
    # | replacement_suggested | awaiting_confirmation
    # | fulfillment_executing | info_query | completed

    confirmation_token: Optional[str] = None        # UUID4 — set when gate opens
    confirmation_expires_at: Optional[str] = None   # ISO-8601 UTC
    confirmation_confirmed: bool = False             # True only after explicit YES

    # --------------------------------------------------------
    # Fulfillment & Notifications
    # --------------------------------------------------------
    order_id: Optional[str] = None
    total_amount: float = 0.0               # Final order total
    order_status: Optional[str] = None      # created | fulfilled | failed
    notifications_sent: bool = False

    # --------------------------------------------------------
    # Payment & Notification Integration (Block 5)
    # --------------------------------------------------------
    payment_id: Optional[str] = None
    payment_status: Optional[str] = "pending" # pending | success | failed
    qr_code_data: Optional[str] = None
    payment_transaction_id: Optional[str] = None
    notification_sent_at: Optional[str] = None

    # --------------------------------------------------------
    # Meta / Debug / Tracing
    # --------------------------------------------------------
    trace_metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True
