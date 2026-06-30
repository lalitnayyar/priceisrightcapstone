#!/usr/bin/env bash
# ============================================================================
# diagnose.sh — Diagnostic script for Price Is Right application
# ============================================================================
# Tests all modules and provides PASS/FAIL/WARN results.
# Usage: ./scripts/diagnose.sh
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

pass() { echo -e "  ${GREEN}[PASS]${NC} $1"; ((PASS++)); }
fail() { echo -e "  ${RED}[FAIL]${NC} $1"; ((FAIL++)); }
warn() { echo -e "  ${YELLOW}[WARN]${NC} $1"; ((WARN++)); }

echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}  Price Is Right — Diagnostic Report                        ${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

# ---------------------------------------------------------------------------
# 1. Environment checks
# ---------------------------------------------------------------------------
echo -e "${BLUE}[1] Environment Configuration${NC}"

if [ -f ".env" ]; then
    pass ".env file exists"
else
    fail ".env file missing (copy from .env.example)"
fi

if [ -f ".env" ] && grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null; then
    pass "OPENAI_API_KEY appears to be set"
else
    warn "OPENAI_API_KEY may not be set in .env"
fi

if [ -f ".env" ] && grep -q "PUSHOVER_USER=" .env 2>/dev/null; then
    pass "PUSHOVER_USER is present in .env"
else
    warn "PUSHOVER_USER not set — push notifications will be disabled"
fi

if [ -f ".env" ] && grep -q "PUSHOVER_TOKEN=" .env 2>/dev/null; then
    pass "PUSHOVER_TOKEN is present in .env"
else
    warn "PUSHOVER_TOKEN not set — push notifications will be disabled"
fi

echo ""

# ---------------------------------------------------------------------------
# 2. File structure checks
# ---------------------------------------------------------------------------
echo -e "${BLUE}[2] Project File Structure${NC}"

REQUIRED_FILES=(
    "app/__init__.py"
    "app/main.py"
    "app/api.py"
    "app/agents/__init__.py"
    "app/agents/agent.py"
    "app/agents/scanner_agent.py"
    "app/agents/frontier_agent.py"
    "app/agents/specialist_agent.py"
    "app/agents/neural_network_agent.py"
    "app/agents/ensemble_agent.py"
    "app/agents/messaging_agent.py"
    "app/agents/planning_agent.py"
    "app/agents/autonomous_planning_agent.py"
    "app/core/__init__.py"
    "app/core/deals.py"
    "app/core/preprocessor.py"
    "app/core/deal_agent_framework.py"
    "app/core/rag_db.py"
    "app/models/__init__.py"
    "app/models/deep_neural_network.py"
    "app/ui/__init__.py"
    "app/ui/dashboard.py"
    "app/utils/__init__.py"
    "app/utils/log_utils.py"
    "Dockerfile"
    "docker-compose.yml"
    "requirements.txt"
    ".env.example"
    "README.md"
    "scripts/deploy.sh"
    "scripts/start.sh"
    "scripts/stop.sh"
)

for f in "${REQUIRED_FILES[@]}"; do
    if [ -f "$f" ]; then
        pass "$f"
    else
        fail "$f is missing"
    fi
done

echo ""

# ---------------------------------------------------------------------------
# 3. Python syntax checks
# ---------------------------------------------------------------------------
echo -e "${BLUE}[3] Python Syntax Validation${NC}"

PYTHON_FILES=(
    "app/main.py"
    "app/api.py"
    "app/agents/agent.py"
    "app/agents/scanner_agent.py"
    "app/agents/frontier_agent.py"
    "app/agents/specialist_agent.py"
    "app/agents/neural_network_agent.py"
    "app/agents/ensemble_agent.py"
    "app/agents/messaging_agent.py"
    "app/agents/planning_agent.py"
    "app/core/deals.py"
    "app/core/preprocessor.py"
    "app/core/deal_agent_framework.py"
    "app/core/rag_db.py"
    "app/models/deep_neural_network.py"
    "app/ui/dashboard.py"
    "app/utils/log_utils.py"
)

for f in "${PYTHON_FILES[@]}"; do
    if python3 -m py_compile "$f" 2>/dev/null; then
        pass "Syntax OK: $f"
    else
        fail "Syntax error in: $f"
    fi
done

echo ""

# ---------------------------------------------------------------------------
# 4. Docker checks
# ---------------------------------------------------------------------------
echo -e "${BLUE}[4] Docker Configuration${NC}"

if command -v docker &>/dev/null; then
    pass "Docker is installed: $(docker --version)"
else
    fail "Docker is not installed"
fi

if command -v docker &>/dev/null && docker compose version &>/dev/null 2>&1; then
    pass "Docker Compose is available: $(docker compose version)"
else
    warn "Docker Compose plugin may not be available (try 'docker-compose' instead)"
fi

if [ -f "Dockerfile" ]; then
    pass "Dockerfile exists"
else
    fail "Dockerfile missing"
fi

if [ -f "docker-compose.yml" ]; then
    pass "docker-compose.yml exists"
else
    fail "docker-compose.yml missing"
fi

echo ""

# ---------------------------------------------------------------------------
# 5. Data checks
# ---------------------------------------------------------------------------
echo -e "${BLUE}[5] Data and Model Files${NC}"

if [ -d "data" ]; then
    pass "data/ directory exists"
else
    warn "data/ directory missing (will be created on first run)"
fi

if [ -f "data/deep_neural_network.pth" ]; then
    pass "Neural network weights file found"
else
    warn "data/deep_neural_network.pth not found — Neural Network Agent will use random weights"
fi

if [ -d "products_vectorstore" ]; then
    pass "ChromaDB vector store directory exists"
else
    warn "products_vectorstore/ not found — run 'python -m app.main --mode init-rag' to initialise"
fi

echo ""

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
TOTAL=$((PASS + FAIL + WARN))
echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}  Diagnostic Summary${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""
echo -e "  Total checks: $TOTAL"
echo -e "  ${GREEN}PASS: $PASS${NC}"
echo -e "  ${RED}FAIL: $FAIL${NC}"
echo -e "  ${YELLOW}WARN: $WARN${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "  ${GREEN}✓ System is ready to deploy!${NC}"
    echo -e "  Run: ${CYAN}./scripts/deploy.sh${NC}"
else
    echo -e "  ${RED}✗ Please fix the FAIL items above before deploying.${NC}"
fi

if [ $WARN -gt 0 ]; then
    echo -e "  ${YELLOW}⚠ Review WARN items — some features may be limited.${NC}"
fi
echo ""
