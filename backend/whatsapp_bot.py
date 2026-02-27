from fastapi import APIRouter, Form, Request
import logging
from src.whatsapp_pipeline import WhatsAppPipeline

router = APIRouter()
pipeline = WhatsAppPipeline()
logger = logging.getLogger(__name__)

@router.post("/webhook/whatsapp")
async def whatsapp_webhook(
    request: Request,
    From: str = Form(...),
    Body: str = Form(default=""),
    MediaUrl0: str = Form(default=None),
    MediaContentType0: str = Form(default=None),
    NumMedia: int = Form(default=0),
):
    """
    Twilio sends POST to this endpoint for every inbound WhatsApp message.
    From = 'whatsapp:+91XXXXXXXXXX'
    Body = message text
    MediaUrl0 = URL of attached image/voice (if any)
    """
    # Extract clean phone number
    phone = From.replace("whatsapp:", "").replace("+91", "")
    
    logger.info(f"Received WhatsApp from {phone}: {Body} (Media: {NumMedia})")

    if NumMedia > 0 and MediaContentType0:
        if MediaContentType0.startswith("image/"):
            await pipeline.handle_image(phone, MediaUrl0)
        elif MediaContentType0.startswith("audio/"):
            await pipeline.handle_voice(phone, MediaUrl0)
        else:
            logger.warning(f"Unsupported media type: {MediaContentType0}")
    else:
        await pipeline.handle_text(phone, Body)

    # Twilio requires a 200 response — return empty TwiML
    return "<Response></Response>"
