"""
AGENT DEFINITIONS
=================
Each agent is a PURE transformation:
    PharmacyState -> PharmacyState
"""

from typing import List

from src.state import PharmacyState, OrderItem
from src.database import Database
from src.services import call_llm_extract, call_llm_safety_check, call_llm_parse_prescription
from src.services.ocr_service import extract_prescription_text
from src.services.observability_service import trace_agent

# Import medical validation agent
from src.agents.medical_validator_agent import medical_validation_agent


# Shared database instance
db = Database()


# -------------------------------------------------------------------
# FRONT DESK AGENT
# -------------------------------------------------------------------
def front_desk_agent(state: PharmacyState) -> PharmacyState:
    extraction = call_llm_extract(state.user_message)

    if not extraction:
        state.intent = "unknown"
        state.language = "en"
        state.extracted_items = []
        return state

    # ---- intent & language ----
    state.intent = extraction.get("intent", "unknown")
    state.language = extraction.get("language", "en")

    # ---- items → OrderItem ----
    items = []
    for item in extraction.get("items", []):
        items.append(
            OrderItem(
                medicine_name=item.get("medicine_name"),
                dosage=item.get("dosage"),
                quantity=item.get("quantity", 1),
            )
        )

    state.extracted_items = items
    return state


# -------------------------------------------------------------------
# VISION AGENT
# -------------------------------------------------------------------
@trace_agent("VisionAgent", agent_type="agent")
def vision_agent(state: PharmacyState, image_path: str, use_mock: bool = False) -> PharmacyState:
    """
    Vision Agent: Extract and parse prescription from image.
    
    Responsibilities:
    1. Extract text from prescription image using OCR
    2. Parse raw text into structured data using LLM
    3. Populate state with prescription details
    4. Set confidence scores and flags
    
    Args:
        state: Current pharmacy state
        image_path: Path to prescription image
        use_mock: If True, use mock data when OCR engines not available (for testing)
        
    Returns:
        Updated state with prescription data
        
    Decision States:
    - High confidence (>90%): Mark prescription_verified = True
    - Medium confidence (70-90%): Mark for review
    - Low confidence (<70%): Request re-capture
    """
    
    # Step 1: Extract text using OCR
    ocr_result = extract_prescription_text(image_path, use_mock=use_mock)
    
    if not ocr_result.get("success"):
        state.prescription_verified = False
        state.safety_issues.append(f"OCR failed: {ocr_result.get('error', 'Unknown error')}")
        return state
    
    raw_text = ocr_result.get("raw_text", "")
    ocr_confidence = ocr_result.get("confidence", 0.0)
    
    # Step 2: Parse text using LLM for intelligent extraction
    parsed_data = call_llm_parse_prescription(raw_text)
    
    # Step 3: Extract medicines and create OrderItems
    items = []
    for medicine in parsed_data.get("medicines", []):
        items.append(
            OrderItem(
                medicine_name=medicine.get("name", "Unknown"),
                dosage=medicine.get("dosage"),
                quantity=1  # Default quantity, can be updated later
            )
        )
    
    state.extracted_items = items
    
    # Step 4: Calculate overall confidence
    llm_confidence = parsed_data.get("confidence", {}).get("overall", 0.0)
    overall_confidence = (ocr_confidence + llm_confidence) / 2
    
    # Step 5: Set prescription verification status based on confidence
    if overall_confidence >= 0.9:
        state.prescription_verified = True
        state.prescription_uploaded = True
    elif overall_confidence >= 0.7:
        state.prescription_uploaded = True
        state.prescription_verified = False
        state.safety_issues.append(
            f"Medium confidence ({overall_confidence:.2f}) - Requires pharmacist review"
        )
    else:
        state.prescription_uploaded = False
        state.prescription_verified = False
        state.safety_issues.append(
            f"Low confidence ({overall_confidence:.2f}) - Please re-capture prescription"
        )
    
    # Step 6: Store metadata for tracing
    state.trace_metadata["vision_agent"] = {
        "ocr_confidence": ocr_confidence,
        "llm_confidence": llm_confidence,
        "overall_confidence": overall_confidence,
        "patient_name": parsed_data.get("patient_name"),
        "doctor_name": parsed_data.get("doctor_name"),
        "date": parsed_data.get("date"),
        "signature_present": parsed_data.get("signature_present"),
        "notes": parsed_data.get("notes"),
        "medicines_count": len(items)
    }
    
    # Step 7: Add any notes from LLM to safety issues
    if parsed_data.get("notes"):
        state.safety_issues.append(f"Note: {parsed_data['notes']}")
    
    return state



# -------------------------------------------------------------------
# PHARMACIST AGENT
# -------------------------------------------------------------------
def pharmacist_agent(state: PharmacyState) -> PharmacyState:
    safety_issues: List[str] = []

    for item in state.extracted_items:
        record = db.get_medicine(item.medicine_name)

        if record is None:
            safety_issues.append(f"{item.medicine_name} not found")
            item.in_stock = False
            continue

        item.in_stock = record["stock"] >= item.quantity
        item.requires_prescription = bool(record["requires_prescription"])

        if not item.in_stock:
            safety_issues.append(f"{item.medicine_name} out of stock")

        if item.requires_prescription and not state.prescription_verified:
            safety_issues.append(
                f"{item.medicine_name} requires prescription"
            )

    safety_issues.extend(
        call_llm_safety_check(state.extracted_items)
    )

    state.safety_issues = safety_issues
    state.pharmacist_decision = "approved" if not safety_issues else "rejected"

    return state


# -------------------------------------------------------------------
# FULFILLMENT AGENT
# -------------------------------------------------------------------
def fulfillment_agent(state: PharmacyState) -> PharmacyState:
    if state.pharmacist_decision != "approved":
        return state

    state.order_id = db.create_order(
        user_id=state.user_id,
        items=state.extracted_items,
    )

    for item in state.extracted_items:
        db.decrement_stock(item.medicine_name, item.quantity)

    state.order_status = "fulfilled"
    state.notifications_sent = True

    return state


# -------------------------------------------------------------------
# EXPORTS
# -------------------------------------------------------------------
# Export all agents for backward compatibility
__all__ = [
    "front_desk_agent",
    "vision_agent",
    "medical_validation_agent",
]
