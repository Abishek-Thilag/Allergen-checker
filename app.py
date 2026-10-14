"""
app.py — Streamlit entry point for the Food Allergy Ingredient Checker.

Responsibilities:
  - st.set_page_config (only here, nowhere else)
  - Global CSS via core/ui.apply_theme()
  - Data + DB init into session_state
  - st.navigation with titled pages (Home / Check / History / About)

Page content lives in views/. HTML is always rendered through render_html()
in core/ui.py to prevent indentation-as-code-block issues.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import streamlit as st

# ── Page config — MUST be the very first Streamlit call ──────────────────────
st.set_page_config(
    page_title="Allergy Checker",
    page_icon="🥛",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# ── Theme injection ───────────────────────────────────────────────────────────
from core.ui import apply_theme
apply_theme()

# ── Data loading ──────────────────────────────────────────────────────────────
DATA_DIR = ROOT / "data"


@st.cache_data(show_spinner=False)
def _load_allergen_data() -> dict:
    path = DATA_DIR / "allergens.json"
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Data file missing: {path.name}. Please reinstall the app.")
        st.stop()
    except json.JSONDecodeError as exc:
        st.error(f"Could not read data file: {path.name}. ({exc})")
        st.stop()


@st.cache_data(show_spinner=False)
def _load_ins_data() -> dict:
    path = DATA_DIR / "ins_codes.json"
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Data file missing: {path.name}. Please reinstall the app.")
        st.stop()
    except json.JSONDecodeError as exc:
        st.error(f"Could not read data file: {path.name}. ({exc})")
        st.stop()


if "allergen_data" not in st.session_state:
    st.session_state["allergen_data"] = _load_allergen_data()
if "ins_data" not in st.session_state:
    st.session_state["ins_data"] = _load_ins_data()

# ── DB init ───────────────────────────────────────────────────────────────────
if "db_initialised" not in st.session_state:
    try:
        from core.db import init_db
        init_db()
        st.session_state["db_initialised"] = True
    except Exception as exc:
        st.error(f"Could not initialise the database: {exc}")
        st.stop()

# ── Session state defaults ────────────────────────────────────────────────────
_defaults = {
    "active_profile_id": None,
    "last_results": None,
    "last_ingredient_text": "",
    "reopen_text": "",
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Auto-select first profile ─────────────────────────────────────────────────
if st.session_state["active_profile_id"] is None:
    try:
        from core.db import get_profiles
        profiles = get_profiles()
        if profiles:
            st.session_state["active_profile_id"] = profiles[0].id
    except Exception:
        pass

# ── Navigation ────────────────────────────────────────────────────────────────
# st.Page wraps each view module. The title= kwarg controls the sidebar label.
# Pages are NOT in pages/ so Streamlit's auto-detect doesn't run.

import views.home as _home
import views.check as _check
import views.history as _history
import views.about as _about
import views.sidebar as _sidebar

_sidebar.render_sidebar()

pg = st.navigation([
    st.Page(lambda: _home.show(),    title="Home",    icon="🏠", url_path="home",    default=True),
    st.Page(lambda: _check.show(),   title="Check",   icon="🔍", url_path="check"),
    st.Page(lambda: _history.show(), title="History", icon="🕘", url_path="history"),
    st.Page(lambda: _about.show(),   title="About",   icon="ℹ️", url_path="about"),
])
pg.run()
