"""
views/history.py — History page. All HTML via render_html().
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
    STATUS_MAY_CONTAIN, STATUS_NO_MATCH, STATUS_PRESENT, STATUS_UNCERTAIN,
)
from core.db import delete_history_entry, get_history, get_profiles
from core.matcher import MatchedTerm, MatchResult
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

_STATUS_META = {
    STATUS_PRESENT:     (PRESENT_BG,   PRESENT_BORDER,   f"{PRESENT_ICON} {PRESENT_LABEL}",   PRESENT_FG),
    STATUS_MAY_CONTAIN: (MAY_BG,       MAY_BORDER,       f"{MAY_ICON} {MAY_LABEL}",           MAY_FG),
    STATUS_UNCERTAIN:   (UNCERTAIN_BG, UNCERTAIN_BORDER, f"{UNCERTAIN_ICON} {UNCERTAIN_LABEL}", UNCERTAIN_FG),
    STATUS_NO_MATCH:    (NO_MATCH_BG,  NO_MATCH_BORDER,  f"{NO_MATCH_ICON} No Match",          NO_MATCH_FG),
}


def _parse_results(results_json: str) -> list[MatchResult]:
    try:
        raw = json.loads(results_json)
        out = []
        for r in raw:
            terms = [
                MatchedTerm(
                    term=mt.get("term", ""), explanation=mt.get("explanation", ""),
                    match_type=mt.get("match_type", "exact"), synonym=mt.get("synonym", ""),
                )
                for mt in r.get("matched_terms", [])
            ]
            out.append(MatchResult(
                allergen=r.get("allergen", ""), severity=r.get("severity", "moderate"),
                status=r.get("status", STATUS_NO_MATCH), emoji=r.get("emoji", "⚠️"),
                matched_terms=terms,
            ))
        return out
    except Exception:
        return []


def show() -> None:
    render_html(f"""
<div style="background:{TINT};border:1px solid {BORDER_TINT};border-radius:8px;
    padding:10px 12px;font-size:0.75rem;color:{TEXT_MUTED};line-height:1.5;margin-top:8px;">
⚠️ {DISCLAIMER_TEXT_SHORT}
</div>
""")

    render_html(f"""
<div style="margin-bottom:20px;">
<h1 style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;
    font-size:1.6rem;color:{DARK_CHERRY};margin:0;">🕘 Check History</h1>
<p style="color:{TEXT_MUTED};margin:4px 0 0;font-size:0.9rem;">
Every check you run is saved here. Filter, reopen or delete entries.
</p>
</div>
""")

    # Stats strip
    try:
        all_entries = get_history()
        total    = len(all_entries)
        n_present = sum(1 for e in all_entries if e.summary_status == STATUS_PRESENT)
        n_may     = sum(1 for e in all_entries if e.summary_status == STATUS_MAY_CONTAIN)
        n_none    = sum(1 for e in all_entries if e.summary_status == STATUS_NO_MATCH)
    except Exception:
        total = n_present = n_may = n_none = 0

    render_html(f"""
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:20px;">
<div style="background:{WHITE};border:1.5px solid {BORDER_TINT};border-radius:12px;
    padding:14px 16px;text-align:center;box-shadow:0 2px 6px rgba(210,4,45,.05);">
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;
    font-size:1.6rem;color:{TEXT_DARK};">{total}</div>
<div style="font-size:0.78rem;color:{TEXT_MUTED};margin-top:2px;">Total checks</div>
</div>
<div style="background:{PRESENT_BG};border:1.5px solid {PRESENT_BORDER};border-radius:12px;
    padding:14px 16px;text-align:center;">
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;
    font-size:1.6rem;color:{PRESENT_FG};">{n_present}</div>
<div style="font-size:0.78rem;color:{PRESENT_FG};margin-top:2px;opacity:.85;">
{PRESENT_ICON} {PRESENT_LABEL}</div>
</div>
<div style="background:{MAY_BG};border:1.5px solid {MAY_BORDER};border-radius:12px;
    padding:14px 16px;text-align:center;">
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;
    font-size:1.6rem;color:{MAY_FG};">{n_may}</div>
<div style="font-size:0.78rem;color:{MAY_FG};margin-top:2px;opacity:.85;">
{MAY_ICON} {MAY_LABEL}</div>
</div>
<div style="background:{NO_MATCH_BG};border:1.5px solid {NO_MATCH_BORDER};border-radius:12px;
    padding:14px 16px;text-align:center;">
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;
    font-size:1.6rem;color:{NO_MATCH_FG};">{n_none}</div>
<div style="font-size:0.78rem;color:{NO_MATCH_FG};margin-top:2px;opacity:.85;">
{NO_MATCH_ICON} No Match</div>
</div>
</div>
""")

    # Filters
    try:
        profiles = get_profiles()
    except Exception as exc:
        st.error(f"Could not load profiles: {exc}")
        return

    profile_options = {"All Profiles": None} | {p.name: p.id for p in profiles}
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        selected_profile_name = st.selectbox(
            "👤 Filter By Profile", list(profile_options.keys()), key="hist_profile_filter"
        )
    with col_f2:
        status_options = {
            "All Statuses": None,
            f"{PRESENT_ICON} {PRESENT_LABEL}": STATUS_PRESENT,
            f"{MAY_ICON} {MAY_LABEL}": STATUS_MAY_CONTAIN,
            f"{UNCERTAIN_ICON} {UNCERTAIN_LABEL}": STATUS_UNCERTAIN,
            f"{NO_MATCH_ICON} No Match": STATUS_NO_MATCH,
        }
        selected_status_label = st.selectbox(
            "🏷️ Filter By Status", list(status_options.keys()), key="hist_status_filter"
        )

    profile_id_filter = profile_options[selected_profile_name]
    status_filter = status_options[selected_status_label]

    try:
        entries = get_history(profile_id=profile_id_filter, status_filter=status_filter)
    except Exception as exc:
        st.error(f"Could not load history: {exc}")
        return

    if not entries:
        render_html(f"""
<div class="fade-up" style="background:{TINT};border:1.5px solid {BORDER_TINT};
    border-radius:14px;padding:40px 24px;text-align:center;margin-top:24px;">
<div style="font-size:2.5rem;margin-bottom:12px;">📭</div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;
    font-size:1.1rem;color:{DARK_CHERRY};margin-bottom:6px;">No history yet</div>
<div style="font-size:0.875rem;color:{TEXT_MUTED};">
Run a check on the Check page and it will appear here.
</div>
</div>
""")
        return

    render_html(f"""
<div style="font-size:0.82rem;color:{TEXT_MUTED};margin-bottom:12px;">
<strong style="color:{CHERRY};">{len(entries)}</strong>
entr{'y' if len(entries) == 1 else 'ies'} found
</div>
""")
    st.divider()

    for entry in entries:
        bg, border, status_label, fg = _STATUS_META.get(
            entry.summary_status, (WHITE, BORDER_TINT, entry.summary_status, TEXT_DARK)
        )
        try:
            dt = datetime.fromisoformat(entry.timestamp)
            ts_display = dt.strftime("%d %b %Y, %H:%M UTC")
        except Exception:
            ts_display = entry.timestamp

        snippet = entry.ingredient_text[:130].replace("\n", " ")
        if len(entry.ingredient_text) > 130:
            snippet += "…"

        render_html(f"""
<div class="fade-up" style="background:{WHITE};border-radius:12px;
    border:1.5px solid {border};box-shadow:0 2px 8px rgba(210,4,45,.06);
    overflow:hidden;margin-bottom:4px;">
<div style="background:{bg};padding:10px 16px;
    display:flex;justify-content:space-between;align-items:center;
    flex-wrap:wrap;gap:8px;border-bottom:1px solid {border};">
<div style="display:flex;align-items:center;gap:10px;">
<span style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:600;
    font-size:0.875rem;color:{fg if bg != WHITE else TEXT_DARK};">{ts_display}</span>
<span style="font-size:0.78rem;color:{fg if bg != WHITE else TEXT_MUTED};">
👤 {entry.profile_name}</span>
</div>
<span style="background:rgba(0,0,0,.18);color:{fg};border-radius:20px;
    padding:3px 13px;font-size:0.78rem;font-weight:700;">
{status_label}</span>
</div>
<div style="padding:10px 16px 12px;">
<div style="font-family:'SF Mono','Fira Code',monospace;font-size:0.8rem;
    color:{TEXT_BODY};background:{TINT};padding:8px 12px;
    border-radius:7px;border:1px solid {BORDER_TINT};
    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
{snippet}
</div>
</div>
</div>
""")

        col_a, col_b, col_c = st.columns([2, 2, 1])
        if col_a.button("↩️ Reopen", key=f"reopen_{entry.id}", use_container_width=True):
            st.session_state["reopen_text"] = entry.ingredient_text
            st.session_state["active_profile_id"] = entry.profile_id
            try:
                st.switch_page("views/check.py")
            except Exception:
                st.info("Switch to the **Check** page to see the reopened ingredients.")

        try:
            match_results = _parse_results(entry.results_json)
            try:
                dt = datetime.fromisoformat(entry.timestamp)
                ts_str = dt.strftime("%Y-%m-%d %H:%M UTC")
            except Exception:
                ts_str = entry.timestamp
            pdf_bytes = generate_pdf(
                profile_name=entry.profile_name,
                timestamp=ts_str,
                ingredient_text=entry.ingredient_text,
                match_results=match_results,
                summary_status=entry.summary_status,
            )
            col_b.download_button(
                label="📄 Download PDF",
                data=pdf_bytes,
                file_name=f"report_{entry.id}.pdf",
                mime="application/pdf",
                key=f"pdf_{entry.id}",
                use_container_width=True,
            )
        except Exception as exc:
            col_b.caption(f"PDF error: {exc}")

        if col_c.button("🗑️", key=f"delete_{entry.id}", help="Delete this entry", use_container_width=True):
            try:
                delete_history_entry(entry.id)
                st.rerun()
            except Exception as exc:
                st.error(f"Could not delete entry: {exc}")

        st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

    render_html(f"""
<div style="background:#1F2937;border-radius:14px;padding:20px 28px;
    margin-top:32px;display:flex;justify-content:space-between;
    align-items:center;flex-wrap:wrap;gap:12px;">
<div style="font-size:0.8rem;color:#9CA3AF;">
🥛 <strong style="color:#fff;">Food Allergy Ingredient Checker</strong> ·
History stored locally in SQLite
</div>
<div style="font-size:0.75rem;color:#6B7280;">
⚠️ Always read the original product label before consuming.
</div>
</div>
<div style="height:24px;"></div>
""")
