"""
Autonomous Planning Agent — LLM-driven orchestration variant.

This agent exposes the scan, estimate, and notify operations as OpenAI
function-calling tools and lets GPT-5.1 decide the order and logic of
execution autonomously. It is an alternative to the deterministic PlanningAgent.
"""
import json
from typing import Optional, List, Dict

from openai import OpenAI

from app.agents.agent import Agent
from app.core.deals import Deal, Opportunity
from app.agents.scanner_agent import ScannerAgent
from app.agents.ensemble_agent import EnsembleAgent
from app.agents.messaging_agent import MessagingAgent


class AutonomousPlanningAgent(Agent):
    """
    LLM-driven planning agent that uses OpenAI function-calling to
    autonomously orchestrate scanning, pricing, and notification.
    """

    name = "Autonomous Planning Agent"
    color = Agent.GREEN
    MODEL = "gpt-5.1"

    SYSTEM_MESSAGE = (
        "You find great deals on bargain products using your tools, "
        "and notify the user of the best bargain."
    )
    USER_MESSAGE = (
        "First, use your tool to scan the internet for bargain deals. "
        "Then for each deal, use your tool to estimate its true value. "
        "Then pick the single most compelling deal where the price is much lower "
        "than the estimated true value, and use your tool to notify the user. "
        "Then just reply OK to indicate success."
    )

    def __init__(self, collection) -> None:
        self.log("Autonomous Planning Agent is initializing")
        self.scanner = ScannerAgent()
        self.ensemble = EnsembleAgent(collection)
        self.messenger = MessagingAgent()
        self.openai = OpenAI()
        self.memory: List[Opportunity] = []
        self.opportunity: Optional[Opportunity] = None
        self.log("Autonomous Planning Agent is ready")

    # ------------------------------------------------------------------
    # Tool implementations
    # ------------------------------------------------------------------

    def scan_the_internet_for_bargains(self) -> str:
        """Tool: scan RSS feeds and return deal JSON."""
        self.log("Autonomous Planning Agent — calling ScannerAgent")
        results = self.scanner.scan(memory=self.memory)
        return results.model_dump_json() if results else "No deals found"

    def estimate_true_value(self, description: str) -> str:
        """Tool: estimate the true value of a product."""
        self.log("Autonomous Planning Agent — calling EnsembleAgent")
        estimate = self.ensemble.price(description)
        return f"The estimated true value of {description[:60]}... is ${estimate:.2f}"

    def notify_user_of_deal(
        self,
        description: str,
        deal_price: float,
        estimated_true_value: float,
        url: str,
    ) -> str:
        """Tool: send a push notification for the best deal (called once only)."""
        if self.opportunity:
            self.log("Autonomous Planning Agent — ignoring duplicate notification request")
            return "Notification already sent"
        self.log("Autonomous Planning Agent — sending notification via MessagingAgent")
        self.messenger.notify(description, deal_price, estimated_true_value, url)
        deal = Deal(product_description=description, price=deal_price, url=url)
        discount = estimated_true_value - deal_price
        self.opportunity = Opportunity(deal=deal, estimate=estimated_true_value, discount=discount)
        return "Notification sent successfully"

    # ------------------------------------------------------------------
    # Tool schemas
    # ------------------------------------------------------------------

    SCAN_FUNCTION: Dict = {
        "name": "scan_the_internet_for_bargains",
        "description": "Returns top bargains scraped from the internet along with the price each item is being offered for",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    }

    ESTIMATE_FUNCTION: Dict = {
        "name": "estimate_true_value",
        "description": "Given the description of an item, estimate how much it is actually worth",
        "parameters": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "The description of the item to be estimated",
                },
            },
            "required": ["description"],
            "additionalProperties": False,
        },
    }

    NOTIFY_FUNCTION: Dict = {
        "name": "notify_user_of_deal",
        "description": "Send the user a push notification about the single most compelling deal; only call this one time",
        "parameters": {
            "type": "object",
            "properties": {
                "description": {"type": "string", "description": "The description of the item"},
                "deal_price": {"type": "number", "description": "The price offered by this deal"},
                "estimated_true_value": {"type": "number", "description": "The estimated actual value"},
                "url": {"type": "string", "description": "The URL of this deal"},
            },
            "required": ["description", "deal_price", "estimated_true_value", "url"],
            "additionalProperties": False,
        },
    }

    def get_tools(self) -> List[Dict]:
        return [
            {"type": "function", "function": self.SCAN_FUNCTION},
            {"type": "function", "function": self.ESTIMATE_FUNCTION},
            {"type": "function", "function": self.NOTIFY_FUNCTION},
        ]

    def handle_tool_call(self, message) -> List[Dict]:
        """Dispatch tool calls from the LLM response."""
        mapping = {
            "scan_the_internet_for_bargains": self.scan_the_internet_for_bargains,
            "estimate_true_value": self.estimate_true_value,
            "notify_user_of_deal": self.notify_user_of_deal,
        }
        results = []
        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            tool = mapping.get(tool_name)
            result = tool(**arguments) if tool else "Unknown tool"
            results.append({
                "role": "tool",
                "content": str(result),
                "tool_call_id": tool_call.id,
            })
        return results

    def plan(self, memory: List[Opportunity] = []) -> Optional[Opportunity]:
        """
        Run the autonomous LLM-driven planning loop.
        :param memory: previously surfaced opportunities
        :return: the best Opportunity if one was notified, else None
        """
        self.log("Autonomous Planning Agent is starting a run")
        self.memory = memory
        self.opportunity = None

        messages = [
            {"role": "system", "content": self.SYSTEM_MESSAGE},
            {"role": "user", "content": self.USER_MESSAGE},
        ]

        done = False
        while not done:
            response = self.openai.chat.completions.create(
                model=self.MODEL,
                messages=messages,
                tools=self.get_tools(),
            )
            if response.choices[0].finish_reason == "tool_calls":
                message = response.choices[0].message
                tool_results = self.handle_tool_call(message)
                messages.append(message)
                messages.extend(tool_results)
            else:
                done = True

        reply = response.choices[0].message.content
        self.log(f"Autonomous Planning Agent completed with: {reply}")
        return self.opportunity
