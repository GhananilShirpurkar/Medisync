#!/bin/bash

# MediSync Project Launcher
# Starts both backend (FastAPI) and frontend (Vite) servers

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
VENV_PATH="$BACKEND_DIR/.venv"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# ── FIXED: dynamically generate subdomain to avoid localtunnel server locks ──
RANDOM_SUFFIX=$(head /dev/urandom | tr -dc a-z0-9 | head -c 6)
SUBDOMAIN="medisync-koanoir-$RANDOM_SUFFIX"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     MediSync Project Launcher          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${NC}"
    
    kill_pid() {
        local pid=$1
        local name=$2
        if [ ! -z "$pid" ]; then
            echo -e "${YELLOW}→ Stopping $name (PID: $pid)...${NC}"
            kill $pid 2>/dev/null
            for i in {1..5}; do
                if ! ps -p $pid > /dev/null 2>&1; then
                    break
                fi
                sleep 0.5
            done
            if ps -p $pid > /dev/null 2>&1; then
                echo -e "${RED}  $name hung. Force killing...${NC}"
                kill -9 $pid 2>/dev/null
            fi
            wait $pid 2>/dev/null
        fi
    }

    kill_pid "$BACKEND_PID" "Backend"
    kill_pid "$FRONTEND_PID" "Frontend"
    kill_pid "$TUNNEL_PID" "Public Tunnel"
    
    echo -e "${GREEN}✓ All services stopped${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# Check for virtual environment
echo -e "${BLUE}[1/4] Checking virtual environment...${NC}"
if [ -d "$VENV_PATH" ]; then
    echo -e "${GREEN}✓ Virtual environment found at .venv${NC}"
    source "$VENV_PATH/bin/activate"
else
    echo -e "${RED}✗ Virtual environment not found at $VENV_PATH${NC}"
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv "$VENV_PATH"
    source "$VENV_PATH/bin/activate"
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Check backend dependencies
echo -e "\n${BLUE}[2/4] Checking backend dependencies...${NC}"
cd "$BACKEND_DIR"
if ! python -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}Installing backend dependencies...${NC}"
    pip install -r requirements.txt > /dev/null 2>&1
    echo -e "${GREEN}✓ Backend dependencies installed${NC}"
else
    echo -e "${GREEN}✓ Backend dependencies OK${NC}"
fi

# Check frontend dependencies
echo -e "\n${BLUE}[3/4] Checking frontend dependencies...${NC}"
cd "$FRONTEND_DIR"
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    npm install > /dev/null 2>&1
    echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
else
    echo -e "${GREEN}✓ Frontend dependencies OK${NC}"
fi

# Database Preparation
echo -e "\n${BLUE}[3.5/4] Preparing database...${NC}"
cd "$BACKEND_DIR"
echo -e "${YELLOW}  → Running migrations...${NC}"
python scripts/migrate_schema.py
status=$?
if [ $status -ne 0 ]; then
    echo -e "${RED}✗ Database migration failed${NC}"
    exit 1
fi

echo -e "${YELLOW}  → Synchronizing data...${NC}"
python scripts/sync_data.py
status=$?
if [ $status -ne 0 ]; then
    echo -e "${RED}✗ Data synchronization failed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Database ready${NC}"

# Start Backend
echo -e "\n${BLUE}[4/4] Starting services...${NC}"
echo -e "${BLUE}→ Starting Backend Server...${NC}"
cd "$BACKEND_DIR"

stale=$(ss -tlnp 2>/dev/null | grep ':8000 ' | grep -oP 'pid=\K[0-9]+')
if [ ! -z "$stale" ]; then
    echo -e "${YELLOW}  → Killing stale process on port 8000 (PID: $stale)...${NC}"
    kill $stale 2>/dev/null; sleep 1
fi

BACKEND_LOG="/tmp/medisync_backend.log"
rm -f "$BACKEND_LOG" # ── FIXED: clear stale log to prevent false pass ──
uvicorn main:app --reload --host 0.0.0.0 --port 8000 > "$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!

echo -e "${YELLOW}  Waiting for backend (loading ML models)...${NC}"
for i in $(seq 1 40); do
    sleep 1
    if ! ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo -e "${RED}✗ Backend crashed. Last log:${NC}"
        tail -20 "$BACKEND_LOG"
        exit 1
    fi
    if grep -q 'Application startup complete' "$BACKEND_LOG" 2>/dev/null; then
        break
    fi
done

if ps -p $BACKEND_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend running (PID: $BACKEND_PID) — logs: $BACKEND_LOG${NC}"
else
    echo -e "${RED}✗ Backend failed to start. Last log:${NC}"
    tail -20 "$BACKEND_LOG"
    exit 1
fi

# Start Frontend
echo -e "${BLUE}→ Starting Frontend Server...${NC}"
cd "$FRONTEND_DIR"

FRONTEND_LOG="/tmp/medisync_frontend.log"
rm -f "$FRONTEND_LOG" # ── FIXED: clear stale log to prevent false pass ──
npm run dev > "$FRONTEND_LOG" 2>&1 &
FRONTEND_PID=$!

for i in $(seq 1 8); do
    sleep 1
    if ! ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo -e "${RED}✗ Frontend crashed. Last log:${NC}"
        tail -20 "$FRONTEND_LOG"
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
    if grep -q 'Local:' "$FRONTEND_LOG" 2>/dev/null; then
        break
    fi
done

if ps -p $FRONTEND_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend running (PID: $FRONTEND_PID) — logs: $FRONTEND_LOG${NC}"
else
    echo -e "${RED}✗ Frontend failed to start. Last log:${NC}"
    tail -20 "$FRONTEND_LOG"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Start Tunnel
echo -e "\n${BLUE}[5/5] Starting Public Tunnel for WhatsApp...${NC}"

# Kill any stale localtunnel processes to ensure our subdomain isn't blocked
stale_tunnel=$(pgrep -f "localtunnel.*$SUBDOMAIN" || true)
if [ ! -z "$stale_tunnel" ]; then
    echo -e "${YELLOW}  → Killing stale localtunnel process (PID: $stale_tunnel)...${NC}"
    pkill -f "localtunnel.*$SUBDOMAIN" 2>/dev/null; sleep 1
fi

TUNNEL_LOG="/tmp/medisync_tunnel.log"

# ── FIXED: bypass localtunnel confirmation page automatically ──
yes | npx localtunnel --port 8000 --subdomain "$SUBDOMAIN" > "$TUNNEL_LOG" 2>&1 &
TUNNEL_PID=$!

echo -e "${YELLOW}  Waiting for tunnel URL (using subdomain: $SUBDOMAIN)...${NC}"
TUNNEL_URL=""
for i in $(seq 1 15); do
    sleep 1
    TUNNEL_URL=$(grep -o 'https://[^ ]*\.loca\.lt' "$TUNNEL_LOG" | head -n 1)
    if [ ! -z "$TUNNEL_URL" ]; then
        break
    fi
done

if [ ! -z "$TUNNEL_URL" ]; then
    echo -e "${GREEN}✓ Tunnel running at: $TUNNEL_URL${NC}"

    # ── FIXED: bypass localtunnel browser confirmation by pre-hitting with correct header ──
    echo -e "${YELLOW}  Bypassing tunnel confirmation page...${NC}"
    sleep 2
    curl --max-time 10 -s -o /dev/null "$TUNNEL_URL" -H "Bypass-Tunnel-Reminder: true" || true

    echo -e "${YELLOW}  Registering WhatsApp Webhook...${NC}"
    cd "$BACKEND_DIR"
    python scripts/register_whatsapp_webhook.py "$TUNNEL_URL/api/webhook/whatsapp" 2>/dev/null || \
        echo -e "${YELLOW}  ⚠️  Auto-register failed. Manually set webhook in Twilio Console to:${NC}\n  👉 $TUNNEL_URL/api/webhook/whatsapp${NC}"
else
    echo -e "${RED}✗ Failed to start public tunnel.${NC}"
fi

echo -e "\n${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        All Services Running!           ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Backend API:${NC}  http://localhost:8000"
echo -e "${BLUE}API Docs:${NC}     http://localhost:8000/docs"
echo -e "${BLUE}Frontend:${NC}     http://localhost:5173"
if [ ! -z "$TUNNEL_URL" ]; then
    echo -e "${BLUE}Public API:${NC}   $TUNNEL_URL"
    echo -e "${BLUE}WhatsApp WH:${NC}  $TUNNEL_URL/api/webhook/whatsapp"
fi
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

wait