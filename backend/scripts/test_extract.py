import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.routes.conversation import _extract_medicine_name
from src.database import Database

db = Database()
print("Extracting from: 'i have headache + stomach ache and i think i need paracitamol'")
extracted = _extract_medicine_name("i have headache + stomach ache and i think i need paracitamol")
print(f"Extracted string: '{extracted}'")

if extracted:
    result = db.get_medicine(extracted)
    if result:
        print(f"DB matched: {result['name']} (fuzzy: {result.get('fuzzy_match')}, sem: {result.get('semantic_match')})")
    else:
        print("DB did not match anything")
