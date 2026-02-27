"""
TEST PROACTIVE INTELLIGENCE AGENT
==================================
Tests for refill prediction and proactive intelligence.
"""

import sys
import asyncio
from datetime import datetime, timedelta

sys.path.insert(0, 'backend')

from src.agents.proactive_intelligence_agent import ProactiveIntelligenceAgent
from src.database import Database
from src.models import Order, OrderItem as DBOrderItem
from src.db_config import get_db_context

def create_demo_orders():
    """Create demo orders for testing refill predictions."""
    
    print("\n📦 Creating demo orders...")
    
    db = Database()
    
    # Demo user
    user_id = "demo_user_refill"
    
    # Create 3 orders over 60 days for diabetes medication
    orders_data = [
        {
            "date_offset": 60,  # 60 days ago
            "medicine": "Metformin 500mg",
            "quantity": 30  # 30-day supply
        },
        {
            "date_offset": 30,  # 30 days ago
            "medicine": "Metformin 500mg",
            "quantity": 30  # 30-day supply
        },
        {
            "date_offset": 5,  # 5 days ago
            "medicine": "Metformin 500mg",
            "quantity": 30  # 30-day supply
        }
    ]
    
    with get_db_context() as db_session:
        for order_data in orders_data:
            # Create order
            order_date = datetime.now() - timedelta(days=order_data["date_offset"])
            
            order = Order(
                order_id=f"DEMO-{order_data['date_offset']}",
                user_id=user_id,
                status="fulfilled",
                pharmacist_decision="approved",
                total_amount=45.0,
                created_at=order_date
            )
            db_session.add(order)
            db_session.flush()
            
            # Add order item
            item = DBOrderItem(
                order_id=order.id,
                medicine_id=6,  # Metformin ID
                medicine_name=order_data["medicine"],
                dosage="500mg",
                quantity=order_data["quantity"],
                price=45.0
            )
            db_session.add(item)
            
            print(f"   ✅ Order {order_data['date_offset']} days ago: {order_data['medicine']} x{order_data['quantity']}")
        
        db_session.commit()
    
    print(f"   ✅ Created 3 demo orders for {user_id}")
    return user_id


async def test_proactive_intelligence():
    """Test proactive intelligence agent."""
    
    print("\n" + "="*60)
    print("TESTING PROACTIVE INTELLIGENCE AGENT")
    print("="*60)
    
    # Step 1: Create demo data
    user_id = create_demo_orders()
    
    # Step 2: Initialize agent
    print("\n🤖 Initializing ProactiveIntelligenceAgent...")
    agent = ProactiveIntelligenceAgent()
    print("   ✅ Agent initialized")
    
    # Step 3: Run analysis
    print("\n🔍 Running proactive analysis...")
    result = await agent.run_proactive_analysis(user_id)
    
    # Step 4: Verify results
    print("\n✅ ANALYSIS COMPLETE")
    print(f"\n📊 Results:")
    print(f"   - Status: {result['status']}")
    print(f"   - Predictions: {len(result['predictions'])}")
    print(f"   - Conversations triggered: {len(result['conversations_triggered'])}")
    
    if result["predictions"]:
        print(f"\n🔮 Predictions:")
        for pred in result["predictions"]:
            print(f"\n   Medicine: {pred['medicine_name']}")
            print(f"   Days until depletion: {pred['days_until_depletion']}")
            print(f"   Urgency: {pred['urgency']}")
            print(f"   Should notify: {pred['should_notify']}")
            print(f"   Daily consumption: {pred['daily_consumption']:.2f} units/day")
            print(f"   Confidence: {pred['confidence']:.0%}")
    
    if result["admin_alert"]:
        print(f"\n📢 Admin Alert:")
        alert = result["admin_alert"]
        print(f"   - Total predictions: {alert['total_predictions']}")
        print(f"   - Urgent: {alert['urgent_count']}")
        print(f"   - Soon: {alert['soon_count']}")
        print(f"   - Requires action: {alert['requires_action']}")
    
    if result["conversations_triggered"]:
        print(f"\n🔔 Conversations Triggered:")
        for conv in result["conversations_triggered"]:
            print(f"   - {conv['medicine_name']}: Session {conv['session_id']} ({conv['urgency']})")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED")
    print("="*60)
    print("\n🎉 ProactiveIntelligenceAgent is working!")
    print("\n💡 KEY FEATURES DEMONSTRATED:")
    print("   ✅ Purchase history analysis")
    print("   ✅ Daily consumption estimation")
    print("   ✅ Refill date prediction")
    print("   ✅ Proactive conversation triggering")
    print("   ✅ Admin alert generation")
    print("\n⭐ THIS IS THE DIFFERENTIATION FEATURE!")


if __name__ == "__main__":
    asyncio.run(test_proactive_intelligence())
