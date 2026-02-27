#!/usr/bin/env python3
"""
DATABASE MIGRATION SCRIPT
=========================
Migrates existing database to new schema with conversation support.

Adds:
- symptom_medicine_mapping table
- conversation_sessions table
- conversation_messages table
- Medicine table columns: indications, generic_equivalent, contraindications
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import inspect, text
from src.db_config import engine, get_db_context
from src.models import Base, Medicine, SymptomMedicineMapping, ConversationSession, ConversationMessage

def check_column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def check_table_exists(table_name: str) -> bool:
    """Check if a table exists."""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()

def migrate():
    """Run database migration."""
    print("🔄 Starting database migration...")
    
    # Step 1: Add new columns to medicines table
    print("\n📋 Step 1: Updating medicines table...")
    
    new_columns = [
        ("indications", "TEXT"),
        ("generic_equivalent", "VARCHAR(255)"),
        ("contraindications", "TEXT"),
        ("side_effects", "TEXT"),
        ("dosage_form", "VARCHAR(50)"),
        ("strength", "VARCHAR(50)"),
        ("active_ingredients", "TEXT"),
    ]
    
    with get_db_context() as db:
        for column_name, column_type in new_columns:
            if not check_column_exists("medicines", column_name):
                print(f"  ➕ Adding column: {column_name}")
                db.execute(text(f"ALTER TABLE medicines ADD COLUMN {column_name} {column_type}"))
                db.commit()
            else:
                print(f"  ✅ Column already exists: {column_name}")
    
    # Step 2: Create new tables
    print("\n📋 Step 2: Creating new tables...")
    
    new_tables = [
        ("symptom_medicine_mapping", SymptomMedicineMapping),
        ("conversation_sessions", ConversationSession),
        ("conversation_messages", ConversationMessage),
    ]
    
    for table_name, model_class in new_tables:
        if not check_table_exists(table_name):
            print(f"  ➕ Creating table: {table_name}")
            model_class.__table__.create(engine)
        else:
            print(f"  ✅ Table already exists: {table_name}")
    
    # Step 2.5: Add new columns to conversation_sessions
    print("\n📋 Step 2.5: Updating conversation_sessions table...")
    
    new_session_columns = [
        ("conversation_phase", "VARCHAR(50) DEFAULT 'intake'"),
        ("last_medicine_discussed", "VARCHAR(255)"),
        ("last_recommendations", "TEXT"),
        ("whatsapp_phone", "VARCHAR(20)"),
    ]
    
    with get_db_context() as db:
        for column_name, column_type in new_session_columns:
            if not check_column_exists("conversation_sessions", column_name):
                print(f"  ➕ Adding column: {column_name}")
                db.execute(text(
                    f"ALTER TABLE conversation_sessions ADD COLUMN {column_name} {column_type}"
                ))
                db.commit()
            else:
                print(f"  ✅ Column already exists: {column_name}")
    
    # Step 3: Verify migration
    print("\n📋 Step 3: Verifying migration...")
    
    inspector = inspect(engine)
    all_tables = inspector.get_table_names()
    
    required_tables = [
        "medicines",
        "orders",
        "order_items",
        "audit_logs",
        "patients",
        "refill_predictions",
        "symptom_medicine_mapping",
        "conversation_sessions",
        "conversation_messages",
    ]
    
    missing_tables = [t for t in required_tables if t not in all_tables]
    
    if missing_tables:
        print(f"  ❌ Missing tables: {missing_tables}")
        return False
    
    # Verify medicines columns
    medicine_columns = [col['name'] for col in inspector.get_columns("medicines")]
    required_medicine_columns = [
        "id", "name", "category", "manufacturer", "price", "stock",
        "requires_prescription", "description", "indications",
        "generic_equivalent", "contraindications", "side_effects",
        "dosage_form", "strength", "active_ingredients"
    ]
    
    missing_columns = [c for c in required_medicine_columns if c not in medicine_columns]
    
    if missing_columns:
        print(f"  ❌ Missing columns in medicines: {missing_columns}")
        return False
    
    # Verify conversation_sessions columns
    session_columns = [col['name'] for col in inspector.get_columns("conversation_sessions")]
    required_session_columns = [
        "id", "session_id", "user_id", "status", "intent", 
        "conversation_phase", "last_medicine_discussed", "last_recommendations",
        "patient_age", "patient_allergies", "patient_conditions",
        "turn_count", "created_at", "updated_at"
    ]
    
    missing_session_columns = [c for c in required_session_columns if c not in session_columns]
    
    if missing_session_columns:
        print(f"  ❌ Missing columns in conversation_sessions: {missing_session_columns}")
        return False
    
    print("  ✅ All tables and columns verified")
    
    # Step 4: Create indexes
    print("\n📋 Step 4: Creating indexes...")
    
    with get_db_context() as db:
        try:
            # Index on symptom for fast lookup
            db.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_symptom_medicine_symptom "
                "ON symptom_medicine_mapping(symptom)"
            ))
            
            # Index on session_id for fast lookup
            db.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_conversation_session_id "
                "ON conversation_sessions(session_id)"
            ))
            
            # Index on conversation_phase for state queries
            db.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_conversation_phase "
                "ON conversation_sessions(conversation_phase)"
            ))
            
            db.commit()
            print("  ✅ Indexes created")
        except Exception as e:
            print(f"  ⚠️  Index creation warning: {e}")
    
    print("\n✅ Migration completed successfully!")
    print("\n📊 Database schema:")
    print(f"  - Total tables: {len(all_tables)}")
    print(f"  - Medicine columns: {len(medicine_columns)}")
    print(f"  - Conversation sessions columns: {len(session_columns)}")
    
    return True

if __name__ == "__main__":
    try:
        success = migrate()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)