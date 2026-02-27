#!/usr/bin/env python3
"""
Standalone SQLite migration: creates and seeds symptom_medicine_mapping table.
Uses raw sqlite3 module — no app imports, no sentence transformer loading.

Run from the backend/ directory:
    python3 scripts/seed_symptoms_raw.py
"""

import sqlite3
import os

# Find the DB file
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)

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
    # Search for any .db file in backend dir
    for f in os.listdir(BACKEND_DIR):
        if f.endswith(".db"):
            DB_PATH = os.path.join(BACKEND_DIR, f)
            break

if not DB_PATH:
    print("ERROR: Could not find SQLite database file!")
    exit(1)

print(f"Using database: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# ── Step 1: Create table if missing ────────────────────────────────────────
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='symptom_medicine_mapping'")
if cur.fetchone():
    print("Table already exists. Dropping and recreating...")
    cur.execute("DROP TABLE IF EXISTS symptom_medicine_mapping")

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
conn.commit()
print("✅ Table created.")

# ── Step 2: Load all medicines ──────────────────────────────────────────────
cur.execute("SELECT id, name, stock FROM medicines")
medicines = cur.fetchall()
print(f"Found {len(medicines)} medicines in DB:")
for m in medicines:
    print(f"  [{m['id']}] {m['name']} (stock={m['stock']})")

# Build lookup: lowercase name fragment → (id, name)
medicine_lookup = {m["name"].lower(): (m["id"], m["name"]) for m in medicines}

# ── Step 3: Symptom seed data ───────────────────────────────────────────────
# Format: { symptom: [(medicine_name_fragment, relevance), ...] }
SEED = {
    # Pain / Fever
    "headache":         [("paracetamol", 1.0), ("aspirin", 0.9), ("ibuprofen", 0.85), ("dolo", 0.9)],
    "fever":            [("paracetamol", 1.0), ("dolo", 0.95), ("aspirin", 0.8), ("ibuprofen", 0.75)],
    "mild fever":       [("paracetamol", 1.0), ("dolo", 0.95), ("ibuprofen", 0.8)],
    "body pain":        [("ibuprofen", 1.0), ("paracetamol", 0.9), ("diclofenac", 0.85)],
    "pain":             [("ibuprofen", 0.9), ("paracetamol", 0.85), ("diclofenac", 0.8)],
    "joint pain":       [("diclofenac", 1.0), ("ibuprofen", 0.9)],
    "back pain":        [("diclofenac", 1.0), ("ibuprofen", 0.9), ("paracetamol", 0.7)],
    "muscle pain":      [("ibuprofen", 1.0), ("diclofenac", 0.9)],
    "toothache":        [("ibuprofen", 1.0), ("paracetamol", 0.9)],
    # Cold / Respiratory
    "cold":             [("cetirizine", 0.9), ("paracetamol", 0.8)],
    "cough":            [("dextromethorphan", 0.9), ("ambroxol", 0.85), ("paracetamol", 0.7)],
    "sore throat":      [("paracetamol", 0.9), ("ibuprofen", 0.8)],
    "runny nose":       [("cetirizine", 1.0), ("loratadine", 0.9)],
    "congestion":       [("cetirizine", 0.9), ("loratadine", 0.85)],
    "sneezing":         [("cetirizine", 1.0), ("loratadine", 0.9)],
    # Allergy
    "allergy":          [("cetirizine", 1.0), ("loratadine", 0.95), ("fexofenadine", 0.9)],
    "allergic":         [("cetirizine", 1.0), ("loratadine", 0.9)],
    "itching":          [("cetirizine", 1.0), ("loratadine", 0.85)],
    "rash":             [("cetirizine", 0.9), ("hydrocortisone", 0.85)],
    # Stomach / Digestion
    "stomach pain":     [("omeprazole", 0.9), ("pantoprazole", 0.8)],
    "stomach ache":     [("omeprazole", 0.9)],
    "acidity":          [("omeprazole", 1.0), ("pantoprazole", 0.95)],
    "heartburn":        [("omeprazole", 1.0)],
    "indigestion":      [("omeprazole", 0.85)],
    "nausea":           [("domperidone", 1.0), ("ondansetron", 0.9), ("metoclopramide", 0.85)],
    "vomiting":         [("ondansetron", 1.0), ("domperidone", 0.9)],
    "diarrhea":         [("loperamide", 0.9), ("metronidazole", 0.8)],
    "loose motion":     [("loperamide", 0.9)],
    "constipation":     [("lactulose", 1.0), ("bisacodyl", 0.9)],
    # Infection
    "infection":        [("amoxicillin", 0.9), ("azithromycin", 0.85)],
    "bacterial":        [("amoxicillin", 1.0), ("azithromycin", 0.9)],
    "throat infection": [("amoxicillin", 1.0), ("azithromycin", 0.9)],
    # Diabetes / BP
    "diabetes":         [("metformin", 1.0), ("glipizide", 0.9)],
    "blood sugar":      [("metformin", 1.0)],
    "blood pressure":   [("amlodipine", 1.0), ("atenolol", 0.9)],
    "hypertension":     [("amlodipine", 1.0), ("atenolol", 0.9), ("losartan", 0.85)],
    # Sleep / Anxiety
    "insomnia":         [("melatonin", 1.0), ("zolpidem", 0.8)],
    "sleep":            [("melatonin", 1.0)],
    # Skin
    "acne":             [("benzoyl peroxide", 1.0), ("clindamycin", 0.9)],
    "fungal":           [("clotrimazole", 1.0), ("fluconazole", 0.9)],
    # Vitamins
    "vitamin":          [("vitamin c", 0.9), ("vitamin d", 0.85), ("multivitamin", 0.8)],
    "weakness":         [("multivitamin", 0.9)],
    "fatigue":          [("multivitamin", 0.9)],
}

# ── Step 4: Insert mappings ─────────────────────────────────────────────────
inserted = 0
skipped_no_match = 0

for symptom, med_list in SEED.items():
    for med_fragment, relevance in med_list:
        # Find matching medicine (partial name match)
        matched_id = None
        matched_name = None
        for med_name_lower, (med_id, med_name) in medicine_lookup.items():
            if med_fragment in med_name_lower or med_name_lower in med_fragment:
                matched_id = med_id
                matched_name = med_name
                break

        if matched_id:
            cur.execute(
                "INSERT INTO symptom_medicine_mapping (symptom, medicine_id, relevance_score, notes) VALUES (?, ?, ?, ?)",
                (symptom, matched_id, relevance, f"Seeded: {symptom} → {matched_name}")
            )
            inserted += 1
        else:
            skipped_no_match += 1

conn.commit()
print(f"\n✅ Seeded {inserted} mappings ({skipped_no_match} skipped — medicine not in DB)")

# ── Step 5: Show sample ─────────────────────────────────────────────────────
cur.execute("""
    SELECT s.symptom, m.name, s.relevance_score
    FROM symptom_medicine_mapping s
    JOIN medicines m ON m.id = s.medicine_id
    ORDER BY s.symptom
    LIMIT 20
""")
rows = cur.fetchall()
print("\nSample mappings:")
for r in rows:
    print(f"  {r['symptom']!r:25s} → {r['name']!r} (score={r['relevance_score']})")

conn.close()
print("\n✅ Done!")
