#!/usr/bin/env python3
"""
FINAL DATA SEEDING SCRIPT
=========================
Seeds database with complete medicine catalog and symptom mappings.

Includes:
- 50 medicines with full details (indications, contraindications, generics)
- 150+ symptom→medicine mappings
"""

import sys
import csv
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db_config import get_db_context
from src.models import Medicine, SymptomMedicineMapping

def seed_medicines():
    """Seed medicines from CSV."""
    print("📦 Seeding medicines...")
    
    csv_path = Path(__file__).parent.parent / "data" / "medicines_catalog.csv"
    
    if not csv_path.exists():
        print(f"  ❌ CSV file not found: {csv_path}")
        return False
    
    with get_db_context() as db:
        # Clear existing medicines (optional - comment out to keep existing)
        # db.query(Medicine).delete()
        # db.commit()
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            
            for row in reader:
                # Check if medicine already exists
                existing = db.query(Medicine).filter(
                    Medicine.name == row['name']
                ).first()
                
                if existing:
                    # Update existing medicine
                    existing.category = row['category']
                    existing.manufacturer = row['manufacturer']
                    existing.price = float(row['price'])
                    existing.stock = int(row['stock'])
                    existing.requires_prescription = row['requires_prescription'].lower() == 'true'
                    existing.description = row['description']
                    existing.indications = row['indications']
                    existing.generic_equivalent = row['generic_equivalent'] if row['generic_equivalent'] != 'None' else None
                    existing.contraindications = row['contraindications']
                    print(f"  ✏️  Updated: {row['name']}")
                else:
                    # Create new medicine
                    medicine = Medicine(
                        name=row['name'],
                        category=row['category'],
                        manufacturer=row['manufacturer'],
                        price=float(row['price']),
                        stock=int(row['stock']),
                        requires_prescription=row['requires_prescription'].lower() == 'true',
                        description=row['description'],
                        indications=row['indications'],
                        generic_equivalent=row['generic_equivalent'] if row['generic_equivalent'] != 'None' else None,
                        contraindications=row['contraindications']
                    )
                    db.add(medicine)
                    print(f"  ➕ Added: {row['name']}")
                
                count += 1
            
            db.commit()
            print(f"  ✅ Processed {count} medicines")
    
    return True

def seed_symptom_mappings():
    """Seed symptom→medicine mappings from CSV."""
    print("\n🔗 Seeding symptom mappings...")
    
    csv_path = Path(__file__).parent.parent / "data" / "symptom_mappings.csv"
    
    if not csv_path.exists():
        print(f"  ❌ CSV file not found: {csv_path}")
        return False
    
    with get_db_context() as db:
        # Clear existing mappings
        db.query(SymptomMedicineMapping).delete()
        db.commit()
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            skipped = 0
            
            for row in reader:
                # Find medicine by name
                medicine = db.query(Medicine).filter(
                    Medicine.name == row['medicine_name']
                ).first()
                
                if not medicine:
                    print(f"  ⚠️  Medicine not found: {row['medicine_name']}")
                    skipped += 1
                    continue
                
                # Create mapping
                mapping = SymptomMedicineMapping(
                    symptom=row['symptom'].lower(),  # Normalize to lowercase
                    medicine_id=medicine.id,
                    relevance_score=float(row['relevance_score']),
                    notes=row['notes']
                )
                db.add(mapping)
                count += 1
            
            db.commit()
            print(f"  ✅ Added {count} symptom mappings")
            if skipped > 0:
                print(f"  ⚠️  Skipped {skipped} mappings (medicine not found)")
    
    return True

def verify_data():
    """Verify seeded data."""
    print("\n🔍 Verifying data...")
    
    with get_db_context() as db:
        medicine_count = db.query(Medicine).count()
        mapping_count = db.query(SymptomMedicineMapping).count()
        prescription_count = db.query(Medicine).filter(
            Medicine.requires_prescription == True
        ).count()
        
        print(f"  📊 Total medicines: {medicine_count}")
        print(f"  📊 Prescription medicines: {prescription_count}")
        print(f"  📊 OTC medicines: {medicine_count - prescription_count}")
        print(f"  📊 Symptom mappings: {mapping_count}")
        
        # Sample queries
        print("\n  🔍 Sample queries:")
        
        # Find medicines for headache
        headache_mappings = db.query(SymptomMedicineMapping).filter(
            SymptomMedicineMapping.symptom == 'headache'
        ).all()
        print(f"    - Medicines for 'headache': {len(headache_mappings)}")
        
        # Find medicines for fever
        fever_mappings = db.query(SymptomMedicineMapping).filter(
            SymptomMedicineMapping.symptom == 'fever'
        ).all()
        print(f"    - Medicines for 'fever': {len(fever_mappings)}")
        
        # Check medicines with indications
        with_indications = db.query(Medicine).filter(
            Medicine.indications != None,
            Medicine.indications != ''
        ).count()
        print(f"    - Medicines with indications: {with_indications}")
        
        # Check medicines with contraindications
        with_contraindications = db.query(Medicine).filter(
            Medicine.contraindications != None,
            Medicine.contraindications != ''
        ).count()
        print(f"    - Medicines with contraindications: {with_contraindications}")
    
    return True

if __name__ == "__main__":
    try:
        print("🚀 Starting final data seeding...\n")
        
        # Seed medicines
        if not seed_medicines():
            print("\n❌ Medicine seeding failed")
            sys.exit(1)
        
        # Seed symptom mappings
        if not seed_symptom_mappings():
            print("\n❌ Symptom mapping seeding failed")
            sys.exit(1)
        
        # Verify data
        if not verify_data():
            print("\n❌ Data verification failed")
            sys.exit(1)
        
        print("\n✅ Final data seeding completed successfully!")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ Seeding failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
