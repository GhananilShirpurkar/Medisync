"""
REPLACEMENT MODELS
==================
Pydantic models for the medicine replacement engine.

A ReplacementResponse is the single output of find_equivalent_replacement().
It encodes the result of all safety gates in one structured object.
"""

from typing import Literal, Optional, List
from pydantic import BaseModel


class ReplacementOption(BaseModel):
    """A single alternative medicine option."""
    name: str
    price: float
    confidence: Literal["high", "medium", "low"]
    reasoning: str
    price_difference_percent: float
    requires_pharmacist_override: bool


class ReplacementResponse(BaseModel):
    """
    Result of the replacement engine, including the best pick and a list of options.
    """

    replacement_found: bool
    original: str
    suggested: Optional[str] = None
    suggested_price: float = 0.0
    confidence: Literal["high", "medium", "low"] = "low"
    reasoning: str = ""
    price_difference_percent: float = 0.0
    requires_pharmacist_override: bool = True
    suggestions: List[ReplacementOption] = []
