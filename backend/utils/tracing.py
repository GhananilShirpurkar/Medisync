# backend/utils/tracing.py
import os
from langfuse import Langfuse

langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com"),
)

def check_tracing():
    """Check if Langfuse tracing is available."""
    try:
        if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
            # Try to verify connection
            langfuse.auth_check()
            print("✅ Langfuse connected — tracing enabled")
        else:
            print("⚠️  Langfuse keys not configured — tracing disabled")
    except Exception as e:
        print(f"⚠️  Langfuse not available: {e}")

