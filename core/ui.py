"""
core/ui.py — Shared UI helpers for the Food Allergy Ingredient Checker.

render_html() fixes the root cause of raw-HTML-as-code-block bugs:
Streamlit's CommonMark parser converts any line that starts with 4+
spaces into a <pre><code> block, so indented HTML inside triple-quoted
strings renders as code text instead of markup. render_html() strips
that leading whitespace before calling st.markdown.

apply_theme() injects the global CSS once via render_html().

No matching or business-logic imports are allowed in this file.
"""
from __future__ import annotations

import re
import textwrap


def render_html(block: str) -> None:
    """
    Render a block of HTML via st.markdown, fixing the indentation issue
    that causes Streamlit to display HTML as a code block.

    Rules applied before rendering:
    1. Strip common leading whitespace (textwrap.dedent).
    2. Remove all leading whitespace from every line (so no line starts
       with 4+ spaces, which CommonMark would treat as a code fence).
    3. Collapse runs of blank lines to a single blank line.
    4. Strip leading/trailing blank lines from the whole block.

    Args:
        block: A string of HTML, typically a triple-quoted literal.
    """
    import streamlit as st  # imported here so core/ui.py stays importable in tests

    # 1. Remove common indentation added by Python indentation
    cleaned = textwrap.dedent(block)
    # 2. Strip ALL leading whitespace from every line
    lines = [line.lstrip() for line in cleaned.splitlines()]
    # 3. Collapse consecutive blank lines
    result_lines: list[str] = []
    prev_blank = False
    for line in lines:
        is_blank = line.strip() == ""
        if is_blank and prev_blank:
            continue
        result_lines.append(line)
        prev_blank = is_blank
    # 4. Strip leading/trailing blank lines
    cleaned = "\n".join(result_lines).strip()
    st.markdown(cleaned, unsafe_allow_html=True)


# ── Cherry palette ────────────────────────────────────────────────────────────
CHERRY         = "#D20A2E"
DARK_CHERRY    = "#8F0720"
DEEP_CHERRY    = "#5C0516"
TINT           = "#FCE8EB"
WHITE          = "#FFFFFF"
TEXT_DARK      = "#2B1B1E"
TEXT_BODY      = "#4B3035"
TEXT_MUTED     = "#9C7980"
BORDER_TINT    = "#F5C2C7"

# Status colours — WCAG AA, visually distinct from brand cherry
PRESENT_FG       = "#FFFFFF"
PRESENT_BG       = "#5C0516"   # deep cherry — darker than brand, unmistakably urgent
PRESENT_BORDER   = "#3D000F"
PRESENT_ICON     = "⛔"
PRESENT_LABEL    = "PRESENT"

MAY_FG           = "#FFFFFF"
MAY_BG           = "#B84500"   # orange — different hue family from cherry
MAY_BORDER       = "#8C3200"
MAY_ICON         = "⚠️"
MAY_LABEL        = "MAY CONTAIN"

UNCERTAIN_FG     = "#2B1B1E"   # dark text on amber — WCAG AA (ratio > 4.5)
UNCERTAIN_BG     = "#C97A00"   # amber-yellow
UNCERTAIN_BORDER = "#9A5C00"
UNCERTAIN_ICON   = "❓"
UNCERTAIN_LABEL  = "UNCERTAIN"

NOT_RECOGNISED_FG     = "#374151"
NOT_RECOGNISED_BG     = "#F3F4F6"   # neutral grey
NOT_RECOGNISED_BORDER = "#D1D5DB"
NOT_RECOGNISED_ICON   = "❔"
NOT_RECOGNISED_LABEL  = "NOT RECOGNISED"

NO_MATCH_FG      = DARK_CHERRY
NO_MATCH_BG      = WHITE
NO_MATCH_BORDER  = CHERRY
NO_MATCH_ICON    = "✅"
NO_MATCH_LABEL   = "No Known Match Found"


def apply_theme() -> None:
    """
    Inject the global cherry-red & white CSS design system.
    Must be called once in app.py after set_page_config.
    Uses render_html() so no indentation issues arise.
    """
    css = f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root {{
--cherry:       {CHERRY};
--dark-cherry:  {DARK_CHERRY};
--deep-cherry:  {DEEP_CHERRY};
--tint:         {TINT};
--white:        {WHITE};
--text-dark:    {TEXT_DARK};
--text-body:    {TEXT_BODY};
--text-muted:   {TEXT_MUTED};
--border-tint:  {BORDER_TINT};
--radius-sm:    8px;
--radius-md:    12px;
--radius-lg:    20px;
--shadow:       0 4px 16px rgba(210,10,46,.10);
--shadow-sm:    0 2px 8px rgba(210,10,46,.07);
--transition:   all 180ms ease;
}}
html,body,[class*="css"] {{
font-family:'Inter',-apple-system,BlinkMacSystemFont,sans-serif !important;
color:var(--text-body);
}}
h1,h2,h3,h4 {{
font-family:'Plus Jakarta Sans',sans-serif !important;
color:var(--dark-cherry) !important;
font-weight:800 !important;
}}
/* Hero banner: override the global heading colour so titles stay white */
.hero h1,.hero h2,.hero h3,.hero h4 {{
color:#FFFFFF !important;
text-shadow:0 1px 4px rgba(0,0,0,.30) !important;
}}
.stApp {{ background:var(--white) !important; }}
[data-testid="stSidebar"] {{
background:var(--tint) !important;
border-right:1px solid var(--border-tint) !important;
}}
.stButton>button[kind="primary"] {{
background:linear-gradient(135deg,{CHERRY},{DARK_CHERRY}) !important;
color:#fff !important;border:none !important;
border-radius:var(--radius-md) !important;padding:10px 24px !important;
font-family:'Plus Jakarta Sans',sans-serif !important;font-weight:700 !important;
font-size:0.95rem !important;box-shadow:0 4px 14px rgba(210,10,46,.30) !important;
transition:var(--transition) !important;
}}
.stButton>button[kind="primary"]:hover {{
background:linear-gradient(135deg,{DARK_CHERRY},{DEEP_CHERRY}) !important;
box-shadow:0 6px 20px rgba(143,7,32,.40) !important;
transform:translateY(-1px) !important;
}}
.stButton>button:not([kind="primary"]) {{
background:#fff !important;color:var(--cherry) !important;
border:1.5px solid var(--cherry) !important;
border-radius:var(--radius-sm) !important;
font-family:'Plus Jakarta Sans',sans-serif !important;font-weight:600 !important;
transition:var(--transition) !important;
}}
.stButton>button:not([kind="primary"]):hover {{
background:var(--tint) !important;border-color:var(--dark-cherry) !important;
}}
.stDownloadButton>button {{
background:linear-gradient(135deg,{CHERRY},{DARK_CHERRY}) !important;
color:#fff !important;border:none !important;
border-radius:var(--radius-md) !important;
font-family:'Plus Jakarta Sans',sans-serif !important;font-weight:700 !important;
box-shadow:0 4px 14px rgba(210,10,46,.28) !important;
transition:var(--transition) !important;
}}
.stDownloadButton>button:hover {{
transform:translateY(-1px) !important;
}}
.stTextInput>div>div>input,
.stTextArea>div>div>textarea {{
background:#fff !important;border:1.5px solid #E5E7EB !important;
border-radius:var(--radius-sm) !important;
font-family:'Inter',sans-serif !important;
color:var(--text-dark) !important;transition:var(--transition) !important;
}}
.stTextInput>div>div>input:focus,
.stTextArea>div>div>textarea:focus {{
border-color:var(--cherry) !important;
box-shadow:0 0 0 3px rgba(210,10,46,.15) !important;
}}
.stSelectbox>div>div {{
border-radius:var(--radius-sm) !important;
border:1.5px solid #E5E7EB !important;background:#fff !important;
}}
.stSelectbox>div>div:focus-within {{
border-color:var(--cherry) !important;
box-shadow:0 0 0 3px rgba(210,10,46,.12) !important;
}}
.stTabs [data-baseweb="tab-list"] {{
background:var(--tint) !important;
border-radius:var(--radius-md) !important;
padding:4px !important;gap:4px !important;border-bottom:none !important;
}}
.stTabs [data-baseweb="tab"] {{
border-radius:var(--radius-sm) !important;
font-family:'Plus Jakarta Sans',sans-serif !important;
font-weight:600 !important;font-size:0.875rem !important;
color:var(--text-body) !important;background:transparent !important;
transition:var(--transition) !important;
}}
.stTabs [aria-selected="true"] {{
background:#fff !important;color:var(--cherry) !important;
box-shadow:var(--shadow-sm) !important;
}}
.stExpander {{
border:1.5px solid var(--border-tint) !important;
border-radius:var(--radius-md) !important;background:#fff !important;
}}
.stExpander summary {{
font-family:'Plus Jakarta Sans',sans-serif !important;
font-weight:600 !important;color:var(--text-dark) !important;
}}
hr {{
border:none !important;border-top:1px solid var(--border-tint) !important;
margin:1.5rem 0 !important;
}}
.stSpinner>div {{ border-top-color:var(--cherry) !important; }}
[data-testid="stFileUploadDropzone"] {{
border:2px dashed var(--border-tint) !important;
border-radius:var(--radius-md) !important;
background:var(--tint) !important;transition:var(--transition) !important;
}}
[data-testid="stFileUploadDropzone"]:hover {{
border-color:var(--cherry) !important;
}}
::-webkit-scrollbar {{ width:6px;height:6px; }}
::-webkit-scrollbar-track {{ background:var(--tint); }}
::-webkit-scrollbar-thumb {{ background:var(--border-tint);border-radius:99px; }}
::-webkit-scrollbar-thumb:hover {{ background:var(--cherry); }}
.main .block-container {{ padding-top:1.5rem !important;padding-bottom:0 !important; }}
@keyframes fadeUp {{
from {{ opacity:0;transform:translateY(12px); }}
to {{ opacity:1;transform:translateY(0); }}
}}
.fade-up {{ animation:fadeUp 250ms ease forwards; }}
.feat-card {{ transition:transform 200ms ease,box-shadow 200ms ease; }}
.feat-card:hover {{
transform:translateY(-4px);
box-shadow:0 12px 32px rgba(210,10,46,.15) !important;
}}
.stat-card {{ transition:transform 180ms ease; }}
.stat-card:hover {{ transform:translateY(-2px); }}
</style>
"""
    render_html(css)
