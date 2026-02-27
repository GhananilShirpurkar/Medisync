#!/usr/bin/env python3
"""
MIGRATE & SEED: symptom_medicine_mapping
=========================================
Creates the symptom_medicine_mapping table if it doesn't exist,
then seeds it with comprehensive symptom→medicine mappings based
on the medicines already in the database.

Run from the backend/ directory:
    python scripts/migrate_symptom_mappings.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.db_config import get_db_context, engine
from src.models import Base, Medicine, SymptomMedicineMapping
from sqlalchemy import inspect, text


def create_table_if_missing():
    """Create symptom_medicine_mapping table if it doesn't exist."""
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    if "symptom_medicine_mapping" not in existing_tables:
        print("Creating symptom_medicine_mapping table...")
        Base.metadata.create_all(engine, tables=[SymptomMedicineMapping.__table__])
        print("✅ Table created.")
    else:
        print("✅ Table already exists.")


# Comprehensive symptom → medicine keyword mappings
# Format: { symptom_keyword: [(medicine_name_fragment, relevance_score), ...] }
SYMPTOM_SEED_DATA = {
    # Pain / Fever
    "headache":         [("Paracetamol", 1.0), ("Aspirin", 0.9), ("Ibuprofen", 0.85), ("Dolo", 0.9)],
    "fever":            [("Paracetamol", 1.0), ("Dolo", 0.95), ("Aspirin", 0.8), ("Ibuprofen", 0.75)],
    "mild fever":       [("Paracetamol", 1.0), ("Dolo", 0.95)],
    "body pain":        [("Ibuprofen", 1.0), ("Paracetamol", 0.9), ("Diclofenac", 0.85)],
    "pain":             [("Ibuprofen", 0.9), ("Paracetamol", 0.85), ("Diclofenac", 0.8)],
    "joint pain":       [("Diclofenac", 1.0), ("Ibuprofen", 0.9)],
    "back pain":        [("Diclofenac", 1.0), ("Ibuprofen", 0.9), ("Paracetamol", 0.7)],
    "muscle pain":      [("Ibuprofen", 1.0), ("Diclofenac", 0.9)],
    "toothache":        [("Ibuprofen", 1.0), ("Paracetamol", 0.9)],
    # Cold / Respiratory
    "cold":             [("Cetirizine", 0.9), ("Paracetamol", 0.8)],
    "cough":            [("Dextromethorphan", 0.9), ("Ambroxol", 0.85)],
    "sore throat":      [("Paracetamol", 0.9), ("Ibuprofen", 0.8)],
    "runny nose":       [("Cetirizine", 1.0), ("Loratadine", 0.9)],
    "congestion":       [("Cetirizine", 0.9), ("Loratadine", 0.85)],
    "sneezing":         [("Cetirizine", 1.0), ("Loratadine", 0.9)],
    # Allergy
    "allergy":          [("Cetirizine", 1.0), ("Loratadine", 0.95), ("Fexofenadine", 0.9)],
    "allergic":         [("Cetirizine", 1.0), ("Loratadine", 0.9)],
    "itching":          [("Cetirizine", 1.0), ("Loratadine", 0.85)],
    "rash":             [("Cetirizine", 0.9), ("Hydrocortisone", 0.85)],
    # Stomach / Digestion
    "stomach pain":     [("Omeprazole", 0.9), ("Antacid", 0.85), ("Pantoprazole", 0.8)],
    "stomach ache":     [("Omeprazole", 0.9), ("Antacid", 0.85)],
    "acidity":          [("Omeprazole", 1.0), ("Pantoprazole", 0.95), ("Antacid", 0.9)],
    "heartburn":        [("Omeprazole", 1.0), ("Antacid", 0.9)],
    "indigestion":      [("Antacid", 1.0), ("Omeprazole", 0.85)],
    "nausea":           [("Domperidone", 1.0), ("Ondansetron", 0.9), ("Metoclopramide", 0.85)],
    "vomiting":         [("Ondansetron", 1.0), ("Domperidone", 0.9)],
    "diarrhea":         [("ORS", 1.0), ("Loperamide", 0.9), ("Metronidazole", 0.8)],
    "loose motion":     [("ORS", 1.0), ("Loperamide", 0.9)],
    "constipation":     [("Lactulose", 1.0), ("Bisacodyl", 0.9)],
    # Infection / Antibiotic
    "infection":        [("Amoxicillin", 0.9), ("Azithromycin", 0.85)],
    "bacterial":        [("Amoxicillin", 1.0), ("Azithromycin", 0.9)],
    "throat infection": [("Amoxicillin", 1.0), ("Azithromycin", 0.9)],
    "ear infection":    [("Amoxicillin", 1.0), ("Azithromycin", 0.85)],
    # Diabetes / BP
    "diabetes":         [("Metformin", 1.0), ("Glipizide", 0.9)],
    "blood sugar":      [("Metformin", 1.0)],
    "blood pressure":   [("Amlodipine", 1.0), ("Atenolol", 0.9)],
    "hypertension":     [("Amlodipine", 1.0), ("Atenolol", 0.9), ("Losartan", 0.85)],
    # Sleep / Anxiety
    "insomnia":         [("Melatonin", 1.0), ("Zolpidem", 0.8)],
    "sleep":            [("Melatonin", 1.0)],
    "anxiety":          [("Alprazolam", 0.8), ("Clonazepam", 0.75)],
    # Skin
    "acne":             [("Benzoyl Peroxide", 1.0), ("Clindamycin", 0.9)],
    "fungal":           [("Clotrimazole", 1.0), ("Fluconazole", 0.9)],
    # Eyes
    "eye infection":    [("Ciprofloxacin Eye Drops", 1.0)],
    "conjunctivitis":   [("Ciprofloxacin Eye Drops", 1.0)],
    # Vitamins
    "vitamin":          [("Vitamin C", 0.9), ("Vitamin D", 0.85), ("Multivitamin", 0.8)],
    "weakness":         [("Multivitamin", 0.9), ("Iron Supplement", 0.85)],
    "fatigue":          [("Multivitamin", 0.9), ("Vitamin B12", 0.85)],
}


def seed_mappings():
    """Seed symptom→medicine mappings based on medicines in DB."""
    with get_db_context() as db:
        # Clear existing mappings
        existing = db.query(SymptomMedicineMapping).count()
        if existing > 0:
            print(f"Clearing {existing} existing mappings...")
            db.query(SymptomMedicineMapping).delete()
            db.flush()

        # Get all medicines
        all_medicines = db.query(Medicine).all()
        medicine_map = {m.name.lower(): m for m in all_medicines}

        print(f"Found {len(all_medicines)} medicines in DB.")

        inserted = 0
        skipped = 0

        import re
        
        for symptom, medicine_list in SYMPTOM_SEED_DATA.items():
            for med_fragment, relevance in medicine_list:
                # Find matching medicine (case-insensitive partial match or active ingredient match)
                matched_medicines = []
                frag_lower = med_fragment.lower()
                
                # Create a word boundary regex to prevent "ORS" from matching "AtORSave"
                # but handle things like "Vitamin C" correctly.
                # If the fragment is short (<= 3 chars like ORS), force exact word boundary
                if len(frag_lower) <= 3:
                    pattern = re.compile(rf'\b{re.escape(frag_lower)}\b', re.IGNORECASE)
                else:
                    pattern = re.compile(re.escape(frag_lower), re.IGNORECASE)

                for med_name_lower, med_obj in medicine_map.items():
                    active_ingr = str(med_obj.active_ingredients or "").lower()
                    
                    if pattern.search(med_name_lower) or pattern.search(active_ingr):
                        matched_medicines.append(med_obj)

                if matched_medicines:
                    for matched_medicine in matched_medicines:
                        mapping = SymptomMedicineMapping(
                            symptom=symptom,
                            medicine_id=matched_medicine.id,
                            relevance_score=relevance,
                            notes=f"Auto-seeded: {symptom} → {matched_medicine.name}",
                        )
                        db.add(mapping)
                        inserted += 1
                else:
                    skipped += 1
                    # Don't warn for every miss — many medicines may not be in DB

        db.commit()
        print(f"✅ Seeded {inserted} mappings ({skipped} skipped — medicine not in DB).")

        # Show what was seeded
        mappings = db.query(SymptomMedicineMapping).all()
        print(f"\nSample mappings:")
        for m in mappings[:10]:
            print(f"  {m.symptom!r} → {m.medicine.name!r} (score={m.relevance_score})")


if __name__ == "__main__":
    print("=" * 60)
    print("MediSync: Symptom Mapping Migration & Seed")
    print("=" * 60)
    create_table_if_missing()
    seed_mappings()
    print("\n✅ Done!")
