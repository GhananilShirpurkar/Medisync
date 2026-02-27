"""
VISION AGENT
=============
Extracts structured data from prescription images using Gemini Vision.
"""

import base64
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import json
import os


class MedicineItem(BaseModel):
    """Single medicine from prescription."""
    name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    instructions: Optional[str] = None


class PrescriptionData(BaseModel):
    """Structured prescription data."""
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    date: Optional[str] = None
    medicines: List[MedicineItem] = []
    special_instructions: Optional[str] = None
    diagnosis: Optional[str] = None


class VisionAgent:
    """
    Vision Agent for prescription OCR and data extraction.
    
    Uses Gemini's vision capabilities to extract structured data
    from prescription images via the native google.genai SDK.
    """
    
    def __init__(self):
        """Initialize Vision Agent."""
        try:
            from google import genai
            self.genai = genai
            self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        except ImportError:
            self.genai = None
            self.client = None
    
    def extract_prescription_data(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Extract structured data from prescription image.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Dictionary with extracted prescription data
        """
        if not self.client:
            return {
                "success": False,
                "error": "google-genai SDK not installed or GEMINI_API_KEY missing"
            }

        try:
            prompt = """
You are a medical prescription OCR expert. Analyze this prescription image and extract ALL information in JSON format.

Extract the following fields:
- patient_name: Patient's full name
- doctor_name: Doctor's full name
- date: Prescription date (format: YYYY-MM-DD if possible)
- diagnosis: Any diagnosis mentioned
- medicines: List of medicines with:
  * name: Medicine name (generic or brand)
  * dosage: Dosage amount (e.g., "500mg", "10ml")
  * frequency: How often to take (e.g., "twice daily", "3 times a day")
  * duration: How long to take (e.g., "7 days", "2 weeks")
  * instructions: Special instructions (e.g., "after meals", "before sleep")
- special_instructions: Any general notes or warnings

Return ONLY valid JSON. If a field is not found, use null.

Example format:
{
  "patient_name": "John Doe",
  "doctor_name": "Dr. Smith",
  "date": "2024-02-15",
  "diagnosis": "Bacterial infection",
  "medicines": [
    {
      "name": "Amoxicillin",
      "dosage": "500mg",
      "frequency": "3 times daily",
      "duration": "7 days",
      "instructions": "Take after meals"
    }
  ],
  "special_instructions": "Complete the full course"
}
"""
            
            # Using the native GenAI SDK
            from google.genai import types
            
            # Use gemini-2.5-flash as the primary multimodal model
            model_name = "gemini-2.5-flash"
            
            response = self.client.models.generate_content(
                model=model_name,
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                    prompt,
                ],
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="application/json"
                )
            )
            
            # Parse JSON response
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # Parse JSON
            data = json.loads(response_text)
            
            # Validate with Pydantic
            prescription = PrescriptionData(**data)
            
            return {
                "success": True,
                "data": prescription.model_dump() if hasattr(prescription, 'model_dump') else prescription.dict(),
                "raw_response": response_text
            }
            
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Failed to parse JSON: {str(e)}",
                "raw_response": response_text if 'response_text' in locals() else None
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Extraction failed: {str(e)}"
            }
    
    def validate_extraction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate extracted prescription data.
        
        Args:
            data: Extracted prescription data
            
        Returns:
            Validation results with warnings/errors
        """
        warnings = []
        errors = []
        
        # Check for required fields
        if not data.get("medicines") or len(data["medicines"]) == 0:
            errors.append("No medicines found in prescription")
        
        # Check each medicine
        for i, medicine in enumerate(data.get("medicines", [])):
            if not medicine.get("name"):
                errors.append(f"Medicine #{i+1}: Missing name")
            if not medicine.get("dosage"):
                warnings.append(f"{medicine.get('name', f'Medicine #{i+1}')}: Missing dosage")
            if not medicine.get("frequency"):
                warnings.append(f"{medicine.get('name', f'Medicine #{i+1}')}: Missing frequency")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
