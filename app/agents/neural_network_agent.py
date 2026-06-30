"""
Neural Network Agent — Agent 4 of 7 in the Price Is Right framework.

Responsibility: Use a locally-hosted deep residual neural network (trained on
product price data) to provide a fast, offline price estimate as one signal
in the ensemble.
"""
import os

from app.agents.agent import Agent
from app.models.deep_neural_network import DeepNeuralNetworkInference

# Default path to the trained weights file
DEFAULT_WEIGHTS_PATH = os.getenv(
    "DNN_WEIGHTS_PATH",
    os.path.join(os.path.dirname(__file__), "../../data/deep_neural_network.pth"),
)


class NeuralNetworkAgent(Agent):
    """
    Wraps the DeepNeuralNetworkInference helper to provide price estimates
    from a locally-loaded PyTorch model.
    """

    name = "Neural Network Agent"
    color = Agent.MAGENTA

    def __init__(self, weights_path: str = DEFAULT_WEIGHTS_PATH) -> None:
        """
        Initialise the Neural Network Agent by loading model weights.
        :param weights_path: path to the .pth weights file
        """
        self.log("Neural Network Agent is initializing")
        self.neural_network = DeepNeuralNetworkInference()
        self.neural_network.setup()
        self.neural_network.load(weights_path)
        self.log("Neural Network Agent is ready and weights are loaded")

    def price(self, description: str) -> float:
        """
        Use the Deep Neural Network to estimate the price of the described item.
        :param description: product description
        :return: estimated price in USD
        """
        self.log("Neural Network Agent is starting a prediction")
        result = self.neural_network.inference(description)
        self.log(f"Neural Network Agent completed — predicting ${result:.2f}")
        return result
