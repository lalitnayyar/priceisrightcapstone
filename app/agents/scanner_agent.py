"""
Scanner Agent — Agent 1 of 7 in the Price Is Right framework.

Responsibility: Monitor RSS feeds, fetch live deals, and use GPT-5 with
Structured Outputs to identify the 5 most promising deals with clear prices
and detailed product descriptions.
"""
from typing import Optional, List

from openai import OpenAI

from app.agents.agent import Agent
from app.core.deals import ScrapedDeal, DealSelection, Opportunity


class ScannerAgent(Agent):
    """
    Uses GPT-5 (gpt-5-mini) with Structured Outputs to scan RSS feeds
    and extract the 5 best-described deals with confirmed prices.
    """

    name = "Scanner Agent"
    color = Agent.CYAN
    MODEL = "gpt-5-mini"

    SYSTEM_PROMPT = (
        "You identify and summarize the 5 most detailed deals from a list, by selecting deals "
        "that have the most detailed, high quality description and the most clear price. "
        "Respond strictly in JSON with no explanation, using this format. You should provide "
        "the price as a number derived from the description. If the price of a deal isn't clear, "
        "do not include that deal in your response. "
        "Most important is that you respond with the 5 deals that have the most detailed product "
        "description with price. It's not important to mention the terms of the deal; most important "
        "is a thorough description of the product. "
        "Be careful with products that are described as '$XXX off' or 'reduced by $XXX' - this isn't "
        "the actual price of the product. Only respond with products when you are highly confident "
        "about the price."
    )

    USER_PROMPT_PREFIX = (
        "Respond with the most promising 5 deals from this list, selecting those which have the most "
        "detailed, high quality product description and a clear price that is greater than 0. "
        "You should rephrase the description to be a summary of the product itself, not the terms of "
        "the deal. Remember to respond with a short paragraph of text in the product_description field "
        "for each of the 5 items that you select. "
        "Be careful with products that are described as '$XXX off' or 'reduced by $XXX' - this isn't "
        "the actual price of the product. Only respond with products when you are highly confident "
        "about the price.\n\nDeals:\n\n"
    )

    USER_PROMPT_SUFFIX = "\n\nInclude exactly 5 deals, no more."

    def __init__(self) -> None:
        self.log("Scanner Agent is initializing")
        self.openai = OpenAI()
        self.log("Scanner Agent is ready")

    def fetch_deals(self, memory: List[Opportunity]) -> List[ScrapedDeal]:
        """
        Fetch deals from RSS feeds, filtering out any already in memory.
        :param memory: list of previously surfaced Opportunity objects
        :return: list of new ScrapedDeal instances
        """
        self.log("Scanner Agent is fetching deals from RSS feeds")
        seen_urls = {opp.deal.url for opp in memory}
        scraped = ScrapedDeal.fetch()
        result = [s for s in scraped if s.url not in seen_urls]
        self.log(f"Scanner Agent found {len(result)} new deals not in memory")
        return result

    def make_user_prompt(self, scraped: List[ScrapedDeal]) -> str:
        """Build the user prompt from a list of scraped deals."""
        user_prompt = self.USER_PROMPT_PREFIX
        user_prompt += "\n\n".join([s.describe() for s in scraped])
        user_prompt += self.USER_PROMPT_SUFFIX
        return user_prompt

    def scan(self, memory: List[Opportunity] = []) -> Optional[DealSelection]:
        """
        Call GPT-5 with Structured Outputs to identify the 5 best deals.
        :param memory: previously surfaced opportunities (used to avoid duplicates)
        :return: a DealSelection of up to 5 deals, or None if no new deals found
        """
        scraped = self.fetch_deals(memory)
        if not scraped:
            self.log("Scanner Agent found no new deals to process")
            return None

        user_prompt = self.make_user_prompt(scraped)
        self.log(f"Scanner Agent is calling {self.MODEL} with Structured Outputs")
        result = self.openai.chat.completions.parse(
            model=self.MODEL,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format=DealSelection,
            reasoning_effort="minimal",
        )
        selection = result.choices[0].message.parsed
        selection.deals = [deal for deal in selection.deals if deal.price > 0]
        self.log(
            f"Scanner Agent received {len(selection.deals)} deals with price > 0 from {self.MODEL}"
        )
        return selection

    def test_scan(self, memory: List[Opportunity] = []) -> Optional[DealSelection]:
        """Return a static DealSelection for testing without live API calls."""
        results = {
            "deals": [
                {
                    "product_description": (
                        "The Hisense R6 Series 55R6030N is a 55-inch 4K UHD Roku Smart TV that "
                        "offers stunning picture quality with 3840x2160 resolution. It features "
                        "Dolby Vision HDR and HDR10 compatibility. The TV runs Roku OS with "
                        "Google Assistant and Alexa voice control. Three HDMI ports are included."
                    ),
                    "price": 178,
                    "url": "https://www.dealnews.com/products/Hisense/Hisense-R6-Series-55-R6030-N-55-4-K-UHD-Roku-Smart-TV/484824.html",
                },
                {
                    "product_description": (
                        "The Lenovo IdeaPad Slim 5 laptop is powered by an AMD Ryzen 5 8645HS "
                        "6-core CPU with a 16-inch 1080p touch display. It includes 16GB RAM "
                        "and a 512GB SSD for fast everyday performance."
                    ),
                    "price": 446,
                    "url": "https://www.dealnews.com/products/Lenovo/Lenovo-Idea-Pad-Slim-5/485068.html",
                },
                {
                    "product_description": (
                        "The Dell G15 gaming laptop features a 6th-generation AMD Ryzen 5 7640HS "
                        "CPU with a 15.6-inch 1080p 120Hz display. It includes 16GB RAM, 1TB NVMe "
                        "SSD, and an Nvidia GeForce RTX 3050 GPU."
                    ),
                    "price": 650,
                    "url": "https://www.dealnews.com/products/Dell/Dell-G15-Ryzen-5-15-6-Gaming-Laptop/485067.html",
                },
            ]
        }
        return DealSelection(**results)
