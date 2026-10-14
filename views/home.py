"""
views/home.py — Landing / Home page.

All HTML goes through render_html() to prevent indentation-as-code-block issues.
Theme: Cherry red (#D20A2E), dark cherry (#8F0720), deep cherry (#5C0516), tint (#FCE8EB), white (#FFFFFF).
"""
from __future__ import annotations
import json
import sys
from datetime import datetime
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from core.constants import (
    DISCLAIMER_TEXT_SHORT,
    SEVERITY_MILD, SEVERITY_MODERATE, SEVERITY_SEVERE,
    STATUS_MAY_CONTAIN, STATUS_NO_MATCH, STATUS_PRESENT, STATUS_UNCERTAIN,
)
from core.db import (
    get_history, get_profiles, get_allergens_for_profile, save_history,
)
from core.matcher import MatchResult, match_allergens, AllergenEntry as MatchAllergenEntry, _is_vague
from core.ins_decoder import extract_ins_codes
from core.parser import parse_ingredients
from core.ui import (
    render_html,
    CHERRY, DARK_CHERRY, DEEP_CHERRY, TINT, WHITE,
    TEXT_DARK, TEXT_BODY, TEXT_MUTED, BORDER_TINT,
    PRESENT_FG, PRESENT_BG, PRESENT_BORDER, PRESENT_ICON, PRESENT_LABEL,
    MAY_FG, MAY_BG, MAY_BORDER, MAY_ICON, MAY_LABEL,
    UNCERTAIN_FG, UNCERTAIN_BG, UNCERTAIN_BORDER, UNCERTAIN_ICON, UNCERTAIN_LABEL,
    NOT_RECOGNISED_FG, NOT_RECOGNISED_BG, NOT_RECOGNISED_BORDER, NOT_RECOGNISED_ICON, NOT_RECOGNISED_LABEL,
    NO_MATCH_FG, NO_MATCH_BG, NO_MATCH_BORDER, NO_MATCH_ICON, NO_MATCH_LABEL,
)

DATA_DIR = ROOT / "data"
SAMPLES_DIR = DATA_DIR / "samples"


def _summary_status(results: list[MatchResult]) -> str:
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


def show() -> None:
    # ── Load data dynamically for stats ───────────────────────────────────────
    allergen_data = st.session_state.get("allergen_data", {})
    ins_data = st.session_state.get("ins_data", {})

    n_categories = len(allergen_data)
    n_synonyms = sum(len(v.get("synonyms", [])) for v in allergen_data.values()) if allergen_data else 0
    n_ins = len(ins_data)
    sample_files = list(SAMPLES_DIR.glob("*.txt")) if SAMPLES_DIR.exists() else []
    n_samples = len(sample_files)

    # ── Active profile resolution ─────────────────────────────────────────────
    profiles = []
    try:
        profiles = get_profiles()
    except Exception:
        profiles = []

    active_id = st.session_state.get("active_profile_id")
    active_profile = next((p for p in profiles if p.id == active_id), profiles[0] if profiles else None)
    if active_profile and active_id != active_profile.id:
        active_id = active_profile.id
        st.session_state["active_profile_id"] = active_id

    profile_allergens_db = []
    if active_id:
        try:
            profile_allergens_db = get_allergens_for_profile(active_id)
        except Exception:
            profile_allergens_db = []

    prof_name = active_profile.name if active_profile else "Default"
    n_prof_allergens = len(profile_allergens_db)

    # ── 1. Hero Banner ────────────────────────────────────────────────────────
    render_html(f"""
<div class="fade-up hero" style="
    background:linear-gradient(135deg,{CHERRY} 0%,{DARK_CHERRY} 100%);
    border-radius:20px;padding:32px 36px;margin-bottom:12px;
    box-shadow:0 10px 30px rgba(210,10,46,.22);position:relative;overflow:hidden;
">
<div style="display:flex;align-items:center;justify-content:space-between;gap:24px;flex-wrap:wrap;">
<div style="flex:1;min-width:300px;max-width:680px;">
<div style="display:inline-flex;align-items:center;gap:8px;
    background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.35);
    border-radius:20px;padding:4px 14px;margin-bottom:12px;">
<span style="font-size:0.95rem;">🛡️</span>
<span style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;
    font-size:0.78rem;color:#FFFFFF;letter-spacing:.03em;">100% Offline &amp; Private · Indian Food Allergen Scanner</span>
</div>
<h1 style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;
    font-size:2.3rem;line-height:1.2;color:#FFFFFF !important;margin:0 0 10px;
    text-shadow:0 2px 6px rgba(0,0,0,.35);">
Food Allergy Ingredient Checker
</h1>
<p style="font-size:0.98rem;color:rgba(255,255,255,.94);line-height:1.6;
    margin:0 0 20px;">
Spot hidden allergens masquerading as <strong style="color:#fff;background:rgba(255,255,255,.2);padding:1px 6px;border-radius:4px;">casein</strong>,
<strong style="color:#fff;background:rgba(255,255,255,.2);padding:1px 6px;border-radius:4px;">maida</strong>,
<strong style="color:#fff;background:rgba(255,255,255,.2);padding:1px 6px;border-radius:4px;">INS 322</strong>, and
<strong style="color:#fff;background:rgba(255,255,255,.2);padding:1px 6px;border-radius:4px;">groundnut</strong> on Indian packaged food labels —
instantly and privately on your device.
</p>
<div style="display:flex;gap:12px;flex-wrap:wrap;">
<a href="check" target="_self" style="text-decoration:none;">
<div style="background:#FFFFFF;color:{DARK_CHERRY};border-radius:12px;
    padding:11px 24px;font-family:'Plus Jakarta Sans',sans-serif;
    font-weight:800;font-size:0.92rem;cursor:pointer;
    box-shadow:0 4px 14px rgba(0,0,0,.20);display:inline-flex;align-items:center;gap:8px;">
🔍 Check Ingredients
</div>
</a>
<a href="about" target="_self" style="text-decoration:none;">
<div style="background:rgba(255,255,255,.15);color:#FFFFFF;
    border:1.5px solid rgba(255,255,255,.65);border-radius:12px;
    padding:10px 20px;font-family:'Plus Jakarta Sans',sans-serif;
    font-weight:700;font-size:0.92rem;cursor:pointer;display:inline-flex;align-items:center;gap:8px;">
ℹ️ Learn More
</div>
</a>
</div>
</div>

<div style="flex-shrink:0;background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.3);
    border-radius:16px;padding:16px 20px;backdrop-filter:blur(8px);min-width:240px;">
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:0.85rem;color:#FFFFFF;margin-bottom:8px;display:flex;align-items:center;gap:6px;">
<span>⚡</span> Active Inspection Profile
</div>
<div style="background:rgba(0,0,0,.25);border-radius:10px;padding:8px 12px;margin-bottom:8px;">
<div style="font-size:0.75rem;color:rgba(255,255,255,.75);">Profile</div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:1rem;color:#FFFFFF;">👤 {prof_name}</div>
<div style="font-size:0.74rem;color:rgba(255,255,255,.9);margin-top:2px;">Tracking {n_prof_allergens} allergen{'s' if n_prof_allergens != 1 else ''}</div>
</div>
<div style="font-size:0.72rem;color:rgba(255,255,255,.85);">
Deterministic algorithmic evaluation · Zero cloud telemetry
</div>
</div>
</div>
</div>
""")

    # ── 2. Allergen Emoji Strip ───────────────────────────────────────────────
    render_html(f"""
<div style="background:{WHITE};border:1.5px solid {BORDER_TINT};border-radius:14px;
    padding:12px 18px;margin-bottom:14px;box-shadow:0 2px 8px rgba(210,10,46,.04);
    display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;">
<div style="display:flex;align-items:center;gap:8px;">
<span style="font-size:1.1rem;">🧬</span>
<span style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;font-size:0.82rem;color:{DARK_CHERRY};">
Tracked Allergen Spectrum:
</span>
</div>
<div style="display:flex;align-items:center;flex-wrap:wrap;gap:12px;font-size:0.84rem;color:{TEXT_BODY};font-weight:600;">
<span>🥛 Milk</span>
<span style="color:{BORDER_TINT};">•</span>
<span>🥜 Peanut</span>
<span style="color:{BORDER_TINT};">•</span>
<span>🥚 Egg</span>
<span style="color:{BORDER_TINT};">•</span>
<span>🌾 Wheat</span>
<span style="color:{BORDER_TINT};">•</span>
<span>🌰 Tree nuts</span>
<span style="color:{BORDER_TINT};">•</span>
<span>🫘 Soy</span>
<span style="color:{BORDER_TINT};">•</span>
<span>🐟 Fish</span>
<span style="color:{BORDER_TINT};">•</span>
<span>🦐 Shellfish</span>
<span style="color:{BORDER_TINT};">•</span>
<span>🌿 Sesame &amp; mustard</span>
</div>
</div>
""")

    # ── 3. Quick Check & Live Detection Preview Side-by-Side ───────────────────
    col_quick, col_preview = st.columns([1, 1], gap="medium")

    with col_quick:
        render_html(f"""
<div style="background:{WHITE};border:1.5px solid {BORDER_TINT};border-radius:16px;
    padding:20px 22px;box-shadow:0 3px 12px rgba(210,10,46,.05);margin-bottom:14px;">
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;flex-wrap:wrap;gap:8px;">
<div style="display:flex;align-items:center;gap:8px;">
<div style="width:34px;height:34px;background:{TINT};border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:1.1rem;">⚡</div>
<div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:1.05rem;color:{DARK_CHERRY};">
Quick Check
</div>
<div style="font-size:0.75rem;color:{TEXT_MUTED};">Checking vs profile: <strong>{prof_name}</strong></div>
</div>
</div>
<span style="background:{TINT};color:{DARK_CHERRY};font-size:0.72rem;font-weight:700;border-radius:8px;padding:3px 8px;">
Instant Test
</span>
</div>
<div style="font-size:0.8rem;color:{TEXT_MUTED};margin-bottom:8px;">
Load a sample or enter ingredient text:
</div>
""")

        # Quick preset chips
        p_c1, p_c2, p_c3, p_c4 = st.columns(4)
        if p_c1.button("🍫 Choc", key="home_chip_choc", use_container_width=True):
            p = SAMPLES_DIR / "sample_04_chocolate.txt"
            if p.exists():
                st.session_state["home_quick_input"] = p.read_text(encoding="utf-8")
                st.rerun()
        if p_c2.button("🍪 Biscuit", key="home_chip_bisc", use_container_width=True):
            p = SAMPLES_DIR / "sample_01_biscuit.txt"
            if p.exists():
                st.session_state["home_quick_input"] = p.read_text(encoding="utf-8")
                st.rerun()
        if p_c3.button("🍜 Noodles", key="home_chip_nood", use_container_width=True):
            p = SAMPLES_DIR / "sample_03_instant_noodles.txt"
            if p.exists():
                st.session_state["home_quick_input"] = p.read_text(encoding="utf-8")
                st.rerun()
        if p_c4.button("🥜 Snack", key="home_chip_namk", use_container_width=True):
            p = SAMPLES_DIR / "sample_02_namkeen.txt"
            if p.exists():
                st.session_state["home_quick_input"] = p.read_text(encoding="utf-8")
                st.rerun()

        quick_text = st.text_area(
            "Quick check ingredients",
            value=st.session_state.get("home_quick_input", ""),
            height=75,
            placeholder="e.g. Sugar, cocoa butter, casein, whey, emulsifier (INS 322), natural flavours",
            key="home_quick_text_area",
            label_visibility="collapsed",
        )

        btn_col, link_col = st.columns([1, 1])
        with btn_col:
            run_quick = st.button("🔍 Check now", type="primary", key="home_btn_quick_check", use_container_width=True)
        with link_col:
            render_html(f"""
<div style="padding-top:8px;text-align:right;">
<a href="check" target="_self" style="color:{CHERRY};font-family:'Plus Jakarta Sans',sans-serif;font-size:0.8rem;font-weight:700;text-decoration:none;">
Advanced Check Page &rarr;
</a>
</div>
""")

        if run_quick:
            if not quick_text.strip():
                st.warning("Please enter an ingredient list before checking.")
            elif not profile_allergens_db:
                st.warning("No allergens configured in the active profile. Please add allergens on the Check page first.")
            else:
                try:
                    parse_result = parse_ingredients(quick_text)
                    profile_entries = [
                        MatchAllergenEntry(name=a.allergen, severity=a.severity)
                        for a in profile_allergens_db
                    ]
                    results = match_allergens(parse_result, profile_entries, allergen_data, ins_data)
                    st.session_state["home_quick_results"] = results
                    st.session_state["home_quick_checked_text"] = quick_text
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
                            ingredient_text=quick_text,
                            results_json=results_json,
                            summary_status=summary,
                        )
                    except Exception:
                        pass
                except Exception as exc:
                    st.error(f"Could not complete check: {exc}")

        # Render Quick Check Results if available
        quick_results = st.session_state.get("home_quick_results")
        quick_checked_text = st.session_state.get("home_quick_checked_text", "")

        if quick_results is not None and quick_checked_text:
            status = _summary_status(quick_results)
            p_count = sum(1 for r in quick_results if r.status == STATUS_PRESENT)
            m_count = sum(1 for r in quick_results if r.status == STATUS_MAY_CONTAIN)
            u_count = sum(1 for r in quick_results if r.status == STATUS_UNCERTAIN)

            # Find unrecognised tokens
            parse_res = parse_ingredients(quick_checked_text)
            matched_terms_lower = {mt.term.lower() for r in quick_results for mt in r.matched_terms}
            unrecognised = []
            for tok in parse_res.tokens:
                t = tok.strip().lower()
                if not t:
                    continue
                if any(t in mt or mt in t for mt in matched_terms_lower):
                    continue
                if extract_ins_codes(tok):
                    continue
                if _is_vague(tok):
                    continue
                unrecognised.append(tok.strip())

            if status == STATUS_PRESENT:
                b_icon, b_title = PRESENT_ICON, "PRESENT — Allergen(s) Detected"
                b_bg, b_border, b_fg = "#FFF0F2", PRESENT_BORDER, PRESENT_BG
            elif status == STATUS_MAY_CONTAIN:
                b_icon, b_title = MAY_ICON, "MAY CONTAIN — Trace Allergen(s) Detected"
                b_bg, b_border, b_fg = "#FFF7ED", MAY_BORDER, MAY_BG
            elif status == STATUS_UNCERTAIN:
                b_icon, b_title = UNCERTAIN_ICON, "UNCERTAIN — Ambiguous Ingredient(s)"
                b_bg, b_border, b_fg = "#FEFCE8", UNCERTAIN_BORDER, "#713F12"
            else:
                b_icon, b_title = NO_MATCH_ICON, "No known match found among recognised ingredients"
                b_bg, b_border, b_fg = WHITE, CHERRY, DARK_CHERRY

            pills_html = []
            if p_count:
                pills_html.append(f"<span style='background:{PRESENT_BG};color:{PRESENT_FG};border-radius:20px;padding:2px 10px;font-size:0.75rem;font-weight:700;'>{PRESENT_ICON} {p_count} {PRESENT_LABEL}</span>")
            if m_count:
                pills_html.append(f"<span style='background:{MAY_BG};color:{MAY_FG};border-radius:20px;padding:2px 10px;font-size:0.75rem;font-weight:700;'>{MAY_ICON} {m_count} {MAY_LABEL}</span>")
            if u_count:
                pills_html.append(f"<span style='background:{UNCERTAIN_BG};color:{UNCERTAIN_FG};border-radius:20px;padding:2px 10px;font-size:0.75rem;font-weight:700;'>{UNCERTAIN_ICON} {u_count} {UNCERTAIN_LABEL}</span>")
            if unrecognised:
                pills_html.append(f"<span style='background:{NOT_RECOGNISED_BG};color:{NOT_RECOGNISED_FG};border:1px solid {NOT_RECOGNISED_BORDER};border-radius:20px;padding:2px 10px;font-size:0.75rem;font-weight:700;'>{NOT_RECOGNISED_ICON} {len(unrecognised)} {NOT_RECOGNISED_LABEL}</span>")

            rendered_pills = " ".join(pills_html)

            render_html(f"""
<div class="fade-up" style="background:{b_bg};border:1.5px solid {b_border};
    border-radius:12px;padding:12px 16px;margin-top:12px;">
<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
<span style="font-size:1.3rem;">{b_icon}</span>
<span style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:0.92rem;color:{b_fg};">
{b_title}
</span>
</div>
<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:6px;">{rendered_pills}</div>
<div style="font-size:0.75rem;color:{TEXT_MUTED};border-top:1px solid {b_border};padding-top:6px;margin-top:6px;">
⚠️ Informational aid only. Always read physical label.
</div>
</div>
""")

        render_html("</div>")

    # Right column: Example Result Preview
    with col_preview:
        render_html(f"""
<div style="background:{WHITE};border:1.5px solid {BORDER_TINT};border-radius:16px;
    padding:20px 22px;box-shadow:0 3px 12px rgba(210,10,46,.05);margin-bottom:14px;">
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;flex-wrap:wrap;gap:8px;">
<div style="display:flex;align-items:center;gap:8px;">
<div style="width:34px;height:34px;background:{TINT};border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:1.1rem;">🧪</div>
<div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:1.05rem;color:{DARK_CHERRY};">
Detection Output Preview
</div>
<div style="font-size:0.75rem;color:{TEXT_MUTED};">Interactive sample label showing highlight indicators</div>
</div>
</div>
<span style="background:{TINT};color:{DARK_CHERRY};font-size:0.72rem;font-weight:700;border-radius:8px;padding:3px 8px;">
Sample #04
</span>
</div>

<div style="background:{TINT};border:1px solid {BORDER_TINT};border-radius:10px;padding:10px 14px;
    font-family:'SF Mono',monospace;font-size:0.8rem;color:{TEXT_BODY};line-height:1.8;margin-bottom:10px;">
Sugar, cocoa butter,
<mark style="background:{DEEP_CHERRY};color:#FFFFFF;border-radius:4px;padding:2px 6px;font-weight:700;" title="MILK: Casein dairy protein">casein</mark>,
<mark style="background:{DEEP_CHERRY};color:#FFFFFF;border-radius:4px;padding:2px 6px;font-weight:700;" title="MILK: Liquid dairy whey">whey</mark>,
emulsifier (<mark style="background:{MAY_BG};color:#FFFFFF;border-radius:4px;padding:2px 6px;font-weight:700;" title="SOY/EGG: INS 322 Lecithin">INS 322</mark>),
<mark style="background:{UNCERTAIN_BG};color:{UNCERTAIN_FG};border-radius:4px;padding:2px 6px;font-weight:700;" title="UNCERTAIN: Natural flavour source undeclared">natural flavours</mark>
</div>

<div style="display:flex;flex-direction:column;gap:6px;">
<div style="background:{DEEP_CHERRY};border-radius:8px;padding:7px 12px;color:#fff;display:flex;align-items:center;justify-content:space-between;">
<span style="font-size:0.8rem;font-weight:700;">🥛 Milk (Casein, Whey)</span>
<span style="background:rgba(255,255,255,.2);border-radius:12px;padding:2px 8px;font-size:0.7rem;font-weight:800;">⛔ PRESENT</span>
</div>
<div style="background:{MAY_BG};border-radius:8px;padding:7px 12px;color:#fff;display:flex;align-items:center;justify-content:space-between;">
<span style="font-size:0.8rem;font-weight:700;">🫘 Soy / Egg (INS 322 Lecithin)</span>
<span style="background:rgba(255,255,255,.2);border-radius:12px;padding:2px 8px;font-size:0.7rem;font-weight:800;">⚠️ MAY CONTAIN</span>
</div>
<div style="background:{UNCERTAIN_BG};border-radius:8px;padding:7px 12px;color:{UNCERTAIN_FG};display:flex;align-items:center;justify-content:space-between;">
<span style="font-size:0.8rem;font-weight:700;">❓ Vague Source (Natural Flavours)</span>
<span style="background:rgba(0,0,0,.12);border-radius:12px;padding:2px 8px;font-size:0.7rem;font-weight:800;">❓ UNCERTAIN</span>
</div>
<div style="background:{NOT_RECOGNISED_BG};border:1px solid {NOT_RECOGNISED_BORDER};border-radius:8px;padding:7px 12px;color:{NOT_RECOGNISED_FG};display:flex;align-items:center;justify-content:space-between;">
<span style="font-size:0.8rem;font-weight:600;">Sugar, Cocoa Butter</span>
<span style="background:#E5E7EB;border-radius:12px;padding:2px 8px;font-size:0.7rem;font-weight:700;">❔ NOT RECOGNISED</span>
</div>
</div>
</div>
""")

    # ── 4. Stats Strip (Dynamically Read) ─────────────────────────────────────
    render_html(f"""
<div style="background:linear-gradient(135deg,{CHERRY} 0%,{DARK_CHERRY} 100%);
    border-radius:16px;padding:20px 24px;margin-bottom:16px;
    box-shadow:0 8px 24px rgba(210,10,46,.20);">
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0;text-align:center;">
<div class="stat-card" style="border-right:1px solid rgba(255,255,255,.25);padding:0 12px;">
<div style="font-size:1.2rem;margin-bottom:2px;">🗂️</div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;
    font-size:1.8rem;color:#FFFFFF;line-height:1;">{n_categories}</div>
<div style="font-size:0.78rem;color:rgba(255,255,255,.9);margin-top:4px;font-weight:600;">Allergen Categories</div>
</div>
<div class="stat-card" style="border-right:1px solid rgba(255,255,255,.25);padding:0 12px;">
<div style="font-size:1.2rem;margin-bottom:2px;">📖</div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;
    font-size:1.8rem;color:#FFFFFF;line-height:1;">{n_synonyms}</div>
<div style="font-size:0.78rem;color:rgba(255,255,255,.9);margin-top:4px;font-weight:600;">Synonyms &amp; Indian Names</div>
</div>
<div class="stat-card" style="border-right:1px solid rgba(255,255,255,.25);padding:0 12px;">
<div style="font-size:1.2rem;margin-bottom:2px;">🧪</div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;
    font-size:1.8rem;color:#FFFFFF;line-height:1;">{n_ins}</div>
<div style="font-size:0.78rem;color:rgba(255,255,255,.9);margin-top:4px;font-weight:600;">INS Codes Decoded</div>
</div>
<div class="stat-card" style="padding:0 12px;">
<div style="font-size:1.2rem;margin-bottom:2px;">📦</div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;
    font-size:1.8rem;color:#FFFFFF;line-height:1;">{n_samples}</div>
<div style="font-size:0.78rem;color:rgba(255,255,255,.9);margin-top:4px;font-weight:600;">Sample Labels</div>
</div>
</div>
</div>
""")

    # ── 5. How It Works (4 Cards in One Row) ──────────────────────────────────
    render_html(f"""
<div style="background:{WHITE};border:1.5px solid {BORDER_TINT};border-radius:16px;
    padding:20px 24px;margin-bottom:16px;box-shadow:0 3px 12px rgba(210,10,46,.05);">
<div style="text-align:center;margin-bottom:16px;">
<div style="display:inline-flex;align-items:center;gap:6px;background:{TINT};
    border:1px solid {BORDER_TINT};border-radius:20px;padding:3px 12px;margin-bottom:4px;">
<span style="font-size:0.8rem;">🔄</span>
<span style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;font-size:0.75rem;color:{CHERRY};text-transform:uppercase;letter-spacing:.05em;">Step-by-Step Flow</span>
</div>
<h2 style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;
    font-size:1.35rem;color:{DARK_CHERRY};margin:0;">
How It Works
</h2>
</div>

<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px;">
<div style="background:{TINT};border-radius:12px;padding:16px 14px;text-align:center;border:1px solid {BORDER_TINT};">
<div style="width:38px;height:38px;background:{CHERRY};border-radius:50%;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:0.95rem;margin:0 auto 10px;box-shadow:0 3px 8px rgba(210,10,46,.25);">1</div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:0.9rem;color:{DARK_CHERRY};margin-bottom:4px;">Enter or scan</div>
<div style="font-size:0.78rem;color:{TEXT_MUTED};line-height:1.45;">
Type or paste an ingredient list, upload a label photo, or choose a test sample.
</div>
</div>

<div style="background:{TINT};border-radius:12px;padding:16px 14px;text-align:center;border:1px solid {BORDER_TINT};">
<div style="width:38px;height:38px;background:{CHERRY};border-radius:50%;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:0.95rem;margin:0 auto 10px;box-shadow:0 3px 8px rgba(210,10,46,.25);">2</div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:0.9rem;color:{DARK_CHERRY};margin-bottom:4px;">Choose allergens</div>
<div style="font-size:0.78rem;color:{TEXT_MUTED};line-height:1.45;">
Select target allergens and configure mild, moderate, or severe flags in your profile.
</div>
</div>

<div style="background:{TINT};border-radius:12px;padding:16px 14px;text-align:center;border:1px solid {BORDER_TINT};">
<div style="width:38px;height:38px;background:{CHERRY};border-radius:50%;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:0.95rem;margin:0 auto 10px;box-shadow:0 3px 8px rgba(210,10,46,.25);">3</div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:0.9rem;color:{DARK_CHERRY};margin-bottom:4px;">Check</div>
<div style="font-size:0.78rem;color:{TEXT_MUTED};line-height:1.45;">
Engine evaluates Indian synonyms, INS additive codes, and trace cross-contact notes.
</div>
</div>

<div style="background:{TINT};border-radius:12px;padding:16px 14px;text-align:center;border:1px solid {BORDER_TINT};">
<div style="width:38px;height:38px;background:{CHERRY};border-radius:50%;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:0.95rem;margin:0 auto 10px;box-shadow:0 3px 8px rgba(210,10,46,.25);">4</div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:0.9rem;color:{DARK_CHERRY};margin-bottom:4px;">Review results</div>
<div style="font-size:0.78rem;color:{TEXT_MUTED};line-height:1.45;">
Read highlighted terms, color-coded badges, reason explanations, and export PDF.
</div>
</div>
</div>
</div>
""")

    # ── 6. Feature Cards (3-Column Grid) ──────────────────────────────────────
    render_html(f"""
<div style="text-align:center;margin-bottom:14px;">
<div style="display:inline-flex;align-items:center;gap:6px;background:{TINT};
    border:1px solid {BORDER_TINT};border-radius:20px;padding:3px 12px;margin-bottom:4px;">
<span style="font-size:0.8rem;">✨</span>
<span style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;font-size:0.75rem;color:{CHERRY};text-transform:uppercase;letter-spacing:.05em;">Core Features</span>
</div>
<h2 style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;
    font-size:1.35rem;color:{DARK_CHERRY};margin:0;">
Key Capabilities
</h2>
</div>
""")

    FEATURES = [
        ("🇮🇳", "Indian label decoder",
         "Translates colloquial Indian culinary terms: <em>maida</em> (wheat), <em>groundnut</em> (peanut), <em>til</em> (sesame), and <em>khoya/paneer</em> (milk).",
         "Regional Cuisine"),
        ("❓", "\"Why was this flagged?\" explanations",
         "Transparent reason breakdowns showing exact match, fuzzy typo correction, INS code lookup, or trace cross-contamination line.",
         "Explainable AI"),
        ("👤", "Multiple profiles",
         "Maintain tailored allergen profiles for every family member, child, or guest with customized allergen lists.",
         "Family Safety"),
        ("⚖️", "Severity levels",
         "Assign mild, moderate, or severe ratings to each allergen to tailor warning urgency to clinical risk.",
         "Clinical Triage"),
        ("🕘", "Scan history",
         "SQLite database records past scans locally so you can review previously checked food packages anytime.",
         "Persistent Audit"),
        ("📄", "PDF report",
         "Generate clean, printable PDF audit summaries with match evidence, highlighted ingredients, timestamps, and disclaimers.",
         "Print Ready"),
    ]

    cols_feat = st.columns(3, gap="medium")
    for i, (icon, title, desc, tag) in enumerate(FEATURES):
        with cols_feat[i % 3]:
            render_html(f"""
<div class="feat-card" style="
    background:{WHITE};border-radius:14px;padding:18px 20px 16px;
    border-left:4px solid {CHERRY};border-top:1px solid {BORDER_TINT};
    border-right:1px solid {BORDER_TINT};border-bottom:1px solid {BORDER_TINT};
    box-shadow:0 2px 8px rgba(210,10,46,.05);
    margin-bottom:12px;min-height:150px;display:flex;flex-direction:column;justify-content:space-between;
">
<div>
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
<div style="width:36px;height:36px;background:{TINT};
    border-radius:10px;display:flex;align-items:center;justify-content:center;
    font-size:1.2rem;">{icon}</div>
<span style="background:{TINT};color:{DARK_CHERRY};font-size:0.7rem;font-weight:700;
    border-radius:6px;padding:2px 8px;">{tag}</span>
</div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;
    font-size:0.95rem;color:{DARK_CHERRY};margin-bottom:4px;">{title}</div>
<div style="font-size:0.8rem;color:{TEXT_MUTED};line-height:1.5;">{desc}</div>
</div>
</div>
""")

    # ── 7. Recent Checks & Tips Box Side-by-Side ──────────────────────────────
    col_hist, col_tips = st.columns([1, 1], gap="medium")

    with col_hist:
        render_html(f"""
<div style="background:{WHITE};border:1.5px solid {BORDER_TINT};border-radius:16px;
    padding:20px 22px;box-shadow:0 3px 12px rgba(210,10,46,.05);margin-bottom:14px;height:100%;">
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
<div style="display:flex;align-items:center;gap:8px;">
<div style="width:34px;height:34px;background:{TINT};border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:1.1rem;">🕘</div>
<div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:1.05rem;color:{DARK_CHERRY};">
Recent Checks
</div>
<div style="font-size:0.75rem;color:{TEXT_MUTED};">Latest 3 entries from local SQLite scan history</div>
</div>
</div>
<a href="history" target="_self" style="color:{CHERRY};font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;font-size:0.8rem;text-decoration:none;">
View all &rarr;
</a>
</div>
""")
        recent_entries = []
        try:
            recent_entries = get_history(limit=3)
        except Exception:
            recent_entries = []

        if not recent_entries:
            render_html(f"""
<div style="background:{TINT};border:1px dashed {BORDER_TINT};border-radius:10px;padding:22px;text-align:center;color:{TEXT_MUTED};font-size:0.82rem;margin-top:8px;">
📋 No recent checks recorded yet. Run your first check above or on the Check page!
</div>
""")
        else:
            for entry in recent_entries:
                st_badge = ""
                if entry.summary_status == STATUS_PRESENT:
                    st_badge = f"<span style='background:{PRESENT_BG};color:{PRESENT_FG};border-radius:12px;padding:2px 8px;font-size:0.7rem;font-weight:700;'>{PRESENT_ICON} PRESENT</span>"
                elif entry.summary_status == STATUS_MAY_CONTAIN:
                    st_badge = f"<span style='background:{MAY_BG};color:{MAY_FG};border-radius:12px;padding:2px 8px;font-size:0.7rem;font-weight:700;'>{MAY_ICON} MAY CONTAIN</span>"
                elif entry.summary_status == STATUS_UNCERTAIN:
                    st_badge = f"<span style='background:{UNCERTAIN_BG};color:{UNCERTAIN_FG};border-radius:12px;padding:2px 8px;font-size:0.7rem;font-weight:700;'>{UNCERTAIN_ICON} UNCERTAIN</span>"
                else:
                    st_badge = f"<span style='background:{WHITE};color:{DARK_CHERRY};border:1px solid {CHERRY};border-radius:12px;padding:2px 8px;font-size:0.7rem;font-weight:700;'>{NO_MATCH_ICON} No Match Found</span>"

                # Parse date nicely
                try:
                    dt = datetime.fromisoformat(entry.timestamp.replace("Z", "+00:00"))
                    date_str = dt.strftime("%b %d, %H:%M")
                except Exception:
                    date_str = entry.timestamp[:16]

                preview_txt = entry.ingredient_text.strip()
                if len(preview_txt) > 55:
                    preview_txt = preview_txt[:55] + "..."

                render_html(f"""
<div style="background:{TINT};border:1px solid {BORDER_TINT};border-radius:10px;padding:10px 12px;margin-bottom:8px;">
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px;">
<span style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;font-size:0.82rem;color:{DARK_CHERRY};">
👤 {entry.profile_name}
</span>
<div style="display:flex;align-items:center;gap:6px;">
{st_badge}
<span style="font-size:0.72rem;color:{TEXT_MUTED};">{date_str}</span>
</div>
</div>
<div style="font-size:0.78rem;color:{TEXT_BODY};font-family:'SF Mono',monospace;line-height:1.3;">
{preview_txt}
</div>
</div>
""")

        render_html("</div>")

    with col_tips:
        render_html(f"""
<div style="background:{WHITE};border:1.5px solid {BORDER_TINT};border-radius:16px;
    padding:20px 22px;box-shadow:0 3px 12px rgba(210,10,46,.05);margin-bottom:14px;height:100%;">
<div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
<div style="width:34px;height:34px;background:{TINT};border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:1.1rem;">💡</div>
<div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:1.05rem;color:{DARK_CHERRY};">
Important Allergy Safety Tips
</div>
<div style="font-size:0.75rem;color:{TEXT_MUTED};">Key guidance for navigating packaged food labels</div>
</div>
</div>

<div style="display:flex;flex-direction:column;gap:10px;">
<div style="background:{TINT};border:1px solid {BORDER_TINT};border-radius:10px;padding:10px 12px;">
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;font-size:0.82rem;color:{DARK_CHERRY};margin-bottom:2px;display:flex;align-items:center;gap:6px;">
<span>🏷️</span> Check the original label
</div>
<div style="font-size:0.78rem;color:{TEXT_BODY};line-height:1.45;">
Food manufacturers frequently change formulations, ingredient suppliers, and production lines without notice. Always read the physical package in your hand.
</div>
</div>

<div style="background:{TINT};border:1px solid {BORDER_TINT};border-radius:10px;padding:10px 12px;">
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;font-size:0.82rem;color:{DARK_CHERRY};margin-bottom:2px;display:flex;align-items:center;gap:6px;">
<span>🛡️</span> "No known match found" does not mean "safe"
</div>
<div style="font-size:0.78rem;color:{TEXT_BODY};line-height:1.45;">
It means the engine evaluated your text against its 213 synonym rules and 25 INS codes and found no listed allergen keyword. It cannot detect undeclared cross-contact or obscure regional terms.
</div>
</div>

<div style="background:{TINT};border:1px solid {BORDER_TINT};border-radius:10px;padding:10px 12px;">
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;font-size:0.82rem;color:{DARK_CHERRY};margin-bottom:2px;display:flex;align-items:center;gap:6px;">
<span>📷</span> OCR can misread text
</div>
<div style="font-size:0.78rem;color:{TEXT_BODY};line-height:1.45;">
Camera glare, packaging folds, low-contrast ink, and curved bottles can cause character misreads during photo scanning. Always verify extracted text before relying on results.
</div>
</div>
</div>
</div>
""")

    # ── 8. Compact Footer ─────────────────────────────────────────────────────
    render_html(f"""
<div style="background:#1F2937;border-radius:14px;padding:22px 28px 18px;margin-top:10px;">
<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:16px;margin-bottom:14px;border-bottom:1px solid #374151;padding-bottom:12px;">
<div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:0.95rem;color:#FFFFFF;">
🥛 Food Allergy Ingredient Checker
</div>
<div style="font-size:0.76rem;color:#9CA3AF;margin-top:2px;">
Local, deterministic, offline Indian food allergen inspection engine.
</div>
</div>
<div style="display:flex;align-items:center;gap:14px;font-size:0.8rem;">
<a href="check" target="_self" style="color:#D1D5DB;text-decoration:none;font-weight:600;">🔍 Check</a>
<a href="history" target="_self" style="color:#D1D5DB;text-decoration:none;font-weight:600;">🕘 History</a>
<a href="about" target="_self" style="color:#D1D5DB;text-decoration:none;font-weight:600;">ℹ️ About</a>
</div>
</div>

<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;font-size:0.74rem;color:#9CA3AF;">
<div style="display:inline-flex;align-items:center;gap:6px;background:#374151;border-radius:6px;padding:3px 10px;color:#F3F4F6;">
<span>⚠️</span> <span>Aid only — not medical advice. Consult a healthcare professional for allergy care.</span>
</div>
<div style="color:#6B7280;">
"No known match found among recognised ingredients" ≠ allergen-free.
</div>
</div>
</div>
""")
