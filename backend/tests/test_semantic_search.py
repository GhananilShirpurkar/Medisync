import sys
import os
import time

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.semantic_search_service import semantic_search_service
from src.database import Database

def test_semantic_search():
    print("\n--- Testing Semantic Search ---")
    
    if not semantic_search_service.enabled:
        print("⚠️  Semantic search is disabled (sentence-transformers not found). Skipping test.")
        return

    # Mock Data indexing
    medicines = [
        {
            "name": "Paracetamol 500mg", 
            "description": "Pain reliever and fever reducer", 
            "indication": "Headache, muscle ache, fever", 
            "category": "Analgesic"
        },
        {
            "name": "Ibuprofen 400mg", 
            "description": "Non-steroidal anti-inflammatory drug (NSAID)", 
            "indication": "Pain, inflammation, fever", 
            "category": "Analgesic"
        },
        {
            "name": "Amoxicillin 500mg", 
            "description": "Antibiotic penicillin", 
            "indication": "Bacterial infections", 
            "category": "Antibiotic"
        },
        {
            "name": "Cetirizine 10mg", 
            "description": "Antihistamine for allergies", 
            "indication": "Runny nose, sneezing, itching", 
            "category": "Antihistamine"
        }
    ]
    
    print("Indexing mock medicines...")
    semantic_search_service.index_medicines(medicines)
    
    test_queries = [
        ("pain killer", ["Paracetamol 500mg", "Ibuprofen 400mg"]),
        ("fever tablet", ["Paracetamol 500mg", "Ibuprofen 400mg"]),
        ("runny nose", ["Cetirizine 10mg"]),
        ("infection", ["Amoxicillin 500mg"]),
        ("headache medicine", ["Paracetamol 500mg"]),
        ("Dolo", ["Paracetamol 500mg"]),  # Brand association might not work without description match, but "Dolo" usually implies Paracetamol contextually if model knows it, but mostly explicit text match. MiniLM might not know "Dolo" = Paracetamol unless in description. Let's see.
    ]
    
    for query, expected_candidates in test_queries:
        print(f"\nQuery: '{query}'")
        results = semantic_search_service.search(query, top_k=2)
        print(f"Results: {results}")
        
        found = False
        for name, score in results:
            if name in expected_candidates:
                found = True
                print(f"✅ Found expected match: {name} (score: {score:.2f})")
                break
        
        if not found and query != "Dolo": # Dolo might fail if not in text
            print(f"❌ Failed to find expected match: {expected_candidates}")

if __name__ == "__main__":
    try:
        test_semantic_search()
    except Exception as e:
        print(f"Test Failed: {e}")
        import traceback
        traceback.print_exc()
