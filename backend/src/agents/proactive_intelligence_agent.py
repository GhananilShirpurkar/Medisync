"""
PROACTIVE INTELLIGENCE AGENT
=============================
Agent 6: Predictive refill engine (DIFFERENTIATION FEATURE)

Responsibilities:
1. Analyze purchase history
2. Estimate daily consumption
3. Predict refill date
4. Trigger refill conversation
5. Generate admin alerts

This is the KEY DIFFERENTIATION feature - most teams won't have this.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import func

from src.db_config import get_db_context
from src.models import Order, OrderItem, Medicine, RefillPrediction
from src.services.conversation_service import ConversationService


class ProactiveIntelligenceAgent:
    """
    Proactive Intelligence Agent - Predictive refill engine.
    
    This agent analyzes purchase history to predict when users will
    need refills and proactively triggers conversations.
    
    KEY DIFFERENTIATION: Most teams won't implement this properly.
    """
    
    def __init__(self):
        """Initialize proactive intelligence agent."""
        self.conversation_service = ConversationService()
    
    def analyze_user_history(self, user_id: str) -> Dict[str, Any]:
        """
        Analyze complete purchase history for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dict with analysis results:
            {
                "user_id": str,
                "total_orders": int,
                "medicines_purchased": List[Dict],
                "recurring_medicines": List[Dict],
                "last_order_date": str,
                "analysis_timestamp": str
            }
        """
        with get_db_context() as db:
            # Get all orders for user
            orders = db.query(Order).filter(
                Order.user_id == user_id
            ).order_by(Order.created_at.desc()).all()
            
            if not orders:
                return {
                    "user_id": user_id,
                    "total_orders": 0,
                    "medicines_purchased": [],
                    "recurring_medicines": [],
                    "last_order_date": None,
                    "analysis_timestamp": datetime.now().isoformat()
                }
            
            # Aggregate medicine purchases
            medicine_purchases = {}
            
            for order in orders:
                for item in order.items:
                    if item.medicine_name not in medicine_purchases:
                        medicine_purchases[item.medicine_name] = {
                            "medicine_name": item.medicine_name,
                            "total_quantity": 0,
                            "purchase_count": 0,
                            "last_purchase_date": None,
                            "first_purchase_date": None,
                            "average_quantity": 0.0
                        }
                    
                    medicine_purchases[item.medicine_name]["total_quantity"] += item.quantity
                    medicine_purchases[item.medicine_name]["purchase_count"] += 1
                    
                    # Update dates
                    purchase_date = order.created_at
                    if not medicine_purchases[item.medicine_name]["last_purchase_date"]:
                        medicine_purchases[item.medicine_name]["last_purchase_date"] = purchase_date
                    
                    medicine_purchases[item.medicine_name]["first_purchase_date"] = purchase_date
            
            # Calculate averages and identify recurring medicines
            medicines_list = []
            recurring_medicines = []
            
            for med_name, data in medicine_purchases.items():
                data["average_quantity"] = data["total_quantity"] / data["purchase_count"]
                
                # Convert dates to ISO format
                if data["last_purchase_date"]:
                    data["last_purchase_date"] = data["last_purchase_date"].isoformat()
                if data["first_purchase_date"]:
                    data["first_purchase_date"] = data["first_purchase_date"].isoformat()
                
                medicines_list.append(data)
                
                # Recurring if purchased 2+ times
                if data["purchase_count"] >= 2:
                    recurring_medicines.append(data)
            
            return {
                "user_id": user_id,
                "total_orders": len(orders),
                "medicines_purchased": medicines_list,
                "recurring_medicines": recurring_medicines,
                "last_order_date": orders[0].created_at.isoformat() if orders else None,
                "analysis_timestamp": datetime.now().isoformat()
            }
    
    def estimate_daily_consumption(
        self,
        medicine_name: str,
        purchase_history: List[Dict]
    ) -> Dict[str, Any]:
        """
        Estimate daily consumption rate for a medicine.
        
        Args:
            medicine_name: Medicine name
            purchase_history: List of purchase records
            
        Returns:
            Dict with consumption estimate:
            {
                "medicine_name": str,
                "daily_consumption": float,
                "confidence": float,
                "method": str,
                "reasoning": str
            }
        """
        # Filter purchases for this medicine
        medicine_purchases = [
            p for p in purchase_history
            if p["medicine_name"] == medicine_name
        ]
        
        if not medicine_purchases:
            return {
                "medicine_name": medicine_name,
                "daily_consumption": 0.0,
                "confidence": 0.0,
                "method": "no_data",
                "reasoning": "No purchase history available"
            }
        
        if len(medicine_purchases) == 1:
            # Single purchase - assume standard dosage
            # Most medicines are taken 1-3 times daily
            # Conservative estimate: 1 unit per day
            return {
                "medicine_name": medicine_name,
                "daily_consumption": 1.0,
                "confidence": 0.5,
                "method": "single_purchase_estimate",
                "reasoning": "Only one purchase - assuming 1 unit/day"
            }
        
        # Multiple purchases - calculate from intervals
        purchases = sorted(
            medicine_purchases,
            key=lambda x: x["last_purchase_date"]
        )
        
        # Calculate time between purchases and quantities
        intervals = []
        for i in range(len(purchases) - 1):
            date1 = datetime.fromisoformat(purchases[i]["last_purchase_date"])
            date2 = datetime.fromisoformat(purchases[i + 1]["last_purchase_date"])
            days_between = (date2 - date1).days
            
            if days_between > 0:
                # Quantity from first purchase should last until second purchase
                quantity = purchases[i]["total_quantity"]
                daily_rate = quantity / days_between
                intervals.append({
                    "days": days_between,
                    "quantity": quantity,
                    "daily_rate": daily_rate
                })
        
        if not intervals:
            # Fallback to average quantity
            avg_quantity = sum(p["total_quantity"] for p in purchases) / len(purchases)
            return {
                "medicine_name": medicine_name,
                "daily_consumption": avg_quantity / 30,  # Assume 30-day supply
                "confidence": 0.6,
                "method": "average_quantity",
                "reasoning": f"Based on average quantity of {avg_quantity:.1f} units"
            }
        
        # Calculate weighted average daily consumption
        total_days = sum(i["days"] for i in intervals)
        weighted_consumption = sum(
            i["daily_rate"] * (i["days"] / total_days)
            for i in intervals
        )
        
        # Confidence based on number of data points
        confidence = min(0.9, 0.5 + (len(intervals) * 0.1))
        
        return {
            "medicine_name": medicine_name,
            "daily_consumption": round(weighted_consumption, 2),
            "confidence": confidence,
            "method": "interval_analysis",
            "reasoning": f"Based on {len(intervals)} purchase intervals"
        }
    
    def predict_refill_date(
        self,
        medicine_name: str,
        last_purchase_date: str,
        last_purchase_quantity: int,
        daily_consumption: float
    ) -> Dict[str, Any]:
        """
        Predict when user will need a refill.
        
        Args:
            medicine_name: Medicine name
            last_purchase_date: Date of last purchase (ISO format)
            last_purchase_quantity: Quantity purchased
            daily_consumption: Estimated daily consumption rate
            
        Returns:
            Dict with prediction:
            {
                "medicine_name": str,
                "predicted_depletion_date": str,
                "days_until_depletion": int,
                "should_notify": bool,
                "urgency": str,
                "confidence": float
            }
        """
        last_purchase = datetime.fromisoformat(last_purchase_date)
        
        # Calculate depletion date
        if daily_consumption > 0:
            days_supply = last_purchase_quantity / daily_consumption
            depletion_date = last_purchase + timedelta(days=days_supply)
        else:
            # Fallback: assume 30-day supply
            depletion_date = last_purchase + timedelta(days=30)
        
        # Calculate days until depletion
        days_until = (depletion_date - datetime.now()).days
        
        # Determine if should notify (7 days before depletion)
        should_notify = days_until <= 7 and days_until >= 0
        
        # Determine urgency
        if days_until < 0:
            urgency = "overdue"
        elif days_until <= 3:
            urgency = "urgent"
        elif days_until <= 7:
            urgency = "soon"
        else:
            urgency = "normal"
        
        # Confidence based on consumption estimate quality
        confidence = 0.7 if daily_consumption > 0 else 0.5
        
        return {
            "medicine_name": medicine_name,
            "predicted_depletion_date": depletion_date.isoformat(),
            "days_until_depletion": days_until,
            "should_notify": should_notify,
            "urgency": urgency,
            "confidence": confidence,
            "last_purchase_date": last_purchase_date,
            "last_purchase_quantity": last_purchase_quantity,
            "daily_consumption": daily_consumption
        }
    
    def generate_refill_predictions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Generate refill predictions for all recurring medicines.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of refill predictions
        """
        # Analyze user history
        history = self.analyze_user_history(user_id)
        
        predictions = []
        
        for medicine in history["recurring_medicines"]:
            # Estimate consumption
            consumption = self.estimate_daily_consumption(
                medicine["medicine_name"],
                history["medicines_purchased"]
            )
            
            # Predict refill date
            prediction = self.predict_refill_date(
                medicine_name=medicine["medicine_name"],
                last_purchase_date=medicine["last_purchase_date"],
                last_purchase_quantity=medicine["average_quantity"],
                daily_consumption=consumption["daily_consumption"]
            )
            
            # Add consumption info
            prediction["consumption_estimate"] = consumption
            
            predictions.append(prediction)
        
        # Sort by urgency
        urgency_order = {"overdue": 0, "urgent": 1, "soon": 2, "normal": 3}
        predictions.sort(key=lambda x: urgency_order.get(x["urgency"], 4))
        
        return predictions
    
    def save_predictions(self, user_id: str, predictions: List[Dict]) -> bool:
        """
        Save refill predictions to database.
        
        Args:
            user_id: User identifier
            predictions: List of predictions
            
        Returns:
            True if successful
        """
        with get_db_context() as db:
            # Clear old predictions for this user
            db.query(RefillPrediction).filter(
                RefillPrediction.user_id == user_id
            ).delete()
            
            # Save new predictions
            for pred in predictions:
                refill_pred = RefillPrediction(
                    user_id=user_id,
                    medicine_name=pred["medicine_name"],
                    predicted_depletion_date=datetime.fromisoformat(
                        pred["predicted_depletion_date"]
                    ),
                    confidence=pred["confidence"],
                    reminder_sent=False
                )
                db.add(refill_pred)
            
            db.commit()
            return True
    
    def trigger_refill_conversation(
        self,
        user_id: str,
        prediction: Dict[str, Any]
    ) -> Optional[str]:
        """
        Trigger a proactive refill conversation.
        
        Args:
            user_id: User identifier
            prediction: Refill prediction
            
        Returns:
            Session ID if conversation created, None otherwise
        """
        # Create new conversation session
        session_id = self.conversation_service.create_session(user_id)
        
        # Generate refill message
        medicine_name = prediction["medicine_name"]
        days_until = prediction["days_until_depletion"]
        urgency = prediction["urgency"]
        
        if urgency == "overdue":
            message = f"⚠️ Your {medicine_name} supply may have run out. Would you like to reorder?"
        elif urgency == "urgent":
            message = f"🔔 Your {medicine_name} is running low ({days_until} days left). Time to refill?"
        elif urgency == "soon":
            message = f"📅 Your {medicine_name} will run out in {days_until} days. Would you like to order a refill?"
        else:
            message = f"💊 Reminder: You may need to refill {medicine_name} soon."
        
        # Add proactive message
        self.conversation_service.add_message(
            session_id=session_id,
            role="assistant",
            content=message,
            agent_name="proactive_intelligence",
            extra_data={
                "prediction": prediction,
                "trigger_type": "refill_reminder"
            }
        )
        
        # Update session intent
        self.conversation_service.update_session(
            session_id=session_id,
            intent="refill"
        )
        
        return session_id
    
    def generate_admin_alert(
        self,
        user_id: str,
        predictions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate admin alert for refill predictions.
        
        Args:
            user_id: User identifier
            predictions: List of predictions
            
        Returns:
            Admin alert dict
        """
        # Filter urgent predictions
        urgent = [p for p in predictions if p["urgency"] in ["overdue", "urgent"]]
        soon = [p for p in predictions if p["urgency"] == "soon"]
        
        return {
            "alert_type": "refill_predictions",
            "user_id": user_id,
            "total_predictions": len(predictions),
            "urgent_count": len(urgent),
            "soon_count": len(soon),
            "urgent_medicines": [p["medicine_name"] for p in urgent],
            "soon_medicines": [p["medicine_name"] for p in soon],
            "generated_at": datetime.now().isoformat(),
            "requires_action": len(urgent) > 0
        }
    
    async def run_proactive_analysis(self, user_id: str) -> Dict[str, Any]:
        """
        Run complete proactive analysis for a user.
        
        This is the main entry point for the agent.
        
        Args:
            user_id: User identifier
            
        Returns:
            Complete analysis results
        """
        print(f"\n{'='*60}")
        print(f"PROACTIVE INTELLIGENCE AGENT")
        print(f"{'='*60}")
        print(f"User: {user_id}")
        
        # Step 1: Analyze history
        print("\n📊 Analyzing purchase history...")
        history = self.analyze_user_history(user_id)
        print(f"   ✅ Total orders: {history['total_orders']}")
        print(f"   ✅ Medicines purchased: {len(history['medicines_purchased'])}")
        print(f"   ✅ Recurring medicines: {len(history['recurring_medicines'])}")
        
        if not history["recurring_medicines"]:
            print("\n   ℹ️  No recurring medicines found")
            print(f"{'='*60}\n")
            return {
                "user_id": user_id,
                "predictions": [],
                "admin_alert": None,
                "conversations_triggered": [],
                "status": "no_recurring_medicines"
            }
        
        # Step 2: Generate predictions
        print("\n🔮 Generating refill predictions...")
        predictions = self.generate_refill_predictions(user_id)
        print(f"   ✅ Generated {len(predictions)} predictions")
        
        for pred in predictions:
            urgency_icon = {
                "overdue": "🔴",
                "urgent": "🟠",
                "soon": "🟡",
                "normal": "🟢"
            }.get(pred["urgency"], "⚪")
            
            print(f"   {urgency_icon} {pred['medicine_name']}: {pred['days_until_depletion']} days")
        
        # Step 3: Save predictions
        print("\n💾 Saving predictions...")
        self.save_predictions(user_id, predictions)
        print("   ✅ Predictions saved to database")
        
        # Step 4: Trigger conversations for urgent refills
        print("\n🔔 Triggering refill conversations...")
        conversations_triggered = []
        
        for pred in predictions:
            if pred["should_notify"]:
                session_id = self.trigger_refill_conversation(user_id, pred)
                if session_id:
                    conversations_triggered.append({
                        "session_id": session_id,
                        "medicine_name": pred["medicine_name"],
                        "urgency": pred["urgency"]
                    })
                    print(f"   ✅ Triggered: {pred['medicine_name']} (Session: {session_id})")
        
        if not conversations_triggered:
            print("   ℹ️  No urgent refills requiring notification")
        
        # Step 5: Generate admin alert
        print("\n📢 Generating admin alert...")
        admin_alert = self.generate_admin_alert(user_id, predictions)
        print(f"   ✅ Alert generated: {admin_alert['urgent_count']} urgent, {admin_alert['soon_count']} soon")
        
        print(f"\n{'='*60}\n")
        
        return {
            "user_id": user_id,
            "predictions": predictions,
            "admin_alert": admin_alert,
            "conversations_triggered": conversations_triggered,
            "status": "success",
            "analysis_timestamp": datetime.now().isoformat()
        }


# ------------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------------

def get_users_needing_refills() -> List[str]:
    """
    Get list of users who may need refills.
    
    Returns users who have made purchases in the last 90 days.
    """
    with get_db_context() as db:
        cutoff_date = datetime.now() - timedelta(days=90)
        
        users = db.query(Order.user_id).filter(
            Order.created_at >= cutoff_date
        ).distinct().all()
        
        return [user[0] for user in users]


async def run_batch_analysis() -> Dict[str, Any]:
    """
    Run proactive analysis for all eligible users.
    
    This can be run as a scheduled job (e.g., daily cron).
    """
    agent = ProactiveIntelligenceAgent()
    users = get_users_needing_refills()
    
    results = {
        "total_users": len(users),
        "users_analyzed": 0,
        "total_predictions": 0,
        "urgent_refills": 0,
        "conversations_triggered": 0,
        "timestamp": datetime.now().isoformat()
    }
    
    for user_id in users:
        try:
            analysis = await agent.run_proactive_analysis(user_id)
            
            results["users_analyzed"] += 1
            results["total_predictions"] += len(analysis["predictions"])
            results["urgent_refills"] += analysis["admin_alert"]["urgent_count"]
            results["conversations_triggered"] += len(analysis["conversations_triggered"])
            
        except Exception as e:
            print(f"Error analyzing user {user_id}: {e}")
    
    return results
