"""
MIGRATE TO POSTGRESQL
=====================
Initialize PostgreSQL database with schema and seed data.

Usage:
    python scripts/migrate_to_postgres.py
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path, override=True)  # override=True to reload
print(f"📁 Loaded environment from: {env_path}")
print(f"🔗 DATABASE_URL: {os.getenv('DATABASE_URL', 'NOT FOUND')[:80]}...")

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db_config import init_db, get_db_type, engine
from src.models import Base
from sqlalchemy import text
import pandas as pd


def check_connection():
    """Test database connection."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Connected to PostgreSQL")
            print(f"   Version: {version[:50]}...")
            return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


def create_tables():
    """Create all tables."""
    try:
        print("\n📋 Creating tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully")
        
        # List created tables
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            print(f"\n📊 Created {len(tables)} tables:")
            for table in tables:
                print(f"   • {table}")
        
        return True
    except Exception as e:
        print(f"❌ Table creation failed: {e}")
        return False


def seed_medicines():
    """Seed medicines from CSV."""
    try:
        print("\n💊 Seeding medicines...")
        
        # Read CSV (adjust path to be relative to script location)
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'medicines_catalog.csv')
        if not os.path.exists(csv_path):
            print(f"⚠️  CSV not found: {csv_path}")
            return False
        
        df = pd.read_csv(csv_path)
        
        # Insert medicines
        from src.db_config import get_db_context
        from src.models import Medicine
        
        with get_db_context() as db:
            count = 0
            for _, row in df.iterrows():
                medicine = Medicine(
                    name=str(row['name']),
                    category=str(row.get('category', '')),
                    manufacturer=str(row.get('manufacturer', '')),
                    price=float(row['price']),
                    stock=int(row.get('stock', 100)),
                    requires_prescription=bool(str(row.get('requires_prescription', 'False')).lower() in ['true', '1', 'yes']),
                    description=str(row.get('description', '')),
                    indications=str(row.get('indications', '')),
                    generic_equivalent=str(row.get('generic_equivalent', '')),
                    contraindications=str(row.get('contraindications', ''))
                )
                db.add(medicine)
                count += 1
                
                # Commit in batches of 10
                if count % 10 == 0:
                    db.commit()
            
            # Final commit
            db.commit()
            print(f"✅ Seeded {count} medicines")
        
        return True
    except Exception as e:
        print(f"❌ Medicine seeding failed: {e}")
        return False


def seed_symptom_mappings():
    """Seed symptom mappings from CSV."""
    try:
        print("\n🔗 Seeding symptom mappings...")
        
        # Read CSV (adjust path to be relative to script location)
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'symptom_mappings.csv')
        if not os.path.exists(csv_path):
            print(f"⚠️  CSV not found: {csv_path}")
            return False
        
        df = pd.read_csv(csv_path)
        
        # Insert mappings
        from src.db_config import get_db_context
        from src.models import SymptomMedicineMapping, Medicine
        
        with get_db_context() as db:
            count = 0
            for _, row in df.iterrows():
                # Find medicine by name
                medicine = db.query(Medicine).filter(
                    Medicine.name == row['medicine_name']
                ).first()
                
                if medicine:
                    mapping = SymptomMedicineMapping(
                        symptom=row['symptom'].lower(),
                        medicine_id=medicine.id,
                        relevance_score=float(row.get('relevance_score', 1.0)),
                        notes=row.get('notes')
                    )
                    db.add(mapping)
                    count += 1
            
            db.commit()
            print(f"✅ Seeded {count} symptom mappings")
        
        return True
    except Exception as e:
        print(f"❌ Symptom mapping seeding failed: {e}")
        return False


def verify_data():
    """Verify seeded data."""
    try:
        print("\n🔍 Verifying data...")
        
        from src.db_config import get_db_context
        from src.models import Medicine, SymptomMedicineMapping
        
        with get_db_context() as db:
            medicine_count = db.query(Medicine).count()
            mapping_count = db.query(SymptomMedicineMapping).count()
            
            print(f"✅ Medicines: {medicine_count}")
            print(f"✅ Symptom Mappings: {mapping_count}")
            
            # Show sample medicines
            print("\n📋 Sample medicines:")
            medicines = db.query(Medicine).limit(5).all()
            for med in medicines:
                print(f"   • {med.name} - ₹{med.price} (Stock: {med.stock})")
        
        return True
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False


def main():
    """Main migration function."""
    print("="*60)
    print("POSTGRESQL MIGRATION")
    print("="*60)
    
    # Check database type
    db_type = get_db_type()
    print(f"\n📊 Database Type: {db_type}")
    
    if db_type != "PostgreSQL":
        print("❌ Not connected to PostgreSQL/Supabase")
        print("   Please check DATABASE_URL in .env")
        return False
    
    # Step 1: Check connection
    if not check_connection():
        return False
    
    # Step 2: Create tables
    if not create_tables():
        return False
    
    # Step 3: Seed medicines
    if not seed_medicines():
        print("⚠️  Continuing without medicine data...")
    
    # Step 4: Seed symptom mappings
    if not seed_symptom_mappings():
        print("⚠️  Continuing without symptom mappings...")
    
    # Step 5: Verify data
    verify_data()
    
    print("\n" + "="*60)
    print("✅ MIGRATION COMPLETE")
    print("="*60)
    print("\n🚀 Your PostgreSQL database is ready!")
    print("   • Tables created")
    print("   • Data seeded")
    print("   • Ready for production")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
