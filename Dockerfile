# ============================================================================
# Price Is Right — Multi-Agent Deal Hunter
# Dockerfile for the main application container
# ============================================================================

FROM python:3.11-slim

# Metadata
LABEL maintainer="Lalit Nayyar"
LABEL description="Price Is Right — 7-Agent AI Deal Hunter with RAG + GPT-5 + Fine-tuned LLM"
LABEL version="1.0.0"

# ---------------------------------------------------------------------------
# System dependencies
# ---------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Python environment
# ---------------------------------------------------------------------------
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ---------------------------------------------------------------------------
# Working directory
# ---------------------------------------------------------------------------
WORKDIR /app

# ---------------------------------------------------------------------------
# Install Python dependencies
# ---------------------------------------------------------------------------
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# ---------------------------------------------------------------------------
# Download sentence-transformer model at build time to avoid cold starts
# ---------------------------------------------------------------------------
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# ---------------------------------------------------------------------------
# Copy application source
# ---------------------------------------------------------------------------
COPY app/ ./app/
COPY data/ ./data/
COPY scripts/ ./scripts/

# Create directories for persistent data
RUN mkdir -p /app/products_vectorstore /app/data

# ---------------------------------------------------------------------------
# Expose ports
# ---------------------------------------------------------------------------
# Gradio dashboard
EXPOSE 7860
# FastAPI REST API
EXPOSE 8000

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7860/ || exit 1

# ---------------------------------------------------------------------------
# Default command — launch the Gradio dashboard
# ---------------------------------------------------------------------------
CMD ["python", "-m", "app.main", "--mode", "dashboard"]
