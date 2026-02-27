import sys
import os
import io
import contextlib

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.inventory_service import InventoryService
from src.database import Database, get_db_context
from src.models import Medicine

def test_smart_inventory():
    print("\n--- Testing Smart Inventory ---")
    
    db = Database()
    inventory_service = InventoryService()
    
    # 1. Setup Data
    # Create an Out-of-Stock Item, a Substitute, and a Complementary pair
    print("Setting up test data...")
    with get_db_context() as session:
        # Clear previous test data to avoid duplicates/conflicts
        session.query(Medicine).filter(Medicine.name.in_([
            "Test Antibiotic", "Test Probiotic", "Test OOS Drug", "Test Substitute"
        ])).delete(synchronize_session=False)
        
        # Test Antibiotic (In Stock)
        session.add(Medicine(
            name="Test Antibiotic", stock=10, price=100.0, 
            category="Antibiotic", generic_equivalent="Amoxicillin"
        ))
        
        # Test Probiotic (Recommendation)
        session.add(Medicine(
            name="Enterogermina", stock=50, price=50.0, 
            category="Probiotic"
        ))
        
        # Test OOS Drug
        session.add(Medicine(
            name="Test OOS Drug", stock=0, price=20.0, 
            category="Analgesic", generic_equivalent="Paracetamol"
        ))
        
        # Test Substitute (Available)
        session.add(Medicine(
            name="Test Substitute", stock=100, price=15.0, 
            category="Analgesic", generic_equivalent="Paracetamol"
        ))
        
        session.commit()
    
    # 2. Test Smart Substitution
    print("\n[Test 1] Smart Substitution")
    items = [{"name": "Test OOS Drug", "quantity": 1}]
    result = inventory_service.check_availability(items)
    
    item_result = result["items"][0]
    print(f"Requested: {item_result['medicine']}")
    print(f"Available: {item_result['available']}")
    
    if "alternatives" in item_result and item_result["alternatives"]:
        print(f"✅ Alternatives Found: {[alt['name'] for alt in item_result['alternatives']]}")
        assert "Test Substitute" in [alt['name'] for alt in item_result['alternatives']]
    else:
        print("❌ No alternatives found!")

    # 3. Test Dynamic Bundling
    print("\n[Test 2] Dynamic Bundling (Antibiotic -> Probiotic)")
    # Using real name Amoxicillin to trigger logic if hardcoded, or "Test Antibiotic" if flexible
    # The logic in inventory_service used hardcoded strings. Let's see.
    # Logic: antibiotics = ["amoxicillin", "azithromycin", "ciprofloxacin", "augmentin"]
    # So we should use "Amoxicillin" for the request to match the rule.
    
    # Ensure "Amoxicillin" exists or use it in the request even if not in DB (mock check deals with DB availability only for recommendation)
    # The item in cart needs to trigger the rule.
    items = [{"name": "Amoxicillin 500mg", "quantity": 1}] # Name contains "Amoxicillin"
    
    # We need "Amoxicillin 500mg" in DB for check_availability to not fail on 'not_found' 
    # but recommendations are separate.
    # Actually, check_availability processes items. If item not found, it sets available=False. 
    # But get_complementary_recommendations just looks at names in the list.
    
    result = inventory_service.check_availability(items)
    
    recommendations = result.get("recommendations", [])
    if recommendations:
        print(f"✅ Recommendations Found: {[rec['medicine'] for rec in recommendations]}")
        assert "Enterogermina" in [rec['medicine'] for rec in recommendations]
        print(f"   Reason: {recommendations[0]['reason']}")
    else:
        print("❌ No recommendations found!")

if __name__ == "__main__":
    try:
        test_smart_inventory()
    except Exception as e:
        print(f"Test Failed: {e}")
        import traceback
        traceback.print_exc()
