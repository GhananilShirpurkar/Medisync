"""
ATC SERVICE
===========
Provides helpers for working with Anatomical Therapeutic Chemical (ATC) classification system.
"""

from typing import Optional, Dict, List, Any
from sqlalchemy import or_, and_
from src.db_config import get_db_context
from src.models import Medicine, DrugCombination

class ATCService:
    @staticmethod
    def get_atc_hierarchy(atc_code: str) -> Dict[str, str]:
        """Parse an ATC code into its hierarchy levels."""
        if not atc_code or len(atc_code) < 7:
            return {}
            
        return {
            "level_1": atc_code[:1],   # Anatomical main group
            "level_2": atc_code[:3],   # Therapeutic subgroup
            "level_3": atc_code[:4],   # Pharmacological subgroup
            "level_4": atc_code[:5],   # Chemical subgroup
            "level_5": atc_code[:7]    # Chemical substance
        }
        
    @staticmethod
    def are_same_molecule(atc1: str, atc2: str) -> bool:
        """Check if two ATC codes represent the same chemical substance."""
        if not atc1 or not atc2 or len(atc1) < 7 or len(atc2) < 7:
            return False
        return atc1[:7] == atc2[:7]
        
    @staticmethod
    def are_same_class(atc1: str, atc2: str) -> bool:
        """Check if two ATC codes belong to the same chemical subgroup."""
        if not atc1 or not atc2 or len(atc1) < 5 or len(atc2) < 5:
            return False
        return atc1[:5] == atc2[:5]

    @staticmethod
    def get_synergistic_combinations(primary_atc: str, indication: str) -> List[Dict[str, Any]]:
        """
        Check if the requested ATC code has any known fixed-dose combinations or synergistic pairs
        for a specific indication in the database.
        """
        with get_db_context() as db:
            combos = db.query(DrugCombination).filter(
                or_(
                    DrugCombination.primary_atc == primary_atc,
                    DrugCombination.secondary_atc == primary_atc
                ),
                DrugCombination.indication.ilike(f"%{indication}%")
            ).order_by(DrugCombination.synergy_score.desc()).all()
            
            results = []
            for combo in combos:
                # Find which is the 'other' drug
                secondary_target = combo.secondary_atc if combo.primary_atc == primary_atc else combo.primary_atc
                
                # Try to find a medicine covering this combo (FDC) or the secondary drug
                # For demo, just return the complementary ATC code and rationale
                results.append({
                    "complementary_atc": secondary_target,
                    "synergy_score": combo.synergy_score,
                    "evidence_level": combo.evidence_level,
                    "guideline_source": combo.guideline_source,
                    "rationale": combo.rationale
                })
                
            return results
