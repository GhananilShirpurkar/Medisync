# MediSync Codebase Structure

## Project Overview
MediSync is an AI-powered pharmacy assistant with semantic intent classification, operator console, and multi-agent architecture.

---

## 📁 Root Directory

```
MediSync/
├── backend/                          # Python FastAPI backend
├── frontend/                         # React + Vite frontend
├── .agent/                          # Agent configuration and skills
├── .kiro/                           # Kiro IDE settings
├── .venv/                           # Python virtual environment
├── *.md                             # Documentation files
└── README.md                        # Project overview
```

---

## 🔧 Backend Structure (`backend/`)

```
backend/
│
├── main.py                          # FastAPI application entry point, CORS setup
├── start_server.sh                  # Script to start uvicorn server
├── requirements.txt                 # Python dependencies
├── hackfusion.db                    # SQLite database (medicines, orders, sessions)
├── .env                             # Environment variables (API keys, config)
│
├── src/                             # Source code
│   ├── __init__.py
│   ├── database.py                  # Database operations (CRUD, fuzzy matching)
│   ├── db_config.py                 # Database configuration and context manager
│   ├── models.py                    # SQLAlchemy models (Medicine, Order, Session)
│   ├── state.py                     # Conversation state management
│   ├── errors.py                    # Custom error classes
│   ├── graph.py                     # LangGraph workflow definition
│   ├── vision_agent.py              # OCR and prescription image processing
│   ├── telegram_pipeline.py         # Telegram bot integration
│   │
│   ├── agents/                      # AI agents for different tasks
│   │   ├── __init__.py
│   │   ├── front_desk_agent.py      # Intent classification, patient intake
│   │   ├── medical_validator_agent.py # Medical validation and safety checks
│   │   ├── inventory_and_rules_agent.py # Stock checking, business rules
│   │   ├── fulfillment_agent.py     # Order processing and fulfillment
│   │   ├── notification_agent.py    # Notification handling
│   │   ├── proactive_intelligence_agent.py # Refill reminders, analytics
│   │   ├── semantic_intent_classifier.py # Semantic intent classification
│   │   └── severity_scorer.py       # Symptom severity assessment
│   │
│   ├── services/                    # Business logic services
│   │   ├── __init__.py
│   │   ├── conversation_service.py  # Conversation management (sessions, messages)
│   │   ├── intent_classifier.py     # Semantic intent classification (sentence-transformers)
│   │   ├── inventory_service.py     # Inventory management
│   │   ├── llm_service.py          # LLM API calls (Gemini)
│   │   ├── observability_service.py # Logging and monitoring (Langfuse)
│   │   ├── ocr_service.py          # OCR processing (EasyOCR)
│   │   ├── order_service.py        # Order management
│   │   ├── prescription_service.py  # Prescription validation
│   │   ├── speech_service.py       # Speech-to-text (Whisper)
│   │   └── telegram_service.py     # Telegram API integration
│   │
│   ├── routes/                      # API endpoints
│   │   ├── __init__.py
│   │   └── conversation.py         # Conversation API (POST /conversation, /voice)
│   │
│   └── events/                      # Event-driven architecture
│       ├── __init__.py
│       ├── event_bus.py            # Event bus for agent communication
│       ├── event_types.py          # Event type definitions
│       └── handlers/               # Event handlers
│           ├── __init__.py
│           └── notification_handler.py # Notification event handler
│
├── data/                            # Data files
│   ├── medicines_catalog.csv       # Medicine database (name, price, stock, indications)
│   ├── symptom_mappings.csv        # Symptom → Medicine mappings
│   ├── consumer_order_history.csv  # Order history data
│   └── product_export.csv          # Product export data
│
├── scripts/                         # Utility scripts
│   ├── seed_database.py            # Seed database with initial data
│   ├── seed_demo_data.py           # Seed demo data
│   ├── seed_final_data.py          # Seed final production data
│   ├── seed_indian_medicines.py    # Seed Indian medicine catalog
│   ├── migrate_schema.py           # Database schema migration
│   ├── migrate_to_postgres.py      # Migrate SQLite to PostgreSQL
│   ├── migrate_to_supabase.py      # Migrate to Supabase
│   └── cleanup_project.py          # Cleanup temporary files
│
├── tests/                           # Test suite
│   ├── conftest.py                 # Pytest configuration
│   ├── test_conversation_api.py    # Conversation API tests
│   ├── test_fulfillment_agent.py   # Fulfillment agent tests
│   ├── test_inventory_agent.py     # Inventory agent tests
│   ├── test_medical_validator.py   # Medical validator tests
│   ├── test_notification_agent.py  # Notification agent tests
│   ├── test_ocr_service.py         # OCR service tests
│   ├── test_voice_input.py         # Voice input tests
│   ├── test_workflow_integration.py # Workflow integration tests
│   └── ... (more test files)
│
├── utils/                           # Utility functions
│   ├── __init__.py
│   ├── image_processing.py         # Image processing utilities
│   ├── resource_manager.py         # Resource management
│   ├── tracing.py                  # Tracing and logging
│   └── validation_rules.py         # Validation rules
│
├── notifications/                   # Notification services
│   ├── __init__.py
│   └── telegram_service.py         # Telegram notification service
│
├── logs/                            # Log files
│   └── notifications_*.jsonl       # Notification logs (JSONL format)
│
└── test_*.py                        # Test scripts (semantic classifier, conversation flow)
```

---

## 🎨 Frontend Structure (`frontend/`)

```
frontend/
│
├── index.html                       # HTML entry point
├── package.json                     # NPM dependencies
├── package-lock.json                # NPM lock file
├── vite.config.js                   # Vite configuration
├── tailwind.config.js               # Tailwind CSS configuration
├── postcss.config.js                # PostCSS configuration
├── eslint.config.js                 # ESLint configuration
├── .env                             # Environment variables (API URL)
│
├── public/                          # Static assets
│
├── src/                             # Source code
│   ├── main.jsx                     # React entry point
│   ├── App.jsx                      # Main app component with routing
│   ├── index.css                    # Global styles (Tailwind imports)
│   │
│   ├── pages/                       # Page components
│   │   ├── Landing.jsx              # Landing page (home)
│   │   ├── Kiosk.jsx                # Operator console (3-column layout)
│   │   └── OrderSummary.jsx         # Order summary page
│   │
│   ├── components/                  # Reusable components
│   │   ├── AppLayout.jsx            # Layout wrapper for 3-column design
│   │   ├── Sidebar.jsx              # Left sidebar navigation
│   │   ├── OrderPanel.jsx           # Center panel (order details, interaction log)
│   │   ├── AgentActivityPanel.jsx   # Right panel (agent timeline)
│   │   ├── AgentTimeline.jsx        # Agent activity timeline (original)
│   │   ├── ConversationalInterface.jsx # Chat interface (original, preserved)
│   │   ├── CameraCapture.jsx        # Camera/prescription upload
│   │   ├── VoiceInputButton.jsx     # Voice input button
│   │   └── VoiceToggle.jsx          # Voice output toggle
│   │
│   ├── services/                    # API services
│   │   └── api.js                   # API client (fetch wrapper)
│   │
│   ├── hooks/                       # Custom React hooks
│   │   └── useApi.js                # API hook
│   │
│   └── assets/                      # Assets (images, icons)
│
└── dist/                            # Build output (generated)
```

---

## 🤖 Agent Configuration (`.agent/`)

```
.agent/
│
├── ARCHITECTURE.md                  # System architecture documentation
├── mcp_config.json                  # MCP (Model Context Protocol) configuration
│
├── agents/                          # Agent definitions
│   ├── backend-specialist.md        # Backend development agent
│   ├── frontend-specialist.md       # Frontend development agent
│   ├── database-architect.md        # Database design agent
│   ├── debugger.md                  # Debugging agent
│   ├── devops-engineer.md          # DevOps agent
│   ├── documentation-writer.md     # Documentation agent
│   ├── explorer-agent.md           # Code exploration agent
│   ├── orchestrator.md             # Multi-agent orchestrator
│   ├── performance-optimizer.md    # Performance optimization agent
│   ├── security-auditor.md         # Security audit agent
│   └── ... (more agent definitions)
│
├── skills/                          # Agent skills and capabilities
│   ├── api-patterns/               # API design patterns
│   ├── architecture/               # Architecture patterns
│   ├── clean-code/                 # Clean code principles
│   ├── database-design/            # Database design patterns
│   ├── frontend-design/            # Frontend design patterns
│   ├── nextjs-react-expert/        # Next.js/React expertise
│   ├── testing-patterns/           # Testing patterns
│   └── ... (more skills)
│
├── workflows/                       # Workflow definitions
│   ├── brainstorm.md               # Brainstorming workflow
│   ├── create.md                   # Creation workflow
│   ├── debug.md                    # Debugging workflow
│   ├── deploy.md                   # Deployment workflow
│   ├── enhance.md                  # Enhancement workflow
│   ├── plan.md                     # Planning workflow
│   └── ... (more workflows)
│
├── scripts/                         # Automation scripts
│   ├── auto_preview.py             # Auto preview script
│   ├── checklist.py                # Checklist generator
│   ├── session_manager.py          # Session management
│   └── verify_all.py               # Verification script
│
└── .shared/                         # Shared resources
    └── ui-ux-pro-max/              # UI/UX design system
        ├── data/                    # Design data (colors, icons, etc.)
        └── scripts/                 # Design scripts
```

---

## 📚 Documentation Files (Root)

```
Root Documentation:
│
├── README.md                        # Project overview and setup
├── PROJECT-STATUS.md                # Current project status
├── CURRENT-STATUS-SUMMARY.md        # Status summary
├── DEMO-READY-SUMMARY.md            # Demo readiness checklist
├── FINAL-STATUS.md                  # Final implementation status
│
├── ENHANCEMENTS-PLAN.md             # Enhancement roadmap
├── ALL-ENHANCEMENTS-COMPLETE.md     # Completed enhancements
├── MEDISYNC-FINAL-PLAN.md           # Final project plan
│
├── SEMANTIC-INTENT-CLASSIFIER.md    # Semantic classifier documentation
├── SEMANTIC-CLASSIFICATION-COMPLETE.md # Implementation complete
├── SHOULD-I-TAKE-PATTERN-FIX.md     # "Should I take" pattern fix
├── MEDICINE-NAME-QUERY-FIX.md       # Medicine name query fix
├── MEDICINE-INFO-QUERY-FIX.md       # Medicine info query fix
│
├── FUZZY-MATCHING-IMPLEMENTED.md    # Fuzzy matching implementation
├── SEVERITY-SCORING-IMPLEMENTED.md  # Severity scoring implementation
├── TELEGRAM-NOTIFICATIONS-IMPLEMENTED.md # Telegram notifications
├── HINDI-SUPPORT-ADDED.md           # Hindi language support
│
├── FRONTEND-REDESIGN-COMPLETE.md    # Frontend redesign documentation
├── OPERATOR-CONSOLE-REFACTOR.md     # Operator console refactor
├── UI-POLISH-PLAN.md                # UI polish plan
│
├── SUPABASE-SETUP.md                # Supabase setup guide
├── TELEGRAM-BOT-GUIDE.md            # Telegram bot guide
├── VOICE-FEATURES-GUIDE.md          # Voice features guide
├── TESTING-RESULTS.md               # Testing results
├── DEMO-GUIDE.md                    # Demo guide
│
└── HACKFUSION-RESOURCES-MAPPING.md  # Resource mapping
```

---

## 🔑 Key Files Explained

### Backend Core Files

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app initialization, CORS, route registration |
| `database.py` | Database CRUD operations, fuzzy matching (Levenshtein) |
| `models.py` | SQLAlchemy ORM models (Medicine, Order, Session, etc.) |
| `state.py` | Conversation state management |
| `graph.py` | LangGraph workflow for agent orchestration |

### Frontend Core Files

| File | Purpose |
|------|---------|
| `App.jsx` | React Router setup, main app structure |
| `Kiosk.jsx` | Operator console (3-column layout) |
| `OrderPanel.jsx` | Center panel with order details and interaction log |
| `AgentActivityPanel.jsx` | Right panel with agent activity timeline |
| `Sidebar.jsx` | Left navigation sidebar |

### Agent Files

| File | Purpose |
|------|---------|
| `front_desk_agent.py` | Intent classification, patient intake, routing |
| `medical_validator_agent.py` | Medical validation, safety checks |
| `inventory_and_rules_agent.py` | Stock checking, business rules |
| `fulfillment_agent.py` | Order processing and fulfillment |
| `semantic_intent_classifier.py` | Semantic intent classification |
| `severity_scorer.py` | Symptom severity assessment (1-10 scale) |

### Service Files

| File | Purpose |
|------|---------|
| `intent_classifier.py` | Semantic intent classification (sentence-transformers) |
| `conversation_service.py` | Session and message management |
| `llm_service.py` | LLM API calls (Google Gemini) |
| `speech_service.py` | Speech-to-text (Faster Whisper) |
| `ocr_service.py` | OCR processing (EasyOCR) |
| `telegram_service.py` | Telegram bot integration |

---

## 🎯 Key Features by File

### Semantic Intent Classification
- `backend/src/services/intent_classifier.py` - Core classifier
- `backend/src/agents/front_desk_agent.py` - Intent routing
- Uses `all-MiniLM-L6-v2` model (80MB, CPU-optimized)

### Fuzzy Medicine Matching
- `backend/src/database.py` - `get_medicine()` with Levenshtein distance
- 70% similarity threshold
- Typo detection and suggestions

### Operator Console
- `frontend/src/pages/Kiosk.jsx` - Main page
- `frontend/src/components/Sidebar.jsx` - Navigation
- `frontend/src/components/OrderPanel.jsx` - Order management
- `frontend/src/components/AgentActivityPanel.jsx` - Agent monitoring

### Voice Features
- `backend/src/services/speech_service.py` - Speech-to-text
- `frontend/src/components/VoiceInputButton.jsx` - Voice input
- `frontend/src/components/VoiceToggle.jsx` - Voice output

### Prescription Processing
- `backend/src/vision_agent.py` - OCR and validation
- `backend/src/services/ocr_service.py` - EasyOCR integration
- `frontend/src/components/CameraCapture.jsx` - Image capture

---

## 📊 Data Flow

```
User Input (Frontend)
    ↓
API Request (POST /api/conversation)
    ↓
Front Desk Agent (Intent Classification)
    ↓
Semantic Intent Classifier (sentence-transformers)
    ↓
Route to Appropriate Agent
    ↓
Medical Validator / Inventory / Fulfillment
    ↓
Database Query (SQLite)
    ↓
Response with Recommendations
    ↓
Frontend Display (OrderPanel + AgentActivityPanel)
```

---

## 🧪 Test Files

| File | Purpose |
|------|---------|
| `test_semantic_classifier.py` | Test semantic intent classification |
| `test_conversation_flow.py` | Test full conversation flow |
| `test_all_scenarios.py` | Comprehensive test suite (12 tests) |
| `test_medicine_info.py` | Test medicine information queries |
| `test_diclofenac.py` | Test specific medicine queries |
| `test_should_take.py` | Test "should I take" pattern |

---

## 🚀 Quick Start Files

| File | Purpose |
|------|---------|
| `backend/start_server.sh` | Start backend server |
| `frontend/package.json` | Frontend dependencies and scripts |
| `backend/requirements.txt` | Python dependencies |
| `.env` files | Environment configuration |

---

This structure represents a production-ready AI-powered pharmacy assistant with:
- ✅ Semantic intent classification
- ✅ Multi-agent architecture
- ✅ Operator console
- ✅ Voice features
- ✅ Prescription processing
- ✅ Telegram notifications
- ✅ Bilingual support (English + Hindi)
