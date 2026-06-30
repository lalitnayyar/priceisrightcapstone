"""
Price Is Right — Unified Design System & Theme Module
======================================================
Single source of truth for all colours, typography, spacing, and CSS.
Both dark and light themes are defined here. The dashboard and settings
page import from this module so the entire app stays visually consistent.

Fixes applied (v2):
  - Toggle button is now compact/small (pill, 28px height, 12px font)
  - All Gradio-internal selectors added with higher specificity to fix:
      * Accordion inner background bleeding white
      * Input label text invisible on dark bg
      * Input info/description text invisible
      * Markdown italic text invisible
      * Form block backgrounds bleeding white
      * svelte-generated class backgrounds
  - Header subtitle text contrast improved
  - All text-on-dark surfaces guaranteed visible

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
    "bg_page":       "#0D1117",
    "bg_surface":    "#161B22",
    "bg_surface2":   "#1C2128",
    "bg_header":     "#0D1117",
    "bg_footer":     "#0D1117",
    "bg_table_head": "#1C2128",
    "bg_table_row":  "#161B22",
    "bg_table_alt":  "#1A2030",
    "bg_log":        "#0D1117",
    # Borders
    "border":        "#30363D",
    "border_accent": "#FF6B35",
    # Text
    "text_primary":  "#E6EDF3",
    "text_secondary":"#A0ADB8",   # Brighter than before for visibility
    "text_accent":   "#FF6B35",
    "text_link":     "#4ECDC4",
    "text_code":     "#79C0FF",
    # Inputs
    "input_bg":      "#1C2128",
    "input_border":  "#444C56",   # Slightly brighter border
    "input_focus":   "#FF6B35",
    "input_text":    "#E6EDF3",
    "input_placeholder": "#8B949E",   # Raised from #6A737D (was 3.36:1 FAIL → now 5.2:1 AA PASS)
    # Buttons
    "btn_primary_bg":    "#FF6B35",
    "btn_primary_text":  "#1A1A1A",   # Dark text on orange: 6.14:1 WCAG AA PASS
    "btn_primary_hover": "#E55A24",
    "btn_secondary_bg":  "#21262D",
    "btn_secondary_text":"#C9D1D9",
    "btn_secondary_hover":"#30363D",
    "btn_danger_bg":     "#DA3633",
    "btn_success_bg":    "#238636",
    # Status dots
    "dot_ready":   "#3FB950",
    "dot_busy":    "#F39C12",
    "dot_error":   "#F85149",
    # Scrollbar
    "scrollbar_track": "#161B22",
    "scrollbar_thumb": "#30363D",
    # Toggle button label
    "toggle_label": "☀️ Light",
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
    "bg_log":        "#1A1A2E",
    # Borders
    "border":        "#D0D7DE",
    "border_accent": "#FF6B35",
    # Text
    "text_primary":  "#1F2328",
    "text_secondary":"#57606A",
    "text_accent":   "#C04A00",
    "text_link":     "#0969DA",
    "text_code":     "#0550AE",
    # Inputs
    "input_bg":      "#FFFFFF",
    "input_border":  "#D0D7DE",
    "input_focus":   "#FF6B35",
    "input_text":    "#1F2328",
    "input_placeholder": "#6E7781",   # Light theme: 4.6:1 AA PASS on white
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
    "toggle_label": "🌙 Dark",
}


# ---------------------------------------------------------------------------
# CSS generator — produces the full stylesheet for a given theme palette
# ---------------------------------------------------------------------------
def get_css(t: dict) -> str:
    """
    Generate the complete application CSS for the given theme palette dict.
    Uses high-specificity selectors and !important to override all Gradio defaults.
    """
    return f"""
/* ============================================================
   PRICE IS RIGHT — UNIFIED DESIGN SYSTEM  v2
   Theme: {t['id'].upper()}
   ============================================================ */

/* ---- Google Font import ---- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ============================================================
   BASE — Page, body, root container
   ============================================================ */
body,
.gradio-container,
#root,
.main,
.wrap,
.contain {{
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

/* ============================================================
   SCROLLBAR
   ============================================================ */
::-webkit-scrollbar {{ width: 8px; height: 8px; }}
::-webkit-scrollbar-track {{ background: {t['scrollbar_track']}; }}
::-webkit-scrollbar-thumb {{ background: {t['scrollbar_thumb']}; border-radius: 4px; }}
::-webkit-scrollbar-thumb:hover {{ background: {BRAND['primary']}; }}

/* ============================================================
   TABS
   ============================================================ */
.tabs > .tab-nav,
div.tabs > div.tab-nav {{
    background: {t['bg_surface']} !important;
    border-bottom: 2px solid {t['border']} !important;
    padding: 0 16px !important;
}}
.tabs > .tab-nav button,
div.tabs > div.tab-nav button {{
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
.tabs > .tab-nav button.selected,
div.tabs > div.tab-nav button.selected {{
    color: {BRAND['primary']} !important;
    border-bottom: 3px solid {BRAND['primary']} !important;
    font-weight: 600 !important;
    background: transparent !important;
}}

/* ============================================================
   ACCORDION — full override including Gradio svelte internals
   ============================================================ */
.accordion,
div.accordion {{
    background: {t['bg_surface']} !important;
    border: 1px solid {t['border']} !important;
    border-radius: 8px !important;
    margin-bottom: 12px !important;
    overflow: hidden !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.18) !important;
}}
/* Accordion header row */
.accordion > .label-wrap,
div.accordion > div.label-wrap,
.accordion button.label-wrap,
div[data-testid="accordion"] > button {{
    background: {t['bg_surface2']} !important;
    padding: 13px 18px !important;
    border-bottom: 1px solid {t['border']} !important;
    cursor: pointer !important;
}}
.accordion > .label-wrap:hover,
div[data-testid="accordion"] > button:hover {{
    background: {t['bg_surface']} !important;
    filter: brightness(1.08) !important;
}}
/* Accordion header text */
.accordion > .label-wrap span,
div.accordion > div.label-wrap span,
div[data-testid="accordion"] > button span,
div[data-testid="accordion"] > button p {{
    color: {t['text_primary']} !important;
    font-weight: 600 !important;
    font-size: 14px !important;
}}
/* Accordion chevron icon */
.accordion > .label-wrap svg,
div[data-testid="accordion"] > button svg {{
    color: {t['text_secondary']} !important;
    fill: {t['text_secondary']} !important;
}}
/* Accordion body / inner content — THE KEY FIX for white bleed */
.accordion .inner,
div.accordion > div.inner,
div[data-testid="accordion"] > div,
div[data-testid="accordion"] > div > div,
.accordion-content,
div.accordion .gap,
div.accordion .block,
div.accordion .form,
div.accordion .wrap,
div.accordion .contain {{
    background: {t['bg_surface']} !important;
    padding: 16px !important;
}}

/* ============================================================
   ALL BLOCK / FORM CONTAINERS — prevent white bleed
   ============================================================ */
.block,
.form,
.box,
fieldset,
.gr-form,
.gr-box,
div.block,
div.form {{
    background: {t['bg_surface']} !important;
    border-color: {t['border']} !important;
}}

/* ============================================================
   BUTTONS
   ============================================================ */
/* Primary button — white text on orange: boosted to #1A1A1A on light, white on dark */
button.primary,
.btn-primary,
button[variant="primary"],
div button.primary,
.gradio-container button.primary {{
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
button.primary:hover {{ background: {t['btn_primary_hover']} !important; transform: translateY(-1px) !important; }}
button.primary:active {{ transform: translateY(0) !important; }}

/* Secondary button */
button.secondary,
.btn-secondary,
button[variant="secondary"],
div button.secondary,
.gradio-container button.secondary {{
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
    color: {BRAND['primary']} !important;
}}

/* ============================================================
   THEME TOGGLE BUTTON — compact small pill
   ============================================================ */
#theme-toggle-btn,
#theme-toggle-btn button,
button#theme-toggle-btn {{
    background: {t['btn_secondary_bg']} !important;
    color: {t['text_secondary']} !important;
    border: 1px solid {t['border']} !important;
    border-radius: 14px !important;
    padding: 3px 12px !important;
    font-size: 11px !important;
    font-weight: 500 !important;
    height: 28px !important;
    min-height: 28px !important;
    max-height: 28px !important;
    line-height: 1 !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    white-space: nowrap !important;
    width: auto !important;
    min-width: 80px !important;
    max-width: 110px !important;
    box-shadow: none !important;
    align-self: center !important;
}}
#theme-toggle-btn:hover,
button#theme-toggle-btn:hover {{
    border-color: {BRAND['primary']} !important;
    color: {BRAND['primary']} !important;
    background: {t['btn_secondary_hover']} !important;
}}

/* ============================================================
   TEXT INPUTS, PASSWORD FIELDS, TEXTAREAS
   ============================================================ */
input[type="text"],
input[type="password"],
input[type="number"],
input[type="email"],
textarea,
.gr-text-input,
.gradio-container input,
.gradio-container textarea {{
    background: {t['input_bg']} !important;
    border: 1px solid {t['input_border']} !important;
    border-radius: 6px !important;
    color: {t['input_text']} !important;
    font-family: {BRAND['font_sans']} !important;
    font-size: 14px !important;
    padding: 8px 12px !important;
    transition: border-color 0.2s ease !important;
}}
input:focus,
textarea:focus {{
    border-color: {t['input_focus']} !important;
    outline: none !important;
    box-shadow: 0 0 0 3px rgba(255,107,53,0.15) !important;
}}
input::placeholder,
textarea::placeholder {{
    color: {t['input_placeholder']} !important;
}}

/* ============================================================
   LABELS, DESCRIPTIONS, INFO TEXT — THE KEY FIX for invisible text
   ============================================================ */
/* All label text */
label,
label span,
.block label,
.block label span,
.gr-form label,
.gr-form label span,
div.block > label,
div.block > label > span,
span.svelte-1f354aw,
.wrap > label,
.wrap > label span {{
    color: {t['text_primary']} !important;
    font-weight: 500 !important;
    font-size: 13px !important;
}}
/* Info / description text below inputs */
.info,
.description,
span.info,
p.info,
div.info,
.gr-form .info,
.gr-form .description,
span[data-testid="block-info"],
.block .info,
.block span.info,
.gradio-container .info,
.gradio-container .description,
.gradio-container span.info {{
    color: {t['text_secondary']} !important;
    font-size: 12px !important;
    font-style: normal !important;
}}
/* Italic description text (Gradio renders _desc_ as <em>) */
em, i {{
    color: {t['text_secondary']} !important;
    font-style: italic !important;
}}

/* ============================================================
   MARKDOWN & PROSE
   ============================================================ */
.prose,
.gr-markdown,
.md,
div.prose,
div.gr-markdown,
div.md,
.gradio-container .prose,
.gradio-container .gr-markdown {{
    color: {t['text_primary']} !important;
    background: transparent !important;
}}
.prose h1, .prose h2, .prose h3,
.gr-markdown h1, .gr-markdown h2, .gr-markdown h3 {{
    color: {t['text_accent']} !important;
    font-weight: 700 !important;
    border-bottom: 1px solid {t['border']} !important;
    padding-bottom: 6px !important;
    margin-top: 20px !important;
}}
.prose p, .gr-markdown p,
.prose li, .gr-markdown li,
.prose span, .gr-markdown span {{
    color: {t['text_primary']} !important;
    margin: 8px 0 !important;
}}
.prose strong, .gr-markdown strong,
.prose b, .gr-markdown b {{
    color: {t['text_primary']} !important;
    font-weight: 700 !important;
}}
.prose em, .gr-markdown em {{
    color: {t['text_secondary']} !important;
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
.prose a:hover, .gr-markdown a:hover {{ text-decoration: underline !important; }}

/* ============================================================
   MARKDOWN TABLES
   ============================================================ */
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
    background: {t['bg_table_row']} !important;
}}
.prose table tr:nth-child(even) td, .gr-markdown table tr:nth-child(even) td {{
    background: {t['bg_table_alt']} !important;
}}
.prose table tr:hover td, .gr-markdown table tr:hover td {{
    background: {t['bg_surface2']} !important;
}}

/* ============================================================
   DATAFRAME (Deal Opportunities table)
   ============================================================ */
.gr-dataframe,
div.gr-dataframe,
.gradio-container .gr-dataframe,
table.svelte-table {{
    background: {t['bg_surface']} !important;
}}
.gr-dataframe table {{
    background: {t['bg_surface']} !important;
    border-collapse: collapse !important;
    width: 100% !important;
    font-size: 13px !important;
}}
.gr-dataframe table th,
.gr-dataframe thead th {{
    background: {t['bg_table_head']} !important;
    color: {t['text_accent']} !important;
    font-weight: 600 !important;
    padding: 10px 14px !important;
    border: 1px solid {t['border']} !important;
    position: sticky !important;
    top: 0 !important;
    z-index: 1 !important;
}}
.gr-dataframe table td,
.gr-dataframe tbody td {{
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

/* ============================================================
   DROPDOWN / SELECT
   ============================================================ */
select,
.gr-dropdown,
.gradio-container select {{
    background: {t['input_bg']} !important;
    color: {t['input_text']} !important;
    border: 1px solid {t['input_border']} !important;
    border-radius: 6px !important;
    padding: 8px 12px !important;
    font-size: 14px !important;
}}

/* ============================================================
   SLIDER / CHECKBOX / RADIO
   ============================================================ */
.gr-slider input[type=range] {{ accent-color: {BRAND['primary']} !important; }}
input[type=checkbox], input[type=radio] {{ accent-color: {BRAND['primary']} !important; }}

/* ============================================================
   STATUS BADGES
   ============================================================ */
.status-badge {{
    display: inline-flex !important;
    align-items: center !important;
    gap: 6px !important;
    padding: 3px 10px !important;
    border-radius: 12px !important;
    font-size: 12px !important;
    font-weight: 600 !important;
}}
.status-ready  {{ background: rgba(63,185,80,0.15)  !important; color: {t['dot_ready']} !important; border: 1px solid {t['dot_ready']} !important; }}
.status-busy   {{ background: rgba(243,156,18,0.15) !important; color: {t['dot_busy']}  !important; border: 1px solid {t['dot_busy']}  !important; }}
.status-error  {{ background: rgba(248,81,73,0.15)  !important; color: {t['dot_error']} !important; border: 1px solid {t['dot_error']} !important; }}

/* ============================================================
   LOG PANEL
   ============================================================ */
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

/* ============================================================
   ALERT / NOTIFICATION BANNERS
   ============================================================ */
.alert-success {{ background: rgba(63,185,80,0.12)  !important; border-left: 4px solid {t['dot_ready']} !important; color: {t['dot_ready']} !important; padding: 10px 14px !important; border-radius: 0 6px 6px 0 !important; margin: 8px 0 !important; }}
.alert-warning {{ background: rgba(243,156,18,0.12) !important; border-left: 4px solid {t['dot_busy']}  !important; color: {t['dot_busy']}  !important; padding: 10px 14px !important; border-radius: 0 6px 6px 0 !important; margin: 8px 0 !important; }}
.alert-error   {{ background: rgba(248,81,73,0.12)  !important; border-left: 4px solid {t['dot_error']} !important; color: {t['dot_error']} !important; padding: 10px 14px !important; border-radius: 0 6px 6px 0 !important; margin: 8px 0 !important; }}
.alert-info    {{ background: rgba(52,152,219,0.12)  !important; border-left: 4px solid {BRAND['info']}  !important; color: {BRAND['info']}  !important; padding: 10px 14px !important; border-radius: 0 6px 6px 0 !important; margin: 8px 0 !important; }}


/* ============================================================
   SETTINGS PAGE HEADER BANNER
   ============================================================ */
.settings-header {
    background: {t['bg_surface2']} !important;
    border-radius: 8px !important;
    padding: 18px 24px !important;
    margin-bottom: 16px !important;
    border: 1px solid {BRAND['primary']} !important;
    border-left: 4px solid {BRAND['primary']} !important;
}
.settings-header h2 {
    color: {BRAND['primary']} !important;
    margin: 0 0 6px 0 !important;
    font-size: 1.3em !important;
    font-weight: 700 !important;
}
.settings-header p {
    color: {t['text_secondary']} !important;
    margin: 0 !important;
    font-size: 0.88em !important;
    line-height: 1.6 !important;
}
.settings-header code {
    border: 1px solid {t['border']} !important;
    border-radius: 3px !important;
    padding: 1px 5px !important;
}

/* ============================================================
   DIVIDER
   ============================================================ */
hr {{ border: none !important; border-top: 1px solid {t['border']} !important; margin: 16px 0 !important; }}

/* ============================================================
   PLOT CONTAINER
   ============================================================ */
.gr-plot {{ background: {t['bg_surface']} !important; border: 1px solid {t['border']} !important; border-radius: 8px !important; }}

/* ============================================================
   GRADIO SVELTE-GENERATED CLASS OVERRIDES
   These target the hashed class names Gradio injects at runtime.
   Using attribute selectors and broad patterns for resilience.
   ============================================================ */
/* Any div that Gradio uses as a panel/block wrapper */
div[class*="svelte"] {{
    background-color: inherit !important;
}}
/* Gradio's internal panel containers */
.panel, .panel-content, .panel-inner {{
    background: {t['bg_surface']} !important;
    color: {t['text_primary']} !important;
}}
/* Gradio Code block */
.code-wrap, .code-wrap pre, .code-wrap code {{
    background: {t['bg_surface2']} !important;
    color: {t['text_code']} !important;
    border: 1px solid {t['border']} !important;
    border-radius: 6px !important;
    font-family: {BRAND['font_mono']} !important;
    font-size: 12px !important;
}}
/* Gradio File component */
.file-preview, .file-preview-title {{
    background: {t['bg_surface2']} !important;
    color: {t['text_primary']} !important;
    border-color: {t['border']} !important;
}}
/* Gradio number input spinners */
input[type=number]::-webkit-inner-spin-button,
input[type=number]::-webkit-outer-spin-button {{
    opacity: 0.4 !important;
    filter: invert({1 if t['id'] == 'dark' else 0}) !important;
}}

/* ============================================================
   HIDE GRADIO DEFAULT FOOTER
   ============================================================ */
footer.svelte-mpyp5e,
footer {{ display: none !important; }}

/* ============================================================
   RESPONSIVE
   ============================================================ */
@media (max-width: 768px) {{
    .gradio-container {{ padding: 0 8px !important; }}
    .tabs > .tab-nav button {{ padding: 10px 12px !important; font-size: 13px !important; }}
    #theme-toggle-btn {{ min-width: 70px !important; font-size: 10px !important; }}
}}
"""


def get_header_html(t: dict) -> str:
    """Return the branded page header HTML for the given theme."""
    return (
        f'<div id="pir-header" style="'
        f'text-align:center;padding:20px 0 14px 0;'
        f'background:linear-gradient(135deg,{t["bg_header"]},{t["bg_surface"]});'
        f'border-bottom:2px solid {BRAND["primary"]};margin-bottom:0">'
        f'<div style="font-size:2em;margin-bottom:2px">🎯</div>'
        f'<h1 style="color:{BRAND["primary"]};font-size:1.9em;margin:0;'
        f'letter-spacing:0.03em;font-family:{BRAND["font_sans"]};font-weight:700">'
        f'The Price Is Right</h1>'
        f'<p style="color:{t["text_secondary"]};font-size:0.82em;margin:6px 0 0 0;'
        f'font-family:{BRAND["font_sans"]};letter-spacing:0.04em">'
        f'Autonomous 7-Agent AI Framework'
        f'&nbsp;<span style="color:{t["text_secondary"]};opacity:0.5">|</span>&nbsp;'
        f'RSS Deal Hunter'
        f'&nbsp;<span style="color:{t["text_secondary"]};opacity:0.5">|</span>&nbsp;'
        f'RAG Price Estimator'
        f'&nbsp;<span style="color:{t["text_secondary"]};opacity:0.5">|</span>&nbsp;'
        f'Push Notifications'
        f'</p>'
        f'</div>'
    )


def get_footer_html(t: dict) -> str:
    """Return the branded page footer HTML for the given theme."""
    return (
        f'<div id="pir-footer" style="'
        f'text-align:center;padding:12px;border-top:1px solid {t["border"]};'
        f'margin-top:20px;background:{t["bg_footer"]};font-family:{BRAND["font_sans"]}">'
        f'<span style="color:{t["text_secondary"]};font-size:12px">'
        f'Lalit Nayyar'
        f'&nbsp;<span style="color:{t["text_secondary"]};opacity:0.5">|</span>&nbsp;'
        f'<a href="mailto:lalitnayyar@gmail.com" style="color:{t["text_link"]};text-decoration:none">'
        f'lalitnayyar@gmail.com</a>'
        f'&nbsp;<span style="color:{t["text_secondary"]};opacity:0.5">|</span>&nbsp;'
        f'+971508320336'
        f'&nbsp;<span style="color:{t["text_secondary"]};opacity:0.5">|</span>&nbsp;'
        f'+919595353336'
        f'</span>'
        f'</div>'
    )


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
        bg = t["bg_table_row"] if int(num) % 2 == 1 else t["bg_table_alt"]
        rows += (
            f'<tr style="background:{bg};border-bottom:1px solid {t["border"]}">'
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
        f'<div style="background:{t["bg_surface2"]};padding:10px 16px;'
        f'border-bottom:2px solid {BRAND["primary"]}">'
        f'<h3 style="color:{BRAND["primary"]};margin:0;font-size:12px;'
        f'letter-spacing:0.1em;font-weight:700;font-family:{BRAND["font_sans"]}">'
        f'7-AGENT COLLABORATION FRAMEWORK</h3>'
        f'</div>'
        f'<table style="width:100%;border-collapse:collapse">'
        f'<thead><tr style="background:{t["bg_table_head"]}">'
        f'<th style="padding:9px 14px;color:{t["text_accent"]};text-align:center;'
        f'font-size:11px;font-weight:600;border-bottom:1px solid {t["border"]};text-transform:uppercase;letter-spacing:0.06em">#</th>'
        f'<th style="padding:9px 14px;color:{t["text_accent"]};text-align:left;'
        f'font-size:11px;font-weight:600;border-bottom:1px solid {t["border"]};text-transform:uppercase;letter-spacing:0.06em">Agent</th>'
        f'<th style="padding:9px 14px;color:{t["text_accent"]};text-align:left;'
        f'font-size:11px;font-weight:600;border-bottom:1px solid {t["border"]};text-transform:uppercase;letter-spacing:0.06em">Role</th>'
        f'<th style="padding:9px 14px;color:{t["text_accent"]};text-align:center;'
        f'font-size:11px;font-weight:600;border-bottom:1px solid {t["border"]};text-transform:uppercase;letter-spacing:0.06em">Status</th>'
        f'</tr></thead>'
        f'<tbody>{rows}</tbody>'
        f'</table>'
        f'</div>'
    )
