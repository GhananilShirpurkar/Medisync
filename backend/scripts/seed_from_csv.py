#!/usr/bin/env python3
"""
Master Seed Script: Populates DB from CSVs
==========================================
Reads data from backend/data/medicines_catalog.csv and backend/data/symptom_mappings.csv
and populates the SQLite database.

Run from the backend/ directory:
    python3 scripts/seed_from_csv.py
"""

import sqlite3
import csv
import os

# Find the DB file
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(BACKEND_DIR, "data")

# Try common DB paths
DB_CANDIDATES = [
    os.path.join(BACKEND_DIR, "hackfusion.db"),
    os.path.join(BACKEND_DIR, "medisync.db"),
    os.path.join(BACKEND_DIR, "app.db"),
]

DB_PATH = None
for candidate in DB_CANDIDATES:
    if os.path.exists(candidate):
        DB_PATH = candidate
        break

if not DB_PATH:
    # Use default if not found (will create new)
    DB_PATH = os.path.join(BACKEND_DIR, "hackfusion.db")
    print(f"Warning: Database not found, creating new at {DB_PATH}")

print(f"Using database: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

def seed_medicines():
    csv_path = os.path.join(DATA_DIR, "medicines_catalog.csv")
    if not os.path.exists(csv_path):
        print(f"❌ Error: {csv_path} not found.")
        return

    print(f"\nSeeding medicines from {csv_path}...")
    
    # Create medicines table if not exists (simplified schema for safety)
    # Note: In a real scenario, we rely on the app to create the schema via ORM, 
    # but for raw seeding we might need to ensure it exists.
    # We assume schema exists or we use the basic fields.
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        inserted = 0
        updated = 0
        
        for row in reader:
            # Check if medicine exists
            cur.execute("SELECT id FROM medicines WHERE name = ?", (row['name'],))
            existing = cur.fetchone()
            
            # Convert boolean string to integer for SQLite (0/1)
            req_rx = 1 if row['requires_prescription'].lower() == 'true' else 0
            
            if existing:
                # Update existing
                cur.execute("""
                    UPDATE medicines SET 
                        category=?, manufacturer=?, price=?, stock=?, 
                        requires_prescription=?, description=?, indications=?, 
                        generic_equivalent=?, contraindications=?, updated_at=CURRENT_TIMESTAMP
                    WHERE id=?
                """, (
                    row['category'], row['manufacturer'], float(row['price']), int(row['stock']),
                    req_rx, row['description'], row['indications'],
                    row['generic_equivalent'], row['contraindications'], existing['id']
                ))
                updated += 1
            else:
                # Insert new
                cur.execute("""
                    INSERT INTO medicines (
                        name, category, manufacturer, price, stock, 
                        requires_prescription, description, indications, 
                        generic_equivalent, contraindications, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (
                    row['name'], row['category'], row['manufacturer'], float(row['price']), int(row['stock']),
                    req_rx, row['description'], row['indications'],
                    row['generic_equivalent'], row['contraindications']
                ))
                inserted += 1
                
        conn.commit()
        print(f"✅ Medicines: {inserted} inserted, {updated} updated.")

def seed_symptom_mappings():
    csv_path = os.path.join(DATA_DIR, "symptom_mappings.csv")
    if not os.path.exists(csv_path):
        print(f"❌ Error: {csv_path} not found.")
        return

    print(f"\nSeeding symptom mappings from {csv_path}...")
    
    # Create table if missing (same as previous script logic)
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='symptom_medicine_mapping'")
    if not cur.fetchone():
        print("Creating symptom_medicine_mapping table...")
        cur.execute("""
        CREATE TABLE symptom_medicine_mapping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symptom VARCHAR(255) NOT NULL,
            medicine_id INTEGER NOT NULL REFERENCES medicines(id),
            relevance_score REAL DEFAULT 1.0,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        cur.execute("CREATE INDEX idx_symptom ON symptom_medicine_mapping(symptom)")
    
    # Build medicine lookup (name -> id)
    cur.execute("SELECT id, name FROM medicines")
    med_map = {row['name'].lower(): row['id'] for row in cur.fetchall()}
    
    # Also partial match lookup
    med_list = [(row['name'].lower(), row['id']) for row in cur.fetchall()] # Reload for safety if cursor exhausted (it isn't but good practice)
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        inserted = 0
        skipped = 0
        
        # Clear existing mappings to avoid duplicates? 
        # For now, let's truncate to be clean, as this is a master seed
        cur.execute("DELETE FROM symptom_medicine_mapping")
        
        for row in reader:
            target_med = row['medicine_name'].lower()
            med_id = med_map.get(target_med)
            
            if not med_id:
                # Try partial match (like "Paracetamol" matching "Paracetamol 500mg")
                # This is O(N) but N is small (50 meds)
                for m_name, m_id in med_map.items():
                    if target_med in m_name or m_name in target_med:
                        med_id = m_id
                        break
            
            if med_id:
                cur.execute("""
                    INSERT INTO symptom_medicine_mapping (
                        symptom, medicine_id, relevance_score, notes, created_at
                    ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    row['symptom'], med_id, float(row['relevance_score']), row['notes']
                ))
                inserted += 1
            else:
                # print(f"Skipping {row['symptom']} -> {row['medicine_name']} (Medicine not found)")
                skipped += 1
                
        conn.commit()
        print(f"✅ Symptom Mappings: {inserted} inserted, {skipped} skipped.")

if __name__ == "__main__":
    print("=" * 60)
    print("MediSync: Master CSV Seeder")
    print("=" * 60)
    
    # Check if medicines table exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='medicines'")
    if not cur.fetchone():
        print("❌ Error: 'medicines' table does not exist. Run the app first to create schema.")
        # Alternatively, we could create it here, but that risks schema drift.
    else:
        seed_medicines()
        seed_symptom_mappings()
        
    conn.close()
    print("\n✅ Done!")
