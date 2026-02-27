import sys
import os
import argparse
from pprint import pprint

# Ensure we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.llm_service import call_llm_chat
from src.services.observability_service import langfuse_context

def test_langfuse():
    print("🚀 Starting Langfuse Test...")
    
    print("\n[1] Checking Environment Variables...")
    pk = os.environ.get("LANGFUSE_PUBLIC_KEY")
    sk = os.environ.get("LANGFUSE_SECRET_KEY")
    host = os.environ.get("LANGFUSE_BASE_URL")
    
    if not pk or not sk:
        print("❌ ERROR: Langfuse keys missing from environment!")
        return
        
    print(f"✅ Keys found. Host: {host}")
    
    print("\n[2] Triggering LLM Call...")
    try:
        response = call_llm_chat(
            system_prompt="You are a helpful test assistant. Reply with exactly 'Langfuse Test Successful'.",
            user_message="Hello! This is a test."
        )
        print(f"🤖 LLM Response: {response}")
    except Exception as e:
        print(f"❌ LLM Call Failed: {e}")
        return

    print("\n[3] Flushing Langfuse Context...")
    try:
        langfuse_context.flush()
        print("✅ Flushed successfully!")
    except Exception as e:
        print(f"❌ Flush Failed: {e}")

    print("\n🎉 Test Complete! Check your Langfuse dashboard for a new trace.")

if __name__ == "__main__":
    test_langfuse()
