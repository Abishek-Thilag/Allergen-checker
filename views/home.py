"""
views/home.py — Landing / Home page.

All HTML goes through render_html() so no indentation-as-code-block issues.
"""
from __future__ import annotations
import sys
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from core.ui import (
    render_html,
    CHERRY, DARK_CHERRY, TINT, WHITE,
    TEXT_DARK, TEXT_BODY, TEXT_MUTED, BORDER_TINT,
)
from core.constants import DISCLAIMER_TEXT_SHORT


def show() -> None:
    # ── Hero ─────────────────────────────────────────────────────────────────
    render_html(f"""
<div class="fade-up hero" style="
    background:linear-gradient(135deg,{CHERRY} 0%,{DARK_CHERRY} 100%);
    border-radius:20px;padding:40px 44px 36px;margin-bottom:8px;
    box-shadow:0 8px 32px rgba(210,10,46,.22);
">
<div style="display:flex;align-items:center;gap:20px;flex-wrap:wrap;">
<span style="font-size:3.5rem;filter:drop-shadow(0 2px 4px rgba(0,0,0,.25))">🥛</span>
<div style="flex:1;min-width:260px;">
<div style="display:inline-flex;align-items:center;gap:8px;
    background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.35);
    border-radius:20px;padding:4px 14px;margin-bottom:14px;">
<span style="width:7px;height:7px;background:#fff;border-radius:50%;display:inline-block;"></span>
<span style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:600;
    font-size:0.78rem;color:#fff;letter-spacing:.04em;">Free · Local · Offline</span>
</div>
<h1 style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;
    font-size:2.4rem;line-height:1.15;color:#fff;margin:0 0 12px;
    text-shadow:0 1px 3px rgba(0,0,0,.2);">
Food Allergy<br>Ingredient Checker
</h1>
<p style="font-size:1rem;color:rgba(255,255,255,.88);line-height:1.7;
    margin:0 0 24px;max-width:500px;">
Spot allergens hidden as <strong style="color:#fff;">casein</strong>,
<strong style="color:#fff;">maida</strong>,
<strong style="color:#fff;">INS&nbsp;322</strong> and
<strong style="color:#fff;">groundnut</strong> on Indian food labels —
instantly, privately, on your device.
</p>
<div style="display:flex;gap:10px;flex-wrap:wrap;">
<a href="/Check" target="_self" style="text-decoration:none;">
<div style="background:#fff;color:{DARK_CHERRY};border-radius:12px;
    padding:11px 26px;font-family:'Plus Jakarta Sans',sans-serif;
    font-weight:800;font-size:0.95rem;cursor:pointer;
    box-shadow:0 4px 12px rgba(0,0,0,.15);display:inline-block;">
🔍 Check Ingredients
</div>
</a>
<a href="/About" target="_self" style="text-decoration:none;">
<div style="background:transparent;color:#fff;
    border:2px solid rgba(255,255,255,.6);border-radius:12px;
    padding:10px 22px;font-family:'Plus Jakarta Sans',sans-serif;
    font-weight:600;font-size:0.95rem;cursor:pointer;display:inline-block;">
ℹ️ Learn More
</div>
</a>
</div>
</div>
</div>
</div>
""")

    # ── Trust badges ─────────────────────────────────────────────────────────
    render_html(f"""
<div style="display:flex;gap:20px;flex-wrap:wrap;margin:12px 0 24px;padding:0 4px;">
<span style="display:flex;align-items:center;gap:6px;font-size:0.82rem;color:{TEXT_MUTED};">
<span style="color:#22C55E;font-size:1rem;">✓</span> 100% offline
</span>
<span style="display:flex;align-items:center;gap:6px;font-size:0.82rem;color:{TEXT_MUTED};">
<span style="color:#22C55E;font-size:1rem;">✓</span> No data leaves your device
</span>
<span style="display:flex;align-items:center;gap:6px;font-size:0.82rem;color:{TEXT_MUTED};">
<span style="color:#22C55E;font-size:1rem;">✓</span> 213 allergen synonyms
</span>
<span style="display:flex;align-items:center;gap:6px;font-size:0.82rem;color:{TEXT_MUTED};">
<span style="color:#22C55E;font-size:1rem;">✓</span> 25 INS codes decoded
</span>
</div>
""")

    # ── Stats strip ───────────────────────────────────────────────────────────
    render_html(f"""
<div style="background:linear-gradient(135deg,{CHERRY} 0%,{DARK_CHERRY} 100%);
    border-radius:16px;padding:24px 32px;margin:0 0 28px;
    box-shadow:0 6px 24px rgba(210,4,45,.22);">
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0;text-align:center;">
<div class="stat-card" style="border-right:1px solid rgba(255,255,255,.25);padding:0 16px;">
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;
    font-size:2rem;color:#fff;line-height:1;">10</div>
<div style="font-size:0.82rem;color:rgba(255,255,255,.82);margin-top:4px;">Allergen categories</div>
</div>
<div class="stat-card" style="border-right:1px solid rgba(255,255,255,.25);padding:0 16px;">
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;
    font-size:2rem;color:#fff;line-height:1;">213</div>
<div style="font-size:0.82rem;color:rgba(255,255,255,.82);margin-top:4px;">Synonyms &amp; Indian names</div>
</div>
<div class="stat-card" style="border-right:1px solid rgba(255,255,255,.25);padding:0 16px;">
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;
    font-size:2rem;color:#fff;line-height:1;">25</div>
<div style="font-size:0.82rem;color:rgba(255,255,255,.82);margin-top:4px;">INS / E-codes decoded</div>
</div>
<div class="stat-card" style="padding:0 16px;">
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;
    font-size:2rem;color:#fff;line-height:1;">10</div>
<div style="font-size:0.82rem;color:rgba(255,255,255,.82);margin-top:4px;">Sample labels included</div>
</div>
</div>
</div>
""")

    # ── Feature cards ─────────────────────────────────────────────────────────
    render_html(f"""
<div style="text-align:center;margin-bottom:20px;">
<h2 style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;
    font-size:1.55rem;color:{DARK_CHERRY};margin:0 0 8px;">
Everything you need to check a label
</h2>
<p style="color:{TEXT_MUTED};font-size:0.95rem;margin:0;">
Six features working together so nothing slips through.
</p>
</div>
""")

    FEATURES = [
        ("🔍", "Exact &amp; fuzzy matching",
         "Catches direct synonyms and OCR typos like <em>peanutt</em> or <em>casien</em>."),
        ("🇮🇳", "Indian name decoder",
         "Knows <em>maida</em>&thinsp;=&thinsp;wheat, <em>groundnut</em>&thinsp;=&thinsp;peanut, <em>ghee/dahi</em>&thinsp;=&thinsp;milk."),
        ("🏭", "INS / E-code lookup",
         "Decodes 25 additive codes. Variable-source codes are always flagged UNCERTAIN."),
        ("📷", "Label scan (OCR)",
         "Upload a photo. Tesseract extracts text into an editable box before you check."),
        ("👤", "Multiple profiles",
         "Separate allergen lists for every family member with mild/moderate/severe severity."),
        ("📄", "PDF reports",
         "Download a full report with results, explanations, and the disclaimer."),
    ]

    cols = st.columns(3, gap="medium")
    for i, (icon, title, desc) in enumerate(FEATURES):
        with cols[i % 3]:
            render_html(f"""
<div class="feat-card" style="
    background:{WHITE};border-radius:14px;padding:22px 20px 20px;
    border-left:5px solid {CHERRY};border-top:1px solid {BORDER_TINT};
    border-right:1px solid {BORDER_TINT};border-bottom:1px solid {BORDER_TINT};
    box-shadow:0 2px 8px rgba(210,4,45,.07);
    margin-bottom:16px;min-height:160px;
">
<div style="width:42px;height:42px;background:{TINT};
    border-radius:10px;display:flex;align-items:center;justify-content:center;
    font-size:1.3rem;margin-bottom:12px;">{icon}</div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;
    font-size:0.95rem;color:{DARK_CHERRY};margin-bottom:6px;">{title}</div>
<div style="font-size:0.83rem;color:{TEXT_MUTED};line-height:1.55;">{desc}</div>
</div>
""")

    # ── Get started strip ─────────────────────────────────────────────────────
    render_html(f"""
<div style="background:{WHITE};border-radius:16px;padding:28px 32px;
    border:1.5px solid {BORDER_TINT};box-shadow:0 2px 8px rgba(210,4,45,.06);
    margin:8px 0 28px;">
<h2 style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;
    font-size:1.2rem;color:{DARK_CHERRY};margin:0 0 20px;text-align:center;">
Get started in 3 steps
</h2>
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:24px;">
<div style="text-align:center;">
<div style="width:46px;height:46px;background:{CHERRY};
    border-radius:50%;display:flex;align-items:center;justify-content:center;
    font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:1.1rem;
    color:#fff;margin:0 auto 12px;">1</div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;
    font-size:0.9rem;color:{DARK_CHERRY};margin-bottom:5px;">Pick a profile</div>
<div style="font-size:0.8rem;color:{TEXT_MUTED};line-height:1.5;">
Use the Demo profile or create your own with the allergens to avoid.
</div>
</div>
<div style="text-align:center;position:relative;">
<div style="position:absolute;top:20px;left:-10px;font-size:1.2rem;color:{BORDER_TINT};">→</div>
<div style="width:46px;height:46px;background:{CHERRY};
    border-radius:50%;display:flex;align-items:center;justify-content:center;
    font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:1.1rem;
    color:#fff;margin:0 auto 12px;">2</div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;
    font-size:0.9rem;color:{DARK_CHERRY};margin-bottom:5px;">Paste or scan the label</div>
<div style="font-size:0.8rem;color:{TEXT_MUTED};line-height:1.5;">
Type, paste, upload a photo, or load one of 10 built-in sample labels.
</div>
</div>
<div style="text-align:center;position:relative;">
<div style="position:absolute;top:20px;left:-10px;font-size:1.2rem;color:{BORDER_TINT};">→</div>
<div style="width:46px;height:46px;background:{CHERRY};
    border-radius:50%;display:flex;align-items:center;justify-content:center;
    font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:1.1rem;
    color:#fff;margin:0 auto 12px;">3</div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;
    font-size:0.9rem;color:{DARK_CHERRY};margin-bottom:5px;">Read the results</div>
<div style="font-size:0.8rem;color:{TEXT_MUTED};line-height:1.5;">
See which allergens were found, why, and download a PDF report.
</div>
</div>
</div>
</div>
""")

    # ── Demo callout ──────────────────────────────────────────────────────────
    render_html(f"""
<div style="background:{TINT};border:1.5px solid {BORDER_TINT};
    border-radius:14px;padding:20px 28px;margin-bottom:28px;
    display:flex;align-items:center;justify-content:space-between;
    flex-wrap:wrap;gap:16px;">
<div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;
    font-size:1.0rem;color:{DARK_CHERRY};margin-bottom:6px;">
💡 Try The Demo Scenario
</div>
<div style="font-size:0.875rem;color:{TEXT_BODY};max-width:520px;line-height:1.6;">
Select the <strong>Demo</strong> profile → Check → Load Sample →
<em>Sample 04 Chocolate</em>. The label never says "milk" or "soy" but lists
<code style="background:{BORDER_TINT};padding:1px 5px;border-radius:4px;">casein</code>,
<code style="background:{BORDER_TINT};padding:1px 5px;border-radius:4px;">whey</code>,
and <code style="background:{BORDER_TINT};padding:1px 5px;border-radius:4px;">INS 322</code>.
Watch the app find them all.
</div>
</div>
<a href="/Check" target="_self" style="text-decoration:none;">
<div style="background:linear-gradient(135deg,{CHERRY},{DARK_CHERRY});color:#fff;
    border-radius:10px;padding:10px 22px;
    font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;
    font-size:0.9rem;white-space:nowrap;
    box-shadow:0 4px 12px rgba(210,4,45,.30);">
Try It Now →
</div>
</a>
</div>
""")

    # ── Footer ────────────────────────────────────────────────────────────────
    render_html(f"""
<div style="background:#1F2937;border-radius:16px;padding:28px 32px 20px;margin-top:8px;">
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
