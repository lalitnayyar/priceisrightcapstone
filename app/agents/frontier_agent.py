"""
Frontier Agent — Agent 2 of 7 in the Price Is Right framework.

Responsibility: Use a massive RAG database (ChromaDB vector store) combined
with a frontier LLM (GPT-5.1) to estimate product prices by finding similar
products and using them as context for the model.
"""
import re
from typing import List, Dict, Tuple

from openai import OpenAI
from sentence_transformers import SentenceTransformer

from app.agents.agent import Agent


class FrontierAgent(Agent):
    """
    RAG-backed frontier pricing agent.

    Embeds the product description, queries ChromaDB for 5 similar products
    with known prices, then calls GPT-5.1 with that context to estimate price.
    """

    name = "Frontier Agent"
    color = Agent.BLUE
    MODEL = "gpt-5.1"
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    N_SIMILAR = 5

    def __init__(self, collection) -> None:
        """
        Initialise the Frontier Agent.
        :param collection: a ChromaDB collection containing product embeddings and prices
        """
        self.log("Initializing Frontier Agent")
        self.client = OpenAI()
        self.collection = collection
        self.log(f"Frontier Agent loading embedding model: {self.EMBEDDING_MODEL}")
        self.model = SentenceTransformer(self.EMBEDDING_MODEL)
        self.log("Frontier Agent is ready")

    def make_context(self, similars: List[str], prices: List[float]) -> str:
        """
        Build a context block from similar products and their prices.
        :param similars: list of similar product descriptions from the RAG store
        :param prices: corresponding prices for those products
        :return: formatted context string for the LLM prompt
        """
        message = (
            "To provide some context, here are some other items that might be "
            "similar to the item you need to estimate.\n\n"
        )
        for similar, price in zip(similars, prices):
            message += f"Potentially related product:\n{similar}\nPrice is ${price:.2f}\n\n"
        return message

    def messages_for(
        self, description: str, similars: List[str], prices: List[float]
    ) -> List[Dict[str, str]]:
        """
        Build the OpenAI messages list for a pricing request.
        :param description: the product description to price
        :param similars: similar products from RAG
        :param prices: prices of similar products
        :return: list of message dicts for the chat completion API
        """
        message = (
            f"Estimate the price of this product. Respond with the price only, "
            f"no explanation.\n\n{description}\n\n"
        )
        message += self.make_context(similars, prices)
        return [{"role": "user", "content": message}]

    def find_similars(self, description: str) -> Tuple[List[str], List[float]]:
        """
        Query ChromaDB for products similar to the given description.
        :param description: product description to embed and search
        :return: tuple of (document strings, prices)
        """
        self.log(
            f"Frontier Agent performing RAG search for {self.N_SIMILAR} similar products"
        )
        vector = self.model.encode([description])
        results = self.collection.query(
            query_embeddings=vector.astype(float).tolist(),
            n_results=self.N_SIMILAR,
        )
        documents = results["documents"][0][:]
        prices = [m["price"] for m in results["metadatas"][0][:]]
        self.log(f"Frontier Agent found {len(documents)} similar products in RAG store")
        return documents, prices

    def get_price(self, s: str) -> float:
        """Extract a floating-point price from a model response string."""
        s = s.replace("$", "").replace(",", "")
        match = re.search(r"[-+]?\d*\.\d+|\d+", s)
        return float(match.group()) if match else 0.0

    def price(self, description: str) -> float:
        """
        Estimate the price of a product using RAG context + GPT-5.1.
        :param description: product description
        :return: estimated price in USD
        """
        documents, prices = self.find_similars(description)
        self.log(
            f"Frontier Agent calling {self.MODEL} with {len(documents)} similar products as context"
        )
        response = self.client.chat.completions.create(
            model=self.MODEL,
            messages=self.messages_for(description, documents, prices),
            seed=42,
            reasoning_effort="none",
        )
        reply = response.choices[0].message.content
        result = self.get_price(reply)
        self.log(f"Frontier Agent completed — predicting ${result:.2f}")
        return result
