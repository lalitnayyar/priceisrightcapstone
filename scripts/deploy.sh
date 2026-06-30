#!/usr/bin/env bash
# ============================================================================
# deploy.sh — Build and deploy the Price Is Right application
# ============================================================================
# Usage: ./scripts/deploy.sh [--no-cache] [--skip-rag-init]
#
# This script:
#   1. Validates the .env file
#   2. Builds Docker images
#   3. Starts all services
#   4. Initialises the RAG database (unless --skip-rag-init is passed)
#   5. Prints service URLs
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
echo -e "${BLUE}[1/5] Validating environment configuration...${NC}"

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
echo -e "${BLUE}[2/5] Creating data directories...${NC}"
mkdir -p data
echo -e "${GREEN}✓ Data directories ready${NC}"

# ---------------------------------------------------------------------------
# Step 3: Build Docker images
# ---------------------------------------------------------------------------
echo -e "${BLUE}[3/5] Building Docker images...${NC}"
echo -e "${YELLOW}This may take several minutes on first build (downloading models)...${NC}"

docker compose build $NO_CACHE

echo -e "${GREEN}✓ Docker images built successfully${NC}"

# ---------------------------------------------------------------------------
# Step 4: Start services
# ---------------------------------------------------------------------------
echo -e "${BLUE}[4/5] Starting services...${NC}"

# Start ChromaDB first
docker compose up -d chromadb
echo -e "${YELLOW}Waiting for ChromaDB to be healthy...${NC}"
timeout 60 bash -c 'until docker compose exec chromadb curl -sf http://localhost:8000/api/v1/heartbeat > /dev/null 2>&1; do sleep 2; done' || {
    echo -e "${YELLOW}ChromaDB health check timed out; continuing anyway...${NC}"
}

# Start main services
docker compose up -d app api

echo -e "${GREEN}✓ Services started${NC}"

# ---------------------------------------------------------------------------
# Step 5: Initialise RAG database
# ---------------------------------------------------------------------------
if [ "$SKIP_RAG_INIT" = false ]; then
    echo -e "${BLUE}[5/5] Initialising RAG database with sample data...${NC}"
    docker compose run --rm rag-init || echo -e "${YELLOW}RAG init completed (may have skipped if already populated)${NC}"
    echo -e "${GREEN}✓ RAG database initialised${NC}"
else
    echo -e "${YELLOW}[5/5] Skipping RAG database initialisation (--skip-rag-init)${NC}"
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
echo -e "  ${YELLOW}Logs:${NC}       docker compose logs -f app"
echo -e "  ${YELLOW}Stop:${NC}       ./scripts/stop.sh"
echo ""
