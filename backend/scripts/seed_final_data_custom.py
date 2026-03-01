"""
Final Data Seeding Script
=========================
Drops all rows from medicines and symptom_medicine_mapping tables.
Seeds tables using medicines.xlsx and symptom_mappings.csv.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
import pandas as pd
from src.db_config import init_db, get_db_context
from src.models import Medicine, SymptomMedicineMapping

def seed_final_data():
    backend_dir = Path(__file__).parent.parent
    meds_path = backend_dir.parent / "new data" / "meds.xlsx"
    symp_path = backend_dir.parent / "new data" / "symptom_medicine_mapping.csv"

    if not meds_path.exists():
        print(f"❌ Excel not found: {meds_path}")
        return
    if not symp_path.exists():
        print(f"❌ CSV not found: {symp_path}")
        return

    print("📦 Loading medicines from Excel...")
    df_meds = pd.read_excel(meds_path)
    
    print("🔗 Loading symptom mappings from CSV...")
    df_symps = pd.read_csv(symp_path)

    with get_db_context() as db:
        print("🗑️ Wiping existing tables (Raw SQL)...")
        try:
            from src.db_config import engine as db_engine
            with db_engine.connect() as conn:
                conn.execute(text("PRAGMA foreign_keys = OFF;"))
                conn.execute(text("DELETE FROM symptom_medicine_mapping;"))
                conn.execute(text("DELETE FROM medicines;"))
                # Reset auto-increment
                try:
                    conn.execute(text("DELETE FROM sqlite_sequence WHERE name='medicines';"))
                    conn.execute(text("DELETE FROM sqlite_sequence WHERE name='symptom_medicine_mapping';"))
                except:
                    pass
                conn.execute(text("PRAGMA foreign_keys = ON;"))
                conn.commit()
            print("✨ Tables wiped successfully.")
        except Exception as e:
            print(f"Schema wipe error: {e}")
            db.rollback()

        print("💉 Inserting medicines...")
        med_count = 0
        new_meds = []
        for _, row in df_meds.iterrows():
            medicine = Medicine(
                id=int(row.get("id")) if pd.notna(row.get("id")) else None,
                name=str(row.get("name", "")),
                category=str(row.get("category", "")),
                manufacturer=str(row.get("manufacturer", "")),
                price=float(row.get("price", 0) if pd.notna(row.get("price")) else 0),
                stock=int(row.get("stock", 0) if pd.notna(row.get("stock")) else 0),
                requires_prescription=bool(row.get("requires_prescriptuon", False)),
                description=str(row.get("description", "")),
                indications=str(row.get("indications", "")),
                generic_equivalent=str(row.get("generic_equivalent", "")),
                contraindications=str(row.get("contradictions", "")),
                side_effects=str(row.get("side_effects", "")),
                dosage_form=str(row.get("dosage_form", "")),
                strength=str(row.get("strength", "")),
                active_ingredients=str(row.get("active_ingredients", "")),
                atc_code=str(row.get("atc_code", "")),
                atc_level_1=str(row.get("atc_level_1", "")),
                atc_level_2=str(row.get("atc_level_2", "")),
                atc_level_3=str(row.get("atc_level_3", "")),
                atc_level_4=str(row.get("atc_level_4", ""))
            )
            new_meds.append(medicine)
            med_count += 1
            
        db.add_all(new_meds)
        db.commit() # Commit to get IDs
        
        print(f"✅ Inserted {med_count} medicines.")
        
        print("🔗 Inserting symptom mappings...")
        symp_count = 0
        skipped = 0
        
        # Build medicine lookup (name lowercase to ID)
        med_map = {m.name.lower(): m.id for m in db.query(Medicine).all()}
        # Print a few mappings for debugging
        print(f"First 3 meds loaded: {list(med_map.keys())[:3]}")

        seen_mappings = set()
        for _, row in df_symps.iterrows():
            med_id = int(row.get('medicine_id')) if pd.notna(row.get('medicine_id')) else None
            
            if med_id:
                combo = (str(row.get('symptom', '')), med_id)
                if combo in seen_mappings:
                    skipped += 1
                    continue
                seen_mappings.add(combo)
                
                mapping = SymptomMedicineMapping(
                    id=int(row.get('id')) if pd.notna(row.get('id')) else None,
                    symptom=combo[0],
                    medicine_id=med_id,
                    relevance_score=float(row.get('relevence_score', 1.0)),
                    notes=str(row.get('notes', ''))
                )
                db.add(mapping)
                symp_count += 1
            else:
                skipped += 1
                
        db.commit()
        print(f"✅ Inserted {symp_count} symptom mappings (Skipped {skipped})")

if __name__ == "__main__":
    print("=" * 60)
    print("DATABASE FINAL SEEDING")
    print("=" * 60)
    init_db()
    seed_final_data()
    print("=" * 60)
    print("✅ SEEDING COMPLETE")
