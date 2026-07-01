#!/usr/bin/env bash
# =============================================================================
# testrun.sh — Price Is Right Full Test Suite Runner
# =============================================================================
# Runs all unit, integration, and UI smoke tests, then generates a timestamped
# Markdown report at:  tests/results/result_YYYYMMDD_HHMMSS.md
#
# Usage:
#   ./scripts/testrun.sh                   # Run all tests, generate report
#   ./scripts/testrun.sh --docker          # Run tests inside the app container
#   ./scripts/testrun.sh --unit-only       # Run only unit tests (core + agents)
#   ./scripts/testrun.sh --integration     # Run only integration tests
#   ./scripts/testrun.sh --ui              # Run only UI smoke tests
#   ./scripts/testrun.sh --no-report       # Run tests without generating report
#   ./scripts/testrun.sh --open            # Open report in browser after run
#   ./scripts/testrun.sh --help            # Show this help
# =============================================================================

set -euo pipefail

# ── Colour helpers ────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { echo -e "${CYAN}[INFO]${RESET}  $*"; }
success() { echo -e "${GREEN}[PASS]${RESET}  $*"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
error()   { echo -e "${RED}[FAIL]${RESET}  $*"; }
header()  { echo -e "\n${BOLD}${BLUE}$*${RESET}"; echo -e "${BLUE}$(printf '─%.0s' {1..60})${RESET}"; }

# ── Defaults ──────────────────────────────────────────────────────────────────
DOCKER_MODE=false
UNIT_ONLY=false
INTEGRATION_ONLY=false
UI_ONLY=false
GENERATE_REPORT=true
OPEN_REPORT=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
RESULTS_DIR="$PROJECT_DIR/tests/results"
REPORT_FILE="$RESULTS_DIR/result_${TIMESTAMP}.md"

# ── Argument parsing ──────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --docker)          DOCKER_MODE=true ;;
        --unit-only)       UNIT_ONLY=true ;;
        --integration)     INTEGRATION_ONLY=true ;;
        --ui)              UI_ONLY=true ;;
        --no-report)       GENERATE_REPORT=false ;;
        --open)            OPEN_REPORT=true ;;
        --help|-h)
            echo ""
            echo "  Price Is Right — Test Suite Runner"
            echo ""
            echo "  Usage: ./scripts/testrun.sh [OPTIONS]"
            echo ""
            echo "  Options:"
            echo "    --docker          Run tests inside the app Docker container"
            echo "    --unit-only       Run only unit tests (test_core.py + test_agents.py)"
            echo "    --integration     Run only integration tests (test_integration.py)"
            echo "    --ui              Run only UI smoke tests (test_ui.py)"
            echo "    --no-report       Skip Markdown report generation"
            echo "    --open            Open the report in a browser after run"
            echo "    --help            Show this help"
            echo ""
            echo "  Reports are saved to: tests/results/result_YYYYMMDD_HHMMSS.md"
            echo ""
            exit 0
            ;;
        *) warn "Unknown option: $1" ;;
    esac
    shift
done

# ── Banner ────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${BLUE}╔══════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${BLUE}║   🧪  Price Is Right — Test Suite Runner                ║${RESET}"
echo -e "${BOLD}${BLUE}║   Autonomous 7-Agent AI Deal Hunter                     ║${RESET}"
echo -e "${BOLD}${BLUE}╚══════════════════════════════════════════════════════════╝${RESET}"
echo ""
info "Timestamp : $TIMESTAMP"
info "Project   : $PROJECT_DIR"
info "Report    : $REPORT_FILE"
echo ""

# ── Docker mode ───────────────────────────────────────────────────────────────
if [[ "$DOCKER_MODE" == "true" ]]; then
    header "Running tests inside Docker container"
    if ! docker compose -f "$PROJECT_DIR/docker-compose.yml" ps | grep -q "price-is-right-app.*Up"; then
        warn "App container is not running. Starting it first..."
        docker compose -f "$PROJECT_DIR/docker-compose.yml" up -d app
        sleep 5
    fi
    info "Executing test suite inside container..."
    docker compose -f "$PROJECT_DIR/docker-compose.yml" exec app \
        python3 tests/report_generator.py --output "/app/tests/results/result_${TIMESTAMP}.md"
    # Copy report out of container
    mkdir -p "$RESULTS_DIR"
    docker compose -f "$PROJECT_DIR/docker-compose.yml" cp \
        "app:/app/tests/results/result_${TIMESTAMP}.md" "$REPORT_FILE" 2>/dev/null || true
    if [[ -f "$REPORT_FILE" ]]; then
        success "Report copied from container: $REPORT_FILE"
    fi
    exit 0
fi

# ── Local mode ────────────────────────────────────────────────────────────────
cd "$PROJECT_DIR"

# Check Python
if ! command -v python3 &>/dev/null; then
    error "python3 not found. Please install Python 3.8+."
    exit 1
fi
PYTHON_VERSION=$(python3 --version 2>&1)
info "Python: $PYTHON_VERSION"

# Install test dependencies if missing
header "Checking test dependencies"
MISSING_DEPS=()
for pkg in unittest2 pydantic fastapi; do
    python3 -c "import ${pkg//-/_}" 2>/dev/null || MISSING_DEPS+=("$pkg")
done

# Core deps check (non-fatal)
for pkg in torch sentence_transformers chromadb gradio openai anthropic feedparser; do
    if ! python3 -c "import ${pkg//-/_}" 2>/dev/null; then
        warn "Optional package not installed: $pkg (related tests will be skipped)"
    else
        success "Found: $pkg"
    fi
done

# Install httpx for FastAPI test client if missing
if ! python3 -c "import httpx" 2>/dev/null; then
    warn "httpx not installed — API endpoint tests will be skipped"
    warn "Install with: sudo pip3 install httpx"
fi

# ── Determine which test files to run ─────────────────────────────────────────
header "Selecting test modules"
mkdir -p "$RESULTS_DIR"

if [[ "$UNIT_ONLY" == "true" ]]; then
    TEST_PATTERN="test_core.py test_agents.py"
    info "Mode: Unit tests only"
elif [[ "$INTEGRATION_ONLY" == "true" ]]; then
    TEST_PATTERN="test_integration.py"
    info "Mode: Integration tests only"
elif [[ "$UI_ONLY" == "true" ]]; then
    TEST_PATTERN="test_ui.py"
    info "Mode: UI smoke tests only"
else
    TEST_PATTERN="test_core.py test_agents.py test_integration.py test_ui.py"
    info "Mode: Full test suite"
fi

# ── Run individual test files with verbose output ─────────────────────────────
header "Running tests"
OVERALL_EXIT=0
CONSOLE_LOG="$RESULTS_DIR/console_${TIMESTAMP}.txt"

for test_file in $TEST_PATTERN; do
    test_path="$PROJECT_DIR/tests/$test_file"
    if [[ ! -f "$test_path" ]]; then
        warn "Test file not found: $test_path — skipping"
        continue
    fi

    module_name="${test_file%.py}"
    echo ""
    echo -e "${BOLD}  ▶ Running: $test_file${RESET}"
    echo "  $(printf '─%.0s' {1..50})"

    # Run with verbose output, capture both stdout and stderr
    set +e
    python3 -m pytest "$test_path" \
        --tb=short \
        --no-header \
        -v \
        --color=yes \
        2>&1 | tee -a "$CONSOLE_LOG"
    FILE_EXIT=${PIPESTATUS[0]}
    set -e

    if [[ $FILE_EXIT -eq 0 ]]; then
        success "$test_file — PASSED"
    else
        error "$test_file — FAILED (exit code $FILE_EXIT)"
        OVERALL_EXIT=$FILE_EXIT
    fi
done

# ── Generate Markdown report ──────────────────────────────────────────────────
if [[ "$GENERATE_REPORT" == "true" ]]; then
    header "Generating Markdown report"
    set +e
    python3 "$PROJECT_DIR/tests/report_generator.py" --output "$REPORT_FILE"
    REPORT_EXIT=$?
    set -e

    if [[ $REPORT_EXIT -eq 0 ]]; then
        success "Report generated: $REPORT_FILE"
    else
        warn "Report generator exited with code $REPORT_EXIT"
        warn "Partial report may have been written to: $REPORT_FILE"
    fi

    # Show report summary
    if [[ -f "$REPORT_FILE" ]]; then
        echo ""
        echo -e "${BOLD}  📄 Report Preview (first 40 lines):${RESET}"
        echo "  $(printf '─%.0s' {1..50})"
        head -40 "$REPORT_FILE" | sed 's/^/  /'
        echo ""
        echo -e "  ${CYAN}Full report: $REPORT_FILE${RESET}"
    fi
fi

# ── List all reports ──────────────────────────────────────────────────────────
header "All test reports"
if [[ -d "$RESULTS_DIR" ]] && ls "$RESULTS_DIR"/result_*.md &>/dev/null 2>&1; then
    echo ""
    ls -lt "$RESULTS_DIR"/result_*.md | head -10 | while read -r line; do
        echo "  $line"
    done
    REPORT_COUNT=$(ls "$RESULTS_DIR"/result_*.md 2>/dev/null | wc -l)
    echo ""
    info "Total reports stored: $REPORT_COUNT"
else
    warn "No reports found in $RESULTS_DIR"
fi

# ── Open report in browser ────────────────────────────────────────────────────
if [[ "$OPEN_REPORT" == "true" ]] && [[ -f "$REPORT_FILE" ]]; then
    if command -v xdg-open &>/dev/null; then
        xdg-open "$REPORT_FILE" &
    elif command -v open &>/dev/null; then
        open "$REPORT_FILE" &
    else
        warn "Cannot open browser automatically. Report at: $REPORT_FILE"
    fi
fi

# ── Final summary ─────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${BLUE}╔══════════════════════════════════════════════════════════╗${RESET}"
if [[ $OVERALL_EXIT -eq 0 ]]; then
    echo -e "${BOLD}${GREEN}║   ✅  ALL TESTS PASSED                                  ║${RESET}"
else
    echo -e "${BOLD}${RED}║   ❌  SOME TESTS FAILED — see report for details        ║${RESET}"
fi
echo -e "${BOLD}${BLUE}╚══════════════════════════════════════════════════════════╝${RESET}"
echo ""
if [[ "$GENERATE_REPORT" == "true" ]] && [[ -f "$REPORT_FILE" ]]; then
    echo -e "  ${CYAN}📄 Report: $REPORT_FILE${RESET}"
fi
echo ""

exit $OVERALL_EXIT
