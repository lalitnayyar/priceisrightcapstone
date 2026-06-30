"""
DealAgentFramework — Central orchestration layer for the Price Is Right system.

This module initialises ChromaDB, manages persistent memory (previously surfaced
opportunities), and coordinates the PlanningAgent to run the full deal-hunting
workflow. It also provides data for the 3D RAG visualisation in the dashboard.
"""
import json
import logging
import os
import sys
from typing import List, Optional

import chromadb
import numpy as np
from sklearn.manifold import TSNE

from app.core.deals import Opportunity
from app.agents.planning_agent import PlanningAgent

# ---------------------------------------------------------------------------
# Terminal color codes for framework-level log messages
# ---------------------------------------------------------------------------
BG_BLUE = "\033[44m"
WHITE = "\033[37m"
RESET = "\033[0m"

# ---------------------------------------------------------------------------
# Product categories and their plot colors for the RAG visualisation
# ---------------------------------------------------------------------------
CATEGORIES = [
    "Appliances",
    "Automotive",
    "Cell_Phones_and_Accessories",
    "Electronics",
    "Musical_Instruments",
    "Office_Products",
    "Tools_and_Home_Improvement",
    "Toys_and_Games",
]
COLORS = ["red", "blue", "brown", "orange", "yellow", "green", "purple", "cyan"]


def init_logging() -> None:
    """Configure root logger to write to stdout with a standard format."""
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "[%(asctime)s] [Agents] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S %z",
    )
    handler.setFormatter(formatter)
    if not root.handlers:
        root.addHandler(handler)


class DealAgentFramework:
    """
    Central orchestration class for the Price Is Right multi-agent framework.

    Responsibilities:
    - Initialise and persist the ChromaDB vector store (RAG database).
    - Load and save the memory file (previously surfaced opportunities).
    - Lazily initialise the PlanningAgent on first use.
    - Run the full deal-hunting workflow and return updated memory.
    - Provide plot data for the 3D RAG visualisation.
    """

    DB = os.getenv("CHROMA_DB_PATH", "products_vectorstore")
    MEMORY_FILENAME = os.getenv("MEMORY_FILE", "data/memory.json")

    def __init__(self) -> None:
        init_logging()
        self.log("DealAgentFramework initializing")
        client = chromadb.PersistentClient(path=self.DB)
        self.collection = client.get_or_create_collection("products")
        self.memory: List[Opportunity] = self.read_memory()
        self.planner: Optional[PlanningAgent] = None
        self.log(
            f"DealAgentFramework ready — "
            f"{len(self.memory)} opportunities in memory, "
            f"{self.collection.count()} products in RAG store"
        )

    def init_agents_as_needed(self) -> None:
        """Lazily initialise the PlanningAgent (and all sub-agents) on first call."""
        if not self.planner:
            self.log("Initializing Agent Framework")
            self.planner = PlanningAgent(self.collection)
            self.log("Agent Framework is ready")

    def read_memory(self) -> List[Opportunity]:
        """Load previously surfaced opportunities from the JSON memory file."""
        if os.path.exists(self.MEMORY_FILENAME):
            try:
                with open(self.MEMORY_FILENAME, "r") as f:
                    data = json.load(f)
                return [Opportunity(**item) for item in data]
            except Exception as exc:
                self.log(f"Could not read memory file: {exc}")
        return []

    def write_memory(self) -> None:
        """Persist the current memory list to the JSON memory file."""
        os.makedirs(os.path.dirname(self.MEMORY_FILENAME) or ".", exist_ok=True)
        data = [opp.model_dump() for opp in self.memory]
        with open(self.MEMORY_FILENAME, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def reset_memory(cls) -> None:
        """Truncate the memory file to the first 2 entries (for testing)."""
        if os.path.exists(cls.MEMORY_FILENAME):
            with open(cls.MEMORY_FILENAME, "r") as f:
                data = json.load(f)
            truncated = data[:2]
            with open(cls.MEMORY_FILENAME, "w") as f:
                json.dump(truncated, f, indent=2)

    def log(self, message: str) -> None:
        """Log a framework-level message with orange color."""
        text = BG_BLUE + WHITE + "[Agent Framework] " + message + RESET
        logging.info(text)

    def run(self) -> List[Opportunity]:
        """
        Execute the full deal-hunting workflow.
        :return: updated list of all surfaced opportunities
        """
        self.init_agents_as_needed()
        self.log("Kicking off Planning Agent")
        result = self.planner.plan(memory=self.memory)
        self.log(f"Planning Agent completed — result: {result}")
        if result:
            self.memory.append(result)
            self.write_memory()
        return self.memory

    @classmethod
    def get_plot_data(cls, max_datapoints: int = 2000):
        """
        Retrieve embeddings from ChromaDB and reduce to 3D via t-SNE
        for the RAG visualisation plot.
        :param max_datapoints: maximum number of products to include
        :return: tuple of (documents, reduced_vectors, colors)
        """
        client = chromadb.PersistentClient(path=cls.DB)
        collection = client.get_or_create_collection("products")
        result = collection.get(
            include=["embeddings", "documents", "metadatas"],
            limit=max_datapoints,
        )
        if not result["embeddings"]:
            return [], np.array([]), []

        vectors = np.array(result["embeddings"])
        documents = result["documents"]
        categories = [m.get("category", "Electronics") for m in result["metadatas"]]
        colors = []
        for c in categories:
            if c in CATEGORIES:
                colors.append(COLORS[CATEGORIES.index(c)])
            else:
                colors.append("gray")

        tsne = TSNE(n_components=3, random_state=42, n_jobs=-1)
        reduced_vectors = tsne.fit_transform(vectors)
        return documents, reduced_vectors, colors


if __name__ == "__main__":
    DealAgentFramework().run()
