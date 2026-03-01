"""
LANGUAGE SERVICE
================
Multi-language support for Hindi, English, Hinglish, and Marathi.
Handles language detection, translation, and localized responses.
"""

import re
from typing import Dict, Optional, List
from enum import Enum

class Language(str, Enum):
    """Supported languages."""
    ENGLISH = "en"
    HINDI = "hi"
    MARATHI = "mr"
    HINGLISH = "mixed"  # English-Hindi mix


# ------------------------------------------------------------------
# LANGUAGE DETECTION
# ------------------------------------------------------------------

def detect_language(text: str) -> str:
    """
    Detect language from user input.
    
    Returns: "en" | "hi" | "mr" | "mixed"
    """
    if not text or not text.strip():
        return Language.ENGLISH
    
    text_lower = text.lower().strip()
    
    # Devanagari script detection (Hindi/Marathi)
    devanagari_pattern = re.compile(r'[\u0900-\u097F]')
    has_devanagari = bool(devanagari_pattern.search(text))
    
    # Marathi-specific words
    marathi_keywords = [
        'मला', 'आहे', 'काय', 'कसे', 'कुठे', 'कधी', 'कोण',
        'तुम्ही', 'तुमचे', 'माझे', 'आपले', 'येथे', 'तेथे'
    ]
    
    # Hindi-specific words
    hindi_keywords = [
        'मुझे', 'है', 'क्या', 'कैसे', 'कहाँ', 'कब', 'कौन',
        'आप', 'आपका', 'मेरा', 'यहाँ', 'वहाँ', 'हूँ', 'हैं'
    ]
    
    # Hinglish patterns (Roman script with Hindi words)
    hinglish_patterns = [
        'mujhe', 'hai', 'kya', 'kaise', 'kahan', 'kab',
        'aap', 'aapka', 'mera', 'yahan', 'wahan',
        'bukhar', 'dard', 'sir', 'pet', 'dawai'
    ]
    
    # Check for Marathi
    if has_devanagari and any(word in text for word in marathi_keywords):
        return Language.MARATHI
    
    # Check for Hindi
    if has_devanagari and any(word in text for word in hindi_keywords):
        return Language.HINDI
    
    # Check for Hinglish (Roman script with Hindi words)
    if any(pattern in text_lower for pattern in hinglish_patterns):
        return Language.HINGLISH
    
    # Check for pure Devanagari (default to Hindi if no specific markers)
    if has_devanagari:
        return Language.HINDI
    
    # Default to English
    return Language.ENGLISH


# ------------------------------------------------------------------
# LOCALIZED TEMPLATES
# ------------------------------------------------------------------

TEMPLATES = {
    # Greeting messages
    "greeting": {
        "en": "Hello! I'm your MediSync pharmacist. How can I help you today?",
        "hi": "नमस्ते! मैं आपका MediSync फार्मासिस्ट हूँ। आज मैं आपकी कैसे मदद कर सकता हूँ?",
        "mr": "नमस्कार! मी तुमचा MediSync फार्मासिस्ट आहे। आज मी तुम्हाला कशी मदत करू शकतो?",
        "mixed": "Hello! Main aapka MediSync pharmacist hoon. Aaj main aapki kaise madad kar sakta hoon?"
    },
    
    # Asking for symptoms
    "ask_symptoms": {
        "en": "What symptoms are you experiencing?",
        "hi": "आपको क्या लक्षण हो रहे हैं?",
        "mr": "तुम्हाला कोणती लक्षणे आहेत?",
        "mixed": "Aapko kya symptoms ho rahe hain?"
    },
    
    # Asking for age
    "ask_age": {
        "en": "May I know your age?",
        "hi": "क्या मैं आपकी उम्र जान सकता हूँ?",
        "mr": "मी तुमचे वय जाणू शकतो का?",
        "mixed": "Kya main aapki age jaan sakta hoon?"
    },
    
    # Asking for duration
    "ask_duration": {
        "en": "How long have you had these symptoms?",
        "hi": "आपको ये लक्षण कितने समय से हैं?",
        "mr": "तुम्हाला ही लक्षणे किती दिवसांपासून आहेत?",
        "mixed": "Aapko ye symptoms kitne time se hain?"
    },
    
    # Asking for allergies
    "ask_allergies": {
        "en": "Do you have any known allergies to medicines?",
        "hi": "क्या आपको किसी दवा से एलर्जी है?",
        "mr": "तुम्हाला कोणत्याही औषधाची ऍलर्जी आहे का?",
        "mixed": "Kya aapko kisi medicine se allergy hai?"
    },
    
    # Confirmation messages
    "order_confirmed": {
        "en": "Your order has been confirmed. Order ID: {order_id}",
        "hi": "आपका ऑर्डर कन्फर्म हो गया है। ऑर्डर ID: {order_id}",
        "mr": "तुमची ऑर्डर कन्फर्म झाली आहे। ऑर्डर ID: {order_id}",
        "mixed": "Aapka order confirm ho gaya hai. Order ID: {order_id}"
    },
    
    # Payment messages
    "payment_pending": {
        "en": "Please complete the payment to proceed.",
        "hi": "कृपया आगे बढ़ने के लिए भुगतान पूरा करें।",
        "mr": "कृपया पुढे जाण्यासाठी पेमेंट पूर्ण करा।",
        "mixed": "Kripya aage badhne ke liye payment complete karein."
    },
    
    # Safety warnings
    "prescription_required": {
        "en": "This medicine requires a prescription. Please upload your prescription.",
        "hi": "इस दवा के लिए प्रिस्क्रिप्शन आवश्यक है। कृपया अपना प्रिस्क्रिप्शन अपलोड करें।",
        "mr": "या औषधासाठी प्रिस्क्रिप्शन आवश्यक आहे. कृपया तुमचे प्रिस्क्रिप्शन अपलोड करा.",
        "mixed": "Is medicine ke liye prescription chahiye. Kripya apna prescription upload karein."
    },
    
    # Emergency warnings
    "seek_emergency": {
        "en": "These symptoms may be serious. Please consult a doctor immediately.",
        "hi": "ये लक्षण गंभीर हो सकते हैं। कृपया तुरंत डॉक्टर से परामर्श लें।",
        "mr": "ही लक्षणे गंभीर असू शकतात. कृपया ताबडतोब डॉक्टरांचा सल्ला घ्या.",
        "mixed": "Ye symptoms serious ho sakte hain. Kripya turant doctor se consult karein."
    },
    
    # Out of stock
    "out_of_stock": {
        "en": "{medicine} is currently out of stock. Would you like an alternative?",
        "hi": "{medicine} अभी स्टॉक में नहीं है। क्या आप विकल्प चाहेंगे?",
        "mr": "{medicine} सध्या स्टॉकमध्ये नाही. तुम्हाला पर्याय हवा आहे का?",
        "mixed": "{medicine} abhi stock mein nahi hai. Kya aap alternative chahenge?"
    },
    
    # Thank you
    "thank_you": {
        "en": "Thank you for using MediSync. Take care!",
        "hi": "MediSync का उपयोग करने के लिए धन्यवाद। अपना ख्याल रखें!",
        "mr": "MediSync वापरल्याबद्दल धन्यवाद. काळजी घ्या!",
        "mixed": "MediSync use karne ke liye dhanyavaad. Apna khayal rakhein!"
    }
}


def get_template(key: str, language: str, **kwargs) -> str:
    """
    Get localized template string.
    
    Args:
        key: Template key
        language: Language code (en, hi, mr, mixed)
        **kwargs: Format arguments for template
        
    Returns:
        Localized string
    """
    if key not in TEMPLATES:
        return ""
    
    template_dict = TEMPLATES[key]
    
    # Fallback to English if language not found
    if language not in template_dict:
        language = "en"
    
    template = template_dict[language]
    
    # Format with kwargs if provided
    if kwargs:
        try:
            return template.format(**kwargs)
        except KeyError:
            return template
    
    return template


# ------------------------------------------------------------------
# LANGUAGE-AWARE SYSTEM PROMPTS
# ------------------------------------------------------------------

def get_system_prompt(language: str, patient_context: Dict) -> str:
    """
    Get language-aware system prompt for LLM.
    
    Args:
        language: Detected language code
        patient_context: Patient context dictionary
        
    Returns:
        System prompt with language instructions
    """
    
    # Base prompt
    base_prompt = """You are an expert, intellectual, and empathetic clinical pharmacist at MediSync.
Your name is "MediSync Pharmacist".

GOAL:
Interact with patients to understand their symptoms, medical history, and needs.
Your output will be shown directly to the patient.

PERSONA GUIDELINES:
1. **Intellectual**: Use precise medical terminology when appropriate, but always explain it in simple terms.
2. **Empathetic**: Acknowledge the patient's pain or discomfort.
3. **Professional**: Maintain a calm, reassuring, and objective tone.
4. **Inquisitive**: Ask relevant follow-up questions to rule out red flags.
5. **Concise**: Keep responses brief (2-3 sentences max) unless explaining a complex concept.
"""
    
    # Language-specific instructions
    language_instructions = {
        "en": """
LANGUAGE INSTRUCTIONS:
- Respond in ENGLISH ONLY.
- Use clear, simple English that is easy to understand.
- Avoid mixing other languages.
""",
        "hi": """
भाषा निर्देश:
- केवल हिंदी (देवनागरी) में जवाब दें।
- सरल और स्पष्ट हिंदी का उपयोग करें।
- चिकित्सा शब्दों को अंग्रेजी में रख सकते हैं (जैसे Paracetamol)।
- अन्य भाषाओं को मिलाएं नहीं।

LANGUAGE INSTRUCTIONS:
- Respond in HINDI (Devanagari script) ONLY.
- Use clear, simple Hindi that is easy to understand.
- Medical terms can be kept in English (e.g., Paracetamol).
- Do not mix other languages.
""",
        "mr": """
भाषा सूचना:
- फक्त मराठी (देवनागरी) मध्ये उत्तर द्या।
- सोपी आणि स्पष्ट मराठी वापरा।
- वैद्यकीय शब्द इंग्रजीमध्ये ठेवू शकता (उदा. Paracetamol).
- इतर भाषा मिसळू नका।

LANGUAGE INSTRUCTIONS:
- Respond in MARATHI (Devanagari script) ONLY.
- Use clear, simple Marathi that is easy to understand.
- Medical terms can be kept in English (e.g., Paracetamol).
- Do not mix other languages.
""",
        "mixed": """
LANGUAGE INSTRUCTIONS (HINGLISH):
- Respond in HINGLISH (Hindi words in Roman script).
- Use simple conversational Hinglish that is easy to understand.
- Example: "Aapko bukhar hai? Kitne din se?"
- Keep medical terms in English (e.g., Paracetamol, fever).
- Do not use Devanagari script.
"""
    }
    
    # Safety protocols
    safety_prompt = """
SAFETY PROTOCOLS:
- If symptoms are life-threatening (chest pain, stroke signs, severe difficulty breathing), immediately advise ER/Doctor.
- **Context Awareness**: CHECK THE CONTEXT. If the user already stated their age/symptoms, DO NOT ASK AGAIN.

CONTEXT:
You have access to the following patient information:
{patient_context}

INSTRUCTIONS:
- Review the patient_context carefully.
- If key information is missing (Age, Duration, Severity, Allergies), ask for it naturally. Ask only ONE question at a time.
- If you have enough information, output: "READY_TO_RECOMMEND"
- NEVER recommend specific medicines yourself. Just gather info or signal readiness.
"""
    
    # Get language instruction
    lang_instruction = language_instructions.get(language, language_instructions["en"])
    
    # Combine prompts
    full_prompt = base_prompt + lang_instruction + safety_prompt
    
    # Format with patient context
    return full_prompt.format(patient_context=patient_context)


# ------------------------------------------------------------------
# MEDICINE NAME NORMALIZATION
# ------------------------------------------------------------------

# Common medicine name variations across languages
MEDICINE_ALIASES = {
    "paracetamol": ["para", "पैरासिटामोल", "पॅरासिटामॉल", "crocin", "dolo"],
    "ibuprofen": ["brufen", "आइबुप्रोफेन", "आयबुप्रोफेन"],
    "amoxicillin": ["amoxy", "एमोक्सिसिलिन", "अमोक्सिसिलिन"],
    "azithromycin": ["azithro", "azee", "एज़िथ्रोमाइसिन", "अझिथ्रोमायसिन"],
    "cetirizine": ["cetrizine", "सेटिरिज़िन", "सेटिरिझिन"],
    "omeprazole": ["omez", "ओमेप्राज़ोल", "ओमेप्राझोल"],
    "metformin": ["मेटफॉर्मिन", "मेटफॉर्मिन"],
    "aspirin": ["एस्पिरिन", "ॲस्पिरिन", "disprin"]
}


def normalize_medicine_name(name: str) -> str:
    """
    Normalize medicine name across languages.
    
    Args:
        name: Medicine name in any language
        
    Returns:
        Normalized English name
    """
    if not name:
        return ""
    
    name_lower = name.lower().strip()
    
    # Check aliases
    for standard_name, aliases in MEDICINE_ALIASES.items():
        if name_lower == standard_name or name_lower in [a.lower() for a in aliases]:
            return standard_name.title()
    
    # Return original if no match
    return name.title()


# ------------------------------------------------------------------
# SYMPTOM TRANSLATION
# ------------------------------------------------------------------

SYMPTOM_TRANSLATIONS = {
    # Fever
    "bukhar": "fever",
    "बुखार": "fever",
    "ताप": "fever",
    
    # Headache
    "sir dard": "headache",
    "सिर दर्द": "headache",
    "डोकेदुखी": "headache",
    
    # Stomach ache
    "pet dard": "stomach ache",
    "पेट दर्द": "stomach ache",
    "पोटदुखी": "stomach ache",
    
    # Cough
    "khansi": "cough",
    "खांसी": "cough",
    "खोकला": "cough",
    
    # Cold
    "sardi": "cold",
    "जुकाम": "cold",
    "सर्दी": "cold",
    
    # Body pain
    "badan dard": "body pain",
    "शरीर दर्द": "body pain",
    "अंगदुखी": "body pain",
    
    # Diarrhea
    "dast": "diarrhea",
    "दस्त": "diarrhea",
    "अतिसार": "diarrhea",
    
    # Vomiting
    "ulti": "vomiting",
    "उल्टी": "vomiting",
    "वांती": "vomiting"
}


def translate_symptom(symptom: str) -> str:
    """
    Translate symptom to English.
    
    Args:
        symptom: Symptom in any language
        
    Returns:
        English symptom name
    """
    if not symptom:
        return ""
    
    symptom_lower = symptom.lower().strip()
    
    # Check direct translation
    if symptom_lower in SYMPTOM_TRANSLATIONS:
        return SYMPTOM_TRANSLATIONS[symptom_lower]
    
    # Return original if no translation found
    return symptom
