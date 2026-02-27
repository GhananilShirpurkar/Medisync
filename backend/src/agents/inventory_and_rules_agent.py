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
        reasoning_trace.append(f"\n🔍 Finding alternatives for {len(alternatives_needed)} item(s)")
        
        for medicine_name in alternatives_needed:
            suggested_alternatives = find_alternatives(medicine_name, db)
            
            if suggested_alternatives:
                alternatives.append({
                    "original": medicine_name,
                    "alternatives": suggested_alternatives
                })
                
                alt_names = [alt["name"] for alt in suggested_alternatives]
                reasoning_trace.append(f"  ✓ {medicine_name} → {', '.join(alt_names[:3])}")
            else:
                reasoning_trace.append(f"  ⚠️  {medicine_name} → No alternatives found")
    
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
def find_alternatives(medicine_name: str, db: Database) -> List[Dict[str, Any]]:
    """
    Find alternative medicines for a given medicine.
    
    Strategy:
    1. Look for generic versions (same active ingredient)
    2. Look for same category medicines
    3. Look for similar names (fuzzy matching)
    
    Args:
        medicine_name: Name of medicine to find alternatives for
        db: Database instance
        
    Returns:
        List of alternative medicine dictionaries
    """
    alternatives = []
    
    # Get the original medicine info
    original = db.get_medicine(medicine_name)
    
    # Strategy 1: Find medicines in same category (if original found)
    if original and original.get("category"):
        category_alternatives = find_by_category(
            original["category"],
            exclude_name=medicine_name,
            db=db
        )
        alternatives.extend(category_alternatives)
    
    # Strategy 2: Find by similar name (generic versions)
    # Extract base name (e.g., "Paracetamol" from "Paracetamol 500mg")
    base_name = extract_base_name(medicine_name)
    if base_name != medicine_name:
        similar_alternatives = find_by_similar_name(base_name, db)
        alternatives.extend(similar_alternatives)
    
    # Remove duplicates and sort by availability and price
    seen = set()
    unique_alternatives = []
    
    for alt in alternatives:
        if alt["name"] not in seen and alt["stock"] > 0:
            seen.add(alt["name"])
            unique_alternatives.append(alt)
    
    # Sort by stock (descending) then price (ascending)
    unique_alternatives.sort(key=lambda x: (-x["stock"], x["price"]))
    
    return unique_alternatives[:5]  # Return top 5 alternatives


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
