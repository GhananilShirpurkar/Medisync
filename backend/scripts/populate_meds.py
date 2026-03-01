import pandas as pd
import sqlite3
import os
from datetime import datetime

# Paths
DB_PATH = 'backend/hackfusion.db'
EXCEL_PATH = 'new data/meds.xlsx'

def populate():
    if not os.path.exists(EXCEL_PATH):
        print(f"Excel file not found at {EXCEL_PATH}")
        return

    print(f"Reading {EXCEL_PATH}...")
    df = pd.read_excel(EXCEL_PATH)
    
    # Mapping Excel columns to DB columns
    # Excel: ['id', 'name', 'category', 'manufacturer', 'price', 'stock', 'requires_prescriptuon', 'description', 'indications', 'generic_equivalent', 'contradictions', 'side_effects', 'dosage_form', 'strength', 'active_ingredients', 'created_at', 'updated_at', 'atc_code', 'atc_level_1', 'atc_level_2', 'atc_level_3', 'atc_level_4']
    
    mapping = {
        'requires_prescriptuon': 'requires_prescription',
        'contradictions': 'contraindications'
    }
    df = df.rename(columns=mapping)
    
    # Ensure date columns are strings for sqlite or handled correctly
    # SQLite DATE/DATETIME columns often take ISO strings
    for col in ['created_at', 'updated_at']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col]).dt.strftime('%Y-%m-%d %H:%M:%S')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print(f"Inserting/Updating {len(df)} records into 'medicines' table...")
    
    success_count = 0
    update_count = 0
    
    for _, row in df.iterrows():
        data = row.to_dict()
        
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        values = tuple(data.values())
        
        # Upsert logic (using ID as conflict target)
        update_stmt = ', '.join([f"{k} = excluded.{k}" for k in data.keys() if k != 'id'])
        
        sql = f"""
        INSERT INTO medicines ({columns})
        VALUES ({placeholders})
        ON CONFLICT(id) DO UPDATE SET
        {update_stmt}
        """
        
        try:
            cursor.execute(sql, values)
            success_count += 1
        except Exception as e:
            print(f"Error inserting ID {data.get('id')} ({data.get('name')}): {e}")

    conn.commit()
    conn.close()
    print(f"Done! Processed {success_count} records.")

if __name__ == "__main__":
    populate()
