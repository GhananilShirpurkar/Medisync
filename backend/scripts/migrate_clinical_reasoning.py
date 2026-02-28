import os
import sys
import uuid
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text
from src.db_config import DATABASE_URL
from src.models import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    engine = create_engine(DATABASE_URL)
    
    logger.info("Creating new tables...")
    Base.metadata.create_all(bind=engine, tables=[
        Base.metadata.tables['drug_combinations'],
        Base.metadata.tables['contraindication_rules'],
        Base.metadata.tables['reasoning_logs']
    ])

    with engine.begin() as conn:
        logger.info("Adding ATC columns to medicines table (if they don't exist)...")
        columns_to_add = [
            ("atc_code", "VARCHAR(7)"),
            ("atc_level_1", "VARCHAR(1)"),
            ("atc_level_2", "VARCHAR(3)"),
            ("atc_level_3", "VARCHAR(4)"),
            ("atc_level_4", "VARCHAR(5)")
        ]
        
        # Check existing columns
        result = conn.execute(text("PRAGMA table_info(medicines)"))
        existing_cols = [row[1] for row in result.fetchall()]
        
        for col_name, col_type in columns_to_add:
            if col_name not in existing_cols:
                logger.info(f"Adding column {col_name} to medicines")
                conn.execute(text(f"ALTER TABLE medicines ADD COLUMN {col_name} {col_type}"))

        logger.info("Populating ATC codes for known medicines...")
        # Common medicines in India that we want to support with reasoning
        atc_map = {
            "Paracetamol 500mg": "N02BE01",
            "Crocin 650mg": "N02BE01",
            "Dolo 650": "N02BE01",
            "Ibuprofen 400mg": "M01AE01",
            "Aspirin 75mg": "B01AC06",
            "Amlodipine 5mg": "C08CA01",
            "Amlong 5mg": "C08CA01",
            "Telmisartan 40mg": "C09CA07",
            "Telma 40": "C09CA07",
            "Metformin 500mg": "A10BA02",
            "Glycomet 500mg": "A10BA02",
            "Amoxicillin 500mg": "J01CA04",
            "Augmentin 625 Duo": "J01CR02", # Amoxicillin + clavulanic acid
            "Azithromycin 500mg": "J01FA10",
            "Azee 500": "J01FA10",
            "Pantoprazole 40mg": "A02BC02",
            "Pan 40": "A02BC02",
            "Cetirizine 10mg": "R06AE07",
            "Cetzine 10mg": "R06AE07",
            "Levocetirizine 5mg": "R06AE09",
            "Montair LC": "R03DC53", # Montelukast + Levocetirizine
            "Thyroxine 50mcg": "H03AA01",
            "Thyronorm 50mcg": "H03AA01",
            "Atorvastatin 10mg": "C10AA05",
            "Atorva 10": "C10AA05",
            "Rosuvastatin 10mg": "C10AA07",
            "Rozavel 10": "C10AA07",
            "Vitamin C 500mg": "A11GA01",
            "Limcee 500mg": "A11GA01",
            "Vitamin D3 60000 IU": "A11CC05",
            "Calcirol Sachet": "A11CC05",
            "Zincovit": "A11AA03",
            "Dolo 650mg": "N02BE01",
            "Crocin Advance": "N02BE01",
            "Sumo Tablet": "M01AX17", # Nimesulide + Paracetamol
            "Combiflam": "M01AE51", # Ibuprofen + Paracetamol
            "Benadryl Syrup": "R06AA59",
            "Corex LS Syrup": "R05CB01",
            "Eno Fruit Salt": "A02AH01",
            "Gelusil MPS": "A02AF02",
            "Pudin Hara": "A03AX13",
            "Volini Spray": "M02AA15",
            "Moov Ointment": "M02AA15",
            "Betadine Solution": "D08AG02",
            "Soframycin Cream": "D06AX09",
            "ORS Powder": "A07CA",
            "Electral Powder": "A07CA",
            "Doxycycline 100mg": "J01AA02"
        }

        for name, code in atc_map.items():
            level_1 = code[:1]
            level_2 = code[:3]
            level_3 = code[:4]
            level_4 = code[:5]
            
            conn.execute(
                text("""
                    UPDATE medicines 
                    SET atc_code = :code,
                        atc_level_1 = :l1,
                        atc_level_2 = :l2,
                        atc_level_3 = :l3,
                        atc_level_4 = :l4
                    WHERE name LIKE :name
                """),
                {"code": code, "l1": level_1, "l2": level_2, "l3": level_3, "l4": level_4, "name": f"%{name}%"}
            )
            
        logger.info("Populating base ContraindicationRules...")
        rules = [
            ("peptic_ulcer", "M01A", "absolute", "N02BE", "NSAIDs worsen ulcers, use Paracetamol"),
            ("pregnancy", "C09AA", "absolute", "C02AB", "ACE inhibitors teratogenic in pregnancy, use Methyldopa"),
            ("pregnancy", "C09CA", "absolute", "C02AB", "ARBs teratogenic in pregnancy, use Methyldopa"),
            ("liver_disease", "N02BE01", "relative", None, "Paracetamol can cause hepatotoxicity, max 2g/day"),
            ("kidney_disease", "M01A", "absolute", "N02BE", "NSAIDs reduce renal blood flow, use Paracetamol"),
            ("asthma", "M01AE", "relative", "N02BE", "Ibuprofen can trigger bronchospasm in susceptible patients")
        ]
        
        # Clear existing rules first
        conn.execute(text("DELETE FROM contraindication_rules"))
        
        for condition, pattern, severity, alt, evidence in rules:
            conn.execute(
                text("""
                    INSERT INTO contraindication_rules (id, condition_name, forbidden_atc_pattern, severity, alternative_atc_suggestion, evidence_reference)
                    VALUES (:id, :cond, :pat, :sev, :alt, :ev)
                """),
                {"id": str(uuid.uuid4()), "cond": condition, "pat": pattern, "sev": severity, "alt": alt, "ev": evidence}
            )

        logger.info("Populating DrugCombinations (FDCs & synergies)...")
        combos = [
            ("C09CA07", "C08CA01", "Hypertension", 0.90, "A", "Telmisartan + Amlodipine FDC is synergistic for BP control"),
            ("J01CA04", "J01CR02", "Bacterial Infection", 0.85, "A", "Amoxicillin + Clavulanic Acid overcomes beta-lactamase resistance"),
            ("M01AE01", "N02BE01", "Severe Pain", 0.80, "B", "Ibuprofen + Paracetamol has synergistic analgesic effect"),
            ("J01FA10", "R05CB01", "Respiratory Infection", 0.70, "C", "Azithromycin + Expectorant combo for respiratory symptoms")
        ]
        
        # Clear existing combinations first
        conn.execute(text("DELETE FROM drug_combinations"))
        
        for p_atc, s_atc, indication, score, ev, rationale in combos:
            conn.execute(
                text("""
                    INSERT INTO drug_combinations (id, primary_atc, secondary_atc, indication, synergy_score, evidence_level, rationale)
                    VALUES (:id, :patc, :satc, :ind, :score, :ev, :rat)
                """),
                {"id": str(uuid.uuid4()), "patc": p_atc, "satc": s_atc, "ind": indication, "score": score, "ev": ev, "rat": rationale}
            )

    logger.info("Migration complete!")

if __name__ == "__main__":
    migrate()
