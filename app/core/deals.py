"""
Core data models and RSS deal ingestion for the Price Is Right framework.

This module defines the Pydantic models that flow through the entire agent
pipeline, as well as the ScrapedDeal class that fetches and parses live
deal data from RSS feeds.
"""
import os
import re
import time
from typing import List, Dict, Optional

import feedparser
import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from tqdm import tqdm

# ---------------------------------------------------------------------------
# RSS feed sources — extend this list to add more deal categories
# ---------------------------------------------------------------------------
DEFAULT_FEEDS: List[str] = [
    "https://www.dealnews.com/c142/Electronics/?rss=1",
    "https://www.dealnews.com/c39/Computers/?rss=1",
    "https://www.dealnews.com/f1912/Smart-Home/?rss=1",
    # Uncomment to add more categories:
    # "https://www.dealnews.com/c238/Automotive/?rss=1",
    # "https://www.dealnews.com/c196/Home-Garden/?rss=1",
]

# Allow override via environment variable (comma-separated URLs)
_env_feeds = os.getenv("RSS_FEED_URLS", "")
feeds: List[str] = [f.strip() for f in _env_feeds.split(",") if f.strip()] or DEFAULT_FEEDS


# ---------------------------------------------------------------------------
# HTML extraction helper
# ---------------------------------------------------------------------------

def extract(html_snippet: str) -> str:
    """
    Use BeautifulSoup to clean up an HTML snippet and extract useful text.
    :param html_snippet: raw HTML string from an RSS entry summary
    :return: plain text with whitespace normalised
    """
    soup = BeautifulSoup(html_snippet, "html.parser")
    snippet_div = soup.find("div", class_="snippet summary")
    if snippet_div:
        description = snippet_div.get_text(strip=True)
        description = BeautifulSoup(description, "html.parser").get_text()
        description = re.sub("<[^<]+?>", "", description)
        result = description.strip()
    else:
        result = html_snippet
    return result.replace("\n", " ")


# ---------------------------------------------------------------------------
# ScrapedDeal — raw deal fetched from RSS + page scrape
# ---------------------------------------------------------------------------

class ScrapedDeal:
    """
    Represents a deal retrieved from an RSS feed and enriched by scraping
    the linked deal page for additional product details and features.
    """

    category: str
    title: str
    summary: str
    url: str
    details: str
    features: str

    def __init__(self, entry: Dict) -> None:
        """
        Populate this instance from a feedparser entry dict.
        Fetches the deal URL to extract structured product content.
        """
        self.title = entry["title"]
        self.summary = extract(entry["summary"])
        self.url = entry["links"][0]["href"]
        try:
            stuff = requests.get(self.url, timeout=10).content
            soup = BeautifulSoup(stuff, "html.parser")
            content_section = soup.find("div", class_="content-section")
            if content_section:
                content = content_section.get_text()
                content = content.replace("\nmore", "").replace("\n", " ")
                if "Features" in content:
                    self.details, self.features = content.split("Features", 1)
                else:
                    self.details = content
                    self.features = ""
            else:
                self.details = self.summary
                self.features = ""
        except Exception:
            self.details = self.summary
            self.features = ""
        self.truncate()

    def truncate(self) -> None:
        """Limit fields to a sensible length to avoid overloading the model."""
        self.title = self.title[:100]
        self.details = self.details[:500]
        self.features = self.features[:500]

    def __repr__(self) -> str:
        return f"<{self.title}>"

    def describe(self) -> str:
        """Return a formatted string suitable for inclusion in a model prompt."""
        return (
            f"Title: {self.title}\n"
            f"Details: {self.details.strip()}\n"
            f"Features: {self.features.strip()}\n"
            f"URL: {self.url}"
        )

    @classmethod
    def fetch(cls, show_progress: bool = False) -> List["ScrapedDeal"]:
        """
        Retrieve all deals from the configured RSS feeds.
        :param show_progress: whether to display a tqdm progress bar
        :return: list of ScrapedDeal instances
        """
        deals: List["ScrapedDeal"] = []
        feed_iter = tqdm(feeds) if show_progress else feeds
        for feed_url in feed_iter:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:10]:
                    try:
                        deals.append(cls(entry))
                        time.sleep(0.05)
                    except Exception:
                        pass
            except Exception:
                pass
        return deals


# ---------------------------------------------------------------------------
# Pydantic models — shared across all agents
# ---------------------------------------------------------------------------

class Deal(BaseModel):
    """A deal with a summarised product description and confirmed price."""

    product_description: str = Field(
        description=(
            "A clearly expressed summary of the product in 3-4 sentences. "
            "Details of the item are much more important than why it's a good deal. "
            "Avoid mentioning discounts and coupons; focus on the item itself."
        )
    )
    price: float = Field(
        description=(
            "The actual price of this product as advertised in the deal. "
            "For example, if a deal is described as '$100 off the usual $300 price', "
            "respond with $200."
        )
    )
    url: str = Field(description="The URL of the deal, as provided in the input.")


class DealSelection(BaseModel):
    """A curated list of the most promising deals from a raw RSS scrape."""

    deals: List[Deal] = Field(
        description=(
            "Your selection of the 5 deals that have the most detailed, high-quality "
            "description and the most clearly stated price."
        )
    )


class Opportunity(BaseModel):
    """
    A confirmed deal opportunity: a Deal where the estimated true value
    significantly exceeds the advertised price.
    """

    deal: Deal
    estimate: float
    discount: float
