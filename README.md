# 💊 MediSync - Agentic AI Pharmacy Assistant

**Multi-Agent Conversational System for Pharmacy Automation**

Complete agentic AI system with voice I/O, symptom-based recommendations, prescription validation, and real-time observability. Built for HackFusion 2026.

---

## 🎯 Project Status

**88% Complete • Demo Ready** ✅

- ✅ **Phase 1:** Core Agents (100%)
- ✅ **Phase 2:** Advanced Features (100%)
- ⏳ **Phase 3:** Frontend + Integration (67% - 4/6 tasks)
- ⏳ **Phase 4:** Demo Preparation (0%)

**15/17 tasks complete** • **1-2 days to full completion**

---

## ✨ Key Features

### 🤖 Multi-Agent System
- **6 Specialized Agents:** FrontDesk, Vision, MedicalValidation, Inventory, Fulfillment, ProactiveIntelligence
- **LangGraph Orchestration:** Complete agent pipeline with state management
- **Langfuse Tracing:** Full observability with decision summaries and tool calls

### 💬 Conversational Interface
- **Natural Language:** Symptom-based medicine recommendations
- **Intent Classification:** Automatic routing to appropriate agents
- **Session Management:** Persistent conversation history
- **Patient Context:** Age, allergies, duration extraction

### 🎤 Voice Input/Output
- **Push-to-Talk:** Hold mic button to record audio
- **Whisper Transcription:** Fast, accurate speech-to-text
- **Browser SpeechSynthesis:** Text-to-speech for AI responses
- **Multi-Language:** English, Hindi, auto-detect

### 📊 Agent Timeline
- **Real-Time Visualization:** See agents process requests live
- **Expandable Reasoning:** Click to view agent decision traces
- **Confidence Scores:** Trust indicators for each agent
- **Processing Times:** Performance monitoring

### ⚕️ Medical Validation
- **Safety Engine:** Drug interactions, age checks, contraindications
- **Prescription Validation:** OCR extraction with compliance checks
- **Two Modes:** OTC Summary vs Prescription Validation
- **Never Forges Data:** No hallucinated doctor info or dosages

### 📦 Smart Inventory
- **Real-Time Stock:** 77 medicines with live availability
- **Generic Alternatives:** Suggest alternatives when out of stock
- **Prescription Enforcement:** Blocks OTC sale of prescription meds
- **146 Symptom Mappings:** Comprehensive symptom→medicine database

### 🔗 Webhook Integration
- **Order Fulfillment:** Triggers webhook on order creation
- **Real-World Actions:** Demonstrates production-ready integration
- **Tool Call Logging:** Complete audit trail

### 🔮 Proactive Intelligence
- **Refill Prediction:** Analyzes purchase history
- **Consumption Estimation:** Predicts next refill date
- **Async Operations:** Non-blocking background processing

---

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- Node.js 18+
- Git

### 1. Clone & Setup Backend

```bash
# Clone repository
git clone <repo-url>
cd MediSync/backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Add your GEMINI_API_KEY to .env

# Initialize database (77 medicines, 146 symptom mappings)
python scripts/seed_database.py

# Start backend server
bash start_server.sh
# Or: uvicorn main:app --reload
# Running on http://localhost:8000
```

### 2. Setup Frontend

```bash
# New terminal
cd MediSync/frontend

# Install dependencies
npm install

# Start development server
npm run dev
# Running on http://localhost:5173
```

### 3. Try It Out!

**Kiosk Mode (Recommended):**
- Visit: http://localhost:5173/kiosk
- Type: "I have a headache"
- Watch the agent timeline process your request
- Try voice: Hold mic button and speak

**Prescription Upload:**
- Visit: http://localhost:5173/capture
- Upload a prescription image
- See OCR extraction and validation

**Dashboard:**
- Visit: http://localhost:5173/dashboard
- View system analytics (coming soon)

---
## 📚 Documentation

### 🔒 Critical Files (Start Here)

| Document | Purpose | Priority |
|----------|---------|----------|
| [HACKFUSION-FINAL-PLAN.md](HACKFUSION-FINAL-PLAN.md) | Master hackathon plan & roadmap | **P0** |
| [CONTINUE-DEVELOPMENT.md](CONTINUE-DEVELOPMENT.md) | Development workflow (v3.0 Hackathon Edition) | **P0** |
| [HACKFUSION-RESOURCES-MAPPING.md](HACKFUSION-RESOURCES-MAPPING.md) | Agent/skill mapping for tasks | **P0** |
| [CURRENT-STATUS.md](CURRENT-STATUS.md) | Latest status (47% complete) | **P0** |
| [CRITICAL-FILES.md](CRITICAL-FILES.md) | Protected files list | **P0** |

### 📊 Reference Documentation

| Document | Purpose |
|----------|---------|
| [PROJECT-PROGRESS.md](PROJECT-PROGRESS.md) | Detailed progress tracking |
| [OFFLINE-ARCHITECTURE.md](OFFLINE-ARCHITECTURE.md) | Offline-first architecture |
| [PHASE-5-API-IMPLEMENTATION.md](PHASE-5-API-IMPLEMENTATION.md) | API endpoint documentation |
| [CONCURRENCY-TEST-RESULTS.md](CONCURRENCY-TEST-RESULTS.md) | Performance validation |
| [INSTALL.md](INSTALL.md) | Installation guide |

**Note:** See [CRITICAL-FILES.md](CRITICAL-FILES.md) for complete file protection rules

---

## 🏗️ Architecture

### Multi-Agent Pipeline

```
User Input (Voice/Text/Image)
         ↓
[1] Front Desk Agent (Intent Classification)
         ↓
[2] Vision Agent (OCR + Validation)
         ↓
[3] Medical Validation Agent (Safety + Compliance)
         ↓
[4] Inventory Agent (Stock + Alternatives)
         ↓
[5] Fulfillment Agent (Order Creation)
         ↓
[6] Notification Agent (WhatsApp + Audit)
         ↓
[7] Proactive Agent (Refills + Reminders)
         ↓
[8] Observability Layer (Dashboard + Trace)
```

### Tech Stack

**Backend:**
- FastAPI - High-performance async API
- LangGraph - Multi-agent orchestration
- Gemini 2.5 Flash - LLM reasoning
- SQLAlchemy - Database ORM
- OpenCV - Image preprocessing
- Langfuse - Observability

**Frontend:**
- React 19 + Vite - Modern UI
- Tailwind CSS v4 - Styling
- React Router - Navigation
- React Query - Server state
- Zustand - Client state

**Database:**
- SQLite (development)
- Supabase PostgreSQL (production)

---

## 📁 Project Structure

```
MediSync/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── src/
│   │   ├── agents.py           # Agent definitions
│   │   ├── graph.py            # LangGraph orchestration
│   │   ├── models.py           # Database models
│   │   ├── services.py         # LLM services
│   │   └── database.py         # Database operations
│   ├── utils/
│   │   ├── image_processing.py # Computer vision
│   │   └── tracing.py          # Observability
│   └── tests/                  # Test suite
├── frontend/
│   └── src/
│       ├── App.jsx             # Main component
│       ├── components/         # Reusable components
│       └── pages/              # Page components
└── .agent/                     # Agent definitions & skills
```

---

## 🔧 Development

### Backend

```bash
cd backend

# Run server
python main.py

# Run tests
pytest

# Seed database
python scripts/seed_database.py

# Clean project (remove cache, temp files)
python scripts/cleanup_project.py --dry-run  # Preview
python scripts/cleanup_project.py            # Execute

# Check health
curl http://localhost:8000/health
```

### Frontend

```bash
cd frontend

# Development server
npm run dev

# Build for production
npm run build

# Lint
npm run lint
```

---

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest tests/

# Frontend tests (when added)
cd frontend
npm test
```

---

## 📊 API Endpoints

### Health Check
```bash
GET /health
Response: {"status": "ok", "database": "SQLite"}
```

### Chat (Main Endpoint)
```bash
POST /chat
Body: {
  "user_id": "user123",
  "message": "I need paracetamol 500mg"
}
Response: {
  "decision": "approved",
  "safety_issues": [],
  "order_id": "ORD-00001",
  "order_status": "fulfilled"
}
```

---

## 🗄️ Database

### Current: SQLite
- File-based, local development
- Fast, zero configuration
- Perfect for testing

### Production: Supabase
- PostgreSQL with real-time features
- Auto-scaling, managed backups
- See [SUPABASE-MIGRATION.md](backend/SUPABASE-MIGRATION.md)

### Tables
- `medicines` - Product catalog
- `orders` - Customer orders
- `order_items` - Order line items
- `audit_logs` - Agent decision trail
- `patients` - Customer information
- `refill_predictions` - Proactive intelligence

---

## 🔐 Environment Variables

Copy `backend/.env.example` to `backend/.env`:

```env
# Required
GEMINI_API_KEY=your_key_here

# Optional (for observability)
LANGFUSE_SECRET_KEY=your_key_here
LANGFUSE_PUBLIC_KEY=your_key_here

# Database (auto-configured)
DATABASE_URL=sqlite:///./hackfusion.db
```

---

## 📈 Project Status

**Overall: 88% Complete (15/17 tasks)** • **Demo Ready** ✅

| Phase | Status | Progress | Tasks |
|-------|--------|----------|-------|
| Phase 1: Core Agents | ✅ Complete | 100% | 7/7 |
| Phase 2: Advanced Features | ✅ Complete | 100% | 4/4 |
| Phase 3: Frontend + Integration | ⏳ In Progress | 67% | 4/6 |
| Phase 4: Demo Preparation | ⏳ Pending | 0% | 0/3 |

**Current Task:** Task 3.5 - Homepage Update

### What's Working:
- ✅ 6 AI Agents (FrontDesk, Vision, MedicalValidation, Inventory, Fulfillment, ProactiveIntelligence)
- ✅ Conversational UI with voice input/output
- ✅ Agent timeline with real-time visualization
- ✅ Symptom-based medicine recommendations
- ✅ Prescription upload with OCR
- ✅ Langfuse observability integration
- ✅ Webhook trigger for order fulfillment
- ✅ 77 medicines, 146 symptom mappings

### Remaining Work:
- ⏳ Task 3.5: Homepage update (3 hours) - IN PROGRESS
- ⏳ Task 3.6: End-to-end testing (4 hours)
- ⏳ Phase 4: Demo preparation (1 day)

**Estimated Time to Completion:** 1-2 days

---

## 🎯 Key Features

- ✅ Multi-agent orchestration with LangGraph
- ✅ Voice input with Whisper transcription
- ✅ Voice output with Browser SpeechSynthesis
- ✅ Agent timeline with expandable reasoning traces
- ✅ Langfuse tracing for complete observability
- ✅ Symptom-based medicine recommendations
- ✅ Prescription validation with OCR
- ✅ Real-time inventory management
- ✅ Webhook integration for order fulfillment
- ✅ Proactive refill prediction

- ✅ SQLite database with Supabase migration path
- ✅ Complete audit trail for all decisions
- ✅ Type-safe with Pydantic models
- ✅ Observability with Langfuse
- 🔄 Vision Agent (in progress)
- ⏳ WhatsApp notifications (Phase 4)
- ⏳ Real-time dashboard (Phase 6)
- ⏳ Voice input (Phase 7)

---

## 🤝 Contributing

This is a HackFusion project. Follow the development plan in [HACKFUSION-PLAN.md](HACKFUSION-PLAN.md).

---

## 📄 License

[Add your license here]

---

## 🙏 Acknowledgments

- Built with guidance from `.agent` folder best practices
- Uses LangGraph for multi-agent orchestration
- Powered by Gemini 2.5 Flash

---

**Status:** ✅ Phase 1 - 50% Complete  
**Next:** Task 1.3 - Build Vision Agent
