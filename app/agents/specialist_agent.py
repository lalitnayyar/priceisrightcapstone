"""
Specialist Agent — Agent 3 of 7 in the Price Is Right framework.

Responsibility: Call the frontier-busting fine-tuned LLM (Llama-3.2-3B with
PEFT adapter, deployed on Modal GPU infrastructure) to estimate product prices.
This agent provides the fine-tuned specialist pricing signal in the ensemble.
"""
import os

from app.agents.agent import Agent


class SpecialistAgent(Agent):
    """
    Wraps the fine-tuned LLM deployed remotely on Modal.

    The underlying model is a quantised Llama-3.2-3B base with a PEFT LoRA
    adapter trained specifically for product price estimation. It is served
    as a persistent Modal class to keep the GPU container warm between calls.

    If Modal is not available (e.g., in local/Docker mode without GPU),
    the agent falls back to a configurable local inference endpoint.
    """

    name = "Specialist Agent"
    color = Agent.RED

    # Modal service identifiers
    MODAL_APP_NAME = "pricer-service"
    MODAL_CLASS_NAME = "Pricer"

    # Fallback: local REST endpoint for the fine-tuned model
    LOCAL_ENDPOINT = os.getenv("SPECIALIST_LOCAL_ENDPOINT", "")

    def __init__(self) -> None:
        self.log("Specialist Agent is initializing")
        self.pricer = None
        self._use_modal = False

        # Attempt to connect to Modal deployment
        try:
            import modal  # type: ignore
            Pricer = modal.Cls.from_name(self.MODAL_APP_NAME, self.MODAL_CLASS_NAME)
            self.pricer = Pricer()
            self._use_modal = True
            self.log("Specialist Agent connected to Modal fine-tuned model")
        except Exception as exc:
            self.log(
                f"Specialist Agent could not connect to Modal ({exc}); "
                "will use local fallback if configured"
            )

        if not self._use_modal and self.LOCAL_ENDPOINT:
            self.log(f"Specialist Agent will use local endpoint: {self.LOCAL_ENDPOINT}")

        self.log("Specialist Agent is ready")

    def price(self, description: str) -> float:
        """
        Estimate the price of a product using the fine-tuned specialist model.
        :param description: product description
        :return: estimated price in USD
        """
        self.log("Specialist Agent is calling the fine-tuned model")

        if self._use_modal and self.pricer:
            result = self.pricer.price.remote(description)
            self.log(f"Specialist Agent (Modal) completed — predicting ${result:.2f}")
            return float(result)

        if self.LOCAL_ENDPOINT:
            import requests  # type: ignore
            try:
                resp = requests.post(
                    self.LOCAL_ENDPOINT,
                    json={"description": description},
                    timeout=30,
                )
                result = float(resp.json().get("price", 0.0))
                self.log(f"Specialist Agent (local) completed — predicting ${result:.2f}")
                return result
            except Exception as exc:
                self.log(f"Specialist Agent local endpoint failed: {exc}; returning 0.0")
                return 0.0

        self.log("Specialist Agent has no available backend; returning 0.0")
        return 0.0
