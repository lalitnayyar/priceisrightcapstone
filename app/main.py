"""
Price Is Right — Main Application Entry Point.

Supports three launch modes:
  - dashboard: Launch the Gradio folding-view dashboard (default)
  - api:       Launch the FastAPI REST API server
  - run:       Run a single deal-hunting cycle and exit
  - init-rag:  Initialise the RAG database with sample data

Usage:
    python -m app.main                    # Launch dashboard
    python -m app.main --mode dashboard   # Launch dashboard
    python -m app.main --mode api         # Launch API server
    python -m app.main --mode run         # Single run
    python -m app.main --mode init-rag    # Initialise RAG DB
"""
import argparse
import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv(override=True)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def launch_dashboard(port: int = 7860, share: bool = False) -> None:
    """Launch the Gradio folding-view dashboard."""
    logger.info(f"Starting Price Is Right Dashboard on port {port}")
    from app.ui.dashboard import PriceIsRightDashboard
    PriceIsRightDashboard().run(server_port=port, share=share)


def launch_api(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Launch the FastAPI REST API server."""
    logger.info(f"Starting Price Is Right API on {host}:{port}")
    import uvicorn
    uvicorn.run("app.api:app", host=host, port=port, reload=False)


def run_once() -> None:
    """Execute a single deal-hunting cycle."""
    logger.info("Running a single deal-hunting cycle")
    from app.core.deal_agent_framework import DealAgentFramework
    framework = DealAgentFramework()
    memory = framework.run()
    logger.info(f"Run complete — {len(memory)} opportunities in memory")
    for opp in memory[-3:]:
        logger.info(
            f"  Opportunity: {opp.deal.product_description[:60]}... "
            f"Price=${opp.deal.price:.2f} Estimate=${opp.estimate:.2f} "
            f"Discount=${opp.discount:.2f}"
        )


def init_rag() -> None:
    """Initialise the RAG database with sample product data."""
    logger.info("Initialising RAG database with sample data")
    from app.core.rag_db import RAGDatabase
    db = RAGDatabase()
    added = db.load_sample_data()
    status = db.status()
    logger.info(f"RAG database ready: {status['product_count']} products")
    if added:
        logger.info(f"Added {added} new sample products")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Price Is Right — Multi-Agent Deal Hunter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--mode",
        choices=["dashboard", "api", "run", "init-rag"],
        default="dashboard",
        help="Launch mode (default: dashboard)",
    )
    parser.add_argument("--port", type=int, default=None, help="Port number")
    parser.add_argument("--share", action="store_true", help="Share Gradio UI publicly")
    args = parser.parse_args()

    if args.mode == "dashboard":
        port = args.port or int(os.getenv("DASHBOARD_PORT", "7860"))
        launch_dashboard(port=port, share=args.share)

    elif args.mode == "api":
        port = args.port or int(os.getenv("API_PORT", "8000"))
        launch_api(port=port)

    elif args.mode == "run":
        run_once()

    elif args.mode == "init-rag":
        init_rag()


if __name__ == "__main__":
    main()
