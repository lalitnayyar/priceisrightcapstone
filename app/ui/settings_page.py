"""
Price Is Right — Settings Page (Unified Theme Edition)
=======================================================
Live environment variable management for the Price Is Right dashboard.

Provides a full settings UI with:
  - API Keys section (OpenAI, Anthropic, Pushover, Modal)
  - Agent Configuration (deal threshold, scan interval, model selection)
  - RAG Database settings (ChromaDB path, embedding model, result count)
  - Notification settings (Pushover sound, notification format)
  - Advanced settings (memory file, log level, preprocessor model)
  - Live validation with masked secret display
  - Save to .env file and apply to running process on the fly
  - Export / Import settings as JSON
  - Connection test buttons for each API
"""
import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, Tuple, Any

import gradio as gr
import requests

from app.ui.theme import BRAND, DARK_THEME

logger = logging.getLogger(__name__)

ENV_FILE = Path(".env")

# ---------------------------------------------------------------------------
# All configurable settings, grouped by section
# ---------------------------------------------------------------------------
SETTINGS_SCHEMA = {
    "API Keys": {
        "icon": "🔑",
        "description": "API credentials for external services. These are stored securely in your .env file.",
        "fields": {
            "OPENAI_API_KEY": {
                "label": "OpenAI API Key",
                "type": "password",
                "placeholder": "sk-...",
                "description": "Required for Scanner Agent (GPT-5) and Frontier Agent (GPT-5.1).",
                "required": True,
                "validate": lambda v: v.startswith("sk-") if v else False,
                "validate_msg": "Must start with 'sk-'",
            },
            "ANTHROPIC_API_KEY": {
                "label": "Anthropic API Key",
                "type": "password",
                "placeholder": "sk-ant-...",
                "description": "Required for Messaging Agent (Claude Sonnet message crafting).",
                "required": True,
                "validate": lambda v: v.startswith("sk-ant-") if v else False,
                "validate_msg": "Must start with 'sk-ant-'",
            },
            "PUSHOVER_USER": {
                "label": "Pushover User Key",
                "type": "password",
                "placeholder": "Your Pushover user key",
                "description": "Your personal Pushover user key. Get it at pushover.net.",
                "required": True,
                "validate": lambda v: len(v) == 30 if v else False,
                "validate_msg": "Pushover user keys are 30 characters",
            },
            "PUSHOVER_TOKEN": {
                "label": "Pushover App Token",
                "type": "password",
                "placeholder": "Your Pushover app token",
                "description": "The app token for the Price Is Right Pushover application.",
                "required": True,
                "validate": lambda v: len(v) == 30 if v else False,
                "validate_msg": "Pushover app tokens are 30 characters",
            },
            "MODAL_TOKEN_ID": {
                "label": "Modal Token ID",
                "type": "password",
                "placeholder": "ak-...",
                "description": "Optional. Required only for the fine-tuned Specialist Agent on Modal GPU.",
                "required": False,
                "validate": None,
                "validate_msg": "",
            },
            "MODAL_TOKEN_SECRET": {
                "label": "Modal Token Secret",
                "type": "password",
                "placeholder": "as-...",
                "description": "Optional. Required only for the fine-tuned Specialist Agent on Modal GPU.",
                "required": False,
                "validate": None,
                "validate_msg": "",
            },
        },
    },
    "Agent Configuration": {
        "icon": "🤖",
        "description": "Configure the behaviour of the 7-agent deal-hunting framework.",
        "fields": {
            "DEAL_THRESHOLD": {
                "label": "Deal Threshold ($)",
                "type": "number",
                "placeholder": "50",
                "description": "Minimum discount in USD required to trigger a push notification. Default: 50.",
                "required": False,
                "validate": lambda v: v.isdigit() and int(v) > 0 if v else True,
                "validate_msg": "Must be a positive integer",
                "default": "50",
            },
            "SCAN_INTERVAL_SECONDS": {
                "label": "Scan Interval (seconds)",
                "type": "number",
                "placeholder": "300",
                "description": "How often the dashboard auto-scans for new deals. Default: 300 (5 minutes).",
                "required": False,
                "validate": lambda v: v.isdigit() and int(v) >= 60 if v else True,
                "validate_msg": "Must be at least 60 seconds",
                "default": "300",
            },
            "SCANNER_MODEL": {
                "label": "Scanner Agent Model",
                "type": "text",
                "placeholder": "gpt-4o-mini",
                "description": "OpenAI model for the Scanner Agent. Default: gpt-4o-mini.",
                "required": False,
                "validate": None,
                "validate_msg": "",
                "default": "gpt-4o-mini",
            },
            "FRONTIER_MODEL": {
                "label": "Frontier Agent Model",
                "type": "text",
                "placeholder": "gpt-4o",
                "description": "OpenAI model for the Frontier Agent price estimation. Default: gpt-4o.",
                "required": False,
                "validate": None,
                "validate_msg": "",
                "default": "gpt-4o",
            },
            "MESSAGING_MODEL": {
                "label": "Messaging Agent Model",
                "type": "text",
                "placeholder": "claude-sonnet-4-5",
                "description": "Anthropic model for crafting push notification messages.",
                "required": False,
                "validate": None,
                "validate_msg": "",
                "default": "claude-sonnet-4-5",
            },
            "ENSEMBLE_FRONTIER_WEIGHT": {
                "label": "Ensemble Frontier Weight",
                "type": "number",
                "placeholder": "0.8",
                "description": "Weight for Frontier Agent in ensemble (0.0–1.0). Default: 0.8.",
                "required": False,
                "validate": None,
                "validate_msg": "",
                "default": "0.8",
            },
            "ENSEMBLE_SPECIALIST_WEIGHT": {
                "label": "Ensemble Specialist Weight",
                "type": "number",
                "placeholder": "0.1",
                "description": "Weight for Specialist Agent in ensemble (0.0–1.0). Default: 0.1.",
                "required": False,
                "validate": None,
                "validate_msg": "",
                "default": "0.1",
            },
        },
    },
    "RAG Database": {
        "icon": "🧠",
        "description": "Configure the ChromaDB vector store used by the Frontier Agent for product similarity search.",
        "fields": {
            "CHROMA_DB_PATH": {
                "label": "ChromaDB Path",
                "type": "text",
                "placeholder": "products_vectorstore",
                "description": "Path to the ChromaDB persistent storage directory.",
                "required": False,
                "validate": None,
                "validate_msg": "",
                "default": "products_vectorstore",
            },
            "RAG_RESULTS_COUNT": {
                "label": "RAG Results Count",
                "type": "number",
                "placeholder": "5",
                "description": "Number of similar products to retrieve from ChromaDB per query. Default: 5.",
                "required": False,
                "validate": lambda v: v.isdigit() and 1 <= int(v) <= 20 if v else True,
                "validate_msg": "Must be between 1 and 20",
                "default": "5",
            },
            "EMBEDDING_MODEL": {
                "label": "Embedding Model",
                "type": "text",
                "placeholder": "sentence-transformers/all-MiniLM-L6-v2",
                "description": "Sentence Transformers model used to embed product descriptions.",
                "required": False,
                "validate": None,
                "validate_msg": "",
                "default": "sentence-transformers/all-MiniLM-L6-v2",
            },
            "RAG_MAX_DATAPOINTS": {
                "label": "RAG Visualisation Max Points",
                "type": "number",
                "placeholder": "800",
                "description": "Maximum number of products to include in the 3D RAG visualisation. Default: 800.",
                "required": False,
                "validate": lambda v: v.isdigit() and int(v) > 0 if v else True,
                "validate_msg": "Must be a positive integer",
                "default": "800",
            },
        },
    },
    "Notifications": {
        "icon": "🔔",
        "description": "Configure push notification delivery and message formatting.",
        "fields": {
            "PUSHOVER_SOUND": {
                "label": "Pushover Notification Sound",
                "type": "text",
                "placeholder": "cashregister",
                "description": "Pushover sound name. Options: cashregister, magic, alien, bike, bugle, classical, etc.",
                "required": False,
                "validate": None,
                "validate_msg": "",
                "default": "cashregister",
            },
            "NOTIFICATION_TITLE": {
                "label": "Notification Title",
                "type": "text",
                "placeholder": "Price Is Right — Deal Alert!",
                "description": "Title shown in the push notification header.",
                "required": False,
                "validate": None,
                "validate_msg": "",
                "default": "Price Is Right — Deal Alert!",
            },
            "MIN_NOTIFICATION_INTERVAL": {
                "label": "Min Notification Interval (seconds)",
                "type": "number",
                "placeholder": "3600",
                "description": "Minimum time between push notifications to avoid spam. Default: 3600 (1 hour).",
                "required": False,
                "validate": lambda v: v.isdigit() and int(v) >= 0 if v else True,
                "validate_msg": "Must be a non-negative integer",
                "default": "3600",
            },
        },
    },
    "RSS Feeds": {
        "icon": "📡",
        "description": "Configure the RSS feed sources monitored by the Scanner Agent.",
        "fields": {
            "RSS_FEED_URLS": {
                "label": "RSS Feed URLs",
                "type": "textarea",
                "placeholder": "https://www.dealnews.com/c142/Electronics/?rss=1\nhttps://www.dealnews.com/c39/Computers/?rss=1",
                "description": "One RSS feed URL per line. The Scanner Agent monitors all of these feeds.",
                "required": False,
                "validate": None,
                "validate_msg": "",
                "default": "https://www.dealnews.com/c142/Electronics/?rss=1\nhttps://www.dealnews.com/c39/Computers/?rss=1",
            },
            "MAX_DEALS_PER_SCAN": {
                "label": "Max Deals Per Scan",
                "type": "number",
                "placeholder": "5",
                "description": "Maximum number of deals to evaluate per scan cycle. Default: 5.",
                "required": False,
                "validate": lambda v: v.isdigit() and 1 <= int(v) <= 20 if v else True,
                "validate_msg": "Must be between 1 and 20",
                "default": "5",
            },
        },
    },
    "Advanced": {
        "icon": "⚙️",
        "description": "Advanced settings for logging, storage, and preprocessing.",
        "fields": {
            "MEMORY_FILE": {
                "label": "Memory File Path",
                "type": "text",
                "placeholder": "data/memory.json",
                "description": "Path to the JSON file storing previously surfaced opportunities.",
                "required": False,
                "validate": None,
                "validate_msg": "",
                "default": "data/memory.json",
            },
            "LOG_LEVEL": {
                "label": "Log Level",
                "type": "text",
                "placeholder": "INFO",
                "description": "Python logging level: DEBUG, INFO, WARNING, ERROR. Default: INFO.",
                "required": False,
                "validate": lambda v: v.upper() in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL") if v else True,
                "validate_msg": "Must be DEBUG, INFO, WARNING, ERROR, or CRITICAL",
                "default": "INFO",
            },
            "PRICER_PREPROCESSOR_MODEL": {
                "label": "Preprocessor Model",
                "type": "text",
                "placeholder": "gpt-4o-mini",
                "description": "Model used by the Preprocessor to clean and structure product descriptions.",
                "required": False,
                "validate": None,
                "validate_msg": "",
                "default": "gpt-4o-mini",
            },
            "DNN_WEIGHTS_PATH": {
                "label": "DNN Weights Path",
                "type": "text",
                "placeholder": "data/deep_neural_network.pth",
                "description": "Path to the PyTorch weights file for the Neural Network Agent.",
                "required": False,
                "validate": None,
                "validate_msg": "",
                "default": "data/deep_neural_network.pth",
            },
            "DASHBOARD_PORT": {
                "label": "Dashboard Port",
                "type": "number",
                "placeholder": "7860",
                "description": "Port for the Gradio dashboard (requires restart to take effect).",
                "required": False,
                "validate": lambda v: v.isdigit() and 1024 <= int(v) <= 65535 if v else True,
                "validate_msg": "Must be between 1024 and 65535",
                "default": "7860",
            },
            "API_PORT": {
                "label": "API Port",
                "type": "number",
                "placeholder": "8000",
                "description": "Port for the FastAPI server (requires restart to take effect).",
                "required": False,
                "validate": lambda v: v.isdigit() and 1024 <= int(v) <= 65535 if v else True,
                "validate_msg": "Must be between 1024 and 65535",
                "default": "8000",
            },
        },
    },
}


# ---------------------------------------------------------------------------
# .env file read / write helpers
# ---------------------------------------------------------------------------

def read_env_file() -> Dict[str, str]:
    """Read the .env file and return a dict of key → value."""
    env_vars: Dict[str, str] = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                env_vars[key.strip()] = value.strip().strip('"').strip("'")
    return env_vars


def write_env_file(env_vars: Dict[str, str]) -> None:
    """Write a dict of key → value to the .env file, preserving comments."""
    existing_lines = ENV_FILE.read_text().splitlines() if ENV_FILE.exists() else []
    written_keys = set()
    new_lines = []

    for line in existing_lines:
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            new_lines.append(line)
            continue
        if "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in env_vars:
                new_lines.append(f'{key}={env_vars[key]}')
                written_keys.add(key)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    # Append any new keys not already in the file
    for key, value in env_vars.items():
        if key not in written_keys:
            new_lines.append(f"{key}={value}")

    ENV_FILE.write_text("\n".join(new_lines) + "\n")


def apply_to_process(env_vars: Dict[str, str]) -> None:
    """Apply env vars to the current running process immediately."""
    for key, value in env_vars.items():
        if value:
            os.environ[key] = value
            logger.info(f"Settings: applied {key} to running process")


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def validate_field(key: str, value: str, schema_field: dict) -> Tuple[bool, str]:
    """Validate a single field value. Returns (is_valid, message)."""
    if schema_field.get("required") and not value:
        return False, f"{schema_field['label']} is required."
    if value and schema_field.get("validate"):
        try:
            if not schema_field["validate"](value):
                return False, f"{schema_field['label']}: {schema_field['validate_msg']}"
        except Exception:
            pass
    return True, ""


def validate_all(values: Dict[str, str]) -> Tuple[bool, str]:
    """Validate all fields. Returns (all_valid, summary_message)."""
    errors = []
    for section_data in SETTINGS_SCHEMA.values():
        for key, field in section_data["fields"].items():
            value = values.get(key, "")
            ok, msg = validate_field(key, value, field)
            if not ok:
                errors.append(msg)
    if errors:
        return False, "Validation errors:\n" + "\n".join(f"  • {e}" for e in errors)
    return True, "All fields are valid."


# ---------------------------------------------------------------------------
# Connection test helpers
# ---------------------------------------------------------------------------

def test_openai(api_key: str) -> str:
    """Test the OpenAI API key."""
    if not api_key:
        return "⚠️ No API key provided"
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        models = client.models.list()
        count = len(list(models))
        return f"✅ Connected — {count} models available"
    except Exception as exc:
        return f"❌ Failed: {str(exc)[:80]}"


def test_anthropic(api_key: str) -> str:
    """Test the Anthropic API key."""
    if not api_key:
        return "⚠️ No API key provided"
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}],
        )
        return "✅ Connected — Anthropic API is working"
    except Exception as exc:
        return f"❌ Failed: {str(exc)[:80]}"


def test_pushover(user_key: str, token: str) -> str:
    """Test Pushover credentials by calling the validation endpoint."""
    if not user_key or not token:
        return "⚠️ User key and token are both required"
    try:
        resp = requests.post(
            "https://api.pushover.net/1/users/validate.json",
            data={"token": token, "user": user_key},
            timeout=8,
        )
        data = resp.json()
        if data.get("status") == 1:
            devices = ", ".join(data.get("devices", [])) or "none registered"
            return f"✅ Valid — Devices: {devices}"
        else:
            return f"❌ Invalid: {data.get('errors', ['Unknown error'])}"
    except Exception as exc:
        return f"❌ Failed: {str(exc)[:80]}"


def test_chromadb(db_path: str) -> str:
    """Test ChromaDB connectivity and return collection stats."""
    try:
        import chromadb
        path = db_path or "products_vectorstore"
        client = chromadb.PersistentClient(path=path)
        collection = client.get_or_create_collection("products")
        count = collection.count()
        return f"✅ Connected — {count} products in vector store at '{path}'"
    except Exception as exc:
        return f"❌ Failed: {str(exc)[:80]}"


# ---------------------------------------------------------------------------
# Settings page builder
# ---------------------------------------------------------------------------

def build_settings_tab() -> None:
    """
    Build and return the complete Settings tab content.
    Call this inside a gr.Tab() context.
    """
    current_env = read_env_file()

    # ---- Header (uses unified theme colours) ----
    t = DARK_THEME  # default; CSS overrides handle light mode
    gr.HTML(
        f'<div style="background:{t["bg_surface2"]};border-radius:8px;padding:18px 24px;'
        f'margin-bottom:16px;border:1px solid {BRAND["primary"]};'
        f'border-left:4px solid {BRAND["primary"]}">'
        f'<h2 style="color:{BRAND["primary"]};margin:0 0 6px 0;font-size:1.3em;'
        f'font-family:{BRAND["font_sans"]};font-weight:700">⚙️ Settings &amp; Configuration</h2>'
        f'<p style="color:{t["text_secondary"]};margin:0;font-size:0.88em;'
        f'font-family:{BRAND["font_sans"]}">'
        f'Configure all environment variables on the fly. Changes are saved to '
        f'<code style="background:{t["bg_log"]};color:{t["text_code"]};'
        f'padding:1px 5px;border-radius:3px">.env</code> '
        f'and applied to the running process immediately — no restart required for API keys '
        f'and thresholds. Port changes require a container restart.'
        f'</p></div>'
    )

    # ---- Status banner ----
    status_banner = gr.HTML(value=_status_html("", "idle"))

    # ---- Collect all input components keyed by env var name ----
    input_components: Dict[str, gr.components.Component] = {}
    test_result_components: Dict[str, gr.HTML] = {}

    # ---- Render each section as an accordion ----
    for section_name, section_data in SETTINGS_SCHEMA.items():
        icon = section_data["icon"]
        desc = section_data["description"]
        is_api_section = section_name == "API Keys"

        with gr.Accordion(f"{icon} {section_name}", open=(section_name == "API Keys")):
            gr.Markdown(f"_{desc}_")

            for key, field in section_data["fields"].items():
                current_val = current_env.get(key, field.get("default", ""))
                label = field["label"]
                placeholder = field["placeholder"]
                field_desc = field["description"]
                required_badge = " **\\*** " if field.get("required") else ""

                with gr.Row():
                    with gr.Column(scale=3):
                        if field["type"] == "password":
                            comp = gr.Textbox(
                                label=f"{label}{required_badge}",
                                value=current_val,
                                placeholder=placeholder,
                                type="password",
                                info=field_desc,
                                interactive=True,
                            )
                        elif field["type"] == "textarea":
                            comp = gr.Textbox(
                                label=label,
                                value=current_val.replace(",", "\n") if current_val else field.get("default", ""),
                                placeholder=placeholder,
                                lines=4,
                                info=field_desc,
                                interactive=True,
                            )
                        else:
                            comp = gr.Textbox(
                                label=label,
                                value=current_val,
                                placeholder=placeholder,
                                info=field_desc,
                                interactive=True,
                            )
                    input_components[key] = comp

            # ---- Connection test buttons for API Keys section ----
            if is_api_section:
                gr.Markdown("**Connection Tests** — verify your credentials without saving:")
                with gr.Row():
                    test_openai_btn = gr.Button("🔌 Test OpenAI", variant="secondary", size="sm")
                    test_anthropic_btn = gr.Button("🔌 Test Anthropic", variant="secondary", size="sm")
                    test_pushover_btn = gr.Button("🔌 Test Pushover", variant="secondary", size="sm")
                    test_chroma_btn = gr.Button("🔌 Test ChromaDB", variant="secondary", size="sm")

                test_result = gr.HTML(value="")
                test_result_components["api_test"] = test_result

                def _test_openai(k): return _status_html(test_openai(k), "test")
                def _test_anthropic(k): return _status_html(test_anthropic(k), "test")
                def _test_pushover(u, t): return _status_html(test_pushover(u, t), "test")
                def _test_chroma(p): return _status_html(test_chromadb(p), "test")

                test_openai_btn.click(
                    fn=_test_openai,
                    inputs=[input_components["OPENAI_API_KEY"]],
                    outputs=[test_result],
                )
                test_anthropic_btn.click(
                    fn=_test_anthropic,
                    inputs=[input_components["ANTHROPIC_API_KEY"]],
                    outputs=[test_result],
                )
                test_pushover_btn.click(
                    fn=_test_pushover,
                    inputs=[input_components["PUSHOVER_USER"], input_components["PUSHOVER_TOKEN"]],
                    outputs=[test_result],
                )
                test_chroma_btn.click(
                    fn=_test_chroma,
                    inputs=[input_components.get("CHROMA_DB_PATH", gr.State("products_vectorstore"))],
                    outputs=[test_result],
                )

    # ---- Action buttons ----
    gr.HTML(f'<hr style="border-color:{DARK_THEME["border"]};margin:20px 0">')
    with gr.Row():
        save_btn = gr.Button("💾 Save & Apply Settings", variant="primary", scale=2)
        validate_btn = gr.Button("✅ Validate Only", variant="secondary", scale=1)
        reset_btn = gr.Button("🔄 Reset to Defaults", variant="secondary", scale=1)
        export_btn = gr.Button("📤 Export Settings", variant="secondary", scale=1)

    export_file = gr.File(label="Exported Settings", visible=False)
    import_file = gr.File(label="Import Settings JSON", file_types=[".json"])

    # ---- Wire save button ----
    all_inputs = list(input_components.values())
    all_keys = list(input_components.keys())

    def _save_settings(*values):
        new_env = dict(zip(all_keys, values))
        # Normalise textarea newlines to comma-separated for RSS_FEED_URLS
        if "RSS_FEED_URLS" in new_env:
            new_env["RSS_FEED_URLS"] = ",".join(
                line.strip() for line in new_env["RSS_FEED_URLS"].splitlines() if line.strip()
            )
        ok, msg = validate_all(new_env)
        if not ok:
            return _status_html(msg, "error")
        try:
            write_env_file(new_env)
            apply_to_process(new_env)
            return _status_html(
                f"✅ Settings saved to .env and applied to running process. {len(new_env)} variables updated.",
                "success",
            )
        except Exception as exc:
            return _status_html(f"❌ Save failed: {exc}", "error")

    save_btn.click(fn=_save_settings, inputs=all_inputs, outputs=[status_banner])

    def _validate_only(*values):
        new_env = dict(zip(all_keys, values))
        ok, msg = validate_all(new_env)
        return _status_html(("✅ " if ok else "❌ ") + msg, "success" if ok else "error")

    validate_btn.click(fn=_validate_only, inputs=all_inputs, outputs=[status_banner])

    def _reset_defaults():
        defaults = {}
        for section_data in SETTINGS_SCHEMA.values():
            for key, field in section_data["fields"].items():
                defaults[key] = field.get("default", "")
        updates = [gr.update(value=defaults.get(k, "")) for k in all_keys]
        return updates + [_status_html("🔄 Fields reset to defaults. Click 'Save & Apply' to persist.", "idle")]

    reset_btn.click(fn=_reset_defaults, outputs=all_inputs + [status_banner])

    def _export_settings(*values):
        new_env = dict(zip(all_keys, values))
        # Mask secrets in export
        safe = {}
        for k, v in new_env.items():
            if any(word in k for word in ("KEY", "TOKEN", "SECRET")):
                safe[k] = "***REDACTED***"
            else:
                safe[k] = v
        path = "/tmp/price_is_right_settings.json"
        with open(path, "w") as f:
            json.dump(safe, f, indent=2)
        return gr.update(value=path, visible=True), _status_html(
            "📤 Settings exported (secrets redacted). Download the file below.", "idle"
        )

    export_btn.click(fn=_export_settings, inputs=all_inputs, outputs=[export_file, status_banner])

    def _import_settings(file):
        if file is None:
            return [gr.update()] * len(all_keys) + [_status_html("⚠️ No file selected.", "error")]
        try:
            with open(file.name, "r") as f:
                imported = json.load(f)
            updates = [gr.update(value=imported.get(k, "")) for k in all_keys]
            return updates + [_status_html(
                f"📥 Imported {len(imported)} settings. Review and click 'Save & Apply'.", "idle"
            )]
        except Exception as exc:
            return [gr.update()] * len(all_keys) + [_status_html(f"❌ Import failed: {exc}", "error")]

    import_file.change(fn=_import_settings, inputs=[import_file], outputs=all_inputs + [status_banner])

    # ---- Current .env preview ----
    with gr.Accordion("📄 Current .env Preview (secrets masked)", open=False):
        env_preview = gr.Code(
            value=_masked_env_preview(),
            language="shell",
            label=".env file contents",
            interactive=False,
        )
        refresh_preview_btn = gr.Button("🔄 Refresh Preview", variant="secondary", size="sm")
        refresh_preview_btn.click(fn=lambda: _masked_env_preview(), outputs=[env_preview])


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------

def _status_html(message: str, status: str) -> str:
    """Return a themed status banner HTML snippet."""
    t = DARK_THEME
    configs = {
        "success": (t["dot_ready"],  "rgba(46,204,113,0.12)",  t["dot_ready"]),
        "error":   (t["dot_error"],   "rgba(231,76,60,0.12)",   t["dot_error"]),
        "idle":    (t["text_link"],   "rgba(52,152,219,0.10)",  BRAND["info"]),
        "test":    (t["dot_busy"],    "rgba(243,156,18,0.12)",  t["dot_busy"]),
    }
    text_color, bg_color, border_color = configs.get(status, configs["idle"])
    if not message:
        return ""
    return (
        f'<div style="background:{bg_color};border-left:4px solid {border_color};'
        f'border:1px solid {border_color};border-radius:0 6px 6px 0;'
        f'padding:10px 14px;margin:8px 0;'
        f'font-family:{BRAND["font_mono"]};font-size:13px;color:{text_color}">'
        f'{message.replace(chr(10), "<br>")}'
        f'</div>'
    )


def _masked_env_preview() -> str:
    """Return the .env file contents with secrets masked."""
    if not ENV_FILE.exists():
        return "# .env file not found"
    lines = []
    for line in ENV_FILE.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or not stripped or "=" not in stripped:
            lines.append(line)
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        if any(word in key for word in ("KEY", "TOKEN", "SECRET", "PASSWORD", "PASS")):
            masked = value[:4] + "****" + value[-2:] if len(value) > 6 else "****"
            lines.append(f"{key}={masked}")
        else:
            lines.append(line)
    return "\n".join(lines)
