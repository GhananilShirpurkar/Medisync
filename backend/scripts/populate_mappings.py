import pandas as pd
import sqlite3
import os
from datetime import datetime

# Paths
DB_PATH = 'backend/hackfusion.db'
CSV_PATH = 'new data/symptom_medicine_mapping.csv'

def populate():
    if not os.path.exists(CSV_PATH):
        print(f"CSV file not found at {CSV_PATH}")
        return

    print(f"Reading {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH)
    
    # Mapping CSV columns to DB columns
    # CSV: ['id', 'symptom', 'medicine_id', 'relevence_score', 'notes', 'created_at']
    
    mapping = {
        'relevence_score': 'relevance_score'
    }
    df = df.rename(columns=mapping)
    
    # Ensure date columns are strings for sqlite
    if 'created_at' in df.columns:
        df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print(f"Inserting/Updating {len(df)} records into 'symptom_medicine_mapping' table...")
    
    success_count = 0
    
    for _, row in df.iterrows():
        # Using columns from CSV (except id which we handle in DB)
        # We'll use symptom and medicine_id for the conflict target
        data = {
            'symptom': row['symptom'],
            'medicine_id': row['medicine_id'],
            'relevance_score': row['relevance_score'],
            'notes': row['notes'],
            'created_at': row['created_at']
        }
        
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        values = tuple(data.values())
        
        # Upsert logic (requires the unique index we just created)
        sql = f"""
        INSERT INTO symptom_medicine_mapping ({columns})
        VALUES ({placeholders})
        ON CONFLICT(symptom, medicine_id) DO UPDATE SET
        relevance_score = excluded.relevance_score,
        notes = excluded.notes,
        created_at = excluded.created_at
        """
        
        try:
            cursor.execute(sql, values)
            success_count += 1
        except Exception as e:
            print(f"Error mapping {row['symptom']} to {row['medicine_id']}: {e}")

    conn.commit()
    conn.close()
    print(f"Done! Processed {success_count} records.")

if __name__ == "__main__":
    populate()
