"""
FASTAPI ENTRYPOINT
==================
Execution shell around the agentic brain.

Responsibilities:
- Accept HTTP requests
- Initialize shared state
- Invoke LangGraph
- Return clean responses
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.state import PharmacyState
from src.graph import agent_graph
from src.db_config import init_db, get_db_type, get_db_context
from utils.tracing import check_tracing
from src.agents.proactive_intelligence_agent import run_batch_analysis

# Import API routes
from src.routes.prescriptions import router as prescriptions_router
from src.routes.orders import router as orders_router
from src.routes.inventory import router as inventory_router
from src.routes.admin import router as admin_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# APP INIT
# ------------------------------------------------------------------
app = FastAPI(
    title="MediSync Agentic Backend",
    description="AI-powered pharmacy automation system with multi-agent orchestration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize observability (must never crash app)
check_tracing()

# Initialize Prediction Service (Event Listener)
from src.services.prediction_service import prediction_service
logger.info("🔮 Prediction Service Initialized")

# Initialize database
@app.on_event("startup")
def startup_event():
    """Initialize database on startup."""
    init_db()
    logger.info(f"🗄️  Database: {get_db_type()}")
    # Index medicines for semantic search
    from src.database import Database
    from src.services.semantic_search_service import semantic_search_service
    from src.models import Medicine
    
    with get_db_context() as db:
        medicines = db.query(Medicine).all()
        med_dicts = []
        for m in medicines:
            med_dicts.append({
                "name": m.name,
                "description": m.description or "",
                "indication": m.indications or "",
                "category": m.category or ""
            })
        semantic_search_service.index_medicines(med_dicts)
        logger.info(f"🧠 Indexed {len(med_dicts)} medicines for semantic search")

# ------------------------------------------------------------------
# PROACTIVE INTELLIGENCE SCHEDULER
# ------------------------------------------------------------------
_scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def start_proactive_scheduler():
    """Start the proactive refill prediction scheduler."""
    _scheduler.add_job(
        run_batch_analysis,
        'interval',
        seconds=60,
        id='proactive_refill_job',
        replace_existing=True
    )
    _scheduler.start()
    logger.info("✅ Proactive Intelligence Scheduler started — running every 60 seconds")

@app.on_event("shutdown")
async def stop_proactive_scheduler():
    """Gracefully stop the scheduler."""
    _scheduler.shutdown(wait=False)
    logger.info("⏹️  Proactive Intelligence Scheduler stopped")

# ------------------------------------------------------------------
# CORS (Frontend ↔ Backend bridge)
# ------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# INCLUDE API ROUTERS
# ------------------------------------------------------------------
app.include_router(prescriptions_router, prefix="/api/v1")
app.include_router(orders_router, prefix="/api/v1")
app.include_router(inventory_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1/admin")

# Import conversation router
from src.routes.conversation import router as conversation_router
app.include_router(conversation_router, prefix="/api")

# Import prescription router
from src.routes.prescription import router as prescription_router
app.include_router(prescription_router, prefix="/api")

# Import WebSocket trace stream router
from src.routes.stream import router as stream_router
app.include_router(stream_router)  # /ws/* handled internally

# Import notifications router
from src.routes.notifications import router as notifications_router
app.include_router(notifications_router, prefix="/api")

# Import WhatsApp Webhook router
from whatsapp_bot import router as whatsapp_bot_router
app.include_router(whatsapp_bot_router, prefix="/api")

# Import Telegram Webhook router (REPLACED BY WHATSAPP)
# from src.routes.telegram_webhook import router as telegram_webhook_router
# app.include_router(telegram_webhook_router, prefix="/api")

# ------------------------------------------------------------------
# REQUEST / RESPONSE SCHEMAS (Legacy)
# ------------------------------------------------------------------
class ChatRequest(BaseModel):
    user_id: str | None = None
    message: str = Field(..., min_length=1, max_length=1000)


class ChatResponse(BaseModel):
    decision: str | None
    safety_issues: list[str]
    order_id: str | None
    order_status: str | None


# ------------------------------------------------------------------
# ROUTES
# ------------------------------------------------------------------

@app.get("/")
def root():
    """API root - redirect to docs or return API info."""
    return {
        "message": "MediSync Agentic API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "api": {
            "prescriptions": "/api/v1/prescriptions",
            "orders": "/api/v1/orders",
            "inventory": "/api/v1/inventory"
        },
        "database": get_db_type(),
    }

@app.get("/health")
def health_check():
    """Simple liveness probe."""
    return {
        "status": "ok",
        "database": get_db_type(),
        "version": "1.0.0"
    }


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """
    Legacy chat endpoint.
    
    Deprecated: Use /api/v1/prescriptions/upload instead.
    """
    logger.warning("Legacy /chat endpoint used - consider migrating to /api/v1/prescriptions/upload")
    
    state = PharmacyState(
        user_id=req.user_id,
        user_message=req.message,
    )

    # LangGraph returns dict
    result = agent_graph.invoke(state)

    # Rehydrate into Pydantic model
    final_state = PharmacyState(**result)

    return ChatResponse(
        decision=final_state.pharmacist_decision,
        safety_issues=final_state.safety_issues,
        order_id=final_state.order_id,
        order_status=final_state.order_status,
    )

