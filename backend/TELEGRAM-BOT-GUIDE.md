# 🤖 Telegram Bot Guide

## Quick Start

### 1. Install Dependencies
```bash
pip install python-telegram-bot --upgrade
```

### 2. Configure Bot Token
Already set in `.env`:
```bash
TELEGRAM_BOT_TOKEN="8334042946:AAGuo-Sr9mgw2dZPU4Pf-C5yVy28TTtrtgk"
```

### 3. Run the Bot
```bash
python backend/telegram_bot.py
```

### 4. Test the Bot
1. Open Telegram
2. Search for your bot (get username from @BotFather)
3. Send `/start`
4. Try sending messages!

---

## Architecture

### Clean Separation of Concerns

```
Telegram Bot (telegram_bot.py)
    ↓ (transport layer only)
Pipeline Integration (telegram_pipeline.py)
    ↓ (orchestration)
Agent System (agents.py)
    ↓ (business logic)
Services (ocr_service.py, speech_service.py, etc.)
```

**Key Principle:** Bot handlers are thin wrappers. All business logic lives in agents.

---

## Features

### Text Messages
```
User: "I need paracetamol"
Bot: Processes through agent pipeline
     → Front Desk Agent (extraction)
     → Pharmacist Agent (validation)
     → Fulfillment Agent (order)
     → Notification
```

### Prescription Images
```
User: [Sends photo]
Bot: Downloads image
     → Vision Agent (OCR + parsing)
     → Pharmacist Agent (validation)
     → Fulfillment Agent (order)
     → Notification
```

### Voice Messages
```
User: [Sends voice]
Bot: Downloads audio
     → Speech Agent (transcription)
     → Front Desk Agent (extraction)
     → Pharmacist Agent (validation)
     → Fulfillment Agent (order)
     → Notification
```

---

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message + chat ID |
| `/help` | Show help text |
| `/status` | Check order status |

---

## Message Flow

### 1. Text Message Handler
```python
async def handle_text_message(update, context):
    # Get user input
    user_text = update.message.text
    chat_id = update.effective_chat.id
    
    # Call pipeline (business logic)
    result = await process_text_message(
        user_id=str(chat_id),
        telegram_chat_id=str(chat_id),
        message=user_text
    )
    
    # Send response
    await update.message.reply_text(result["message"])
```

### 2. Pipeline Processing
```python
async def process_text_message(user_id, telegram_chat_id, message):
    # Initialize state
    state = PharmacyState(
        user_id=user_id,
        telegram_chat_id=telegram_chat_id,
        user_message=message
    )
    
    # Run through agents
    state = front_desk_agent(state)
    state = pharmacist_agent(state)
    state = fulfillment_agent(state)
    
    # Return response
    return {"message": "Order confirmed!", "state": state}
```

---

## Testing

### Local Testing (Polling Mode)
```bash
python backend/telegram_bot.py
```

Bot will poll Telegram servers for updates. Good for development.

### Production (Webhook Mode)
For production, use webhooks instead of polling:

```python
# Set webhook
import requests

url = f"https://api.telegram.org/bot{TOKEN}/setWebhook"
data = {"url": "https://your-domain.com/telegram/webhook"}
requests.post(url, json=data)
```

Then handle webhooks in FastAPI:
```python
@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    # Process update
    return {"ok": True}
```

---

## File Structure

```
backend/
├── telegram_bot.py              # Bot entry point (polling mode)
├── src/
│   ├── telegram_pipeline.py     # Pipeline integration
│   ├── agents.py                # Business logic agents
│   ├── services/
│   │   ├── telegram_service.py  # Telegram API wrapper
│   │   ├── ocr_service.py       # Vision processing
│   │   └── speech_service.py    # Audio processing
│   └── state.py                 # Shared state model
└── tests/
    └── test_telegram_service.py # Tests
```

---

## Development Workflow

### 1. Start Bot
```bash
python backend/telegram_bot.py
```

### 2. Send Test Message
Open Telegram → Send message to bot

### 3. Check Logs
```
📨 Message from John (123456789): I need paracetamol
🤖 Processing through pipeline...
✅ Order created: ORD-12345
```

### 4. Iterate
- Modify agents in `src/agents.py`
- Restart bot
- Test again

---

## Common Issues

### Bot Not Responding
**Check:**
1. Token is correct in `.env`
2. Bot is running (`python telegram_bot.py`)
3. No firewall blocking Telegram API

### "Unauthorized" Error
**Fix:** Token is invalid. Get new token from @BotFather

### Messages Not Processing
**Check:**
1. Pipeline integration is correct
2. Agents are returning valid state
3. Check console logs for errors

---

## Next Steps

1. ✅ Bot running with polling
2. ✅ Pipeline integration complete
3. 🎯 Test with real messages
4. 🎯 Add database integration
5. 🎯 Deploy with webhook mode
6. 🎯 Add inline keyboards for better UX

---

## Production Checklist

- [ ] Switch from polling to webhook
- [ ] Add rate limiting
- [ ] Implement user authentication
- [ ] Store chat IDs in database
- [ ] Add error recovery
- [ ] Set up monitoring
- [ ] Add logging
- [ ] Test with multiple users

---

## Resources

- [python-telegram-bot Documentation](https://docs.python-telegram-bot.org/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [BotFather](https://t.me/botfather) - Manage your bot

---

## Status

✅ **Bot Ready**

The Telegram bot is fully integrated with the agent pipeline and ready for testing!
