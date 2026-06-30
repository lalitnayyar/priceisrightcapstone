"""
Messaging Agent — Agent 6 of 7 in the Price Is Right framework.

Responsibility: Craft compelling push notification messages using Claude
(via LiteLLM) and deliver them via the Pushover API when a great deal
opportunity is identified.
"""
import os

import requests
from litellm import completion

from app.agents.agent import Agent
from app.core.deals import Opportunity

PUSHOVER_API_URL = "https://api.pushover.net/1/messages.json"


class MessagingAgent(Agent):
    """
    Sends push notifications via Pushover.

    Two notification modes are supported:
    - alert(): sends a concise, auto-formatted alert from an Opportunity object.
    - notify(): uses Claude to craft an engaging 2-3 sentence message before sending.
    """

    name = "Messaging Agent"
    color = Agent.WHITE
    CLAUDE_MODEL = "claude-sonnet-4-5"

    def __init__(self) -> None:
        self.log("Messaging Agent is initializing")
        self.pushover_user = os.getenv("PUSHOVER_USER", "")
        self.pushover_token = os.getenv("PUSHOVER_TOKEN", "")
        if not self.pushover_user or not self.pushover_token:
            self.log(
                "WARNING: PUSHOVER_USER or PUSHOVER_TOKEN not set; "
                "push notifications will be logged only"
            )
        self.log("Messaging Agent is ready")

    def push(self, text: str) -> bool:
        """
        Send a push notification via the Pushover API.
        :param text: message text (max 1024 characters)
        :return: True if the notification was sent successfully
        """
        self.log("Messaging Agent is sending a push notification")
        if not self.pushover_user or not self.pushover_token:
            self.log(f"[PUSH NOTIFICATION — no credentials]: {text}")
            return False
        payload = {
            "user": self.pushover_user,
            "token": self.pushover_token,
            "message": text[:1024],
            "sound": "cashregister",
            "title": "Price Is Right — Deal Alert!",
        }
        try:
            resp = requests.post(PUSHOVER_API_URL, data=payload, timeout=10)
            resp.raise_for_status()
            self.log("Messaging Agent push notification sent successfully")
            return True
        except Exception as exc:
            self.log(f"Messaging Agent push notification failed: {exc}")
            return False

    def alert(self, opportunity: Opportunity) -> None:
        """
        Send a concise alert for the given Opportunity.
        :param opportunity: the deal opportunity to notify about
        """
        text = (
            f"Deal Alert! Price=${opportunity.deal.price:.2f}, "
            f"Estimate=${opportunity.estimate:.2f}, "
            f"Discount=${opportunity.discount:.2f}: "
            f"{opportunity.deal.product_description[:80]}... "
            f"{opportunity.deal.url}"
        )
        self.push(text)
        self.log("Messaging Agent alert completed")

    def craft_message(
        self, description: str, deal_price: float, estimated_true_value: float
    ) -> str:
        """
        Use Claude to craft an engaging push notification message.
        :param description: product description
        :param deal_price: the advertised deal price
        :param estimated_true_value: the estimated true market value
        :return: a 2-3 sentence notification message
        """
        user_prompt = (
            "Please summarize this great deal in 2-3 sentences to be sent as an exciting "
            "push notification alerting the user about this deal.\n"
            f"Item Description: {description}\n"
            f"Offered Price: ${deal_price:.2f}\n"
            f"Estimated true value: ${estimated_true_value:.2f}\n\n"
            "Respond only with the 2-3 sentence message which will be used to alert & excite "
            "the user about this deal."
        )
        response = completion(
            model=self.CLAUDE_MODEL,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.choices[0].message.content

    def notify(
        self,
        description: str,
        deal_price: float,
        estimated_true_value: float,
        url: str,
    ) -> None:
        """
        Craft a Claude-generated message and send it as a push notification.
        :param description: product description
        :param deal_price: advertised price
        :param estimated_true_value: estimated true value
        :param url: deal URL to append to the notification
        """
        self.log("Messaging Agent is using Claude to craft the notification message")
        text = self.craft_message(description, deal_price, estimated_true_value)
        self.push(text[:200] + "... " + url)
        self.log("Messaging Agent notification completed")
