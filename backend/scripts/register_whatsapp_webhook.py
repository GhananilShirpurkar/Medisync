import sys
import os
from twilio.rest import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

def set_whatsapp_webhook(url: str):
    sid = os.environ.get("TWILIO_ACCOUNT_SID")
    token = os.environ.get("TWILIO_AUTH_TOKEN")
    from_number = os.environ.get("TWILIO_WHATSAPP_FROM")
    
    if not all([sid, token, from_number]):
        print("❌ Error: Twilio credentials missing in .env")
        return

    # Extract the actual number to find the SID
    # from_number is usually "whatsapp:+14155238886"
    raw_number = from_number.replace("whatsapp:", "")
    
    try:
        client = Client(sid, token)
        
        # Sandbox Check: Standard IncomingPhoneNumbers API cannot update Sandbox webhooks
        if raw_number == "+14155238886":
            print(f"ℹ️  Detected Twilio Sandbox number ({raw_number})")
            print(f"⚠️  Sandbox webhooks MUST be set manually in the Twilio Console.")
            print(f"Please go to: https://console.twilio.com/us1/develop/sms/settings/whatsapp-sandbox")
            print(f"Set 'When a message comes in' to:")
            print(f"👉 {url}")
            return

        # Find the incoming phone number SID
        numbers = client.incoming_phone_numbers.list(phone_number=raw_number)
        
        if not numbers:
            # Maybe it's a Sandbox number or we can't find it by strict match
            print(f"⚠️  Could not find incoming phone number SID for {raw_number}")
            print(f"Please manually set your webhook in the Twilio Console to:")
            print(f"👉 {url}")
            return
            
        number_sid = numbers[0].sid
        client.incoming_phone_numbers(number_sid).update(sms_url=url)
        
        print(f"✅ WhatsApp Webhook successfully updated for {raw_number}")
        print(f"New URL: {url}")
        
    except Exception as e:
        print(f"❌ Failed to update Twilio webhook: {e}")
        print(f"Please manually set your webhook in the Twilio Console to:")
        print(f"👉 {url}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python register_whatsapp_webhook.py [WEBHOOK_URL]")
        print("Example: python scripts/register_whatsapp_webhook.py https://my-ngrok-url.com/api/webhook/whatsapp")
        sys.exit(1)
        
    set_whatsapp_webhook(sys.argv[1])
