import sys
import os

# Ensure we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.telegram_service import get_bot_info, send_message

def test_telegram_bot():
    print("🤖 Testing Telegram Bot Configuration...\n")
    
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ ERROR: TELEGRAM_BOT_TOKEN environment variable is not set.")
        return
        
    print(f"Token found: {token[:10]}...{token[-5:]}")
    print("Calling getMe API...\n")
    
    result = get_bot_info()
    
    if result.get("success"):
        print("✅ SUCCESS! Bot configuration is valid.")
        print(f"Bot Username: @{result.get('bot_username')}")
        print(f"Bot Name: {result.get('bot_name')}")
        print(f"Bot ID: {result.get('bot_id')}")
        print(f"Can read messages: {result.get('can_read_messages')}")
        print("\nSending test message to provided chat_id...")
        
        test_msg = send_message(chat_id="1775065634", text="✅ *MediSync Test Notification*\n\nThis is a test confirming that the backend can successfully reach your device. Have a nice day!")
        if test_msg.get("success"):
            print("✉️  Message delivered successfully!")
        else:
            print(f"❌ Failed to deliver message: {test_msg.get('error')}")
            
    else:
        print("❌ FAILED! Bot configuration is invalid or API is unreachable.")
        print(f"Error details: {result.get('error')}")

if __name__ == "__main__":
    test_telegram_bot()
