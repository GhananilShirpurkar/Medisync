"""
DATABASE MODELS
===============
SQLAlchemy models for SQLite (dev) and PostgreSQL/Supabase (prod).

Migration path: SQLite → Supabase PostgreSQL
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Medicine(Base):
    """Medicine/Product catalog."""
    __tablename__ = "medicines"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    category = Column(String(100))
    manufacturer = Column(String(255))
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    requires_prescription = Column(Boolean, default=False)
    description = Column(Text)
    
    # NEW: Additional fields for conversational system
    indications = Column(Text)  # What symptoms/conditions this treats
    generic_equivalent = Column(String(255))  # Generic alternative name
    contraindications = Column(Text)  # When NOT to use this medicine
    side_effects = Column(Text)  # Patient counseling info
    
    # NEW: Detailed product info
    dosage_form = Column(String(50))  # Tablet, Syrup, Injection, etc.
    strength = Column(String(50))  # 500mg, 10ml, etc.
    active_ingredients = Column(Text)  # Comma-separated list of active ingredients
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order_items = relationship("OrderItem", back_populates="medicine")
    symptom_mappings = relationship("SymptomMedicineMapping", back_populates="medicine")


class Order(Base):
    """Customer orders."""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(50), unique=True, index=True, nullable=False)
    user_id = Column(String(100), index=True)
    
    # Order status
    status = Column(String(50), default="pending")  # pending, fulfilled, cancelled
    
    # Pharmacist decision
    pharmacist_decision = Column(String(50))  # approved, rejected, needs_review
    safety_issues = Column(JSON)  # List of safety concerns
    
    # Prescription info
    prescription_verified = Column(Boolean, default=False)
    prescription_image_url = Column(String(500))
    
    # Totals
    total_amount = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    """Individual items in an order."""
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=False)
    
    # Item details
    medicine_name = Column(String(255), nullable=False)  # Denormalized for history
    dosage = Column(String(100))
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="items")
    medicine = relationship("Medicine", back_populates="order_items")


class AuditLog(Base):
    """Audit trail for all agent decisions."""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    
    # Agent info
    agent_name = Column(String(100), nullable=False)  # front_desk, pharmacist, etc.
    decision = Column(String(100))
    reasoning = Column(Text)
    confidence_score = Column(Float)
    
    # Additional context
    extra_data = Column(JSON)  # Additional context (renamed from metadata)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    order = relationship("Order", back_populates="audit_logs")


class Patient(Base):
    """Patient/Customer information."""
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), unique=True, index=True, nullable=False)  # This is the PID (e.g., PT000123)
    
    # Contact info
    name = Column(String(255))
    phone = Column(String(20), unique=True, index=True)  # Phone is now unique identity key
    email = Column(String(255))
    telegram_id = Column(String(50), nullable=True, index=True)  # For notifications
    
    # Order history metadata
    total_orders = Column(Integer, default=0)
    last_order_date = Column(DateTime)
    last_visit = Column(DateTime, default=datetime.utcnow)  # Track engagement
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# For future: Proactive intelligence
class RefillPrediction(Base):
    """Predicted refill dates for proactive reminders."""
    __tablename__ = "refill_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), index=True, nullable=False)
    medicine_name = Column(String(255), nullable=False)
    
    # Prediction
    predicted_depletion_date = Column(DateTime)
    confidence = Column(Float)
    reminder_sent = Column(Boolean, default=False)
    refill_confirmed = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# NEW: Symptom to Medicine Mapping
class SymptomMedicineMapping(Base):
    """Maps symptoms to recommended medicines."""
    __tablename__ = "symptom_medicine_mapping"
    
    id = Column(Integer, primary_key=True, index=True)
    symptom = Column(String(255), index=True, nullable=False)  # e.g., "headache", "fever"
    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=False)
    
    # Relevance scoring
    relevance_score = Column(Float, default=1.0)  # How relevant this medicine is for this symptom
    
    # Additional context
    notes = Column(Text)  # Additional guidance (e.g., "for mild cases only")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    medicine = relationship("Medicine", back_populates="symptom_mappings")


# NEW: Conversation Sessions
class ConversationSession(Base):
    """Tracks conversation sessions with users."""
    __tablename__ = "conversation_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(String(100), index=True)
    whatsapp_phone = Column(String(20))
    
    # Session state
    status = Column(String(50), default="active")  # active, completed, abandoned
    intent = Column(String(100))  # symptom, known_medicine, refill, prescription_upload
    
    # -------------------------------------------------------
    # Conversation Phase (Pre-Order State Machine)
    # -------------------------------------------------------
    conversation_phase = Column(String, default="intake", nullable=True)
    last_medicine_discussed = Column(String, nullable=True)
    last_recommendations = Column(JSON, nullable=True)
    
    # Patient context
    patient_age = Column(Integer)
    patient_allergies = Column(JSON)  # List of allergies
    patient_conditions = Column(JSON)  # List of existing conditions
    
    # Session metadata
    turn_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages = relationship("ConversationMessage", back_populates="session", cascade="all, delete-orphan")


# NEW: Conversation Messages
class ConversationMessage(Base):
    """Individual messages in a conversation."""
    __tablename__ = "conversation_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("conversation_sessions.id"), nullable=False)
    
    # Message details
    role = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    
    # Agent info (for assistant messages)
    agent_name = Column(String(100))  # Which agent generated this message
    
    # Additional context
    extra_data = Column(JSON)  # Structured data (e.g., medicine recommendations)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("ConversationSession", back_populates="messages")