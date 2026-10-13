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


def _render_sidebar():
    render_html(f"""
<div style="background:linear-gradient(135deg,{CHERRY},{DARK_CHERRY});
    border-radius:10px;padding:14px 16px;margin-bottom:16px;">
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;
    font-size:1rem;color:#fff;">👤 Profile Manager</div>
<div style="font-size:0.78rem;color:rgba(255,255,255,.82);margin-top:2px;">
Manage your allergen profiles
</div>
</div>
""")

    try:
        profiles = get_profiles()
    except Exception as exc:
        st.sidebar.error(f"Could not load profiles: {exc}")
        return

    if not profiles:
        render_html(f"""
<div style="background:{TINT};border-radius:8px;padding:10px 12px;
    font-size:0.85rem;color:{DARK_CHERRY};border:1px solid {BORDER_TINT};">
No profiles yet — create one below ↓
</div>
""")
    else:
        profile_names = [p.name for p in profiles]
        active_id = st.session_state.get("active_profile_id")
        current_idx = next((i for i, p in enumerate(profiles) if p.id == active_id), 0)
        selected_name = st.sidebar.selectbox(
            "Active Profile", profile_names, index=current_idx, key="profile_selector"
        )
        selected_profile = next(p for p in profiles if p.name == selected_name)
        st.session_state["active_profile_id"] = selected_profile.id
        render_html(f"""
<div style="background:{TINT};border-radius:8px;padding:8px 12px;
    font-weight:600;font-size:0.875rem;color:{DARK_CHERRY};
    border:1px solid {BORDER_TINT};margin-bottom:4px;">
✅ {selected_name}
</div>
""")

    with st.sidebar.expander("➕ New Profile"):
        new_name = st.text_input("Name", key="new_profile_name", placeholder="e.g. Mom, Kid")
        if st.button("Create Profile", key="btn_create_profile", type="primary"):
            if not new_name.strip():
                st.error("Name cannot be empty.")
            else:
                try:
                    new_id = create_profile(new_name.strip())
                    st.session_state["active_profile_id"] = new_id
                    st.success(f'Profile "{new_name}" created.')
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
                except Exception as exc:
                    st.error(f"Error: {exc}")

    active_id = st.session_state.get("active_profile_id")
    if active_id and profiles:
        with st.sidebar.expander("🗑️ Delete Profile"):
            active_profile = next((p for p in profiles if p.id == active_id), None)
            if active_profile:
                st.warning(f'Delete **"{active_profile.name}"** and all its history?')
                if st.button("Confirm Delete", key="btn_delete_profile"):
                    try:
                        delete_profile(active_id)
                        st.session_state["active_profile_id"] = None
                        st.success("Profile deleted.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Error: {exc}")

    st.sidebar.markdown(f"<hr style='border-top:1px solid {BORDER_TINT};margin:12px 0'>", unsafe_allow_html=True)

    active_id = st.session_state.get("active_profile_id")
    if not active_id:
        st.sidebar.info("Select or create a profile to manage allergens.")
        return

    render_html(f"""
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;
    font-size:0.8rem;color:{TEXT_MUTED};text-transform:uppercase;
    letter-spacing:.07em;margin-bottom:8px;">🚨 Allergens To Watch</div>
""")

    try:
        current_allergens = get_allergens_for_profile(active_id)
    except Exception as exc:
        st.sidebar.error(f"Could not load allergens: {exc}")
        return

    if not current_allergens:
        render_html(f"""<div style="font-size:0.82rem;color:{TEXT_MUTED};padding:4px 0;">
No allergens yet — add one below ↓</div>""")
    else:
        for a in current_allergens:
            fg, bg, dot = _SEVERITY_META.get(a.severity, (TEXT_MUTED, "#F3F4F6", "⚪"))
            allergen_info = _allergen_data().get(a.allergen, {})
            emoji = allergen_info.get("emoji", "⚠️")
            col1, col2 = st.sidebar.columns([5, 1])
            col1.markdown(
                f"<div style='display:flex;align-items:center;gap:6px;padding:5px 0;"
                f"border-bottom:1px solid {BORDER_TINT};'>"
                f"<span style='font-size:1.1rem;'>{emoji}</span>"
                f"<span style='font-weight:600;font-size:0.875rem;color:{TEXT_DARK};'>{a.allergen}</span>"
                f"<span style='background:{bg};color:{fg};border-radius:6px;"
                f"padding:1px 7px;font-size:0.7rem;font-weight:600;'>{dot} {a.severity}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
            if col2.button("✕", key=f"remove_{a.allergen}", help=f"Remove {a.allergen}"):
                try:
                    remove_allergen_from_profile(active_id, a.allergen)
                    st.rerun()
                except Exception as exc:
                    st.sidebar.error(str(exc))

    with st.sidebar.expander("➕ Add Allergen"):
        existing_names = {a.allergen for a in current_allergens}
        available_standard = [a for a in STANDARD_ALLERGENS if a not in existing_names]
        add_type = st.radio("Type", ["Standard", "Custom"], key="add_type", horizontal=True)
        if add_type == "Standard":
            allergen_choice = (
                st.selectbox("Allergen", available_standard, key="std_allergen_choice")
                if available_standard else None
            )
            if not available_standard:
                st.caption("All standard allergens already added.")
        else:
            allergen_choice = st.text_input("Custom name", key="custom_allergen", placeholder="e.g. lupin")
        severity_choice = st.select_slider("Severity", SEVERITY_OPTIONS, value=SEVERITY_MODERATE, key="sev_choice")
        if st.button("Add Allergen", key="btn_add_allergen", type="primary"):
            if not allergen_choice or not str(allergen_choice).strip():
                st.error("Please enter an allergen name.")
            else:
                try:
                    add_allergen_to_profile(active_id, str(allergen_choice).strip(), severity_choice)
                    st.success(f"Added: {allergen_choice}")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

    st.sidebar.markdown(f"<hr style='border-top:1px solid {BORDER_TINT};margin:12px 0'>", unsafe_allow_html=True)

    # Tips card
    render_html(f"""
<div style="background:{TINT};border:1px solid {BORDER_TINT};
    border-radius:10px;padding:14px 14px 10px;margin-bottom:12px;">
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;
    font-size:0.8rem;color:{DARK_CHERRY};margin-bottom:8px;">💡 Quick Tips</div>
<div style="display:flex;flex-direction:column;gap:6px;">
<div style="font-size:0.75rem;color:{TEXT_BODY};display:flex;gap:6px;align-items:flex-start;">
<span style="flex-shrink:0;">🍼</span>
<span>Milk hides as <strong>casein, whey, dahi, ghee, paneer</strong></span>
</div>
<div style="font-size:0.75rem;color:{TEXT_BODY};display:flex;gap:6px;align-items:flex-start;">
<span style="flex-shrink:0;">🌾</span>
<span>Wheat hides as <strong>maida, atta, suji, rava, gluten</strong></span>
</div>
<div style="font-size:0.75rem;color:{TEXT_BODY};display:flex;gap:6px;align-items:flex-start;">
<span style="flex-shrink:0;">🥜</span>
<span>Peanut hides as <strong>groundnut, arachis oil</strong></span>
</div>
<div style="font-size:0.75rem;color:{TEXT_BODY};display:flex;gap:6px;align-items:flex-start;">
<span style="flex-shrink:0;">🏭</span>
<span><strong>INS 322</strong> = lecithin, may be soy or egg</span>
</div>
</div>
</div>
""")

    render_html(f"""
<div style="background:{TINT};border:1px solid {BORDER_TINT};border-radius:8px;
    padding:10px 12px;font-size:0.75rem;color:{TEXT_MUTED};line-height:1.5;">
⚠️ {DISCLAIMER_TEXT_SHORT}
</div>
""")


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
            bg, border, fg = "#FFF0F0", PRESENT_BORDER, PRESENT_BG
        elif status == STATUS_MAY_CONTAIN:
            icon, headline = MAY_ICON, "Trace Statement Found"
            sub = "Cross-contamination or trace allergen statements were found on this label."
            bg, border, fg = "#FFF5EE", MAY_BORDER, MAY_BG
        else:
            icon, headline = UNCERTAIN_ICON, "Uncertain Ingredient(s)"
            sub = "Vague ingredients or INS codes with multiple possible sources were found."
            bg, border, fg = "#FFFDE7", UNCERTAIN_BORDER, UNCERTAIN_BG

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

        render_html(f"""
<div class="fade-up" style="background:{WHITE};border-radius:12px;
    border:1.5px solid {border};box-shadow:0 2px 10px rgba(210,4,45,.07);
    overflow:hidden;margin-bottom:12px;">
<div style="background:{status_bg};padding:14px 18px;
    display:flex;align-items:center;flex-wrap:wrap;gap:10px;
    border-bottom:1px solid {border};">
<span style="font-size:1.6rem;">{emoji}</span>
<span style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;
    font-size:1.05rem;color:{WHITE if status_bg not in (WHITE, NO_MATCH_BG) else TEXT_DARK};">
{result.allergen.upper()}</span>
<span style="background:rgba(0,0,0,.20);color:{fg};border-radius:20px;
    padding:3px 13px;font-size:0.78rem;font-weight:700;
    font-family:'Plus Jakarta Sans',sans-serif;">
{icon} {label}</span>
<span style="background:rgba(0,0,0,.12);color:{fg};border-radius:6px;
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


def show() -> None:
    _render_sidebar()

    render_html(f"""
<div style="margin-bottom:20px;">
<h1 style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;
    font-size:1.6rem;color:{DARK_CHERRY};margin:0;">🔍 Check Ingredients</h1>
<p style="color:{TEXT_MUTED};margin:4px 0 0;font-size:0.9rem;">
Paste an ingredient list, scan a label, or load a sample — then click Check.
</p>
</div>
""")

    active_id = st.session_state.get("active_profile_id")
    if not active_id:
        render_html(f"""
<div style="background:{TINT};border:1.5px solid {BORDER_TINT};
    border-radius:12px;padding:16px 20px;color:{DARK_CHERRY};font-weight:500;">
👈 Create a profile and add allergens in the sidebar to get started.
</div>
""")
        return

    try:
        profile_allergens_db = get_allergens_for_profile(active_id)
    except Exception as exc:
        st.error(f"Could not load allergens: {exc}")
        return

    if not profile_allergens_db:
        render_html(f"""
<div style="background:#FFF8E0;border:1.5px solid #FDE68A;
    border-radius:12px;padding:14px 18px;color:#92400E;">
⚠️ No allergens in this profile — add some in the sidebar first.
</div>
""")

    # ── Input tabs ────────────────────────────────────────────────────────────
    tab_manual, tab_scan, tab_sample = st.tabs(["✏️ Manual / Paste", "📷 Scan Label", "📦 Load Sample"])
    ingredient_text = st.session_state.get("reopen_text", "")

    with tab_manual:
        ingredient_text = st.text_area(
            "Paste or type the ingredient list",
            value=ingredient_text,
            height=180,
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
After upload, review and correct the extracted text before clicking Check.
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

    # ── Tips strip ────────────────────────────────────────────────────────────
    render_html(f"""
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:16px 0 4px;">
<div style="background:{WHITE};border:1px solid {BORDER_TINT};border-radius:10px;
    padding:12px 14px;display:flex;align-items:flex-start;gap:10px;">
<span style="font-size:1.2rem;flex-shrink:0;">💡</span>
<div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;
    font-size:0.8rem;color:{DARK_CHERRY};margin-bottom:2px;">Try a sample first</div>
<div style="font-size:0.75rem;color:{TEXT_MUTED};line-height:1.4;">
Load <em>Sample 04 Chocolate</em> to see the app in action.
</div>
</div>
</div>
<div style="background:{WHITE};border:1px solid {BORDER_TINT};border-radius:10px;
    padding:12px 14px;display:flex;align-items:flex-start;gap:10px;">
<span style="font-size:1.2rem;flex-shrink:0;">🧐</span>
<div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;
    font-size:0.8rem;color:{DARK_CHERRY};margin-bottom:2px;">Include everything</div>
<div style="font-size:0.75rem;color:{TEXT_MUTED};line-height:1.4;">
Paste the full ingredient list including additive codes like INS 322.
</div>
</div>
</div>
<div style="background:{WHITE};border:1px solid {BORDER_TINT};border-radius:10px;
    padding:12px 14px;display:flex;align-items:flex-start;gap:10px;">
<span style="font-size:1.2rem;flex-shrink:0;">⚠️</span>
<div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;
    font-size:0.8rem;color:{DARK_CHERRY};margin-bottom:2px;">Check the original label</div>
<div style="font-size:0.75rem;color:{TEXT_MUTED};line-height:1.4;">
This tool is an aid. Always read the physical label yourself.
</div>
</div>
</div>
</div>
""")

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    st.divider()

    # ── Check button ──────────────────────────────────────────────────────────
    text_to_check = st.session_state.get("manual_text", ingredient_text) or ingredient_text
    col_btn, col_hint = st.columns([2, 5])
    with col_btn:
        run_check = st.button("🔍 Check Ingredients", type="primary", key="btn_check", use_container_width=True)
    with col_hint:
        if profile_allergens_db:
            allergen_names = [a.allergen for a in profile_allergens_db]
            pills = " ".join([
                f"<span style='background:{TINT};color:{DARK_CHERRY};"
                f"border-radius:4px;padding:1px 8px;font-weight:500;font-size:0.78rem;'>{n}</span>"
                for n in allergen_names
            ])
            render_html(f"""
<div style="padding-top:8px;font-size:0.83rem;color:{TEXT_MUTED};">
Checking against: {pills}
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

    # ── Results ───────────────────────────────────────────────────────────────
    results = st.session_state.get("last_results")
    last_text = st.session_state.get("last_ingredient_text", "")

    if results is None or not last_text:
        render_html(f"""
<div style="background:{WHITE};border:1.5px dashed {BORDER_TINT};
    border-radius:16px;padding:48px 32px;text-align:center;margin-top:16px;">
<div style="font-size:3rem;margin-bottom:16px;">🔍</div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;
    font-size:1.15rem;color:{DARK_CHERRY};margin-bottom:8px;">
Your results will appear here
</div>
<div style="font-size:0.875rem;color:{TEXT_MUTED};max-width:360px;
    margin:0 auto 20px;line-height:1.6;">
Paste an ingredient list above, or load a sample, then click
<strong style="color:{CHERRY};">Check Ingredients</strong>.
</div>
<div style="display:inline-flex;gap:10px;flex-wrap:wrap;justify-content:center;
    background:{TINT};border-radius:10px;padding:12px 18px;">
<span style="font-size:0.78rem;color:{TEXT_MUTED};">You'll see:</span>
<span style="background:{PRESENT_BG};color:{PRESENT_FG};border-radius:20px;
    padding:2px 12px;font-size:0.75rem;font-weight:700;">{PRESENT_ICON} {PRESENT_LABEL}</span>
<span style="background:{MAY_BG};color:{MAY_FG};border-radius:20px;
    padding:2px 12px;font-size:0.75rem;font-weight:700;">{MAY_ICON} {MAY_LABEL}</span>
<span style="background:{UNCERTAIN_BG};color:{UNCERTAIN_FG};border-radius:20px;
    padding:2px 12px;font-size:0.75rem;font-weight:700;">{UNCERTAIN_ICON} {UNCERTAIN_LABEL}</span>
</div>
</div>
""")
        return

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

    # ── PDF download ──────────────────────────────────────────────────────────
    st.divider()
    try:
        profiles = get_profiles()
        active_profile = next((p for p in profiles if p.id == active_id), None)
        profile_name = active_profile.name if active_profile else "Unknown"
    except Exception:
        profile_name = "Unknown"
    col_dl, col_note = st.columns([2, 5])
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
Includes full results, explanations, and the disclaimer.
</div>
""")
    except Exception as exc:
        st.warning(f"PDF generation failed: {exc}")

    # ── Page footer ───────────────────────────────────────────────────────────
    render_html(f"""
<div style="background:#1F2937;border-radius:14px;padding:20px 28px;
    margin-top:32px;display:flex;justify-content:space-between;
    align-items:center;flex-wrap:wrap;gap:12px;">
<div style="font-size:0.8rem;color:#9CA3AF;">
🥛 <strong style="color:#fff;">Food Allergy Ingredient Checker</strong> ·
All processing is local · No data sent anywhere
</div>
<div style="font-size:0.75rem;color:#6B7280;">
⚠️ "No known match found" ≠ allergen-free. Always read the original label.
</div>
</div>
<div style="height:24px;"></div>
""")
