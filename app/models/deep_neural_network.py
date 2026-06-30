"""
Deep Neural Network price regression model for the Price Is Right framework.

Defines a residual-block DNN that predicts product prices from text features
extracted by a HashingVectorizer. Weights are loaded from a .pth checkpoint.
"""
import logging
import os

import numpy as np
import torch
import torch.nn as nn
from sklearn.feature_extraction.text import HashingVectorizer

# Normalisation constants derived from the training dataset
Y_STD = 1.0328539609909058
Y_MEAN = 4.434937953948975


class ResidualBlock(nn.Module):
    """A single residual block with LayerNorm, ReLU, and Dropout."""

    def __init__(self, hidden_size: int, dropout_prob: float) -> None:
        super().__init__()
        self.block = nn.Sequential(
            nn.Linear(hidden_size, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout_prob),
            nn.Linear(hidden_size, hidden_size),
            nn.LayerNorm(hidden_size),
        )
        self.relu = nn.ReLU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = x
        out = self.block(x)
        out += residual  # Skip connection
        return self.relu(out)


class DeepNeuralNetwork(nn.Module):
    """
    Deep residual neural network for price regression.
    Input: 5000-dimensional hashed text feature vector.
    Output: log-scale price prediction (un-normalised by inference helper).
    """

    def __init__(
        self,
        input_size: int,
        num_layers: int = 10,
        hidden_size: int = 4096,
        dropout_prob: float = 0.2,
    ) -> None:
        super().__init__()
        self.input_layer = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout_prob),
        )
        self.residual_blocks = nn.ModuleList(
            [ResidualBlock(hidden_size, dropout_prob) for _ in range(num_layers - 2)]
        )
        self.output_layer = nn.Linear(hidden_size, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.input_layer(x)
        for block in self.residual_blocks:
            x = block(x)
        return self.output_layer(x)


class DeepNeuralNetworkInference:
    """
    Inference helper that wraps DeepNeuralNetwork with text vectorisation
    and denormalisation of the log-scale output back to a dollar price.
    """

    def __init__(self) -> None:
        self.vectorizer = None
        self.model = None
        self.device = None
        np.random.seed(42)
        torch.manual_seed(42)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(42)

    def setup(self) -> None:
        """Initialise the vectorizer, model architecture, and select device."""
        self.vectorizer = HashingVectorizer(n_features=5000, stop_words="english", binary=True)
        self.model = DeepNeuralNetwork(5000)
        if torch.cuda.is_available():
            self.device = torch.device("cuda")
        elif torch.backends.mps.is_available():
            self.device = torch.device("mps")
        else:
            self.device = torch.device("cpu")
        logging.info(f"[Neural Network] Using device: {self.device}")
        self.model.to(self.device)

    def load(self, path: str) -> None:
        """Load model weights from a .pth checkpoint file."""
        if not os.path.exists(path):
            logging.warning(f"[Neural Network] Weights file not found at {path}; using random weights")
            return
        self.model.load_state_dict(torch.load(path, map_location=self.device))
        self.model.to(self.device)
        logging.info(f"[Neural Network] Loaded weights from {path}")

    def inference(self, text: str) -> float:
        """
        Predict the price of a product from its text description.
        :param text: product description string
        :return: estimated price in USD
        """
        self.model.eval()
        with torch.no_grad():
            vector = self.vectorizer.transform([text])
            tensor = torch.FloatTensor(vector.toarray()).to(self.device)
            pred = self.model(tensor)[0]
            result = torch.exp(pred * Y_STD + Y_MEAN) - 1
        return max(0.0, result.item())
