#!/usr/bin/env bash
# ============================================================================
# theme_patch.sh — Apply unified colour scheme to the Price Is Right app
# ============================================================================
# This script:
#   1. Verifies that the unified theme module (app/ui/theme.py) is present
#   2. Verifies that dashboard.py and settings_page.py import from theme.py
#   3. Checks that the dark/light toggle button is wired in dashboard.py
#   4. Validates Python syntax on all three UI files
#   5. Optionally rebuilds the Docker image and restarts the app container
#      so the new theme is live immediately
#
# Usage:
#   ./scripts/theme_patch.sh               # Check + rebuild + restart
#   ./scripts/theme_patch.sh --check       # Dry-run: report only, no changes
#   ./scripts/theme_patch.sh --no-restart  # Apply but skip container restart
#   ./scripts/theme_patch.sh --help        # Show this help
#
# What the unified theme provides:
#   - Single source of truth: app/ui/theme.py
#   - Dark palette  (#0D1117 page, #161B22 surface, #FF6B35 accent)
#   - Light palette (#F6F8FA page, #FFFFFF surface, #FF6B35 accent)
#   - Dark/Light toggle button in the top-right of the header
#   - Uniform CSS applied to: tabs, accordions, buttons, inputs, tables,
#     dataframes, markdown, code blocks, log panel, footer, plots
#   - All HTML helpers (header, footer, agent status) are theme-aware
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
CHECKS_PASS=0
CHECKS_FAIL=0

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
check_header() {
    echo -e "${CYAN}${BOLD}------------------------------------------------------------${NC}"
    echo -e "${CYAN}${BOLD}  $1${NC}"
    echo -e "${CYAN}${BOLD}------------------------------------------------------------${NC}"
}

pass() { CHECKS_PASS=$((CHECKS_PASS+1)); echo -e "  ${GREEN}[PASS]${NC} $1"; }
fail() { CHECKS_FAIL=$((CHECKS_FAIL+1)); echo -e "  ${RED}[FAIL]${NC} $1"; }
warn() { echo -e "  ${YELLOW}[WARN]${NC} $1"; }
info() { echo -e "  ${BLUE}[INFO]${NC} $1"; }

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
echo ""
echo -e "${CYAN}${BOLD}============================================================${NC}"
echo -e "${CYAN}${BOLD}  Price Is Right — Theme Patch Script                      ${NC}"
if [ "$DRY_RUN" = true ]; then
echo -e "${YELLOW}${BOLD}  MODE: DRY RUN (--check) — no container changes           ${NC}"
fi
echo -e "${CYAN}${BOLD}============================================================${NC}"
echo ""

# ============================================================================
# CHECK 1 — theme.py exists
# ============================================================================
check_header "Check 1 — app/ui/theme.py (unified design system) exists"

if [ -f "app/ui/theme.py" ]; then
    SIZE=$(wc -l < app/ui/theme.py)
    pass "app/ui/theme.py exists ($SIZE lines)"
else
    fail "app/ui/theme.py NOT FOUND — the unified theme module is missing"
    echo -e "${RED}  Please ensure the file was created by the latest commit.${NC}"
    echo -e "${RED}  Run: git pull origin main${NC}"
    echo ""
fi

echo ""

# ============================================================================
# CHECK 2 — dashboard.py imports from theme.py
# ============================================================================
check_header "Check 2 — dashboard.py imports from app.ui.theme"

if grep -q "from app.ui.theme import" app/ui/dashboard.py 2>/dev/null; then
    IMPORTS=$(grep "from app.ui.theme import" app/ui/dashboard.py)
    pass "dashboard.py imports theme module"
    info "  $IMPORTS"
else
    fail "dashboard.py does NOT import from app.ui.theme"
fi

echo ""

# ============================================================================
# CHECK 3 — settings_page.py imports from theme.py
# ============================================================================
check_header "Check 3 — settings_page.py imports from app.ui.theme"

if grep -q "from app.ui.theme import" app/ui/settings_page.py 2>/dev/null; then
    IMPORTS=$(grep "from app.ui.theme import" app/ui/settings_page.py)
    pass "settings_page.py imports theme module"
    info "  $IMPORTS"
else
    fail "settings_page.py does NOT import from app.ui.theme"
fi

echo ""

# ============================================================================
# CHECK 4 — Dark/Light toggle button is wired in dashboard.py
# ============================================================================
check_header "Check 4 — Dark/Light toggle button wired in dashboard.py"

if grep -q "theme_btn" app/ui/dashboard.py 2>/dev/null && \
   grep -q "_toggle_theme" app/ui/dashboard.py 2>/dev/null; then
    pass "Dark/Light toggle button (theme_btn) and _toggle_theme() found"
else
    fail "Dark/Light toggle button NOT found in dashboard.py"
fi

echo ""

# ============================================================================
# CHECK 5 — Python syntax validation on all three UI files
# ============================================================================
check_header "Check 5 — Python syntax validation (theme.py, dashboard.py, settings_page.py)"

for f in app/ui/theme.py app/ui/dashboard.py app/ui/settings_page.py; do
    if python3 -m py_compile "$f" 2>/dev/null; then
        pass "$f — syntax OK"
    else
        fail "$f — SYNTAX ERROR"
        python3 -m py_compile "$f" 2>&1 | sed 's/^/    /'
    fi
done

echo ""

# ============================================================================
# CHECK 6 — BRAND colours are consistent (primary is #FF6B35)
# ============================================================================
check_header "Check 6 — Brand primary colour is #FF6B35 (vivid orange)"

if grep -q '"primary": "#FF6B35"' app/ui/theme.py 2>/dev/null; then
    pass "Brand primary colour #FF6B35 confirmed in theme.py"
else
    warn "Brand primary colour may have changed — verify app/ui/theme.py BRAND dict"
fi

echo ""

# ============================================================================
# CHECK 7 — Both DARK_THEME and LIGHT_THEME are defined
# ============================================================================
check_header "Check 7 — DARK_THEME and LIGHT_THEME both defined in theme.py"

DARK_OK=false; LIGHT_OK=false
grep -q "^DARK_THEME" app/ui/theme.py 2>/dev/null && DARK_OK=true
grep -q "^LIGHT_THEME" app/ui/theme.py 2>/dev/null && LIGHT_OK=true

if $DARK_OK && $LIGHT_OK; then
    pass "DARK_THEME and LIGHT_THEME both defined"
elif $DARK_OK; then
    fail "LIGHT_THEME not found in theme.py"
elif $LIGHT_OK; then
    fail "DARK_THEME not found in theme.py"
else
    fail "Neither DARK_THEME nor LIGHT_THEME found in theme.py"
fi

echo ""

# ============================================================================
# CHECK 8 — get_css(), get_header_html(), get_footer_html() are exported
# ============================================================================
check_header "Check 8 — Required theme helper functions are exported"

for fn in "def get_css" "def get_header_html" "def get_footer_html" "def get_agent_status_html"; do
    if grep -q "$fn" app/ui/theme.py 2>/dev/null; then
        pass "theme.py exports: $fn()"
    else
        fail "theme.py MISSING: $fn()"
    fi
done

echo ""

# ============================================================================
# Summary
# ============================================================================
echo -e "${CYAN}${BOLD}============================================================${NC}"
echo -e "${CYAN}${BOLD}  Theme Check Summary${NC}"
echo -e "${CYAN}${BOLD}============================================================${NC}"
echo ""
echo -e "  Checks passed : ${GREEN}${CHECKS_PASS}${NC}"
echo -e "  Checks failed : $([ $CHECKS_FAIL -gt 0 ] && echo "${RED}${CHECKS_FAIL}${NC}" || echo "${GREEN}${CHECKS_FAIL}${NC}")"
echo ""

if [ "$CHECKS_FAIL" -gt 0 ]; then
    echo -e "  ${RED}✗ Theme check FAILED — pull latest code and try again:${NC}"
    echo -e "    ${CYAN}git pull origin main && ./scripts/theme_patch.sh${NC}"
    echo ""
    if [ "$DRY_RUN" = false ] && [ "$NO_RESTART" = false ]; then
        echo -e "${YELLOW}Skipping container restart due to check failures.${NC}"
    fi
else
    echo -e "  ${GREEN}✓ All theme checks passed!${NC}"
    echo ""

    if [ "$DRY_RUN" = false ] && [ "$NO_RESTART" = false ]; then
        echo -e "${BLUE}Rebuilding app container to apply theme changes...${NC}"
        echo ""

        # Only rebuild the app service (chromadb and api don't need it)
        if docker compose ps --quiet app 2>/dev/null | grep -q .; then
            echo -e "${YELLOW}Rebuilding app image...${NC}"
            docker compose build app

            echo -e "${YELLOW}Restarting app container (rolling — chromadb stays running)...${NC}"
            docker compose up -d --no-deps app

            echo ""
            echo -e "${GREEN}✓ App container restarted with new theme.${NC}"
            echo ""
            echo -e "  ${GREEN}Dashboard:${NC}  http://localhost:7860"
            echo -e "  ${CYAN}Tip:${NC}        Use the ☀️/🌙 button in the top-right to toggle themes"
        else
            echo -e "${YELLOW}App container is not running — starting all services...${NC}"
            docker compose up -d
            echo -e "${GREEN}✓ Services started.${NC}"
            echo ""
            echo -e "  ${GREEN}Dashboard:${NC}  http://localhost:7860"
        fi
    elif [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}  Dry-run mode — no container changes made.${NC}"
        echo -e "  Run ${CYAN}./scripts/theme_patch.sh${NC} to apply and restart."
    else
        echo -e "${YELLOW}  --no-restart: container not restarted.${NC}"
        echo -e "  Run ${CYAN}./scripts/start.sh${NC} when ready."
    fi
fi

echo ""
echo -e "${CYAN}${BOLD}============================================================${NC}"
echo -e "  Colour Palette Summary"
echo -e "${CYAN}${BOLD}============================================================${NC}"
echo ""
echo -e "  ${BOLD}Dark Theme${NC}"
echo -e "    Page background  : #0D1117  (GitHub-dark)"
echo -e "    Surface          : #161B22"
echo -e "    Accent (primary) : #FF6B35  (vivid orange)"
echo -e "    Secondary accent : #4ECDC4  (teal)"
echo -e "    Text primary     : #E6EDF3"
echo -e "    Text muted       : #8B949E"
echo ""
echo -e "  ${BOLD}Light Theme${NC}"
echo -e "    Page background  : #F6F8FA"
echo -e "    Surface          : #FFFFFF"
echo -e "    Accent (primary) : #FF6B35  (vivid orange — unchanged)"
echo -e "    Secondary accent : #0969DA  (GitHub blue)"
echo -e "    Text primary     : #1F2328"
echo -e "    Text muted       : #57606A"
echo ""
echo -e "  ${BOLD}Toggle:${NC} Click the ☀️ / 🌙 button in the top-right of the header"
echo ""
echo -e "${CYAN}${BOLD}============================================================${NC}"
echo -e "  Author: Lalit Nayyar | lalitnayyar@gmail.com"
echo -e "  Repo  : https://github.com/lalitnayyar/priceisrightcapstone"
echo -e "${CYAN}${BOLD}============================================================${NC}"
echo ""
