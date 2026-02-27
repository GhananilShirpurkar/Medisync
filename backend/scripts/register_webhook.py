import sys
import os
import requests
from dotenv import load_dotenv

# Ensure we can import from .env
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

def set_webhook(url: str):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ Error: TELEGRAM_BOT_TOKEN not found.")
        return
        
    api_url = f"https://api.telegram.org/bot{token}/setWebhook"
    response = requests.post(api_url, json={"url": url})
    
    if response.status_code == 200 and response.json().get("ok"):
        print(f"✅ Webhook successfully set to: {url}")
    else:
        print(f"❌ Failed to set webhook: {response.text}")

def delete_webhook():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ Error: TELEGRAM_BOT_TOKEN not found.")
        return
        
    api_url = f"https://api.telegram.org/bot{token}/deleteWebhook"
    response = requests.post(api_url)
    
    if response.status_code == 200 and response.json().get("ok"):
        print("✅ Webhook successfully deleted. The bot is now off-hook.")
    else:
        print(f"❌ Failed to delete webhook: {response.text}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python register_webhook.py [SET_URL | DELETE]")
        print("Example: python scripts/register_webhook.py https://my-ngrok-url.com/api/telegram/webhook")
        sys.exit(1)
        
    arg = sys.argv[1]
    if arg.upper() == "DELETE":
        delete_webhook()
    else:
        set_webhook(arg)
