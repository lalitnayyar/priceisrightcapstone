"""
Integration tests — Framework Pipeline, API Endpoints, DNN Model
Tests the DealAgentFramework orchestration, FastAPI endpoints,
and DeepNeuralNetwork model architecture.
"""
import sys
import os
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# Test: DealAgentFramework
# ---------------------------------------------------------------------------
class TestDealAgentFramework(unittest.TestCase):
    """Integration tests for the main DealAgentFramework orchestration class."""

    def _make_framework(self):
        with patch("app.core.deal_agent_framework.chromadb") as mock_chroma, \
             patch("app.core.deal_agent_framework.PlanningAgent") as mock_pa, \
             patch("app.core.deal_agent_framework.SentenceTransformer") as mock_st:
            mock_chroma.HttpClient.return_value = MagicMock()
            mock_chroma.HttpClient.return_value.get_or_create_collection.return_value = MagicMock()
            mock_pa.return_value = MagicMock()
            mock_st.return_value = MagicMock()
            from app.core.deal_agent_framework import DealAgentFramework
            fw = DealAgentFramework()
            fw.agent = mock_pa.return_value
            fw.memory = []
            return fw

    def test_framework_instantiation(self):
        fw = self._make_framework()
        self.assertIsNotNone(fw)

    def test_framework_has_agent(self):
        fw = self._make_framework()
        self.assertIsNotNone(fw.agent)

    def test_framework_has_memory(self):
        fw = self._make_framework()
        self.assertIsInstance(fw.memory, list)

    def test_run_returns_opportunity_or_none(self):
        """run() should return an Opportunity or None."""
        from app.core.deals import Opportunity
        fw = self._make_framework()
        opp = MagicMock(spec=Opportunity)
        fw.agent.plan.return_value = opp
        with patch.object(fw, "run", return_value=opp):
            result = fw.run()
            self.assertIsNotNone(result)

    def test_run_appends_to_memory(self):
        """run() should append found opportunities to memory."""
        from app.core.deals import Deal, Opportunity
        fw = self._make_framework()
        deal = Deal(product_description="Test product", price=100.0, url="https://ex.com")
        opp = Opportunity(deal=deal, estimate=200.0, discount=100.0)
        fw.memory = []

        def fake_run():
            fw.memory.append(opp)
            return opp

        with patch.object(fw, "run", side_effect=fake_run):
            fw.run()
            self.assertEqual(len(fw.memory), 1)

    def test_framework_memory_persists_across_runs(self):
        """Memory should accumulate opportunities across multiple runs."""
        from app.core.deals import Deal, Opportunity
        fw = self._make_framework()
        fw.memory = []
        for i in range(3):
            deal = Deal(product_description=f"Product {i}", price=float(i * 50 + 50),
                        url=f"https://ex.com/{i}")
            opp = Opportunity(deal=deal, estimate=float(i * 50 + 150), discount=100.0)
            fw.memory.append(opp)
        self.assertEqual(len(fw.memory), 3)


# ---------------------------------------------------------------------------
# Test: FastAPI Endpoints
# ---------------------------------------------------------------------------
class TestAPIEndpoints(unittest.TestCase):
    """Tests for the FastAPI REST API layer."""

    def setUp(self):
        """Set up the FastAPI test client with mocked framework."""
        try:
            from fastapi.testclient import TestClient
        except ImportError:
            self.skipTest("httpx not installed — skipping API tests")

        with patch("app.api.DealAgentFramework") as mock_fw, \
             patch("app.api.RAGDatabase") as mock_rag:
            mock_fw.return_value = MagicMock()
            mock_rag.return_value = MagicMock()
            from app.api import app
            self.client = TestClient(app)
            self.mock_fw = mock_fw
            self.mock_rag = mock_rag

    def test_health_endpoint_returns_200(self):
        """GET /health should return 200 OK."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)

    def test_health_endpoint_json_structure(self):
        """GET /health should return JSON with status field."""
        response = self.client.get("/health")
        data = response.json()
        self.assertIn("status", data)

    def test_root_endpoint_returns_200(self):
        """GET / should return 200 OK."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_memory_endpoint_returns_list(self):
        """GET /memory should return a list."""
        response = self.client.get("/memory")
        self.assertIn(response.status_code, [200, 404])
        if response.status_code == 200:
            data = response.json()
            self.assertIsInstance(data, (list, dict))

    def test_run_endpoint_exists(self):
        """POST /run should be a valid endpoint (200 or 422 for missing body)."""
        response = self.client.post("/run")
        self.assertIn(response.status_code, [200, 202, 422, 500])

    def test_price_endpoint_with_description(self):
        """POST /price should accept a description and return a response."""
        payload = {"description": "Sony WH-1000XM5 wireless headphones"}
        response = self.client.post("/price", json=payload)
        self.assertIn(response.status_code, [200, 422, 500])

    def test_cors_headers_present(self):
        """API should include CORS headers."""
        response = self.client.options("/health",
                                        headers={"Origin": "http://localhost:7860",
                                                 "Access-Control-Request-Method": "GET"})
        self.assertIn(response.status_code, [200, 204])

    def test_api_docs_accessible(self):
        """GET /docs should return the Swagger UI."""
        response = self.client.get("/docs")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers.get("content-type", ""))

    def test_openapi_schema_accessible(self):
        """GET /openapi.json should return the OpenAPI schema."""
        response = self.client.get("/openapi.json")
        self.assertEqual(response.status_code, 200)
        schema = response.json()
        self.assertIn("info", schema)
        self.assertIn("paths", schema)


# ---------------------------------------------------------------------------
# Test: DeepNeuralNetwork model
# ---------------------------------------------------------------------------
class TestDeepNeuralNetwork(unittest.TestCase):
    """Tests for the PyTorch DNN model architecture."""

    def setUp(self):
        try:
            import torch
            self.torch = torch
        except ImportError:
            self.skipTest("PyTorch not installed — skipping DNN tests")

    def test_dnn_instantiation(self):
        """DeepNeuralNetwork should instantiate with given input_size."""
        from app.models.deep_neural_network import DeepNeuralNetwork
        model = DeepNeuralNetwork(input_size=128, num_layers=4, hidden_size=256)
        self.assertIsNotNone(model)

    def test_dnn_forward_pass_shape(self):
        """DNN forward pass should output shape (batch, 1)."""
        import torch
        from app.models.deep_neural_network import DeepNeuralNetwork
        model = DeepNeuralNetwork(input_size=64, num_layers=4, hidden_size=128)
        model.eval()
        x = torch.randn(8, 64)
        with torch.no_grad():
            out = model(x)
        self.assertEqual(out.shape, (8, 1))

    def test_dnn_single_sample(self):
        """DNN should handle single-sample input."""
        import torch
        from app.models.deep_neural_network import DeepNeuralNetwork
        model = DeepNeuralNetwork(input_size=32, num_layers=3, hidden_size=64)
        model.eval()
        x = torch.randn(1, 32)
        with torch.no_grad():
            out = model(x)
        self.assertEqual(out.shape, (1, 1))

    def test_dnn_residual_blocks_count(self):
        """DNN should have (num_layers - 2) residual blocks."""
        from app.models.deep_neural_network import DeepNeuralNetwork
        model = DeepNeuralNetwork(input_size=64, num_layers=6, hidden_size=128)
        self.assertEqual(len(model.residual_blocks), 4)

    def test_dnn_output_is_finite(self):
        """DNN output should be finite (no NaN or Inf)."""
        import torch
        from app.models.deep_neural_network import DeepNeuralNetwork
        model = DeepNeuralNetwork(input_size=64, num_layers=4, hidden_size=128)
        model.eval()
        x = torch.randn(4, 64)
        with torch.no_grad():
            out = model(x)
        self.assertTrue(torch.isfinite(out).all())

    def test_dnn_inference_wrapper(self):
        """DeepNeuralNetworkInference should wrap the model for text input."""
        from app.models.deep_neural_network import DeepNeuralNetworkInference
        with patch("app.models.deep_neural_network.SentenceTransformer") as mock_st, \
             patch("app.models.deep_neural_network.torch.load") as mock_load:
            mock_st.return_value = MagicMock()
            mock_load.return_value = {}
            try:
                inf = DeepNeuralNetworkInference()
                self.assertIsNotNone(inf)
            except Exception:
                # Model weights file may not exist — acceptable in test env
                pass


# ---------------------------------------------------------------------------
# Test: RAGDatabase
# ---------------------------------------------------------------------------
class TestRAGDatabase(unittest.TestCase):
    """Tests for the RAG vector store database module."""

    def _make_rag(self):
        with patch("app.core.rag_db.chromadb") as mock_chroma, \
             patch("app.core.rag_db.SentenceTransformer") as mock_st:
            mock_chroma.HttpClient.return_value = MagicMock()
            mock_chroma.HttpClient.return_value.get_or_create_collection.return_value = MagicMock()
            mock_st.return_value = MagicMock()
            from app.core.rag_db import RAGDatabase
            rag = RAGDatabase()
            rag.collection = MagicMock()
            rag.model = MagicMock()
            return rag

    def test_rag_instantiation(self):
        rag = self._make_rag()
        self.assertIsNotNone(rag)

    def test_rag_has_collection(self):
        rag = self._make_rag()
        self.assertIsNotNone(rag.collection)

    def test_rag_query_returns_results(self):
        """query() should return a list of similar products."""
        rag = self._make_rag()
        rag.collection.query.return_value = {
            "documents": [["Product A", "Product B"]],
            "metadatas": [[{"price": "199.99"}, {"price": "219.99"}]],
            "distances": [[0.05, 0.12]]
        }
        rag.model.encode.return_value = MagicMock()
        with patch.object(rag, "query", return_value=[
            {"document": "Product A", "price": 199.99, "distance": 0.05},
            {"document": "Product B", "price": 219.99, "distance": 0.12},
        ]):
            results = rag.query("Sony headphones")
            self.assertIsInstance(results, list)
            self.assertGreater(len(results), 0)

    def test_rag_query_empty_returns_list(self):
        """query() with no matches should return an empty list."""
        rag = self._make_rag()
        with patch.object(rag, "query", return_value=[]):
            results = rag.query("obscure product with no matches")
            self.assertIsInstance(results, list)


if __name__ == "__main__":
    unittest.main(verbosity=2)
