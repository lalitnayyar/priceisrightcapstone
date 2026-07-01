"""
Unit tests — Core Modules
Tests: deals.py (Deal, DealSelection, Opportunity, ScrapedDeal),
       preprocessor.py (Preprocessor),
       log_utils.py (reformat, html_for)
"""
import sys
import os
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# Test: Deal data model
# ---------------------------------------------------------------------------
class TestDealModel(unittest.TestCase):
    """Tests for the Deal Pydantic model."""

    def setUp(self):
        from app.core.deals import Deal
        self.Deal = Deal

    def test_deal_creation_valid(self):
        deal = self.Deal(
            product_description="Sony WH-1000XM5 wireless noise-cancelling headphones.",
            price=249.99,
            url="https://example.com/deal/sony-headphones"
        )
        self.assertEqual(deal.price, 249.99)
        self.assertIn("Sony", deal.product_description)
        self.assertTrue(deal.url.startswith("https://"))

    def test_deal_price_zero(self):
        deal = self.Deal(
            product_description="Free sample product.",
            price=0.0,
            url="https://example.com/free"
        )
        self.assertEqual(deal.price, 0.0)

    def test_deal_price_large(self):
        deal = self.Deal(
            product_description="High-end gaming laptop with RTX 4090.",
            price=3999.99,
            url="https://example.com/laptop"
        )
        self.assertGreater(deal.price, 1000)

    def test_deal_missing_url_raises(self):
        with self.assertRaises(Exception):
            self.Deal(product_description="Test", price=10.0)

    def test_deal_missing_price_raises(self):
        with self.assertRaises(Exception):
            self.Deal(product_description="Test", url="https://example.com")

    def test_deal_fields_are_accessible(self):
        from app.core.deals import Deal
        deal = Deal(product_description="Test product", price=99.0, url="https://ex.com")
        self.assertEqual(deal.product_description, "Test product")
        self.assertEqual(deal.price, 99.0)
        self.assertEqual(deal.url, "https://ex.com")


# ---------------------------------------------------------------------------
# Test: DealSelection data model
# ---------------------------------------------------------------------------
class TestDealSelectionModel(unittest.TestCase):
    """Tests for the DealSelection Pydantic model."""

    def setUp(self):
        from app.core.deals import Deal, DealSelection
        self.Deal = Deal
        self.DealSelection = DealSelection

    def _make_deal(self, i=1):
        return self.Deal(
            product_description=f"Product {i} description.",
            price=float(i * 10),
            url=f"https://example.com/deal/{i}"
        )

    def test_deal_selection_empty(self):
        ds = self.DealSelection(deals=[])
        self.assertEqual(len(ds.deals), 0)

    def test_deal_selection_five_deals(self):
        deals = [self._make_deal(i) for i in range(1, 6)]
        ds = self.DealSelection(deals=deals)
        self.assertEqual(len(ds.deals), 5)

    def test_deal_selection_prices_preserved(self):
        deals = [self._make_deal(i) for i in range(1, 4)]
        ds = self.DealSelection(deals=deals)
        prices = [d.price for d in ds.deals]
        self.assertEqual(prices, [10.0, 20.0, 30.0])

    def test_deal_selection_is_iterable(self):
        deals = [self._make_deal(i) for i in range(1, 3)]
        ds = self.DealSelection(deals=deals)
        for d in ds.deals:
            self.assertIsNotNone(d.url)


# ---------------------------------------------------------------------------
# Test: Opportunity data model
# ---------------------------------------------------------------------------
class TestOpportunityModel(unittest.TestCase):
    """Tests for the Opportunity Pydantic model."""

    def setUp(self):
        from app.core.deals import Deal, Opportunity
        self.deal = Deal(
            product_description="Apple AirPods Pro 2nd generation.",
            price=189.99,
            url="https://example.com/airpods"
        )
        self.Opportunity = Opportunity

    def test_opportunity_creation(self):
        opp = self.Opportunity(deal=self.deal, estimate=249.99, discount=60.0)
        self.assertEqual(opp.discount, 60.0)
        self.assertEqual(opp.estimate, 249.99)
        self.assertEqual(opp.deal.price, 189.99)

    def test_opportunity_negative_discount(self):
        """A deal where estimated value is below asking price — negative discount."""
        opp = self.Opportunity(deal=self.deal, estimate=150.0, discount=-39.99)
        self.assertLess(opp.discount, 0)

    def test_opportunity_zero_discount(self):
        opp = self.Opportunity(deal=self.deal, estimate=189.99, discount=0.0)
        self.assertEqual(opp.discount, 0.0)

    def test_opportunity_deal_reference_preserved(self):
        opp = self.Opportunity(deal=self.deal, estimate=300.0, discount=110.01)
        self.assertEqual(opp.deal.url, "https://example.com/airpods")


# ---------------------------------------------------------------------------
# Test: ScrapedDeal
# ---------------------------------------------------------------------------
class TestScrapedDeal(unittest.TestCase):
    """Tests for the ScrapedDeal RSS scraper class."""

    def _make_entry(self, title="Test Product", summary="<p>A great deal on electronics.</p>",
                    url="https://example.com/deal/1"):
        return {
            "title": title,
            "summary": summary,
            "links": [{"href": url}]
        }

    @patch("app.core.deals.requests.get")
    def test_scraped_deal_init_with_content_section(self, mock_get):
        """ScrapedDeal should parse content-section div when present."""
        from app.core.deals import ScrapedDeal
        html = '<div class="content-section">Great laptop. Features: Fast CPU, 16GB RAM.</div>'
        mock_resp = MagicMock()
        mock_resp.content = html.encode()
        mock_get.return_value = mock_resp

        deal = ScrapedDeal(self._make_entry())
        self.assertIn("laptop", deal.details.lower())
        self.assertIsInstance(deal.title, str)
        self.assertIsInstance(deal.url, str)

    @patch("app.core.deals.requests.get")
    def test_scraped_deal_fallback_to_summary(self, mock_get):
        """ScrapedDeal should fall back to RSS summary when no content-section."""
        from app.core.deals import ScrapedDeal
        mock_resp = MagicMock()
        mock_resp.content = b"<html><body><p>No content section here.</p></body></html>"
        mock_get.return_value = mock_resp

        entry = self._make_entry(summary="<p>Fallback summary text.</p>")
        deal = ScrapedDeal(entry)
        self.assertIn("Fallback", deal.details)

    @patch("app.core.deals.requests.get")
    def test_scraped_deal_truncation(self, mock_get):
        """ScrapedDeal.truncate() should cap fields at their max lengths."""
        from app.core.deals import ScrapedDeal
        mock_resp = MagicMock()
        mock_resp.content = b"<html><body></body></html>"
        mock_get.return_value = mock_resp

        long_title = "X" * 200
        entry = self._make_entry(title=long_title)
        deal = ScrapedDeal(entry)
        self.assertLessEqual(len(deal.title), 100)

    @patch("app.core.deals.requests.get")
    def test_scraped_deal_describe(self, mock_get):
        """ScrapedDeal.describe() should return a formatted string."""
        from app.core.deals import ScrapedDeal
        mock_resp = MagicMock()
        mock_resp.content = b"<html><body></body></html>"
        mock_get.return_value = mock_resp

        deal = ScrapedDeal(self._make_entry())
        desc = deal.describe()
        self.assertIn("Title:", desc)
        self.assertIn("URL:", desc)

    @patch("app.core.deals.requests.get", side_effect=Exception("Network error"))
    def test_scraped_deal_network_failure_graceful(self, mock_get):
        """ScrapedDeal should not raise when network request fails."""
        from app.core.deals import ScrapedDeal
        entry = self._make_entry()
        deal = ScrapedDeal(entry)
        self.assertIsNotNone(deal.details)

    @patch("app.core.deals.feedparser.parse")
    @patch("app.core.deals.requests.get")
    def test_scraped_deal_fetch(self, mock_get, mock_parse):
        """ScrapedDeal.fetch() should return a list of deals."""
        from app.core.deals import ScrapedDeal
        mock_get.return_value = MagicMock(content=b"<html><body></body></html>")
        mock_parse.return_value = MagicMock(entries=[
            {"title": "Deal 1", "summary": "<p>Summary 1</p>", "links": [{"href": "https://ex.com/1"}]},
            {"title": "Deal 2", "summary": "<p>Summary 2</p>", "links": [{"href": "https://ex.com/2"}]},
        ])
        deals = ScrapedDeal.fetch()
        self.assertIsInstance(deals, list)


# ---------------------------------------------------------------------------
# Test: Preprocessor
# ---------------------------------------------------------------------------
class TestPreprocessor(unittest.TestCase):
    """Tests for the Preprocessor LLM-based text rewriting module."""

    def _make_preprocessor(self):
        """Create a Preprocessor with mocked LiteLLM completion."""
        with patch("app.core.preprocessor.completion") as mock_completion:
            mock_completion.return_value = MagicMock(
                choices=[MagicMock(message=MagicMock(content="Title: Sony Headphones\nCategory: Electronics\nBrand: Sony"))]
            )
            from app.core.preprocessor import Preprocessor
            pp = Preprocessor()
            pp._mock_completion = mock_completion
            return pp, mock_completion

    def test_preprocessor_instantiation(self):
        pp, _ = self._make_preprocessor()
        self.assertIsNotNone(pp)

    def test_preprocessor_has_model_name(self):
        pp, _ = self._make_preprocessor()
        self.assertTrue(hasattr(pp, "model_name"))
        self.assertIsInstance(pp.model_name, str)

    def test_preprocessor_has_messages_for(self):
        pp, _ = self._make_preprocessor()
        self.assertTrue(hasattr(pp, "messages_for"))
        msgs = pp.messages_for("test product text")
        self.assertIsInstance(msgs, list)
        self.assertGreater(len(msgs), 0)

    def test_messages_for_contains_system_and_user(self):
        pp, _ = self._make_preprocessor()
        msgs = pp.messages_for("Sony headphones")
        roles = [m["role"] for m in msgs]
        self.assertIn("system", roles)
        self.assertIn("user", roles)

    def test_messages_for_user_content_matches_input(self):
        pp, _ = self._make_preprocessor()
        text = "Apple AirPods Pro 2nd generation"
        msgs = pp.messages_for(text)
        user_msg = next(m for m in msgs if m["role"] == "user")
        self.assertIn(text, user_msg["content"])

    def test_preprocess_calls_completion(self):
        """preprocess() should call the LLM completion function."""
        with patch("app.core.preprocessor.completion") as mock_completion:
            mock_completion.return_value = MagicMock(
                choices=[MagicMock(message=MagicMock(content="Title: Test\nCategory: Electronics\nBrand: Test"))]
            )
            from app.core.preprocessor import Preprocessor
            pp = Preprocessor()
            result = pp.preprocess("raw product description")
            mock_completion.assert_called_once()
            self.assertIsInstance(result, str)

    def test_preprocess_returns_non_empty_string(self):
        """preprocess() should return a non-empty string."""
        with patch("app.core.preprocessor.completion") as mock_completion:
            mock_completion.return_value = MagicMock(
                choices=[MagicMock(message=MagicMock(content="Title: Sony Headphones\nCategory: Electronics"))]
            )
            from app.core.preprocessor import Preprocessor
            pp = Preprocessor()
            result = pp.preprocess("Sony WH-1000XM5 headphones")
            self.assertGreater(len(result), 0)


# ---------------------------------------------------------------------------
# Test: log_utils
# ---------------------------------------------------------------------------
class TestLogUtils(unittest.TestCase):
    """Tests for ANSI-to-HTML log formatting utilities."""

    def setUp(self):
        from app.utils.log_utils import reformat, html_for, COLOR_MAP
        self.reformat = reformat
        self.html_for = html_for
        self.COLOR_MAP = COLOR_MAP

    def test_reformat_plain_text(self):
        """Plain text with no ANSI codes should pass through unchanged."""
        msg = "Hello, world!"
        result = self.reformat(msg)
        self.assertEqual(result, msg)

    def test_reformat_green_color(self):
        """Green ANSI code should become a green HTML span."""
        GREEN = '\033[32m'
        BG_BLACK = '\033[40m'
        RESET = '\033[0m'
        msg = f"{BG_BLACK}{GREEN}[Planning Agent] Ready{RESET}"
        result = self.reformat(msg)
        self.assertIn("<span", result)
        self.assertIn("#00dd00", result)
        self.assertIn("</span>", result)

    def test_reformat_red_color(self):
        """Red ANSI code should become a red HTML span."""
        RED = '\033[31m'
        BG_BLACK = '\033[40m'
        RESET = '\033[0m'
        msg = f"{BG_BLACK}{RED}[Scanner Agent] Error{RESET}"
        result = self.reformat(msg)
        self.assertIn("#dd0000", result)

    def test_reformat_all_colors_mapped(self):
        """All entries in COLOR_MAP should produce valid HTML spans."""
        RESET = '\033[0m'
        for ansi, hex_color in self.COLOR_MAP.items():
            msg = f"{ansi}test{RESET}"
            result = self.reformat(msg)
            self.assertIn(hex_color, result, f"Color {hex_color} not found for ANSI {repr(ansi)}")

    def test_html_for_empty_list(self):
        """html_for([]) should return a valid HTML div."""
        result = self.html_for([])
        self.assertIn("<div", result)
        self.assertIn("</div>", result)

    def test_html_for_truncates_to_max_lines(self):
        """html_for should only include the last max_lines entries."""
        lines = [f"Line {i}" for i in range(100)]
        result = self.html_for(lines, max_lines=10)
        self.assertIn("Line 99", result)
        self.assertNotIn("Line 0", result)

    def test_html_for_contains_scroll_div(self):
        """html_for output should have a scrollable container."""
        result = self.html_for(["test message"])
        self.assertIn("overflow-y: auto", result)
        self.assertIn("scrollContent", result)

    def test_html_for_default_max_lines(self):
        """html_for with default max_lines=18 should show last 18 lines."""
        lines = [f"Line {i}" for i in range(50)]
        result = self.html_for(lines)
        self.assertIn("Line 49", result)
        self.assertNotIn("Line 30", result)

    def test_html_for_single_line(self):
        result = self.html_for(["Only one line"])
        self.assertIn("Only one line", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
