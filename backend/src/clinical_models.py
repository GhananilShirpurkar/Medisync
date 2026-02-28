"""
CLINICAL MODELS
===============
Pydantic models for the Clinical Reasoning Engine.
Data structures for multi-turn clinical context accumulator and reasoning responses.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ClinicalContext(BaseModel):
    """
    Accumulates patient context across conversation turns.
    """
    chief_complaint: Optional[str] = None
    symptom_duration: Optional[str] = None
    severity: Optional[str] = None  # mild/moderate/severe
    associated_symptoms: List[str] = Field(default_factory=list)
    red_flags: List[str] = Field(default_factory=list)
    
    # Patient profile
    comorbidities: List[str] = Field(default_factory=list)
    current_medications: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    pregnancy_status: Optional[str] = None
    age: Optional[int] = None
    weight: Optional[float] = None
    
    # Reasoning state
    information_gaps: List[str] = Field(default_factory=list)
    tentative_diagnosis: Optional[str] = None
    contraindications_active: List[str] = Field(default_factory=list)


class ClinicalRecommendation(BaseModel):
    """
    Evidence-based primary recommendation.
    """
    medicine: str
    atc_code: str
    confidence: str = "low"
    dose_adjustment_needed: bool = False
    contraindications_checked: List[str] = Field(default_factory=list)


class ClinicalAlternative(BaseModel):
    """
    Alternative recommendation if primary is unavailable or contraindicated.
    """
    medicine: str
    atc_code: str
    reason: str


class ClinicalResponse(BaseModel):
    """
    Complete response format from the Clinical Reasoning LLM.
    """
    reasoning_chain: List[str] = Field(default_factory=list)
    primary_recommendation: Optional[ClinicalRecommendation] = None
    alternatives_if_unavailable: List[ClinicalAlternative] = Field(default_factory=list)
    combination_suggestions: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    information_gaps: List[str] = Field(default_factory=list)
