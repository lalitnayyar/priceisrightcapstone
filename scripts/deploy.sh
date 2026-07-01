#!/usr/bin/env bash
# ============================================================================
# deploy.sh — Build and deploy the Price Is Right application
# ============================================================================
# Usage: ./scripts/deploy.sh [--no-cache] [--skip-rag-init]
#
# This script:
#   1. Validates the .env file
#   2. Creates required host directories
#   3. Builds Docker images
#   4. Starts ChromaDB and waits for it to be healthy (Python TCP probe)
#   5. Starts app + api services
#   6. Initialises the RAG database (unless --skip-rag-init is passed)
#   7. Prints service URLs
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

NO_CACHE=""
SKIP_RAG_INIT=false

for arg in "$@"; do
    case $arg in
        --no-cache) NO_CACHE="--no-cache" ;;
        --skip-rag-init) SKIP_RAG_INIT=true ;;
        --help)
            echo "Usage: $0 [--no-cache] [--skip-rag-init]"
            echo "  --no-cache       Force full Docker image rebuild"
            echo "  --skip-rag-init  Skip RAG database initialisation"
            exit 0
            ;;
    esac
done

echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}  Price Is Right — Multi-Agent Deal Hunter                  ${NC}"
echo -e "${CYAN}  Deployment Script                                         ${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

# ---------------------------------------------------------------------------
# Step 1: Validate .env file
# ---------------------------------------------------------------------------
echo -e "${BLUE}[1/6] Validating environment configuration...${NC}"

if [ ! -f ".env" ]; then
    echo -e "${YELLOW}WARNING: .env file not found. Copying from .env.example...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${YELLOW}Please edit .env with your API keys before proceeding.${NC}"
        echo -e "${YELLOW}Required: OPENAI_API_KEY, PUSHOVER_USER, PUSHOVER_TOKEN${NC}"
        read -p "Press Enter to continue after editing .env, or Ctrl+C to abort..."
    else
        echo -e "${RED}ERROR: Neither .env nor .env.example found. Please create .env${NC}"
        exit 1
    fi
fi

# Check for required keys
MISSING_KEYS=()
if ! grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null; then
    MISSING_KEYS+=("OPENAI_API_KEY")
fi

if [ ${#MISSING_KEYS[@]} -gt 0 ]; then
    echo -e "${YELLOW}WARNING: The following keys may not be set in .env:${NC}"
    for key in "${MISSING_KEYS[@]}"; do
        echo -e "${YELLOW}  - $key${NC}"
    done
    echo -e "${YELLOW}The application will start but some features may not work.${NC}"
fi

echo -e "${GREEN}✓ Environment configuration checked${NC}"

# ---------------------------------------------------------------------------
# Step 2: Create data directories
# ---------------------------------------------------------------------------
echo -e "${BLUE}[2/6] Creating data directories...${NC}"
mkdir -p data products_vectorstore logs
echo -e "${GREEN}✓ Data directories ready (data/, products_vectorstore/, logs/)${NC}"

# ---------------------------------------------------------------------------
# Step 3: Build Docker images
# ---------------------------------------------------------------------------
echo -e "${BLUE}[3/6] Building Docker images...${NC}"
echo -e "${YELLOW}This may take several minutes on first build (downloading models)...${NC}"

docker compose build $NO_CACHE

echo -e "${GREEN}✓ Docker images built successfully${NC}"

# ---------------------------------------------------------------------------
# Step 4: Start ChromaDB and wait for it to be healthy
# ---------------------------------------------------------------------------
echo -e "${BLUE}[4/6] Starting ChromaDB...${NC}"

# Start ChromaDB first, detached
docker compose up -d chromadb

echo -e "${YELLOW}Waiting for ChromaDB to be ready (up to 180 s)...${NC}"
echo -e "${YELLOW}(Using Python TCP probe — no curl/wget dependency)${NC}"

# ---------------------------------------------------------------------------
# BULLETPROOF ChromaDB health probe:
# Uses Python TCP socket — always available in the chroma image.
# Tries /api/v2/heartbeat (chroma >= 0.5.x) then /api/v1/heartbeat (older).
# Does NOT rely on curl or wget which are absent in many chroma image builds.
# ---------------------------------------------------------------------------
CHROMA_READY=false
CHROMA_TIMEOUT=180
CHROMA_ELAPSED=0
CHROMA_SLEEP=5

while [ $CHROMA_ELAPSED -lt $CHROMA_TIMEOUT ]; do
    # Run the Python probe inside the chromadb container
    PROBE_RESULT=$(docker compose exec -T chromadb python3 -c "
import socket, sys
def probe(path):
    try:
        s = socket.create_connection(('localhost', 8000), timeout=8)
        s.sendall(('GET ' + path + ' HTTP/1.0\r\nHost: localhost\r\n\r\n').encode())
        r = s.recv(512).decode('utf-8', errors='ignore')
        s.close()
        return '200' in r or 'nanosecond' in r.lower() or 'heartbeat' in r.lower()
    except:
        return False
if probe('/api/v2/heartbeat') or probe('/api/v1/heartbeat'):
    print('READY')
    sys.exit(0)
else:
    print('NOT_READY')
    sys.exit(1)
" 2>/dev/null || echo "EXEC_FAILED")

    if [ "$PROBE_RESULT" = "READY" ]; then
        CHROMA_READY=true
        echo ""
        echo -e "${GREEN}✓ ChromaDB is healthy and ready${NC}"
        break
    fi

    echo -n "."
    sleep $CHROMA_SLEEP
    CHROMA_ELAPSED=$((CHROMA_ELAPSED + CHROMA_SLEEP))
done

if [ "$CHROMA_READY" = false ]; then
    echo ""
    echo -e "${YELLOW}⚠ ChromaDB probe timed out after ${CHROMA_TIMEOUT}s.${NC}"
    echo -e "${YELLOW}  Checking container status...${NC}"
    docker compose ps chromadb
    echo -e "${YELLOW}  Last 20 lines of ChromaDB logs:${NC}"
    docker compose logs --tail=20 chromadb 2>/dev/null || true
    echo ""
    echo -e "${YELLOW}  Continuing deployment — app/api will retry connection on startup.${NC}"
    echo -e "${YELLOW}  Run: ./scripts/chromadb_patch.sh  to diagnose and fix ChromaDB issues.${NC}"
fi

# ---------------------------------------------------------------------------
# Step 5: Start main services
# ---------------------------------------------------------------------------
echo -e "${BLUE}[5/6] Starting app and api services...${NC}"

# Use --no-deps so we don't re-start chromadb (already running)
docker compose up -d --no-deps app api

echo -e "${GREEN}✓ Services started${NC}"

# ---------------------------------------------------------------------------
# Step 6: Initialise RAG database
# ---------------------------------------------------------------------------
if [ "$SKIP_RAG_INIT" = false ]; then
    echo -e "${BLUE}[6/6] Initialising RAG database with sample data...${NC}"
    # IMPORTANT: Do NOT use 'docker compose run rag-init' here.
    # docker compose run re-evaluates depends_on health conditions and blocks
    # when chromadb shows 'unhealthy' (Docker internal probe) even though it
    # IS responding. Instead, exec into the already-running app container.
    echo -e "${YELLOW}Waiting for app container to be ready (up to 90s)...${NC}"
    WAIT=0
    while [ $WAIT -lt 90 ]; do
        if docker compose ps app 2>/dev/null | grep -q "Up"; then break; fi
        sleep 5; WAIT=$((WAIT+5)); printf "."
    done
    echo ""
    if docker compose ps app 2>/dev/null | grep -q "Up"; then
        docker compose exec -T app python -m app.main --mode init-rag 2>/dev/null \
            || docker compose exec -T app python -c \
               "from app.core.rag_db import init_rag_db; init_rag_db()" 2>/dev/null \
            || echo -e "${YELLOW}RAG init skipped (already populated or ChromaDB not yet ready)${NC}"
    else
        echo -e "${YELLOW}App not ready — skipping RAG init. Run manually: docker compose exec app python -m app.main --mode init-rag${NC}"
    fi
    echo -e "${GREEN}✓ RAG database initialised${NC}"
else
    echo -e "${YELLOW}[6/6] Skipping RAG database initialisation (--skip-rag-init)${NC}"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo -e "${CYAN}============================================================${NC}"
echo -e "${GREEN}  Deployment Complete!${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""
echo -e "  ${GREEN}Dashboard:${NC}  http://localhost:7860"
echo -e "  ${GREEN}API:${NC}        http://localhost:8000"
echo -e "  ${GREEN}API Docs:${NC}   http://localhost:8000/docs"
echo -e "  ${GREEN}ChromaDB:${NC}   http://localhost:8001"
echo ""
echo -e "  ${YELLOW}Logs:${NC}         docker compose logs -f app"
echo -e "  ${YELLOW}Update:${NC}       ./scripts/update.sh"
echo -e "  ${YELLOW}Stop:${NC}         ./scripts/stop.sh"
echo -e "  ${YELLOW}Diagnose:${NC}     ./scripts/chromadb_patch.sh --check"
echo ""
