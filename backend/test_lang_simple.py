"""
Simple Multi-Language Test (No Dependencies)
"""

import re

def detect_language(text: str) -> str:
    """Detect language from user input."""
    if not text or not text.strip():
        return "en"
    
    text_lower = text.lower().strip()
    
    # Devanagari script detection
    devanagari_pattern = re.compile(r'[\u0900-\u097F]')
    has_devanagari = bool(devanagari_pattern.search(text))
    
    # Marathi-specific words
    marathi_keywords = ['मला', 'आहे', 'काय', 'कसे', 'तुम्ही']
    
    # Hindi-specific words
    hindi_keywords = ['मुझे', 'है', 'क्या', 'कैसे', 'आप', 'हूँ', 'हैं']
    
    # Hinglish patterns
    hinglish_patterns = ['mujhe', 'hai', 'kya', 'kaise', 'aap', 'bukhar', 'dard']
    
    # Check for Marathi
    if has_devanagari and any(word in text for word in marathi_keywords):
        return "mr"
    
    # Check for Hindi
    if has_devanagari and any(word in text for word in hindi_keywords):
        return "hi"
    
    # Check for Hinglish
    if any(pattern in text_lower for pattern in hinglish_patterns):
        return "mixed"
    
    # Check for pure Devanagari
    if has_devanagari:
        return "hi"
    
    return "en"


# Test cases
test_cases = [
    ("I need paracetamol", "en"),
    ("मुझे बुखार है", "hi"),
    ("मला ताप आहे", "mr"),
    ("mujhe sir dard hai", "mixed"),
    ("I have bukhar", "mixed"),
    ("क्या आपके पास पैरासिटामोल है?", "hi"),
    ("तुम्हाला कोणती औषधे हवी आहेत?", "mr"),
    ("Hello, I need medicine", "en"),
    ("aap kaise hain", "mixed"),
]

print("=" * 60)
print("LANGUAGE DETECTION TEST")
print("=" * 60)

passed = 0
failed = 0

for text, expected in test_cases:
    detected = detect_language(text)
    status = "✅" if detected == expected else "❌"
    if detected == expected:
        passed += 1
    else:
        failed += 1
    print(f"{status} '{text}' -> {detected} (expected: {expected})")

print("\n" + "=" * 60)
print(f"RESULTS: {passed} passed, {failed} failed")
print("=" * 60)
