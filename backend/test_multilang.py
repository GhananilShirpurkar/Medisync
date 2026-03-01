"""
Test Multi-Language Support
============================
Test language detection and localization for Hindi, English, Hinglish, and Marathi.
"""

from src.services.language_service import (
    detect_language,
    get_template,
    normalize_medicine_name,
    translate_symptom,
    Language
)


def test_language_detection():
    """Test language detection."""
    print("=" * 60)
    print("TESTING LANGUAGE DETECTION")
    print("=" * 60)
    
    test_cases = [
        ("I need paracetamol", Language.ENGLISH),
        ("मुझे बुखार है", Language.HINDI),
        ("मला ताप आहे", Language.MARATHI),
        ("mujhe sir dard hai", Language.HINGLISH),
        ("I have bukhar", Language.HINGLISH),
        ("क्या आपके पास पैरासिटामोल है?", Language.HINDI),
        ("तुम्हाला कोणती औषधे हवी आहेत?", Language.MARATHI),
    ]
    
    for text, expected in test_cases:
        detected = detect_language(text)
        status = "✅" if detected == expected else "❌"
        print(f"{status} '{text}' -> {detected} (expected: {expected})")
    print()


def test_templates():
    """Test localized templates."""
    print("=" * 60)
    print("TESTING LOCALIZED TEMPLATES")
    print("=" * 60)
    
    languages = [Language.ENGLISH, Language.HINDI, Language.MARATHI, Language.HINGLISH]
    templates = ["greeting", "ask_symptoms", "ask_age", "order_confirmed"]
    
    for template_key in templates:
        print(f"\n{template_key.upper()}:")
        for lang in languages:
            text = get_template(template_key, lang, order_id="ORD123")
            print(f"  [{lang}] {text}")
    print()


def test_medicine_normalization():
    """Test medicine name normalization."""
    print("=" * 60)
    print("TESTING MEDICINE NAME NORMALIZATION")
    print("=" * 60)
    
    test_cases = [
        ("para", "Paracetamol"),
        ("पैरासिटामोल", "Paracetamol"),
        ("crocin", "Paracetamol"),
        ("brufen", "Ibuprofen"),
        ("आइबुप्रोफेन", "Ibuprofen"),
        ("azee", "Azithromycin"),
        ("disprin", "Aspirin"),
    ]
    
    for input_name, expected in test_cases:
        normalized = normalize_medicine_name(input_name)
        status = "✅" if normalized == expected else "❌"
        print(f"{status} '{input_name}' -> {normalized} (expected: {expected})")
    print()


def test_symptom_translation():
    """Test symptom translation."""
    print("=" * 60)
    print("TESTING SYMPTOM TRANSLATION")
    print("=" * 60)
    
    test_cases = [
        ("bukhar", "fever"),
        ("बुखार", "fever"),
        ("sir dard", "headache"),
        ("सिर दर्द", "headache"),
        ("डोकेदुखी", "headache"),
        ("khansi", "cough"),
        ("खांसी", "cough"),
        ("pet dard", "stomach ache"),
        ("पेट दर्द", "stomach ache"),
    ]
    
    for symptom, expected in test_cases:
        translated = translate_symptom(symptom)
        status = "✅" if translated == expected else "❌"
        print(f"{status} '{symptom}' -> {translated} (expected: {expected})")
    print()


def test_system_prompt():
    """Test language-aware system prompts."""
    print("=" * 60)
    print("TESTING SYSTEM PROMPTS")
    print("=" * 60)
    
    from src.services.language_service import get_system_prompt
    
    patient_context = {
        "age": 25,
        "symptoms": "fever, headache",
        "duration": "2 days"
    }
    
    for lang in [Language.ENGLISH, Language.HINDI, Language.MARATHI, Language.HINGLISH]:
        prompt = get_system_prompt(lang, patient_context)
        print(f"\n[{lang}] System Prompt (first 200 chars):")
        print(prompt[:200] + "...")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("MULTI-LANGUAGE SUPPORT TEST SUITE")
    print("=" * 60 + "\n")
    
    test_language_detection()
    test_templates()
    test_medicine_normalization()
    test_symptom_translation()
    test_system_prompt()
    
    print("=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)
