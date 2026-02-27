
# DEMO SCENARIOS FOR MEDISYNC

## Scenario 1: Symptom-Based Query (Primary Demo)
**User:** "I have a headache and fever"
**Expected Flow:**
1. FrontDesk Agent classifies intent as "symptom"
2. MedicalValidation Agent recommends Paracetamol
3. Inventory Agent confirms stock available
4. Timeline shows all 3 agents processing
5. Recommendations display with price and stock

**Talking Points:**
- Natural language understanding
- Symptom-based recommendations
- Real-time agent pipeline
- Stock verification
- Safety checks

---

## Scenario 2: Known Medicine Query
**User:** "Do you have paracetamol?"
**Expected Flow:**
1. FrontDesk Agent classifies intent as "known_medicine"
2. Medicine search finds Paracetamol
3. Stock information displayed
4. Price shown
5. Add to cart option

**Talking Points:**
- Direct medicine search
- Inventory integration
- Pricing transparency
- Simple user experience

---

## Scenario 3: Voice Input Demo
**User:** Hold mic button and say "I need aspirin"
**Expected Flow:**
1. Audio recorded
2. Whisper transcribes: "I need aspirin"
3. Transcription displayed with confidence
4. AI processes request
5. Response shown and spoken (if voice enabled)

**Talking Points:**
- Push-to-talk interaction
- Whisper transcription
- Hands-free experience
- Voice output option
- Accessibility feature

---

## Scenario 4: Agent Timeline Deep Dive
**User:** Any query (use Scenario 1)
**Expected Flow:**
1. Timeline appears on right side
2. Show FrontDesk agent reasoning
3. Expand MedicalValidation reasoning
4. Show confidence scores
5. Point out processing times
6. Highlight Langfuse integration

**Talking Points:**
- Complete transparency
- Agent reasoning visible
- Confidence scores
- Performance monitoring
- Observability with Langfuse

---

## Scenario 5: Proactive Refill Prediction (Advanced)
**User:** Demo user "Rajesh Kumar"
**Expected Flow:**
1. Show purchase history (3 orders)
2. Highlight Metformin order (30 days ago)
3. Show refill prediction (tomorrow)
4. Explain consumption estimation (2 tablets/day)
5. Show confidence score (92%)

**Talking Points:**
- Proactive intelligence
- Purchase history analysis
- Consumption estimation
- Predictive analytics
- Customer retention feature

---

## Demo Script (5 minutes)

### 1. Introduction (30 seconds)
- Show homepage
- Highlight 94% complete status
- Review key features
- Click Kiosk Mode

### 2. Conversational Demo (2 minutes)
- Type: "I have a headache"
- Show agent timeline
- Point out 3 agents
- Show recommendations
- Expand reasoning traces

### 3. Voice Demo (1 minute)
- Hold mic button
- Say: "Do you have aspirin?"
- Show transcription
- Show AI response
- Enable voice output

### 4. Agent Timeline (1 minute)
- Expand FrontDesk reasoning
- Show intent classification
- Expand MedicalValidation
- Show recommendation logic
- Point out processing times

### 5. Proactive Intelligence (30 seconds)
- Mention purchase history
- Show refill prediction
- Explain differentiation
- Highlight business value

---

## Backup Scenarios

### If Voice Fails:
- Continue with text input
- Mention voice is optional
- Show other features

### If API Slow:
- Explain LLM processing
- Show agent timeline updating
- Highlight real-time nature

### If Questions About Data:
- 77 medicines in database
- 146 symptom mappings
- Real Indian medicine names
- Production-ready scale

---

## Key Talking Points

### Technical:
- 6 specialized AI agents
- LangGraph orchestration
- Gemini 2.5 Flash reasoning
- Langfuse observability
- Whisper transcription
- Browser SpeechSynthesis

### Business:
- Pharmacy automation
- Customer self-service
- Reduced wait times
- Improved accuracy
- Better customer experience
- Proactive engagement

### Differentiation:
- Multi-agent architecture
- Complete observability
- Voice input/output
- Proactive refill prediction
- Real-time agent timeline
- Production-ready quality

---

## Demo Tips

1. **Start Strong:** Homepage makes great first impression
2. **Show Timeline:** Most impressive visual feature
3. **Use Voice:** Demonstrates technical depth
4. **Expand Reasoning:** Shows transparency
5. **Mention Langfuse:** Observability is critical
6. **Highlight Proactive:** Differentiation feature
7. **Stay Calm:** If issues, pivot to working features
8. **Time Management:** Keep under 5 minutes
9. **Engage Judges:** Ask if they want to see specific features
10. **End Strong:** Summarize key achievements

---

**Status:** Demo scenarios ready
**Confidence:** HIGH
**Estimated Demo Time:** 5 minutes
