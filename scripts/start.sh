#!/usr/bin/env bash
# ============================================================================
# start.sh — Start the Price Is Right application containers
# ============================================================================
# Usage: ./scripts/start.sh [service_name]
#
# If no service_name is provided, all services are started.
# Examples:
#   ./scripts/start.sh          # Start all services
#   ./scripts/start.sh app      # Start only the dashboard
#   ./scripts/start.sh api      # Start only the API
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SERVICE="${1:-}"

echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}  Price Is Right — Starting Services                        ${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

if [ -z "$SERVICE" ]; then
    echo -e "${BLUE}Starting all services...${NC}"
    docker compose up -d
else
    echo -e "${BLUE}Starting service: $SERVICE${NC}"
    docker compose up -d "$SERVICE"
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
echo -e "  Stop:       ./scripts/stop.sh"
echo ""
