"""
INTERACTION SERVICE
===================
Basic drug-drug interaction checker.
"""

from typing import List, Dict, Any
from src.db_config import get_db_context
from src.models import Medicine

class InteractionService:
    @staticmethod
    def check_interactions(proposed_medicine_name: str, proposed_atc: str, current_medications: List[str]) -> List[Dict[str, Any]]:
        """
        Check proposed medicine against current medications.
        This provides a base-level interaction check utilizing ATC groups.
        """
        if not proposed_atc or not current_medications:
            return []
            
        interactions = []
        
        # Hardcoded critical interactions for demonstration
        # In a real app, this would query a DrugBank/FDA database or robust API
        critical_pairs = [
            ("N02BA", "B01AA", "Aspirin + Warfarin: High risk of severe bleeding."), # Salicylic acid + Antithrombotic
            ("C09AA", "C03EA", "ACE Inhibitor + Potassium Sparing Diuretic: Risk of hyperkalemia."),
            ("J01MA", "M01A", "Fluoroquinolones + NSAIDs: Increased risk of CNS stimulation and seizures.")
        ]
        
        with get_db_context() as db:
            for current_med in current_medications:
                # Find current med ATC
                med_record = db.query(Medicine).filter(Medicine.name.ilike(f"%{current_med}%")).first()
                if not med_record or not med_record.atc_code:
                    continue
                    
                current_atc = med_record.atc_code
                
                # Check against rules
                for pat1, pat2, warning in critical_pairs:
                    if (proposed_atc.startswith(pat1) and current_atc.startswith(pat2)) or \
                       (proposed_atc.startswith(pat2) and current_atc.startswith(pat1)):
                        interactions.append({
                            "medication": current_med,
                            "severity": "major",
                            "warning": warning
                        })
                        
        return interactions
