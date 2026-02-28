"""
CART MANAGER SERVICE
====================
Manages the state of the shopping cart across a user session.
Handles dynamic addition, removal, and quantity updates of medicine items.
"""

from typing import List, Dict, Optional, Any
from src.state import OrderItem
from src.services import conversation_service


class CartManager:
    """Manages the shopping cart state stored in the conversation session."""

    def __init__(self):
        pass

    def get_cart(self, session_id: str) -> List[OrderItem]:
        """Retrieve the current cart for a session."""
        session_data = conversation_service.get_session(session_id)
        cart_data = session_data.get("pending_cart") or []
        
        # Convert raw dicts back to OrderItems
        items = []
        for item_data in cart_data:
            items.append(OrderItem(**item_data))
        return items

    def _save_cart(self, session_id: str, items: List[OrderItem]) -> None:
        """Save the cart state to the database."""
        # Convert OrderItems to dicts for JSON storage
        cart_data = [item.model_dump() for item in items]
        conversation_service.update_session_metadata(
            session_id,
            {"pending_cart": cart_data}
        )

    def process_updates(self, session_id: str, new_items: List[OrderItem]) -> List[OrderItem]:
        """
        Merge new items from the FrontDeskAgent into the existing cart.
        Returns the completely updated cart list.
        
        Rules:
        - If medicine exists: add quantity.
        - If new medicine: add to list.
        """
        current_cart = self.get_cart(session_id)
        
        # Map for quick lookup
        cart_map = {item.medicine_name.lower(): item for item in current_cart}
        
        for new_item in new_items:
            key = new_item.medicine_name.lower()
            if key in cart_map:
                # Increment quantity
                cart_map[key].quantity += new_item.quantity
            else:
                cart_map[key] = new_item
                
        updated_cart = list(cart_map.values())
        self._save_cart(session_id, updated_cart)
        
        return updated_cart

    def override_cart(self, session_id: str, items: List[OrderItem]) -> None:
        """Completely override the cart (useful for inventory replacements)."""
        self._save_cart(session_id, items)

    def clear_cart(self, session_id: str) -> None:
        """Empty the cart (after successful order)."""
        self._save_cart(session_id, [])

    def format_cart_summary_for_llm(self, cart: List[OrderItem]) -> str:
        """Format the cart contents into a string useful for prompts."""
        if not cart:
            return "Cart is empty."
            
        summary = "Current Cart Items:\n"
        for item in cart:
            dosage_str = f" ({item.dosage})" if item.dosage else ""
            summary += f"- {item.medicine_name}{dosage_str} x{item.quantity}\n"
        return summary

    def parse_complex_modifiers(self, text: str, current_cart: List[OrderItem]) -> List[OrderItem]:
        """
        Future enhancement logic for "remove 1", "change quantity to 4", etc.
        For now, this relies heavily on FrontDeskAgent's extraction, 
        and basically trusts the pipeline.
        """
        pass

# Global instance
cart_manager = CartManager()
