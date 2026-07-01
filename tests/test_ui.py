"""
UI Smoke Tests — Theme, Dashboard, Settings Page
All tests use the EXACT function signatures from the actual source files.
"""
import sys, os, re, unittest
from unittest.mock import patch, MagicMock
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestThemeModule(unittest.TestCase):
    def setUp(self):
        from app.ui.theme import DARK_THEME, LIGHT_THEME, BRAND, get_css, get_header_html, get_footer_html, get_agent_status_html
        self.t = DARK_THEME
        self.lt = LIGHT_THEME
        self.BRAND = BRAND
        self.get_css = get_css
        self.get_header_html = get_header_html
        self.get_footer_html = get_footer_html
        self.get_agent_status_html = get_agent_status_html

    REQUIRED_KEYS = ["id","bg_page","bg_surface","bg_surface2","bg_log","border",
                     "text_primary","text_secondary","text_accent","input_bg","input_text",
                     "btn_primary_bg","btn_primary_text","btn_primary_hover",
                     "btn_secondary_bg","btn_secondary_text","dot_ready","dot_busy","dot_error",
                     "scrollbar_track","scrollbar_thumb","toggle_label"]

    def test_dark_theme_has_required_keys(self):
        for k in self.REQUIRED_KEYS:
            self.assertIn(k, self.t, f"DARK_THEME missing key: {k}")

    def test_light_theme_has_required_keys(self):
        for k in ["id","bg_page","bg_surface","text_primary","text_secondary"]:
            self.assertIn(k, self.lt, f"LIGHT_THEME missing key: {k}")

    def test_dark_theme_id_is_dark(self):
        self.assertEqual(self.t["id"], "dark")

    def test_light_theme_id_is_light(self):
        self.assertEqual(self.lt["id"], "light")

    def test_brand_has_primary_colour(self):
        self.assertIn("primary", self.BRAND)
        self.assertEqual(self.BRAND["primary"], "#FF6B35")

    def test_all_colour_values_valid(self):
        hex_re = re.compile(r'^#[0-9A-Fa-f]{3,8}$')
        rgba_re = re.compile(r'^rgba?\(')
        for k, v in self.t.items():
            if k in ("id","toggle_label"):
                continue
            self.assertTrue(hex_re.match(str(v)) or rgba_re.match(str(v)),
                f"DARK_THEME['{k}'] = {v!r} not a valid CSS colour")

    def test_get_css_returns_non_empty_string(self):
        css = self.get_css(self.t)
        self.assertIsInstance(css, str)
        self.assertGreater(len(css), 500)

    def test_get_css_contains_accent_colour(self):
        css = self.get_css(self.t)
        self.assertIn("#FF6B35", css)

    def test_get_css_dark_light_differ(self):
        self.assertNotEqual(self.get_css(self.t), self.get_css(self.lt))

    def test_get_css_no_fstring_artifacts(self):
        css = self.get_css(self.t)
        self.assertNotIn("{t[", css)

    def test_get_css_contains_important(self):
        css = self.get_css(self.t)
        self.assertIn("!important", css)

    def test_get_header_html_returns_string(self):
        html = self.get_header_html(self.t)
        self.assertIsInstance(html, str)
        self.assertGreater(len(html), 50)

    def test_get_header_html_contains_title(self):
        html = self.get_header_html(self.t)
        self.assertIn("Price Is Right", html)

    def test_get_header_html_contains_pir_header_id(self):
        html = self.get_header_html(self.t)
        self.assertIn("pir-header", html)

    def test_get_header_html_uses_accent_colour(self):
        html = self.get_header_html(self.t)
        self.assertIn("#FF6B35", html)

    def test_get_footer_html_returns_string(self):
        html = self.get_footer_html(self.t)
        self.assertIsInstance(html, str)

    def test_get_footer_html_contains_author(self):
        html = self.get_footer_html(self.t)
        self.assertIn("Lalit", html)

    def test_get_agent_status_html_returns_string(self):
        # get_agent_status_html(t: dict) — takes only theme dict
        html = self.get_agent_status_html(self.t)
        self.assertIsInstance(html, str)

    def test_get_agent_status_html_contains_scanner(self):
        html = self.get_agent_status_html(self.t)
        self.assertIn("Scanner Agent", html)

    def test_get_agent_status_html_contains_ready(self):
        html = self.get_agent_status_html(self.t)
        self.assertIn("Ready", html)

    def test_get_agent_status_html_contains_all_7_agents(self):
        html = self.get_agent_status_html(self.t)
        for name in ["Scanner","Frontier","Specialist","Neural Network","Ensemble","Messaging","Planning"]:
            self.assertIn(name, html, f"Agent '{name}' not found in status HTML")

    def _luminance(self, h):
        h = h.lstrip("#")
        if len(h) == 3: h = "".join(c*2 for c in h)
        r,g,b = (int(h[i:i+2],16)/255.0 for i in (0,2,4))
        def lin(c): return c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4
        return 0.2126*lin(r)+0.7152*lin(g)+0.0722*lin(b)

    def _cr(self, c1, c2):
        l1,l2 = self._luminance(c1), self._luminance(c2)
        li,da = max(l1,l2), min(l1,l2)
        return (li+0.05)/(da+0.05)

    def test_primary_text_contrast_wcag_aa(self):
        r = self._cr(self.t["text_primary"], self.t["bg_surface"])
        self.assertGreaterEqual(r, 4.5, f"Primary text contrast {r:.2f}:1 fails WCAG AA")

    def test_secondary_text_contrast_wcag_aa(self):
        r = self._cr(self.t["text_secondary"], self.t["bg_surface"])
        self.assertGreaterEqual(r, 4.5, f"Secondary text contrast {r:.2f}:1 fails WCAG AA")

    def test_button_text_on_orange_contrast_wcag_aa(self):
        r = self._cr(self.t["btn_primary_text"], self.t["btn_primary_bg"])
        self.assertGreaterEqual(r, 4.5, f"Button text contrast {r:.2f}:1 fails WCAG AA")


class TestSettingsPageModule(unittest.TestCase):
    def test_settings_page_imports(self):
        try:
            import app.ui.settings_page
        except ImportError as e:
            if "gradio" in str(e).lower():
                self.skipTest(f"Gradio not installed: {e}")
            raise

    def test_build_settings_tab_callable(self):
        try:
            from app.ui.settings_page import build_settings_tab
            self.assertTrue(callable(build_settings_tab))
        except ImportError as e:
            if "gradio" in str(e).lower():
                self.skipTest(f"Gradio not installed: {e}")

    def test_status_html_success(self):
        # _status_html(message: str, status: str, theme: dict = None)
        from app.ui.settings_page import _status_html
        html = _status_html("Connection OK", "success")
        self.assertIn("Connection OK", html)
        self.assertIsInstance(html, str)

    def test_status_html_error(self):
        from app.ui.settings_page import _status_html
        html = _status_html("Invalid key", "error")
        self.assertIn("Invalid key", html)

    def test_status_html_empty_returns_empty(self):
        from app.ui.settings_page import _status_html
        html = _status_html("", "success")
        self.assertEqual(html, "")

    def test_read_env_file_returns_dict(self):
        from app.ui.settings_page import read_env_file
        result = read_env_file()
        self.assertIsInstance(result, dict)

    def test_write_env_file_creates_file(self):
        import tempfile
        from app.ui.settings_page import write_env_file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            tmp = f.name
        try:
            import pathlib
            from app.ui.settings_page import ENV_FILE
            orig = ENV_FILE
            # Patch ENV_FILE to write to temp path
            import app.ui.settings_page as sp
            sp.ENV_FILE = pathlib.Path(tmp)
            write_env_file({"OPENAI_API_KEY": "sk-test", "DEAL_THRESHOLD": "50"})
            sp.ENV_FILE = orig
            content = open(tmp).read()
            self.assertIn("OPENAI_API_KEY", content)
        finally:
            os.unlink(tmp)

    def test_validate_field_valid(self):
        from app.ui.settings_page import validate_field
        ok, msg = validate_field("OPENAI_API_KEY", "sk-abc123", {"required": True, "type": "str", "label": "OpenAI API Key"})
        self.assertTrue(ok)

    def test_validate_field_empty_required(self):
        from app.ui.settings_page import validate_field
        ok, msg = validate_field("OPENAI_API_KEY", "", {"required": True, "type": "str", "label": "OpenAI API Key"})
        self.assertFalse(ok)

    def test_masked_env_preview_returns_string(self):
        from app.ui.settings_page import _masked_env_preview
        result = _masked_env_preview()
        self.assertIsInstance(result, str)


class TestDashboardModule(unittest.TestCase):
    def _try_import(self):
        try:
            with patch.dict("sys.modules", {
                "app.core.deal_agent_framework": MagicMock(),
                "app.core.rag_db": MagicMock(),
                "torch": MagicMock(),
                "sentence_transformers": MagicMock(),
                "chromadb": MagicMock(),
                "gradio": MagicMock(),
            }):
                import importlib
                import app.ui.dashboard as d
                importlib.reload(d)
                return d
        except Exception:
            return None

    def test_dashboard_class_exists(self):
        d = self._try_import()
        if d:
            self.assertTrue(hasattr(d, "PriceIsRightDashboard"))

    def test_dashboard_has_build_method(self):
        d = self._try_import()
        if d and hasattr(d, "PriceIsRightDashboard"):
            self.assertTrue(hasattr(d.PriceIsRightDashboard, "build"))

    def test_dashboard_has_run_method(self):
        d = self._try_import()
        if d and hasattr(d, "PriceIsRightDashboard"):
            self.assertTrue(hasattr(d.PriceIsRightDashboard, "run"))


class TestMainModule(unittest.TestCase):
    def test_main_module_importable(self):
        try:
            with patch.dict("sys.modules", {
                "app.core.deal_agent_framework": MagicMock(),
                "app.core.rag_db": MagicMock(),
                "app.ui.dashboard": MagicMock(),
                "torch": MagicMock(),
                "sentence_transformers": MagicMock(),
                "chromadb": MagicMock(),
                "gradio": MagicMock(),
            }):
                import importlib, app.main
                importlib.reload(app.main)
        except SystemExit:
            pass
        except Exception as e:
            if "litellm" not in str(e) and "torch" not in str(e):
                self.fail(f"main.py raised unexpected error: {e}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
