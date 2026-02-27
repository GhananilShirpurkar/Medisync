import pytest
from fastapi.testclient import TestClient
from main import app
from src.models import Order, Medicine, Patient, OrderItem
from datetime import datetime

client = TestClient(app)

def test_admin_stats(test_db, setup_test_db):
    """Test the /stats endpoint."""
    # Seed some data for stats
    _, SessionTesting = setup_test_db
    db = SessionTesting()
    
    # Add a patient who visited today
    patient = Patient(user_id="PT-TEST-01", name="Test Patient", phone="+1234567890", last_visit=datetime.utcnow())
    db.add(patient)
    
    # Add an order
    order = Order(order_id="ORD-TEST-01", user_id="PT-TEST-01", status="pending", total_amount=100.0)
    db.add(order)
    db.commit()
    
    response = client.get("/api/v1/admin/stats")
    assert response.status_code == 200
    data = response.json()
    
    assert "stats" in data
    assert "recent_activity" in data
    
    labels = [s["label"] for s in data["stats"]]
    assert "TOTAL ORDERS" in labels
    assert "PENDING ORDERS" in labels
    
    # Find TOTAL ORDERS value
    total_orders = next(s["value"] for s in data["stats"] if s["label"] == "TOTAL ORDERS")
    assert total_orders >= 1

def test_admin_inventory(test_db):
    """Test the /inventory endpoint."""
    response = client.get("/api/v1/admin/inventory")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "name" in data[0]
        assert "stock" in data[0]

def test_admin_customers(test_db, setup_test_db):
    """Test the /customers endpoint."""
    _, SessionTesting = setup_test_db
    db = SessionTesting()
    patient = Patient(user_id="PT-CUST-01", name="Customer One", phone="+9876543210")
    db.add(patient)
    db.commit()
    
    response = client.get("/api/v1/admin/customers")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(c["id"] == "PT-CUST-01" for c in data)

def test_admin_orders(test_db, setup_test_db):
    """Test the /orders endpoint."""
    _, SessionTesting = setup_test_db
    db = SessionTesting()
    order = Order(order_id="ORD-LIST-01", user_id="PT-CUST-01", status="pending")
    db.add(order)
    db.commit()
    
    response = client.get("/api/v1/admin/orders")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(o["id"] == "ORD-LIST-01" for o in data)

def test_order_action(test_db, setup_test_db):
    """Test approving/rejecting an order."""
    _, SessionTesting = setup_test_db
    db = SessionTesting()
    order = Order(order_id="ORD-ACT-01", user_id="PT-CUST-01", status="pending")
    db.add(order)
    db.commit()
    
    # Approve
    response = client.post("/api/v1/admin/orders/ORD-ACT-01/action", json={"status": "approved"})
    assert response.status_code == 200
    assert response.json()["new_status"] == "fulfilled"
    
    # Verify in DB
    db.refresh(order)
    assert order.status == "fulfilled"
    
    # Reject another
    order2 = Order(order_id="ORD-ACT-02", user_id="PT-CUST-01", status="pending")
    db.add(order2)
    db.commit()
    
    response = client.post("/api/v1/admin/orders/ORD-ACT-02/action", json={"status": "rejected"})
    assert response.status_code == 200
    assert response.json()["new_status"] == "cancelled"
