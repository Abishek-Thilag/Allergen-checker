---
inclusion: always
---

# Tech Steering — Food Allergy Ingredient Checker

## Language and runtime

- Python 3.10+
- No async; all operations are synchronous (Streamlit runs in a single thread per user).

## Framework

- **Streamlit** for the UI. Use `st.set_page_config`, `st.session_state`, `st.columns`, `st.container`, `st.markdown` with `unsafe_allow_html=True` for highlighted ingredient text.
- Multi-page layout via the `pages/` directory (Streamlit native multipage).

## Core dependencies (pinned in requirements.txt)

| Package | Purpose |
|---|---|
| streamlit | UI framework |
| pytesseract | OCR wrapper for Tesseract |
| Pillow | Image handling for OCR preprocessing |
| rapidfuzz | Fuzzy string matching |
| fpdf2 | PDF report generation |
| pytest | Testing framework |

No other third-party packages should be introduced without a DECISIONS.md entry explaining the choice.

## Database

- **SQLite** via the standard library `sqlite3` module (no ORM).
- DB file: `allergy_checker.db` in the project root.
- All DB access goes through `core/db.py`. No raw SQL in UI code.

## Data files

- `data/allergens.json` and `data/ins_codes.json` are loaded once and cached in `st.session_state`.
- Sample labels are plain `.txt` files in `data/samples/`.

## Architecture rules

- **`core/` modules must not import Streamlit.** They are pure Python and independently testable.
- **No global mutable state outside of `core/db.py`** (which is stateful by nature).
- **All matching is deterministic.** No LLM or probabilistic external service is called at runtime.
- Session state keys are documented in `design.md` and must not be invented ad hoc.

## Error handling

- Use `try/except` at the boundary between `core/` and the UI layer. Let core functions raise exceptions; catch them in the page files and convert to `st.error()` or `st.warning()`.
- Never silently swallow exceptions. Log to stderr if not surfaced in the UI.

## Testing

- Test runner: `pytest`
- Test files in `tests/` directory, one file per core module.
- All tests are offline (no network, no Tesseract required except in OCR tests which mock pytesseract).
- Coverage target: every matching logic path, every status (PRESENT, MAY_CONTAIN, UNCERTAIN, no-match), every INS format, every error condition.

## Styling

- Colour theme set in `.streamlit/config.toml` (do not hardcode theme colours in Python).
- Status colours (red/orange/amber/blue) are defined as constants in a shared `core/constants.py` file and referenced from there.
- Never use inline `st.markdown` CSS for layout that should be in config.toml.

## INS code policy

- Only include INS codes verifiable against FSSAI Food Additives Regulations 2011 or Codex Alimentarius GSFA.
- Every entry in `ins_codes.json` must have a non-empty `source` field citing the document.
- If a code's allergen source is variable, `variable_source` must be `true` and the result must be UNCERTAIN — never PRESENT.


## UI rendering rule (added)

- **All multi-line HTML strings must go through `core/ui.render_html()`**, never directly to `st.markdown`. This prevents Streamlit's CommonMark parser from treating indented lines as code blocks.
- Page content lives in `views/` not `pages/`. Navigation is wired via `st.navigation` in `app.py`.
- `st.set_page_config` is called exactly once, in `app.py`.
