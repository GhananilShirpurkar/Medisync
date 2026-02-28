import os
import sys

# Add backend directory to sys.path so we can import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from dotenv import load_dotenv

# Load .env
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
load_dotenv(env_path)

from src.agents.vision_agent import VisionAgent
import json
import base64

def run_test():
    agent = VisionAgent()
    
    # Check for test image
    image_path = os.path.join(os.path.dirname(__file__), "test_prescription.jpg")
    if not os.path.exists(image_path):
        print(f"Error: Could not find test image at {image_path}")
        # Create a dummy image for testing if none exists
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new('RGB', (400, 200), color = (255, 255, 255))
        d = ImageDraw.Draw(img)
        d.text((10,10), "Rx Paracetamol 500mg\n1 tablet twice daily\nfor 5 days", fill=(0,0,0))
        img.save(image_path)
        print(f"Created a dummy image at {image_path}")
        
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    print("Extracting data...")
    result = agent.extract_prescription_data(image_bytes)
    
    print("\n--- RESULT ---")
    print(json.dumps(result, indent=2))
    
    if result.get("success"):
        validation = agent.validate_extraction(result["data"])
        print("\n--- VALIDATION ---")
        print(json.dumps(validation, indent=2))
        
if __name__ == "__main__":
    run_test()
