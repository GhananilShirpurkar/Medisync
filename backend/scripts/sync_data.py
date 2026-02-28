#!/usr/bin/env python3
"""
DATA SYNCHRONIZATION SCRIPT
===========================
Syncs database with XLSX files from 'new data' directory.
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db_config import get_db_context, init_db
from src.models import Medicine, SymptomMedicineMapping

def clean_val(val):
    if pd.isna(val) or val == 'None' or val == 'nan':
        return None
    return val

def sync_medicines(medicines_path):
    print(f"📦 Syncing medicines from {medicines_path}...")
    
    if not medicines_path.exists():
        print(f"  ❌ File not found: {medicines_path}")
        return False
    
    df = pd.read_excel(medicines_path)
    
    # Pre-process: Drop duplicates in the file itself to avoid constraint issues
    initial_count = len(df)
    df = df.drop_duplicates(subset=['Name'], keep='first')
    if len(df) < initial_count:
        print(f"  ⚠️  Dropped {initial_count - len(df)} duplicate rows from medicines catalog.")
    
    with get_db_context() as db:
        count = 0
        updated = 0
        added = 0
        errors = 0
        
        for _, row in df.iterrows():
            try:
                name = clean_val(row.get('Name'))
                if not name:
                    continue
                    
                existing = db.query(Medicine).filter(Medicine.name == name).first()
                
                # Map columns
                medicine_data = {
                    "category": clean_val(row.get('Category')),
                    "manufacturer": clean_val(row.get('Manufacturer')),
                    "price": float(row.get('Price', 0)),
                    "stock": int(row.get('Stock', 0)),
                    "requires_prescription": bool(row.get('Requires Prescription', False)),
                    "description": clean_val(row.get('Description')),
                    "indications": clean_val(row.get('Indications')),
                    "generic_equivalent": clean_val(row.get('Generic Equivalent')),
                    "contraindications": clean_val(row.get('Contraindications')),
                }
                
                if existing:
                    for key, value in medicine_data.items():
                        setattr(existing, key, value)
                    updated += 1
                else:
                    medicine = Medicine(name=name, **medicine_data)
                    db.add(medicine)
                    added += 1
                
                count += 1
                
                # Commit in chunks to avoid massive transactions if needed
                if count % 100 == 0:
                    db.commit()
            except Exception as e:
                print(f"  ❌ Error processing medicine '{row.get('Name')}': {e}")
                errors += 1
            
        db.commit()
        print(f"  ✅ Processed {count} medicines (Added: {added}, Updated: {updated}, Errors: {errors})")
    
    return True

def sync_symptoms(symptoms_path):
    print(f"\n🔗 Syncing symptom mappings from {symptoms_path}...")
    
    if not symptoms_path.exists():
        print(f"  ❌ File not found: {symptoms_path}")
        return False
    
    # Detect if this is the large_diversified format (header at row 0) or old format (header at row 1)
    df_preview = pd.read_excel(symptoms_path, header=None, nrows=2)
    is_diversified = "Symptom" in df_preview.iloc[0].values
    
    if is_diversified:
        df = pd.read_excel(symptoms_path)
    else:
        # The old symptoms.xlsx has Row 0 as empty, Row 1 as headers
        df = pd.read_excel(symptoms_path, header=None)
        # Row 1 is where headers actually are
        df.columns = [str(c).strip() for c in df.iloc[1]]
        # Rest is data (Row 2 onwards)
        df = df[2:].reset_index(drop=True)
    
    # Pre-process: Drop exact duplicates
    initial_count = len(df)
    df = df.drop_duplicates(subset=['Symptom', 'Medicine Name'], keep='first')
    if len(df) < initial_count:
        print(f"  ⚠️  Dropped {initial_count - len(df)} duplicate rows from symptoms.")
    
    with get_db_context() as db:
        # Clear existing mappings for clean sync
        db.query(SymptomMedicineMapping).delete()
        db.commit()
        
        count = 0
        skipped = 0
        errors = 0
        
        for _, row in df.iterrows():
            try:
                symptom = clean_val(row.get('Symptom'))
                medicine_name = clean_val(row.get('Medicine Name'))
                notes = clean_val(row.get('Notes'))
                
                if not symptom or not medicine_name:
                    continue
                    
                # Find medicine
                medicine = db.query(Medicine).filter(Medicine.name == medicine_name).first()
                
                # If not found, try case-insensitive partial match
                if not medicine:
                    medicine = db.query(Medicine).filter(Medicine.name.ilike(f"%{medicine_name}%")).first()
                    
                if not medicine:
                    # print(f"  ⚠️  Medicine '{medicine_name}' not found for symptom '{symptom}'")
                    skipped += 1
                    continue
                
                mapping = SymptomMedicineMapping(
                    symptom=symptom.lower(),
                    medicine_id=medicine.id,
                    relevance_score=0.9,
                    notes=notes
                )
                db.add(mapping)
                count += 1
                
                if count % 100 == 0:
                    db.commit()
            except Exception as e:
                print(f"  ❌ Error mapping symptom '{row.get('Symptom')}': {e}")
                errors += 1
            
        db.commit()
        print(f"  ✅ Added {count} symptom mappings (Skipped: {skipped}, Errors: {errors})")
    
    return True

def main():
    print("🚀 Starting Data Synchronization...\n")
    
    # Paths
    base_dir = Path(__file__).parent.parent.parent
    new_data_dir = base_dir / "new data"
    
    # Prioritize large diversified files if they exist
    medicines_path = new_data_dir / "medicines_large_diversified.xlsx"
    if not medicines_path.exists():
        medicines_path = new_data_dir / "medicines.xlsx"
        
    symptoms_path = new_data_dir / "symptoms_large_diversified.xlsx"
    if not symptoms_path.exists():
        symptoms_path = new_data_dir / "symptoms.xlsx"
    
    # Initialize DB (create tables if missing)
    init_db()
    
    # Run sync
    success = sync_medicines(medicines_path)
    if success:
        success = sync_symptoms(symptoms_path)
        
    if success:
        print("\n✅ Data Synchronization Complete!")
    else:
        print("\n❌ Data Synchronization Failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
