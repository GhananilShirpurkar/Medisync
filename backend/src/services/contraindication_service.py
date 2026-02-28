"""
CONTRAINDICATION SERVICE
========================
Provides structured rule checking against patient clinical context.
"""

from typing import List, Dict, Any
from src.db_config import get_db_context
from src.models import ContraindicationRule, Medicine
from src.clinical_models import ClinicalContext

class ContraindicationService:
    @staticmethod
    def check_contraindications(medicine_atc: str, context: ClinicalContext) -> List[Dict[str, Any]]:
        """
        Check a proposed medicine's ATC code against patient context (comorbidities, allergies).
        """
        if not medicine_atc:
            return []
            
        violations = []
        
        with get_db_context() as db:
            all_rules = db.query(ContraindicationRule).all()
            
            comorbidities = [c.lower() for c in (context.comorbidities or [])]
            allergies = [a.lower() for a in (context.allergies or [])]
            
            for rule in all_rules:
                condition_lower = rule.condition_name.lower()
                
                # Check if patient has this condition or allergy
                has_condition = False
                if condition_lower in comorbidities or condition_lower in allergies:
                    has_condition = True
                else:
                    # Fuzzy match condition
                    if any(condition_lower in c for c in comorbidities) or \
                       any(condition_lower in a for a in allergies):
                        has_condition = True
                        
                if has_condition:
                    # Check if medicine matches forbidden pattern
                    if medicine_atc.startswith(rule.forbidden_atc_pattern):
                        violation = {
                            "condition": rule.condition_name,
                            "medicine_atc": medicine_atc,
                            "severity": rule.severity,
                            "reason": rule.evidence_reference
                        }
                        
                        # Find alternative if suggested
                        if rule.alternative_atc_suggestion:
                            alt_medicine = db.query(Medicine).filter(
                                Medicine.atc_code.startswith(rule.alternative_atc_suggestion),
                                Medicine.stock > 0
                            ).first()
                            
                            if alt_medicine:
                                violation["alternative_suggestion"] = alt_medicine.name
                                violation["alternative_atc"] = alt_medicine.atc_code
                                
                        violations.append(violation)
                        
        return violations
