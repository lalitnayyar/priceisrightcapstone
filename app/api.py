"""
FastAPI REST API for the Price Is Right multi-agent framework.

Provides endpoints for:
  - Running the deal-hunting workflow
  - Querying the RAG database
  - Viewing memory / surfaced opportunities
  - Health check
"""
import logging
from typing import List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.core.deals import Opportunity
from app.core.deal_agent_framework import DealAgentFramework
from app.core.rag_db import RAGDatabase

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Price Is Right — Multi-Agent Deal Hunter",
    description=(
        "A 7-agent AI framework that monitors RSS feeds, estimates product prices "
        "using a RAG database + frontier LLM + fine-tuned model ensemble, and sends "
        "push notifications for great deal opportunities."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared framework instance (initialised on first request)
_framework: Optional[DealAgentFramework] = None
_rag_db: Optional[RAGDatabase] = None


def get_framework() -> DealAgentFramework:
    global _framework
    if _framework is None:
        _framework = DealAgentFramework()
    return _framework


def get_rag_db() -> RAGDatabase:
    global _rag_db
    if _rag_db is None:
        _rag_db = RAGDatabase()
    return _rag_db


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class PriceQueryRequest(BaseModel):
    description: str


class PriceQueryResponse(BaseModel):
    description: str
    similar_products: List[dict]


class RunResponse(BaseModel):
    opportunities_count: int
    new_opportunity: Optional[dict] = None
    message: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "price-is-right"}


@app.get("/memory", response_model=List[dict])
def get_memory():
    """Return all previously surfaced deal opportunities."""
    framework = get_framework()
    return [opp.model_dump() for opp in framework.memory]


@app.post("/run", response_model=RunResponse)
def run_framework(background_tasks: BackgroundTasks):
    """
    Trigger a full deal-hunting run.
    Scans RSS feeds, prices deals, and sends a push notification if a
    great opportunity is found.
    """
    framework = get_framework()
    try:
        memory = framework.run()
        new_opp = memory[-1] if memory else None
        return RunResponse(
            opportunities_count=len(memory),
            new_opportunity=new_opp.model_dump() if new_opp else None,
            message="Run completed successfully",
        )
    except Exception as exc:
        logger.error(f"Framework run failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/query-rag", response_model=PriceQueryResponse)
def query_rag(request: PriceQueryRequest):
    """
    Query the RAG database for products similar to the given description.
    """
    db = get_rag_db()
    try:
        similar = db.query(request.description, n_results=5)
        return PriceQueryResponse(
            description=request.description,
            similar_products=similar,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/rag-status")
def rag_status():
    """Return the current status of the RAG vector database."""
    db = get_rag_db()
    return db.status()


@app.post("/reset-memory")
def reset_memory():
    """Truncate the memory file to the first 2 entries (for testing)."""
    DealAgentFramework.reset_memory()
    return {"message": "Memory reset to first 2 entries"}
