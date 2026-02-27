"""
SEED INDIAN MEDICINES
=====================
Add common Indian medicines to the database for testing.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db_config import get_db_context
from src.models import Medicine


def seed_indian_medicines():
    """Add common Indian medicines."""
    
    medicines = [
        # Pain relievers
        {"name": "Paracetamol", "category": "Analgesic", "manufacturer": "Generic", "price": 10.0, "stock": 100, "requires_prescription": False},
        {"name": "Paracetamol 500mg", "category": "Analgesic", "manufacturer": "Generic", "price": 12.0, "stock": 150, "requires_prescription": False},
        {"name": "Crocin", "category": "Analgesic", "manufacturer": "GSK", "price": 15.0, "stock": 80, "requires_prescription": False},
        {"name": "Ibuprofen", "category": "NSAID", "manufacturer": "Generic", "price": 20.0, "stock": 75, "requires_prescription": False},
        {"name": "Aspirin", "category": "NSAID", "manufacturer": "Generic", "price": 8.0, "stock": 90, "requires_prescription": False},
        {"name": "Diclofenac", "category": "NSAID", "manufacturer": "Generic", "price": 25.0, "stock": 60, "requires_prescription": True},
        
        # Antibiotics
        {"name": "Amoxicillin", "category": "Antibiotic", "manufacturer": "Generic", "price": 50.0, "stock": 120, "requires_prescription": True},
        {"name": "Amoxicillin 250mg", "category": "Antibiotic", "manufacturer": "Generic", "price": 55.0, "stock": 100, "requires_prescription": True},
        {"name": "Azithromycin", "category": "Antibiotic", "manufacturer": "Generic", "price": 80.0, "stock": 50, "requires_prescription": True},
        {"name": "Ciprofloxacin", "category": "Antibiotic", "manufacturer": "Generic", "price": 60.0, "stock": 70, "requires_prescription": True},
        {"name": "Doxycycline", "category": "Antibiotic", "manufacturer": "Generic", "price": 45.0, "stock": 65, "requires_prescription": True},
        
        # Controlled substances
        {"name": "Alprazolam", "category": "Benzodiazepine", "manufacturer": "Generic", "price": 100.0, "stock": 30, "requires_prescription": True},
        {"name": "Diazepam", "category": "Benzodiazepine", "manufacturer": "Generic", "price": 90.0, "stock": 25, "requires_prescription": True},
        {"name": "Tramadol", "category": "Opioid", "manufacturer": "Generic", "price": 120.0, "stock": 20, "requires_prescription": True},
        {"name": "Codeine", "category": "Opioid", "manufacturer": "Generic", "price": 110.0, "stock": 15, "requires_prescription": True},
        
        # Steroids
        {"name": "Prednisolone", "category": "Steroid", "manufacturer": "Generic", "price": 35.0, "stock": 55, "requires_prescription": True},
        {"name": "Dexamethasone", "category": "Steroid", "manufacturer": "Generic", "price": 40.0, "stock": 45, "requires_prescription": True},
        
        # Anticoagulants
        {"name": "Warfarin", "category": "Anticoagulant", "manufacturer": "Generic", "price": 150.0, "stock": 40, "requires_prescription": True},
        
        # Common OTC
        {"name": "Cetirizine", "category": "Antihistamine", "manufacturer": "Generic", "price": 18.0, "stock": 110, "requires_prescription": False},
        {"name": "Omeprazole", "category": "Antacid", "manufacturer": "Generic", "price": 30.0, "stock": 95, "requires_prescription": False},
        {"name": "Ranitidine", "category": "Antacid", "manufacturer": "Generic", "price": 25.0, "stock": 85, "requires_prescription": False},
        
        # Vitamins
        {"name": "Vitamin C", "category": "Vitamin", "manufacturer": "Generic", "price": 12.0, "stock": 200, "requires_prescription": False},
        {"name": "Vitamin D3", "category": "Vitamin", "manufacturer": "Generic", "price": 15.0, "stock": 180, "requires_prescription": False},
        {"name": "Multivitamin", "category": "Vitamin", "manufacturer": "Generic", "price": 35.0, "stock": 150, "requires_prescription": False},
        
        # Diabetes
        {"name": "Metformin", "category": "Antidiabetic", "manufacturer": "Generic", "price": 40.0, "stock": 100, "requires_prescription": True},
        {"name": "Glimepiride", "category": "Antidiabetic", "manufacturer": "Generic", "price": 50.0, "stock": 80, "requires_prescription": True},
        
        # Blood pressure
        {"name": "Amlodipine", "category": "Antihypertensive", "manufacturer": "Generic", "price": 45.0, "stock": 90, "requires_prescription": True},
        {"name": "Atenolol", "category": "Antihypertensive", "manufacturer": "Generic", "price": 38.0, "stock": 85, "requires_prescription": True},
        
        # Respiratory
        {"name": "Salbutamol", "category": "Bronchodilator", "manufacturer": "Generic", "price": 55.0, "stock": 70, "requires_prescription": True},
        {"name": "Montelukast", "category": "Antiasthmatic", "manufacturer": "Generic", "price": 60.0, "stock": 65, "requires_prescription": True},
    ]
    
    with get_db_context() as db:
        # Clear existing medicines
        db.query(Medicine).delete()
        
        # Add new medicines
        for med_data in medicines:
            medicine = Medicine(**med_data)
            db.add(medicine)
        
        db.commit()
        print(f"✅ Seeded {len(medicines)} Indian medicines")
        
        # Verify
        count = db.query(Medicine).count()
        print(f"📊 Total medicines in database: {count}")
        
        # Show sample
        print("\n📋 Sample medicines:")
        samples = db.query(Medicine).limit(5).all()
        for med in samples:
            print(f"  - {med.name} (₹{med.price}, Stock: {med.stock})")


if __name__ == "__main__":
    print("\n🌿 Seeding Indian Medicines Database...\n")
    seed_indian_medicines()
    print("\n✅ Done!\n")
