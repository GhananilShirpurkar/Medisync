# Multi-Language Support - Quick Start

## 🚀 Ready to Use

Multi-language support is **already integrated** and requires **no setup**.

## Supported Languages

| Language | Code | Example |
|----------|------|---------|
| English | `en` | "I need paracetamol" |
| Hindi | `hi` | "मुझे बुखार है" |
| Marathi | `mr` | "मला ताप आहे" |
| Hinglish | `mixed` | "mujhe bukhar hai" |

## How It Works

1. User sends message in any supported language
2. System automatically detects language
3. Bot responds in the same language
4. Medicine names normalized across languages
5. Symptoms translated for processing

## Test It Now

### Via API
```bash
# Hindi
curl -X POST http://localhost:8000/api/conversation \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "message": "मुझे बुखार है"}'

# Hinglish
curl -X POST http://localhost:8000/api/conversation \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "message": "mujhe sir dard hai"}'

# Marathi
curl -X POST http://localhost:8000/api/conversation \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "message": "मला ताप आहे"}'
```

### Via WhatsApp
Just send a message in any language:
- "मुझे पैरासिटामोल चाहिए"
- "mujhe bukhar hai"
- "I need medicine for headache"

## Run Tests

```bash
cd backend
python test_lang_simple.py
```

Expected: All 9 tests pass ✅

## Examples

### English → English
```
User: "I need paracetamol"
Bot: "I found Paracetamol 500mg. Would you like to add it to your cart?"
```

### Hindi → Hindi
```
User: "मुझे बुखार है"
Bot: "आपको बुखार कितने दिन से है?"
```

### Hinglish → Hinglish
```
User: "mujhe sir dard hai"
Bot: "Aapko sir dard kitne din se hai?"
```

### Marathi → Marathi
```
User: "मला ताप आहे"
Bot: "तुम्हाला ताप किती दिवसांपासून आहे?"
```

## Medicine Names Work Across Languages

All these work:
- "paracetamol" ✅
- "पैरासिटामोल" ✅
- "para" ✅
- "crocin" ✅
- "dolo" ✅

All resolve to: **Paracetamol**

## Symptoms Work Across Languages

All these work:
- "fever" ✅
- "bukhar" ✅
- "बुखार" ✅
- "ताप" ✅

All resolve to: **fever**

## No Configuration Needed

- ✅ Works out of the box
- ✅ No environment variables
- ✅ No database changes
- ✅ No external APIs
- ✅ No performance impact

## Files to Know

| File | Purpose |
|------|---------|
| `backend/src/services/language_service.py` | Core language logic |
| `backend/test_lang_simple.py` | Test suite |
| `MULTI-LANGUAGE-SUPPORT.md` | Full documentation |

## Troubleshooting

### Bot responds in wrong language?
- Check if message has clear language markers
- Try more explicit language (e.g., "मुझे" instead of "mujhe")

### Medicine not recognized?
- Try common name (e.g., "para" instead of "पैरा")
- System normalizes most variations

### Need to add more words?
Edit `backend/src/services/language_service.py`:
- `MEDICINE_ALIASES` - for medicine names
- `SYMPTOM_TRANSLATIONS` - for symptoms
- `TEMPLATES` - for messages

## That's It!

Multi-language support is live. Just use it! 🎉
