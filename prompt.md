# 🎯 Price Is Right — Full Solution Prompt

> **Author:** Lalit Nayyar | lalitnayyar@gmail.com | +971508320336 | +919595353336
> **Repository:** https://github.com/lalitnayyar/priceisrightcapstone
> **Stack:** Python 3.11 · Gradio · FastAPI · ChromaDB · Docker Compose · PyTorch · OpenAI GPT-5 · Anthropic Claude · Pushover

---

## 🧠 Master Prompt

Build a **modular, Docker-based, multi-agent AI application** called **"The Price Is Right"** that:

1. **Watches RSS feeds** for products being published online (deals, listings, auctions)
2. **Estimates the true market price** of each product using an ensemble of AI models
3. **Sends a push notification** (via Pushover) when it finds a great opportunity (price significantly below estimated value)
4. Uses **7 collaborating AI agents** in a structured framework
5. Has a **Gradio folding-view dashboard** with a dark/light theme toggle
6. Has a **live Settings page** to configure all environment variables on the fly
7. Is fully **Docker-based** with deploy, start, stop, update, and patch scripts
8. Has a **comprehensive test suite** (118 tests) with timestamped Markdown reports

---

## 🏗️ Architecture Prompt

Design a modular Python package with the following structure:

```
priceisrightcapstone/
├── app/
│   ├── agents/          # All 7 agent modules
│   ├── core/            # Data models, RSS ingestion, RAG DB, framework
│   ├── models/          # PyTorch DNN definition
│   ├── ui/              # Gradio dashboard, settings page, theme system
│   ├── utils/           # Log formatting helpers
│   ├── api.py           # FastAPI REST API layer
│   └── main.py          # Entry point (--mode dashboard | api | init-rag)
├── tests/               # 118-test suite with timestamped .md reports
├── scripts/             # 10 bash scripts (deploy, start, stop, update, patch×4, diagnose, testrun)
├── Dockerfile           # python:3.11-slim, pre-downloads embedding models
├── docker-compose.yml   # 4 services: chromadb, app, api, rag-init
├── requirements.txt     # All Python dependencies
└── .env.example         # Template for all 24 environment variables
```

---

## 👥 7-Agent Framework Prompt

Implement exactly **7 agents** that collaborate in a pipeline. Each agent inherits from a base `Agent` class with `name`, `color`, `role`, and an abstract `run()` method.

### Agent 1 — Scanner Agent
- **Model:** GPT-5 (`gpt-4o-mini` or `gpt-5-mini`) with Structured Outputs
- **Input:** List of RSS feed URLs from environment variable `RSS_FEED_URLS`
- **Task:** Parse each RSS feed, extract product listings, use GPT-5 with JSON schema to identify the **5 best deal candidates** per scan
- **Output:** List of `Deal` objects with `title`, `price`, `url`, `description`, `source`
- **Key detail:** Use `response_format={"type": "json_object"}` or Pydantic structured output to get clean deal data from the LLM

### Agent 2 — Frontier Agent
- **Model:** GPT-5.1 (`gpt-4.1` or `gpt-4o`) + ChromaDB RAG
- **Input:** A `Deal` object
- **Task:** Query the ChromaDB vector store for the 5 most similar products by embedding similarity, then prompt GPT-5.1 with the retrieved context to estimate the true market price
- **Output:** `float` — estimated price in USD
- **Key detail:** Use `sentence-transformers/all-MiniLM-L6-v2` for embeddings. ChromaDB collection name: `products`. The RAG context improves price accuracy by grounding the LLM in real comparable products.

### Agent 3 — Specialist Agent
- **Model:** Fine-tuned Llama-3.2-3B hosted on Modal GPU (`modal.com`)
- **Input:** A `Deal` object
- **Task:** Call the Modal-hosted fine-tuned model endpoint to get a specialist price estimate. The fine-tuned model was trained specifically on product price prediction and "busts the frontier" — outperforming general LLMs on this narrow task.
- **Output:** `float` — estimated price in USD
- **Fallback:** If Modal is unavailable, fall back to a local heuristic based on title keyword matching
- **Key detail:** Use `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET` environment variables for authentication

### Agent 4 — Neural Network Agent
- **Model:** Deep Residual DNN (local PyTorch, no GPU required)
- **Input:** A `Deal` object (preprocessed to a feature vector)
- **Task:** Run the preprocessed deal through a 5-layer residual neural network to get a fast offline price estimate
- **Output:** `float` — estimated price in USD
- **Architecture:** Input → Linear(256) → ReLU → Residual blocks × 3 → Linear(1). Uses `Preprocessor` class to tokenise and vectorise the product title and description.
- **Key detail:** If no pre-trained weights file exists at `DNN_WEIGHTS_PATH`, the model initialises randomly and returns a heuristic estimate

### Agent 5 — Ensemble Agent
- **Model:** Weighted average combiner (no LLM)
- **Input:** Three price estimates from Agents 2, 3, 4
- **Task:** Combine the three estimates using configurable weights (default: Frontier 80%, Specialist 10%, DNN 10%). Calculate the discount percentage: `(ensemble_price - deal_price) / ensemble_price × 100`. If discount ≥ `DEAL_THRESHOLD` (default 50%), flag as a great deal.
- **Output:** `EnsembleResult` with `estimated_price`, `discount_pct`, `is_great_deal`, `weights_used`

### Agent 6 — Messaging Agent
- **Model:** Claude Sonnet (`claude-sonnet-4-5` or `claude-3-5-sonnet-20241022`) + Pushover API
- **Input:** A `Deal` object + `EnsembleResult`
- **Task:** Use Claude to craft a compelling, concise push notification message (max 200 chars). Send via Pushover API to the user's device. Include deal title, estimated savings, and URL.
- **Output:** `bool` — notification sent successfully
- **Key detail:** Use `PUSHOVER_USER` and `PUSHOVER_TOKEN` environment variables. Pushover API endpoint: `https://api.pushover.net/1/messages.json`

### Agent 7 — Planning Agent (Orchestrator)
- **Model:** GPT-5.1 (`gpt-4.1` or `gpt-4o`) as orchestrator
- **Input:** None (reads RSS feeds from env)
- **Task:** Coordinate the full pipeline: Scanner → [Frontier + Specialist + DNN in parallel] → Ensemble → [Messaging if great deal]. Log every step. Store results in `memory.json`. Run on a configurable interval (`SCAN_INTERVAL_MINUTES`, default 5).
- **Output:** List of `DealResult` objects
- **Key detail:** The Planning Agent uses GPT-5.1 to make high-level decisions about which deals to prioritise when multiple great deals are found simultaneously

---

## 🗄️ RAG Database Prompt

Build a ChromaDB-backed RAG database for product price context:

```python
# Collection: "products"
# Embedding model: sentence-transformers/all-MiniLM-L6-v2
# Documents: product titles + descriptions
# Metadata: {"price": float, "category": str, "source": str}
# Query: top-5 similar products by cosine similarity

# Initialisation: populate with ~200 sample products across categories:
# Electronics, Clothing, Books, Home & Garden, Sports, Toys, Automotive
# Price range: $5 to $2000
```

The RAG DB is initialised by running:
```bash
docker compose exec app python -m app.main --mode init-rag
```

---

## 🖥️ Dashboard UI Prompt

Build a **Gradio tabbed interface** with two tabs:

### Tab 1 — Dashboard
Four collapsible accordion sections:

1. **🤖 Agent Framework** — Status table showing all 7 agents with name, model, role, and colour-coded status badge (Ready / Running / Error)
2. **🔥 Deal Opportunities Found** — Gradio Dataframe showing deal title, URL, listed price, estimated price, discount %, and a "great deal" flag. Clicking a row re-sends the push notification.
3. **📋 Live Agent Logs** — Auto-refreshing HTML panel with ANSI-to-HTML colour conversion showing real-time agent activity. Large orange "🔍 Scan for Deals Now" button triggers an immediate scan.
4. **📊 RAG Vector Store** — Plotly 3D scatter plot of product embeddings reduced via t-SNE, colour-coded by product category. "Refresh RAG Plot" button re-renders.

### Tab 2 — Settings
Six collapsible accordion sections for live environment variable management:

1. **🔑 API Keys** — OpenAI, Anthropic, Pushover User/Token, Modal Token ID/Secret. Each has a "Test Connection" button that validates the key without saving.
2. **🤖 Agent Configuration** — Deal threshold %, scan interval, model names for Scanner/Frontier/Messaging agents, ensemble weights (must sum to 100)
3. **🧠 RAG Database** — ChromaDB path, results count, embedding model, visualisation max points
4. **🔔 Notifications** — Pushover sound, notification title, minimum interval between notifications
5. **📡 RSS Feeds** — Multi-line textarea for feed URLs, max deals per scan
6. **⚙️ Advanced** — Memory file path, log level, preprocessor model, DNN weights path, dashboard/API ports

**Action buttons:** 💾 Save & Apply (writes to `.env` + applies to running process) · ✅ Validate Only · 🔄 Reset to Defaults · 📤 Export Settings (JSON, secrets redacted) · 📥 Import Settings · 📄 .env Preview (secrets masked)

---

## 🎨 Theme System Prompt

Create a **unified colour scheme** in `app/ui/theme.py` with:

```python
BRAND = {"primary": "#FF6B35", "secondary_dark": "#4ECDC4", "secondary_light": "#0969DA"}

DARK_THEME = {
    "bg_page": "#0D1117",      # GitHub-dark page background
    "bg_surface": "#161B22",   # Card/panel background
    "bg_surface2": "#1C2128",  # Input field background
    "bg_log": "#0D1117",       # Log panel (always dark)
    "text_primary": "#E6EDF3", # Main body text
    "text_secondary": "#A0ADB8", # Muted/description text
    "border": "#30363D",       # Panel borders
    "accent": "#FF6B35",       # Brand orange (same in both themes)
    "tab_active": "#FF6B35",   # Active tab underline
}

LIGHT_THEME = {
    "bg_page": "#F6F8FA",
    "bg_surface": "#FFFFFF",
    "bg_surface2": "#F0F2F5",
    "bg_log": "#0D1117",       # Log panel stays dark for ANSI compatibility
    "text_primary": "#1F2328",
    "text_secondary": "#57606A",
    "border": "#D0D7DE",
    "accent": "#FF6B35",
    "tab_active": "#FF6B35",
}
```

**Dark/Light toggle:** A compact pill button (28px tall, 95px wide) in the top-right corner of the header. One click switches the entire app — all accordions, inputs, tables, buttons, log panel, and footer — via JavaScript `classList.toggle` on `document.body`.

**WCAG AA compliance:** All text/background pairs must achieve ≥ 4.5:1 contrast ratio. Primary button text must be `#1A1A1A` (dark) on the orange `#FF6B35` background (ratio: 6.14:1). Placeholder text must be `#8B949E` (ratio: 5.26:1).

**Critical CSS fix:** Gradio's Svelte-compiled components inject inline `background: white`. Override with high-specificity selectors:
```css
div[data-testid="accordion"] > div,
div.accordion .gap, div.accordion .block,
div.accordion .form, div.accordion .wrap
{ background: {bg_surface} !important; }
```

---

## 🐳 Docker Configuration Prompt

### Dockerfile
```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y build-essential curl git libgomp1
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
# Pre-download embedding model at build time (avoids runtime delay)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
COPY app/ ./app/
COPY scripts/ ./scripts/
RUN mkdir -p /app/data /app/products_vectorstore /app/logs
RUN find /app/scripts -name '*.sh' -exec chmod +x {} +
```

### docker-compose.yml (4 services)

**chromadb service:**
```yaml
image: chromadb/chroma:0.5.20
ports: ["8001:8000"]
environment:
  IS_PERSISTENT: "TRUE"
  PERSIST_DIRECTORY: /chroma/chroma
healthcheck:
  # CRITICAL: chromadb/chroma image has NO curl and NO wget.
  # Use Python TCP socket probe (Python is always present).
  # Must be a single-line string — multi-line YAML block scalars break CMD-SHELL.
  test: ["CMD-SHELL", "python3 -c \"import socket,sys; s=socket.create_connection(('localhost',8000),timeout=5); s.sendall(b'GET /api/v1/heartbeat HTTP/1.0\\r\\nHost: localhost\\r\\n\\r\\n'); r=s.recv(128).decode('utf-8','ignore'); s.close(); sys.exit(0 if '200' in r or 'nanosecond' in r.lower() else 1)\""]
  interval: 15s
  timeout: 10s
  retries: 20
  start_period: 120s
```

**app and api services:**
```yaml
depends_on:
  chromadb:
    condition: service_started   # NOT service_healthy — avoids cascading failure
```

**rag-init service:**
```yaml
# One-shot container — but NEVER call with 'docker compose run'.
# docker compose run re-evaluates depends_on health conditions at runtime.
# Instead, exec into the running app container:
#   docker compose exec app python -m app.main --mode init-rag
restart: "no"
```

---

## 🔧 Scripts Prompt

Create **10 bash scripts** in `scripts/`:

| Script | Purpose | Key Behaviour |
|--------|---------|---------------|
| `deploy.sh` | First-time full deployment | Build → start chromadb → wait → start app+api → RAG init via exec |
| `start.sh` | Start containers (with build) | `docker compose up -d --build` |
| `stop.sh` | Stop containers | `--remove-volumes` flag to also wipe data |
| `update.sh` | Pull latest code + rolling redeploy | git pull → build → restart app+api → RAG init via exec → health check |
| `diagnose.sh` | Pre-flight PASS/FAIL/WARN checks | Docker version, .env file, API key format, port availability |
| `patch.sh` | Apply Fixes 1–3 idempotently | Remove `COPY data/`, remove `version:`, add `--build` to start.sh |
| `chromadb_patch.sh` | Apply Fixes 4–5 | Replace curl/wget probe with Python TCP probe |
| `rag_init_patch.sh` | Apply Fix 6 | Replace `docker compose run rag-init` with `docker compose exec` |
| `theme_patch.sh` | Verify/apply theme system | 13 checks: theme.py exists, imports, toggle wired, syntax OK |
| `testrun.sh` | Run test suite + generate report | `pytest` → `tests/reports/result_YYYYMMDD_HHMMSS.md` |

**All scripts must be:**
- Idempotent (safe to run multiple times)
- Support `--check` dry-run mode (diagnose only, no changes)
- Print colour-coded PASS/FAIL/WARN/FIXED status lines
- Exit with code 0 on success, 1 on failure

---

## 🐛 Known Issues & Fixes Prompt

### Fix 1 — `COPY data/` Build Failure
**Problem:** `COPY data/ ./data/` fails if `data/` doesn't exist in the repo (it's runtime-generated).
**Fix:** Remove `COPY data/` from Dockerfile. Add `RUN mkdir -p /app/data` instead.

### Fix 2 — Obsolete `version:` Key Warning
**Problem:** `version: "3.9"` in docker-compose.yml causes `WARN` on every Docker Compose v2+ command.
**Fix:** Remove the `version:` key entirely.

### Fix 3 — `start.sh` Fails on Fresh Clone
**Problem:** `docker compose up -d` without `--build` tries to use a non-existent image.
**Fix:** Change to `docker compose up -d --build`.

### Fix 4 — ChromaDB Permanently Unhealthy (curl missing)
**Problem:** `chromadb/chroma` image has no `curl`. Healthcheck `CMD curl -f http://localhost:8000/api/v1/heartbeat` fails instantly on every probe. After 5 retries, container is marked `unhealthy`, blocking `app` and `api`.
**Fix:** Replace `CMD curl` with `CMD-SHELL wget` probe.

### Fix 5 — ChromaDB Still Unhealthy (wget also missing)
**Problem:** Many `chromadb/chroma:0.5.x` builds also lack `wget`. The API endpoint also changed to `/api/v2/heartbeat` in newer versions.
**Fix:** Replace with a pure Python TCP socket probe (Python is always present in the ChromaDB image). Use a **single-line string** — multi-line YAML `|` block scalars are unreliable with `CMD-SHELL`. Try both `/api/v2/heartbeat` and `/api/v1/heartbeat`.

### Fix 6 — `docker compose run rag-init` Blocks on `service_healthy`
**Problem:** Even with `condition: service_started` in docker-compose.yml, `docker compose run` **re-evaluates `depends_on` health conditions at runtime**. When ChromaDB is `unhealthy` (Docker internal probe), `docker compose run rag-init` throws "dependency failed to start".
**Fix:** Replace `docker compose run --rm rag-init` with `docker compose exec -T app python -m app.main --mode init-rag` in both `deploy.sh` and `update.sh`. This execs into the already-running `app` container, bypassing health check gating entirely.

---

## 🧪 Test Suite Prompt

Create a **pytest test suite** with 118 tests across 3 files:

### `tests/test_core.py` (36 tests)
- `TestDealModel` — Deal dataclass, discount calculation, `is_good_deal()`, string repr
- `TestPreprocessor` — Text cleaning, price extraction, normalisation (mock SentenceTransformer)
- `TestLogUtils` — ANSI colour codes, log formatting, timestamps
- `TestItemsModule` — Item parsing, tokenisation, price cleaning
- `TestDealsModule` — RSS feed parsing, Deal creation, filtering
- `TestMemoryModule` — JSON persistence, read/write/update

### `tests/test_agents.py` (49 tests)
Mock all LLM/API calls with `unittest.mock.patch`. Test each agent in isolation:
- `TestBaseAgent` — Abstract interface, colour constants, name/role attributes
- `TestScannerAgent` — RSS fetch mock, GPT structured output, deal extraction
- `TestFrontierAgent` — ChromaDB query mock, GPT price estimation, RAG context
- `TestSpecialistAgent` — Modal GPU mock, fine-tuned model inference, fallback
- `TestNeuralNetworkAgent` — DNN forward pass, weight loading, price regression
- `TestEnsembleAgent` — Weighted average (80/10/10), discount calc, threshold
- `TestMessagingAgent` — Pushover mock, Claude message crafting, notification
- `TestPlanningAgent` — Agent orchestration, pipeline flow, deal filtering

### `tests/test_ui.py` (33 tests)
- `TestThemeModule` — Palette keys present, CSS generation, WCAG contrast ratios (≥ 4.5:1 for all 16 text/bg pairs)
- `TestSettingsPageModule` — Import, build callable, env file read/write, validation
- `TestDashboardModule` — Class exists, `build()` method, `run()` method

### Report Generator (`tests/generate_report.py`)
Run with `python3 tests/generate_report.py`. Produces:
- `tests/reports/result_YYYYMMDD_HHMMSS.md` — Full Markdown report with summary table, per-suite breakdown, WCAG audit table, module health table
- `tests/results/console_YYYYMMDD_HHMMSS.txt` — Raw pytest console output

---

## 🌍 Environment Variables Prompt

All 24 variables must be documented in `.env.example`:

```bash
# === API Keys ===
OPENAI_API_KEY=sk-...           # Required: Scanner Agent (GPT-5) + Frontier Agent (GPT-5.1)
ANTHROPIC_API_KEY=sk-ant-...    # Required: Messaging Agent (Claude Sonnet)
PUSHOVER_USER=...               # Required: Push notification recipient
PUSHOVER_TOKEN=...              # Required: Push notification app token
MODAL_TOKEN_ID=ak-...           # Optional: Specialist Agent (fine-tuned Llama on Modal GPU)
MODAL_TOKEN_SECRET=...          # Optional: Specialist Agent

# === Agent Configuration ===
DEAL_THRESHOLD=50               # Minimum discount % to trigger notification (default: 50)
SCAN_INTERVAL_MINUTES=5         # How often to scan RSS feeds (default: 5)
SCANNER_MODEL=gpt-4o-mini       # Model for Scanner Agent
FRONTIER_MODEL=gpt-4o           # Model for Frontier Agent
MESSAGING_MODEL=claude-sonnet-4-5  # Model for Messaging Agent
ENSEMBLE_FRONTIER_WEIGHT=0.8    # Frontier weight in ensemble (default: 0.8)
ENSEMBLE_SPECIALIST_WEIGHT=0.1  # Specialist weight (default: 0.1)
ENSEMBLE_DNN_WEIGHT=0.1         # DNN weight (default: 0.1)

# === RAG Database ===
CHROMA_DB_PATH=./products_vectorstore
CHROMA_HOST=chromadb            # Docker service name
CHROMA_PORT=8000
CHROMA_RESULTS_COUNT=5          # Number of similar products to retrieve
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# === RSS Feeds ===
RSS_FEED_URLS=https://www.dealnews.com/rss.html,https://feeds.feedburner.com/techbargains

# === Application ===
MEMORY_FILE=./data/memory.json
LOG_LEVEL=INFO
DASHBOARD_PORT=7860
API_PORT=8000
DNN_WEIGHTS_PATH=./data/dnn_weights.pt
```

---

## 📦 Requirements Prompt

Key Python packages required:

```
# Core AI/ML
openai>=1.0.0
anthropic>=0.25.0
chromadb>=0.5.0
sentence-transformers>=2.7.0
torch>=2.0.0
modal>=0.62.0

# Web/API
gradio>=4.0.0
fastapi>=0.110.0
uvicorn>=0.29.0

# Data
feedparser>=6.0.0
requests>=2.31.0
numpy>=1.26.0
pandas>=2.2.0
plotly>=5.20.0
scikit-learn>=1.4.0

# Utils
python-dotenv>=1.0.0
pydantic>=2.0.0
litellm>=1.30.0
```

---

## 🚀 Quick Start Prompt

After cloning, the user should be able to run the full application with:

```bash
git clone https://github.com/lalitnayyar/priceisrightcapstone.git
cd priceisrightcapstone
cp .env.example .env
# Edit .env: add OPENAI_API_KEY, ANTHROPIC_API_KEY, PUSHOVER_USER, PUSHOVER_TOKEN
./scripts/diagnose.sh      # Pre-flight: check Docker, .env, ports
./scripts/deploy.sh        # Build images + start all services + init RAG DB
# Dashboard: http://localhost:7860
# API Docs:  http://localhost:8000/docs
# ChromaDB:  http://localhost:8001/api/v1/heartbeat
```

To update after a code change:
```bash
./scripts/update.sh        # git pull + rebuild + rolling restart
```

To run the test suite:
```bash
python3 tests/generate_report.py
# Report: tests/reports/result_YYYYMMDD_HHMMSS.md
```

---

## 📊 Project Statistics

| Metric | Value |
|--------|-------|
| Total Python files | 33 |
| Total shell scripts | 10 |
| Total lines of code | ~8,100 |
| Test cases | 118 (100% pass rate) |
| Docker services | 4 (chromadb, app, api, rag-init) |
| Docker volumes | 3 (chromadb_data, app_data, rag_store) |
| Environment variables | 24 |
| Agent count | 7 |
| Known issues documented & fixed | 6 |
| WCAG AA contrast pairs verified | 16 |

---

## 🏷️ Disclaimer

This project was designed and built by **Lalit Nayyar**.

| Contact | Detail |
|---------|--------|
| Name | Lalit Nayyar |
| Email | lalitnayyar@gmail.com |
| Phone (UAE) | +971508320336 |
| Phone (India) | +919595353336 |
| GitHub | https://github.com/lalitnayyar |
| Repository | https://github.com/lalitnayyar/priceisrightcapstone |
