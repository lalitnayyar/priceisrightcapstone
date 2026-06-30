"""
Planning Agent — Agent 7 of 7 in the Price Is Right framework.

Responsibility: Orchestrate the full deal-hunting workflow by coordinating
the Scanner, Ensemble, and Messaging agents. Evaluates opportunities and
triggers notifications only when the discount exceeds the configured threshold.
"""
from typing import Optional, List

from app.agents.agent import Agent
from app.core.deals import Opportunity, Deal, DealSelection
from app.agents.scanner_agent import ScannerAgent
from app.agents.ensemble_agent import EnsembleAgent
from app.agents.messaging_agent import MessagingAgent


class PlanningAgent(Agent):
    """
    Top-level orchestrator for the Price Is Right multi-agent framework.

    Workflow:
    1. ScannerAgent fetches and filters RSS deals using GPT-5.
    2. EnsembleAgent prices each deal using three sub-agents.
    3. The best opportunity (highest discount) is identified.
    4. MessagingAgent sends a push notification if the discount exceeds
       the DEAL_THRESHOLD.
    """

    name = "Planning Agent"
    color = Agent.GREEN

    # Minimum discount (USD) required to trigger a push notification
    DEAL_THRESHOLD = 50.0

    def __init__(self, collection) -> None:
        """
        Instantiate the three coordinated agents.
        :param collection: ChromaDB collection passed through to FrontierAgent
        """
        self.log("Planning Agent is initializing")
        self.scanner = ScannerAgent()
        self.ensemble = EnsembleAgent(collection)
        self.messenger = MessagingAgent()
        self.log("Planning Agent is ready")

    def run(self, deal: Deal) -> Opportunity:
        """
        Price a single deal and return an Opportunity.
        :param deal: a Deal object from the scanner
        :return: an Opportunity with estimate and discount fields populated
        """
        self.log(f"Planning Agent is pricing: {deal.product_description[:60]}...")
        estimate = self.ensemble.price(deal.product_description)
        discount = estimate - deal.price
        self.log(f"Planning Agent priced deal — estimate=${estimate:.2f}, discount=${discount:.2f}")
        return Opportunity(deal=deal, estimate=estimate, discount=discount)

    def plan(self, memory: List[Opportunity] = []) -> Optional[Opportunity]:
        """
        Execute the full deal-hunting workflow.

        1. Scan RSS feeds for new deals (filtered against memory).
        2. Price the top 5 deals using the Ensemble Agent.
        3. Sort by discount and identify the best opportunity.
        4. Send a push notification if the discount exceeds DEAL_THRESHOLD.

        :param memory: list of previously surfaced Opportunity objects
        :return: the best Opportunity if it exceeds the threshold, else None
        """
        self.log("Planning Agent is starting a new run")
        selection: Optional[DealSelection] = self.scanner.scan(memory=memory)

        if not selection:
            self.log("Planning Agent found no new deals; run complete")
            return None

        opportunities = [self.run(deal) for deal in selection.deals[:5]]
        opportunities.sort(key=lambda opp: opp.discount, reverse=True)
        best = opportunities[0]

        self.log(
            f"Planning Agent identified best deal: discount=${best.discount:.2f} "
            f"(threshold=${self.DEAL_THRESHOLD:.2f})"
        )

        if best.discount > self.DEAL_THRESHOLD:
            self.log("Planning Agent is triggering push notification for great deal")
            self.messenger.alert(best)
            self.log("Planning Agent run complete — opportunity surfaced")
            return best
        else:
            self.log(
                f"Planning Agent run complete — best discount ${best.discount:.2f} "
                f"is below threshold ${self.DEAL_THRESHOLD:.2f}; no notification sent"
            )
            return None
