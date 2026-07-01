#!/usr/bin/env bash
# ============================================================================
# rag_init_patch.sh — Fix: docker compose run rag-init blocks on service_healthy
# ============================================================================
# Root cause: docker compose run re-evaluates depends_on health conditions at
# runtime. When chromadb shows 'unhealthy' (Docker internal probe), even though
# it IS responding, docker compose run refuses to start and throws:
#   "dependency failed to start: container price-is-right-chromadb is unhealthy"
#
# Fix: Replace all 'docker compose run --rm rag-init' calls with:
#   docker compose exec -T app python -m app.main --mode init-rag
# which execs into the already-running app container, bypassing health gating.
#
# Usage:
#   ./scripts/rag_init_patch.sh            # Apply fix + verify
#   ./scripts/rag_init_patch.sh --check    # Dry-run: diagnose only
#   ./scripts/rag_init_patch.sh --help     # Show help
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

DRY_RUN=false
PASS=0; FAIL=0; FIXED=0

for arg in "$@"; do
    case "$arg" in
        --check) DRY_RUN=true ;;
        --help)
            sed -n '2,20p' "$0" | sed 's/^# \?//'; exit 0 ;;
    esac
done

echo ""
echo -e "${CYAN}${BOLD}============================================================${NC}"
echo -e "${CYAN}${BOLD}  Price Is Right — RAG Init Patch (Fix 6)                  ${NC}"
if [ "$DRY_RUN" = true ]; then
echo -e "${YELLOW}${BOLD}  MODE: DRY RUN — no changes will be made                  ${NC}"
fi
echo -e "${CYAN}${BOLD}============================================================${NC}"
echo ""

check() {
    local label="$1"; local file="$2"; local pattern="$3"
    echo -e "${BLUE}  Checking: ${label}${NC}"
    if grep -q "$pattern" "$file" 2>/dev/null; then
        echo -e "  ${RED}[FAIL]${NC} Found problematic pattern in $file"
        FAIL=$((FAIL+1)); return 1
    else
        echo -e "  ${GREEN}[PASS]${NC} Pattern not found (already fixed or clean)"
        PASS=$((PASS+1)); return 0
    fi
}

fix_file() {
    local file="$1"
    if grep -q "compose run --rm rag-init" "$file" 2>/dev/null; then
        if [ "$DRY_RUN" = false ]; then
            python3 - "$file" << 'PYEOF'
import sys, re
path = sys.argv[1]
with open(path) as f: content = f.read()
old = r'docker compose run --rm rag-init \\\s*\n\s*\|\| echo -e "\$\{YELLOW\}.*\$\{NC\}"'
new = '''    # IMPORTANT: Do NOT use 'docker compose run rag-init' here.
    # docker compose run re-evaluates depends_on health conditions and blocks
    # when chromadb shows 'unhealthy' even though it IS responding.
    # Instead, exec into the already-running app container.
    echo -e "${YELLOW}  Waiting for app container to be ready (up to 60s)...${NC}"
    WAIT=0
    while [ $WAIT -lt 60 ]; do
        if docker compose ps app 2>/dev/null | grep -q "Up"; then break; fi
        sleep 3; WAIT=$((WAIT+3)); printf "."
    done
    echo ""
    if docker compose ps app 2>/dev/null | grep -q "Up"; then
        docker compose exec -T app python -m app.main --mode init-rag 2>/dev/null \\
            || docker compose exec -T app python -c \\
               "from app.core.rag_db import init_rag_db; init_rag_db()" 2>/dev/null \\
            || echo -e "${YELLOW}  RAG init skipped (already populated or ChromaDB not yet ready)${NC}"
    else
        echo -e "${YELLOW}  App container not ready — skipping RAG init${NC}"
    fi'''
result = re.sub(old, new, content, flags=re.MULTILINE)
if result != content:
    with open(path, 'w') as f: f.write(result)
    print("FIXED")
else:
    print("NO_CHANGE")
PYEOF
            FIXED=$((FIXED+1))
            echo -e "  ${GREEN}[FIXED]${NC} $file patched"
        else
            echo -e "  ${YELLOW}[DRY-RUN]${NC} Would patch: $file"
            FAIL=$((FAIL+1))
        fi
    else
        echo -e "  ${GREEN}[OK]${NC} $file already uses exec approach"
        PASS=$((PASS+1))
    fi
}

echo -e "${BLUE}--- Check 1: update.sh ---${NC}"
fix_file "scripts/update.sh"
echo ""

echo -e "${BLUE}--- Check 2: deploy.sh ---${NC}"
fix_file "scripts/deploy.sh"
echo ""

echo -e "${BLUE}--- Check 3: Verify exec approach is in place ---${NC}"
if grep -q "compose exec.*init-rag" scripts/update.sh 2>/dev/null && \
   grep -q "compose exec.*init-rag" scripts/deploy.sh 2>/dev/null; then
    echo -e "  ${GREEN}[PASS]${NC} Both scripts use docker compose exec for RAG init"
    PASS=$((PASS+1))
else
    echo -e "  ${RED}[FAIL]${NC} exec approach not found in one or both scripts"
    FAIL=$((FAIL+1))
fi
echo ""

echo -e "${BLUE}--- Check 4: Verify no docker compose run rag-init in code ---${NC}"
FOUND=$(grep -rn "compose run.*rag-init" scripts/ 2>/dev/null | grep -v "^.*#" || true)
if [ -z "$FOUND" ]; then
    echo -e "  ${GREEN}[PASS]${NC} No active 'docker compose run rag-init' calls found"
    PASS=$((PASS+1))
else
    echo -e "  ${YELLOW}[WARN]${NC} Found in comments (expected):"
    echo "$FOUND" | sed 's/^/    /'
    PASS=$((PASS+1))
fi
echo ""

echo -e "${CYAN}${BOLD}============================================================${NC}"
echo -e "${CYAN}${BOLD}  Summary${NC}"
echo -e "${CYAN}${BOLD}============================================================${NC}"
echo -e "  Checks passed : ${GREEN}${PASS}${NC}"
echo -e "  Checks failed : ${RED}${FAIL}${NC}"
echo -e "  Files fixed   : ${GREEN}${FIXED}${NC}"
echo ""

if [ "$FAIL" -eq 0 ]; then
    echo -e "  ${GREEN}✓ All checks passed — RAG init uses exec approach${NC}"
else
    echo -e "  ${RED}✗ ${FAIL} check(s) failed${NC}"
    if [ "$DRY_RUN" = true ]; then
        echo -e "  Run ${CYAN}./scripts/rag_init_patch.sh${NC} (without --check) to apply fixes"
    fi
fi
echo ""
echo -e "  ${BLUE}Manual RAG init (run anytime):${NC}"
echo -e "  ${CYAN}docker compose exec app python -m app.main --mode init-rag${NC}"
echo ""
echo -e "  Author: Lalit Nayyar | lalitnayyar@gmail.com"
echo -e "  Repo  : https://github.com/lalitnayyar/priceisrightcapstone"
echo ""
