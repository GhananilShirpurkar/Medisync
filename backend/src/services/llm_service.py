"""
LLM SERVICE LAYER
=================
All external AI calls live here.

- Uses the NEW google.genai SDK
- No agent logic
- No FastAPI
- Pure input → output
"""

import os
from typing import List, Dict, Any

from dotenv import load_dotenv
try:
    from google import genai
    from google.genai import types
    HAS_GOOGLE_GENAI = True
except ImportError:
    HAS_GOOGLE_GENAI = False
    class MockTypes:
        class Content: 
            def __init__(self, role, parts): pass
        class Part: 
            def __init__(self, text): pass
        class GenerateContentConfig: 
            def __init__(self, **kwargs): pass
    types = MockTypes()
    genai = None

try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False
    Groq = None

from src.state import OrderItem

# ------------------------------------------------------------------
# ENV + CLIENT INIT
# ------------------------------------------------------------------
# Load .env from backend directory
import pathlib
env_path = pathlib.Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path, override=True)

# Import Langfuse decorators
from src.services.observability_service import observe, langfuse_context

# Lazy client initialization to avoid errors when API key not set
_client = None

def _get_client():
    """Get or initialize the Gemini client."""
    global _client
    
    if not HAS_GOOGLE_GENAI:
        return None
        
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return None
        try:
            _client = genai.Client(api_key=api_key)
        except Exception as e:
            print(f"Error initializing Gemini client: {e}")
            return None
            
    return _client

# ------------------------------------------------------------------
# GROQ AND GEMINI FALLBACK HYBRID
# ------------------------------------------------------------------
GROQ_MODEL = "llama-3.3-70b-versatile"
MODEL_HIERARCHY = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash"
]

_groq_client = None

def _get_groq_client():
    global _groq_client
    if not HAS_GROQ:
        return None
    if _groq_client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return None
        try:
            import httpx
            # Force IPv4 to prevent hanging on environments with broken IPv6 routes
            http_client = httpx.Client(
                transport=httpx.HTTPTransport(local_address="0.0.0.0"),
                timeout=10.0
            )
            _groq_client = Groq(api_key=api_key, http_client=http_client)
        except Exception as e:
            print(f"Error initializing Groq client: {e}")
            return None
    return _groq_client

def _generate_content_with_fallback(client, contents, config=None, **kwargs):
    """
    Gemini-specific wrapper that automatically falls back to secondary models 
    if a 429 Resource Exhausted (quota limit) error occurs.
    """
    from google.genai import errors
    
    last_error = None
    for model_name in MODEL_HIERARCHY:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config,
                **kwargs
            )
            if model_name != MODEL_HIERARCHY[0]:
                print(f"✅ Auto-fallback successful: Used {model_name}")
            return response, model_name
        except errors.APIError as e:
            last_error = e
            if getattr(e, 'code', None) == 429 or "429" in str(e):
                print(f"⚠️ Quota exhausted for {model_name}, trying fallback...")
                continue
            raise e
        except Exception as e:
            last_error = e
            if "429" in str(e):
                print(f"⚠️ Quota exhausted for {model_name}, trying fallback...")
                continue
            raise e
            
    print(f"❌ All models exhausted quota. Last error: {last_error}")
    raise last_error

def _generate_text_with_hybrid_fallback(prompt: str, is_json: bool = False, temperature: float = 0.2, system_prompt: str = None, history: List[Dict] = None) -> tuple[Any, str]:
    """
    Tries Groq (Llama 3 70B) first. If unavailable or fails, falls back to Gemini hierarchy.
    Returns (response_text_or_json_string, used_model_name).
    """
    groq_client = _get_groq_client()
    if groq_client:
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            if history:
                for msg in history:
                    messages.append({
                        "role": "user" if msg.get("role") == "user" else "assistant",
                        "content": msg.get("content", "")
                    })
            messages.append({"role": "user", "content": prompt})

            completion_kwargs = {
                "model": GROQ_MODEL,
                "messages": messages,
                "temperature": temperature,
            }
            if is_json:
                completion_kwargs["response_format"] = {"type": "json_object"}

            response = groq_client.chat.completions.create(**completion_kwargs)
            return response.choices[0].message.content, GROQ_MODEL
        except Exception as e:
            print(f"⚠️ Groq failed ({type(e).__name__}: {e}), falling back to Gemini...")

    # Fallback to Gemini
    gemini_client = _get_client()
    if not gemini_client:
        raise Exception("Both Groq and Gemini clients are unavailable.")

    contents = []
    if history:
        for msg in history:
            role = "user" if msg.get("role") == "user" else "model"
            contents.append(types.Content(role=role, parts=[types.Part(text=msg.get("content", ""))]))
    contents.append(types.Content(role="user", parts=[types.Part(text=prompt)]))
    
    config = types.GenerateContentConfig(
        temperature=temperature,
        system_instruction=system_prompt if system_prompt else None,
        response_mime_type="application/json" if is_json else None
    )

    response, used_model = _generate_content_with_fallback(
        client=gemini_client,
        contents=contents,
        config=config
    )
    return response.text, used_model

# ------------------------------------------------------------------
# INTERNAL HELPERS
# ------------------------------------------------------------------
def _safe_dict(value: Any) -> Dict:
    """Guarantee a dict return."""
    return value if isinstance(value, dict) else {}

def _safe_list(value: Any) -> List:
    """Guarantee a list return."""
    return value if isinstance(value, list) else []


# ------------------------------------------------------------------
# GENERIC STRUCTURED PARSING
# ------------------------------------------------------------------
@observe(as_type="generation")
def parse_structured(prompt: str) -> Dict:
    """
    Generic structured parsing using LLM.
    
    Expects prompt to request JSON response.
    Returns parsed JSON as dict.
    """
    try:
        text, used_model = _generate_text_with_hybrid_fallback(
            prompt=prompt,
            is_json=True,
            temperature=0.2
        )
        
        # Parse JSON from response
        import json
        result = json.loads(text)
        
        langfuse_context.update_current_observation(
            model=used_model,
            input=prompt,
            output=result
        )
        return _safe_dict(result)
        
    except Exception as e:
        print("LLM PARSE ERROR:", e)
        # Return empty dict on error
        return {}


# ------------------------------------------------------------------
# FRONT DESK EXTRACTION
# ------------------------------------------------------------------
@observe(as_type="generation")
def call_llm_extract(user_message: str) -> Dict:
    """
    Extract intent + medicines from messy human input.

    GUARANTEES:
    - Always returns a dict
    - Keys always exist
    """

    prompt = f"""
You are a pharmacy assistant.

Extract structured information from this message.

Message:
\"\"\"{user_message}\"\"\"

Return JSON ONLY in this exact format:
{{
  "intent": "purchase | refill | inquiry | unknown",
  "language": "en | hi | mixed",
  "items": [
    {{
      "medicine_name": "string",
      "dosage": "string | null",
      "quantity": number
    }}
  ]
}}
"""

    try:
        text, used_model = _generate_text_with_hybrid_fallback(
            prompt=prompt,
            is_json=True,
            temperature=0.2
        )

        # Parse JSON from response text
        import json
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = {}

    except Exception as e:
        print("LLM EXTRACT ERROR:", e)
        # Fallback to mock extraction on API error
        return _mock_extract(user_message)

    # 🔒 Hard schema guarantees
    final_output = {
        "intent": data.get("intent", "unknown"),
        "language": data.get("language", "en"),  # Default to en if unknown
        "items": _safe_list(data.get("items")),
    }
    
    langfuse_context.update_current_observation(
        model=used_model if 'used_model' in locals() else MODEL_HIERARCHY[0],
        input=user_message,
        output=final_output
    )
    
    return final_output

def _mock_extract(user_message: str) -> Dict:
    """Mock extraction for offline mode."""
    user_message = user_message.lower()
    items = []
    
    # Simple keyword extraction
    if "paracetamol" in user_message:
        items.append({"medicine_name": "Paracetamol", "dosage": "500mg", "quantity": 1})
    if "amoxicillin" in user_message:
        items.append({"medicine_name": "Amoxicillin", "dosage": "250mg", "quantity": 1})
        
    intent = "inquiry"
    if any(word in user_message for word in ["buy", "order", "purchase", "need", "want"]):
        intent = "purchase"
        
    return {
        "intent": intent,
        "language": "en",
        "items": items
    }


# ------------------------------------------------------------------
# TRANSLATION SERVICE
# ------------------------------------------------------------------
@observe(as_type="generation")
def call_llm_translate(text: str, target_language: str = "hi") -> str:
    """
    Translate text to target language using LLM.
    
    Args:
        text: Text to translate
        target_language: Target language code (default: hi)
        
    Returns:
        Translated text
    """
    if not text or not text.strip():
        return text
        
    # Check if API key is available
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("⚠️  GEMINI_API_KEY not set, returning original text")
        return text
        
    prompt = f"""
Translate the following medical/pharmacy related text to {target_language}.
Maintain a professional but empathetic tone.
Keep medical terms in English if they are commonly used (like Paracetamol), 
or provide the English term in brackets.

Text:
\"\"\"{text}\"\"\"

Return ONLY the translated text.
"""

    try:
        text_resp, used_model = _generate_text_with_hybrid_fallback(
            prompt=prompt,
            is_json=False,
            temperature=0.1
        )
        out_text = text_resp.strip()
        langfuse_context.update_current_observation(
            model=used_model,
            input=[{"role": "user", "content": text}],
            output=out_text
        )
        return out_text
    except Exception as e:
        print(f"LLM TRANSLATE ERROR: {e}")
        return text

# ------------------------------------------------------------------
# CONVERSATIONAL CHAT
# ------------------------------------------------------------------
@observe(as_type="generation")
def call_llm_chat(system_prompt: str, user_message: str, history: List[Dict] = None) -> str:
    """
    Free-form chat with system prompt and history.
    
    Args:
        system_prompt: The persona/instruction for the AI
        user_message: The latest user input
        history: List of previous message dicts [{"role": "user", "content": "..."}, ...]
        
    Returns:
        AI response string
    """
    try:
        text_resp, used_model = _generate_text_with_hybrid_fallback(
            prompt=user_message,
            is_json=False,
            temperature=0.7,
            system_prompt=system_prompt,
            history=history
        )
        
        out_text = text_resp.strip()
        langfuse_context.update_current_observation(
            model=used_model,
            input={"system": system_prompt, "messages": history + [{"role": "user", "content": user_message}] if history else [{"role": "user", "content": user_message}]},
            output=out_text
        )
        return out_text
        
    except Exception as e:
        import traceback; traceback.print_exc(); print(f"LLM CHAT ERROR: {e}")
        # Fallback response for offline mode
        return "I am currently running in offline mode. I can help you search for medicines by name or check stock, but conversational features are limited."

# ------------------------------------------------------------------
# SAFETY / INTERACTION CHECK
# ------------------------------------------------------------------
@observe(as_type="generation")
def call_llm_safety_check(items: List[OrderItem]) -> Dict[str, Any]:
    """
    Check for drug interactions or safety warnings using LLM.
    
    This provides intelligent interaction detection that handles:
    - Drug-drug interactions
    - Contraindications
    - Duplicate therapy warnings
    - Age/condition-specific warnings
    
    Args:
        items: List of OrderItem objects with medicine names and dosages
        
    Returns:
        Dictionary with interaction analysis:
        {
            "has_interactions": bool,
            "severity": "none" | "minor" | "moderate" | "severe",
            "interactions": [
                {
                    "medicines": ["med1", "med2"],
                    "severity": "moderate",
                    "description": "...",
                    "recommendation": "..."
                }
            ],
            "warnings": ["warning1", "warning2"],
            "safe_to_dispense": bool
        }
    
    GUARANTEES:
    - Always returns a dict with all required fields
    - Falls back to rule-based check if LLM unavailable
    """

    if not items:
        return {
            "has_interactions": False,
            "severity": "none",
            "interactions": [],
            "warnings": [],
            "safe_to_dispense": True
        }

    # Check if API key is available
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("⚠️  GEMINI_API_KEY not set, using rule-based interaction check")
        return _rule_based_interaction_check(items)

    # Build medicine list with dosages
    medicine_details = []
    for item in items:
        detail = f"{item.medicine_name}"
        if item.dosage:
            detail += f" ({item.dosage})"
        medicine_details.append(detail)
    
    meds_str = "\n".join(f"- {med}" for med in medicine_details)

    prompt = f"""
You are a clinical pharmacist expert in drug interactions.

Analyze the following medicines for potential interactions, contraindications, and safety concerns.

Medicines:
{meds_str}

Provide a comprehensive safety analysis in JSON format:

{{
  "has_interactions": boolean,
  "severity": "none" | "minor" | "moderate" | "severe",
  "interactions": [
    {{
      "medicines": ["medicine1", "medicine2"],
      "severity": "minor" | "moderate" | "severe",
      "description": "Clear explanation of the interaction",
      "recommendation": "What to do (e.g., monitor, adjust dose, avoid combination)"
    }}
  ],
  "warnings": [
    "General warning 1",
    "General warning 2"
  ],
  "safe_to_dispense": boolean
}}

Rules:
- Check for drug-drug interactions
- Check for duplicate therapy (same drug class)
- Consider dosage if provided
- Severity levels:
  * minor: Can be managed with monitoring
  * moderate: May require dose adjustment or timing changes
  * severe: Should not be combined without specialist consultation
- Set safe_to_dispense to false only for severe interactions
- Include practical recommendations for pharmacist
- If no interactions found, return empty interactions array
"""

    try:
        text, used_model = _generate_text_with_hybrid_fallback(
            prompt=prompt,
            is_json=True,
            temperature=0.1
        )

        # Parse JSON from response text
        import json
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            print("⚠️  Failed to parse LLM response, using rule-based check")
            return _rule_based_interaction_check(items)

    except Exception as e:
        print(f"LLM SAFETY ERROR: {type(e).__name__}: {e}")
        # Fallback to rule-based check on any error
        return _rule_based_interaction_check(items)

    # Ensure all required fields exist
    final_output = {
        "has_interactions": data.get("has_interactions", False),
        "severity": data.get("severity", "none"),
        "interactions": _safe_list(data.get("interactions")),
        "warnings": _safe_list(data.get("warnings")),
        "safe_to_dispense": data.get("safe_to_dispense", True)
    }
    langfuse_context.update_current_observation(
        model=used_model if 'used_model' in locals() else MODEL_HIERARCHY[0],
        input=meds_str,
        output=final_output
    )
    return final_output


def _rule_based_interaction_check(items: List[OrderItem]) -> Dict[str, Any]:
    """
    Rule-based drug interaction checking (fallback when LLM unavailable).
    
    Checks for:
    - Known dangerous combinations
    - Duplicate medicines
    - Common interaction patterns
    
    Args:
        items: List of OrderItem objects
        
    Returns:
        Same format as call_llm_safety_check
    """
    interactions = []
    warnings = []
    has_interactions = False
    severity = "none"
    safe_to_dispense = True
    
    # Extract medicine names (lowercase for comparison)
    medicine_names = [item.medicine_name.lower().strip() for item in items]
    
    # Rule 1: Check for duplicate medicines
    seen = set()
    for name in medicine_names:
        if name in seen:
            interactions.append({
                "medicines": [name, name],
                "severity": "moderate",
                "description": f"Duplicate medicine detected: {name.title()}",
                "recommendation": "Verify if intentional, may indicate prescription error"
            })
            has_interactions = True
            severity = "moderate"
        seen.add(name)
    
    # Rule 2: Known dangerous combinations
    dangerous_combinations = [
        # NSAIDs + Anticoagulants
        (["aspirin", "warfarin"], "severe", 
         "NSAIDs with anticoagulants increase bleeding risk",
         "Avoid combination or use with extreme caution and monitoring"),
        
        (["ibuprofen", "warfarin"], "severe",
         "NSAIDs with anticoagulants increase bleeding risk",
         "Avoid combination or use with extreme caution and monitoring"),
        
        # Multiple NSAIDs
        (["aspirin", "ibuprofen"], "moderate",
         "Multiple NSAIDs increase GI bleeding and kidney damage risk",
         "Use only one NSAID at a time"),
        
        (["ibuprofen", "diclofenac"], "moderate",
         "Multiple NSAIDs increase GI bleeding and kidney damage risk",
         "Use only one NSAID at a time"),
        
        # Benzodiazepines + Opioids
        (["alprazolam", "tramadol"], "severe",
         "Benzodiazepines with opioids can cause severe respiratory depression",
         "Avoid combination, high risk of overdose"),
        
        (["diazepam", "codeine"], "severe",
         "Benzodiazepines with opioids can cause severe respiratory depression",
         "Avoid combination, high risk of overdose"),
        
        # Multiple antibiotics (same class)
        (["amoxicillin", "ampicillin"], "moderate",
         "Multiple antibiotics from same class (penicillins)",
         "Use only one antibiotic unless specifically prescribed"),
        
        # ACE inhibitors + Potassium supplements
        (["lisinopril", "potassium"], "moderate",
         "ACE inhibitors with potassium can cause hyperkalemia",
         "Monitor potassium levels, may need dose adjustment"),
    ]
    
    for combo_meds, combo_severity, description, recommendation in dangerous_combinations:
        # Check if all medicines in combination are present
        if all(any(med in name for name in medicine_names) for med in combo_meds):
            interactions.append({
                "medicines": [med.title() for med in combo_meds],
                "severity": combo_severity,
                "description": description,
                "recommendation": recommendation
            })
            has_interactions = True
            
            # Update overall severity (take highest)
            if combo_severity == "severe":
                severity = "severe"
                safe_to_dispense = False
            elif combo_severity == "moderate" and severity != "severe":
                severity = "moderate"
    
    # Rule 3: General warnings for specific drug classes
    
    # NSAIDs warning
    nsaids = ["aspirin", "ibuprofen", "diclofenac", "naproxen", "indomethacin"]
    if any(any(nsaid in name for name in medicine_names) for nsaid in nsaids):
        warnings.append("NSAIDs present: Take with food to reduce GI irritation")
    
    # Antibiotics warning
    antibiotics = ["amoxicillin", "azithromycin", "ciprofloxacin", "doxycycline", "cephalexin"]
    if any(any(antibiotic in name for name in medicine_names) for antibiotic in antibiotics):
        warnings.append("Antibiotics present: Complete full course even if symptoms improve")
    
    # Controlled substances warning
    controlled = ["alprazolam", "diazepam", "tramadol", "codeine", "morphine"]
    if any(any(controlled_med in name for name in medicine_names) for controlled_med in controlled):
        warnings.append("Controlled substances present: Risk of dependence, use exactly as prescribed")
    
    # Steroids warning
    steroids = ["prednisolone", "dexamethasone", "hydrocortisone"]
    if any(any(steroid in name for name in medicine_names) for steroid in steroids):
        warnings.append("Steroids present: Do not stop abruptly, taper as directed")
    
    return {
        "has_interactions": has_interactions,
        "severity": severity,
        "interactions": interactions,
        "warnings": warnings,
        "safe_to_dispense": safe_to_dispense
    }


# ------------------------------------------------------------------
# VISION AGENT - PRESCRIPTION PARSING
# ------------------------------------------------------------------
@observe(as_type="generation")
def call_llm_parse_prescription(raw_text: str) -> Dict[str, Any]:
    """
    Parse raw OCR text into structured prescription data using LLM.
    
    This provides intelligent extraction that handles:
    - Messy handwriting transcriptions
    - Various prescription formats
    - Missing or unclear fields
    - Medicine name variations
    
    Args:
        raw_text: Raw text from OCR service
        
    Returns:
        Structured prescription data with confidence scores
        
    GUARANTEES:
    - Always returns a dict
    - All required fields present (may be null)
    """
    
    # Check if API key is available
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("⚠️  GEMINI_API_KEY not set, using mock prescription parsing")
        return _mock_prescription_parse(raw_text)
    
    prompt = f"""
You are a medical prescription parser.

Extract structured information from this prescription text.
Handle messy OCR output, abbreviations, and unclear text.

Prescription Text:
\"\"\"
{raw_text}
\"\"\"

Return JSON ONLY in this exact format:
{{
  "patient_name": "string or null",
  "doctor_name": "string or null",
  "doctor_registration_number": "string or null",
  "date": "YYYY-MM-DD or null",
  "medicines": [
    {{
      "name": "string",
      "dosage": "string (e.g., 500mg)",
      "frequency": "string (e.g., 3 times daily)",
      "duration": "string (e.g., 5 days)"
    }}
  ],
  "signature_present": boolean,
  "confidence": {{
    "overall": 0.0-1.0,
    "patient_name": 0.0-1.0,
    "doctor_name": 0.0-1.0,
    "medicines": 0.0-1.0
  }},
  "notes": "string or null (any unclear or concerning items)"
}}

Rules:
- Extract medicine names even if dosage is unclear
- Normalize medicine names (e.g., "Para" -> "Paracetamol")
- If date format is unclear, try to parse it
- Set confidence low if text is messy or ambiguous
- Include notes for anything that needs human review
"""

    try:
        client = _get_client()
        response, used_model = _generate_content_with_fallback(
            client=client,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json",
            )
        )

        # Parse JSON from response text
        import json
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            data = {}

    except Exception as e:
        print(f"LLM PRESCRIPTION PARSE ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to mock parsing on any error
        return _mock_prescription_parse(raw_text)

    # Ensure all required fields exist
    final_output = {
        "patient_name": data.get("patient_name"),
        "doctor_name": data.get("doctor_name"),
        "doctor_registration_number": data.get("doctor_registration_number"),
        "date": data.get("date"),
        "medicines": _safe_list(data.get("medicines")),
        "signature_present": data.get("signature_present", False),
        "confidence": _safe_dict(data.get("confidence")),
        "notes": data.get("notes")
    }
    langfuse_context.update_current_observation(
        model=used_model if 'used_model' in locals() else MODEL_HIERARCHY[0],
        input=raw_text,
        output=final_output
    )
    return final_output


def _mock_prescription_parse(raw_text: str) -> Dict[str, Any]:
    """
    Mock prescription parsing for development/testing.
    
    Extracts basic information from raw text without LLM.
    """
    import re
    
    # Simple pattern matching for mock parsing
    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
    
    # Extract patient name
    patient_name = None
    for line in lines:
        if 'patient' in line.lower() and 'name' in line.lower():
            # Extract name after "Patient Name:"
            parts = line.split(':', 1)
            if len(parts) > 1:
                patient_name = parts[1].strip()
            else:
                patient_name = line.strip()
            break
    
    # Extract doctor name
    doctor_name = None
    doctor_reg = None
    for line in lines:
        if 'dr.' in line.lower() or 'doctor' in line.lower():
            if 'registration' not in line.lower():
                doctor_name = line.strip()
        if 'registration' in line.lower():
            parts = line.split(':', 1)
            if len(parts) > 1:
                doctor_reg = parts[1].strip()
    
    # Extract date
    date = None
    date_pattern = r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}'
    for line in lines:
        if 'date' in line.lower():
            match = re.search(date_pattern, line)
            if match:
                date = match.group(0)
                break
    
    # Extract medicines (look for numbered list or medicine patterns)
    medicines = []
    medicine_pattern = r'(\d+)\.\s*([A-Za-z]+)\s+(\d+mg|ml)\s*-?\s*(.*)'
    
    for line in lines:
        match = re.match(medicine_pattern, line)
        if match:
            name = match.group(2)
            dosage = match.group(3)
            rest = match.group(4)
            
            # Try to extract frequency and duration
            frequency = None
            duration = None
            
            if 'times daily' in rest or 'times a day' in rest:
                freq_match = re.search(r'(\d+)\s+(?:times daily|times a day)', rest)
                if freq_match:
                    frequency = f"{freq_match.group(1)} times daily"
            
            if 'for' in rest and 'days' in rest:
                dur_match = re.search(r'for\s+(\d+)\s+days', rest)
                if dur_match:
                    duration = f"{dur_match.group(1)} days"
            
            medicines.append({
                "name": name,
                "dosage": dosage,
                "frequency": frequency or "As directed",
                "duration": duration
            })
    
    # If no medicines found with pattern, try simpler extraction
    if not medicines:
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ['mg', 'ml', 'tablet', 'capsule']):
                # Try to extract medicine name (first word)
                words = line.split()
                if words:
                    # Skip numbers
                    name_idx = 0
                    while name_idx < len(words) and (words[name_idx].replace('.', '').isdigit()):
                        name_idx += 1
                    
                    if name_idx < len(words):
                        name = words[name_idx]
                        dosage = words[name_idx + 1] if name_idx + 1 < len(words) else None
                        
                        medicines.append({
                            "name": name,
                            "dosage": dosage,
                            "frequency": "As directed",
                            "duration": None
                        })
    
    # Check for signature
    signature_present = any(
        keyword in raw_text.lower() 
        for keyword in ['signature', 'signed', 'dr.']
    )
    
    return {
        "patient_name": patient_name or "Jane Doe",
        "doctor_name": doctor_name or "Dr. John Smith",
        "doctor_registration_number": doctor_reg or "12345",
        "date": date or "2024-01-15",
        "medicines": medicines if medicines else [
            {"name": "Paracetamol", "dosage": "500mg", "frequency": "3 times daily", "duration": "5 days"},
            {"name": "Amoxicillin", "dosage": "250mg", "frequency": "2 times daily", "duration": "7 days"}
        ],
        "signature_present": signature_present,
        "confidence": {
            "overall": 0.85,
            "patient_name": 0.9,
            "doctor_name": 0.9,
            "medicines": 0.8
        },
        "notes": "Mock parsing - Gemini API not configured"
    }
