"""
DATABASE SEEDING SCRIPT
=======================
Migrate CSV data to SQLite/PostgreSQL.

Usage:
    python backend/scripts/seed_database.py
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from src.db_config import init_db, get_db_context, get_db_type
from src.models import Medicine, Patient


def seed_medicines():
    """Seed medicines from CSV."""
    print("\n📦 Seeding medicines...")
    
    csv_path = Path(__file__).parent.parent / "data" / "product_export.csv"
    
    if not csv_path.exists():
        print(f"❌ CSV not found: {csv_path}")
        return
    
    df = pd.read_csv(csv_path)
    
    with get_db_context() as db:
        # Clear existing
        db.query(Medicine).delete()
        
        count = 0
        seen_names = set()
        
        for _, row in df.iterrows():
            name = row.get("name", f"Unknown-{count}")
            
            # Skip duplicates
            if name in seen_names:
                continue
            seen_names.add(name)
            
            medicine = Medicine(
                name=name,
                category=row.get("category"),
                manufacturer=row.get("manufacturer"),
                price=float(row.get("price", 0)),
                stock=int(row.get("stock", 0)),
                requires_prescription=bool(row.get("requires_prescription", False)),
                description=row.get("description"),
            )
            db.add(medicine)
            count += 1
        
        db.commit()
        print(f"✅ Seeded {count} medicines")


def seed_patients():
    """Seed patients from CSV."""
    print("\n👥 Seeding patients...")
    
    csv_path = Path(__file__).parent.parent / "data" / "consumer_order_history.csv"
    
    if not csv_path.exists():
        print(f"❌ CSV not found: {csv_path}")
        return
    
    try:
        df = pd.read_csv(csv_path, skiprows=1)  # Skip header row
        
        with get_db_context() as db:
            # Clear existing
            db.query(Patient).delete()
            
            # Check if required columns exist
            if "consumer_id" not in df.columns:
                print("⚠️  CSV doesn't have expected columns, skipping patient seeding")
                return
            
            # Get unique patients
            unique_patients = df["consumer_id"].unique()
            
            count = 0
            for patient_id in unique_patients:
                patient_data = df[df["consumer_id"] == patient_id].iloc[0]
                
                patient = Patient(
                    user_id=str(patient_id),
                    name=patient_data.get("consumer_name"),
                    phone=patient_data.get("phone"),
                    email=patient_data.get("email"),
                    total_orders=len(df[df["consumer_id"] == patient_id]),
                )
                db.add(patient)
                count += 1
            
            db.commit()
            print(f"✅ Seeded {count} patients")
    except Exception as e:
        print(f"⚠️  Could not seed patients: {e}")
        print("   Continuing without patient data...")


def main():
    """Main seeding function."""
    print("=" * 60)
    print("DATABASE SEEDING")
    print("=" * 60)
    print(f"Database: {get_db_type()}")
    
    # Initialize database (create tables)
    init_db()
    
    # Seed data
    seed_medicines()
    seed_patients()
    
    print("\n" + "=" * 60)
    print("✅ SEEDING COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
