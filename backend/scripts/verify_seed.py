
import sys
import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 1. Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 2. Add backend root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 3. Import lightweight DB config
try:
    from src.db_config import DATABASE_URL
except ImportError as e:
    logger.error(f"Failed to import modules: {e}")
    sys.exit(1)

def verify_data():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        med_count = conn.execute(text("SELECT COUNT(*) FROM medicines")).scalar()
        sym_count = conn.execute(text("SELECT COUNT(*) FROM symptom_medicine_mapping")).scalar()
        
        print(f"✅ Verified Data Functionality:")
        print(f"   - Medicines: {med_count}")
        print(f"   - Symptom Mappings: {sym_count}")
        
        # Sample query
        print("\n🔍 Sample Check (Headache):")
        result = conn.execute(text("""
            SELECT m.name, sm.relevance_score, m.dosage_form, m.strength 
            FROM symptom_medicine_mapping sm
            JOIN medicines m ON sm.medicine_id = m.id
            WHERE sm.symptom LIKE '%headache%'
            LIMIT 3
        """)).fetchall()
        for row in result:
            print(f"   - {row[0]} (Score: {row[1]}) [Form: {row[2]}, Strength: {row[3]}]")

if __name__ == "__main__":
    verify_data()
