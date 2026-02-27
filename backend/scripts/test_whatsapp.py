import sys
import os
from dotenv import load_dotenv

# Ensure we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.whatsapp_service import send_message

def test_whatsapp_configuration():
    print("🤖 Testing WhatsApp (Twilio) Configuration...\n")
    
    # Load env explicitly if not loaded
    load_dotenv()
    
    sid = os.environ.get("TWILIO_ACCOUNT_SID")
    token = os.environ.get("TWILIO_AUTH_TOKEN")
    from_number = os.environ.get("TWILIO_WHATSAPP_FROM")
    
    if not all([sid, token, from_number]):
        print("❌ ERROR: Twilio environment variables are missing.")
        print(f"SID: {'Found' if sid else 'Missing'}")
        print(f"Token: {'Found' if token else 'Missing'}")
        print(f"From Number: {'Found' if from_number else 'Missing'}")
        return
        
    print(f"Account SID: {sid[:10]}...")
    print(f"From Number: {from_number}")
    
    target_phone = input("\nEnter your phone number to receive a test message (e.g., +919876543210): ").strip()
    
    if not target_phone:
        print("❌ ERROR: No target phone number provided.")
        return
        
    print(f"\nSending test message to {target_phone}...")
    
    result = send_message(target_phone, "✅ *MediSync WhatsApp Test*\n\nYour backend is successfully connected to Twilio!")
    
    if result.get("success"):
        print("✉️  Message sent successfully! Check your WhatsApp.")
        print(f"Message SID: {result.get('message_id')}")
    else:
        print(f"❌ Failed to send message: {result.get('error')}")

if __name__ == "__main__":
    test_whatsapp_configuration()
