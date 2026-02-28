"""
LANGGRAPH ORCHESTRATION
=======================
Defines the agent workflow as a deterministic state machine.

Flow:
START
  -> Medical Validation Agent (Safety + Compliance)
  -> Inventory Agent (Stock Check + Alternatives)
  -> Fulfillment Agent (Order Creation + Event Emission)
  -> END

Routing Logic:
- Medical Validation: rejected → END (emit rejection event)
- Medical Validation: approved/needs_review → Inventory
- Inventory: no stock → END (emit rejection event)
- Inventory: has stock → Fulfillment
- Fulfillment: always → END (emit order created event)

Note: Notifications are now event-driven and decoupled from the graph.
"""

from typing import Literal
from langgraph.graph import StateGraph, END

from src.state import PharmacyState
from src.agents.medical_validator_agent import medical_validation_agent
from src.agents.risk_scoring_agent import run_risk_scoring_agent
from src.agents.inventory_and_rules_agent import inventory_agent
from src.agents.fulfillment_agent import fulfillment_agent
from src.events.event_bus import get_event_bus
from src.events.event_types import OrderRejectedEvent
from src.events.handlers.notification_handler import register_notification_handlers


# ------------------------------------------------------------------
# ROUTING LOGIC
# ------------------------------------------------------------------
def route_after_validation(state: PharmacyState) -> Literal["risk_scoring", "end"]:
    """
    Decide next step based on medical validation decision.
    
    - rejected: Emit rejection event and stop (safety concern)
    - continue to risk assessment
    """
    if state.pharmacist_decision == "rejected":
        # Emit rejection event
        event_bus = get_event_bus()
        event = OrderRejectedEvent(
            user_id=state.user_id or "anonymous",
            reason="prescription_rejected",
            details={"safety_flags": state.safety_flags}
        )
        event_bus.publish(event)
        return "end"
    return "risk_scoring"


def route_after_risk_scoring(state: PharmacyState) -> Literal["inventory", "end"]:
    """
    Decide next step based on risk level.
    """
    if state.risk_level == "critical":
        # Order already blocked by risk_scoring_agent (pharmacist_decision=rejected)
        event_bus = get_event_bus()
        event = OrderRejectedEvent(
            user_id=state.user_id or "anonymous",
            reason="critical_risk_blocked",
            details={"risk_score": state.risk_score, "factors": state.risk_factors_triggered}
        )
        event_bus.publish(event)
        return "end"
    return "inventory"


def route_after_inventory(state: PharmacyState) -> Literal["fulfillment", "end"]:
    """
    Decide next step based on inventory availability.
    
    - No items available: Emit rejection event and stop
    - Some items available: Continue to fulfillment
    """
    inventory_metadata = state.trace_metadata.get("inventory_agent", {})
    availability_score = inventory_metadata.get("availability_score", 0.0)
    
    if availability_score == 0.0:
        # Emit rejection event
        event_bus = get_event_bus()
        event = OrderRejectedEvent(
            user_id=state.user_id or "anonymous",
            reason="no_stock_available",
            details={"availability_score": availability_score}
        )
        event_bus.publish(event)
        return "end"
    return "fulfillment"


# ------------------------------------------------------------------
# GRAPH DEFINITION
# ------------------------------------------------------------------
def build_graph():
    """
    Builds and compiles the LangGraph state machine.
    
    Returns:
        Compiled LangGraph workflow
    """
    # Initialize event bus and register handlers
    event_bus = get_event_bus()
    register_notification_handlers(event_bus)

    graph = StateGraph(PharmacyState)

    # --- Nodes ---
    graph.add_node("medical_validation", medical_validation_agent)
    graph.add_node("risk_scoring", run_risk_scoring_agent)
    graph.add_node("inventory", inventory_agent)
    graph.add_node("fulfillment", fulfillment_agent)

    # --- Edges ---
    graph.set_entry_point("medical_validation")

    # Medical Validation → Risk Scoring (if approved/needs_review) or END (if rejected)
    graph.add_conditional_edges(
        "medical_validation",
        route_after_validation,
        {
            "risk_scoring": "risk_scoring",
            "end": END,
        },
    )

    # Risk Scoring → Inventory (if not critical) or END (if critical)
    graph.add_conditional_edges(
        "risk_scoring",
        route_after_risk_scoring,
        {
            "inventory": "inventory",
            "end": END,
        },
    )

    # Inventory → Fulfillment (if stock available) or END (if no stock)
    graph.add_conditional_edges(
        "inventory",
        route_after_inventory,
        {
            "fulfillment": "fulfillment",
            "end": END,
        },
    )

    # Fulfillment → END (events are emitted automatically)
    graph.add_edge("fulfillment", END)

    return graph.compile()


# ------------------------------------------------------------------
# SINGLETON (used by FastAPI)
# ------------------------------------------------------------------
agent_graph = build_graph()


# ------------------------------------------------------------------
# HELPER FUNCTION FOR TESTING
# ------------------------------------------------------------------
def run_workflow(state: PharmacyState) -> PharmacyState:
    """
    Run the complete workflow for testing.
    
    Args:
        state: Initial pharmacy state
        
    Returns:
        Final state after workflow execution
    """
    result = agent_graph.invoke(state)
    return result

