"""Core data models, RSS ingestion, and preprocessing utilities."""
from app.core.deals import Deal, DealSelection, Opportunity, ScrapedDeal
from app.core.preprocessor import Preprocessor

__all__ = ["Deal", "DealSelection", "Opportunity", "ScrapedDeal", "Preprocessor"]
