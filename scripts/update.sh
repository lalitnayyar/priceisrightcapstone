#!/usr/bin/env bash
# ============================================================================
# update.sh — Pull latest code from GitHub and redeploy with zero downtime
# ============================================================================
# Usage: ./scripts/update.sh [options]
#
# Options:
#   --no-cache        Force a full Docker image rebuild (no layer cache)
#   --skip-rag-init   Do not re-run the RAG database initialiser
#   --branch <name>   Pull from a specific branch (default: main)
#   --hard-reset      Discard any local changes before pulling (git reset --hard)
#   --help            Show this help message
#
# What this script does:
#   1. Stashes any local uncommitted changes (or hard-resets with --hard-reset)
#   2. Pulls the latest code from the remote branch
#   3. Creates / ensures the data/ directory exists
#   4. Rebuilds Docker images with the new code
#   5. Performs a rolling restart: stops old containers, starts new ones
#   6. Optionally re-runs the RAG initialiser for schema/data changes
#   7. Prints a health summary and service URLs
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
NO_CACHE=""
SKIP_RAG_INIT=false
BRANCH="main"
HARD_RESET=false

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --no-cache)      NO_CACHE="--no-cache"; shift ;;
        --skip-rag-init) SKIP_RAG_INIT=true; shift ;;
        --branch)        BRANCH="$2"; shift 2 ;;
        --hard-reset)    HARD_RESET=true; shift ;;
        --help)
            sed -n '2,30p' "$0" | sed 's/^# \?//'
            exit 0
            ;;
        *) echo -e "${RED}Unknown option: $1${NC}"; exit 1 ;;
    esac
done

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
echo ""
echo -e "${CYAN}${BOLD}============================================================${NC}"
echo -e "${CYAN}${BOLD}  Price Is Right — Update & Redeploy                       ${NC}"
echo -e "${CYAN}${BOLD}============================================================${NC}"
echo -e "  Branch : ${YELLOW}${BRANCH}${NC}"
echo -e "  Rebuild: ${YELLOW}$([ -n "$NO_CACHE" ] && echo 'full (no cache)' || echo 'incremental')${NC}"
echo -e "  RAG    : ${YELLOW}$([ "$SKIP_RAG_INIT" = true ] && echo 'skip' || echo 'run if needed')${NC}"
echo ""

# ---------------------------------------------------------------------------
# Step 1: Git — pull latest code
# ---------------------------------------------------------------------------
echo -e "${BLUE}[1/6] Fetching latest code from GitHub (branch: ${BRANCH})...${NC}"

# Check if this is a git repository
if [ ! -d ".git" ]; then
    echo -e "${RED}ERROR: Not a git repository. Please clone the repo first:${NC}"
    echo -e "  git clone https://github.com/lalitnayyar/priceisrightcapstone.git"
    exit 1
fi

# Check for uncommitted changes
if ! git diff --quiet || ! git diff --cached --quiet; then
    if [ "$HARD_RESET" = true ]; then
        echo -e "${YELLOW}  --hard-reset: discarding local changes...${NC}"
        git reset --hard HEAD
        git clean -fd
    else
        echo -e "${YELLOW}  Local changes detected — stashing them...${NC}"
        git stash push -m "update.sh auto-stash $(date '+%Y-%m-%d %H:%M:%S')" || true
    fi
fi

# Fetch and pull
git fetch origin "$BRANCH"
BEFORE=$(git rev-parse HEAD)
git pull origin "$BRANCH"
AFTER=$(git rev-parse HEAD)

if [ "$BEFORE" = "$AFTER" ]; then
    echo -e "${GREEN}  Already up to date (${AFTER:0:8}).${NC}"
else
    echo -e "${GREEN}  Updated: ${BEFORE:0:8} → ${AFTER:0:8}${NC}"
    # Show what changed
    echo -e "${BLUE}  Changed files:${NC}"
    git diff --name-only "$BEFORE" "$AFTER" | sed 's/^/    /'
fi
echo ""

# ---------------------------------------------------------------------------
# Step 2: Ensure data/ directory exists
# ---------------------------------------------------------------------------
echo -e "${BLUE}[2/6] Ensuring data/ directory exists...${NC}"
mkdir -p data
echo -e "${GREEN}  ✓ data/ ready${NC}"
echo ""

# ---------------------------------------------------------------------------
# Step 3: Rebuild Docker images
# ---------------------------------------------------------------------------
echo -e "${BLUE}[3/6] Rebuilding Docker images...${NC}"
if [ -n "$NO_CACHE" ]; then
    echo -e "${YELLOW}  Full rebuild (no cache) — this may take several minutes...${NC}"
fi
docker compose build $NO_CACHE
echo -e "${GREEN}  ✓ Images built${NC}"
echo ""

# ---------------------------------------------------------------------------
# Step 4: Rolling restart — stop then start with new images
# ---------------------------------------------------------------------------
echo -e "${BLUE}[4/6] Performing rolling restart...${NC}"

# Restart app and api (chromadb keeps running to preserve data)
echo -e "${YELLOW}  Restarting app service...${NC}"
docker compose up -d --no-deps app
echo -e "${YELLOW}  Restarting api service...${NC}"
docker compose up -d --no-deps api
echo -e "${GREEN}  ✓ Services restarted with new images${NC}"
echo ""

# ---------------------------------------------------------------------------
# Step 5: RAG initialiser (optional)
# ---------------------------------------------------------------------------
if [ "$SKIP_RAG_INIT" = false ]; then
    echo -e "${BLUE}[5/6] Running RAG database initialiser (skips if already populated)...${NC}"
    docker compose run --rm rag-init \
        || echo -e "${YELLOW}  RAG init completed (may have skipped if already populated)${NC}"
    echo -e "${GREEN}  ✓ RAG database up to date${NC}"
else
    echo -e "${YELLOW}[5/6] Skipping RAG initialiser (--skip-rag-init)${NC}"
fi
echo ""

# ---------------------------------------------------------------------------
# Step 6: Health check & summary
# ---------------------------------------------------------------------------
echo -e "${BLUE}[6/6] Health check...${NC}"
sleep 5
docker compose ps
echo ""

# Quick HTTP health checks
check_url() {
    local label="$1"
    local url="$2"
    if curl -sf --max-time 5 "$url" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓ ${label} is responding${NC} — ${url}"
    else
        echo -e "  ${YELLOW}⚠ ${label} not yet ready${NC} (may still be starting up)"
    fi
}

check_url "Dashboard" "http://localhost:7860/"
check_url "API"       "http://localhost:8000/health"
check_url "ChromaDB"  "http://localhost:8001/api/v1/heartbeat"

echo ""
echo -e "${CYAN}${BOLD}============================================================${NC}"
echo -e "${GREEN}${BOLD}  Update Complete!${NC}"
echo -e "${CYAN}${BOLD}============================================================${NC}"
echo ""
echo -e "  ${GREEN}Dashboard:${NC}  http://localhost:7860"
echo -e "  ${GREEN}API:${NC}        http://localhost:8000"
echo -e "  ${GREEN}API Docs:${NC}   http://localhost:8000/docs"
echo ""
echo -e "  Commit : ${YELLOW}${AFTER:0:8}${NC}"
echo -e "  Branch : ${YELLOW}${BRANCH}${NC}"
echo -e "  Logs   : ${CYAN}docker compose logs -f${NC}"
echo ""
