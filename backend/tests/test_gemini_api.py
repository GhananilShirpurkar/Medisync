"""Quick test to verify Gemini API is working"""
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

print(f"API Key loaded: {os.getenv('GEMINI_API_KEY')[:20]}...")

try:
    from google import genai
    from google.genai import types
    
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    # List available models
    print("\n📋 Available models:")
    models = client.models.list()
    for model in models:
        print(f"  - {model.name}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
