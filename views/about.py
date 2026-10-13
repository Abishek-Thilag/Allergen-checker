"""
views/about.py — About page. All HTML via render_html().
"""
from __future__ import annotations
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from core.constants import DISCLAIMER_TEXT, DISCLAIMER_TEXT_SHORT
from core.ui import (
    render_html,
    CHERRY, DARK_CHERRY, TINT, WHITE,
    TEXT_DARK, TEXT_BODY, TEXT_MUTED, BORDER_TINT,
    PRESENT_FG, PRESENT_BG, PRESENT_BORDER, PRESENT_ICON, PRESENT_LABEL,
    MAY_FG, MAY_BG, MAY_BORDER, MAY_ICON, MAY_LABEL,
    UNCERTAIN_FG, UNCERTAIN_BG, UNCERTAIN_BORDER, UNCERTAIN_ICON, UNCERTAIN_LABEL,
)

DECODER_TABLE = [
    ("Casein",              "🥛 Milk protein"),
    ("Whey",                "🥛 Milk protein fraction"),
    ("Maida",               "🌾 Refined wheat flour"),
    ("Groundnut / Mungfali","🥜 Peanut"),
    ("Ghee / Dahi / Paneer","🥛 Milk derivatives"),
    ("INS 322",             "🫘 Lecithin (may be soy or egg)"),
    ("Til / Gingelly",      "🌿 Sesame"),
    ("Rai / Sarson",        "🌿 Mustard"),
    ("Khoya / Mawa",        "🥛 Reduced milk"),
    ("Soya / Tofu",         "🫘 Soy"),
    ("Arachis oil",         "🥜 Peanut oil"),
    ("Atta / Suji / Rava",  "🌾 Wheat flour / semolina"),
]

NOT_CLAIMED = [
    ("Does NOT declare any product safe",
     '"No known match found" is not a safety clearance. Always read the original label.'),
    ("Does NOT guarantee completeness",
     "The synonym dictionary is curated but not exhaustive. Regional terms may be missing."),
    ("Does NOT provide medical advice",
     "It is an informational aid. Consult a doctor or dietitian for allergen management."),
    ("OCR can misread text",
     "Always review and correct extracted text before checking."),
    ("INS codes can have multiple sources",
     "INS 322 (lecithin) may come from soy, egg, or sunflower. Variable-source codes are always UNCERTAIN."),
    ("Does not cover all Indian languages",
     "Hindi/Urdu transliterations only. Tamil, Telugu, Bengali, Kannada, Marathi etc. not covered."),
    ("Does not check cross-contact during cooking",
     "Only declared ingredient labels are analysed."),
    ('"No known match found" ≠ free from allergen',
     "This phrase means the tool found nothing to flag — not that the product is allergen-free."),
]

HOW_IT_WORKS = [
    ("📝", "Input",    "Type/paste an ingredient list, upload a label photo, or load a sample."),
    ("🔧", "Parsing",  "Text is lowercased, nested groups flattened, trace statements extracted."),
    ("🔍", "Matching", "Tokens are checked: exact → fuzzy → INS code → vague flag."),
    ("🏷️", "Results",  "Each allergen in your profile gets PRESENT, MAY CONTAIN, or UNCERTAIN."),
    ("🗄️", "History",  "Every check is saved locally to SQLite. No data leaves your device."),
    ("📄", "PDF",      "Download a report with results, explanations, and the disclaimer."),
]


def show() -> None:
    render_html(f"""
<div style="background:{TINT};border:1px solid {BORDER_TINT};border-radius:8px;
    padding:10px 12px;font-size:0.75rem;color:{TEXT_MUTED};line-height:1.5;margin-top:8px;">
⚠️ {DISCLAIMER_TEXT_SHORT}
</div>
""")
    render_html(f"""
<div style="background:{TINT};border:1px solid {BORDER_TINT};border-radius:10px;
    padding:14px;margin:12px 0;">
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;
    font-size:0.82rem;color:{DARK_CHERRY};margin-bottom:8px;">🔗 Quick Links</div>
<div style="display:flex;flex-direction:column;gap:6px;">
<a href="/Check" target="_self" style="font-size:0.8rem;color:{CHERRY};
    text-decoration:none;font-weight:500;">🔍 Go to Check page →</a>
<a href="/History" target="_self" style="font-size:0.8rem;color:{CHERRY};
    text-decoration:none;font-weight:500;">🕘 View History →</a>
</div>
</div>
""")

    # Hero
    render_html(f"""
<div class="fade-up" style="background:linear-gradient(135deg,{CHERRY} 0%,{DARK_CHERRY} 100%);
    border-radius:20px;padding:28px 32px;margin-bottom:28px;
    box-shadow:0 6px 24px rgba(210,4,45,.22);">
<h1 style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;
    font-size:1.6rem;color:#fff;margin:0;">ℹ️ About This App</h1>
<p style="color:rgba(255,255,255,.88);margin:6px 0 0;font-size:0.9375rem;">
Food Allergy Ingredient Checker — how it works, what it does, and what it doesn't.
</p>
</div>
""")

    # What it does
    render_html(f"""
<h2 style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;
    font-size:1.2rem;color:{DARK_CHERRY};margin:0 0 16px;">🎯 What It Does</h2>
<div style="background:{WHITE};border-radius:12px;padding:18px 22px;
    border:1px solid {BORDER_TINT};box-shadow:0 2px 8px rgba(210,4,45,.05);
    margin-bottom:24px;font-size:0.9375rem;color:{TEXT_BODY};line-height:1.7;">
<strong style="color:{TEXT_DARK};">Food Allergy Ingredient Checker</strong>
helps people with food allergies understand whether a packaged Indian food product
contains ingredients they need to avoid.<br><br>
Indian food labels often list allergens under technical names, Indian regional names,
or INS/E-number additive codes that are not immediately recognisable.
</div>
""")

    # Decoder table
    render_html(f"""
<h2 style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;
    font-size:1.2rem;color:{DARK_CHERRY};margin:0 0 16px;">📖 Hidden Name Decoder</h2>
""")
    rows_html = "".join([
        f"<tr>"
        f"<td style='padding:8px 14px;font-family:monospace;font-size:0.875rem;"
        f"background:{TINT};color:{DARK_CHERRY};font-weight:600;"
        f"border-radius:6px;white-space:nowrap;'>{label}</td>"
        f"<td style='padding:8px 14px;color:{TEXT_BODY};font-size:0.875rem;'>{meaning}</td>"
        f"</tr>"
        for label, meaning in DECODER_TABLE
    ])
    render_html(f"""
<div style="background:{WHITE};border-radius:12px;overflow:hidden;
    border:1px solid {BORDER_TINT};box-shadow:0 2px 8px rgba(210,4,45,.05);
    margin-bottom:24px;">
<table style="width:100%;border-collapse:separate;border-spacing:0 6px;padding:12px 8px;">
<thead><tr>
<th style="text-align:left;padding:8px 14px;font-size:0.78rem;
    color:{TEXT_MUTED};font-weight:600;text-transform:uppercase;
    letter-spacing:.07em;">What The Label Says</th>
<th style="text-align:left;padding:8px 14px;font-size:0.78rem;
    color:{TEXT_MUTED};font-weight:600;text-transform:uppercase;
    letter-spacing:.07em;">What It Actually Is</th>
</tr></thead>
<tbody>{rows_html}</tbody>
</table>
</div>
""")

    # Status system
    render_html(f"""
<h2 style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;
    font-size:1.2rem;color:{DARK_CHERRY};margin:0 0 16px;">🏷️ The Three Statuses</h2>
<div style="display:flex;flex-direction:column;gap:10px;margin-bottom:24px;">
<div style="background:{PRESENT_BG};border:1.5px solid {PRESENT_BORDER};border-radius:10px;
    padding:13px 16px;display:flex;align-items:center;gap:12px;">
<span style="color:{PRESENT_FG};border-radius:20px;padding:4px 14px;font-size:0.82rem;
    font-weight:700;font-family:'Plus Jakarta Sans',sans-serif;white-space:nowrap;
    background:rgba(0,0,0,.15);">{PRESENT_ICON} {PRESENT_LABEL}</span>
<span style="font-size:0.9rem;color:{PRESENT_FG};opacity:.9;">
A matching ingredient or synonym was found.
</span>
</div>
<div style="background:{MAY_BG};border:1.5px solid {MAY_BORDER};border-radius:10px;
    padding:13px 16px;display:flex;align-items:center;gap:12px;">
<span style="color:{MAY_FG};border-radius:20px;padding:4px 14px;font-size:0.82rem;
    font-weight:700;font-family:'Plus Jakarta Sans',sans-serif;white-space:nowrap;
    background:rgba(0,0,0,.15);">{MAY_ICON} {MAY_LABEL}</span>
<span style="font-size:0.9rem;color:{MAY_FG};opacity:.9;">
A trace or cross-contamination statement was found.
</span>
</div>
<div style="background:{UNCERTAIN_BG};border:1.5px solid {UNCERTAIN_BORDER};border-radius:10px;
    padding:13px 16px;display:flex;align-items:center;gap:12px;">
<span style="color:{UNCERTAIN_FG};border-radius:20px;padding:4px 14px;font-size:0.82rem;
    font-weight:700;font-family:'Plus Jakarta Sans',sans-serif;white-space:nowrap;
    background:rgba(0,0,0,.10);">{UNCERTAIN_ICON} {UNCERTAIN_LABEL}</span>
<span style="font-size:0.9rem;color:{UNCERTAIN_FG};opacity:.9;">
Vague wording or an INS code with multiple possible sources.
</span>
</div>
</div>
""")

    # How it works
    render_html(f"""
<h2 style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;
    font-size:1.2rem;color:{DARK_CHERRY};margin:0 0 16px;">🔧 How It Works</h2>
""")
    cols = st.columns(3)
    for idx, (icon, title, desc) in enumerate(HOW_IT_WORKS):
        with cols[idx % 3]:
            render_html(f"""
<div style="background:{WHITE};border-radius:12px;padding:16px;
    border-left:4px solid {CHERRY};border-top:1px solid {BORDER_TINT};
    border-right:1px solid {BORDER_TINT};border-bottom:1px solid {BORDER_TINT};
    box-shadow:0 2px 6px rgba(210,4,45,.05);margin-bottom:12px;min-height:130px;">
<div style="font-size:1.5rem;margin-bottom:6px;">{icon}</div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;
    color:{DARK_CHERRY};margin-bottom:4px;">{title}</div>
<div style="font-size:0.82rem;color:{TEXT_MUTED};line-height:1.5;">{desc}</div>
</div>
""")

    # Not claimed
    render_html(f"""
<h2 style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;
    font-size:1.2rem;color:{DARK_CHERRY};margin:16px 0 16px;">⚠️ What This Tool Does NOT Claim</h2>
""")
    for i, (heading, detail) in enumerate(NOT_CLAIMED, 1):
        render_html(f"""
<div style="background:{WHITE};border-radius:10px;padding:13px 16px;
    border:1px solid {BORDER_TINT};box-shadow:0 1px 4px rgba(210,4,45,.05);
    margin-bottom:8px;display:flex;gap:12px;align-items:flex-start;">
<span style="background:{TINT};color:{DARK_CHERRY};
    border-radius:50%;width:26px;height:26px;display:flex;
    align-items:center;justify-content:center;font-weight:800;
    font-size:0.8rem;flex-shrink:0;">{i}</span>
<div>
<div style="font-weight:700;color:{TEXT_DARK};font-size:0.9rem;margin-bottom:2px;">
This tool {heading}.
</div>
<div style="font-size:0.85rem;color:{TEXT_BODY};">{detail}</div>
</div>
</div>
""")

    # Disclaimer
    render_html(f"""
<h2 style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;
    font-size:1.2rem;color:{DARK_CHERRY};margin:16px 0 16px;">📋 Disclaimer</h2>
<div style="background:#FFF0F2;border:2px solid {BORDER_TINT};border-radius:14px;
    padding:20px 24px;margin-bottom:24px;">
<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
<span style="font-size:1.5rem;">⚠️</span>
<span style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;
    font-size:1rem;color:{DARK_CHERRY};">Important Disclaimer</span>
</div>
<div style="font-size:0.9rem;color:{TEXT_BODY};line-height:1.7;">
{DISCLAIMER_TEXT.replace("⚠️ ", "").replace("⚠️", "").strip()}
</div>
</div>
""")

    # Footer
    render_html(f"""
<div style="background:#1F2937;border-radius:16px;padding:28px 32px 20px;margin-top:16px;">
<div style="display:grid;grid-template-columns:2fr 1fr 1fr;gap:28px;margin-bottom:20px;">
<div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;
    font-size:1rem;color:#fff;margin-bottom:8px;">🥛 Food Allergy Ingredient Checker</div>
<div style="font-size:0.83rem;color:#9CA3AF;line-height:1.7;max-width:300px;margin-bottom:10px;">
A local, offline tool that decodes hidden allergens in Indian packaged food.
No data ever leaves your device.
</div>
<div style="display:inline-block;background:#374151;border-radius:6px;
    padding:4px 12px;font-size:0.72rem;color:#9CA3AF;">
⚠️ Aid only — not medical advice
</div>
</div>
<div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;font-size:0.75rem;
    color:{CHERRY};text-transform:uppercase;letter-spacing:.08em;margin-bottom:10px;">Pages</div>
<div style="display:flex;flex-direction:column;gap:7px;">
<a href="/Check" target="_self" style="color:#D1D5DB;font-size:0.83rem;text-decoration:none;">🔍 Check</a>
<a href="/History" target="_self" style="color:#D1D5DB;font-size:0.83rem;text-decoration:none;">🕘 History</a>
<a href="/About" target="_self" style="color:#D1D5DB;font-size:0.83rem;text-decoration:none;">ℹ️ About</a>
</div>
</div>
<div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;font-size:0.75rem;
    color:{CHERRY};text-transform:uppercase;letter-spacing:.08em;margin-bottom:10px;">Built With</div>
<div style="display:flex;flex-direction:column;gap:7px;">
<span style="color:#D1D5DB;font-size:0.83rem;">🌊 Streamlit</span>
<span style="color:#D1D5DB;font-size:0.83rem;">🐍 Python 3.10+</span>
<span style="color:#D1D5DB;font-size:0.83rem;">⚡ rapidfuzz · fpdf2</span>
</div>
</div>
</div>
<div style="border-top:1px solid #374151;padding-top:14px;font-size:0.75rem;color:#6B7280;
    display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;">
<span>Open source · All processing local · No external API calls at runtime</span>
<span>"No known match found" ≠ allergen-free. Always read the original label.</span>
</div>
</div>
<div style="height:24px;"></div>
""")
