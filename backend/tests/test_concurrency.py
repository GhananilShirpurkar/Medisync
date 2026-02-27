"""
CONCURRENCY TESTS
=================
Test concurrent order processing to verify:
1. No race conditions in inventory management
2. No overselling (stock never goes negative)
3. Pessimistic locking works correctly
4. Transaction isolation is maintained

CRITICAL: These tests verify the system can handle simultaneous requests
without data corruption or overselling inventory.
"""

import sys
from pathlib import Path
import threading
import time
from typing import List, Dict, Any

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.state import PharmacyState, OrderItem
from src.agents.fulfillment_agent import fulfillment_agent
from src.database import Database


def test_concurrent_orders_same_medicine(test_db):
    """
    Test 10 concurrent orders for the same medicine.
    
    This is the critical test for race conditions.
    If pessimistic locking works, only orders that fit within
    available stock should succeed.
    """
    print("\n" + "="*60)
    print("TEST: CONCURRENT ORDERS - SAME MEDICINE")
    print("="*60)
    
    db = test_db
    
    # Get initial stock for Paracetamol
    medicine = db.get_medicine("Paracetamol")
    initial_stock = medicine["stock"]
    print(f"\nInitial stock: {initial_stock}")
    
    # Create 10 threads, each trying to order 15 units
    # With initial stock of 100, only 6 orders should succeed (6 * 15 = 90)
    # The remaining 4 should fail due to insufficient stock
    
    num_threads = 10
    quantity_per_order = 15
    results = []
    
    def place_order(thread_id: int):
        """Place an order in a separate thread."""
        try:
            state = PharmacyState(
                user_id=f"concurrent_user_{thread_id}",
                pharmacist_decision="approved",
                prescription_verified=True,
                extracted_items=[
                    OrderItem(
                        medicine_name="Paracetamol",
                        dosage="500mg",
                        quantity=quantity_per_order,
                        in_stock=True
                    )
                ]
            )
            
            # Add inventory metadata
            state.trace_metadata["inventory_agent"] = {
                "availability_score": 1.0,
                "available_items": 1,
                "total_items": 1
            }
            
            # Run fulfillment
            result = fulfillment_agent(state)
            
            results.append({
                "thread_id": thread_id,
                "success": result.order_id is not None,
                "order_id": result.order_id,
                "status": result.order_status
            })
            
            print(f"Thread {thread_id}: {'✓ SUCCESS' if result.order_id else '✗ FAILED'}")
            
        except Exception as e:
            results.append({
                "thread_id": thread_id,
                "success": False,
                "error": str(e)
            })
            print(f"Thread {thread_id}: ✗ ERROR - {e}")
    
    # Create and start threads
    threads = []
    print(f"\nStarting {num_threads} concurrent orders...")
    print(f"Each order requests {quantity_per_order} units")
    print(f"Expected: ~{initial_stock // quantity_per_order} orders should succeed\n")
    
    for i in range(num_threads):
        thread = threading.Thread(target=place_order, args=(i,))
        threads.append(thread)
    
    # Start all threads simultaneously
    for thread in threads:
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Analyze results
    successful_orders = [r for r in results if r.get("success")]
    failed_orders = [r for r in results if not r.get("success")]
    
    print(f"\n{'='*60}")
    print(f"RESULTS:")
    print(f"{'='*60}")
    print(f"Successful orders: {len(successful_orders)}")
    print(f"Failed orders: {len(failed_orders)}")
    
    # Check final stock
    medicine_after = db.get_medicine("Paracetamol")
    final_stock = medicine_after["stock"]
    expected_stock = initial_stock - (len(successful_orders) * quantity_per_order)
    
    print(f"\nStock verification:")
    print(f"  Initial: {initial_stock}")
    print(f"  Final: {final_stock}")
    print(f"  Expected: {expected_stock}")
    print(f"  Difference: {abs(final_stock - expected_stock)}")
    
    # CRITICAL ASSERTIONS
    assert final_stock >= 0, "❌ CRITICAL: Stock went negative! Race condition detected!"
    assert final_stock == expected_stock, f"❌ CRITICAL: Stock mismatch! Expected {expected_stock}, got {final_stock}"
    assert len(successful_orders) == initial_stock // quantity_per_order, \
        f"Expected {initial_stock // quantity_per_order} successful orders, got {len(successful_orders)}"
    
    print(f"\n✅ Concurrency test passed - No race conditions detected")
    print(f"✅ Pessimistic locking working correctly")
    print(f"✅ No overselling occurred")
    
    return results


def test_concurrent_orders_different_medicines(test_db):
    """
    Test concurrent orders for different medicines.
    
    This should have no contention and all orders should succeed.
    """
    print("\n" + "="*60)
    print("TEST: CONCURRENT ORDERS - DIFFERENT MEDICINES")
    print("="*60)
    
    db = test_db
    
    # Get initial stocks
    medicines = ["Paracetamol", "Vitamin C", "Ibuprofen", "Amoxicillin"]
    initial_stocks = {}
    for med in medicines:
        medicine = db.get_medicine(med)
        if medicine:
            initial_stocks[med] = medicine["stock"]
            print(f"{med}: {medicine['stock']} units")
    
    num_threads = len(medicines)
    results = []
    
    def place_order(thread_id: int, medicine_name: str):
        """Place an order for a specific medicine."""
        try:
            state = PharmacyState(
                user_id=f"concurrent_user_{thread_id}",
                pharmacist_decision="approved",
                prescription_verified=True,
                extracted_items=[
                    OrderItem(
                        medicine_name=medicine_name,
                        dosage="500mg",
                        quantity=5,
                        in_stock=True
                    )
                ]
            )
            
            state.trace_metadata["inventory_agent"] = {
                "availability_score": 1.0,
                "available_items": 1,
                "total_items": 1
            }
            
            result = fulfillment_agent(state)
            
            results.append({
                "thread_id": thread_id,
                "medicine": medicine_name,
                "success": result.order_id is not None,
                "order_id": result.order_id
            })
            
            print(f"Thread {thread_id} ({medicine_name}): {'✓ SUCCESS' if result.order_id else '✗ FAILED'}")
            
        except Exception as e:
            results.append({
                "thread_id": thread_id,
                "medicine": medicine_name,
                "success": False,
                "error": str(e)
            })
            print(f"Thread {thread_id} ({medicine_name}): ✗ ERROR - {e}")
    
    # Create and start threads
    threads = []
    print(f"\nStarting {num_threads} concurrent orders for different medicines...\n")
    
    for i, medicine_name in enumerate(medicines):
        thread = threading.Thread(target=place_order, args=(i, medicine_name))
        threads.append(thread)
    
    # Start all threads simultaneously
    for thread in threads:
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Analyze results
    successful_orders = [r for r in results if r.get("success")]
    
    print(f"\n{'='*60}")
    print(f"RESULTS:")
    print(f"{'='*60}")
    print(f"Successful orders: {len(successful_orders)}/{num_threads}")
    
    # Verify stock for each medicine
    print(f"\nStock verification:")
    all_correct = True
    for med in medicines:
        medicine_after = db.get_medicine(med)
        if medicine_after:
            final_stock = medicine_after["stock"]
            expected_stock = initial_stocks[med] - 5
            status = "✓" if final_stock == expected_stock else "✗"
            print(f"  {status} {med}: {initial_stocks[med]} → {final_stock} (expected {expected_stock})")
            
            if final_stock != expected_stock:
                all_correct = False
    
    assert all_correct, "❌ Stock verification failed for some medicines"
    assert len(successful_orders) == num_threads, f"Expected all {num_threads} orders to succeed"
    
    print(f"\n✅ Concurrent orders for different medicines passed")
    print(f"✅ No contention between different medicines")
    
    return results


def test_concurrent_mixed_operations(test_db):
    """
    Test mixed concurrent operations:
    - Some orders succeed
    - Some orders fail (insufficient stock)
    - Multiple medicines
    
    This simulates real-world load.
    """
    print("\n" + "="*60)
    print("TEST: CONCURRENT MIXED OPERATIONS")
    print("="*60)
    
    db = test_db
    
    # Get initial stock
    medicine = db.get_medicine("Paracetamol")
    initial_stock = medicine["stock"]
    print(f"\nInitial Paracetamol stock: {initial_stock}")
    
    # Create mixed orders:
    # - 5 orders for 10 units each (should succeed)
    # - 5 orders for 30 units each (some should fail)
    
    orders = [
        {"quantity": 10, "should_succeed": True},
        {"quantity": 10, "should_succeed": True},
        {"quantity": 10, "should_succeed": True},
        {"quantity": 10, "should_succeed": True},
        {"quantity": 10, "should_succeed": True},
        {"quantity": 30, "should_succeed": False},  # Will fail - not enough stock
        {"quantity": 30, "should_succeed": False},
        {"quantity": 30, "should_succeed": False},
        {"quantity": 30, "should_succeed": False},
        {"quantity": 30, "should_succeed": False},
    ]
    
    results = []
    
    def place_order(thread_id: int, quantity: int):
        """Place an order with specified quantity."""
        try:
            state = PharmacyState(
                user_id=f"mixed_user_{thread_id}",
                pharmacist_decision="approved",
                prescription_verified=True,
                extracted_items=[
                    OrderItem(
                        medicine_name="Paracetamol",
                        dosage="500mg",
                        quantity=quantity,
                        in_stock=True
                    )
                ]
            )
            
            state.trace_metadata["inventory_agent"] = {
                "availability_score": 1.0,
                "available_items": 1,
                "total_items": 1
            }
            
            result = fulfillment_agent(state)
            
            results.append({
                "thread_id": thread_id,
                "quantity": quantity,
                "success": result.order_id is not None,
                "order_id": result.order_id
            })
            
            status = "✓" if result.order_id else "✗"
            print(f"Thread {thread_id} (qty={quantity}): {status}")
            
        except Exception as e:
            results.append({
                "thread_id": thread_id,
                "quantity": quantity,
                "success": False,
                "error": str(e)
            })
            print(f"Thread {thread_id} (qty={quantity}): ✗ ERROR - {e}")
    
    # Create and start threads
    threads = []
    print(f"\nStarting {len(orders)} concurrent mixed orders...\n")
    
    for i, order in enumerate(orders):
        thread = threading.Thread(target=place_order, args=(i, order["quantity"]))
        threads.append(thread)
    
    # Start all threads simultaneously
    for thread in threads:
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Analyze results
    successful_orders = [r for r in results if r.get("success")]
    failed_orders = [r for r in results if not r.get("success")]
    
    print(f"\n{'='*60}")
    print(f"RESULTS:")
    print(f"{'='*60}")
    print(f"Successful orders: {len(successful_orders)}")
    print(f"Failed orders: {len(failed_orders)}")
    
    # Calculate total units ordered successfully
    total_units_ordered = sum(r["quantity"] for r in successful_orders)
    
    # Check final stock
    medicine_after = db.get_medicine("Paracetamol")
    final_stock = medicine_after["stock"]
    expected_stock = initial_stock - total_units_ordered
    
    print(f"\nStock verification:")
    print(f"  Initial: {initial_stock}")
    print(f"  Total units ordered: {total_units_ordered}")
    print(f"  Final: {final_stock}")
    print(f"  Expected: {expected_stock}")
    
    # CRITICAL ASSERTIONS
    assert final_stock >= 0, "❌ CRITICAL: Stock went negative!"
    assert final_stock == expected_stock, f"❌ Stock mismatch! Expected {expected_stock}, got {final_stock}"
    
    print(f"\n✅ Mixed concurrent operations passed")
    print(f"✅ System correctly handled mixed load")
    
    return results


def test_stress_test_high_concurrency(test_db):
    """
    Stress test with high concurrency (50 simultaneous requests).
    
    This tests system behavior under heavy load.
    """
    print("\n" + "="*60)
    print("TEST: STRESS TEST - HIGH CONCURRENCY")
    print("="*60)
    
    db = test_db
    
    # Get initial stock
    medicine = db.get_medicine("Paracetamol")
    initial_stock = medicine["stock"]
    print(f"\nInitial stock: {initial_stock}")
    
    num_threads = 50
    quantity_per_order = 2
    results = []
    start_time = time.time()
    
    def place_order(thread_id: int):
        """Place an order in a separate thread."""
        try:
            state = PharmacyState(
                user_id=f"stress_user_{thread_id}",
                pharmacist_decision="approved",
                prescription_verified=True,
                extracted_items=[
                    OrderItem(
                        medicine_name="Paracetamol",
                        dosage="500mg",
                        quantity=quantity_per_order,
                        in_stock=True
                    )
                ]
            )
            
            state.trace_metadata["inventory_agent"] = {
                "availability_score": 1.0,
                "available_items": 1,
                "total_items": 1
            }
            
            result = fulfillment_agent(state)
            
            results.append({
                "thread_id": thread_id,
                "success": result.order_id is not None
            })
            
        except Exception as e:
            results.append({
                "thread_id": thread_id,
                "success": False,
                "error": str(e)
            })
    
    # Create and start threads
    threads = []
    print(f"\nStarting {num_threads} concurrent orders...")
    print(f"Each order requests {quantity_per_order} units")
    
    for i in range(num_threads):
        thread = threading.Thread(target=place_order, args=(i,))
        threads.append(thread)
    
    # Start all threads simultaneously
    for thread in threads:
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Analyze results
    successful_orders = [r for r in results if r.get("success")]
    failed_orders = [r for r in results if not r.get("success")]
    
    print(f"\n{'='*60}")
    print(f"RESULTS:")
    print(f"{'='*60}")
    print(f"Total requests: {num_threads}")
    print(f"Successful orders: {len(successful_orders)}")
    print(f"Failed orders: {len(failed_orders)}")
    print(f"Duration: {duration:.2f}s")
    print(f"Throughput: {num_threads/duration:.2f} requests/second")
    
    # Check final stock
    medicine_after = db.get_medicine("Paracetamol")
    final_stock = medicine_after["stock"]
    expected_stock = initial_stock - (len(successful_orders) * quantity_per_order)
    
    print(f"\nStock verification:")
    print(f"  Initial: {initial_stock}")
    print(f"  Final: {final_stock}")
    print(f"  Expected: {expected_stock}")
    
    # CRITICAL ASSERTIONS
    assert final_stock >= 0, "❌ CRITICAL: Stock went negative under high load!"
    assert final_stock == expected_stock, f"❌ Stock mismatch under high load!"
    
    print(f"\n✅ Stress test passed")
    print(f"✅ System stable under high concurrency")
    
    return results


if __name__ == "__main__":
    print("\n🧪 Running Concurrency Tests...\n")
    print("⚠️  CRITICAL: These tests verify no race conditions exist")
    print("⚠️  If any test fails, DO NOT PROCEED to production\n")
    
    try:
        # Run all concurrency tests
        test_concurrent_orders_same_medicine()
        test_concurrent_orders_different_medicines()
        test_concurrent_mixed_operations()
        test_stress_test_high_concurrency()
        
        print("\n" + "="*60)
        print("✅ ALL CONCURRENCY TESTS PASSED")
        print("="*60)
        print("\n💡 System is safe for concurrent operations:")
        print("   ✓ No race conditions detected")
        print("   ✓ Pessimistic locking working correctly")
        print("   ✓ No overselling of inventory")
        print("   ✓ Transaction isolation maintained")
        print("   ✓ System stable under high load")
        print("\n🚀 System is ready for production deployment\n")
        
    except AssertionError as e:
        print(f"\n❌ CRITICAL TEST FAILED: {e}")
        print("\n⚠️  DO NOT DEPLOY TO PRODUCTION")
        print("⚠️  Fix race conditions before proceeding\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
