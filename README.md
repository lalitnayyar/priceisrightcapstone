# 🎯 The Price Is Right — Multi-Agent Deal Hunter

A modular, Docker-based application that uses a 7-agent AI framework to hunt for online deals, estimate true product values, and send push notifications for the best opportunities.

## 🌟 Architecture Overview

The system is built around a collaborative 7-agent framework:

1. **Scanner Agent (GPT-5)**: Monitors RSS feeds and uses Structured Outputs to identify the 5 most promising deals with clear prices and detailed descriptions.
2. **Frontier Agent (RAG + GPT-5.1)**: Embeds product descriptions, queries a massive ChromaDB vector store for similar products, and uses GPT-5.1 to estimate prices based on that context.
3. **Specialist Agent (Fine-tuned LLM)**: A "frontier-busting" specialist agent that calls a fine-tuned Llama-3.2-3B model (with PEFT adapter) deployed on Modal GPU infrastructure.
4. **Neural Network Agent (DNN)**: A local deep residual neural network that provides fast, offline price regression from text features.
5. **Ensemble Agent (Combiner)**: Orchestrates the Frontier, Specialist, and Neural Network agents, weighting their outputs (80/10/10) to produce a highly accurate combined price estimate.
6. **Messaging Agent (Claude + Pushover)**: Uses Anthropic's Claude Sonnet to craft engaging 2-3 sentence push notifications and delivers them via the Pushover API.
7. **Planning Agent (Orchestrator)**: The top-level controller that manages the workflow, evaluates the final discount against a configured threshold (e.g., $50), and triggers notifications.

## 🚀 Features

- **Folding View Dashboard**: A sleek Gradio UI with collapsible accordion sections for agent status, live logs, opportunities table, and 3D RAG vector space visualisation.
- **Dockerized Deployment**: Fully containerised with Docker Compose for easy deployment.
- **REST API**: FastAPI backend for programmatic access to the deal-hunting workflow and RAG database.
- **Automated Scanning**: Runs an autonomous deal-hunting cycle every 5 minutes.
- **Live Log Streaming**: Real-time agent logs with ANSI-to-HTML color rendering in the browser.

## 🛠️ Prerequisites

- Docker and Docker Compose
- OpenAI API Key (for GPT-5 and GPT-5.1)
- Anthropic API Key (for Claude message crafting)
- Pushover Account (User Key and App Token)
- Modal Account (optional, for the fine-tuned Specialist Agent)

## ⚙️ Setup & Configuration

1. Clone the repository.
2. Copy the environment template:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` and add your API keys:
   ```env
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...
   PUSHOVER_USER=...
   PUSHOVER_TOKEN=...
   DEAL_THRESHOLD=50
   ```

## 🩺 Diagnostics

Before deploying, run the diagnostic script to ensure your environment is configured correctly:

```bash
./scripts/diagnose.sh
```

This will test your `.env` configuration, file structure, Python syntax, and Docker setup, providing a PASS/FAIL/WARN report.

## 🚢 Deployment

Deploy the entire stack using the provided script:

```bash
./scripts/deploy.sh
```

This script will:
1. Validate your `.env` file.
2. Build the Docker images.
3. Start the ChromaDB, FastAPI, and Gradio containers.
4. Initialise the RAG database with sample product data.

### Other Scripts

- `./scripts/start.sh` — Start existing containers without rebuilding.
- `./scripts/stop.sh` — Stop all containers (use `--remove-volumes` to wipe data).

## 🖥️ Usage

Once deployed, access the services at:

- **Dashboard**: http://localhost:7860
- **API Server**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

### Disclaimer

**Author**: Lalit Nayyar  
**Email**: lalitnayyar@gmail.com  
**Phone**: +971508320336 / +919595353336  

*This project is a capstone demonstration of multi-agent LLM orchestration, RAG integration, and fine-tuned model deployment.*
