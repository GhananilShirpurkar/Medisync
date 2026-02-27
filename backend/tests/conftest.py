"""
TEST FIXTURES
=============
Shared fixtures for all tests.
"""

import pytest
import sys
from pathlib import Path
import importlib

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Explicitly import all models at the top level
from src.models import (
    Base,
    Medicine,
    Order,
    OrderItem as DBOrderItem,
    AuditLog,
    Patient,
    RefillPrediction,
    SymptomMedicineMapping,
    ConversationSession,
    ConversationMessage
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src import db_config
from contextlib import contextmanager

@pytest.fixture(scope="function")
def setup_test_db(monkeypatch, tmp_path):
    """
    Setup test database for each test function.
    - Creates a new temporary database file for each test
    - Drops and recreates all tables
    - Seeds initial data
    - Monkeypatches the db_config to use the test database
    """
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

    # Force reload of src.models and src.db_config to ensure they pick up the monkeypatch
    # and that Base.metadata is correctly linked.
    if "src.models" in sys.modules:
        importlib.reload(sys.modules["src.models"])
    if "src.db_config" in sys.modules:
        importlib.reload(sys.modules["src.db_config"])

    # Ensure tables are created for the newly reloaded Base.metadata
    print("[DEBUG] Calling Base.metadata.create_all(engine)...")
    Base.metadata.create_all(engine)
    print("[DEBUG] Finished Base.metadata.create_all(engine).")
    
    # Define SessionTesting AFTER tables are created
    SessionTesting = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Monkeypatch the database configuration to use the test engine
    @contextmanager
    def test_get_db_context():
        session = SessionTesting()
        try:
            yield session
        finally:
            session.close()

    monkeypatch.setattr(db_config, "get_db_context", test_get_db_context)

    # Force reload of src.database AFTER db_config.get_db_context has been monkeypatched
    # This ensures that the Database class uses the mocked get_db_context correctly for seeding.
    if "src.database" in sys.modules:
        importlib.reload(sys.modules["src.database"])
    # No need to import Database here, as we are directly using SessionTesting for seeding

    # Seed data
    seeding_session = SessionTesting() # Directly create a session for seeding
    try:
        medicines = [
            Medicine(name="Paracetamol", stock=100, price=10.0, requires_prescription=False),
            Medicine(name="Ibuprofen", stock=50, price=15.0, requires_prescription=False),
            Medicine(name="Aspirin", stock=0, price=5.0, requires_prescription=False), # Out of stock
            Medicine(name="Amoxicillin", stock=20, price=25.0, requires_prescription=True),
            Medicine(name="Vitamin C", stock=200, price=12.0, requires_prescription=False),
        ]
        print("[DEBUG] Adding medicines to seeding session...")
        seeding_session.add_all(medicines)
        print("[DEBUG] Committing seeding session...")
        seeding_session.commit()
        print("[DEBUG] Seeding session committed successfully.")
    except Exception as e:
        seeding_session.rollback()
        print(f"[DEBUG] Seeding session rolled back due to error: {e}")
        raise
    finally:
        seeding_session.close()
    

    yield engine, SessionTesting  # Yield the engine and SessionTesting factory

    # Teardown: drop all tables
    print("[DEBUG] Tearing down: dropping all tables...")
    Base.metadata.drop_all(engine)
    print("[DEBUG] Tables dropped.")

@pytest.fixture(scope="function")
def test_db(setup_test_db):
    """
    Provide a Database instance for tests, ensuring it uses the monkeypatched context.
    
    Returns:
        Database instance configured for testing
    """
    # src.database has already been reloaded in setup_test_db
    from src.database import Database
    return Database()


@pytest.fixture(scope="function")
def sample_state():
    """
    Create a sample pharmacy state for testing.
    
    Returns:
        PharmacyState with basic test data
    """
    from src.state import PharmacyState, OrderItem
    
    return PharmacyState(
        user_id="test_user_001",
        pharmacist_decision="approved",
        prescription_verified=True,
        extracted_items=[
            OrderItem(medicine_name="Paracetamol", dosage="500mg", quantity=2, in_stock=True),
            OrderItem(medicine_name="Vitamin C", dosage="1000mg", quantity=1, in_stock=True)
        ],
        trace_metadata={
            "inventory_agent": {
                "availability_score": 1.0,
                "available_items": 2,
                "total_items": 2
            }
        }
    )