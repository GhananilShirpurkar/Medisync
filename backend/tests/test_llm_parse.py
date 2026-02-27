"""Test LLM prescription parsing directly"""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

print(f"API Key: {os.getenv('GEMINI_API_KEY')[:20]}...")

from src.services.llm_service import call_llm_parse_prescription

raw_text = """
Dr. John Smith, MD
Medical Registration: 12345

Patient Name: Jane Doe
Date: 15/01/2024

Rx:
1. Paracetamol 500mg - 1 tablet 3 times daily for 5 days
2. Amoxicillin 250mg - 1 capsule 2 times daily for 7 days

Signature: Dr. John Smith
"""

print("\n🧪 Testing LLM prescription parsing...")
result = call_llm_parse_prescription(raw_text)

print(f"\nResult:")
print(f"  Patient: {result.get('patient_name')}")
print(f"  Doctor: {result.get('doctor_name')}")
print(f"  Medicines: {len(result.get('medicines', []))}")
for med in result.get('medicines', []):
    print(f"    - {med.get('name')} {med.get('dosage')}")
print(f"  Confidence: {result.get('confidence', {}).get('overall', 0)}")
print(f"  Notes: {result.get('notes')}")
