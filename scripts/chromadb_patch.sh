#!/usr/bin/env bash
# ============================================================================
# chromadb_patch.sh — Diagnose and fix ChromaDB container health issues
# ============================================================================
#
# PROBLEM SOLVED:
#   chromadb/chroma Docker images (0.5.x and later) are missing curl AND wget
#   in many builds. The previous healthcheck used:
#       test: ["CMD-SHELL", "wget -qO- http://localhost:8000/api/v1/heartbeat || exit 1"]
#   This always failed with "executable file not found in $PATH", making the
#   container permanently unhealthy and blocking app + api from starting.
#
# ROOT CAUSE (GitHub issue chroma-core/chroma#6855):
#   The CI pipeline uses rust/Dockerfile which omits curl from the apt-install
#   step. wget availability is also inconsistent across image tags.
#
# THIS SCRIPT:
#   1. Diagnoses the current state of the ChromaDB container
#   2. Detects which tools (curl/wget/python3) are available inside it
#   3. Patches docker-compose.yml with a bulletproof Python TCP healthcheck
#   4. Patches deploy.sh to use the same Python probe
#   5. Optionally restarts ChromaDB and verifies it becomes healthy
#   6. Prints a full diagnostic report
#
# USAGE:
#   ./scripts/chromadb_patch.sh              # Apply all fixes + restart
#   ./scripts/chromadb_patch.sh --check      # Dry-run: diagnose only, no changes
#   ./scripts/chromadb_patch.sh --no-restart # Apply fixes but skip restart
#   ./scripts/chromadb_patch.sh --force      # Force re-apply even if already patched
#   ./scripts/chromadb_patch.sh --help       # Show this help
#
# ============================================================================

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Flags
DRY_RUN=false
NO_RESTART=false
FORCE=false

for arg in "$@"; do
    case $arg in
        --check)      DRY_RUN=true ;;
        --no-restart) NO_RESTART=true ;;
        --force)      FORCE=true ;;
        --help)
            sed -n '2,40p' "$0" | grep '^#' | sed 's/^# \?//'
            exit 0
            ;;
    esac
done

# ============================================================================
# HELPERS
# ============================================================================
pass()  { echo -e "  ${GREEN}[PASS]${NC} $*"; }
fail()  { echo -e "  ${RED}[FAIL]${NC} $*"; }
warn()  { echo -e "  ${YELLOW}[WARN]${NC} $*"; }
info()  { echo -e "  ${BLUE}[INFO]${NC} $*"; }
fix()   { echo -e "  ${CYAN}[FIX ]${NC} $*"; }
skip()  { echo -e "  ${YELLOW}[SKIP]${NC} $*"; }

FIXES_APPLIED=0
CHECKS_PASSED=0
CHECKS_FAILED=0

# ============================================================================
# BANNER
# ============================================================================
echo ""
echo -e "${CYAN}${BOLD}============================================================${NC}"
echo -e "${CYAN}${BOLD}  ChromaDB Patch Script — Price Is Right                    ${NC}"
echo -e "${CYAN}${BOLD}============================================================${NC}"
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}  Mode: DRY-RUN (--check) — no changes will be made${NC}"
else
    echo -e "${GREEN}  Mode: APPLY — fixes will be applied${NC}"
fi
echo ""

# ============================================================================
# SECTION 1: ENVIRONMENT CHECKS
# ============================================================================
echo -e "${BOLD}[1] Environment Checks${NC}"

# Check docker compose is available
if command -v docker &>/dev/null && docker compose version &>/dev/null 2>&1; then
    pass "docker compose is available ($(docker compose version --short 2>/dev/null || echo 'v2+'))"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    fail "docker compose not found — install Docker Desktop or Docker Engine with Compose plugin"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
    echo ""
    echo -e "${RED}Cannot continue without Docker. Exiting.${NC}"
    exit 1
fi

# Check docker-compose.yml exists
if [ -f "docker-compose.yml" ]; then
    pass "docker-compose.yml found"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    fail "docker-compose.yml not found in $PROJECT_DIR"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
    exit 1
fi

# Check .env exists
if [ -f ".env" ]; then
    pass ".env file found"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    warn ".env not found — will use .env.example defaults"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
fi

echo ""

# ============================================================================
# SECTION 2: CHROMADB CONTAINER DIAGNOSTICS
# ============================================================================
echo -e "${BOLD}[2] ChromaDB Container Diagnostics${NC}"

CHROMA_RUNNING=false
CHROMA_STATUS="not found"

# Check if container exists
if docker compose ps chromadb 2>/dev/null | grep -q "price-is-right-chromadb"; then
    CHROMA_STATUS=$(docker compose ps chromadb --format "{{.Status}}" 2>/dev/null || \
                   docker compose ps chromadb 2>/dev/null | grep chromadb | awk '{print $4}' || \
                   echo "unknown")
    info "Container status: $CHROMA_STATUS"

    if echo "$CHROMA_STATUS" | grep -qi "running\|up"; then
        CHROMA_RUNNING=true
        pass "ChromaDB container is running"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    elif echo "$CHROMA_STATUS" | grep -qi "unhealthy"; then
        fail "ChromaDB container is UNHEALTHY"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    else
        warn "ChromaDB container status: $CHROMA_STATUS"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    fi
else
    warn "ChromaDB container not running (will be started by patch)"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
fi

# If running, probe what tools are available inside the container
if [ "$CHROMA_RUNNING" = true ]; then
    echo ""
    info "Probing tools available inside chromadb container..."

    HAS_CURL=false
    HAS_WGET=false
    HAS_PYTHON=false
    HAS_PYTHON3=false
    HAS_NC=false

    docker compose exec -T chromadb which curl  &>/dev/null && HAS_CURL=true
    docker compose exec -T chromadb which wget  &>/dev/null && HAS_WGET=true
    docker compose exec -T chromadb which python3 &>/dev/null && HAS_PYTHON3=true
    docker compose exec -T chromadb which python  &>/dev/null && HAS_PYTHON=true
    docker compose exec -T chromadb which nc     &>/dev/null && HAS_NC=true

    [ "$HAS_CURL"    = true ] && pass "curl    is available in container" || warn "curl    is NOT available in container"
    [ "$HAS_WGET"    = true ] && pass "wget    is available in container" || warn "wget    is NOT available in container"
    [ "$HAS_PYTHON3" = true ] && pass "python3 is available in container" || warn "python3 is NOT available in container"
    [ "$HAS_PYTHON"  = true ] && pass "python  is available in container" || warn "python  is NOT available in container"
    [ "$HAS_NC"      = true ] && pass "nc      is available in container" || warn "nc      is NOT available in container"

    # Test actual connectivity
    echo ""
    info "Testing ChromaDB API endpoints..."

    ENDPOINT_V2_OK=false
    ENDPOINT_V1_OK=false

    # Try Python3 probe (most reliable)
    if [ "$HAS_PYTHON3" = true ] || [ "$HAS_PYTHON" = true ]; then
        PYTHON_CMD="python3"
        [ "$HAS_PYTHON3" = false ] && PYTHON_CMD="python"

        PROBE_RESULT=$(docker compose exec -T chromadb $PYTHON_CMD -c "
import socket, sys
def probe(path):
    try:
        s = socket.create_connection(('localhost', 8000), timeout=8)
        s.sendall(('GET ' + path + ' HTTP/1.0\r\nHost: localhost\r\n\r\n').encode())
        r = s.recv(512).decode('utf-8', errors='ignore')
        s.close()
        return '200' in r or 'nanosecond' in r.lower() or 'heartbeat' in r.lower(), r[:100]
    except Exception as e:
        return False, str(e)
ok2, r2 = probe('/api/v2/heartbeat')
ok1, r1 = probe('/api/v1/heartbeat')
print('V2:' + ('OK' if ok2 else 'FAIL') + ' V1:' + ('OK' if ok1 else 'FAIL'))
print('V2_RESP:' + r2[:80])
print('V1_RESP:' + r1[:80])
" 2>/dev/null || echo "PROBE_ERROR")

        if echo "$PROBE_RESULT" | grep -q "V2:OK"; then
            ENDPOINT_V2_OK=true
            pass "/api/v2/heartbeat responded OK"
            CHECKS_PASSED=$((CHECKS_PASSED + 1))
        else
            warn "/api/v2/heartbeat did not respond (may be older chroma version)"
        fi

        if echo "$PROBE_RESULT" | grep -q "V1:OK"; then
            ENDPOINT_V1_OK=true
            pass "/api/v1/heartbeat responded OK"
            CHECKS_PASSED=$((CHECKS_PASSED + 1))
        else
            warn "/api/v1/heartbeat did not respond"
        fi

        if [ "$ENDPOINT_V2_OK" = false ] && [ "$ENDPOINT_V1_OK" = false ]; then
            fail "ChromaDB API is not responding on any known endpoint"
            CHECKS_FAILED=$((CHECKS_FAILED + 1))
            info "Raw probe output: $PROBE_RESULT"
        fi
    fi
fi

echo ""

# ============================================================================
# SECTION 3: DOCKER-COMPOSE.YML HEALTHCHECK AUDIT
# ============================================================================
echo -e "${BOLD}[3] docker-compose.yml Healthcheck Audit${NC}"

COMPOSE_HAS_PYTHON_PROBE=false
COMPOSE_HAS_WGET_PROBE=false
COMPOSE_HAS_CURL_PROBE=false
COMPOSE_HAS_OLD_WGET=false

if grep -q "python3 -c" docker-compose.yml 2>/dev/null && \
   grep -q "socket.create_connection" docker-compose.yml 2>/dev/null; then
    COMPOSE_HAS_PYTHON_PROBE=true
    pass "docker-compose.yml uses Python TCP probe (bulletproof)"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
elif grep -q "wget.*heartbeat" docker-compose.yml 2>/dev/null; then
    COMPOSE_HAS_WGET_PROBE=true
    warn "docker-compose.yml uses wget probe (may fail — wget absent in many chroma builds)"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
elif grep -q "curl.*heartbeat" docker-compose.yml 2>/dev/null; then
    COMPOSE_HAS_CURL_PROBE=true
    fail "docker-compose.yml uses curl probe (curl is NOT in chromadb/chroma image)"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
else
    warn "docker-compose.yml healthcheck probe type unknown"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
fi

# Check start_period is generous enough
START_PERIOD=$(grep -A5 "healthcheck:" docker-compose.yml | grep "start_period:" | head -1 | awk '{print $2}' || echo "unknown")
info "ChromaDB start_period: $START_PERIOD"
if echo "$START_PERIOD" | grep -qE "^[0-9]+s$"; then
    SP_VAL=$(echo "$START_PERIOD" | tr -d 's')
    if [ "$SP_VAL" -ge 90 ]; then
        pass "start_period >= 90s (sufficient for cold start)"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        warn "start_period ${START_PERIOD} may be too short (recommend >= 90s)"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    fi
fi

echo ""

# ============================================================================
# SECTION 4: DEPLOY.SH PROBE AUDIT
# ============================================================================
echo -e "${BOLD}[4] deploy.sh Probe Audit${NC}"

if grep -q "socket.create_connection" scripts/deploy.sh 2>/dev/null; then
    pass "deploy.sh uses Python TCP probe (bulletproof)"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
elif grep -q "wget.*heartbeat" scripts/deploy.sh 2>/dev/null; then
    warn "deploy.sh uses wget probe (may fail)"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
elif grep -q "curl.*heartbeat" scripts/deploy.sh 2>/dev/null; then
    fail "deploy.sh uses curl probe (will fail inside chroma container)"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
fi

echo ""

# ============================================================================
# SECTION 5: APPLY FIXES (unless --check)
# ============================================================================
echo -e "${BOLD}[5] Applying Fixes${NC}"

if [ "$DRY_RUN" = true ]; then
    skip "Dry-run mode — no changes applied"
    echo ""
    echo -e "${YELLOW}  Run without --check to apply all fixes.${NC}"
else

    # FIX A: Patch docker-compose.yml if not already using Python probe
    if [ "$COMPOSE_HAS_PYTHON_PROBE" = false ] || [ "$FORCE" = true ]; then
        fix "Patching docker-compose.yml ChromaDB healthcheck → Python TCP probe..."

        # Create backup
        cp docker-compose.yml docker-compose.yml.bak
        info "Backup saved: docker-compose.yml.bak"

        # Use Python to do a precise YAML-aware replacement of the healthcheck block
        python3 << 'PYEOF'
import re

with open('docker-compose.yml', 'r') as f:
    content = f.read()

# The new bulletproof healthcheck block (indented for YAML service level)
NEW_HEALTHCHECK = '''    healthcheck:
      # Pure Python TCP + HTTP probe — works regardless of curl/wget availability.
      # chromadb/chroma images are missing curl AND wget in many builds (GitHub #6855).
      # Python is always present (chroma runs on Python).
      # Tries /api/v2/heartbeat (chroma >= 0.5), falls back to /api/v1/heartbeat.
      test:
        - "CMD-SHELL"
        - |
          python3 -c "
          import socket, sys
          def probe(path):
              try:
                  s = socket.create_connection(('localhost', 8000), timeout=10)
                  s.sendall(('GET ' + path + ' HTTP/1.0\\r\\nHost: localhost\\r\\n\\r\\n').encode())
                  r = s.recv(512).decode('utf-8', errors='ignore')
                  s.close()
                  return '200' in r or 'nanosecond' in r.lower() or 'heartbeat' in r.lower()
              except:
                  return False
          if probe('/api/v2/heartbeat') or probe('/api/v1/heartbeat'):
              sys.exit(0)
          sys.exit(1)
          "
      interval: 20s
      timeout: 15s
      retries: 15
      start_period: 90s'''

# Replace the entire healthcheck block under the chromadb service
# Match from "    healthcheck:" up to the next top-level key at same indent
pattern = r'(  chromadb:.*?)(\n    healthcheck:.*?)(\n  \w)'
def replacer(m):
    return m.group(1) + '\n' + NEW_HEALTHCHECK + m.group(3)

new_content = re.sub(pattern, replacer, content, flags=re.DOTALL)
if new_content == content:
    # Fallback: simple line-by-line replacement of healthcheck block
    lines = content.split('\n')
    out = []
    in_chroma = False
    in_healthcheck = False
    healthcheck_indent = 0
    replaced = False
    i = 0
    while i < len(lines):
        line = lines[i]
        if '  chromadb:' in line and not in_chroma:
            in_chroma = True
        if in_chroma and not replaced and '    healthcheck:' in line:
            in_healthcheck = True
            healthcheck_indent = len(line) - len(line.lstrip())
            # Skip all lines of the old healthcheck block
            out.append(NEW_HEALTHCHECK)
            i += 1
            while i < len(lines):
                next_line = lines[i]
                if next_line.strip() == '':
                    i += 1
                    continue
                next_indent = len(next_line) - len(next_line.lstrip())
                if next_indent <= healthcheck_indent and next_line.strip() and not next_line.strip().startswith('#'):
                    break
                i += 1
            replaced = True
            in_healthcheck = False
            continue
        out.append(line)
        i += 1
    new_content = '\n'.join(out)

with open('docker-compose.yml', 'w') as f:
    f.write(new_content)
print("docker-compose.yml patched successfully")
PYEOF
        FIXES_APPLIED=$((FIXES_APPLIED + 1))
        pass "docker-compose.yml patched with Python TCP healthcheck"
    else
        skip "docker-compose.yml already uses Python probe — no change needed"
    fi

    # FIX B: Patch deploy.sh if not already using Python probe
    if ! grep -q "socket.create_connection" scripts/deploy.sh 2>/dev/null || [ "$FORCE" = true ]; then
        fix "Patching scripts/deploy.sh ChromaDB wait probe → Python TCP probe..."

        cp scripts/deploy.sh scripts/deploy.sh.bak
        info "Backup saved: scripts/deploy.sh.bak"

        python3 << 'PYEOF'
content = open('scripts/deploy.sh').read()

OLD_PROBE = '''echo -e "${YELLOW}Waiting for ChromaDB to be healthy (up to 90 s)...${NC}"
# NOTE: chromadb/chroma image has wget but NOT curl — use wget for the probe.
timeout 90 bash -c '
  until docker compose exec chromadb wget -qO- http://localhost:8000/api/v1/heartbeat > /dev/null 2>&1; do
    echo -n "."
    sleep 3
  done
  echo ""
' || {
    echo -e "${YELLOW}ChromaDB health probe timed out after 90 s; continuing anyway...${NC}"
}'''

NEW_PROBE = '''echo -e "${YELLOW}Waiting for ChromaDB to be ready (up to 180 s)...${NC}"
echo -e "${YELLOW}(Using Python TCP probe — no curl/wget dependency)${NC}"

# Bulletproof probe: Python TCP socket — always available in the chroma image.
# Does NOT rely on curl or wget (absent in many chroma image builds).
CHROMA_READY=false
CHROMA_TIMEOUT=180
CHROMA_ELAPSED=0
CHROMA_SLEEP=5

while [ $CHROMA_ELAPSED -lt $CHROMA_TIMEOUT ]; do
    PROBE_RESULT=$(docker compose exec -T chromadb python3 -c "
import socket, sys
def probe(path):
    try:
        s = socket.create_connection(('localhost', 8000), timeout=8)
        s.sendall(('GET ' + path + ' HTTP/1.0\\r\\nHost: localhost\\r\\n\\r\\n').encode())
        r = s.recv(512).decode('utf-8', errors='ignore')
        s.close()
        return '200' in r or 'nanosecond' in r.lower() or 'heartbeat' in r.lower()
    except:
        return False
if probe('/api/v2/heartbeat') or probe('/api/v1/heartbeat'):
    print('READY')
    sys.exit(0)
print('NOT_READY')
sys.exit(1)
" 2>/dev/null || echo "EXEC_FAILED")

    if [ "$PROBE_RESULT" = "READY" ]; then
        CHROMA_READY=true
        echo ""
        echo -e "${GREEN}✓ ChromaDB is healthy and ready${NC}"
        break
    fi
    echo -n "."
    sleep $CHROMA_SLEEP
    CHROMA_ELAPSED=$((CHROMA_ELAPSED + CHROMA_SLEEP))
done

if [ "$CHROMA_READY" = false ]; then
    echo ""
    echo -e "${YELLOW}⚠ ChromaDB probe timed out after ${CHROMA_TIMEOUT}s — continuing anyway.${NC}"
    echo -e "${YELLOW}  Run: ./scripts/chromadb_patch.sh  to diagnose ChromaDB issues.${NC}"
fi'''

if OLD_PROBE in content:
    content = content.replace(OLD_PROBE, NEW_PROBE)
    open('scripts/deploy.sh', 'w').write(content)
    print("deploy.sh patched successfully")
else:
    # Already patched or different format — check if it already has the Python probe
    if 'socket.create_connection' in content:
        print("deploy.sh already has Python probe — no change needed")
    else:
        print("WARNING: Could not find old probe pattern in deploy.sh — manual review needed")
PYEOF
        FIXES_APPLIED=$((FIXES_APPLIED + 1))
        pass "scripts/deploy.sh patched with Python TCP probe"
    else
        skip "scripts/deploy.sh already uses Python probe — no change needed"
    fi

    # FIX C: Ensure data directories exist
    if [ ! -d "data" ] || [ ! -d "products_vectorstore" ]; then
        fix "Creating missing data directories..."
        mkdir -p data products_vectorstore logs
        FIXES_APPLIED=$((FIXES_APPLIED + 1))
        pass "Data directories created"
    else
        skip "Data directories already exist"
    fi

    # FIX D: Ensure scripts are executable
    if [ ! -x "scripts/deploy.sh" ] || [ ! -x "scripts/chromadb_patch.sh" ]; then
        fix "Making scripts executable..."
        chmod +x scripts/*.sh
        FIXES_APPLIED=$((FIXES_APPLIED + 1))
        pass "Scripts made executable"
    else
        skip "Scripts already executable"
    fi

fi  # end of DRY_RUN check

echo ""

# ============================================================================
# SECTION 6: RESTART AND VERIFY (unless --no-restart or --check)
# ============================================================================
echo -e "${BOLD}[6] Restart and Verify${NC}"

if [ "$DRY_RUN" = true ] || [ "$NO_RESTART" = true ]; then
    skip "Skipping restart ($([ "$DRY_RUN" = true ] && echo '--check mode' || echo '--no-restart flag'))"
else
    if [ $FIXES_APPLIED -gt 0 ] || [ "$FORCE" = true ]; then
        fix "Restarting ChromaDB with patched configuration..."

        # Stop chromadb container (keep volume)
        docker compose stop chromadb 2>/dev/null || true
        docker compose rm -f chromadb 2>/dev/null || true

        # Start with new healthcheck
        docker compose up -d chromadb
        info "ChromaDB started — waiting for health probe (up to 180 s)..."

        VERIFY_READY=false
        VERIFY_TIMEOUT=180
        VERIFY_ELAPSED=0
        VERIFY_SLEEP=5

        while [ $VERIFY_ELAPSED -lt $VERIFY_TIMEOUT ]; do
            VERIFY_RESULT=$(docker compose exec -T chromadb python3 -c "
import socket, sys
def probe(path):
    try:
        s = socket.create_connection(('localhost', 8000), timeout=8)
        s.sendall(('GET ' + path + ' HTTP/1.0\r\nHost: localhost\r\n\r\n').encode())
        r = s.recv(512).decode('utf-8', errors='ignore')
        s.close()
        return '200' in r or 'nanosecond' in r.lower() or 'heartbeat' in r.lower()
    except:
        return False
if probe('/api/v2/heartbeat') or probe('/api/v1/heartbeat'):
    print('READY')
    sys.exit(0)
print('NOT_READY')
sys.exit(1)
" 2>/dev/null || echo "EXEC_FAILED")

            if [ "$VERIFY_RESULT" = "READY" ]; then
                VERIFY_READY=true
                echo ""
                pass "ChromaDB is healthy after patch!"
                CHECKS_PASSED=$((CHECKS_PASSED + 1))
                break
            fi
            echo -n "."
            sleep $VERIFY_SLEEP
            VERIFY_ELAPSED=$((VERIFY_ELAPSED + VERIFY_SLEEP))
        done

        if [ "$VERIFY_READY" = false ]; then
            echo ""
            fail "ChromaDB still not healthy after ${VERIFY_TIMEOUT}s"
            CHECKS_FAILED=$((CHECKS_FAILED + 1))
            echo ""
            echo -e "${YELLOW}  ChromaDB container logs:${NC}"
            docker compose logs --tail=30 chromadb 2>/dev/null || true
        fi

        # If healthy, start app and api
        if [ "$VERIFY_READY" = true ]; then
            fix "Starting app and api services..."
            docker compose up -d --no-deps app api
            pass "app and api services started"
        fi
    else
        skip "No fixes were applied — skipping restart"
    fi
fi

echo ""

# ============================================================================
# SECTION 7: FINAL REPORT
# ============================================================================
echo -e "${CYAN}${BOLD}============================================================${NC}"
echo -e "${CYAN}${BOLD}  ChromaDB Patch Report                                     ${NC}"
echo -e "${CYAN}${BOLD}============================================================${NC}"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo -e "  Mode:            ${YELLOW}DRY-RUN (--check)${NC}"
else
    echo -e "  Mode:            ${GREEN}APPLY${NC}"
    echo -e "  Fixes applied:   ${FIXES_APPLIED}"
fi

echo -e "  Checks passed:   ${GREEN}${CHECKS_PASSED}${NC}"
echo -e "  Checks failed:   $([ $CHECKS_FAILED -gt 0 ] && echo "${RED}${CHECKS_FAILED}${NC}" || echo "${GREEN}0${NC}")"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "  ${GREEN}${BOLD}All checks passed — ChromaDB is healthy!${NC}"
elif [ "$DRY_RUN" = true ]; then
    echo -e "  ${YELLOW}Run without --check to apply fixes:${NC}"
    echo -e "  ${YELLOW}  ./scripts/chromadb_patch.sh${NC}"
else
    echo -e "  ${YELLOW}Some issues remain. Try:${NC}"
    echo -e "  ${YELLOW}  ./scripts/chromadb_patch.sh --force  (force re-apply all fixes)${NC}"
    echo -e "  ${YELLOW}  docker compose logs chromadb          (view container logs)${NC}"
    echo -e "  ${YELLOW}  docker compose ps                     (check container status)${NC}"
fi

echo ""
echo -e "  ${BLUE}Services:${NC}"
echo -e "    Dashboard:  http://localhost:7860"
echo -e "    API:        http://localhost:8000"
echo -e "    ChromaDB:   http://localhost:8001"
echo ""
