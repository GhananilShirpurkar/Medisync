"""
REPLACEMENT MODELS
==================
Pydantic models for the medicine replacement engine.

A ReplacementResponse is the single output of find_equivalent_replacement().
It encodes the result of all safety gates in one structured object.
"""

from typing import Literal, Optional
from pydantic import BaseModel


class ReplacementResponse(BaseModel):
    """
    Single confident replacement suggestion for an out-of-stock medicine.

    Fields
    ------
    replacement_found
        False when no same-category in-stock alternative passed all safety gates.
    original
        The medicine that could not be fulfilled.
    suggested
        Name of the recommended replacement (None when replacement_found=False).
    confidence
        'high'   → same active ingredient + same category + no contraindications
        'medium' → same category + same generic_equivalent + no contraindications
        'low'    → same category only (also triggers pharmacist override)
    reasoning
        Human-readable explanation surfaced to the dispensing agent/UI.
    price_difference_percent
        ((suggested_price - original_price) / original_price) * 100.
        Negative = cheaper, positive = more expensive.
        0.0 when replacement_found=False.
    requires_pharmacist_override
        True whenever confidence is 'medium' or 'low', or when original
        required a prescription.
    """

    replacement_found: bool
    original: str
    suggested: Optional[str] = None
    suggested_price: float = 0.0
    confidence: Literal["high", "medium", "low"] = "low"
    reasoning: str = ""
    price_difference_percent: float = 0.0
    requires_pharmacist_override: bool = True
