"""
Price Is Right — Gradio Dashboard with Folding View.

Features:
  - Collapsible (folding) accordion sections for each view
  - Live agent log stream with ANSI-to-HTML color rendering
  - Opportunities table with click-to-notify functionality
  - 3D RAG vector store visualisation (t-SNE reduced embeddings)
  - Manual scan trigger and auto-scan every 5 minutes
  - Agent status panel showing all 7 agents and their states
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

load_dotenv(override=True)


# ---------------------------------------------------------------------------
# Logging queue handler for streaming logs to the UI
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
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


# ---------------------------------------------------------------------------
# Dashboard application class
# ---------------------------------------------------------------------------

class PriceIsRightDashboard:
    """
    Gradio-based dashboard with folding accordion sections for the
    Price Is Right multi-agent deal hunting framework.
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
                opp.deal.product_description[:120] + "..." if len(opp.deal.product_description) > 120 else opp.deal.product_description,
                f"${opp.deal.price:.2f}",
                f"${opp.estimate:.2f}",
                f"${opp.discount:.2f}",
                "GREAT DEAL ✓" if opp.discount > 50 else "Good Deal",
                opp.deal.url,
            ]
            for opp in opportunities
        ]

    def get_agent_status_html(self) -> str:
        """Generate an HTML status panel showing all 7 agents."""
        agents = [
            ("1", "Scanner Agent", "GPT-5 RSS Monitor", Agent.CYAN, "#00dddd"),
            ("2", "Frontier Agent", "RAG + GPT-5.1 Pricer", Agent.BLUE, "#0000ee"),
            ("3", "Specialist Agent", "Fine-tuned LLM (Modal)", Agent.RED, "#dd0000"),
            ("4", "Neural Network Agent", "Deep Residual DNN", Agent.MAGENTA, "#aa00dd"),
            ("5", "Ensemble Agent", "Weighted Price Combiner", Agent.YELLOW, "#dddd00"),
            ("6", "Messaging Agent", "Pushover + Claude Notifier", Agent.WHITE, "#87CEEB"),
            ("7", "Planning Agent", "Workflow Orchestrator", Agent.GREEN, "#00dd00"),
        ]
        rows = ""
        for num, name, role, _, color in agents:
            rows += (
                f'<tr>'
                f'<td style="padding:6px;text-align:center;font-weight:bold;color:{color}">#{num}</td>'
                f'<td style="padding:6px;color:{color};font-weight:bold">{name}</td>'
                f'<td style="padding:6px;color:#aaa">{role}</td>'
                f'<td style="padding:6px;text-align:center"><span style="color:#00dd00">●</span> Ready</td>'
                f'</tr>'
            )
        return (
            '<div style="background:#1a1a2e;border-radius:8px;padding:12px;margin:4px 0">'
            '<h3 style="color:#ff7800;margin:0 0 10px 0;text-align:center">7-Agent Collaboration Framework</h3>'
            '<table style="width:100%;border-collapse:collapse;font-family:monospace;font-size:13px">'
            '<thead><tr>'
            '<th style="padding:6px;color:#888;text-align:center">#</th>'
            '<th style="padding:6px;color:#888">Agent</th>'
            '<th style="padding:6px;color:#888">Role</th>'
            '<th style="padding:6px;color:#888;text-align:center">Status</th>'
            '</tr></thead>'
            f'<tbody>{rows}</tbody>'
            '</table>'
            '</div>'
        )

    # ------------------------------------------------------------------
    # Plot helpers
    # ------------------------------------------------------------------

    def get_empty_plot(self) -> go.Figure:
        fig = go.Figure()
        fig.update_layout(
            title="RAG Vector Store — Loading...",
            height=420,
            paper_bgcolor="#1a1a2e",
            plot_bgcolor="#1a1a2e",
            font=dict(color="#aaa"),
        )
        return fig

    def get_rag_plot(self) -> go.Figure:
        """Generate the 3D t-SNE scatter plot of the RAG vector store."""
        try:
            documents, vectors, colors = DealAgentFramework.get_plot_data(max_datapoints=800)
            if len(vectors) == 0:
                return self.get_empty_plot()

            fig = go.Figure(
                data=[
                    go.Scatter3d(
                        x=vectors[:, 0],
                        y=vectors[:, 1],
                        z=vectors[:, 2],
                        mode="markers",
                        marker=dict(size=2, color=colors, opacity=0.7),
                        text=documents,
                        hovertemplate="<b>%{text}</b><extra></extra>",
                    )
                ]
            )
            fig.update_layout(
                title="RAG Vector Store — Product Embeddings (t-SNE 3D)",
                scene=dict(
                    xaxis_title="x",
                    yaxis_title="y",
                    zaxis_title="z",
                    aspectmode="manual",
                    aspectratio=dict(x=2.2, y=2.2, z=1),
                    camera=dict(eye=dict(x=1.6, y=1.6, z=0.8)),
                    bgcolor="#1a1a2e",
                ),
                height=420,
                margin=dict(r=5, b=1, l=5, t=40),
                paper_bgcolor="#1a1a2e",
                font=dict(color="#aaa"),
            )
            return fig
        except Exception as exc:
            logging.warning(f"Could not generate RAG plot: {exc}")
            return self.get_empty_plot()

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
            logging.warning(f"Row select notification failed: {exc}")

    # ------------------------------------------------------------------
    # Build and launch the Gradio UI
    # ------------------------------------------------------------------

    def build(self) -> gr.Blocks:
        """Construct the Gradio Blocks UI with folding accordion sections."""
        with gr.Blocks(
            title="The Price Is Right",
            theme=gr.themes.Base(
                primary_hue="orange",
                neutral_hue="slate",
            ),
            css="""
            .gradio-container { background-color: #0f0f1a; }
            .gr-button { background: #ff7800 !important; color: white !important; }
            .gr-button:hover { background: #cc6000 !important; }
            h1, h2, h3 { color: #ff7800; }
            """,
        ) as ui:
            log_data = gr.State([])

            # ---- Header ----
            gr.HTML("""
            <div style="text-align:center;padding:20px 0 10px 0;background:linear-gradient(135deg,#0f0f1a,#1a1a2e)">
              <h1 style="color:#ff7800;font-size:2.2em;margin:0">🎯 The Price Is Right</h1>
              <p style="color:#87CEEB;font-size:1em;margin:8px 0 0 0">
                Autonomous 7-Agent AI Framework · RSS Deal Hunter · RAG Price Estimator · Push Notifications
              </p>
            </div>
            """)

            # ---- SECTION 1: Agent Framework Status (folding) ----
            with gr.Accordion("⚙️ Agent Framework — 7 Collaborating Agents", open=True):
                agent_status = gr.HTML(value=self.get_agent_status_html())

            # ---- SECTION 2: Deal Opportunities (folding) ----
            with gr.Accordion("💰 Deal Opportunities Found", open=True):
                gr.Markdown(
                    "_Click any row to re-send a push notification for that deal._",
                )
                opportunities_df = gr.Dataframe(
                    headers=["Product Description", "Deal Price", "Estimate", "Discount", "Rating", "URL"],
                    wrap=True,
                    column_widths=[5, 1, 1, 1, 1, 3],
                    row_count=10,
                    col_count=6,
                    max_height=350,
                    interactive=False,
                )

            # ---- SECTION 3: Live Agent Logs (folding) ----
            with gr.Accordion("📋 Live Agent Logs", open=True):
                with gr.Row():
                    scan_btn = gr.Button("🔍 Scan for Deals Now", variant="primary", scale=1)
                    gr.Markdown(
                        "_Auto-scan runs every 5 minutes. Click the button for an immediate scan._",
                        scale=3,
                    )
                logs_html = gr.HTML(value=html_for([]))

            # ---- SECTION 4: RAG Vector Store Visualisation (folding) ----
            with gr.Accordion("🧠 RAG Vector Store — Product Embeddings", open=False):
                gr.Markdown(
                    "3D t-SNE visualisation of the ChromaDB product embedding space. "
                    "Each point represents a product; colors indicate category."
                )
                rag_plot = gr.Plot(value=self.get_rag_plot(), show_label=False)
                refresh_plot_btn = gr.Button("🔄 Refresh RAG Plot", variant="secondary")

            # ---- SECTION 5: Configuration Info (folding) ----
            with gr.Accordion("ℹ️ System Configuration", open=False):
                gr.Markdown("""
                ### Agent Configuration

                | Agent | Model | Role |
                |-------|-------|------|
                | Scanner Agent | GPT-5 (gpt-5-mini) | RSS deal identification via Structured Outputs |
                | Frontier Agent | GPT-5.1 + ChromaDB RAG | Price estimation with similar-product context |
                | Specialist Agent | Fine-tuned Llama-3.2-3B (Modal) | Frontier-busting specialist price estimation |
                | Neural Network Agent | Deep Residual DNN (local) | Fast offline price regression |
                | Ensemble Agent | Weighted average (80/10/10) | Combines Frontier + Specialist + DNN |
                | Messaging Agent | Claude Sonnet + Pushover | Crafts and delivers push notifications |
                | Planning Agent | GPT-5.1 (orchestrator) | Coordinates all agents, applies deal threshold |

                ### Environment Variables
                Set these in your `.env` file or Docker environment:
                - `OPENAI_API_KEY` — OpenAI API key
                - `ANTHROPIC_API_KEY` — Anthropic API key (for Claude)
                - `PUSHOVER_USER` — Pushover user key
                - `PUSHOVER_TOKEN` — Pushover app token
                - `CHROMA_DB_PATH` — Path to ChromaDB store (default: `products_vectorstore`)
                - `DEAL_THRESHOLD` — Minimum discount to trigger notification (default: 50)
                """)

            # ---- Event wiring ----
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
                fn=lambda: self.get_rag_plot(),
                outputs=[rag_plot],
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


# Needed for the agent status HTML
from app.agents.agent import Agent


if __name__ == "__main__":
    PriceIsRightDashboard().run()
