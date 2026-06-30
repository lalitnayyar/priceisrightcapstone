"""
Price Is Right — Unified Design System & Theme Module
======================================================
Single source of truth for all colours, typography, spacing, and CSS.
Both dark and light themes are defined here. The dashboard and settings
page import from this module so the entire app stays visually consistent.

Usage:
    from app.ui.theme import get_css, DARK_THEME, LIGHT_THEME, BRAND
"""

# ---------------------------------------------------------------------------
# Brand constants (never change between themes)
# ---------------------------------------------------------------------------
BRAND = {
    "name":    "The Price Is Right",
    "primary": "#FF6B35",   # Vivid orange — primary accent
    "primary_hover": "#E55A24",
    "secondary": "#4ECDC4",  # Teal — secondary accent
    "success": "#2ECC71",
    "warning": "#F39C12",
    "danger":  "#E74C3C",
    "info":    "#3498DB",
    "font_mono": "JetBrains Mono, Fira Code, Consolas, monospace",
    "font_sans": "Inter, Segoe UI, system-ui, sans-serif",
}

# ---------------------------------------------------------------------------
# Dark theme palette
# ---------------------------------------------------------------------------
DARK_THEME = {
    "id": "dark",
    # Backgrounds
    "bg_page":       "#0D1117",   # GitHub-dark page background
    "bg_surface":    "#161B22",   # Card / accordion surface
    "bg_surface2":   "#1C2128",   # Nested surface (inputs, code blocks)
    "bg_header":     "#0D1117",   # Top header bar
    "bg_footer":     "#0D1117",
    "bg_table_head": "#1C2128",
    "bg_table_row":  "#161B22",
    "bg_table_alt":  "#1A2030",
    "bg_log":        "#0D1117",
    # Borders
    "border":        "#30363D",
    "border_accent": "#FF6B35",
    # Text
    "text_primary":  "#E6EDF3",   # Main text
    "text_secondary":"#8B949E",   # Muted / descriptions
    "text_accent":   "#FF6B35",   # Orange headings
    "text_link":     "#4ECDC4",
    "text_code":     "#79C0FF",
    # Inputs
    "input_bg":      "#1C2128",
    "input_border":  "#30363D",
    "input_focus":   "#FF6B35",
    "input_text":    "#E6EDF3",
    "input_placeholder": "#484F58",
    # Buttons
    "btn_primary_bg":    "#FF6B35",
    "btn_primary_text":  "#FFFFFF",
    "btn_primary_hover": "#E55A24",
    "btn_secondary_bg":  "#21262D",
    "btn_secondary_text":"#C9D1D9",
    "btn_secondary_hover":"#30363D",
    "btn_danger_bg":     "#DA3633",
    "btn_success_bg":    "#238636",
    # Status dots
    "dot_ready":   "#2ECC71",
    "dot_busy":    "#F39C12",
    "dot_error":   "#E74C3C",
    # Scrollbar
    "scrollbar_track": "#161B22",
    "scrollbar_thumb": "#30363D",
    # Toggle button label
    "toggle_label": "☀️  Light Mode",
}

# ---------------------------------------------------------------------------
# Light theme palette
# ---------------------------------------------------------------------------
LIGHT_THEME = {
    "id": "light",
    # Backgrounds
    "bg_page":       "#F6F8FA",
    "bg_surface":    "#FFFFFF",
    "bg_surface2":   "#F0F2F5",
    "bg_header":     "#FFFFFF",
    "bg_footer":     "#F6F8FA",
    "bg_table_head": "#F0F2F5",
    "bg_table_row":  "#FFFFFF",
    "bg_table_alt":  "#F6F8FA",
    "bg_log":        "#1A1A2E",   # Log always dark (ANSI colours need dark bg)
    # Borders
    "border":        "#D0D7DE",
    "border_accent": "#FF6B35",
    # Text
    "text_primary":  "#1F2328",
    "text_secondary":"#57606A",
    "text_accent":   "#D04A00",   # Darker orange for light bg readability
    "text_link":     "#0969DA",
    "text_code":     "#0550AE",
    # Inputs
    "input_bg":      "#FFFFFF",
    "input_border":  "#D0D7DE",
    "input_focus":   "#FF6B35",
    "input_text":    "#1F2328",
    "input_placeholder": "#6E7781",
    # Buttons
    "btn_primary_bg":    "#FF6B35",
    "btn_primary_text":  "#FFFFFF",
    "btn_primary_hover": "#E55A24",
    "btn_secondary_bg":  "#F6F8FA",
    "btn_secondary_text":"#1F2328",
    "btn_secondary_hover":"#E8EAED",
    "btn_danger_bg":     "#CF222E",
    "btn_success_bg":    "#1A7F37",
    # Status dots
    "dot_ready":   "#1A7F37",
    "dot_busy":    "#D4A017",
    "dot_error":   "#CF222E",
    # Scrollbar
    "scrollbar_track": "#F6F8FA",
    "scrollbar_thumb": "#D0D7DE",
    # Toggle button label
    "toggle_label": "🌙  Dark Mode",
}


# ---------------------------------------------------------------------------
# CSS generator — produces the full stylesheet for a given theme palette
# ---------------------------------------------------------------------------
def get_css(t: dict) -> str:
    """
    Generate the complete application CSS for the given theme palette dict.
    All selectors are scoped so they override Gradio defaults cleanly.
    """
    return f"""
/* ============================================================
   PRICE IS RIGHT — UNIFIED DESIGN SYSTEM
   Theme: {t['id'].upper()}
   ============================================================ */

/* ---- Google Font import ---- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ---- Page & container ---- */
body, .gradio-container, #root {{
    background-color: {t['bg_page']} !important;
    color: {t['text_primary']} !important;
    font-family: {BRAND['font_sans']} !important;
    font-size: 14px !important;
    line-height: 1.6 !important;
}}
.gradio-container {{
    max-width: 1400px !important;
    margin: 0 auto !important;
    padding: 0 !important;
}}

/* ---- Scrollbar ---- */
::-webkit-scrollbar {{ width: 8px; height: 8px; }}
::-webkit-scrollbar-track {{ background: {t['scrollbar_track']}; }}
::-webkit-scrollbar-thumb {{ background: {t['scrollbar_thumb']}; border-radius: 4px; }}
::-webkit-scrollbar-thumb:hover {{ background: {BRAND['primary']}; }}

/* ---- Tabs ---- */
.tabs > .tab-nav {{
    background: {t['bg_surface']} !important;
    border-bottom: 2px solid {t['border']} !important;
    padding: 0 16px !important;
}}
.tabs > .tab-nav button {{
    color: {t['text_secondary']} !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    padding: 12px 20px !important;
    border: none !important;
    border-bottom: 3px solid transparent !important;
    background: transparent !important;
    transition: all 0.2s ease !important;
    border-radius: 0 !important;
}}
.tabs > .tab-nav button:hover {{
    color: {t['text_primary']} !important;
    background: {t['bg_surface2']} !important;
}}
.tabs > .tab-nav button.selected {{
    color: {BRAND['primary']} !important;
    border-bottom: 3px solid {BRAND['primary']} !important;
    font-weight: 600 !important;
    background: transparent !important;
}}

/* ---- Accordion ---- */
.accordion {{
    background: {t['bg_surface']} !important;
    border: 1px solid {t['border']} !important;
    border-radius: 8px !important;
    margin-bottom: 12px !important;
    overflow: hidden !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.12) !important;
}}
.accordion > .label-wrap {{
    background: {t['bg_surface']} !important;
    padding: 14px 18px !important;
    border-bottom: 1px solid {t['border']} !important;
    cursor: pointer !important;
}}
.accordion > .label-wrap:hover {{
    background: {t['bg_surface2']} !important;
}}
.accordion > .label-wrap span {{
    color: {t['text_primary']} !important;
    font-weight: 600 !important;
    font-size: 14px !important;
}}
.accordion > .label-wrap svg {{
    color: {t['text_secondary']} !important;
}}
.accordion .inner {{
    padding: 16px !important;
    background: {t['bg_surface']} !important;
}}

/* ---- Buttons ---- */
button.primary, .btn-primary, button[variant="primary"] {{
    background: {t['btn_primary_bg']} !important;
    color: {t['btn_primary_text']} !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 10px 20px !important;
    cursor: pointer !important;
    transition: background 0.2s ease, transform 0.1s ease !important;
    box-shadow: 0 2px 6px rgba(255,107,53,0.35) !important;
}}
button.primary:hover, .btn-primary:hover {{
    background: {t['btn_primary_hover']} !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 10px rgba(255,107,53,0.45) !important;
}}
button.primary:active {{ transform: translateY(0) !important; }}

button.secondary, .btn-secondary, button[variant="secondary"] {{
    background: {t['btn_secondary_bg']} !important;
    color: {t['btn_secondary_text']} !important;
    border: 1px solid {t['border']} !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
    font-size: 14px !important;
    padding: 10px 20px !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
}}
button.secondary:hover {{
    background: {t['btn_secondary_hover']} !important;
    border-color: {BRAND['primary']} !important;
}}

/* ---- Theme toggle button ---- */
#theme-toggle-btn {{
    background: {t['btn_secondary_bg']} !important;
    color: {t['text_primary']} !important;
    border: 1px solid {t['border']} !important;
    border-radius: 20px !important;
    padding: 6px 16px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    white-space: nowrap !important;
}}
#theme-toggle-btn:hover {{
    border-color: {BRAND['primary']} !important;
    color: {BRAND['primary']} !important;
}}

/* ---- Text inputs & textareas ---- */
input[type="text"], input[type="password"], input[type="number"],
input[type="email"], textarea, .gr-text-input {{
    background: {t['input_bg']} !important;
    border: 1px solid {t['input_border']} !important;
    border-radius: 6px !important;
    color: {t['input_text']} !important;
    font-family: {BRAND['font_sans']} !important;
    font-size: 14px !important;
    padding: 8px 12px !important;
    transition: border-color 0.2s ease !important;
}}
input:focus, textarea:focus {{
    border-color: {t['input_focus']} !important;
    outline: none !important;
    box-shadow: 0 0 0 3px rgba(255,107,53,0.15) !important;
}}
input::placeholder, textarea::placeholder {{
    color: {t['input_placeholder']} !important;
}}

/* ---- Labels ---- */
label, .gr-form label, .block label span {{
    color: {t['text_primary']} !important;
    font-weight: 500 !important;
    font-size: 13px !important;
}}
.gr-form .description, .gr-form .info {{
    color: {t['text_secondary']} !important;
    font-size: 12px !important;
}}

/* ---- Markdown & prose ---- */
.prose, .gr-markdown, .md {{
    color: {t['text_primary']} !important;
}}
.prose h1, .prose h2, .prose h3,
.gr-markdown h1, .gr-markdown h2, .gr-markdown h3 {{
    color: {t['text_accent']} !important;
    font-weight: 700 !important;
    border-bottom: 1px solid {t['border']} !important;
    padding-bottom: 6px !important;
    margin-top: 20px !important;
}}
.prose p, .gr-markdown p {{
    color: {t['text_primary']} !important;
    margin: 8px 0 !important;
}}
.prose code, .gr-markdown code {{
    background: {t['bg_surface2']} !important;
    color: {t['text_code']} !important;
    border-radius: 4px !important;
    padding: 2px 6px !important;
    font-family: {BRAND['font_mono']} !important;
    font-size: 12px !important;
    border: 1px solid {t['border']} !important;
}}
.prose pre, .gr-markdown pre {{
    background: {t['bg_surface2']} !important;
    border: 1px solid {t['border']} !important;
    border-radius: 6px !important;
    padding: 14px !important;
    overflow-x: auto !important;
}}
.prose a, .gr-markdown a {{
    color: {t['text_link']} !important;
    text-decoration: none !important;
}}
.prose a:hover, .gr-markdown a:hover {{
    text-decoration: underline !important;
}}

/* ---- Markdown tables ---- */
.prose table, .gr-markdown table {{
    width: 100% !important;
    border-collapse: collapse !important;
    margin: 12px 0 !important;
    font-size: 13px !important;
}}
.prose table th, .gr-markdown table th {{
    background: {t['bg_table_head']} !important;
    color: {t['text_accent']} !important;
    font-weight: 600 !important;
    padding: 10px 14px !important;
    border: 1px solid {t['border']} !important;
    text-align: left !important;
}}
.prose table td, .gr-markdown table td {{
    padding: 9px 14px !important;
    border: 1px solid {t['border']} !important;
    color: {t['text_primary']} !important;
}}
.prose table tr:nth-child(even) td, .gr-markdown table tr:nth-child(even) td {{
    background: {t['bg_table_alt']} !important;
}}
.prose table tr:hover td, .gr-markdown table tr:hover td {{
    background: {t['bg_surface2']} !important;
}}

/* ---- Dataframe (opportunities table) ---- */
.gr-dataframe table {{
    background: {t['bg_surface']} !important;
    border-collapse: collapse !important;
    width: 100% !important;
    font-size: 13px !important;
}}
.gr-dataframe table th {{
    background: {t['bg_table_head']} !important;
    color: {t['text_accent']} !important;
    font-weight: 600 !important;
    padding: 10px 14px !important;
    border: 1px solid {t['border']} !important;
    position: sticky !important;
    top: 0 !important;
    z-index: 1 !important;
}}
.gr-dataframe table td {{
    padding: 9px 14px !important;
    border: 1px solid {t['border']} !important;
    color: {t['text_primary']} !important;
    background: {t['bg_table_row']} !important;
}}
.gr-dataframe table tr:nth-child(even) td {{
    background: {t['bg_table_alt']} !important;
}}
.gr-dataframe table tr:hover td {{
    background: {t['bg_surface2']} !important;
    cursor: pointer !important;
}}

/* ---- Dropdown / select ---- */
select, .gr-dropdown {{
    background: {t['input_bg']} !important;
    color: {t['input_text']} !important;
    border: 1px solid {t['input_border']} !important;
    border-radius: 6px !important;
    padding: 8px 12px !important;
    font-size: 14px !important;
}}

/* ---- Slider ---- */
.gr-slider input[type=range] {{
    accent-color: {BRAND['primary']} !important;
}}

/* ---- Checkbox / radio ---- */
input[type=checkbox], input[type=radio] {{
    accent-color: {BRAND['primary']} !important;
}}

/* ---- Status badge ---- */
.status-badge {{
    display: inline-flex !important;
    align-items: center !important;
    gap: 6px !important;
    padding: 3px 10px !important;
    border-radius: 12px !important;
    font-size: 12px !important;
    font-weight: 600 !important;
}}
.status-ready  {{ background: rgba(46,204,113,0.15) !important; color: {t['dot_ready']} !important; border: 1px solid {t['dot_ready']} !important; }}
.status-busy   {{ background: rgba(243,156,18,0.15) !important; color: {t['dot_busy']} !important; border: 1px solid {t['dot_busy']} !important; }}
.status-error  {{ background: rgba(231,76,60,0.15) !important; color: {t['dot_error']} !important; border: 1px solid {t['dot_error']} !important; }}

/* ---- Log panel ---- */
.log-panel {{
    background: {t['bg_log']} !important;
    border: 1px solid {t['border']} !important;
    border-radius: 6px !important;
    padding: 14px !important;
    font-family: {BRAND['font_mono']} !important;
    font-size: 12px !important;
    line-height: 1.7 !important;
    min-height: 200px !important;
    max-height: 380px !important;
    overflow-y: auto !important;
}}

/* ---- Notification / alert banners ---- */
.alert-success {{ background: rgba(46,204,113,0.12) !important; border-left: 4px solid {t['dot_ready']} !important; color: {t['dot_ready']} !important; padding: 10px 14px !important; border-radius: 0 6px 6px 0 !important; margin: 8px 0 !important; }}
.alert-warning {{ background: rgba(243,156,18,0.12) !important; border-left: 4px solid {t['dot_busy']} !important; color: {t['dot_busy']} !important; padding: 10px 14px !important; border-radius: 0 6px 6px 0 !important; margin: 8px 0 !important; }}
.alert-error   {{ background: rgba(231,76,60,0.12) !important; border-left: 4px solid {t['dot_error']} !important; color: {t['dot_error']} !important; padding: 10px 14px !important; border-radius: 0 6px 6px 0 !important; margin: 8px 0 !important; }}
.alert-info    {{ background: rgba(52,152,219,0.12) !important; border-left: 4px solid {BRAND['info']} !important; color: {BRAND['info']} !important; padding: 10px 14px !important; border-radius: 0 6px 6px 0 !important; margin: 8px 0 !important; }}

/* ---- Divider ---- */
hr {{ border: none !important; border-top: 1px solid {t['border']} !important; margin: 16px 0 !important; }}

/* ---- Plot container ---- */
.gr-plot {{ background: {t['bg_surface']} !important; border: 1px solid {t['border']} !important; border-radius: 8px !important; }}

/* ---- Gradio default overrides ---- */
.block {{ background: transparent !important; }}
.gap {{ gap: 12px !important; }}
.wrap {{ padding: 0 !important; }}
.svelte-1gfkn6j {{ background: {t['bg_surface']} !important; }}
footer {{ display: none !important; }}

/* ---- Responsive ---- */
@media (max-width: 768px) {{
    .gradio-container {{ padding: 0 8px !important; }}
    .tabs > .tab-nav button {{ padding: 10px 12px !important; font-size: 13px !important; }}
}}
"""


def get_header_html(t: dict) -> str:
    """Return the branded page header HTML for the given theme."""
    return f"""
<div id="pir-header" style="
    text-align:center;
    padding:24px 0 16px 0;
    background:linear-gradient(135deg,{t['bg_header']},{t['bg_surface']});
    border-bottom:2px solid {BRAND['primary']};
    margin-bottom:0;
">
  <div style="font-size:2.4em;margin-bottom:4px">🎯</div>
  <h1 style="
    color:{BRAND['primary']};
    font-size:2em;
    margin:0;
    letter-spacing:0.03em;
    font-family:{BRAND['font_sans']};
    font-weight:700;
  ">The Price Is Right</h1>
  <p style="
    color:{t['text_secondary']};
    font-size:0.9em;
    margin:8px 0 0 0;
    font-family:{BRAND['font_sans']};
  ">
    Autonomous 7-Agent AI Framework
    &nbsp;<span style="color:{t['border']}">|</span>&nbsp;
    RSS Deal Hunter
    &nbsp;<span style="color:{t['border']}">|</span>&nbsp;
    RAG Price Estimator
    &nbsp;<span style="color:{t['border']}">|</span>&nbsp;
    Push Notifications
  </p>
</div>
"""


def get_footer_html(t: dict) -> str:
    """Return the branded page footer HTML for the given theme."""
    return f"""
<div id="pir-footer" style="
    text-align:center;
    padding:14px;
    border-top:1px solid {t['border']};
    margin-top:20px;
    background:{t['bg_footer']};
    font-family:{BRAND['font_sans']};
">
  <span style="color:{t['text_secondary']};font-size:12px">
    Lalit Nayyar
    &nbsp;<span style="color:{t['border']}">|</span>&nbsp;
    <a href="mailto:lalitnayyar@gmail.com" style="color:{t['text_link']};text-decoration:none">lalitnayyar@gmail.com</a>
    &nbsp;<span style="color:{t['border']}">|</span>&nbsp;
    +971508320336
    &nbsp;<span style="color:{t['border']}">|</span>&nbsp;
    +919595353336
  </span>
</div>
"""


def get_agent_status_html(t: dict) -> str:
    """Generate the 7-agent status panel HTML for the given theme."""
    agents = [
        ("1", "Scanner Agent",        "GPT-5 RSS Monitor",          BRAND["secondary"]),
        ("2", "Frontier Agent",       "RAG + GPT-5.1 Pricer",       BRAND["info"]),
        ("3", "Specialist Agent",     "Fine-tuned LLM (Modal GPU)", BRAND["danger"]),
        ("4", "Neural Network Agent", "Deep Residual DNN",          "#A78BFA"),
        ("5", "Ensemble Agent",       "Weighted Price Combiner",    BRAND["warning"]),
        ("6", "Messaging Agent",      "Pushover + Claude Notifier", "#60A5FA"),
        ("7", "Planning Agent",       "Workflow Orchestrator",      BRAND["success"]),
    ]
    rows = ""
    for num, name, role, color in agents:
        rows += (
            f'<tr style="border-bottom:1px solid {t["border"]}">'
            f'<td style="padding:10px 14px;text-align:center;font-weight:700;'
            f'color:{color};font-family:{BRAND["font_mono"]};font-size:13px">#{num}</td>'
            f'<td style="padding:10px 14px;color:{color};font-weight:600;font-size:13px">{name}</td>'
            f'<td style="padding:10px 14px;color:{t["text_secondary"]};font-size:13px">{role}</td>'
            f'<td style="padding:10px 14px;text-align:center">'
            f'<span class="status-badge status-ready">● Ready</span>'
            f'</td>'
            f'</tr>'
        )
    return (
        f'<div style="background:{t["bg_surface"]};border-radius:8px;'
        f'border:1px solid {t["border"]};overflow:hidden">'
        f'<div style="background:{t["bg_surface2"]};padding:12px 16px;'
        f'border-bottom:2px solid {BRAND["primary"]}">'
        f'<h3 style="color:{BRAND["primary"]};margin:0;font-size:13px;'
        f'letter-spacing:0.08em;font-weight:700;font-family:{BRAND["font_sans"]}">'
        f'7-AGENT COLLABORATION FRAMEWORK</h3>'
        f'</div>'
        f'<table style="width:100%;border-collapse:collapse">'
        f'<thead><tr style="background:{t["bg_table_head"]}">'
        f'<th style="padding:10px 14px;color:{t["text_accent"]};text-align:center;'
        f'font-size:12px;font-weight:600;border-bottom:1px solid {t["border"]}">#</th>'
        f'<th style="padding:10px 14px;color:{t["text_accent"]};text-align:left;'
        f'font-size:12px;font-weight:600;border-bottom:1px solid {t["border"]}">Agent</th>'
        f'<th style="padding:10px 14px;color:{t["text_accent"]};text-align:left;'
        f'font-size:12px;font-weight:600;border-bottom:1px solid {t["border"]}">Role</th>'
        f'<th style="padding:10px 14px;color:{t["text_accent"]};text-align:center;'
        f'font-size:12px;font-weight:600;border-bottom:1px solid {t["border"]}">Status</th>'
        f'</tr></thead>'
        f'<tbody>{rows}</tbody>'
        f'</table>'
        f'</div>'
    )
