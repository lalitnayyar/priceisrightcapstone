#!/usr/bin/env bash
# ============================================================================
# start.sh — Build (if needed) and start the Price Is Right containers
# ============================================================================
# Usage: ./scripts/start.sh [service_name] [--no-build]
#
# If no service_name is provided, all services are started.
# Pass --no-build to skip the image rebuild (use existing images).
#
# Examples:
#   ./scripts/start.sh               # Build + start all services
#   ./scripts/start.sh app           # Build + start only the dashboard
#   ./scripts/start.sh --no-build    # Start all without rebuilding
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SERVICE=""
BUILD_FLAG="--build"

for arg in "$@"; do
    case "$arg" in
        --no-build) BUILD_FLAG="" ;;
        *) SERVICE="$arg" ;;
    esac
done

echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}  Price Is Right — Starting Services                        ${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

# ---------------------------------------------------------------------------
# Ensure .env exists
# ---------------------------------------------------------------------------
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}WARNING: .env not found — copying from .env.example${NC}"
    cp .env.example .env
    echo -e "${YELLOW}Please edit .env with your API keys (OPENAI_API_KEY etc.)${NC}"
fi

# ---------------------------------------------------------------------------
# Ensure data/ directory exists on the host (avoids Docker volume edge cases)
# ---------------------------------------------------------------------------
mkdir -p data
echo -e "${GREEN}✓ data/ directory ready${NC}"

# ---------------------------------------------------------------------------
# Build and start
# ---------------------------------------------------------------------------
if [ -z "$SERVICE" ]; then
    echo -e "${BLUE}Building images and starting all services...${NC}"
    docker compose up -d $BUILD_FLAG
else
    echo -e "${BLUE}Building and starting service: ${SERVICE}${NC}"
    docker compose up -d $BUILD_FLAG "$SERVICE"
fi

echo ""
echo -e "${GREEN}Services started. Checking status...${NC}"
echo ""
docker compose ps

echo ""
echo -e "${CYAN}============================================================${NC}"
echo -e "${GREEN}  Services are running!${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""
echo -e "  Dashboard:  http://localhost:7860"
echo -e "  API:        http://localhost:8000"
echo -e "  API Docs:   http://localhost:8000/docs"
echo ""
echo -e "  View logs:  docker compose logs -f"
echo -e "  Update:     ./scripts/update.sh"
echo -e "  Stop:       ./scripts/stop.sh"
echo ""
