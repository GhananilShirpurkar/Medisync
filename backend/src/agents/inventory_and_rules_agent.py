"""
INVENTORY AGENT
===============
Agent 4: Stock checking and alternative suggestions

Responsibilities:
1. Check medicine availability in inventory
2. Suggest generic alternatives for out-of-stock items
3. Update stock status in state
4. Provide alternative recommendations
5. Calculate availability score
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

from src.state import PharmacyState, OrderItem
from src.database import Database
from src.agents.replacement_models import ReplacementResponse
from src.services.observability_service import trace_agent


# ------------------------------------------------------------------
# INVENTORY AGENT
# ------------------------------------------------------------------
@trace_agent("InventoryAndRulesAgent", agent_type="agent")
def inventory_agent(state: PharmacyState) -> PharmacyState:
    """
    Inventory Agent - Stock checking and alternatives.
    
    This agent checks medicine availability and suggests alternatives
    for out-of-stock items.
    
    Pipeline:
    1. Check each medicine in extracted_items
    2. Query database for stock levels
    3. Mark items as in_stock or out_of_stock
    4. Suggest generic alternatives for unavailable items
    5. Update state with availability info
    
    Args:
        state: Current pharmacy state
        
    Returns:
        Updated state with inventory information
        
    Decision Logic:
    - In stock: Proceed to fulfillment
    - Out of stock: Suggest alternatives
    - Partial stock: Offer what's available + alternatives
    """
    
    # Initialize reasoning trace
    reasoning_trace = []
    db = Database()
    
    # Step 1: Check if there are items to check
    if not state.extracted_items:
        reasoning_trace.append("❌ No items to check inventory")
        state.trace_metadata["inventory_agent"] = {
            "status": "no_items",
            "reasoning": reasoning_trace
        }
        return state
    
    reasoning_trace.append(f"✓ Checking inventory for {len(state.extracted_items)} item(s)")
    
    # Step 2: Check each medicine
    availability_results = []
    all_available = True
    partial_available = False
    alternatives_needed = []
    
    for item in state.extracted_items:
        medicine_data = db.get_medicine(item.medicine_name)
        
        if not medicine_data:
            # Medicine not found in database
            item.in_stock = False
            all_available = False
            alternatives_needed.append(item.medicine_name)
            
            availability_results.append({
                "medicine": item.medicine_name,
                "status": "not_found",
                "stock": 0,
                "requested": item.quantity,
                "message": "Medicine not found in inventory"
            })
            
            reasoning_trace.append(f"❌ {item.medicine_name}: Not found in inventory")
            
        elif medicine_data["stock"] < item.quantity:
            # Insufficient stock
            item.in_stock = False
            all_available = False
            
            if medicine_data["stock"] > 0:
                partial_available = True
                availability_results.append({
                    "medicine": item.medicine_name,
                    "status": "partial",
                    "stock": medicine_data["stock"],
                    "requested": item.quantity,
                    "message": f"Only {medicine_data['stock']} available, {item.quantity} requested",
                    "details": {
                        "dosage_form": medicine_data.get("dosage_form"),
                        "strength": medicine_data.get("strength"),
                        "active_ingredients": medicine_data.get("active_ingredients"),
                        "side_effects": medicine_data.get("side_effects")
                    }
                })
                reasoning_trace.append(f"⚠️  {item.medicine_name}: Partial stock ({medicine_data['stock']}/{item.quantity})")
            else:
                availability_results.append({
                    "medicine": item.medicine_name,
                    "status": "out_of_stock",
                    "stock": 0,
                    "requested": item.quantity,
                    "message": "Out of stock"
                })
                reasoning_trace.append(f"❌ {item.medicine_name}: Out of stock")
            
            alternatives_needed.append(item.medicine_name)
            
        else:
            # In stock
            item.in_stock = True
            
            availability_results.append({
                "medicine": item.medicine_name,
                "status": "available",
                "stock": medicine_data["stock"],
                "requested": item.quantity,
                "message": "In stock",
                "details": {
                    "dosage_form": medicine_data.get("dosage_form"),
                    "strength": medicine_data.get("strength"),
                    "active_ingredients": medicine_data.get("active_ingredients"),
                    "side_effects": medicine_data.get("side_effects")
                }
            })
            
            reasoning_trace.append(f"✓ {item.medicine_name}: In stock ({medicine_data['stock']} available)")
    
    # Step 3: Suggest alternatives for unavailable items
    alternatives = []
    
    if alternatives_needed:
        reasoning_trace.append(f"\n🔍 Finding equivalent replacement for {len(alternatives_needed)} item(s)")
        
        for medicine_name in alternatives_needed:
            replacement = find_equivalent_replacement(medicine_name, db)
            state.replacement_pending.append(replacement.model_dump())
            
            if replacement.replacement_found:
                alternatives.append({
                    "original": medicine_name,
                    "alternatives": [{
                        "name": replacement.suggested,
                        "confidence": replacement.confidence,
                        "reasoning": replacement.reasoning,
                        "price_difference_percent": replacement.price_difference_percent,
                        "requires_pharmacist_override": replacement.requires_pharmacist_override,
                    }]
                })
                override_tag = " ⚠️ (pharmacist override required)" if replacement.requires_pharmacist_override else ""
                reasoning_trace.append(f"  ✓ {medicine_name} → {replacement.suggested} [{replacement.confidence}]{override_tag}")
            else:
                reasoning_trace.append(f"  ⚠️  {medicine_name} → {replacement.reasoning}")
    
    # Step 4: Calculate availability score
    total_items = len(state.extracted_items)
    available_items = sum(1 for item in state.extracted_items if item.in_stock)
    availability_score = available_items / total_items if total_items > 0 else 0.0
    
    reasoning_trace.append(f"\n📊 Availability: {available_items}/{total_items} items ({availability_score*100:.0f}%)")
    
    # Step 5: Determine overall status
    if all_available:
        inventory_status = "all_available"
        reasoning_trace.append("✅ All items available - Ready for fulfillment")
    elif availability_score > 0:
        inventory_status = "partial_available"
        reasoning_trace.append("⚠️  Partial availability - Alternatives suggested")
    else:
        inventory_status = "none_available"
        reasoning_trace.append("❌ No items available - Check alternatives")
    
    # Step 6: Store metadata for tracing
    state.trace_metadata["inventory_agent"] = {
        "status": inventory_status,
        "availability_score": availability_score,
        "available_items": available_items,
        "total_items": total_items,
        "availability_results": availability_results,
        "alternatives": alternatives,
        "reasoning_trace": reasoning_trace,
        "check_timestamp": datetime.now().isoformat()
    }
    
    # Step 7: Log inventory summary
    print(f"\n{'='*60}")
    print(f"INVENTORY AGENT")
    print(f"{'='*60}")
    print(f"Status: {inventory_status}")
    print(f"Availability: {available_items}/{total_items} items ({availability_score*100:.0f}%)")
    
    if availability_results:
        print(f"\nInventory Check:")
        for result in availability_results:
            status_icon = "✓" if result["status"] == "available" else "⚠️" if result["status"] == "partial" else "❌"
            print(f"  {status_icon} {result['medicine']}: {result['message']}")
    
    if alternatives:
        print(f"\nAlternatives Suggested:")
        for alt_group in alternatives:
            print(f"  {alt_group['original']}:")
            for alt in alt_group['alternatives'][:3]:  # Show top 3
                print(f"    → {alt['name']} (₹{alt['price']}, Stock: {alt['stock']})")
    
    print(f"\nReasoning Trace:")
    for trace in reasoning_trace:
        print(f"  {trace}")
    
    print(f"{'='*60}\n")
    
    return state


# ------------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------------
def find_equivalent_replacement(
    medicine_name: str,
    db: Database,
    patient_allergies: Optional[List[str]] = None,
) -> ReplacementResponse:
    """
    Find ONE safe, clinically equivalent replacement for an out-of-stock medicine.

    Safety gates (applied in order, any failure eliminates a candidate):
      1. Hard gate  — candidate must share the *exact* therapeutic category.
      2. Allergy gate — candidate contraindications must not overlap with
                        patient_allergies (skipped when list is None / empty).

    Confidence scoring (first matching rule wins):
      high   → same active_ingredients (non-empty overlap) + same category
      medium → same generic_equivalent value + same category
      low    → same category only

    Args:
        medicine_name: Name of the out-of-stock medicine.
        db: Database instance.
        patient_allergies: Optional list of allergy strings from patient profile.

    Returns:
        ReplacementResponse — always exactly one object, never a list.
    """
    allergies = [a.lower().strip() for a in (patient_allergies or [])]

    def _no_replacement(reason: str) -> ReplacementResponse:
        return ReplacementResponse(
            replacement_found=False,
            original=medicine_name,
            suggested=None,
            confidence="low",
            reasoning=reason,
            price_difference_percent=0.0,
            requires_pharmacist_override=True,
        )

    # ── Fetch original ──────────────────────────────────────────────────────
    original = db.get_medicine(medicine_name)
    if not original:
        return _no_replacement("Original medicine not found in inventory — cannot determine category.")

    original_category: Optional[str] = original.get("category")
    if not original_category:
        return _no_replacement("Original medicine has no category assigned — cross-category guard cannot operate.")

    original_ingredients: List[str] = [
        i.strip().lower()
        for i in (original.get("active_ingredients") or "").split(",")
        if i.strip()
    ]
    original_generic: str = (original.get("generic_equivalent") or "").strip().lower()
    original_price: float = original.get("price") or 0.0

    # ── Query same-category candidates in stock ─────────────────────────────
    from src.db_config import get_db_context
    from src.models import Medicine  # SQLAlchemy model

    with get_db_context() as session:
        candidates = session.query(Medicine).filter(
            Medicine.category == original_category,
            Medicine.name != medicine_name,
            Medicine.stock > 0,
        ).all()

        if not candidates:
            return _no_replacement(
                f"No in-stock medicines found in category '{original_category}'."
            )

        # ── Score each candidate ────────────────────────────────────────────
        best_candidate = None
        best_confidence = ""   # tracks ranking: high > medium > low
        best_reasoning = ""

        for cand in candidates:
            # Gate 1: category already enforced by query — double-check
            if (cand.category or "").lower() != original_category.lower():
                continue

            # Gate 2: contraindication / allergy filter
            if allergies:
                cand_contraindications = [
                    c.strip().lower()
                    for c in (cand.contraindications or "").split(",")
                    if c.strip()
                ]
                if any(allergy in cand_contraindications for allergy in allergies):
                    continue  # skip — contraindicated for this patient

            # ── Determine confidence ────────────────────────────────────────
            cand_ingredients: List[str] = [
                i.strip().lower()
                for i in (cand.active_ingredients or "").split(",")
                if i.strip()
            ]
            cand_generic: str = (cand.generic_equivalent or "").strip().lower()

            if (
                original_ingredients
                and cand_ingredients
                and bool(set(original_ingredients) & set(cand_ingredients))
            ):
                confidence = "high"
                shared = set(original_ingredients) & set(cand_ingredients)
                reasoning = (
                    f"Same category ({original_category}), "
                    f"same active ingredient ({', '.join(shared)}), "
                    f"no contraindications."
                )
            elif original_generic and cand_generic and original_generic == cand_generic:
                confidence = "medium"
                reasoning = (
                    f"Same category ({original_category}), "
                    f"same generic equivalent ({cand_generic}), "
                    f"no contraindications."
                )
            else:
                confidence = "low"
                reasoning = (
                    f"Same category ({original_category}) only — "
                    f"active ingredient match unavailable. Pharmacist review required."
                )

            # Keep the highest-confidence candidate found so far
            rank = {"high": 3, "medium": 2, "low": 1}
            if best_candidate is None or rank[confidence] > rank[best_confidence]:
                best_candidate = cand
                best_confidence = confidence
                best_reasoning = reasoning

            # Short-circuit: can't do better than high
            if best_confidence == "high":
                break

        if best_candidate is None:
            return _no_replacement(
                f"All in-category candidates were contraindicated for this patient "
                f"or no candidates passed safety checks."
            )

        # ── Build response ──────────────────────────────────────────────────
        cand_price: float = best_candidate.price or 0.0
        price_diff_pct = (
            ((cand_price - original_price) / original_price * 100)
            if original_price > 0 else 0.0
        )

        return ReplacementResponse(
            replacement_found=True,
            original=medicine_name,
            suggested=best_candidate.name,
            suggested_price=cand_price,
            confidence=best_confidence,
            reasoning=best_reasoning,
            price_difference_percent=round(price_diff_pct, 2),
            requires_pharmacist_override=(best_confidence != "high"),
        )


def find_by_category(category: str, exclude_name: str, db: Database) -> List[Dict[str, Any]]:
    """
    Find medicines in the same category.
    
    Args:
        category: Medicine category
        exclude_name: Medicine name to exclude
        db: Database instance
        
    Returns:
        List of alternative medicines
    """
    from src.db_config import get_db_context
    from src.models import Medicine
    
    alternatives = []
    
    with get_db_context() as session:
        medicines = session.query(Medicine).filter(
            Medicine.category == category,
            Medicine.name != exclude_name,
            Medicine.stock > 0
        ).limit(10).all()
        
        for med in medicines:
            alternatives.append({
                "name": med.name,
                "category": med.category,
                "price": med.price,
                "stock": med.stock,
                "manufacturer": med.manufacturer,
                "match_type": "category"
            })
    
    return alternatives


def find_by_similar_name(base_name: str, db: Database) -> List[Dict[str, Any]]:
    """
    Find medicines with similar names (generic versions).
    
    Args:
        base_name: Base medicine name
        db: Database instance
        
    Returns:
        List of alternative medicines
    """
    from src.db_config import get_db_context
    from src.models import Medicine
    
    alternatives = []
    
    with get_db_context() as session:
        # Use LIKE for fuzzy matching
        medicines = session.query(Medicine).filter(
            Medicine.name.ilike(f"%{base_name}%"),
            Medicine.stock > 0
        ).limit(10).all()
        
        for med in medicines:
            alternatives.append({
                "name": med.name,
                "category": med.category,
                "price": med.price,
                "stock": med.stock,
                "manufacturer": med.manufacturer,
                "match_type": "similar_name"
            })
    
    return alternatives


def extract_base_name(medicine_name: str) -> str:
    """
    Extract base medicine name (remove dosage, brand info).
    
    Examples:
    - "Paracetamol 500mg" → "Paracetamol"
    - "Crocin (Paracetamol)" → "Paracetamol"
    - "Amoxicillin 250mg Capsules" → "Amoxicillin"
    
    Args:
        medicine_name: Full medicine name
        
    Returns:
        Base medicine name
    """
    import re
    
    # Remove dosage patterns (500mg, 10ml, etc.)
    name = re.sub(r'\d+\s*(mg|ml|g|mcg|iu)\b', '', medicine_name, flags=re.IGNORECASE)
    
    # Remove form patterns (tablet, capsule, syrup, etc.)
    name = re.sub(r'\b(tablet|capsule|syrup|injection|cream|ointment)s?\b', '', name, flags=re.IGNORECASE)
    
    # Remove parentheses and their contents
    name = re.sub(r'\([^)]*\)', '', name)
    
    # Clean up whitespace
    name = ' '.join(name.split())
    
    return name.strip()


def get_inventory_summary(state: PharmacyState) -> Dict[str, Any]:
    """
    Get a summary of inventory check results from state.
    
    Args:
        state: Pharmacy state with inventory metadata
        
    Returns:
        Dictionary with inventory summary
    """
    metadata = state.trace_metadata.get("inventory_agent", {})
    
    return {
        "status": metadata.get("status", "unknown"),
        "availability_score": metadata.get("availability_score", 0.0),
        "available_items": metadata.get("available_items", 0),
        "total_items": metadata.get("total_items", 0),
        "availability_results": metadata.get("availability_results", []),
        "alternatives": metadata.get("alternatives", [])
    }


def format_inventory_report(state: PharmacyState) -> str:
    """
    Format inventory results as a human-readable report.
    
    Args:
        state: Pharmacy state with inventory metadata
        
    Returns:
        Formatted report string
    """
    summary = get_inventory_summary(state)
    metadata = state.trace_metadata.get("inventory_agent", {})
    
    report = f"""
INVENTORY CHECK REPORT
{'='*60}

Status: {summary['status'].upper().replace('_', ' ')}
Availability: {summary['available_items']}/{summary['total_items']} items ({summary['availability_score']*100:.0f}%)

"""
    
    if summary['availability_results']:
        report += "Item Availability:\n"
        for result in summary['availability_results']:
            status_icon = "✓" if result["status"] == "available" else "⚠️" if result["status"] == "partial" else "❌"
            report += f"  {status_icon} {result['medicine']}: {result['message']}\n"
        report += "\n"
    
    if summary['alternatives']:
        report += "Suggested Alternatives:\n"
        for alt_group in summary['alternatives']:
            report += f"  {alt_group['original']}:\n"
            for alt in alt_group['alternatives'][:3]:
                report += f"    → {alt['name']} (₹{alt['price']}, Stock: {alt['stock']})\n"
        report += "\n"
    
    reasoning = metadata.get("reasoning_trace", [])
    if reasoning:
        report += "Reasoning Trace:\n"
        for trace in reasoning:
            report += f"  {trace}\n"
    
    report += f"\n{'='*60}"
    
    return report
