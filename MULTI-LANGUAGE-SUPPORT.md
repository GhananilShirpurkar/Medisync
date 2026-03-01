# Multi-Language Support Implementation

## Overview

MediSync now supports **4 languages**:
- **English** (en)
- **Hindi** (hi) - Devanagari script
- **Marathi** (mr) - Devanagari script  
- **Hinglish** (mixed) - Hindi words in Roman script

## Features Implemented

### 1. Language Detection
Automatic language detection from user input using:
- Devanagari script detection (Unicode range U+0900-U+097F)
- Language-specific keyword matching
- Hinglish pattern recognition

**Location**: `backend/src/services/language_service.py`

```python
from src.services.language_service import detect_language

language = detect_language("मुझे बुखार है")  # Returns "hi"
language = detect_language("mujhe bukhar hai")  # Returns "mixed"
language = detect_language("I have fever")  # Returns "en"
```

### 2. Localized Templates
Pre-defined templates for common messages in all 4 languages:
- Greetings
- Symptom questions
- Age/duration questions
- Order confirmations
- Payment messages
- Safety warnings
- Emergency alerts

**Usage**:
```python
from src.services.language_service import get_template

msg = get_template("greeting", "hi")
# Returns: "नमस्ते! मैं आपका MediSync फार्मासिस्ट हूँ..."

msg = get_template("order_confirmed", "mr", order_id="ORD123")
# Returns: "तुमची ऑर्डर कन्फर्म झाली आहे। ऑर्डर ID: ORD123"
```

### 3. Medicine Name Normalization
Handles medicine names across languages:
- Hindi/Marathi names → English
- Brand names → Generic names
- Common abbreviations → Full names

**Examples**:
- "पैरासिटामोल" → "Paracetamol"
- "para" → "Paracetamol"
- "crocin" → "Paracetamol"
- "brufen" → "Ibuprofen"

### 4. Symptom Translation
Translates symptoms from Hindi/Marathi/Hinglish to English:
- "bukhar" / "बुखार" → "fever"
- "sir dard" / "सिर दर्द" → "headache"
- "pet dard" / "पेट दर्द" → "stomach ache"
- "khansi" / "खांसी" → "cough"

### 5. Language-Aware System Prompts
LLM system prompts adapt to user's language:
- English users get English-only responses
- Hindi users get Hindi (Devanagari) responses
- Marathi users get Marathi responses
- Hinglish users get Hinglish (Roman script) responses

**Location**: `backend/src/services/language_service.py::get_system_prompt()`

## Integration Points

### 1. Conversation API
**File**: `backend/src/routes/conversation.py`

Language is detected automatically when user sends a message:
```python
detected_language = detect_language(request.message)
```

The detected language is passed to:
- Front desk agent for clarifying questions
- LLM for response generation
- Templates for system messages

### 2. WhatsApp Pipeline
**File**: `backend/src/whatsapp_pipeline.py`

WhatsApp messages are processed with language detection:
```python
detected_language = detect_language(text)
state.language = detected_language
```

Welcome messages use localized templates:
```python
welcome_msg = get_template("greeting", detected_language)
```

### 3. Front Desk Agent
**File**: `backend/src/agents/front_desk_agent.py`

- Accepts `language` parameter in methods
- Uses language-aware system prompts
- Normalizes medicine names across languages
- Translates symptoms to English for processing

### 4. Vision Agent
**File**: `backend/src/vision_agent.py`

Detects language from prescription images and sets state:
```python
state.language = detected_lang
```

### 5. State Management
**File**: `backend/src/state.py`

PharmacyState includes language field:
```python
language: Optional[str] = "en"  # en | hi | mr | mixed
```

## Testing

### Run Language Detection Tests
```bash
cd backend
python test_lang_simple.py
```

Expected output:
```
✅ 'I need paracetamol' -> en (expected: en)
✅ 'मुझे बुखार है' -> hi (expected: hi)
✅ 'मला ताप आहे' -> mr (expected: mr)
✅ 'mujhe sir dard hai' -> mixed (expected: mixed)
```

### Manual Testing

#### English
```
User: "I need paracetamol"
Bot: "I found Paracetamol 500mg in stock..."
```

#### Hindi
```
User: "मुझे बुखार है"
Bot: "आपको बुखार कितने दिन से है?"
```

#### Marathi
```
User: "मला ताप आहे"
Bot: "तुम्हाला ताप किती दिवसांपासून आहे?"
```

#### Hinglish
```
User: "mujhe sir dard hai"
Bot: "Aapko sir dard kitne din se hai?"
```

## API Examples

### Create Session and Send Message
```bash
# Create session
curl -X POST http://localhost:8000/api/conversation/create \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user"}'

# Send Hindi message
curl -X POST http://localhost:8000/api/conversation \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "SESSION_ID",
    "message": "मुझे बुखार है"
  }'
```

### WhatsApp Integration
WhatsApp messages automatically detect language:
```
User sends: "mujhe bukhar hai"
System detects: Hinglish (mixed)
Bot responds: "Aapko bukhar kitne din se hai?"
```

## Configuration

No configuration needed! Language detection is automatic.

To customize templates, edit:
```python
# backend/src/services/language_service.py
TEMPLATES = {
    "greeting": {
        "en": "Hello! I'm your MediSync pharmacist...",
        "hi": "नमस्ते! मैं आपका MediSync फार्मासिस्ट हूँ...",
        "mr": "नमस्कार! मी तुमचा MediSync फार्मासिस्ट आहे...",
        "mixed": "Hello! Main aapka MediSync pharmacist hoon..."
    }
}
```

## Error Handling

The system gracefully handles:
- Unknown languages → defaults to English
- Mixed language input → detects dominant language
- Missing translations → falls back to English
- Invalid Unicode → treats as English

## Performance

- Language detection: < 1ms (regex-based)
- No external API calls
- No additional latency
- Works offline

## Future Enhancements

Potential additions:
1. **More languages**: Tamil, Telugu, Bengali, Gujarati
2. **Voice input**: Language detection from audio
3. **Translation API**: For complex medical terms
4. **User preference**: Remember user's preferred language
5. **Code-switching**: Better handling of mixed language sentences

## Troubleshooting

### Issue: Bot responds in wrong language
**Solution**: Check if user message has clear language markers. Add more keywords to detection patterns.

### Issue: Medicine names not recognized
**Solution**: Add aliases to `MEDICINE_ALIASES` dict in `language_service.py`

### Issue: Symptoms not translated
**Solution**: Add translations to `SYMPTOM_TRANSLATIONS` dict

## Files Modified

1. ✅ `backend/src/services/language_service.py` - NEW (core language service)
2. ✅ `backend/src/agents/front_desk_agent.py` - Updated (language support)
3. ✅ `backend/src/routes/conversation.py` - Updated (language detection)
4. ✅ `backend/src/whatsapp_pipeline.py` - Updated (WhatsApp language support)
5. ✅ `backend/src/vision_agent.py` - Updated (language logging)
6. ✅ `backend/src/state.py` - Already had language field
7. ✅ `backend/test_lang_simple.py` - NEW (test suite)

## Summary

Multi-language support is now fully integrated across:
- ✅ Conversation API
- ✅ WhatsApp integration
- ✅ Front desk agent
- ✅ Vision agent
- ✅ State management
- ✅ Template system
- ✅ Medicine normalization
- ✅ Symptom translation

All changes are backward compatible and require no configuration.
