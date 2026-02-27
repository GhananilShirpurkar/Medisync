"""
TELEGRAM BOT - MEDISYNC
========================
Polling mode bot for hackathon/development.
Clean architecture: Bot is just transport layer.
"""

import os
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# Load environment
load_dotenv(".env")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Import business logic
from src.telegram_pipeline import (
    process_text_message,
    process_prescription_image,
    process_voice_message
)


# ------------------------------------------------------------------
# COMMAND HANDLERS
# ------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    welcome_message = f"""
👋 Welcome to *MediSync* – Your Agentic Pharmacist!

I can help you with:
💊 Medicine orders
📋 Prescription verification
🔔 Refill reminders
❓ Medicine information

*Your Chat ID:* `{chat_id}`
_(Save this for notifications)_

Send me a message to get started!
"""
    
    await update.message.reply_text(
        welcome_message,
        parse_mode="Markdown"
    )
    
    # Log user registration
    print(f"📱 New user: {user.first_name} (ID: {chat_id})")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = """
*MediSync Commands:*

/start - Start the bot
/help - Show this help message
/status - Check order status
/refill - Request medicine refill

*How to use:*
Just send me a message like:
• "I need paracetamol"
• "Order 2 strips of amoxicillin"
• "When will my order arrive?"

Or send a prescription photo!
"""
    
    await update.message.reply_text(
        help_text,
        parse_mode="Markdown"
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command."""
    # TODO: Implement order status lookup
    await update.message.reply_text(
        "📦 Order status feature coming soon!\n"
        "For now, send me your order ID."
    )


# ------------------------------------------------------------------
# MESSAGE HANDLERS
# ------------------------------------------------------------------
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle text messages.
    
    This is the main entry point for user input.
    Business logic is delegated to the agent pipeline.
    """
    user_text = update.message.text
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    print(f"📨 Message from {user.first_name} ({chat_id}): {user_text}")
    
    # Show typing indicator
    await update.message.chat.send_action("typing")
    
    try:
        # Call agent pipeline
        result = await process_text_message(
            user_id=str(chat_id),
            telegram_chat_id=str(chat_id),
            message=user_text
        )
        
        # Send response
        await update.message.reply_text(
            result.get("message", "Processing..."),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        print(f"❌ Error processing message: {e}")
        await update.message.reply_text(
            "⚠️ Sorry, something went wrong. Please try again."
        )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle photo messages (prescription images).
    
    Downloads photo and processes with vision agent.
    """
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    print(f"📷 Photo from {user.first_name} ({chat_id})")
    
    await update.message.reply_text("📸 Processing prescription image...")
    
    try:
        # Get the largest photo
        photo = update.message.photo[-1]
        
        # Download photo
        file = await context.bot.get_file(photo.file_id)
        file_path = f"/tmp/prescription_{chat_id}_{photo.file_id}.jpg"
        await file.download_to_drive(file_path)
        
        print(f"✅ Photo downloaded: {file_path}")
        
        # Call vision agent pipeline
        result = await process_prescription_image(
            user_id=str(chat_id),
            telegram_chat_id=str(chat_id),
            image_path=file_path
        )
        
        # Send response
        await update.message.reply_text(
            result.get("message", "Processing..."),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        print(f"❌ Error processing photo: {e}")
        await update.message.reply_text(
            "⚠️ Could not process image. Please try again."
        )


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle voice messages.
    
    Downloads audio and processes with speech agent.
    """
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    print(f"🎤 Voice message from {user.first_name} ({chat_id})")
    
    await update.message.reply_text("🎤 Processing voice message...")
    
    try:
        # Download voice message
        voice = update.message.voice
        file = await context.bot.get_file(voice.file_id)
        file_path = f"/tmp/voice_{chat_id}_{voice.file_id}.ogg"
        await file.download_to_drive(file_path)
        
        print(f"✅ Voice downloaded: {file_path}")
        
        # Call speech agent pipeline
        result = await process_voice_message(
            user_id=str(chat_id),
            telegram_chat_id=str(chat_id),
            audio_path=file_path
        )
        
        # Send response
        await update.message.reply_text(
            result.get("message", "Processing..."),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        print(f"❌ Error processing voice: {e}")
        await update.message.reply_text(
            "⚠️ Could not process voice message. Please try again."
        )


# ------------------------------------------------------------------
# ERROR HANDLER
# ------------------------------------------------------------------
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors."""
    print(f"❌ Update {update} caused error: {context.error}")


# ------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------
def main():
    """Start the bot."""
    if not TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not set in .env")
        return
    
    print("🤖 Starting MediSync Telegram Bot...")
    print(f"   Token: {TOKEN[:20]}...")
    
    # Build application
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status_command))
    
    # Add message handlers
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_text_message
    ))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    
    # Add error handler
    app.add_error_handler(error_handler)
    
    # Start polling
    print("✅ Bot started! Press Ctrl+C to stop.")
    print("   Send /start to your bot to test it.")
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
