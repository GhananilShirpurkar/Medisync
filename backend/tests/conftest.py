"""
TEST FIXTURES
=============
Shared fixtures for all tests.
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

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

    from src.models import Base, Medicine
    
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

    # Seed data
    seeding_session = SessionTesting() # Directly create a session for seeding
    try:
        medicines = [
            Medicine(name="Paracetamol", stock=100, price=10.0, requires_prescription=False, atc_code="N02BE01"),
            Medicine(name="Ibuprofen", stock=50, price=15.0, requires_prescription=False, atc_code="M01AE01"),
            Medicine(name="Aspirin", stock=0, price=5.0, requires_prescription=False, atc_code="N02BA01"), # Out of stock
            Medicine(name="Amoxicillin", stock=20, price=25.0, requires_prescription=True, atc_code="J01CA04"),
            Medicine(name="Vitamin C", stock=200, price=12.0, requires_prescription=False, atc_code="A11G"),
        ]
        
        # Add contraindication rules for clinical reasoning tests
        from src.models import ContraindicationRule
        import uuid
        rules = [
            ContraindicationRule(
                id=str(uuid.uuid4()),
                condition_name="peptic_ulcer",
                forbidden_atc_pattern="M01A",
                severity="absolute",
                evidence_reference="NSAIDs risk GI bleed"
            ),
            ContraindicationRule(
                id=str(uuid.uuid4()),
                condition_name="asthma",
                forbidden_atc_pattern="M01A",
                severity="relative",
                evidence_reference="Aspirin-induced asthma risk"
            )
        ]
        
        print("[DEBUG] Adding data to seeding session...")
        seeding_session.add_all(medicines)
        seeding_session.add_all(rules)
        print("[DEBUG] Committing seeding session...")
        seeding_session.commit()
        print("[DEBUG] Seeding session committed successfully.")
    except Exception as e:
        seeding_session.rollback()
        print(f"[DEBUG] Seeding session rolled back due to error: {e}")
        # Skip fail if table might already exist or other seeding issues
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
        confirmation_confirmed=True,
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