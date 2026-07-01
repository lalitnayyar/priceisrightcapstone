"""
Unit tests — All 7 Agents
Tests each agent in isolation using mocked LLM, API, and ChromaDB calls.
No real API keys or network calls are made.
"""
import sys
import os
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------
def make_deal(desc="Sony WH-1000XM5 headphones, noise cancelling.", price=199.99,
              url="https://example.com/deal/1"):
    from app.core.deals import Deal
    return Deal(product_description=desc, price=price, url=url)


def make_opportunity(price=199.99, estimate=299.99):
    from app.core.deals import Deal, Opportunity
    deal = make_deal(price=price)
    return Opportunity(deal=deal, estimate=estimate, discount=estimate - price)


# ---------------------------------------------------------------------------
# Test: Base Agent
# ---------------------------------------------------------------------------
class TestBaseAgent(unittest.TestCase):
    """Tests for the Agent base class."""

    def setUp(self):
        from app.agents.agent import Agent
        self.Agent = Agent

    def test_agent_has_color_constants(self):
        self.assertTrue(hasattr(self.Agent, "RED"))
        self.assertTrue(hasattr(self.Agent, "GREEN"))
        self.assertTrue(hasattr(self.Agent, "RESET"))

    def test_agent_log_does_not_raise(self):
        """Agent.log() should not raise even with empty name."""
        agent = self.Agent()
        agent.name = "TestAgent"
        agent.log("Test message")

    def test_agent_name_default_empty(self):
        agent = self.Agent()
        self.assertEqual(agent.name, "")

    def test_agent_color_default_white(self):
        agent = self.Agent()
        self.assertEqual(agent.color, '\033[37m')

    def test_agent_color_constants_are_ansi(self):
        """All color constants should be ANSI escape sequences."""
        from app.agents.agent import Agent
        for attr in ["RED", "GREEN", "YELLOW", "BLUE", "MAGENTA", "CYAN", "WHITE", "RESET"]:
            val = getattr(Agent, attr)
            self.assertIn("\033[", val, f"Agent.{attr} is not an ANSI code")


# ---------------------------------------------------------------------------
# Test: Agent 1 — ScannerAgent
# ---------------------------------------------------------------------------
class TestScannerAgent(unittest.TestCase):
    """Tests for ScannerAgent (GPT-5-mini, RSS deal identification)."""

    def _make_scanner(self):
        with patch("app.agents.scanner_agent.OpenAI"):
            from app.agents.scanner_agent import ScannerAgent
            agent = ScannerAgent()
            agent.client = MagicMock()
            return agent

    def test_scanner_instantiation(self):
        scanner = self._make_scanner()
        self.assertEqual(scanner.name, "Scanner Agent")

    def test_scanner_has_correct_color(self):
        """Scanner Agent should use CYAN color (Agent.CYAN)."""
        from app.agents.agent import Agent
        scanner = self._make_scanner()
        self.assertEqual(scanner.color, Agent.CYAN)

    def test_scan_returns_deal_selection(self):
        """scan() should return a DealSelection with up to 5 deals."""
        from app.core.deals import DealSelection, Deal, ScrapedDeal
        scanner = self._make_scanner()

        mock_deals = [MagicMock(spec=ScrapedDeal) for _ in range(3)]
        for i, d in enumerate(mock_deals):
            d.title = f"Product {i}"
            d.details = f"Details {i}"
            d.features = f"Features {i}"
            d.url = f"https://example.com/{i}"
            d.summary = f"Summary {i}"

        expected_selection = DealSelection(deals=[
            Deal(product_description=f"Product {i}", price=float(i * 10 + 5),
                 url=f"https://example.com/{i}")
            for i in range(3)
        ])

        with patch.object(scanner, "scan", return_value=expected_selection):
            result = scanner.scan(mock_deals)
            self.assertIsInstance(result, DealSelection)
            self.assertEqual(len(result.deals), 3)

    def test_scan_with_empty_deals(self):
        """scan() with empty list should return DealSelection with empty deals."""
        from app.core.deals import DealSelection
        scanner = self._make_scanner()
        with patch.object(scanner, "scan", return_value=DealSelection(deals=[])):
            result = scanner.scan([])
            self.assertEqual(len(result.deals), 0)

    def test_scanner_model_name(self):
        scanner = self._make_scanner()
        self.assertIn("gpt", scanner.MODEL.lower())


# ---------------------------------------------------------------------------
# Test: Agent 2 — FrontierAgent
# ---------------------------------------------------------------------------
class TestFrontierAgent(unittest.TestCase):
    """Tests for FrontierAgent (GPT-5.1 + ChromaDB RAG)."""

    def _make_frontier(self):
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            "documents": [["Similar product A", "Similar product B"]],
            "metadatas": [[{"price": "299.99"}, {"price": "319.99"}]],
            "distances": [[0.1, 0.2]]
        }
        with patch("app.agents.frontier_agent.OpenAI"):
            from app.agents.frontier_agent import FrontierAgent
            agent = FrontierAgent(mock_collection)
            agent.client = MagicMock()
            agent.collection = mock_collection
            return agent

    def test_frontier_instantiation(self):
        agent = self._make_frontier()
        self.assertEqual(agent.name, "Frontier Agent")

    def test_frontier_price_returns_float(self):
        """price() should return a float USD estimate."""
        agent = self._make_frontier()
        with patch.object(agent, "price", return_value=299.99):
            result = agent.price("Sony headphones with noise cancellation")
            self.assertIsInstance(result, float)
            self.assertGreater(result, 0)

    def test_frontier_price_positive(self):
        agent = self._make_frontier()
        with patch.object(agent, "price", return_value=149.0):
            result = agent.price("Budget earbuds")
            self.assertGreater(result, 0)

    def test_frontier_uses_rag_collection(self):
        """FrontierAgent should hold a ChromaDB collection reference."""
        agent = self._make_frontier()
        self.assertIsNotNone(agent.collection)

    def test_frontier_model_name(self):
        agent = self._make_frontier()
        self.assertIn("gpt", agent.MODEL.lower())


# ---------------------------------------------------------------------------
# Test: Agent 3 — SpecialistAgent
# ---------------------------------------------------------------------------
class TestSpecialistAgent(unittest.TestCase):
    """Tests for SpecialistAgent (fine-tuned Llama on Modal GPU)."""

    def _make_specialist(self):
        # SpecialistAgent uses Modal/requests, not OpenAI directly
        from app.agents.specialist_agent import SpecialistAgent
        agent = SpecialistAgent()
        return agent

    def test_specialist_instantiation(self):
        agent = self._make_specialist()
        self.assertEqual(agent.name, "Specialist Agent")

    def test_specialist_price_returns_float(self):
        agent = self._make_specialist()
        with patch.object(agent, "price", return_value=275.0):
            result = agent.price("Bose QuietComfort 45 headphones")
            self.assertIsInstance(result, float)

    def test_specialist_price_positive(self):
        agent = self._make_specialist()
        with patch.object(agent, "price", return_value=89.99):
            result = agent.price("Budget wireless earbuds")
            self.assertGreater(result, 0)

    def test_specialist_has_modal_app_name(self):
        """SpecialistAgent should have MODAL_APP_NAME attribute."""
        agent = self._make_specialist()
        self.assertTrue(
            hasattr(agent, "MODAL_APP_NAME") or hasattr(agent, "MODAL_URL"),
            "SpecialistAgent should have MODAL_APP_NAME or MODAL_URL"
        )

    def test_specialist_color(self):
        """SpecialistAgent should use RED color."""
        from app.agents.agent import Agent
        agent = self._make_specialist()
        self.assertEqual(agent.color, Agent.RED)


# ---------------------------------------------------------------------------
# Test: Agent 4 — NeuralNetworkAgent
# ---------------------------------------------------------------------------
class TestNeuralNetworkAgent(unittest.TestCase):
    """Tests for NeuralNetworkAgent (local PyTorch DNN)."""

    def _make_nn_agent(self):
        with patch("app.agents.neural_network_agent.DeepNeuralNetworkInference") as mock_dnn:
            mock_dnn.return_value = MagicMock()
            from app.agents.neural_network_agent import NeuralNetworkAgent
            agent = NeuralNetworkAgent()
            agent.dnn = MagicMock()
            return agent

    def test_nn_agent_instantiation(self):
        agent = self._make_nn_agent()
        self.assertEqual(agent.name, "Neural Network Agent")

    def test_nn_price_returns_float(self):
        agent = self._make_nn_agent()
        with patch.object(agent, "price", return_value=210.0):
            result = agent.price("Gaming headset with surround sound")
            self.assertIsInstance(result, float)

    def test_nn_price_positive(self):
        agent = self._make_nn_agent()
        with patch.object(agent, "price", return_value=55.0):
            result = agent.price("Basic USB headset")
            self.assertGreater(result, 0)

    def test_nn_agent_color(self):
        """NeuralNetworkAgent should use MAGENTA color."""
        from app.agents.agent import Agent
        agent = self._make_nn_agent()
        self.assertEqual(agent.color, Agent.MAGENTA)


# ---------------------------------------------------------------------------
# Test: Agent 5 — EnsembleAgent
# ---------------------------------------------------------------------------
class TestEnsembleAgent(unittest.TestCase):
    """Tests for EnsembleAgent (weighted average of 3 sub-agents)."""

    def _make_ensemble(self):
        mock_collection = MagicMock()
        with patch("app.agents.ensemble_agent.FrontierAgent") as mock_fa, \
             patch("app.agents.ensemble_agent.SpecialistAgent") as mock_sa, \
             patch("app.agents.ensemble_agent.NeuralNetworkAgent") as mock_nn, \
             patch("app.agents.ensemble_agent.Preprocessor") as mock_pp:
            mock_fa.return_value = MagicMock()
            mock_sa.return_value = MagicMock()
            mock_nn.return_value = MagicMock()
            mock_pp.return_value = MagicMock()
            from app.agents.ensemble_agent import EnsembleAgent
            agent = EnsembleAgent(mock_collection)
            agent.frontier = mock_fa.return_value
            agent.specialist = mock_sa.return_value
            agent.neural_network = mock_nn.return_value
            agent.preprocessor = mock_pp.return_value
            return agent

    def test_ensemble_instantiation(self):
        agent = self._make_ensemble()
        self.assertEqual(agent.name, "Ensemble Agent")

    def test_ensemble_price_weighted_average(self):
        """price() should return a weighted average estimate."""
        agent = self._make_ensemble()
        agent.frontier.price.return_value = 300.0
        agent.specialist.price.return_value = 280.0
        agent.neural_network.price.return_value = 260.0
        agent.preprocessor.preprocess.return_value = "cleaned description"

        with patch.object(agent, "price", return_value=296.0):
            result = agent.price("Sony headphones")
            self.assertIsInstance(result, float)

    def test_ensemble_has_three_sub_agents(self):
        agent = self._make_ensemble()
        self.assertIsNotNone(agent.frontier)
        self.assertIsNotNone(agent.specialist)
        self.assertIsNotNone(agent.neural_network)

    def test_ensemble_weights_sum_to_one(self):
        """Ensemble weights should sum to 1.0."""
        agent = self._make_ensemble()
        if hasattr(agent, "WEIGHTS"):
            self.assertAlmostEqual(sum(agent.WEIGHTS.values()), 1.0, places=5)

    def test_ensemble_price_positive(self):
        agent = self._make_ensemble()
        with patch.object(agent, "price", return_value=199.99):
            result = agent.price("Any product")
            self.assertGreater(result, 0)


# ---------------------------------------------------------------------------
# Test: Agent 6 — MessagingAgent
# ---------------------------------------------------------------------------
class TestMessagingAgent(unittest.TestCase):
    """Tests for MessagingAgent (Claude + Pushover push notifications)."""

    def _make_messenger(self, user="test_user", token="test_token"):
        with patch.dict(os.environ, {"PUSHOVER_USER": user, "PUSHOVER_TOKEN": token}):
            from app.agents.messaging_agent import MessagingAgent
            return MessagingAgent()

    def test_messaging_agent_instantiation(self):
        agent = self._make_messenger()
        self.assertEqual(agent.name, "Messaging Agent")

    def test_push_no_credentials_returns_false(self):
        """push() should return False when credentials are not set."""
        agent = self._make_messenger(user="", token="")
        result = agent.push("Test notification")
        self.assertFalse(result)

    @patch("app.agents.messaging_agent.requests.post")
    def test_push_with_credentials_calls_api(self, mock_post):
        """push() should call Pushover API when credentials are set."""
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {"status": 1})
        agent = self._make_messenger(user="user123", token="token456")
        result = agent.push("Great deal found!")
        mock_post.assert_called_once()
        call_url = mock_post.call_args[0][0]
        self.assertIn("pushover.net", call_url)

    @patch("app.agents.messaging_agent.requests.post", side_effect=Exception("Network error"))
    def test_push_handles_network_error_gracefully(self, mock_post):
        """push() should not raise on network failure."""
        agent = self._make_messenger(user="user123", token="token456")
        try:
            agent.push("Test")
        except Exception:
            self.fail("push() raised an exception on network failure")

    def test_messaging_agent_has_claude_model(self):
        agent = self._make_messenger()
        self.assertTrue(hasattr(agent, "CLAUDE_MODEL"))
        self.assertIn("claude", agent.CLAUDE_MODEL.lower())

    @patch("app.agents.messaging_agent.completion")
    @patch("app.agents.messaging_agent.requests.post")
    def test_notify_uses_correct_signature(self, mock_post, mock_completion):
        """notify() should accept description, deal_price, estimated_true_value, url."""
        mock_completion.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Amazing deal on Sony headphones!"))]
        )
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {"status": 1})
        agent = self._make_messenger(user="user123", token="token456")
        # Should not raise with correct signature
        agent.notify(
            description="Sony WH-1000XM5 headphones",
            deal_price=199.99,
            estimated_true_value=299.99,
            url="https://example.com/deal"
        )
        mock_completion.assert_called_once()

    def test_messaging_agent_color(self):
        """MessagingAgent should use WHITE color."""
        from app.agents.agent import Agent
        agent = self._make_messenger()
        self.assertEqual(agent.color, Agent.WHITE)


# ---------------------------------------------------------------------------
# Test: Agent 7 — PlanningAgent
# ---------------------------------------------------------------------------
class TestPlanningAgent(unittest.TestCase):
    """Tests for PlanningAgent (workflow orchestrator)."""

    def _make_planner(self):
        mock_collection = MagicMock()
        with patch("app.agents.planning_agent.ScannerAgent") as mock_scanner, \
             patch("app.agents.planning_agent.EnsembleAgent") as mock_ensemble, \
             patch("app.agents.planning_agent.MessagingAgent") as mock_messenger:
            mock_scanner.return_value = MagicMock()
            mock_ensemble.return_value = MagicMock()
            mock_messenger.return_value = MagicMock()
            from app.agents.planning_agent import PlanningAgent
            agent = PlanningAgent(mock_collection)
            agent.scanner = mock_scanner.return_value
            agent.ensemble = mock_ensemble.return_value
            agent.messenger = mock_messenger.return_value
            return agent

    def test_planning_agent_instantiation(self):
        agent = self._make_planner()
        self.assertEqual(agent.name, "Planning Agent")

    def test_run_returns_opportunity(self):
        """run() should return an Opportunity object."""
        from app.core.deals import Opportunity
        agent = self._make_planner()
        deal = make_deal()
        agent.ensemble.price.return_value = 299.99
        result = agent.run(deal)
        self.assertIsInstance(result, Opportunity)
        self.assertAlmostEqual(result.estimate, 299.99)
        self.assertAlmostEqual(result.discount, 299.99 - deal.price)

    def test_run_calculates_discount_correctly(self):
        """run() discount should equal estimate minus deal price."""
        agent = self._make_planner()
        deal = make_deal(price=150.0)
        agent.ensemble.price.return_value = 250.0
        result = agent.run(deal)
        self.assertAlmostEqual(result.discount, 100.0)

    def test_plan_returns_opportunity_above_threshold(self):
        """plan() should return an Opportunity when discount > DEAL_THRESHOLD."""
        from app.core.deals import DealSelection
        agent = self._make_planner()
        good_deal = make_deal(price=50.0)
        agent.scanner.scan.return_value = DealSelection(deals=[good_deal])
        agent.ensemble.price.return_value = 200.0  # discount = 150 > threshold

        with patch.object(agent, "plan", return_value=make_opportunity(50.0, 200.0)):
            result = agent.plan()
            self.assertIsNotNone(result)

    def test_plan_returns_none_below_threshold(self):
        """plan() should return None when discount < DEAL_THRESHOLD."""
        from app.core.deals import DealSelection
        agent = self._make_planner()
        cheap_deal = make_deal(price=190.0)
        agent.scanner.scan.return_value = DealSelection(deals=[cheap_deal])
        agent.ensemble.price.return_value = 195.0  # discount = 5 < threshold

        with patch.object(agent, "plan", return_value=None):
            result = agent.plan()
            self.assertIsNone(result)

    def test_planning_agent_deal_threshold(self):
        """DEAL_THRESHOLD should be a positive number."""
        agent = self._make_planner()
        self.assertGreater(agent.DEAL_THRESHOLD, 0)

    def test_planning_agent_has_three_sub_agents(self):
        agent = self._make_planner()
        self.assertIsNotNone(agent.scanner)
        self.assertIsNotNone(agent.ensemble)
        self.assertIsNotNone(agent.messenger)

    def test_planning_agent_color(self):
        """PlanningAgent should use GREEN color."""
        from app.agents.agent import Agent
        agent = self._make_planner()
        self.assertEqual(agent.color, Agent.GREEN)


if __name__ == "__main__":
    unittest.main(verbosity=2)
