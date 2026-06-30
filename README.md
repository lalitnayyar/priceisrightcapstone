# 🎯 The Price Is Right — Multi-Agent Deal Hunter

![Tabbed Dashboard Overview](assets/screenshot_tabbed_overview.png)

A modular, Docker-based application that uses a sophisticated **7-agent AI framework** to hunt for online deals, estimate true product values using RAG and fine-tuned models, and send push notifications for the best opportunities.

---

## 🌟 Architecture Overview

The system is built around a collaborative 7-agent framework. Each agent has a specific responsibility, working together to identify, evaluate, and notify you about great deals.

![Architecture Diagram](assets/architecture_diagram.png)

### The 7 Agents

| # | Agent | Model / Technology | Role & Responsibility |
|---|-------|--------------------|-----------------------|
| 1 | **Scanner Agent** | GPT-5 (gpt-5-mini) + Structured Outputs | Monitors RSS feeds (DealNews, Slickdeals) and uses structured outputs to extract the 5 most promising deals with clear prices and descriptions. |
| 2 | **Frontier Agent** | GPT-5.1 + ChromaDB RAG | Embeds product descriptions and queries a massive ChromaDB vector store for similar products, using GPT-5.1 to estimate prices based on that context. |
| 3 | **Specialist Agent** | Fine-tuned Llama-3.2-3B (Modal) | A "frontier-busting" specialist agent deployed on Modal GPU infrastructure with a PEFT adapter for highly accurate, domain-specific price estimation. |
| 4 | **Neural Network Agent** | Deep Residual DNN (PyTorch) | A local deep residual neural network that provides fast, offline price regression directly from text features. |
| 5 | **Ensemble Agent** | Weighted Combiner | Orchestrates the Frontier, Specialist, and Neural Network agents, weighting their outputs (80/10/10) to produce a highly accurate combined price estimate. |
| 6 | **Messaging Agent** | Claude Sonnet + Pushover | Uses Anthropic's Claude Sonnet to craft engaging 2-3 sentence push notifications and delivers them directly to your phone via the Pushover API. |
| 7 | **Planning Agent** | GPT-5.1 Orchestrator | The top-level controller that manages the workflow, evaluates the final discount against a configured threshold (e.g., $50), and triggers notifications. |

---

## 🚀 Key Features & Functionality

### 1. Live Settings & Configuration Manager
![Settings - API Keys](assets/screenshot_settings_api_keys.png)
A dedicated Settings tab allows you to manage all environment variables on the fly without touching the `.env` file directly:
- **API Key Management**: Securely enter OpenAI, Anthropic, Pushover, and Modal keys.
- **Connection Testing**: Instantly verify your API keys and database connections with built-in test buttons.
- **Agent Configuration**: Adjust the deal threshold, scan interval, agent models, and ensemble weights dynamically.
- **Import/Export**: Export your configuration to JSON (secrets are automatically redacted) or import an existing configuration.
- **Live Application**: Changes to thresholds, models, and keys are applied to the running process immediately—no restart required!

![Settings - Agent Config](assets/screenshot_settings_agent_config.png)

### 2. Folding View Dashboard
A sleek, interactive Gradio UI with collapsible accordion sections:
- **Agent Framework Status**: Real-time status of all 7 agents.
- **Deal Opportunities Table**: View identified deals, estimated values, and discounts. Click any row to re-send a push notification.
- **Live Agent Logs**: Real-time streaming logs with ANSI-to-HTML color rendering so you can watch the agents think and collaborate.

### 3. 3D RAG Vector Store Visualisation
![RAG Plot](assets/screenshot_rag_plot.png)
Explore the AI's "brain" with an interactive 3D t-SNE scatter plot of the ChromaDB product embedding space. Products are clustered by category (Electronics, Appliances, etc.), showing exactly how the Frontier Agent finds similar items for price comparison.

### 4. Automated Push Notifications
![Push Notification](assets/screenshot_push_notification.png)
When the Planning Agent identifies a deal where the discount exceeds your configured threshold, the Messaging Agent uses Claude to write a compelling alert and pushes it instantly to your smartphone.

### 5. Comprehensive REST API
![API Docs](assets/screenshot_api_docs.png)
A full FastAPI backend provides programmatic access to trigger runs, query the RAG database, and view surfaced opportunities. Complete with Swagger UI documentation.

### 6. Robust Docker Deployment
![Docker Services](assets/docker_services.png)
Fully containerised architecture using Docker Compose, separating the Gradio UI, FastAPI backend, and ChromaDB vector store into isolated, scalable services with persistent named volumes.

---

## 📖 User Guide

### Prerequisites
- Docker and Docker Compose installed on your host machine.
- **OpenAI API Key** (for Scanner and Frontier agents).
- **Anthropic API Key** (for Claude message crafting).
- **Pushover Account** (User Key and App Token for notifications).
- *(Optional)* Modal Account for the fine-tuned Specialist Agent.

### 1. Setup & Configuration

Clone the repository and set up your environment variables:

```bash
git clone https://github.com/lalitnayyar/priceisrightcapstone.git
cd priceisrightcapstone
cp .env.example .env
```

*Note: You can leave the API keys blank in the `.env` file and configure them later via the Settings UI.*

### 2. Pre-Deployment Diagnostics

Run the built-in diagnostic script to ensure your environment is configured correctly. It will check your `.env`, file structure, Python syntax, and Docker setup, providing a PASS/FAIL/WARN report.

```bash
./scripts/diagnose.sh
```

### 3. Deployment

Deploy the entire stack using the provided script. This will build the Docker images, start the services, and initialise the RAG database with sample product data.

```bash
./scripts/deploy.sh
```

### 4. Accessing the Application

Once deployed, access the services via your browser:

- **Dashboard & Settings**: [http://localhost:7860](http://localhost:7860)
- **API Server**: [http://localhost:8000](http://localhost:8000)
- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

### 5. Managing Settings via UI

1. Open the Dashboard at `http://localhost:7860`.
2. Click the **⚙️ Settings** tab.
3. Enter your API keys in the **API Keys** section and click the "Test" buttons to verify they work.
4. Adjust the **Deal Threshold** (e.g., to $100) in the **Agent Configuration** section.
5. Click **💾 Save & Apply Settings**. The new threshold and keys are immediately active for the next scan cycle.

### 6. Managing the Services

Use the provided scripts to manage the application lifecycle:

- **Start existing containers**: `./scripts/start.sh`
- **Stop all containers**: `./scripts/stop.sh`
- **Stop and wipe all data**: `./scripts/stop.sh --remove-volumes`
- **View live logs**: `docker compose logs -f app`

---

## 📁 Project Structure

```text
priceisrightcapstone/
├── app/
│   ├── agents/          # The 7 agent modules
│   ├── core/            # Data models, RSS ingestion, RAG DB, Framework orchestrator
│   ├── models/          # PyTorch Deep Neural Network definition
│   ├── ui/              # Gradio UI: dashboard.py and settings_page.py
│   ├── utils/           # Log formatting and HTML helpers
│   ├── api.py           # FastAPI REST endpoints
│   └── main.py          # Application entry point
├── assets/              # Documentation screenshots and diagrams
├── data/                # Persistent storage (memory.json, model weights)
├── products_vectorstore/# ChromaDB persistent storage volume
├── scripts/             # Bash scripts for deployment and diagnostics
├── docker-compose.yml   # Docker services configuration
├── Dockerfile           # Main application container definition
└── requirements.txt     # Python dependencies
```

---

## 📝 Disclaimer

**Author**: Lalit Nayyar  
**Email**: lalitnayyar@gmail.com  
**Phone**: +971508320336 / +919595353336  

*This project is a capstone demonstration of multi-agent LLM orchestration, RAG integration, and fine-tuned model deployment.*
