"""
RAG Database initialization and management utilities.

This module provides helpers for populating the ChromaDB vector store
with product embeddings. The store is used by the FrontierAgent to find
similar products and provide context for price estimation.

Usage:
    python -m app.core.rag_db --load-sample   # Load sample data
    python -m app.core.rag_db --status        # Show store statistics
"""
import argparse
import json
import logging
import os
from typing import List, Dict, Optional

import chromadb
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "products_vectorstore")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
COLLECTION_NAME = "products"

# Sample product data for development / testing
SAMPLE_PRODUCTS = [
    {"description": "Apple MacBook Pro 14-inch M3 Pro chip 18GB RAM 512GB SSD laptop computer", "price": 1999.0, "category": "Electronics"},
    {"description": "Samsung 65-inch QLED 4K Smart TV with Quantum HDR and Alexa built-in", "price": 1299.0, "category": "Electronics"},
    {"description": "Sony WH-1000XM5 Wireless Noise Cancelling Headphones Bluetooth 30hr battery", "price": 349.0, "category": "Electronics"},
    {"description": "Dell XPS 15 laptop Intel Core i7 16GB RAM 512GB SSD OLED display", "price": 1799.0, "category": "Electronics"},
    {"description": "iPad Pro 12.9-inch M2 chip 256GB WiFi with Liquid Retina XDR display", "price": 1099.0, "category": "Electronics"},
    {"description": "LG C3 55-inch OLED evo 4K Smart TV with AI Picture Pro and webOS", "price": 1299.0, "category": "Electronics"},
    {"description": "Bose QuietComfort 45 Bluetooth wireless noise cancelling headphones", "price": 279.0, "category": "Electronics"},
    {"description": "Lenovo ThinkPad X1 Carbon Gen 11 Intel Core i7 16GB 512GB SSD ultrabook", "price": 1549.0, "category": "Electronics"},
    {"description": "Nintendo Switch OLED Model with 7-inch OLED screen and 64GB storage", "price": 349.0, "category": "Toys_and_Games"},
    {"description": "PlayStation 5 Digital Edition console with DualSense wireless controller", "price": 449.0, "category": "Electronics"},
    {"description": "Microsoft Xbox Series X 1TB gaming console with Game Pass Ultimate", "price": 499.0, "category": "Electronics"},
    {"description": "Google Pixel 8 Pro smartphone 256GB 5G with Tensor G3 chip", "price": 999.0, "category": "Cell_Phones_and_Accessories"},
    {"description": "Samsung Galaxy S24 Ultra 256GB titanium smartphone with S Pen", "price": 1299.0, "category": "Cell_Phones_and_Accessories"},
    {"description": "Apple iPhone 15 Pro Max 256GB titanium 5G smartphone", "price": 1199.0, "category": "Cell_Phones_and_Accessories"},
    {"description": "Dyson V15 Detect cordless vacuum cleaner with laser dust detection", "price": 699.0, "category": "Appliances"},
    {"description": "KitchenAid Artisan 5-quart stand mixer with 10 speeds and tilt-head", "price": 449.0, "category": "Appliances"},
    {"description": "Instant Pot Duo 7-in-1 electric pressure cooker 6 quart stainless steel", "price": 99.0, "category": "Appliances"},
    {"description": "iRobot Roomba j7+ self-emptying robot vacuum with smart mapping", "price": 599.0, "category": "Appliances"},
    {"description": "DeWalt 20V MAX cordless drill driver kit with 2 batteries and charger", "price": 179.0, "category": "Tools_and_Home_Improvement"},
    {"description": "Makita 18V LXT lithium-ion brushless cordless circular saw 7-1/4 inch", "price": 249.0, "category": "Tools_and_Home_Improvement"},
    {"description": "Fender Player Stratocaster electric guitar with maple neck sunburst finish", "price": 849.0, "category": "Musical_Instruments"},
    {"description": "Yamaha P-45 88-key weighted action digital piano with sustain pedal", "price": 449.0, "category": "Musical_Instruments"},
    {"description": "HP LaserJet Pro MFP M428fdw wireless monochrome all-in-one printer", "price": 349.0, "category": "Office_Products"},
    {"description": "Logitech MX Master 3S wireless mouse with 8K DPI sensor and USB-C", "price": 99.0, "category": "Office_Products"},
    {"description": "Garmin Forerunner 955 Solar GPS running smartwatch with triathlon mode", "price": 499.0, "category": "Electronics"},
    {"description": "Hisense 55-inch 4K UHD Roku Smart TV with Dolby Vision and HDR10", "price": 349.0, "category": "Electronics"},
    {"description": "Asus ROG Strix G16 gaming laptop RTX 4070 Intel i9 16GB 1TB SSD", "price": 1799.0, "category": "Electronics"},
    {"description": "Canon EOS R6 Mark II mirrorless camera body 24.2MP full-frame", "price": 2499.0, "category": "Electronics"},
    {"description": "Anker 65W USB-C GaN charger with 3 ports for laptop phone tablet", "price": 45.0, "category": "Electronics"},
    {"description": "Amazon Echo Show 10 smart display with motion and Alexa built-in", "price": 249.0, "category": "Electronics"},
]


class RAGDatabase:
    """
    Manages the ChromaDB vector store for product similarity search.
    """

    def __init__(self, db_path: str = CHROMA_DB_PATH) -> None:
        self.db_path = db_path
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(COLLECTION_NAME)
        self._encoder: Optional[SentenceTransformer] = None
        logger.info(f"RAGDatabase initialized at {db_path} with {self.collection.count()} products")

    @property
    def encoder(self) -> SentenceTransformer:
        if self._encoder is None:
            logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
            self._encoder = SentenceTransformer(EMBEDDING_MODEL)
        return self._encoder

    def add_products(self, products: List[Dict]) -> int:
        """
        Add a list of product dicts to the vector store.
        :param products: list of dicts with 'description', 'price', 'category' keys
        :return: number of products added
        """
        descriptions = [p["description"] for p in products]
        logger.info(f"Encoding {len(descriptions)} product descriptions")
        embeddings = self.encoder.encode(descriptions).tolist()

        ids = [f"product_{self.collection.count() + i}" for i in range(len(products))]
        metadatas = [{"price": p["price"], "category": p.get("category", "Electronics")} for p in products]

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=descriptions,
            metadatas=metadatas,
        )
        logger.info(f"Added {len(products)} products to RAG store (total: {self.collection.count()})")
        return len(products)

    def load_sample_data(self) -> int:
        """Load the built-in sample product dataset."""
        if self.collection.count() > 0:
            logger.info(f"RAG store already has {self.collection.count()} products; skipping sample load")
            return 0
        return self.add_products(SAMPLE_PRODUCTS)

    def load_from_json(self, filepath: str) -> int:
        """
        Load products from a JSON file.
        :param filepath: path to JSON file with list of product dicts
        :return: number of products added
        """
        with open(filepath, "r") as f:
            products = json.load(f)
        return self.add_products(products)

    def status(self) -> Dict:
        """Return a status summary of the RAG store."""
        return {
            "db_path": self.db_path,
            "collection": COLLECTION_NAME,
            "product_count": self.collection.count(),
            "embedding_model": EMBEDDING_MODEL,
        }

    def query(self, description: str, n_results: int = 5) -> List[Dict]:
        """
        Find products similar to the given description.
        :param description: product description to search for
        :param n_results: number of similar products to return
        :return: list of dicts with 'description', 'price', 'category'
        """
        vector = self.encoder.encode([description]).tolist()
        results = self.collection.query(
            query_embeddings=vector,
            n_results=n_results,
        )
        output = []
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            output.append({
                "description": doc,
                "price": meta.get("price", 0.0),
                "category": meta.get("category", "Unknown"),
            })
        return output


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="RAG Database management")
    parser.add_argument("--load-sample", action="store_true", help="Load sample product data")
    parser.add_argument("--load-json", type=str, help="Load products from JSON file")
    parser.add_argument("--status", action="store_true", help="Show database status")
    parser.add_argument("--query", type=str, help="Query for similar products")
    args = parser.parse_args()

    db = RAGDatabase()

    if args.load_sample:
        added = db.load_sample_data()
        print(f"Added {added} sample products")

    if args.load_json:
        added = db.load_from_json(args.load_json)
        print(f"Added {added} products from {args.load_json}")

    if args.status:
        status = db.status()
        for k, v in status.items():
            print(f"  {k}: {v}")

    if args.query:
        results = db.query(args.query)
        print(f"\nTop {len(results)} similar products for: {args.query}")
        for r in results:
            print(f"  ${r['price']:.2f} — {r['description'][:80]}")
