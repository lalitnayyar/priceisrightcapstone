"""
Price Is Right — Gradio Dashboard (Unified Theme Edition)
==========================================================
Features:
  - Dark / Light theme toggle (top-right of header)
  - Uniform colour scheme across all components via app.ui.theme
  - Tabbed interface: Dashboard | Settings
  - Dashboard: collapsible accordions for agents, deals, logs, RAG plot
  - Settings: live .env management with validation and connection tests
  - Live agent log stream with ANSI-to-HTML colour rendering
  - Opportunities table with click-to-notify functionality
  - 3D RAG vector store visualisation (t-SNE reduced embeddings)
  - Manual scan trigger and auto-scan every 5 minutes
"""
import logging
import queue
import threading
import time
from typing import List

import gradio as gr
import plotly.graph_objects as go
from dotenv import load_dotenv

from app.core.deal_agent_framework import DealAgentFramework
from app.utils.log_utils import reformat, html_for
from app.ui.settings_page import build_settings_tab
from app.ui.theme import (
    DARK_THEME, LIGHT_THEME, BRAND,
    get_css, get_header_html, get_footer_html, get_agent_status_html,
)

load_dotenv(override=True)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Logging queue handler — streams log records into the Gradio UI
# ---------------------------------------------------------------------------

class QueueHandler(logging.Handler):
    def __init__(self, log_queue: queue.Queue) -> None:
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record: logging.LogRecord) -> None:
        self.log_queue.put(self.format(record))


def setup_logging(log_queue: queue.Queue) -> None:
    handler = QueueHandler(log_queue)
    formatter = logging.Formatter(
        "[%(asctime)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S %z",
    )
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)


# ---------------------------------------------------------------------------
# Dashboard application class
# ---------------------------------------------------------------------------

class PriceIsRightDashboard:
    """
    Gradio-based dashboard with a unified dark/light design system.

    Tabs:
      1. Dashboard — folding accordion views for agents, deals, logs, RAG plot
      2. Settings  — live .env management with validation and connection tests
    """

    SCAN_INTERVAL_SECONDS = 300  # Auto-scan every 5 minutes

    def __init__(self) -> None:
        self._framework: DealAgentFramework = None

    def get_framework(self) -> DealAgentFramework:
        if self._framework is None:
            self._framework = DealAgentFramework()
        return self._framework

    # ------------------------------------------------------------------
    # Data helpers
    # ------------------------------------------------------------------

    def table_for(self, opportunities) -> List[List]:
        """Convert opportunities to a list of rows for the Gradio Dataframe."""
        return [
            [
                opp.deal.product_description[:120] + "…"
                if len(opp.deal.product_description) > 120
                else opp.deal.product_description,
                f"${opp.deal.price:.2f}",
                f"${opp.estimate:.2f}",
                f"${opp.discount:.2f}",
                "GREAT DEAL ✓" if opp.discount > 50 else "Good Deal",
                opp.deal.url,
            ]
            for opp in opportunities
        ]

    # ------------------------------------------------------------------
    # Plot helpers
    # ------------------------------------------------------------------

    def _plot_layout(self, t: dict) -> dict:
        return dict(
            paper_bgcolor=t["bg_surface"],
            plot_bgcolor=t["bg_surface2"],
            font=dict(color=t["text_primary"], family=BRAND["font_sans"]),
        )

    def get_empty_plot(self, t: dict = DARK_THEME) -> go.Figure:
        fig = go.Figure()
        fig.update_layout(
            title=dict(text="RAG Vector Store — Loading…", font=dict(color=BRAND["primary"])),
            height=420,
            **self._plot_layout(t),
        )
        return fig

    def get_rag_plot(self, t: dict = DARK_THEME) -> go.Figure:
        """Generate the 3D t-SNE scatter plot of the RAG vector store."""
        try:
            documents, vectors, colors = DealAgentFramework.get_plot_data(max_datapoints=800)
            if len(vectors) == 0:
                return self.get_empty_plot(t)

            fig = go.Figure(
                data=[
                    go.Scatter3d(
                        x=vectors[:, 0],
                        y=vectors[:, 1],
                        z=vectors[:, 2],
                        mode="markers",
                        marker=dict(size=2.5, color=colors, opacity=0.75,
                                    line=dict(width=0)),
                        text=documents,
                        hovertemplate="<b>%{text}</b><extra></extra>",
                    )
                ]
            )
            fig.update_layout(
                title=dict(
                    text="RAG Vector Store — Product Embeddings (t-SNE 3D)",
                    font=dict(color=BRAND["primary"], size=15),
                ),
                scene=dict(
                    xaxis_title="x", yaxis_title="y", zaxis_title="z",
                    aspectmode="manual",
                    aspectratio=dict(x=2.2, y=2.2, z=1),
                    camera=dict(eye=dict(x=1.6, y=1.6, z=0.8)),
                    bgcolor=t["bg_surface2"],
                    xaxis=dict(gridcolor=t["border"], color=t["text_secondary"]),
                    yaxis=dict(gridcolor=t["border"], color=t["text_secondary"]),
                    zaxis=dict(gridcolor=t["border"], color=t["text_secondary"]),
                ),
                height=440,
                margin=dict(r=5, b=1, l=5, t=50),
                **self._plot_layout(t),
            )
            return fig
        except Exception as exc:
            logger.warning(f"Could not generate RAG plot: {exc}")
            return self.get_empty_plot(t)

    # ------------------------------------------------------------------
    # Run workflow with live log streaming
    # ------------------------------------------------------------------

    def run_with_logging(self, initial_log_data):
        """Run the framework in a background thread and stream logs to the UI."""
        log_queue: queue.Queue = queue.Queue()
        result_queue: queue.Queue = queue.Queue()
        setup_logging(log_queue)

        def worker():
            try:
                result = self.get_framework().run()
                result_queue.put(self.table_for(result))
            except Exception as exc:
                logging.error(f"Framework run error: {exc}")
                result_queue.put([])

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

        initial_result = self.table_for(self.get_framework().memory)
        final_result = None

        while True:
            try:
                message = log_queue.get_nowait()
                initial_log_data.append(reformat(message))
                yield initial_log_data, html_for(initial_log_data), final_result or initial_result
            except queue.Empty:
                try:
                    final_result = result_queue.get_nowait()
                    yield initial_log_data, html_for(initial_log_data), final_result
                except queue.Empty:
                    if final_result is not None:
                        break
                    time.sleep(0.1)

    def on_row_select(self, selected_index: gr.SelectData) -> None:
        """Re-send a push notification when a row is clicked in the table."""
        try:
            opportunities = self.get_framework().memory
            row = selected_index.index[0]
            if row < len(opportunities):
                opportunity = opportunities[row]
                self.get_framework().planner.messenger.alert(opportunity)
        except Exception as exc:
            logger.warning(f"Row select notification failed: {exc}")

    # ------------------------------------------------------------------
    # Theme toggle logic
    # ------------------------------------------------------------------

    def _toggle_theme(self, current_theme_id: str):
        """Switch between dark and light themes; returns new CSS, header, footer, agent HTML, theme_id."""
        t = LIGHT_THEME if current_theme_id == "dark" else DARK_THEME
        return (
            get_css(t),
            get_header_html(t),
            get_footer_html(t),
            get_agent_status_html(t),
            t["toggle_label"],
            t["id"],
        )

    # ------------------------------------------------------------------
    # Build and launch the Gradio UI
    # ------------------------------------------------------------------

    def build(self) -> gr.Blocks:
        """Construct the Gradio Blocks UI with unified theme and tabbed interface."""

        # Start with dark theme
        t = DARK_THEME

        with gr.Blocks(
            title="The Price Is Right",
            theme=gr.themes.Base(
                primary_hue=gr.themes.colors.orange,
                neutral_hue=gr.themes.colors.slate,
                font=gr.themes.GoogleFont("Inter"),
            ),
            css=get_css(t),
        ) as ui:

            # ---- State ----
            log_data   = gr.State([])
            theme_id   = gr.State(t["id"])

            # ---- Dynamic CSS (updated on theme toggle) ----
            dynamic_css = gr.HTML(value=f"<style>{get_css(t)}</style>", visible=False)

            # ---- Global Header with theme toggle ----
            with gr.Row(elem_id="pir-header-row", equal_height=False):
                header_html = gr.HTML(value=get_header_html(t), scale=10)
                with gr.Column(scale=0, min_width=95):
                    theme_btn = gr.Button(
                        value=t["toggle_label"],
                        elem_id="theme-toggle-btn",
                        variant="secondary",
                        size="sm",
                    )

            # ================================================================
            # TABBED INTERFACE
            # ================================================================
            with gr.Tabs(elem_id="main-tabs"):

                # ============================================================
                # TAB 1: DASHBOARD
                # ============================================================
                with gr.Tab("📊 Dashboard"):

                    # ---- SECTION 1: Agent Framework Status ----
                    with gr.Accordion("⚙️ Agent Framework — 7 Collaborating Agents", open=True):
                        agent_status = gr.HTML(value=get_agent_status_html(t))

                    # ---- SECTION 2: Deal Opportunities ----
                    with gr.Accordion("💰 Deal Opportunities Found", open=True):
                        gr.HTML(
                            f'<p style="color:{t["text_secondary"]};font-size:13px;margin:0 0 8px 0">'
                            f'Click any row to re-send a push notification for that deal.</p>'
                        )
                        opportunities_df = gr.Dataframe(
                            headers=["Product Description", "Deal Price", "Estimate",
                                     "Discount", "Rating", "URL"],
                            wrap=True,
                            column_widths=[5, 1, 1, 1, 1, 3],
                            row_count=10,
                            col_count=6,
                            max_height=350,
                            interactive=False,
                        )

                    # ---- SECTION 3: Live Agent Logs ----
                    with gr.Accordion("📋 Live Agent Logs", open=True):
                        with gr.Row():
                            scan_btn = gr.Button(
                                "🔍 Scan for Deals Now",
                                variant="primary",
                                scale=1,
                            )
                            gr.HTML(
                                f'<p style="color:{t["text_secondary"]};font-size:13px;'
                                f'padding:10px 0;margin:0">'
                                f'Auto-scan runs every 5 minutes. Click the button for an immediate scan.</p>',
                                scale=3,
                            )
                        logs_html = gr.HTML(value=html_for([]))

                    # ---- SECTION 4: RAG Vector Store Visualisation ----
                    with gr.Accordion("🧠 RAG Vector Store — Product Embeddings", open=False):
                        gr.HTML(
                            f'<p style="color:{t["text_secondary"]};font-size:13px;margin:0 0 10px 0">'
                            f'3D t-SNE visualisation of the ChromaDB product embedding space. '
                            f'Each point represents a product; colours indicate category.</p>'
                        )
                        rag_plot = gr.Plot(value=self.get_rag_plot(t), show_label=False)
                        refresh_plot_btn = gr.Button(
                            "🔄 Refresh RAG Plot",
                            variant="secondary",
                        )

                    # ---- SECTION 5: System Configuration Reference ----
                    with gr.Accordion("ℹ️ System Configuration Reference", open=False):
                        gr.Markdown("""
### Agent Model Reference

| Agent | Model | Role |
|-------|-------|------|
| Scanner Agent | GPT-5 (gpt-4o-mini) | RSS deal identification via Structured Outputs |
| Frontier Agent | GPT-5.1 + ChromaDB RAG | Price estimation with similar-product context |
| Specialist Agent | Fine-tuned Llama-3.2-3B (Modal) | Frontier-busting specialist price estimation |
| Neural Network Agent | Deep Residual DNN (local) | Fast offline price regression |
| Ensemble Agent | Weighted average (80/10/10) | Combines Frontier + Specialist + DNN |
| Messaging Agent | Claude Sonnet + Pushover | Crafts and delivers push notifications |
| Planning Agent | GPT-5.1 (orchestrator) | Coordinates all agents, applies deal threshold |

> **Tip:** Go to the **⚙️ Settings** tab to configure API keys, thresholds, and all other options on the fly.
                        """)

                    # ---- Dashboard event wiring ----
                    scan_btn.click(
                        fn=self.run_with_logging,
                        inputs=[log_data],
                        outputs=[log_data, logs_html, opportunities_df],
                    )
                    ui.load(
                        fn=self.run_with_logging,
                        inputs=[log_data],
                        outputs=[log_data, logs_html, opportunities_df],
                    )
                    timer = gr.Timer(value=self.SCAN_INTERVAL_SECONDS, active=True)
                    timer.tick(
                        fn=self.run_with_logging,
                        inputs=[log_data],
                        outputs=[log_data, logs_html, opportunities_df],
                    )
                    opportunities_df.select(fn=self.on_row_select)
                    refresh_plot_btn.click(
                        fn=lambda tid: self.get_rag_plot(
                            LIGHT_THEME if tid == "light" else DARK_THEME
                        ),
                        inputs=[theme_id],
                        outputs=[rag_plot],
                    )

                # ============================================================
                # TAB 2: SETTINGS
                # ============================================================
                with gr.Tab("⚙️ Settings"):
                    build_settings_tab()

            # ---- Footer ----
            footer_html = gr.HTML(value=get_footer_html(t))

            # ================================================================
            # THEME TOGGLE — wires the button to update all themed components
            # ================================================================
            theme_btn.click(
                fn=self._toggle_theme,
                inputs=[theme_id],
                outputs=[
                    dynamic_css,   # updated <style> block (hidden HTML)
                    header_html,   # header with new bg colours
                    footer_html,   # footer with new border colour
                    agent_status,  # agent table with new row colours
                    theme_btn,     # button label (☀️ / 🌙)
                    theme_id,      # state tracker
                ],
            )

        return ui

    def run(self, server_port: int = 7860, share: bool = False) -> None:
        """Launch the Gradio dashboard."""
        ui = self.build()
        ui.launch(
            server_name="0.0.0.0",
            server_port=server_port,
            share=share,
            inbrowser=False,
        )


if __name__ == "__main__":
    PriceIsRightDashboard().run()
