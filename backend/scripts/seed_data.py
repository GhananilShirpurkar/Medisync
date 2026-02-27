
import sys
import os
import pandas as pd
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 1. Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 2. Add backend root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 3. Import lightweight DB config (bypassing main.py and heavy ML libs)
try:
    from src.db_config import DATABASE_URL, SessionLocal, init_db
    from src.models import Base, Medicine, SymptomMedicineMapping, Patient
except ImportError as e:
    logger.error(f"Failed to import modules: {e}")
    logger.error(f"Current sys.path: {sys.path}")
    sys.exit(1)


def seed_data():
    print("🌱 Starting database seeding...")
    
    # Ensure tables exist
    init_db()
    
    # Initialize DB connection
    engine = create_engine(DATABASE_URL)
    # Enable autoflush to see objects added within the same transaction
    SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)
    db = SessionLocal()

    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    medicines_file = os.path.join(data_dir, "medicines.xlsx")
    symptoms_file = os.path.join(data_dir, "symptoms.xlsx")

    # 1. Seed Medicines
    if os.path.exists(medicines_file):
        print(f"   Reading medicines from {medicines_file}...")
        try:
            df_meds = pd.read_excel(medicines_file)
            # Normalize column names: lowercase, strip, replace spaces with underscores
            df_meds.columns = df_meds.columns.str.strip().str.lower().str.replace(r'\s+', '_', regex=True)
            print(f"   Found columns: {df_meds.columns.tolist()}")

            # Drop duplicates in input file
            df_meds = df_meds.drop_duplicates(subset=['name'])
            
            # Regex for extracting strength (e.g., 500mg, 10ml)
            import re
            strength_pattern = re.compile(r'(\d+(?:\.\d+)?\s*(?:mg|ml|g|mcg|iu|%))', re.IGNORECASE)
            
            meds_added = 0
            for _, row in df_meds.iterrows():
                med_name = str(row['name']).strip()
                
                # Infer Strength
                strength_match = strength_pattern.search(med_name)
                strength_val = strength_match.group(1) if strength_match else "N/A"
                if pd.notna(row.get('strength')):
                    strength_val = str(row['strength'])

                # Infer Dosage Form
                form_val = "Other"
                name_lower = med_name.lower()
                if "tablet" in name_lower or "tab" in name_lower: form_val = "Tablet"
                elif "capsule" in name_lower or "cap" in name_lower: form_val = "Capsule"
                elif "syrup" in name_lower or "syp" in name_lower: form_val = "Syrup"
                elif "injection" in name_lower or "inj" in name_lower: form_val = "Injection"
                elif "cream" in name_lower or "gel" in name_lower: form_val = "Topical"
                elif "drop" in name_lower: form_val = "Drops"
                
                if pd.notna(row.get('dosage_form')):
                    form_val = str(row['dosage_form'])

                # Infer Active Ingredients (fallback to generic name)
                active_ing = row.get('generic_equivalent')
                if pd.notna(row.get('active_ingredients')):
                    active_ing = row.get('active_ingredients')
                if not active_ing or pd.isna(active_ing):
                    active_ing = "Unknown"

                # Infer Side Effects (fallback to generic advice)
                side_eff = "Consult your doctor for specific side effects."
                if pd.notna(row.get('side_effects')):
                    side_eff = row.get('side_effects')

                # Check if medicine already exists
                existing_med = db.query(Medicine).filter(Medicine.name == med_name).first()
                if existing_med:
                    continue

                med = Medicine(
                    name=med_name,
                    category=row.get('category'),
                    manufacturer=row.get('manufacturer'),
                    price=float(row['price']) if pd.notna(row['price']) else 0.0,
                    stock=int(row['stock']) if pd.notna(row['stock']) else 0,
                    requires_prescription=bool(row['requires_prescription']) if pd.notna(row['requires_prescription']) else False,
                    description=row.get('description'),
                    indications=row.get('indications'),
                    generic_equivalent=row.get('generic_equivalent'),
                    contraindications=row.get('contraindications'),
                    side_effects=side_eff,
                    dosage_form=form_val,
                    strength=strength_val,
                    active_ingredients=active_ing
                )
                db.add(med)
                meds_added += 1
            
            db.commit()
            print(f"   ✅ Added {meds_added} new medicines.")
        except Exception as e:
            print(f"   ❌ Error processing medicines: {e}")
            db.rollback()
    else:
        print(f"   ⚠️ Medicines file not found at {medicines_file}")

    # 2. Seed Symptom Mappings
    if os.path.exists(symptoms_file):
        print(f"   Reading symptom mappings from {symptoms_file}...")
        try:
            df_sym = pd.read_excel(symptoms_file)
            # Check if headers are likely in the second row (common user error)
            if 'symptom' not in df_sym.columns.str.lower() and 'medicine' not in df_sym.columns.str.lower():
                print("      ⚠️ Standard headers not found in row 0. Trying row 1...")
                df_sym = pd.read_excel(symptoms_file, header=1)
            
            df_sym.columns = df_sym.columns.str.strip().str.lower().str.replace(r'\s+', '_', regex=True)
            print(f"   Found columns: {df_sym.columns.tolist()}")
            
            mappings_added = 0
            # Check required columns
            if 'medicine_name' not in df_sym.columns:
                 # Fallback: check if 'medicine' column exists
                 if 'medicine' in df_sym.columns:
                     df_sym.rename(columns={'medicine': 'medicine_name'}, inplace=True)
                 else:
                     raise KeyError(f"Column 'medicine_name' not found. Available: {df_sym.columns.tolist()}")

            for _, row in df_sym.iterrows():
                med_name = str(row['medicine_name']).strip()
                medicine = db.query(Medicine).filter(Medicine.name == med_name).first()
                
                if not medicine:
                    # Try partial match or case insensitive? No, keep it strict for now.
                    # print(f"      ⚠️ Skipping mapping for unknown medicine: {med_name}")
                    continue

                symptom_name = str(row['symptom']).strip().lower()

                # Check if mapping already exists
                existing_mapping = db.query(SymptomMedicineMapping).filter(
                    SymptomMedicineMapping.symptom == symptom_name,
                    SymptomMedicineMapping.medicine_id == medicine.id
                ).first()
                
                if existing_mapping:
                    continue

                # Handle relevance score safely
                rel_score = 1.0
                if 'relevance_score' in row and pd.notna(row['relevance_score']):
                    rel_score = float(row['relevance_score'])

                mapping = SymptomMedicineMapping(
                    symptom=symptom_name,
                    medicine_id=medicine.id,
                    relevance_score=rel_score,
                    notes=row.get('notes')
                )
                db.add(mapping)
                mappings_added += 1
            
            db.commit()
            print(f"   ✅ Added {mappings_added} new symptom mappings.")
        except Exception as e:
            print(f"   ❌ Error processing symptoms: {e}")
            import traceback
            traceback.print_exc()
            db.rollback()
    else:
        print(f"   ⚠️ Symptoms file not found at {symptoms_file}")

    db.close()
    print("🌱 Seeding complete!")

if __name__ == "__main__":
    seed_data()
