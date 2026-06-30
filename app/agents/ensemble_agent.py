"""
Ensemble Agent — Agent 5 of 7 in the Price Is Right framework.

Responsibility: Coordinate the three pricing sub-agents (Frontier, Specialist,
Neural Network), preprocess descriptions, and combine their estimates into a
single weighted price prediction.
"""
from app.agents.agent import Agent
from app.agents.specialist_agent import SpecialistAgent
from app.agents.frontier_agent import FrontierAgent
from app.agents.neural_network_agent import NeuralNetworkAgent
from app.core.preprocessor import Preprocessor


class EnsembleAgent(Agent):
    """
    Orchestrates three pricing agents and combines their outputs.

    Weighting strategy (configurable via environment):
      - Frontier Agent (RAG + GPT-5.1):  80%
      - Specialist Agent (fine-tuned LLM): 10%
      - Neural Network Agent (DNN):        10%

    The Preprocessor normalises the raw description before it is passed to
    each sub-agent to improve consistency and accuracy.
    """

    name = "Ensemble Agent"
    color = Agent.YELLOW

    # Weights for the weighted average (must sum to 1.0)
    FRONTIER_WEIGHT = 0.8
    SPECIALIST_WEIGHT = 0.1
    NEURAL_NETWORK_WEIGHT = 0.1

    def __init__(self, collection) -> None:
        """
        Instantiate all three sub-agents and the preprocessor.
        :param collection: ChromaDB collection passed to the Frontier Agent
        """
        self.log("Initializing Ensemble Agent")
        self.specialist = SpecialistAgent()
        self.frontier = FrontierAgent(collection)
        self.neural_network = NeuralNetworkAgent()
        self.preprocessor = Preprocessor()
        self.log("Ensemble Agent is ready")

    def price(self, description: str) -> float:
        """
        Estimate the price of a product by combining three agent predictions.

        1. Preprocess the description for consistency.
        2. Obtain estimates from Frontier, Specialist, and Neural Network agents.
        3. Return a weighted average of the three estimates.

        :param description: raw product description
        :return: weighted ensemble price estimate in USD
        """
        self.log("Ensemble Agent — preprocessing description")
        rewrite = self.preprocessor.preprocess(description)
        self.log(f"Ensemble Agent — preprocessed via {self.preprocessor.model_name}")

        specialist_price = self.specialist.price(rewrite)
        frontier_price = self.frontier.price(rewrite)
        neural_network_price = self.neural_network.price(rewrite)

        combined = (
            frontier_price * self.FRONTIER_WEIGHT
            + specialist_price * self.SPECIALIST_WEIGHT
            + neural_network_price * self.NEURAL_NETWORK_WEIGHT
        )

        self.log(
            f"Ensemble Agent complete — "
            f"frontier=${frontier_price:.2f}, "
            f"specialist=${specialist_price:.2f}, "
            f"dnn=${neural_network_price:.2f}, "
            f"combined=${combined:.2f}"
        )
        return combined
