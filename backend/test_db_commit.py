import asyncio
from src.graph import agent_graph
from src.state import PharmacyState, OrderItem
from src.models import Medicine
from src.database import get_db_context

async def populate_db_mock_stock():
    with get_db_context() as session:
        med = session.query(Medicine).filter(Medicine.name.ilike("Paracetamol 500mg")).first()
        if med:
            med.stock = 100
        else:
            session.add(Medicine(name="Paracetamol 500mg", type="tablet", stock=100, price=15.0, requires_prescription=False))
        session.commit()

async def test_order_commit():
    await populate_db_mock_stock()
    
    # Needs to match what front_desk_agent outputs for fulfillments
    extracted = [OrderItem(medicine_name="Paracetamol 500mg", quantity=2, dosage="", reason="", in_stock=True)]
    
    state = PharmacyState(
        session_id="test_payment_order_gen",
        user_id="9067939108",
        messages=[("user", "yes please")],
        intent="known_medicine",
        patient_context={},
        input_type="voice",
        extracted_items=extracted,
        confirmation_confirmed=True
    )

    result = await agent_graph.ainvoke(state)
    print("FINISHED PIPELINE!")
    print("Result order_id:", result.get("order_id"))
    
    if result.get("order_id"):
        from src.models import Order
        with get_db_context() as db:
            o = db.query(Order).filter(Order.order_id == result["order_id"]).first()
            if o:
                print(f"Verified {o.order_id} in DB. Total: {o.total_amount}")

asyncio.run(test_order_commit())
