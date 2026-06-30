"""
Preprocessor module for the Price Is Right framework.

Uses a configurable LLM (default: gpt-4o-mini via LiteLLM) to rewrite
raw product descriptions into a clean, structured format before they are
passed to the pricing agents.
"""
import os
from litellm import completion
from dotenv import load_dotenv

load_dotenv(override=True)

DEFAULT_MODEL_NAME = os.getenv("PRICER_PREPROCESSOR_MODEL", "gpt-4o-mini")
DEFAULT_REASONING_EFFORT = "low" if "gpt-oss" in DEFAULT_MODEL_NAME else None

SYSTEM_PROMPT = """Create a concise description of a product. Respond only in this format. Do not include part numbers.
Title: Rewritten short precise title
Category: eg Electronics
Brand: Brand name
Description: 1 sentence description
Details: 1 sentence on features"""


class Preprocessor:
    """
    LLM-based text rewriting utility.
    Normalises raw product descriptions into a structured format that
    improves the accuracy of downstream pricing models.
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        reasoning_effort: str = DEFAULT_REASONING_EFFORT,
        base_url: str = None,
    ) -> None:
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.model_name = model_name
        self.reasoning_effort = reasoning_effort
        self.base_url = base_url
        if "ollama" in model_name and not base_url:
            self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    def messages_for(self, text: str) -> list:
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ]

    def preprocess(self, text: str) -> str:
        """
        Rewrite a product description into a clean structured format.
        :param text: raw product description
        :return: normalised product description
        """
        messages = self.messages_for(text)
        kwargs = dict(messages=messages, model=self.model_name)
        if self.reasoning_effort:
            kwargs["reasoning_effort"] = self.reasoning_effort
        if self.base_url:
            kwargs["api_base"] = self.base_url
        response = completion(**kwargs)
        self.total_input_tokens += response.usage.prompt_tokens
        self.total_output_tokens += response.usage.completion_tokens
        try:
            self.total_cost += response._hidden_params.get("response_cost", 0.0)
        except Exception:
            pass
        return response.choices[0].message.content
