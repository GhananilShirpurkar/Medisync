"""
INVENTORY SERVICE
=================
Application service for inventory management.

Handles inventory queries and availability checks.
"""

from typing import Dict, Any, Optional, List
import logging

from src.database import Database
from src.errors import ValidationError

logger = logging.getLogger(__name__)


class InventoryService:
    """
    Service for managing inventory.
    
    Responsibilities:
    - Query medicine availability
    - Check stock levels
    - Provide inventory analytics
    """
    
    def __init__(self):
        """Initialize inventory service."""
        self.db = Database()
    
    def get_medicine(self, name: str) -> Dict[str, Any]:
        """
        Get medicine details by name.
        
        Args:
            name: Medicine name
            
        Returns:
            Medicine details
            
        Raises:
            ValidationError: If medicine not found
        """
        medicine = self.db.get_medicine(name)
        
        if not medicine:
            raise ValidationError(f"Medicine '{name}' not found")
        
        return medicine
    
    def check_availability(
        self,
        items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Check availability for multiple items.
        
        Args:
            items: List of items with medicine_name and quantity
            
        Returns:
            Availability information
        """
        results = []
        available_count = 0
        total_count = len(items)
        
        for item in items:
            medicine_name = item.get("medicine_name", item.get("name"))
            quantity = item.get("quantity", 1)
            
            medicine = self.db.get_medicine(medicine_name)
            
            if not medicine or medicine["stock"] < quantity:
                from src.services.semantic_search_service import semantic_search_service
                
                # Use semantic search to find suitable in-stock alternatives
                search_results = semantic_search_service.search(medicine_name, top_k=5, threshold=0.65)
                alternatives = []
                for alt_name, score in search_results:
                    # Don't recommend the exact same out-of-stock medicine
                    if alt_name.lower() == medicine_name.lower():
                        continue
                        
                    alt_med = self.db.get_medicine(alt_name)
                    if alt_med and alt_med.get("stock", 0) > 0:
                        alternatives.append({
                            "name": alt_med["name"],
                            "price": alt_med["price"],
                            "stock": alt_med["stock"],
                            "compatibility_score": round(score * 100)
                        })
                
                # Sort alternatives by stock & price
                alternatives.sort(key=lambda x: (-x["stock"], x["price"]))
                
                result_item = {
                    "medicine": medicine_name,
                    "available": False,
                    "reason": "not_found" if not medicine else "insufficient_stock",
                    "stock": medicine["stock"] if medicine else 0,
                    "requested": quantity,
                    "alternatives": alternatives
                }
                
                if not alternatives:
                    # Specific requirement for no alternatives found message
                    result_item["message"] = "No therapeutically equivalent alternative found in current inventory."
                    
                results.append(result_item)
            else:
                results.append({
                    "medicine": medicine_name,
                    "available": True,
                    "stock": medicine["stock"],
                    "requested": quantity,
                    "price": medicine["price"]
                })
                available_count += 1
        
        availability_score = available_count / total_count if total_count > 0 else 0.0
        
        # Calculate Bundle Recommendations (Idea 2)
        recommendations = self.get_complementary_recommendations(items)
        
        return {
            "availability_score": availability_score,
            "available_items": available_count,
            "total_items": total_count,
            "items": results,
            "recommendations": self.get_complementary_recommendations(items)
        }

    def get_complementary_recommendations(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Get complementary recommendations based on items in cart.
        Starts with rule-based logic.
        """
        recommendations = []
        item_names = [item.get("medicine_name", item.get("name", "")).lower() for item in items]
        
        # Rule 1: Antibiotics -> Probiotics
        # We can check specific names or categories if we load them
        antibiotics = ["amoxicillin", "azithromycin", "ciprofloxacin", "augmentin"]
        if any(ab in name for ab in antibiotics for name in item_names):
            # Check availability of Probiotics
            # Ideally fetch "Probiotic" category, but hardcoding for demo speed
            probiotic = self.db.get_medicine("Enterogermina") or self.db.get_medicine("Curd") # Mock or real
            if probiotic and probiotic.get("stock", 0) > 0:
                recommendations.append({
                    "type": "complementary",
                    "trigger": "antibiotic_therapy",
                    "medicine": probiotic["name"],
                    "reason": "To protect gut health while on antibiotics."
                })
        
        # Rule 2: Painkillers -> Antacids (if high dosage or multiple)
        nsaids = ["ibuprofen", "diclofenac", "aspirin"]
        if any(nsaid in name for nsaid in nsaids for name in item_names):
             antacid = self.db.get_medicine("Pantoprazole") or self.db.get_medicine("Omee")
             if antacid and antacid.get("stock", 0) > 0:
                 recommendations.append({
                    "type": "complementary",
                    "trigger": "pain_management",
                    "medicine": antacid["name"],
                    "reason": "To prevent acidity caused by painkillers."
                })
                 
        return recommendations
    
    def search_medicines(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search medicines by name.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching medicines
        """
        # TODO: Implement search in database layer
        # For now, return empty list
        return []
    
    def get_low_stock_items(
        self,
        threshold: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get medicines with low stock.
        
        Args:
            threshold: Stock threshold
            
        Returns:
            List of low stock medicines
        """
        # TODO: Implement in database layer
        # For now, return empty list
        return []
