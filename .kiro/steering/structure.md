---
inclusion: always
---

# Structure Steering — Food Allergy Ingredient Checker

## Project layout

```
projk/
├── app.py                        # Streamlit entry point
├── pages/
│   ├── check.py                  # Check page (main feature)
│   ├── history.py                # History page
│   └── about.py                  # About / limitations / disclaimer page
├── core/
│   ├── __init__.py
│   ├── constants.py              # Status strings, colours, vague ingredients list
│   ├── parser.py                 # Text parsing (pure)
│   ├── matcher.py                # Allergen matching (pure)
│   ├── ins_decoder.py            # INS/E-code decoding (pure)
│   ├── ocr.py                    # pytesseract wrapper
│   ├── report.py                 # PDF generation (fpdf2)
│   └── db.py                     # SQLite access layer
├── data/
│   ├── allergens.json            # Allergen synonym dictionary
│   ├── ins_codes.json            # INS/E-number decoder
│   └── samples/
│       ├── sample_01_biscuit.txt
│       ├── sample_02_namkeen.txt
│       ├── sample_03_instant_noodles.txt
│       ├── sample_04_chocolate.txt   ← DEMO scenario
│       ├── sample_05_dairy_product.txt
│       ├── sample_06_snack_bar.txt
│       ├── sample_07_ready_meal.txt
│       ├── sample_08_bread.txt
│       ├── sample_09_sauce.txt
│       └── sample_10_breakfast_cereal.txt
├── tests/
│   ├── __init__.py
│   ├── test_parser.py
│   ├── test_ins_decoder.py
│   ├── test_matcher.py
│   ├── test_db.py
│   ├── test_report.py
│   └── test_ocr.py
├── .streamlit/
│   └── config.toml
├── allergy_checker.db            # Created at runtime (gitignore)
├── requirements.txt
├── README.md
└── DECISIONS.md
```

## Naming conventions

- Module files: `snake_case.py`
- Classes: `PascalCase`
- Functions: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- JSON keys: `snake_case`
- SQLite table and column names: `snake_case`
- Streamlit session state keys: `snake_case`

## File responsibility rules

| File | Allowed imports |
|---|---|
| `core/*.py` | Standard library, rapidfuzz, fpdf2, sqlite3, Pillow, pytesseract — **NO streamlit** |
| `pages/*.py` | streamlit, core/*, standard library |
| `app.py` | streamlit, core/*, standard library |
| `tests/*.py` | pytest, core/*, standard library, unittest.mock |

## Data contracts (TypedDicts / dataclasses)

All cross-module data structures are defined in `core/constants.py` or in the module that owns them and imported where needed. Do not re-define the same structure in multiple places.

Key types:
- `ParseResult` — owned by `core/parser.py`
- `InsDecodeResult` — owned by `core/ins_decoder.py`
- `MatchedTerm`, `MatchResult` — owned by `core/matcher.py`
- `AllergenEntry`, `Profile`, `HistoryEntry` — owned by `core/db.py`
- `OcrResult` — owned by `core/ocr.py`

## What goes in `core/constants.py`

- `STATUS_PRESENT`, `STATUS_MAY_CONTAIN`, `STATUS_UNCERTAIN`, `STATUS_NO_MATCH`
- `COLOUR_PRESENT`, `COLOUR_MAY_CONTAIN`, `COLOUR_UNCERTAIN`, `COLOUR_NO_MATCH`
- `SEVERITY_MILD`, `SEVERITY_MODERATE`, `SEVERITY_SEVERE`
- `VAGUE_INGREDIENTS` — list of ingredient terms that trigger UNCERTAIN
- `TRACE_PATTERNS` — regex patterns for "may contain" and facility statements
- `DEFAULT_FUZZY_THRESHOLD`
- `MAX_IMAGE_BYTES`
- `DISCLAIMER_TEXT`

## gitignore entries

- `allergy_checker.db`
- `__pycache__/`
- `.pytest_cache/`
- `*.pyc`
- `.streamlit/secrets.toml` (if ever added)


## Views directory (added)

Page content has been moved from `pages/` to `views/` so that Streamlit's file-based auto-detection does not run. Navigation is managed explicitly via `st.navigation` in `app.py`.

```
views/
  home.py     — Landing page (show())
  check.py    — Check page (show())
  history.py  — History page (show())
  about.py    — About page (show())
```

`core/ui.py` owns the `render_html()` helper and the cherry-red palette constants. No other file may define palette values.
