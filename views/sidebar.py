"""
views/sidebar.py — Global sidebar content for all pages.

Rendered below Streamlit's page navigation.
Theme: Cherry red (#D20A2E), dark cherry (#8F0720), tint (#FCE8EB), white (#FFFFFF).
Cards are white with a cherry left border and rounded corners.
"""
from __future__ import annotations
import sys
from datetime import datetime
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from core.constants import (
    SEVERITY_MILD, SEVERITY_MODERATE, SEVERITY_SEVERE,
    STATUS_PRESENT, STATUS_MAY_CONTAIN, STATUS_UNCERTAIN, STATUS_NO_MATCH,
)
from core.db import (
    get_profiles, create_profile, delete_profile,
    get_allergens_for_profile, add_allergen_to_profile, remove_allergen_from_profile,
    get_history,
)
from core.ui import (
    render_html,
    CHERRY, DARK_CHERRY, DEEP_CHERRY, TINT, WHITE,
    TEXT_DARK, TEXT_BODY, TEXT_MUTED, BORDER_TINT,
    PRESENT_FG, PRESENT_BG, PRESENT_BORDER, PRESENT_ICON, PRESENT_LABEL,
    MAY_FG, MAY_BG, MAY_BORDER, MAY_ICON, MAY_LABEL,
    UNCERTAIN_FG, UNCERTAIN_BG, UNCERTAIN_BORDER, UNCERTAIN_ICON, UNCERTAIN_LABEL,
    NOT_RECOGNISED_FG, NOT_RECOGNISED_BG, NOT_RECOGNISED_BORDER, NOT_RECOGNISED_ICON, NOT_RECOGNISED_LABEL,
)

STANDARD_ALLERGENS = [
    "milk", "peanut", "egg", "wheat", "tree nuts",
    "soy", "fish", "shellfish", "sesame", "mustard",
]

_SEVERITY_META = {
    SEVERITY_SEVERE:   (PRESENT_FG, PRESENT_BG, "🔴"),
    SEVERITY_MODERATE: (MAY_FG,     MAY_BG,     "🟠"),
    SEVERITY_MILD:     (UNCERTAIN_FG, UNCERTAIN_BG, "🟡"),
}

TIPS_OF_THE_DAY = [
    ("Check the original label", "Formulations and factory lines change without notice. Always verify physical packaging."),
    ("\"No known match found\" does not mean \"safe\"", "It means no configured allergens were detected in recognised text. Undeclared cross-contact may exist."),
    ("OCR can misread text", "Curvature, glare, and low contrast can cause OCR errors. Always verify extracted words."),
    ("Severe allergens deserve extra care", "If you or your family have anaphylactic allergies, never rely solely on an automated scanner."),
]


def render_sidebar() -> None:
    """Render the global compact sidebar below the page navigation."""
    allergen_data = st.session_state.get("allergen_data", {})

    # ── 1. App Brand Block ────────────────────────────────────────────────────
    with st.sidebar:
        render_html(f"""
<div class="sidebar-card" style="background:{WHITE};border-left:4px solid {CHERRY};border-top:1px solid {BORDER_TINT};border-right:1px solid {BORDER_TINT};border-bottom:1px solid {BORDER_TINT};border-radius:10px;padding:10px 12px;margin-bottom:8px;box-shadow:0 2px 6px rgba(210,10,46,.04);">
<div style="display:flex;align-items:center;gap:10px;">
<span style="font-size:1.6rem;line-height:1;">🥛</span>
<div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:1.02rem;color:{DARK_CHERRY};line-height:1.2;">
Allergy Checker
</div>
<div style="font-size:0.72rem;color:{TEXT_MUTED};line-height:1.3;margin-top:2px;">
Spot hidden allergens in Indian food labels
</div>
</div>
</div>
</div>
""")

        # ── 2. Active Profile Card ────────────────────────────────────────────
        profiles = []
        try:
            profiles = get_profiles()
        except Exception:
            profiles = []

        active_id = st.session_state.get("active_profile_id")
        if profiles and (active_id is None or not any(p.id == active_id for p in profiles)):
            active_id = profiles[0].id
            st.session_state["active_profile_id"] = active_id

        profile_names = [p.name for p in profiles]
        current_idx = next((i for i, p in enumerate(profiles) if p.id == active_id), 0) if profiles else 0

        render_html(f"""
<div class="sidebar-card" style="background:{WHITE};border-left:4px solid {CHERRY};border-top:1px solid {BORDER_TINT};border-right:1px solid {BORDER_TINT};border-bottom:1px solid {BORDER_TINT};border-radius:10px;padding:10px 12px;margin-bottom:8px;box-shadow:0 2px 6px rgba(210,10,46,.04);">
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;font-size:0.76rem;color:{DARK_CHERRY};text-transform:uppercase;letter-spacing:.05em;">
👤 Active Profile
</div>
<span style="background:{TINT};color:{DARK_CHERRY};font-size:0.68rem;font-weight:700;border-radius:6px;padding:2px 6px;">
{len(profiles)} Saved
</span>
</div>
""")

        if profiles:
            selected_name = st.selectbox(
                "Select Active Profile",
                profile_names,
                index=current_idx,
                key="sb_profile_selector",
                label_visibility="collapsed",
            )
            selected_prof = next((p for p in profiles if p.name == selected_name), profiles[0])
            if selected_prof.id != active_id:
                st.session_state["active_profile_id"] = selected_prof.id
                st.rerun()

            active_allergens = get_allergens_for_profile(selected_prof.id)
            n_allergens = len(active_allergens)

            render_html(f"""
<div style="font-size:0.75rem;font-weight:600;color:{TEXT_BODY};margin:6px 0 4px;">
Tracking {n_allergens} allergen{'s' if n_allergens != 1 else ''}:
</div>
""")
            if active_allergens:
                chips_html = []
                for a in active_allergens:
                    fg, bg, dot = _SEVERITY_META.get(a.severity, (TEXT_MUTED, "#F3F4F6", "⚪"))
                    emoji = allergen_data.get(a.allergen, {}).get("emoji", "⚠️")
                    chips_html.append(
                        f"<span style='background:{bg};color:{fg};border-radius:12px;padding:2px 7px;font-size:0.68rem;font-weight:700;display:inline-flex;align-items:center;gap:3px;margin:2px 1px;'>"
                        f"{emoji} {a.allergen} ({a.severity})</span>"
                    )
                render_html(f"""<div style="display:flex;flex-wrap:wrap;gap:3px;margin-top:2px;">{''.join(chips_html)}</div>""")
            else:
                render_html(f"""<div style="font-size:0.72rem;color:{TEXT_MUTED};font-style:italic;">No allergens added yet. Open controls below to add.</div>""")
        else:
            render_html(f"""<div style="font-size:0.75rem;color:{DARK_CHERRY};">No profiles found. Create one below.</div>""")

        render_html("</div>")

        # ── 3. Quick Manage Controls Expander ─────────────────────────────────
        with st.expander("⚙️ Manage Profiles & Allergens", expanded=False):
            if active_id:
                active_allergens = get_allergens_for_profile(active_id)
                existing_names = {a.allergen.lower() for a in active_allergens}

                st.markdown(f"<div style='font-size:0.78rem;font-weight:700;color:{DARK_CHERRY};margin-bottom:4px;'>➕ Add Allergen</div>", unsafe_allow_html=True)
                available_std = [a for a in STANDARD_ALLERGENS if a.lower() not in existing_names]
                add_mode = st.radio("Add Mode", ["Standard", "Custom"], horizontal=True, key="sb_add_mode", label_visibility="collapsed")
                if add_mode == "Standard":
                    if available_std:
                        chosen_allergen = st.selectbox("Choose Allergen", available_std, key="sb_std_choice")
                    else:
                        chosen_allergen = None
                        st.caption("All 10 standard allergens already added.")
                else:
                    chosen_allergen = st.text_input("Custom Allergen", placeholder="e.g. celery, kiwi", key="sb_custom_choice")

                chosen_sev = st.selectbox("Severity", [SEVERITY_MODERATE, SEVERITY_SEVERE, SEVERITY_MILD], key="sb_sev_choice")
                if st.button("Add to Profile", key="sb_btn_add_allergen", type="primary", use_container_width=True):
                    if not chosen_allergen or not chosen_allergen.strip():
                        st.error("Please specify an allergen name.")
                    else:
                        try:
                            add_allergen_to_profile(active_id, chosen_allergen.strip().lower(), chosen_sev)
                            st.success(f"Added {chosen_allergen.strip()}")
                            st.rerun()
                        except Exception as exc:
                            st.error(str(exc))

                if active_allergens:
                    st.markdown(f"<div style='font-size:0.78rem;font-weight:700;color:{DARK_CHERRY};margin:10px 0 4px;'>🗑️ Remove Allergen</div>", unsafe_allow_html=True)
                    rem_choice = st.selectbox("Remove", [a.allergen for a in active_allergens], key="sb_rem_choice", label_visibility="collapsed")
                    if st.button("Remove Allergen", key="sb_btn_rem_allergen", use_container_width=True):
                        try:
                            remove_allergen_from_profile(active_id, rem_choice)
                            st.rerun()
                        except Exception as exc:
                            st.error(str(exc))

            st.markdown(f"<div style='font-size:0.78rem;font-weight:700;color:{DARK_CHERRY};margin:10px 0 4px;'>👤 New Profile</div>", unsafe_allow_html=True)
            new_p_name = st.text_input("Profile Name", placeholder="e.g. Kid, Grandpa", key="sb_new_prof_name", label_visibility="collapsed")
            if st.button("Create Profile", key="sb_btn_create_prof", use_container_width=True):
                if not new_p_name.strip():
                    st.error("Name cannot be empty.")
                else:
                    try:
                        new_id = create_profile(new_p_name.strip())
                        st.session_state["active_profile_id"] = new_id
                        st.success(f"Profile '{new_p_name.strip()}' created!")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

        # ── 4. Quick Stats Card ───────────────────────────────────────────────
        all_history = []
        try:
            all_history = get_history(limit=500)
        except Exception:
            all_history = []

        total_checks = len(all_history)
        n_profiles = len(profiles)

        last_check_str = "None yet"
        if all_history:
            try:
                dt = datetime.fromisoformat(all_history[0].timestamp.replace("Z", "+00:00"))
                last_check_str = dt.strftime("%b %d, %H:%M")
            except Exception:
                last_check_str = all_history[0].timestamp[:16]

        render_html(f"""
<div class="sidebar-card" style="background:{WHITE};border-left:4px solid {CHERRY};border-top:1px solid {BORDER_TINT};border-right:1px solid {BORDER_TINT};border-bottom:1px solid {BORDER_TINT};border-radius:10px;padding:10px 12px;margin-bottom:8px;box-shadow:0 2px 6px rgba(210,10,46,.04);">
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;font-size:0.76rem;color:{DARK_CHERRY};text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px;">
📊 Quick Stats
</div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:6px;">
<div style="background:{TINT};padding:6px 8px;border-radius:6px;text-align:center;">
<div style="font-size:0.68rem;color:{TEXT_MUTED};">Total Checks</div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:1.05rem;color:{DARK_CHERRY};line-height:1.1;">{total_checks}</div>
</div>
<div style="background:{TINT};padding:6px 8px;border-radius:6px;text-align:center;">
<div style="font-size:0.68rem;color:{TEXT_MUTED};">Profiles</div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:1.05rem;color:{DARK_CHERRY};line-height:1.1;">{n_profiles}</div>
</div>
</div>
<div style="font-size:0.72rem;color:{TEXT_MUTED};display:flex;justify-content:space-between;border-top:1px solid {BORDER_TINT};padding-top:4px;">
<span>Last check:</span>
<strong style="color:{TEXT_DARK};">{last_check_str}</strong>
</div>
</div>
""")

        # ── 5. Status Legend ──────────────────────────────────────────────────
        render_html(f"""
<div class="sidebar-card" style="background:{WHITE};border-left:4px solid {CHERRY};border-top:1px solid {BORDER_TINT};border-right:1px solid {BORDER_TINT};border-bottom:1px solid {BORDER_TINT};border-radius:10px;padding:10px 12px;margin-bottom:8px;box-shadow:0 2px 6px rgba(210,10,46,.04);">
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;font-size:0.76rem;color:{DARK_CHERRY};text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px;">
🏷️ Status Legend
</div>
<div style="display:flex;flex-direction:column;gap:4px;">
<div style="display:flex;align-items:center;justify-content:space-between;background:#FFF0F2;border:1px solid {PRESENT_BORDER};border-radius:6px;padding:3px 8px;">
<span style="font-size:0.72rem;font-weight:700;color:{PRESENT_BG};">{PRESENT_ICON} {PRESENT_LABEL}</span>
<span style="font-size:0.68rem;color:{TEXT_MUTED};">Confirmed match</span>
</div>
<div style="display:flex;align-items:center;justify-content:space-between;background:#FFF7ED;border:1px solid {MAY_BORDER};border-radius:6px;padding:3px 8px;">
<span style="font-size:0.72rem;font-weight:700;color:{MAY_BG};">{MAY_ICON} {MAY_LABEL}</span>
<span style="font-size:0.68rem;color:{TEXT_MUTED};">Cross-contamination</span>
</div>
<div style="display:flex;align-items:center;justify-content:space-between;background:#FEFCE8;border:1px solid {UNCERTAIN_BORDER};border-radius:6px;padding:3px 8px;">
<span style="font-size:0.72rem;font-weight:700;color:#713F12;">{UNCERTAIN_ICON} {UNCERTAIN_LABEL}</span>
<span style="font-size:0.68rem;color:{TEXT_MUTED};">Vague additive</span>
</div>
<div style="display:flex;align-items:center;justify-content:space-between;background:{NOT_RECOGNISED_BG};border:1px solid {NOT_RECOGNISED_BORDER};border-radius:6px;padding:3px 8px;">
<span style="font-size:0.72rem;font-weight:700;color:{NOT_RECOGNISED_FG};">{NOT_RECOGNISED_ICON} {NOT_RECOGNISED_LABEL}</span>
<span style="font-size:0.68rem;color:{TEXT_MUTED};">Unindexed term</span>
</div>
</div>
</div>
""")

        # ── 6. Tip of the Day ─────────────────────────────────────────────────
        tip_idx = (int(datetime.now().timestamp()) // 3600) % len(TIPS_OF_THE_DAY)
        tip_title, tip_text = TIPS_OF_THE_DAY[tip_idx]

        render_html(f"""
<div class="sidebar-card" style="background:{WHITE};border-left:4px solid {CHERRY};border-top:1px solid {BORDER_TINT};border-right:1px solid {BORDER_TINT};border-bottom:1px solid {BORDER_TINT};border-radius:10px;padding:10px 12px;margin-bottom:8px;box-shadow:0 2px 6px rgba(210,10,46,.04);">
<div style="display:flex;align-items:center;gap:6px;margin-bottom:3px;">
<span style="font-size:0.88rem;">💡</span>
<span style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;font-size:0.76rem;color:{DARK_CHERRY};text-transform:uppercase;letter-spacing:.05em;">
Tip of the Day
</span>
</div>
<div style="font-size:0.73rem;color:{TEXT_BODY};line-height:1.4;">
<strong>{tip_title}</strong>: {tip_text}
</div>
</div>
""")

        # ── 7. Disclaimer at the Bottom ───────────────────────────────────────
        render_html(f"""
<div style="background:{TINT};border:1px solid {BORDER_TINT};border-radius:8px;padding:8px 10px;font-size:0.7rem;color:{TEXT_MUTED};line-height:1.35;text-align:center;">
⚠️ An aid, not medical advice. Always read the original label.
</div>
""")
