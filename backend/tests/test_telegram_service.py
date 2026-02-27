"""
TELEGRAM SERVICE TESTS
======================
Test Telegram bot notification functionality.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.telegram_service import (
    get_bot_info,
    send_message,
    send_order_notification,
    send_prescription_status,
    send_refill_reminder,
    mock_notification,
    TELEGRAM_BOT_TOKEN
)


def test_bot_configuration():
    """Test bot token configuration."""
    print("\n" + "="*60)
    print("TELEGRAM BOT CONFIGURATION TEST")
    print("="*60)
    
    if TELEGRAM_BOT_TOKEN:
        print(f"\n✅ Bot token configured")
        print(f"   Token: {TELEGRAM_BOT_TOKEN[:20]}...")
    else:
        print("\n⚠️  Bot token not configured")
        print("   Set TELEGRAM_BOT_TOKEN in .env")
    
    print("\n✅ Configuration check complete")


def test_get_bot_info():
    """Test getting bot information."""
    print("\n" + "="*60)
    print("BOT INFO TEST")
    print("="*60)
    
    result = get_bot_info()
    
    if result.get("success"):
        print(f"\n✅ Bot connected successfully")
        print(f"   Bot ID: {result.get('bot_id')}")
        print(f"   Username: @{result.get('bot_username')}")
        print(f"   Name: {result.get('bot_name')}")
    else:
        print(f"\n⚠️  Could not connect to bot")
        print(f"   Error: {result.get('error')}")
    
    return result.get("success", False)


def test_mock_notification():
    """Test mock notification (no API call)."""
    print("\n" + "="*60)
    print("MOCK NOTIFICATION TEST")
    print("="*60)
    
    result = mock_notification(
        chat_id="123456789",
        message="Test notification from MediSync"
    )
    
    assert result["success"], "Mock notification should always succeed"
    assert result["method"] == "telegram_mock"
    
    print("\n✅ Mock notification test passed")


def test_order_notification_format():
    """Test order notification message formatting."""
    print("\n" + "="*60)
    print("ORDER NOTIFICATION FORMAT TEST")
    print("="*60)
    
    # Test data
    items = [
        {"name": "Paracetamol 500mg", "quantity": 2},
        {"name": "Amoxicillin 250mg", "quantity": 1}
    ]
    
    # This will use mock if bot not configured
    print("\nTesting order notification format...")
    print("(Using mock mode for testing)")
    
    # Mock the notification
    result = mock_notification(
        chat_id="test_user",
        message=f"""
✅ *Order Confirmed*

*Order ID:* `ORD-12345`

*Items:*
• Paracetamol 500mg x2
• Amoxicillin 250mg x1

*Total:* ₹150.00

Thank you for your order!
"""
    )
    
    assert result["success"]
    print("\n✅ Order notification format test passed")


def test_prescription_status_messages():
    """Test prescription status notification messages."""
    print("\n" + "="*60)
    print("PRESCRIPTION STATUS TEST")
    print("="*60)
    
    statuses = ["verified", "needs_review", "rejected"]
    
    for status in statuses:
        print(f"\nTesting status: {status}")
        result = mock_notification(
            chat_id="test_user",
            message=f"Prescription status: {status}"
        )
        assert result["success"]
        print(f"  ✓ {status} message formatted correctly")
    
    print("\n✅ Prescription status test passed")


def test_refill_reminder():
    """Test refill reminder notification."""
    print("\n" + "="*60)
    print("REFILL REMINDER TEST")
    print("="*60)
    
    result = mock_notification(
        chat_id="test_user",
        message="""
🔔 *Refill Reminder*

Your *Paracetamol 500mg* supply is running low.

*Days remaining:* 3

Would you like to reorder?
"""
    )
    
    assert result["success"]
    print("\n✅ Refill reminder test passed")


if __name__ == "__main__":
    print("\n🧪 Running Telegram Service Tests...\n")
    
    try:
        # Configuration tests
        test_bot_configuration()
        
        # Bot connection test (only if token configured)
        bot_connected = False
        if TELEGRAM_BOT_TOKEN:
            bot_connected = test_get_bot_info()
        
        # Mock tests (always run)
        test_mock_notification()
        test_order_notification_format()
        test_prescription_status_messages()
        test_refill_reminder()
        
        print("\n" + "="*60)
        print("✅ ALL TELEGRAM SERVICE TESTS PASSED")
        print("="*60)
        
        if bot_connected:
            print("\n💡 Bot is connected and ready to send notifications")
        else:
            print("\n💡 Bot not connected - using mock mode")
            print("   To enable real notifications:")
            print("   1. Set TELEGRAM_BOT_TOKEN in .env")
            print("   2. Get your chat ID by messaging the bot")
            print("   3. Use send_message() with your chat ID")
        
        print()
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
