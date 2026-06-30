#!/usr/bin/env bash
# ============================================================================
# stop.sh — Stop the Price Is Right application containers
# ============================================================================
# Usage: ./scripts/stop.sh [--remove-volumes]
#
# Options:
#   --remove-volumes   Also remove persistent data volumes (WARNING: deletes RAG DB)
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

REMOVE_VOLUMES=false

for arg in "$@"; do
    case $arg in
        --remove-volumes) REMOVE_VOLUMES=true ;;
    esac
done

echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}  Price Is Right — Stopping Services                        ${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

if [ "$REMOVE_VOLUMES" = true ]; then
    echo -e "${RED}WARNING: --remove-volumes will delete all persistent data including:${NC}"
    echo -e "${RED}  - ChromaDB RAG vector store${NC}"
    echo -e "${RED}  - Application memory (surfaced opportunities)${NC}"
    echo ""
    read -p "Are you sure? Type 'yes' to confirm: " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        echo -e "${YELLOW}Aborted.${NC}"
        exit 0
    fi
    echo -e "${YELLOW}Stopping services and removing volumes...${NC}"
    docker compose down -v
    echo -e "${GREEN}✓ Services stopped and volumes removed${NC}"
else
    echo -e "${YELLOW}Stopping services (data volumes preserved)...${NC}"
    docker compose down
    echo -e "${GREEN}✓ Services stopped${NC}"
fi

echo ""
echo -e "${CYAN}============================================================${NC}"
echo -e "${GREEN}  All services stopped.${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""
echo -e "  To start again: ./scripts/start.sh"
echo -e "  To redeploy:    ./scripts/deploy.sh"
echo ""
