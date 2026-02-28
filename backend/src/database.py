"""
DATABASE OPERATIONS
===================
SQLAlchemy-based database operations.
Works with both SQLite (dev) and PostgreSQL/Supabase (prod).

Includes transaction support for atomic operations.
"""

from typing import List, Optional, Dict
from contextlib import contextmanager
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from collections import defaultdict

from datetime import datetime
from src.models import Medicine, Order, OrderItem as DBOrderItem, AuditLog, SymptomMedicineMapping, Patient
from src.state import OrderItem
from src.db_config import get_db_context
from src.errors import DatabaseError, TransactionError
from src.services.semantic_search_service import semantic_search_service


class Database:
    """
    Database operations wrapper.
    
    Note: This class maintains backward compatibility with the original
    CSV-based interface while using SQLAlchemy underneath.
    
    Supports transactions for atomic operations.
    """
    
    def __init__(self):
        """Initialize database connection."""
        pass
    
    @contextmanager
    def transaction(self):
        """
        Transaction context manager for atomic operations.
        
        Usage:
            with db.transaction() as tx:
                tx.create_order(...)
                tx.decrement_stock(...)
                # Automatically commits on success, rolls back on exception
        
        Yields:
            TransactionContext with database operations
        """
        with get_db_context() as session:
            tx = TransactionContext(session)
            try:
                yield tx
                session.commit()
            except Exception as e:
                session.rollback()
                raise TransactionError(
                    operation="transaction",
                    reason=str(e)
                ) from e
    
    def get_medicine(self, name: str) -> Optional[Dict]:
        """
        Get medicine by name with fuzzy matching.
        
        Args:
            name: Medicine name (case-insensitive, handles typos)
            
        Returns:
            Medicine dict or None if not found
        """
        print(f"DATABASE: Getting medicine: {name}")
        with get_db_context() as db:
            print(f"DEBUG: get_medicine searching for: '{name}'")
            # Try exact match first
            medicine = db.query(Medicine).filter(
                Medicine.name.ilike(name)
            ).first()
            
            if medicine:
                return {
                    "medicine_id": medicine.id,
                    "name": medicine.name,
                    "category": medicine.category,
                    "price": medicine.price,
                    "stock": medicine.stock,
                    "requires_prescription": medicine.requires_prescription,
                    "description": medicine.description,
                    "indications": medicine.indications,
                    "generic_equivalent": medicine.generic_equivalent,
                    "dosage_form": medicine.dosage_form,
                    "strength": medicine.strength,
                    "active_ingredients": medicine.active_ingredients,
                    "side_effects": medicine.side_effects,
                }
            
            # Try fuzzy match (partial match)
            print(f"DATABASE: Exact match not found, trying fuzzy match...")
            medicine = db.query(Medicine).filter(
                Medicine.name.ilike(f"%{name}%")
            ).first()
            
            if medicine:
                print(f"DATABASE: Found fuzzy match: {medicine.name} (searched for: {name})")
                return {
                    "id": medicine.id,
                    "name": medicine.name,
                    "category": medicine.category,
                    "manufacturer": medicine.manufacturer,
                    "price": medicine.price,
                    "stock": medicine.stock,
                    "requires_prescription": medicine.requires_prescription,
                    "description": medicine.description,
                    "indications": medicine.indications,
                    "generic_equivalent": medicine.generic_equivalent,
                    "dosage_form": medicine.dosage_form,
                    "strength": medicine.strength,
                    "active_ingredients": medicine.active_ingredients,
                    "side_effects": medicine.side_effects,
                    "fuzzy_match": True,
                    "searched_name": name,
                }
            
            # Try Levenshtein distance for typos
            print(f"DATABASE: Fuzzy match not found, trying similarity match...")
            all_medicines = db.query(Medicine).all()
            
            best_match = None
            best_similarity = 0.0
            
            for med in all_medicines:
                similarity = calculate_similarity(name.lower(), med.name.lower())
                if similarity > best_similarity and similarity >= 0.7:  # 70% similarity threshold
                    best_similarity = similarity
                    best_match = med
            
            if best_match:
                print(f"DATABASE: Found similar match: {best_match.name} (similarity: {best_similarity:.2f})")
                return {
                    "id": best_match.id,
                    "name": best_match.name,
                    "category": best_match.category,
                    "manufacturer": best_match.manufacturer,
                    "price": best_match.price,
                    "stock": best_match.stock,
                    "requires_prescription": best_match.requires_prescription,
                    "description": best_match.description,
                    "indications": best_match.indications,
                    "generic_equivalent": best_match.generic_equivalent,
                    "dosage_form": best_match.dosage_form,
                    "strength": best_match.strength,
                    "active_ingredients": best_match.active_ingredients,
                    "side_effects": best_match.side_effects,
                    "fuzzy_match": True,
                    "searched_name": name,
                    "similarity": best_similarity,
                }
            
            print(f"DATABASE: Medicine '{name}' not found (no exact or similarity matches)")
            return None

    def resolve_patient(self, phone: str, name: Optional[str] = None) -> Dict:
        """
        Get or create patient by phone number.
        
        Args:
            phone: Patient phone number
            name: Optional patient name
            
        Returns:
            Dict with patient info: {pid, phone, name, is_new}
        """
        with get_db_context() as db:
            patient = db.query(Patient).filter(Patient.phone == phone).first()
            is_new = False
            
            if not patient:
                is_new = True
                # Generate a new PID
                patient_count = db.query(Patient).count()
                pid = f"PID-{patient_count + 1 + 1000:06d}" # PT-1001 base
                
                patient = Patient(
                    user_id=pid,
                    phone=phone,
                    name=name or f"Patient {pid[-4:]}",
                    created_at=datetime.utcnow()
                )
                db.add(patient)
                db.commit()
                db.refresh(patient)
            
            return {
                "pid": patient.user_id,
                "phone": patient.phone,
                "name": patient.name,
                "is_new": is_new
            }

    def update_patient_whatsapp(self, pid: str, phone: str) -> bool:
        """Update patient's phone number for WhatsApp."""
        with get_db_context() as db:
            patient = db.query(Patient).filter(Patient.user_id == pid).first()
            if not patient:
                return False
            patient.phone = phone
            db.commit()
            return True
    
    def decrement_stock(self, name: str, qty: int) -> bool:
        """
        Decrement medicine stock.
        
        Args:
            name: Medicine name
            qty: Quantity to decrement
            
        Returns:
            True if successful, False otherwise
        """
        with get_db_context() as db:
            medicine = db.query(Medicine).filter(
                Medicine.name.ilike(name)
            ).first()
            
            if not medicine:
                return False
            
            if medicine.stock < qty:
                return False
            
            medicine.stock -= qty
            db.commit()
            return True
    
    def create_order(
        self,
        user_id: str,
        items: List[OrderItem],
        pharmacist_decision: Optional[str] = None,
        safety_issues: Optional[List[str]] = None,
    ) -> str:
        """
        Create a new order.
        
        Args:
            user_id: User/patient ID
            items: List of OrderItem objects
            pharmacist_decision: Decision from pharmacist agent
            safety_issues: List of safety concerns
            
        Returns:
            Order ID string
        """
        with get_db_context() as db:
            # Generate order ID
            order_count = db.query(Order).count()
            order_id_str = f"ORD-{order_count + 1:05d}"
            
            # Calculate total
            total_amount = 0.0
            for item in items:
                medicine = db.query(Medicine).filter(
                    Medicine.name.ilike(item.medicine_name)
                ).first()
                if medicine:
                    total_amount += medicine.price * item.quantity
            
            # Create order
            order = Order(
                order_id=order_id_str,
                user_id=user_id,
                status="pending",
                pharmacist_decision=pharmacist_decision,
                safety_issues=safety_issues or [],
                total_amount=total_amount,
            )
            db.add(order)
            db.flush()  # Get order.id
            
            # Create order items
            for item in items:
                medicine = db.query(Medicine).filter(
                    Medicine.name.ilike(item.medicine_name)
                ).first()
                
                if medicine:
                    db_item = DBOrderItem(
                        order_id=order.id,
                        medicine_id=medicine.id,
                        medicine_name=medicine.name,
                        dosage=item.dosage,
                        quantity=item.quantity,
                        price=medicine.price,
                    )
                    db.add(db_item)
            
            db.commit()
            return order_id_str
    
    def get_order(self, order_id: str) -> Optional[Dict]:
        """
        Get order by ID.
        
        Args:
            order_id: Order ID string
            
        Returns:
            Order dict or None
        """
        with get_db_context() as db:
            order = db.query(Order).filter(
                Order.order_id == order_id
            ).first()
            
            if not order:
                return None
            
            return {
                "order_id": order.order_id,
                "user_id": order.user_id,
                "status": order.status,
                "pharmacist_decision": order.pharmacist_decision,
                "safety_issues": order.safety_issues,
                "total_amount": order.total_amount,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "items": [
                    {
                        "medicine_name": item.medicine_name,
                        "dosage": item.dosage,
                        "quantity": item.quantity,
                        "price": item.price,
                    }
                    for item in order.items
                ],
            }
    
    def add_audit_log(
        self,
        order_id: str,
        agent_name: str,
        decision: str,
        reasoning: str,
        confidence_score: Optional[float] = None,
        extra_data: Optional[Dict] = None,
    ) -> bool:
        """
        Add audit log entry.
        
        Args:
            order_id: Order ID
            agent_name: Name of agent (front_desk, pharmacist, etc.)
            decision: Decision made
            reasoning: Reasoning for decision
            confidence_score: Confidence score (0-1)
            extra_data: Additional context data
            
        Returns:
            True if successful
        """
        with get_db_context() as db:
            order = db.query(Order).filter(
                Order.order_id == order_id
            ).first()
            
            if not order:
                return False
            
            log = AuditLog(
                order_id=order.id,
                agent_name=agent_name,
                decision=decision,
                reasoning=reasoning,
                confidence_score=confidence_score,
                extra_data=extra_data or {},
            )
            db.add(log)
            db.commit()
            return True



# ------------------------------------------------------------------
# TRANSACTION CONTEXT
# ------------------------------------------------------------------

class TransactionContext:
    """
    Transaction context for atomic database operations.
    
    Provides the same interface as Database but operates within
    a single transaction with pessimistic locking.
    """
    
    def __init__(self, session: Session):
        """
        Initialize transaction context.
        
        Args:
            session: SQLAlchemy session
        """
        self.session = session
    
    def get_medicine(self, name: str) -> Optional[Dict]:
        """
        Get medicine by name within transaction.
        
        Args:
            name: Medicine name (case-insensitive)
            
        Returns:
            Medicine dict or None if not found
        """
        medicine = self.session.query(Medicine).filter(
            Medicine.name.ilike(name)
        ).first()
        
        if not medicine:
            return None
        
        return {
            "id": medicine.id,
            "name": medicine.name,
            "category": medicine.category,
            "manufacturer": medicine.manufacturer,
            "price": medicine.price,
            "stock": medicine.stock,
            "requires_prescription": medicine.requires_prescription,
            "description": medicine.description,
            "indications": medicine.indications,
            "generic_equivalent": medicine.generic_equivalent,
            "dosage_form": medicine.dosage_form,
            "strength": medicine.strength,
            "active_ingredients": medicine.active_ingredients,
            "side_effects": medicine.side_effects,
        }
    
    def decrement_stock(self, name: str, qty: int) -> bool:
        """
        Decrement medicine stock within transaction with pessimistic locking.
        
        Uses SELECT FOR UPDATE to prevent race conditions.
        
        Args:
            name: Medicine name
            qty: Quantity to decrement
            
        Returns:
            True if successful, False otherwise
        """
        medicine = self.session.query(Medicine).filter(
            Medicine.name.ilike(name)
        ).with_for_update().first()  # Pessimistic lock - prevents race conditions
        
        if not medicine:
            return False
        
        if medicine.stock < qty:
            return False
        
        medicine.stock -= qty
        return True
    
    def create_order(
        self,
        user_id: str,
        items: List[OrderItem],
        pharmacist_decision: Optional[str] = None,
        safety_issues: Optional[List[str]] = None,
    ) -> str:
        """
        Create a new order within transaction.
        
        Args:
            user_id: User/patient ID
            items: List of OrderItem objects
            pharmacist_decision: Decision from pharmacist agent
            safety_issues: List of safety concerns
            
        Returns:
            Order ID string
        """
        # Generate unique order ID using UUID to avoid race conditions
        # This is more robust than sequential IDs in concurrent environments
        import uuid
        import time
        
        # Use timestamp + short UUID for human-readable but unique IDs
        timestamp = int(time.time() * 1000) % 100000  # Last 5 digits of milliseconds
        short_uuid = str(uuid.uuid4())[:8].upper()
        order_id_str = f"ORD-{timestamp}-{short_uuid}"
        
        # Calculate total
        total_amount = 0.0
        for item in items:
            medicine = self.session.query(Medicine).filter(
                Medicine.name.ilike(item.medicine_name)
            ).first()
            if medicine:
                total_amount += medicine.price * item.quantity
        
        # Create order
        order = Order(
            order_id=order_id_str,
            user_id=user_id,
            status="pending",
            pharmacist_decision=pharmacist_decision,
            safety_issues=safety_issues or [],
            total_amount=total_amount,
        )
        self.session.add(order)
        self.session.flush()  # Get order.id
        
        # Create order items
        for item in items:
            medicine = self.session.query(Medicine).filter(
                Medicine.name.ilike(item.medicine_name)
            ).first()
            
            if medicine:
                db_item = DBOrderItem(
                    order_id=order.id,
                    medicine_id=medicine.id,
                    medicine_name=medicine.name,
                    dosage=item.dosage,
                    quantity=item.quantity,
                    price=medicine.price,
                )
                self.session.add(db_item)
        
        return order_id_str
    
    def add_audit_log(
        self,
        order_id: str,
        agent_name: str,
        decision: str,
        reasoning: str,
        confidence_score: Optional[float] = None,
        extra_data: Optional[Dict] = None,
    ) -> bool:
        """
        Add audit log entry within transaction.
        
        Args:
            order_id: Order ID
            agent_name: Name of agent
            decision: Decision made
            reasoning: Reasoning for decision
            confidence_score: Confidence score (0-1)
            extra_data: Additional context data
            
        Returns:
            True if successful
        """
        order = self.session.query(Order).filter(
            Order.order_id == order_id
        ).first()
        
        if not order:
            return False
        
        log = AuditLog(
            order_id=order.id,
            agent_name=agent_name,
            decision=decision,
            reasoning=reasoning,
            confidence_score=confidence_score,
            extra_data=extra_data or {},
        )
        self.session.add(log)
        return True



def calculate_similarity(str1: str, str2: str) -> float:
    """
    Calculate similarity between two strings using Levenshtein distance.
    
    Args:
        str1: First string
        str2: Second string
        
    Returns:
        Similarity score between 0.0 and 1.0
    """
    # Simple Levenshtein distance implementation
    if str1 == str2:
        return 1.0
    
    len1, len2 = len(str1), len(str2)
    if len1 == 0 or len2 == 0:
        return 0.0
    
    # Create distance matrix
    matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]
    
    # Initialize first row and column
    for i in range(len1 + 1):
        matrix[i][0] = i
    for j in range(len2 + 1):
        matrix[0][j] = j
    
    # Calculate distances
    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if str1[i-1] == str2[j-1] else 1
            matrix[i][j] = min(
                matrix[i-1][j] + 1,      # deletion
                matrix[i][j-1] + 1,      # insertion
                matrix[i-1][j-1] + cost  # substitution
            )
    
    # Calculate similarity (1 - normalized distance)
    max_len = max(len1, len2)
    distance = matrix[len1][len2]
    similarity = 1.0 - (distance / max_len)
    
    return similarity


    def add_medicine(self, data: Dict) -> int:
        """Add a new medicine to the database."""
        with get_db_context() as db:
            medicine = Medicine(
                name=data['name'],
                category=data.get('category'),
                manufacturer=data.get('manufacturer'),
                price=data['price'],
                stock=data.get('stock', 0),
                requires_prescription=data.get('requires_prescription', False),
                description=data.get('description'),
                indications=data.get('indications'),
                generic_equivalent=data.get('generic_equivalent'),
                dosage_form=data.get('dosage_form'),
                strength=data.get('strength'),
                active_ingredients=data.get('active_ingredients')
            )
            db.add(medicine)
            db.commit()
            db.refresh(medicine)
            return medicine.id

    def update_medicine(self, med_id: int, data: Dict) -> bool:
        """Update an existing medicine."""
        with get_db_context() as db:
            medicine = db.query(Medicine).filter(Medicine.id == med_id).first()
            if not medicine:
                return False
            
            for key, value in data.items():
                if hasattr(medicine, key):
                    setattr(medicine, key, value)
            
            db.commit()
            return True

    def delete_medicine(self, med_id: int) -> bool:
        """Delete a medicine from the database."""
        with get_db_context() as db:
            medicine = db.query(Medicine).filter(Medicine.id == med_id).first()
            if not medicine:
                return False
            db.delete(medicine)
            db.commit()
            return True
