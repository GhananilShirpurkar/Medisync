"""
DEMO DATA SEEDING SCRIPT
========================
Seeds demo-specific data for hackathon presentation.

Creates:
- Demo user with purchase history
- Realistic symptom scenarios
- Sample prescriptions
- Proactive refill scenario

Usage:
    python backend/scripts/seed_demo_data.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db_config import init_db, get_db_context
from src.models import (
    Patient, Order, OrderItem, Medicine, 
    RefillPrediction, ConversationSession, ConversationMessage,
    SymptomMedicineMapping
)


def seed_demo_user():
    """Create demo user with purchase history."""
    print("\n👤 Creating demo user...")
    
    with get_db_context() as db:
        # Create demo patient
        demo_user = Patient(
            user_id="demo_user_001",
            name="Rajesh Kumar",
            phone="+91-9876543210",
            email="rajesh.kumar@example.com",
            total_orders=3
        )
        
        # Check if user exists
        existing = db.query(Patient).filter(Patient.user_id == "demo_user_001").first()
        if existing:
            print("   Demo user already exists, updating...")
            existing.name = demo_user.name
            existing.phone = demo_user.phone
            existing.email = demo_user.email
            existing.total_orders = demo_user.total_orders
        else:
            db.add(demo_user)
        
        db.commit()
        print("✅ Demo user created: Rajesh Kumar")


def seed_demo_orders():
    """Create demo orders with purchase history."""
    print("\n📦 Creating demo orders...")
    
    with get_db_context() as db:
        # Get demo user
        demo_user = db.query(Patient).filter(Patient.user_id == "demo_user_001").first()
        if not demo_user:
            print("❌ Demo user not found")
            return
        
        # Get medicines for orders (search more flexibly)
        metformin = db.query(Medicine).filter(
            (Medicine.name.like("%Metformin%")) | 
            (Medicine.name.like("%metformin%"))
        ).first()
        
        paracetamol = db.query(Medicine).filter(
            (Medicine.name.like("%Paracetamol%")) | 
            (Medicine.name.like("%paracetamol%")) |
            (Medicine.name.like("%Crocin%"))
        ).first()
        
        aspirin = db.query(Medicine).filter(
            (Medicine.name.like("%Aspirin%")) | 
            (Medicine.name.like("%aspirin%"))
        ).first()
        
        if not metformin or not paracetamol or not aspirin:
            print("⚠️  Required medicines not found, skipping order creation")
            return
        
        # Clear existing demo orders
        db.query(Order).filter(Order.user_id == "demo_user_001").delete()
        
        # Order 1: 30 days ago (Metformin - for diabetes)
        order1 = Order(
            order_id="DEMO-ORD-001",
            user_id="demo_user_001",
            status="fulfilled",
            total_amount=500.0,
            created_at=datetime.now() - timedelta(days=30)
        )
        db.add(order1)
        db.flush()
        
        order1_item = OrderItem(
            order_id=order1.id,
            medicine_id=metformin.id,
            medicine_name=metformin.name,
            quantity=30,  # 30 tablets
            price=metformin.price,
            dosage="500mg twice daily"
        )
        db.add(order1_item)
        
        # Order 2: 15 days ago (Paracetamol - for fever)
        order2 = Order(
            order_id="DEMO-ORD-002",
            user_id="demo_user_001",
            status="fulfilled",
            total_amount=150.0,
            created_at=datetime.now() - timedelta(days=15)
        )
        db.add(order2)
        db.flush()
        
        order2_item = OrderItem(
            order_id=order2.id,
            medicine_id=paracetamol.id,
            medicine_name=paracetamol.name,
            quantity=10,
            price=paracetamol.price,
            dosage="500mg as needed"
        )
        db.add(order2_item)
        
        # Order 3: 5 days ago (Aspirin - for heart health)
        order3 = Order(
            order_id="DEMO-ORD-003",
            user_id="demo_user_001",
            status="fulfilled",
            total_amount=200.0,
            created_at=datetime.now() - timedelta(days=5)
        )
        db.add(order3)
        db.flush()
        
        order3_item = OrderItem(
            order_id=order3.id,
            medicine_id=aspirin.id,
            medicine_name=aspirin.name,
            quantity=30,
            price=aspirin.price,
            dosage="75mg daily"
        )
        db.add(order3_item)
        
        db.commit()
        print("✅ Created 3 demo orders")


def seed_refill_prediction():
    """Create proactive refill prediction for demo."""
    print("\n🔮 Creating refill prediction...")
    
    with get_db_context() as db:
        # Get demo user
        demo_user = db.query(Patient).filter(Patient.user_id == "demo_user_001").first()
        if not demo_user:
            print("❌ Demo user not found")
            return
        
        # Get Metformin (diabetes medication) - search flexibly
        metformin = db.query(Medicine).filter(
            (Medicine.name.like("%Metformin%")) | 
            (Medicine.name.like("%metformin%"))
        ).first()
        if not metformin:
            print("⚠️  Metformin not found")
            return
        
        # Clear existing predictions
        db.query(RefillPrediction).filter(RefillPrediction.user_id == "demo_user_001").delete()
        
        # Create refill prediction
        # User bought 30 tablets 30 days ago, taking 2 per day
        # Should run out today or tomorrow
        prediction = RefillPrediction(
            user_id="demo_user_001",
            medicine_name=metformin.name,
            predicted_depletion_date=datetime.now() + timedelta(days=1),  # Tomorrow
            confidence=0.92,
            reminder_sent=False
        )
        db.add(prediction)
        db.commit()
        
        print(f"✅ Refill prediction created for {metformin.name}")
        print(f"   Predicted depletion date: {prediction.predicted_depletion_date.strftime('%Y-%m-%d')}")
        print(f"   Confidence: {prediction.confidence * 100:.0f}%")


def seed_symptom_mappings():
    """Ensure key symptom mappings exist for demo."""
    print("\n🔗 Verifying symptom mappings...")
    
    with get_db_context() as db:
        # Key demo symptoms
        demo_symptoms = [
            ("headache", "Paracetamol"),
            ("fever", "Paracetamol"),
            ("pain", "Ibuprofen"),
            ("cold", "Cetirizine"),
            ("cough", "Dextromethorphan"),
        ]
        
        count = 0
        for symptom, medicine_name in demo_symptoms:
            # Find medicine
            medicine = db.query(Medicine).filter(
                Medicine.name.like(f"%{medicine_name}%")
            ).first()
            
            if not medicine:
                continue
            
            # Check if mapping exists
            existing = db.query(SymptomMedicineMapping).filter(
                SymptomMedicineMapping.symptom == symptom,
                SymptomMedicineMapping.medicine_id == medicine.id
            ).first()
            
            if not existing:
                mapping = SymptomMedicineMapping(
                    symptom=symptom,
                    medicine_id=medicine.id,
                    relevance_score=0.9
                )
                db.add(mapping)
                count += 1
        
        db.commit()
        
        if count > 0:
            print(f"✅ Added {count} symptom mappings")
        else:
            print("✅ All symptom mappings exist")


def create_demo_scenarios():
    """Create demo scenario documentation."""
    print("\n📝 Creating demo scenarios...")
    
    scenarios = """
# DEMO SCENARIOS FOR MEDISYNC

## Scenario 1: Symptom-Based Query (Primary Demo)
**User:** "I have a headache and fever"
**Expected Flow:**
1. FrontDesk Agent classifies intent as "symptom"
2. MedicalValidation Agent recommends Paracetamol
3. Inventory Agent confirms stock available
4. Timeline shows all 3 agents processing
5. Recommendations display with price and stock

**Talking Points:**
- Natural language understanding
- Symptom-based recommendations
- Real-time agent pipeline
- Stock verification
- Safety checks

---

## Scenario 2: Known Medicine Query
**User:** "Do you have paracetamol?"
**Expected Flow:**
1. FrontDesk Agent classifies intent as "known_medicine"
2. Medicine search finds Paracetamol
3. Stock information displayed
4. Price shown
5. Add to cart option

**Talking Points:**
- Direct medicine search
- Inventory integration
- Pricing transparency
- Simple user experience

---

## Scenario 3: Voice Input Demo
**User:** Hold mic button and say "I need aspirin"
**Expected Flow:**
1. Audio recorded
2. Whisper transcribes: "I need aspirin"
3. Transcription displayed with confidence
4. AI processes request
5. Response shown and spoken (if voice enabled)

**Talking Points:**
- Push-to-talk interaction
- Whisper transcription
- Hands-free experience
- Voice output option
- Accessibility feature

---

## Scenario 4: Agent Timeline Deep Dive
**User:** Any query (use Scenario 1)
**Expected Flow:**
1. Timeline appears on right side
2. Show FrontDesk agent reasoning
3. Expand MedicalValidation reasoning
4. Show confidence scores
5. Point out processing times
6. Highlight Langfuse integration

**Talking Points:**
- Complete transparency
- Agent reasoning visible
- Confidence scores
- Performance monitoring
- Observability with Langfuse

---

## Scenario 5: Proactive Refill Prediction (Advanced)
**User:** Demo user "Rajesh Kumar"
**Expected Flow:**
1. Show purchase history (3 orders)
2. Highlight Metformin order (30 days ago)
3. Show refill prediction (tomorrow)
4. Explain consumption estimation (2 tablets/day)
5. Show confidence score (92%)

**Talking Points:**
- Proactive intelligence
- Purchase history analysis
- Consumption estimation
- Predictive analytics
- Customer retention feature

---

## Demo Script (5 minutes)

### 1. Introduction (30 seconds)
- Show homepage
- Highlight 94% complete status
- Review key features
- Click Kiosk Mode

### 2. Conversational Demo (2 minutes)
- Type: "I have a headache"
- Show agent timeline
- Point out 3 agents
- Show recommendations
- Expand reasoning traces

### 3. Voice Demo (1 minute)
- Hold mic button
- Say: "Do you have aspirin?"
- Show transcription
- Show AI response
- Enable voice output

### 4. Agent Timeline (1 minute)
- Expand FrontDesk reasoning
- Show intent classification
- Expand MedicalValidation
- Show recommendation logic
- Point out processing times

### 5. Proactive Intelligence (30 seconds)
- Mention purchase history
- Show refill prediction
- Explain differentiation
- Highlight business value

---

## Backup Scenarios

### If Voice Fails:
- Continue with text input
- Mention voice is optional
- Show other features

### If API Slow:
- Explain LLM processing
- Show agent timeline updating
- Highlight real-time nature

### If Questions About Data:
- 77 medicines in database
- 146 symptom mappings
- Real Indian medicine names
- Production-ready scale

---

## Key Talking Points

### Technical:
- 6 specialized AI agents
- LangGraph orchestration
- Gemini 2.5 Flash reasoning
- Langfuse observability
- Whisper transcription
- Browser SpeechSynthesis

### Business:
- Pharmacy automation
- Customer self-service
- Reduced wait times
- Improved accuracy
- Better customer experience
- Proactive engagement

### Differentiation:
- Multi-agent architecture
- Complete observability
- Voice input/output
- Proactive refill prediction
- Real-time agent timeline
- Production-ready quality

---

## Demo Tips

1. **Start Strong:** Homepage makes great first impression
2. **Show Timeline:** Most impressive visual feature
3. **Use Voice:** Demonstrates technical depth
4. **Expand Reasoning:** Shows transparency
5. **Mention Langfuse:** Observability is critical
6. **Highlight Proactive:** Differentiation feature
7. **Stay Calm:** If issues, pivot to working features
8. **Time Management:** Keep under 5 minutes
9. **Engage Judges:** Ask if they want to see specific features
10. **End Strong:** Summarize key achievements

---

**Status:** Demo scenarios ready
**Confidence:** HIGH
**Estimated Demo Time:** 5 minutes
"""
    
    # Save scenarios
    scenarios_path = Path(__file__).parent.parent.parent / "DEMO-SCENARIOS.md"
    scenarios_path.write_text(scenarios)
    
    print(f"✅ Demo scenarios saved to: {scenarios_path}")


def main():
    """Main demo seeding function."""
    print("=" * 60)
    print("DEMO DATA SEEDING")
    print("=" * 60)
    
    # Initialize database
    init_db()
    
    # Seed demo data
    seed_demo_user()
    seed_demo_orders()
    seed_refill_prediction()
    seed_symptom_mappings()
    create_demo_scenarios()
    
    print("\n" + "=" * 60)
    print("✅ DEMO DATA SEEDING COMPLETE")
    print("=" * 60)
    print("\nDemo User:")
    print("  User ID: demo_user_001")
    print("  Name: Rajesh Kumar")
    print("  Orders: 3 (Metformin, Paracetamol, Aspirin)")
    print("  Refill Prediction: Metformin (tomorrow)")
    print("\nDemo Scenarios:")
    print("  See DEMO-SCENARIOS.md for complete demo script")
    print("\nReady for demo! 🎉")


if __name__ == "__main__":
    main()

