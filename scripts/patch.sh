#!/usr/bin/env bash
# ============================================================================
# patch.sh — Apply all Docker & configuration fixes to Price Is Right
# ============================================================================
# This script is a self-contained patch that detects and fixes all known
# issues with the Docker setup. It is safe to run multiple times (idempotent).
#
# Fixes applied:
#   Fix 1 — Remove COPY data/ from Dockerfile (directory does not exist in repo)
#   Fix 2 — Remove obsolete 'version:' key from docker-compose.yml
#   Fix 3 — Add --build flag to start.sh so images are built on fresh clone
#   Fix 4 — Replace curl with wget in ChromaDB healthcheck (curl not in image)
#            Pin chromadb/chroma image to 0.5.20 (not :latest)
#            Fix deploy.sh ChromaDB wait probe (curl → wget)
#
# Usage:
#   ./scripts/patch.sh              # Apply all fixes, rebuild, restart
#   ./scripts/patch.sh --check      # Dry-run: report what needs fixing, no changes
#   ./scripts/patch.sh --no-restart # Apply fixes but do not restart containers
#   ./scripts/patch.sh --help       # Show this help
#
# After patching:
#   ./scripts/deploy.sh             # Full redeploy (first time)
#   ./scripts/start.sh              # Start with rebuilt images
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
# Argument parsing
# ---------------------------------------------------------------------------
DRY_RUN=false
NO_RESTART=false

for arg in "$@"; do
    case "$arg" in
        --check)      DRY_RUN=true ;;
        --no-restart) NO_RESTART=true ;;
        --help)
            sed -n '2,20p' "$0" | sed 's/^# \?//'
            exit 0
            ;;
        *) echo -e "${RED}Unknown option: $arg${NC}"; exit 1 ;;
    esac
done

# ---------------------------------------------------------------------------
# Counters
# ---------------------------------------------------------------------------
FIXES_NEEDED=0
FIXES_APPLIED=0
ALREADY_OK=0

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
check_header() {
    echo -e "${CYAN}${BOLD}------------------------------------------------------------${NC}"
    echo -e "${CYAN}${BOLD}  $1${NC}"
    echo -e "${CYAN}${BOLD}------------------------------------------------------------${NC}"
}

fix_needed() {
    local msg="$1"
    FIXES_NEEDED=$((FIXES_NEEDED + 1))
    if [ "$DRY_RUN" = true ]; then
        echo -e "  ${YELLOW}[NEEDS FIX]${NC} $msg"
    else
        echo -e "  ${YELLOW}[FIXING]${NC}    $msg"
    fi
}

fix_applied() {
    local msg="$1"
    FIXES_APPLIED=$((FIXES_APPLIED + 1))
    echo -e "  ${GREEN}[FIXED]${NC}     $msg"
}

already_ok() {
    local msg="$1"
    ALREADY_OK=$((ALREADY_OK + 1))
    echo -e "  ${GREEN}[OK]${NC}        $msg"
}

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
echo ""
echo -e "${CYAN}${BOLD}============================================================${NC}"
echo -e "${CYAN}${BOLD}  Price Is Right — Docker Patch Script                     ${NC}"
if [ "$DRY_RUN" = true ]; then
echo -e "${YELLOW}${BOLD}  MODE: DRY RUN (--check) — no changes will be made        ${NC}"
fi
echo -e "${CYAN}${BOLD}============================================================${NC}"
echo ""

# ============================================================================
# FIX 1 — Remove COPY data/ from Dockerfile
# ============================================================================
check_header "Fix 1 — Dockerfile: Remove COPY data/ (directory not in repo)"

if grep -q "^COPY data/" Dockerfile 2>/dev/null; then
    fix_needed "Dockerfile contains 'COPY data/' — will cause build failure"
    if [ "$DRY_RUN" = false ]; then
        # Remove the COPY data/ line
        sed -i '/^COPY data\//d' Dockerfile
        # Ensure mkdir -p for runtime dirs exists
        if ! grep -q "mkdir -p /app/data" Dockerfile; then
            # Insert after WORKDIR /app line
            sed -i '/^WORKDIR \/app/a RUN mkdir -p /app/data /app/products_vectorstore /app/logs \&\& chmod -R 777 /app/data /app/products_vectorstore /app/logs' Dockerfile
        fi
        fix_applied "Removed 'COPY data/' from Dockerfile; added 'RUN mkdir -p' for runtime dirs"
    fi
else
    already_ok "Dockerfile: 'COPY data/' not present"
fi

# Ensure mkdir -p is present even if COPY data/ was already absent
if [ "$DRY_RUN" = false ] && ! grep -q "mkdir -p /app/data" Dockerfile; then
    # Find the WORKDIR line and add mkdir after it
    sed -i '/^WORKDIR \/app/a RUN mkdir -p /app/data /app/products_vectorstore /app/logs \&\& chmod -R 777 /app/data /app/products_vectorstore /app/logs' Dockerfile
    echo -e "  ${GREEN}[ADDED]${NC}     Dockerfile: 'RUN mkdir -p' for runtime directories"
fi

echo ""

# ============================================================================
# FIX 2 — Remove obsolete 'version:' key from docker-compose.yml
# ============================================================================
check_header "Fix 2 — docker-compose.yml: Remove obsolete 'version:' key"

if grep -q "^version:" docker-compose.yml 2>/dev/null; then
    fix_needed "docker-compose.yml has 'version:' key — causes WARN on every command"
    if [ "$DRY_RUN" = false ]; then
        sed -i '/^version:/d' docker-compose.yml
        fix_applied "Removed 'version:' key from docker-compose.yml"
    fi
else
    already_ok "docker-compose.yml: 'version:' key not present"
fi

echo ""

# ============================================================================
# FIX 3 — Add --build flag to start.sh
# ============================================================================
check_header "Fix 3 — scripts/start.sh: Add --build so images are built on fresh clone"

if grep -q "docker compose up -d$" scripts/start.sh 2>/dev/null || \
   grep -q 'docker compose up -d "\$SERVICE"$' scripts/start.sh 2>/dev/null; then
    fix_needed "start.sh uses 'docker compose up -d' without --build"
    if [ "$DRY_RUN" = false ]; then
        # Replace bare 'up -d' with 'up -d --build' (only if --no-build not already handled)
        if ! grep -q "\-\-build" scripts/start.sh; then
            sed -i 's/docker compose up -d$/docker compose up -d --build/' scripts/start.sh
            sed -i 's/docker compose up -d "\$SERVICE"$/docker compose up -d --build "$SERVICE"/' scripts/start.sh
        fi
        fix_applied "Added --build flag to docker compose up in start.sh"
    fi
else
    already_ok "start.sh: --build flag already present"
fi

# Ensure data/ directory creation is in start.sh
if [ "$DRY_RUN" = false ] && ! grep -q "mkdir -p data" scripts/start.sh; then
    # Insert mkdir before the docker compose up line
    sed -i '/docker compose up -d/i mkdir -p data products_vectorstore' scripts/start.sh
    echo -e "  ${GREEN}[ADDED]${NC}     start.sh: 'mkdir -p data products_vectorstore' before docker compose up"
fi

echo ""

# ============================================================================
# FIX 4 — ChromaDB healthcheck: replace curl with wget
# ============================================================================
check_header "Fix 4 — docker-compose.yml: ChromaDB healthcheck curl → wget"

CHROMA_HEALTH_LINE=$(grep -n "curl.*heartbeat" docker-compose.yml 2>/dev/null | head -1 || true)

if echo "$CHROMA_HEALTH_LINE" | grep -q "chromadb\|heartbeat"; then
    fix_needed "ChromaDB healthcheck uses 'curl' — not available in chromadb/chroma image"
    if [ "$DRY_RUN" = false ]; then
        # Replace the curl healthcheck line with wget
        sed -i 's|test: \["CMD", "curl", "-f", "http://localhost:8000/api/v1/heartbeat"\]|test: ["CMD-SHELL", "wget -qO- http://localhost:8000/api/v1/heartbeat || exit 1"]|g' docker-compose.yml
        sed -i 's|test: \["CMD-SHELL", "curl.*heartbeat.*"\]|test: ["CMD-SHELL", "wget -qO- http://localhost:8000/api/v1/heartbeat || exit 1"]|g' docker-compose.yml
        fix_applied "Replaced curl with wget in ChromaDB healthcheck"
    fi
else
    # Check if wget is already there
    if grep -q "wget.*heartbeat" docker-compose.yml 2>/dev/null; then
        already_ok "docker-compose.yml: ChromaDB healthcheck already uses wget"
    else
        already_ok "docker-compose.yml: ChromaDB healthcheck looks correct"
    fi
fi

echo ""

# ============================================================================
# FIX 4b — Pin chromadb/chroma image version
# ============================================================================
check_header "Fix 4b — docker-compose.yml: Pin chromadb/chroma:latest → 0.5.20"

if grep -q "chromadb/chroma:latest" docker-compose.yml 2>/dev/null; then
    fix_needed "chromadb/chroma:latest can silently break — should be pinned to 0.5.20"
    if [ "$DRY_RUN" = false ]; then
        sed -i 's|image: chromadb/chroma:latest|image: chromadb/chroma:0.5.20|g' docker-compose.yml
        fix_applied "Pinned chromadb/chroma:latest → chromadb/chroma:0.5.20"
    fi
else
    already_ok "docker-compose.yml: chromadb image already pinned (not :latest)"
fi

echo ""

# ============================================================================
# FIX 4c — Fix deploy.sh ChromaDB wait probe (curl → wget inside container)
# ============================================================================
check_header "Fix 4c — scripts/deploy.sh: ChromaDB wait probe curl → wget"

if grep -q "docker compose exec chromadb curl" scripts/deploy.sh 2>/dev/null; then
    fix_needed "deploy.sh uses 'curl' inside chromadb container — not available"
    if [ "$DRY_RUN" = false ]; then
        sed -i 's|docker compose exec chromadb curl -sf|docker compose exec chromadb wget -qO-|g' scripts/deploy.sh
        fix_applied "Replaced curl with wget in deploy.sh ChromaDB wait probe"
    fi
else
    already_ok "deploy.sh: ChromaDB wait probe already uses wget (or curl not present)"
fi

echo ""

# ============================================================================
# FIX 5 — Ensure .env exists (copy from .env.example if missing)
# ============================================================================
check_header "Fix 5 — Ensure .env file exists"

if [ ! -f ".env" ]; then
    fix_needed ".env file missing"
    if [ "$DRY_RUN" = false ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            fix_applied "Copied .env.example → .env (edit it with your API keys)"
        else
            echo -e "  ${RED}[ERROR]${NC}     Neither .env nor .env.example found — please create .env manually"
        fi
    fi
else
    already_ok ".env file exists"
fi

echo ""

# ============================================================================
# FIX 6 — Ensure runtime directories exist on host
# ============================================================================
check_header "Fix 6 — Create runtime directories on host (data/, products_vectorstore/)"

DIRS_CREATED=()
for dir in data products_vectorstore; do
    if [ ! -d "$dir" ]; then
        fix_needed "Directory '$dir/' does not exist on host"
        if [ "$DRY_RUN" = false ]; then
            mkdir -p "$dir"
            DIRS_CREATED+=("$dir/")
        fi
    else
        already_ok "Directory '$dir/' exists"
    fi
done

if [ ${#DIRS_CREATED[@]} -gt 0 ] && [ "$DRY_RUN" = false ]; then
    fix_applied "Created directories: ${DIRS_CREATED[*]}"
fi

echo ""

# ============================================================================
# FIX 7 — Ensure all scripts are executable
# ============================================================================
check_header "Fix 7 — Ensure all scripts are executable"

SCRIPTS_FIXED=()
for f in scripts/*.sh; do
    if [ ! -x "$f" ]; then
        fix_needed "$f is not executable"
        if [ "$DRY_RUN" = false ]; then
            chmod +x "$f"
            SCRIPTS_FIXED+=("$f")
        fi
    else
        already_ok "$f is executable"
    fi
done

if [ ${#SCRIPTS_FIXED[@]} -gt 0 ] && [ "$DRY_RUN" = false ]; then
    fix_applied "Made executable: ${SCRIPTS_FIXED[*]}"
fi

echo ""

# ============================================================================
# Summary
# ============================================================================
echo -e "${CYAN}${BOLD}============================================================${NC}"
echo -e "${CYAN}${BOLD}  Patch Summary${NC}"
echo -e "${CYAN}${BOLD}============================================================${NC}"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo -e "  ${YELLOW}DRY RUN — no changes were made${NC}"
    echo ""
    echo -e "  Issues found  : ${YELLOW}${FIXES_NEEDED}${NC}"
    echo -e "  Already OK    : ${GREEN}${ALREADY_OK}${NC}"
    echo ""
    if [ "$FIXES_NEEDED" -gt 0 ]; then
        echo -e "  Run ${CYAN}./scripts/patch.sh${NC} (without --check) to apply all fixes."
    else
        echo -e "  ${GREEN}✓ No fixes needed — everything looks good!${NC}"
    fi
else
    echo -e "  Fixes applied : ${GREEN}${FIXES_APPLIED}${NC}"
    echo -e "  Already OK    : ${GREEN}${ALREADY_OK}${NC}"
    echo ""

    if [ "$FIXES_APPLIED" -gt 0 ]; then
        echo -e "  ${GREEN}✓ All fixes applied successfully!${NC}"
        echo ""

        if [ "$NO_RESTART" = false ]; then
            echo -e "${BLUE}Rebuilding Docker images and restarting services...${NC}"
            echo ""

            # Stop existing containers gracefully
            if docker compose ps --quiet 2>/dev/null | grep -q .; then
                echo -e "${YELLOW}Stopping running containers...${NC}"
                docker compose down --remove-orphans || true
            fi

            # Rebuild and start
            echo -e "${YELLOW}Building images with fixes applied...${NC}"
            docker compose build

            echo -e "${YELLOW}Starting services...${NC}"
            docker compose up -d chromadb

            echo -e "${YELLOW}Waiting for ChromaDB to be healthy (up to 90 s)...${NC}"
            timeout 90 bash -c '
              until docker compose exec chromadb wget -qO- http://localhost:8000/api/v1/heartbeat > /dev/null 2>&1; do
                echo -n "."
                sleep 3
              done
              echo ""
            ' || echo -e "${YELLOW}ChromaDB probe timed out — continuing anyway${NC}"

            docker compose up -d app api

            echo ""
            echo -e "${GREEN}Services restarted with all patches applied.${NC}"
            echo ""
            echo -e "  ${GREEN}Dashboard:${NC}  http://localhost:7860"
            echo -e "  ${GREEN}API:${NC}        http://localhost:8000"
            echo -e "  ${GREEN}API Docs:${NC}   http://localhost:8000/docs"
            echo ""
            echo -e "  ${CYAN}View logs:${NC}  docker compose logs -f"
        else
            echo -e "${YELLOW}  --no-restart: containers not restarted.${NC}"
            echo -e "  Run ${CYAN}./scripts/start.sh${NC} when ready to start."
        fi
    else
        echo -e "  ${GREEN}✓ No fixes were needed — everything was already correct!${NC}"
    fi
fi

echo ""
echo -e "${CYAN}${BOLD}============================================================${NC}"
echo -e "  Author: Lalit Nayyar | lalitnayyar@gmail.com"
echo -e "  Repo  : https://github.com/lalitnayyar/priceisrightcapstone"
echo -e "${CYAN}${BOLD}============================================================${NC}"
echo ""
