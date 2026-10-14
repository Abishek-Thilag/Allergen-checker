"""
views/check.py — Check page.

All HTML rendered via render_html() to prevent indentation-as-code-block.
Cherry-red theme. Status colours kept distinct from brand red.
"""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List

import streamlit as st

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from core.constants import (
    DISCLAIMER_TEXT_SHORT,
    SEVERITY_MILD, SEVERITY_MODERATE, SEVERITY_SEVERE,
    STATUS_MAY_CONTAIN, STATUS_NO_MATCH, STATUS_PRESENT, STATUS_UNCERTAIN,
)
from core.db import (
    add_allergen_to_profile, create_profile, delete_profile,
    get_allergens_for_profile, get_profiles, remove_allergen_from_profile,
    save_history,
)
from core.matcher import MatchResult, match_allergens
from core.parser import parse_ingredients
from core.report import generate_pdf
from core.ui import (
    render_html,
    CHERRY, DARK_CHERRY, TINT, WHITE,
    TEXT_DARK, TEXT_BODY, TEXT_MUTED, BORDER_TINT,
    PRESENT_FG, PRESENT_BG, PRESENT_BORDER, PRESENT_ICON, PRESENT_LABEL,
    MAY_FG, MAY_BG, MAY_BORDER, MAY_ICON, MAY_LABEL,
    UNCERTAIN_FG, UNCERTAIN_BG, UNCERTAIN_BORDER, UNCERTAIN_ICON, UNCERTAIN_LABEL,
    NO_MATCH_FG, NO_MATCH_BG, NO_MATCH_BORDER, NO_MATCH_ICON, NO_MATCH_LABEL,
)

STANDARD_ALLERGENS = [
    "milk", "egg", "peanut", "tree nuts", "wheat",
    "soy", "fish", "shellfish", "sesame", "mustard",
]
SEVERITY_OPTIONS = [SEVERITY_MILD, SEVERITY_MODERATE, SEVERITY_SEVERE]
SAMPLES_DIR = ROOT / "data" / "samples"

# Status metadata using new distinct colours
_STATUS_META = {
    STATUS_PRESENT:     (PRESENT_BG,  PRESENT_BG,  PRESENT_BORDER,  PRESENT_ICON,  PRESENT_LABEL,  PRESENT_FG),
    STATUS_MAY_CONTAIN: (MAY_BG,      MAY_BG,      MAY_BORDER,      MAY_ICON,      MAY_LABEL,      MAY_FG),
    STATUS_UNCERTAIN:   (UNCERTAIN_BG,UNCERTAIN_BG,UNCERTAIN_BORDER,UNCERTAIN_ICON,UNCERTAIN_LABEL,UNCERTAIN_FG),
    STATUS_NO_MATCH:    (NO_MATCH_BG, NO_MATCH_BG, NO_MATCH_BORDER, NO_MATCH_ICON, NO_MATCH_LABEL, NO_MATCH_FG),
}

_SEVERITY_META = {
    SEVERITY_SEVERE:   (PRESENT_BG, "#FFE0E6", "🔴"),
    SEVERITY_MODERATE: (MAY_BG,     "#FFE8D6", "🟠"),
    SEVERITY_MILD:     (UNCERTAIN_BG,"#FFF8E0", "🟡"),
}


def _allergen_data():
    return st.session_state.get("allergen_data", {})

def _ins_data():
    return st.session_state.get("ins_data", {})


def _render_sidebar() -> None:
    pass


def _build_highlighted_html(text: str, results: List[MatchResult]) -> str:
    if not results or not text:
        return (
            f"<div style='font-family:\"SF Mono\",monospace;font-size:0.9rem;"
            f"white-space:pre-wrap;line-height:1.8;padding:16px;background:{TINT};"
            f"border-radius:10px;border:1px solid {BORDER_TINT};color:{TEXT_BODY};'>{text}</div>"
        )

    _COLOUR = {
        STATUS_PRESENT:     PRESENT_BG,
        STATUS_MAY_CONTAIN: MAY_BG,
        STATUS_UNCERTAIN:   UNCERTAIN_BG,
    }
    _TEXT = {
        STATUS_PRESENT:     PRESENT_FG,
        STATUS_MAY_CONTAIN: MAY_FG,
        STATUS_UNCERTAIN:   UNCERTAIN_FG,
    }
    _RANK = {STATUS_PRESENT: 3, STATUS_MAY_CONTAIN: 2, STATUS_UNCERTAIN: 1}

    lower_text = text.lower()
    char_colour: dict[int, str] = {}
    char_textcol: dict[int, str] = {}
    char_explanation: dict[int, str] = {}

    for result in results:
        colour = _COLOUR.get(result.status, "#ccc")
        tcol = _TEXT.get(result.status, "#000")
        for mt in result.matched_terms:
            term = mt.term.lower()
            start = 0
            while True:
                idx = lower_text.find(term, start)
                if idx == -1:
                    break
                for i in range(idx, idx + len(term)):
                    existing_rank = _RANK.get(
                        next((s for s, c in _COLOUR.items() if c == char_colour.get(i, "")), None), 0
                    )
                    if _RANK.get(result.status, 0) >= existing_rank:
                        char_colour[i] = colour
                        char_textcol[i] = tcol
                        char_explanation[i] = (
                            f"{result.allergen.upper()} ({result.status.replace('_',' ')}): {mt.explanation}"
                        )
                start = idx + 1

    parts = [
        f"<div style='font-family:\"SF Mono\",monospace;font-size:0.9rem;"
        f"white-space:pre-wrap;line-height:2;padding:16px 20px;background:{TINT};"
        f"border-radius:10px;border:1px solid {BORDER_TINT};color:{TEXT_BODY};'>"
    ]
    i = 0
    while i < len(text):
        if i in char_colour:
            colour = char_colour[i]
            tcol = char_textcol[i]
            tip = char_explanation.get(i, "").replace('"', "&quot;")
            j = i
            while j < len(text) and char_colour.get(j) == colour:
                j += 1
            parts.append(
                f'<mark style="background:{colour};color:{tcol};border-radius:5px;'
                f'padding:2px 5px;margin:0 1px;font-weight:700;" title="{tip}">{text[i:j]}</mark>'
            )
            i = j
        else:
            parts.append(text[i])
            i += 1
    parts.append("</div>")
    return "".join(parts)


def _summary_status(results: List[MatchResult]) -> str:
    if not results:
        return STATUS_NO_MATCH
    statuses = {r.status for r in results}
    if STATUS_PRESENT in statuses:
        return STATUS_PRESENT
    for r in results:
        if r.status == STATUS_MAY_CONTAIN and r.severity == SEVERITY_SEVERE:
            return STATUS_PRESENT
    if STATUS_MAY_CONTAIN in statuses:
        return STATUS_MAY_CONTAIN
    return STATUS_UNCERTAIN


def _render_banner(results: List[MatchResult]) -> None:
    status = _summary_status(results)
    present_count   = sum(1 for r in results if r.status == STATUS_PRESENT)
    may_count       = sum(1 for r in results if r.status == STATUS_MAY_CONTAIN)
    uncertain_count = sum(1 for r in results if r.status == STATUS_UNCERTAIN)

    if status == STATUS_NO_MATCH:
        icon, headline = NO_MATCH_ICON, NO_MATCH_LABEL
        sub = "None of the allergens in your profile were detected in this ingredient list."
        bg, border, fg = NO_MATCH_BG, NO_MATCH_BORDER, NO_MATCH_FG
        pills = ""
    else:
        parts = []
        if status == STATUS_PRESENT:
            icon, headline = PRESENT_ICON, "Allergen(s) Detected"
            sub = "At least one allergen from your profile was found in this ingredient list."
            bg, border, fg = "#FFF0F2", PRESENT_BORDER, PRESENT_BG
        elif status == STATUS_MAY_CONTAIN:
            icon, headline = MAY_ICON, "Trace Statement Found"
            sub = "Cross-contamination or trace allergen statements were found on this label."
            bg, border, fg = "#FFF7ED", MAY_BORDER, MAY_BG
        else:
            icon, headline = UNCERTAIN_ICON, "Uncertain Ingredient(s)"
            sub = "Vague ingredients or INS codes with multiple possible sources were found."
            bg, border, fg = "#FEFCE8", UNCERTAIN_BORDER, "#713F12"

        if present_count:
            parts.append(
                f"<span style='background:{PRESENT_BG};color:{PRESENT_FG};"
                f"border-radius:20px;padding:3px 12px;font-size:0.82rem;font-weight:700;"
                f"display:inline-block;'>"
                f"{PRESENT_ICON} {present_count} {PRESENT_LABEL}</span>"
            )
        if may_count:
            parts.append(
                f"<span style='background:{MAY_BG};color:{MAY_FG};"
                f"border-radius:20px;padding:3px 12px;font-size:0.82rem;font-weight:700;"
                f"display:inline-block;'>"
                f"{MAY_ICON} {may_count} {MAY_LABEL}</span>"
            )
        if uncertain_count:
            parts.append(
                f"<span style='background:{UNCERTAIN_BG};color:{UNCERTAIN_FG};"
                f"border-radius:20px;padding:3px 12px;font-size:0.82rem;font-weight:700;"
                f"display:inline-block;'>"
                f"{UNCERTAIN_ICON} {uncertain_count} {UNCERTAIN_LABEL}</span>"
            )
        pills = " &nbsp;".join(parts)

    render_html(f"""
<div class="fade-up" style="background:{bg};border:1.5px solid {border};
    border-radius:14px;padding:20px 24px;margin:8px 0 20px;">
<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
<span style="font-size:1.75rem;">{icon}</span>
<span style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;
    font-size:1.2rem;color:{fg};">{headline}</span>
</div>
<div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px;">{pills}</div>
<div style="font-size:0.875rem;color:{fg};opacity:.85;">{sub}</div>
<div style="margin-top:10px;padding-top:10px;border-top:1px solid {border};
    font-size:0.75rem;color:{TEXT_MUTED};">
⚠️ {DISCLAIMER_TEXT_SHORT}
</div>
</div>
""")


def _render_legend() -> None:
    render_html(f"""
<div style="display:flex;align-items:center;flex-wrap:wrap;gap:10px;
    padding:10px 14px;background:{WHITE};border-radius:8px;
    border:1px solid {BORDER_TINT};margin-bottom:12px;font-size:0.8rem;color:{TEXT_MUTED};">
<span style="font-weight:600;color:{TEXT_BODY};">Highlight key:</span>
<span style="background:{PRESENT_BG};color:{PRESENT_FG};border-radius:5px;
    padding:2px 10px;font-weight:700;font-size:0.78rem;">{PRESENT_ICON} {PRESENT_LABEL}</span>
<span style="background:{MAY_BG};color:{MAY_FG};border-radius:5px;
    padding:2px 10px;font-weight:700;font-size:0.78rem;">{MAY_ICON} {MAY_LABEL}</span>
<span style="background:{UNCERTAIN_BG};color:{UNCERTAIN_FG};border-radius:5px;
    padding:2px 10px;font-weight:700;font-size:0.78rem;">{UNCERTAIN_ICON} {UNCERTAIN_LABEL}</span>
<span style="font-style:italic;">Hover a highlight for the reason.</span>
</div>
""")


def _render_result_cards(results: List[MatchResult]) -> None:
    if not results:
        return

    MATCH_TYPE_LABEL = {
        "exact": ("🔵", "Exact match"),
        "fuzzy": ("🟣", "Fuzzy match"),
        "ins":   ("🟤", "INS / E-code"),
        "trace": ("🟠", "Trace statement"),
        "vague": ("🟡", "Vague ingredient"),
    }

    render_html(f"""
<h3 style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;
    color:{DARK_CHERRY};margin-bottom:16px;">🚨 Flagged Allergens</h3>
""")

    for result in results:
        status_bg, _, border, icon, label, fg = _STATUS_META.get(
            result.status, (TEXT_MUTED, "#F3F4F6", "#E5E7EB", "⚪", result.status, "#fff")
        )
        sev_fg, sev_bg, sev_dot = _SEVERITY_META.get(result.severity, (TEXT_MUTED, "#F3F4F6", "⚪"))
        allergen_info = _allergen_data().get(result.allergen, {})
        emoji = allergen_info.get("emoji", result.emoji)

        pill_bg = "rgba(0,0,0,.18)" if fg == "#FFFFFF" else "rgba(255,255,255,.45)"

        render_html(f"""
<div class="fade-up" style="background:{WHITE};border-radius:12px;
    border:1.5px solid {border};box-shadow:0 2px 10px rgba(210,10,46,.07);
    overflow:hidden;margin-bottom:12px;">
<div style="background:{status_bg};padding:14px 18px;
    display:flex;align-items:center;flex-wrap:wrap;gap:10px;
    border-bottom:1px solid {border};">
<span style="font-size:1.6rem;">{emoji}</span>
<span style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;
    font-size:1.05rem;color:{fg};">
{result.allergen.upper()}</span>
<span style="background:{pill_bg};color:{fg};border-radius:20px;
    padding:3px 13px;font-size:0.78rem;font-weight:700;
    font-family:'Plus Jakarta Sans',sans-serif;">
{icon} {label}</span>
<span style="background:{pill_bg};color:{fg};border-radius:6px;
    padding:2px 10px;font-size:0.75rem;font-weight:600;">
{sev_dot} {result.severity}</span>
</div>
</div>
""")
        with st.expander(
            f"❓ Why was {result.allergen} flagged? "
            f"({len(result.matched_terms)} reason{'s' if len(result.matched_terms) != 1 else ''})"
        ):
            for mt in result.matched_terms:
                dot2, lbl2 = MATCH_TYPE_LABEL.get(mt.match_type, ("⚪", mt.match_type))
                render_html(f"""
<div style="padding:10px 14px;background:{TINT};border-radius:8px;
    border-left:3px solid {CHERRY};margin-bottom:8px;">
<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
<code style="background:{BORDER_TINT};color:{DARK_CHERRY};
    padding:2px 8px;border-radius:5px;font-size:0.85rem;font-weight:600;">{mt.term}</code>
<span style="font-size:0.78rem;color:{TEXT_MUTED};">{dot2} {lbl2}</span>
</div>
<div style="font-size:0.875rem;color:{TEXT_BODY};font-style:italic;">{mt.explanation}</div>
{"<div style='font-size:0.75rem;color:" + TEXT_MUTED + ";margin-top:4px;'>Matched via synonym: <strong>" + mt.synonym + "</strong></div>" if mt.synonym and mt.synonym.lower() != mt.term.lower() else ""}
</div>
""")


def _render_side_intelligence(prof_name: str, profile_allergens_db: list) -> None:
    allergen_rows = []
    if profile_allergens_db:
        for a in profile_allergens_db:
            sev_fg, sev_bg, sev_dot = _SEVERITY_META.get(a.severity, (TEXT_MUTED, "#F3F4F6", "⚪"))
            info = _allergen_data().get(a.allergen, {})
            emoji = info.get("emoji", "⚠️")
            allergen_rows.append(f"""
<div style="background:{TINT};border:1px solid {BORDER_TINT};border-radius:10px;padding:8px 12px;
    display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
<div style="display:flex;align-items:center;gap:8px;">
<span style="font-size:1.1rem;">{emoji}</span>
<span style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;font-size:0.85rem;color:{DARK_CHERRY};">
{a.allergen.upper()}
</span>
</div>
<span style="background:{sev_fg};color:#fff;border-radius:12px;padding:2px 8px;font-size:0.72rem;font-weight:700;">
{sev_dot} {a.severity}
</span>
</div>
""")
    else:
        allergen_rows.append(f"""
<div style="background:{TINT};border:1px solid {BORDER_TINT};border-radius:10px;padding:12px;text-align:center;font-size:0.8rem;color:{DARK_CHERRY};">
No allergens active. Use sidebar to add allergens.
</div>
""")
    allergens_html = "".join(allergen_rows)

    render_html(f"""
<div style="background:{WHITE};border:1.5px solid {BORDER_TINT};border-radius:16px;
    padding:18px 20px;box-shadow:0 3px 12px rgba(210,10,46,.05);margin-bottom:14px;">
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;border-bottom:1px solid {BORDER_TINT};padding-bottom:10px;">
<div style="display:flex;align-items:center;gap:8px;">
<span style="font-size:1.2rem;">👤</span>
<span style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:0.95rem;color:{DARK_CHERRY};">
{prof_name}'s Watchlist
</span>
</div>
<span style="background:{TINT};color:{DARK_CHERRY};border-radius:12px;padding:2px 8px;font-size:0.75rem;font-weight:700;">
{len(profile_allergens_db)} Active
</span>
</div>
<div style="margin-bottom:8px;">{allergens_html}</div>
<div style="font-size:0.72rem;color:{TEXT_MUTED};text-align:right;">
💡 Add or edit allergens via the left sidebar
</div>
</div>

<div style="background:{WHITE};border:1.5px solid {BORDER_TINT};border-radius:16px;
    padding:18px 20px;box-shadow:0 3px 12px rgba(210,10,46,.05);margin-bottom:14px;">
<div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
<span style="font-size:1.2rem;">🚨</span>
<span style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:0.95rem;color:{DARK_CHERRY};">
Indian Food Risk Radar
</span>
</div>
<div style="display:flex;flex-direction:column;gap:8px;">
<div style="background:{TINT};border:1px solid {BORDER_TINT};border-radius:10px;padding:8px 12px;">
<div style="font-weight:700;font-size:0.82rem;color:{DARK_CHERRY};">🍫 Chocolates &amp; Sweets</div>
<div style="font-size:0.75rem;color:{TEXT_BODY};">Hides casein, whey, soy lecithin (INS 322).</div>
</div>
<div style="background:{TINT};border:1px solid {BORDER_TINT};border-radius:10px;padding:8px 12px;">
<div style="font-weight:700;font-size:0.82rem;color:{DARK_CHERRY};">🍪 Biscuits &amp; Bakery</div>
<div style="font-size:0.75rem;color:{TEXT_BODY};">Hides maida (wheat), skimmed milk, emulsifiers.</div>
</div>
<div style="background:{TINT};border:1px solid {BORDER_TINT};border-radius:10px;padding:8px 12px;">
<div style="font-weight:700;font-size:0.82rem;color:{DARK_CHERRY};">🍜 Instant Noodles</div>
<div style="font-size:0.75rem;color:{TEXT_BODY};">Hides wheat gluten, soy sauce, HVP protein.</div>
</div>
<div style="background:{TINT};border:1px solid {BORDER_TINT};border-radius:10px;padding:8px 12px;">
<div style="font-weight:700;font-size:0.82rem;color:{DARK_CHERRY};">🥨 Namkeens &amp; Fried Snacks</div>
<div style="font-size:0.75rem;color:{TEXT_BODY};">Hides groundnut oil, compounded hing (wheat), til.</div>
</div>
<div style="background:{TINT};border:1px solid {BORDER_TINT};border-radius:10px;padding:8px 12px;">
<div style="font-weight:700;font-size:0.82rem;color:{DARK_CHERRY};">🍨 Mithai &amp; Dairy Treats</div>
<div style="font-size:0.75rem;color:{TEXT_BODY};">Hides khoya, mawa, chhena, and ghee.</div>
</div>
</div>
</div>

<div style="background:{WHITE};border:1.5px solid {BORDER_TINT};border-radius:16px;
    padding:18px 20px;box-shadow:0 3px 12px rgba(210,10,46,.05);margin-bottom:14px;">
<div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
<span style="font-size:1.2rem;">🧪</span>
<span style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:0.95rem;color:{DARK_CHERRY};">
INS Additive Quick Codex
</span>
</div>
<div style="display:flex;flex-direction:column;gap:6px;font-size:0.78rem;">
<div style="display:flex;justify-content:space-between;align-items:center;padding:4px 0;border-bottom:1px solid {BORDER_TINT};">
<span><strong>INS 322</strong> Lecithin</span>
<span style="background:{MAY_BG};color:#fff;border-radius:6px;padding:1px 6px;font-size:0.7rem;font-weight:700;">Soy / Egg</span>
</div>
<div style="display:flex;justify-content:space-between;align-items:center;padding:4px 0;border-bottom:1px solid {BORDER_TINT};">
<span><strong>INS 471</strong> Mono/Diglycerides</span>
<span style="background:{UNCERTAIN_BG};color:{UNCERTAIN_FG};border-radius:6px;padding:1px 6px;font-size:0.7rem;font-weight:700;">Uncertain</span>
</div>
<div style="display:flex;justify-content:space-between;align-items:center;padding:4px 0;border-bottom:1px solid {BORDER_TINT};">
<span><strong>INS 150d</strong> Caramel IV</span>
<span style="background:{UNCERTAIN_BG};color:{UNCERTAIN_FG};border-radius:6px;padding:1px 6px;font-size:0.7rem;font-weight:700;">Wheat / Sulfite</span>
</div>
<div style="display:flex;justify-content:space-between;align-items:center;padding:4px 0;border-bottom:1px solid {BORDER_TINT};">
<span><strong>INS 621</strong> Monosodium Glutamate</span>
<span style="background:{UNCERTAIN_BG};color:{UNCERTAIN_FG};border-radius:6px;padding:1px 6px;font-size:0.7rem;font-weight:700;">Soy / Wheat</span>
</div>
<div style="display:flex;justify-content:space-between;align-items:center;padding:4px 0;">
<span><strong>INS 904</strong> Shellac Glaze</span>
<span style="background:{MAY_BG};color:#fff;border-radius:6px;padding:1px 6px;font-size:0.7rem;font-weight:700;">Insect</span>
</div>
</div>
</div>

<div style="background:linear-gradient(135deg,{CHERRY},{DARK_CHERRY});border-radius:16px;
    padding:16px 18px;color:#fff;box-shadow:0 6px 18px rgba(210,10,46,.25);">
<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
<span style="font-size:1.1rem;">🛡️</span>
<span style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:0.88rem;">
100% On-Device Guarantee
</span>
</div>
<div style="font-size:0.78rem;color:rgba(255,255,255,.9);line-height:1.5;">
Zero telemetry. All checks evaluate deterministically against 213 Indian synonym rules and 25 INS codes.
</div>
</div>
""")


def show() -> None:
    _render_sidebar()

    active_id = st.session_state.get("active_profile_id")
    prof_name = "Default"
    n_allergens = 0
    if active_id:
        try:
            profiles = get_profiles()
            active_prof = next((p for p in profiles if p.id == active_id), None)
            if active_prof:
                prof_name = active_prof.name
            profile_allergens_db = get_allergens_for_profile(active_id)
            n_allergens = len(profile_allergens_db)
        except Exception:
            profile_allergens_db = []
    else:
        profile_allergens_db = []

    render_html(f"""
<div style="background:{WHITE};border:1.5px solid {BORDER_TINT};border-radius:18px;
    padding:18px 24px;margin-bottom:18px;box-shadow:0 3px 12px rgba(210,10,46,.05);
    display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:14px;">
<div>
<div style="display:inline-flex;align-items:center;gap:6px;background:{TINT};border:1px solid {BORDER_TINT};
    border-radius:12px;padding:3px 10px;margin-bottom:4px;">
<span style="font-size:0.8rem;">🔍</span>
<span style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;font-size:0.75rem;
    color:{DARK_CHERRY};letter-spacing:.04em;text-transform:uppercase;">Ingredient Scanner</span>
</div>
<h1 style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:1.6rem;color:{DARK_CHERRY};margin:0;">
Audit Food Label Ingredients
</h1>
<div style="font-size:0.84rem;color:{TEXT_MUTED};margin-top:2px;">
Paste an ingredient panel, upload a photo, or click any quick sample preset below.
</div>
</div>
<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
<div style="background:{TINT};border:1px solid {BORDER_TINT};border-radius:14px;padding:8px 16px;
    display:flex;align-items:center;gap:10px;">
<span style="font-size:1.4rem;">👤</span>
<div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:0.88rem;color:{DARK_CHERRY};">
Profile: {prof_name}
</div>
<div style="font-size:0.74rem;color:{TEXT_MUTED};">
Tracking {n_allergens} allergen{'s' if n_allergens != 1 else ''}
</div>
</div>
</div>
</div>
</div>
""")

    if not active_id:
        render_html(f"""
<div style="background:{TINT};border:1.5px solid {BORDER_TINT};
    border-radius:12px;padding:16px 20px;color:{DARK_CHERRY};font-weight:500;">
👈 Create a profile and add allergens in the sidebar to get started.
</div>
""")
        return

    if not profile_allergens_db:
        render_html(f"""
<div style="background:{TINT};border:1.5px solid {BORDER_TINT};
    border-radius:12px;padding:14px 18px;color:{DARK_CHERRY};">
⚠️ No allergens in this profile — add some in the sidebar first.
</div>
""")

    # ── Two-Column Layout ─────────────────────────────────────────────────────
    col_main, col_intel = st.columns([62, 38], gap="large")

    with col_main:
        # ── Input tabs ────────────────────────────────────────────────────────
        tab_manual, tab_scan, tab_sample = st.tabs(["✏️ Manual / Paste", "📷 Scan Label", "📦 Load Sample"])
        ingredient_text = st.session_state.get("reopen_text", "")

        with tab_manual:
            render_html(f"""
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;flex-wrap:wrap;gap:8px;">
<div style="display:flex;align-items:center;gap:6px;">
<span style="font-size:0.85rem;">⚡</span>
<span style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;font-size:0.8rem;color:{DARK_CHERRY};">
Quick Sample Presets:
</span>
<span style="font-size:0.75rem;color:{TEXT_MUTED};">(Click to pre-fill)</span>
</div>
</div>
""")
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            if col_s1.button("🍫 Chocolate", key="chip_choc", use_container_width=True):
                p = SAMPLES_DIR / "sample_04_chocolate.txt"
                if p.exists():
                    st.session_state["manual_text"] = p.read_text(encoding="utf-8")
                    st.rerun()
            if col_s2.button("🍪 Biscuit", key="chip_bisc", use_container_width=True):
                p = SAMPLES_DIR / "sample_01_biscuit.txt"
                if p.exists():
                    st.session_state["manual_text"] = p.read_text(encoding="utf-8")
                    st.rerun()
            if col_s3.button("🍜 Noodles", key="chip_nood", use_container_width=True):
                p = SAMPLES_DIR / "sample_03_instant_noodles.txt"
                if p.exists():
                    st.session_state["manual_text"] = p.read_text(encoding="utf-8")
                    st.rerun()
            if col_s4.button("🥜 Namkeen", key="chip_namk", use_container_width=True):
                p = SAMPLES_DIR / "sample_02_namkeen.txt"
                if p.exists():
                    st.session_state["manual_text"] = p.read_text(encoding="utf-8")
                    st.rerun()

            ingredient_text = st.text_area(
                "Paste or type the ingredient list",
                value=ingredient_text,
                height=150,
                placeholder="e.g. Sugar, cocoa butter, casein, whey, emulsifier (INS 322), natural flavours",
                key="manual_text",
            )
            if st.session_state.get("reopen_text"):
                st.session_state["reopen_text"] = ""

        with tab_scan:
            render_html(f"""
<div style="background:{TINT};border:1px solid {BORDER_TINT};
    border-radius:10px;padding:12px 16px;margin-bottom:14px;
    display:flex;align-items:flex-start;gap:12px;">
<span style="font-size:1.4rem;flex-shrink:0;">📷</span>
<div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;
    font-size:0.875rem;color:{DARK_CHERRY};margin-bottom:4px;">
How To Get The Best OCR Result
</div>
<div style="font-size:0.82rem;color:{TEXT_BODY};line-height:1.6;opacity:.85;">
Take a flat, well-lit photo of the ingredient panel only.
Avoid glare, shadows, and curved surfaces.
Review extracted text before clicking Check.
</div>
</div>
</div>
""")
            uploaded = st.file_uploader(
                "Upload a food label photo (JPG or PNG, max 10 MB)",
                type=["jpg", "jpeg", "png"],
                key="scan_upload",
            )
            if uploaded is not None:
                from core.constants import MAX_IMAGE_BYTES
                file_bytes = uploaded.read()
                if len(file_bytes) > MAX_IMAGE_BYTES:
                    st.error("Image too large. Maximum size is 10 MB.")
                else:
                    col_img, col_txt = st.columns([1, 1])
                    with col_img:
                        st.image(file_bytes, caption="Uploaded label", use_container_width=True)
                    with col_txt:
                        with st.spinner("🔎 Extracting text with OCR…"):
                            from core.ocr import extract_text_from_image
                            ocr_result = extract_text_from_image(file_bytes)
                        if ocr_result.error:
                            if "tesseract" in ocr_result.error.lower():
                                st.warning(f"OCR unavailable: {ocr_result.error}\n\nType ingredients in the Manual tab.")
                            else:
                                st.error(ocr_result.error)
                        elif not ocr_result.text.strip():
                            st.warning("OCR found no text. Please type the ingredients manually.")
                        else:
                            if ocr_result.confidence is not None:
                                render_html(f"""
<div style="font-size:0.8rem;color:{TEXT_MUTED};margin-bottom:6px;">
OCR confidence: <strong style="color:{CHERRY};">{ocr_result.confidence:.0f}%</strong>
</div>
""")
                            ingredient_text = st.text_area(
                                "Extracted text (edit to fix OCR errors)",
                                value=ocr_result.text,
                                height=150,
                                key="ocr_text",
                            )

        with tab_sample:
            sample_files = sorted(SAMPLES_DIR.glob("*.txt")) if SAMPLES_DIR.exists() else []
            if not sample_files:
                st.warning("No sample files found in data/samples/.")
            else:
                sample_options = {f.stem.replace("_", " ").title(): f for f in sample_files}
                render_html(f"""
<div style="background:{TINT};border:1px solid {BORDER_TINT};
    border-radius:10px;padding:12px 16px;margin-bottom:12px;font-size:0.875rem;
    color:{DARK_CHERRY};">
<strong>💡 Demo Scenario:</strong> Load <em>Sample 04 Chocolate</em> with the Demo
profile (milk: severe, soy: moderate) to see casein, whey, and INS 322 flagged.
</div>
""")
                chosen = st.selectbox("Choose a sample label", list(sample_options.keys()), key="sample_choice")
                if st.button("📦 Load This Sample", key="btn_load_sample", type="primary"):
                    try:
                        sample_text = sample_options[chosen].read_text(encoding="utf-8")
                        st.session_state["manual_text"] = sample_text
                        st.success(f'Loaded "{chosen}" — switch to Manual tab, then click Check.')
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Could not load sample: {exc}")

        # ── Check button ──────────────────────────────────────────────────────
        text_to_check = st.session_state.get("manual_text", ingredient_text) or ingredient_text
        col_btn, col_hint = st.columns([2, 3])
        with col_btn:
            run_check = st.button("🔍 Check Ingredients", type="primary", key="btn_check", use_container_width=True)
        with col_hint:
            if profile_allergens_db:
                allergen_names = [a.allergen for a in profile_allergens_db]
                pills = " ".join([
                    f"<span style='background:{TINT};color:{DARK_CHERRY};"
                    f"border-radius:4px;padding:2px 8px;font-weight:600;font-size:0.75rem;'>{n}</span>"
                    for n in allergen_names
                ])
                render_html(f"""
<div style="padding-top:6px;font-size:0.8rem;color:{TEXT_MUTED};">
Checking vs: {pills}
</div>
""")

        if run_check:
            if not text_to_check.strip():
                st.error("Please enter an ingredient list before checking.")
            elif not profile_allergens_db:
                st.error("Add at least one allergen to your profile first.")
            else:
                with st.spinner("🧪 Matching allergens…"):
                    try:
                        from core.matcher import AllergenEntry as MatchAllergenEntry
                        profile_entries = [
                            MatchAllergenEntry(name=a.allergen, severity=a.severity)
                            for a in profile_allergens_db
                        ]
                        parse_result = parse_ingredients(text_to_check)
                        results = match_allergens(
                            parse_result, profile_entries,
                            st.session_state.get("allergen_data", {}),
                            st.session_state.get("ins_data", {}),
                        )
                        st.session_state["last_results"] = results
                        st.session_state["last_ingredient_text"] = text_to_check
                        summary = _summary_status(results)
                        try:
                            results_json = json.dumps([
                                {"allergen": r.allergen, "severity": r.severity, "status": r.status,
                                 "emoji": r.emoji, "matched_terms": [
                                     {"term": mt.term, "explanation": mt.explanation,
                                      "match_type": mt.match_type, "synonym": mt.synonym}
                                     for mt in r.matched_terms
                                 ]} for r in results
                            ])
                            save_history(
                                profile_id=active_id,
                                ingredient_text=text_to_check,
                                results_json=results_json,
                                summary_status=summary,
                            )
                        except Exception as exc:
                            import sys as _sys
                            print(f"[warn] Could not save history: {exc}", file=_sys.stderr)
                    except ValueError as exc:
                        st.error(str(exc))
                    except Exception as exc:
                        st.error(f"An error occurred during matching: {exc}")
                        import traceback; traceback.print_exc()

        # ── Results Area in Main Column ───────────────────────────────────────
        results = st.session_state.get("last_results")
        last_text = st.session_state.get("last_ingredient_text", "")

        if results is None or not last_text:
            render_html(f"""
<div class="fade-up" style="background:{WHITE};border:1.5px solid {BORDER_TINT};
    border-radius:18px;padding:24px 26px;margin-top:16px;box-shadow:0 4px 16px rgba(210,10,46,.05);">
<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:18px;border-bottom:1px solid {BORDER_TINT};padding-bottom:14px;">
<div>
<div style="display:inline-flex;align-items:center;gap:6px;background:{TINT};border:1px solid {BORDER_TINT};border-radius:12px;padding:3px 10px;margin-bottom:4px;">
<span style="font-size:0.8rem;">🎯</span>
<span style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;font-size:0.75rem;color:{DARK_CHERRY};letter-spacing:.04em;text-transform:uppercase;">Inspection Engine Ready</span>
</div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:1.25rem;color:{DARK_CHERRY};">
Ready to Analyze Ingredients
</div>
<div style="font-size:0.84rem;color:{TEXT_MUTED};margin-top:2px;">
Paste ingredients above or pick a quick preset, then click <strong>Check Ingredients</strong>.
</div>
</div>
</div>

<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:18px;">
<div style="background:{TINT};border:1px solid {BORDER_TINT};border-radius:12px;padding:14px 12px;">
<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
<span style="font-size:1.2rem;">🔍</span>
<span style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:0.85rem;color:{DARK_CHERRY};">Fuzzy Matching</span>
</div>
<div style="font-size:0.78rem;color:{TEXT_BODY};line-height:1.5;">
Catches typos (e.g. <em>peanutt</em>, <em>casien</em>).
</div>
</div>

<div style="background:{TINT};border:1px solid {BORDER_TINT};border-radius:12px;padding:14px 12px;">
<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
<span style="font-size:1.2rem;">🇮🇳</span>
<span style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:0.85rem;color:{DARK_CHERRY};">Indian Decoder</span>
</div>
<div style="font-size:0.78rem;color:{TEXT_BODY};line-height:1.5;">
Translates <em>maida</em>, <em>groundnut</em>, <em>ghee</em>.
</div>
</div>

<div style="background:{TINT};border:1px solid {BORDER_TINT};border-radius:12px;padding:14px 12px;">
<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
<span style="font-size:1.2rem;">🧪</span>
<span style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:0.85rem;color:{DARK_CHERRY};">INS Codex</span>
</div>
<div style="font-size:0.78rem;color:{TEXT_BODY};line-height:1.5;">
Decodes 25 food additive codes.
</div>
</div>
</div>

<div style="background:#fff;border:1px solid {BORDER_TINT};border-radius:12px;padding:14px 16px;">
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;font-size:0.75rem;color:{DARK_CHERRY};margin-bottom:8px;text-transform:uppercase;letter-spacing:.04em;">
Status Classification Guide
</div>
<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
<span style="background:{PRESENT_BG};color:{PRESENT_FG};border-radius:20px;padding:3px 10px;font-size:0.74rem;font-weight:700;">{PRESENT_ICON} {PRESENT_LABEL}</span>
<span style="background:{MAY_BG};color:{MAY_FG};border-radius:20px;padding:3px 10px;font-size:0.74rem;font-weight:700;">{MAY_ICON} {MAY_LABEL}</span>
<span style="background:{UNCERTAIN_BG};color:{UNCERTAIN_FG};border-radius:20px;padding:3px 10px;font-size:0.74rem;font-weight:700;">{UNCERTAIN_ICON} {UNCERTAIN_LABEL}</span>
<span style="background:{NO_MATCH_BG};color:{NO_MATCH_FG};border:1px solid {NO_MATCH_BORDER};border-radius:20px;padding:2px 10px;font-size:0.74rem;font-weight:700;">{NO_MATCH_ICON} {NO_MATCH_LABEL}</span>
</div>
</div>
</div>
""")
        else:
            _render_banner(results)
            if results:
                render_html(f"""
<h3 style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;
    color:{DARK_CHERRY};margin-bottom:4px;">📋 Highlighted Ingredient List</h3>
""")
                _render_legend()
                st.markdown(_build_highlighted_html(last_text, results), unsafe_allow_html=True)
                st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
                _render_result_cards(results)
            else:
                render_html(f"""
<div style="background:{NO_MATCH_BG};border:1.5px solid {NO_MATCH_BORDER};
    border-radius:12px;padding:16px 20px;margin:8px 0;">
<div style="font-weight:700;color:{NO_MATCH_FG};margin-bottom:6px;">
{NO_MATCH_ICON} {NO_MATCH_LABEL}
</div>
<div style="font-family:monospace;font-size:0.875rem;color:{TEXT_BODY};
    white-space:pre-wrap;">{last_text}</div>
</div>
""")

            # ── PDF download ──────────────────────────────────────────────────
            st.divider()
            try:
                profiles = get_profiles()
                active_profile = next((p for p in profiles if p.id == active_id), None)
                profile_name = active_profile.name if active_profile else "Unknown"
            except Exception:
                profile_name = "Unknown"
            col_dl, col_note = st.columns([1, 1])
            try:
                pdf_bytes = generate_pdf(
                    profile_name=profile_name,
                    timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                    ingredient_text=last_text,
                    match_results=results,
                    summary_status=_summary_status(results),
                )
                with col_dl:
                    st.download_button(
                        label="📄 Download PDF Report",
                        data=pdf_bytes,
                        file_name="allergy_check_report.pdf",
                        mime="application/pdf",
                        key="pdf_download",
                        use_container_width=True,
                    )
                with col_note:
                    render_html(f"""
<div style="padding-top:8px;font-size:0.8rem;color:{TEXT_MUTED};">
Includes full results, explanations, and medical disclaimer.
</div>
""")
            except Exception as exc:
                st.warning(f"PDF generation failed: {exc}")

    with col_intel:
        _render_side_intelligence(prof_name, profile_allergens_db)

    # ── Full-Width Tips & Safety Strip ────────────────────────────────────────
    render_html(f"""
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:24px 0 12px;">
<div style="background:{WHITE};border:1px solid {BORDER_TINT};border-radius:12px;
    padding:14px 16px;display:flex;align-items:flex-start;gap:10px;box-shadow:0 2px 8px rgba(210,10,46,.04);">
<span style="font-size:1.3rem;flex-shrink:0;">💡</span>
<div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;
    font-size:0.82rem;color:{DARK_CHERRY};margin-bottom:2px;">Try a sample first</div>
<div style="font-size:0.75rem;color:{TEXT_MUTED};line-height:1.45;">
Load <em>Sample 04 Chocolate</em> above to see casein, whey, and INS 322 flagged in seconds.
</div>
</div>
</div>
<div style="background:{WHITE};border:1px solid {BORDER_TINT};border-radius:12px;
    padding:14px 16px;display:flex;align-items:flex-start;gap:10px;box-shadow:0 2px 8px rgba(210,10,46,.04);">
<span style="font-size:1.3rem;flex-shrink:0;">🧐</span>
<div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;
    font-size:0.82rem;color:{DARK_CHERRY};margin-bottom:2px;">Include the whole panel</div>
<div style="font-size:0.75rem;color:{TEXT_MUTED};line-height:1.45;">
Paste numbers and parentheses too — additives like INS 322 and INS 471 are audited.
</div>
</div>
</div>
<div style="background:{WHITE};border:1px solid {BORDER_TINT};border-radius:12px;
    padding:14px 16px;display:flex;align-items:flex-start;gap:10px;box-shadow:0 2px 8px rgba(210,10,46,.04);">
<span style="font-size:1.3rem;flex-shrink:0;">⚠️</span>
<div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;
    font-size:0.82rem;color:{DARK_CHERRY};margin-bottom:2px;">Always verify original label</div>
<div style="font-size:0.75rem;color:{TEXT_MUTED};line-height:1.45;">
This software is an informational aid, not medical advice. Check physical packaging.
</div>
</div>
</div>
</div>
""")

    # ── Page footer ───────────────────────────────────────────────────────────
    render_html(f"""
<div style="background:#1F2937;border-radius:14px;padding:20px 28px;
    margin-top:20px;display:flex;justify-content:space-between;
    align-items:center;flex-wrap:wrap;gap:12px;">
<div style="font-size:0.8rem;color:#9CA3AF;">
🥛 <strong style="color:#fff;">Food Allergy Ingredient Checker</strong> ·
All processing is local · No data sent anywhere
</div>
<div style="font-size:0.75rem;color:#6B7280;">
⚠️ "No known match found" ≠ allergen-free. Always read the original label.
</div>
</div>
<div style="height:16px;"></div>
""")
