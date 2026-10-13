# Design — Food Allergy Ingredient Checker

## Architecture Overview

The app is a single-user, local Streamlit application. There are no external API calls at runtime. All state is stored in SQLite. Matching logic lives entirely in `core/` and has no Streamlit dependency, making it independently testable.

```
┌───────────────────────────────────────────────────────┐
│                     Streamlit UI                       │
│  app.py  │  pages/check.py  │  pages/history.py       │
│          │  pages/about.py                             │
└────────────────────┬──────────────────────────────────┘
                     │ calls
┌────────────────────▼──────────────────────────────────┐
│                    core/                               │
│  parser.py   matcher.py   ins_decoder.py               │
│  ocr.py      report.py    db.py                        │
└────────────────────┬──────────────────────────────────┘
                     │ reads
┌────────────────────▼──────────────────────────────────┐
│                    data/                               │
│  allergens.json    ins_codes.json    samples/          │
└───────────────────────────────────────────────────────┘
                     │ persists
┌────────────────────▼──────────────────────────────────┐
│              allergy_checker.db (SQLite)               │
└───────────────────────────────────────────────────────┘
```

---

## Data Layer

### `data/allergens.json`

Top-level keys are canonical allergen names. Each value is an object:

```json
{
  "milk": {
    "emoji": "🥛",
    "synonyms": [
      { "term": "whey",        "explanation": "whey is a milk protein fraction" },
      { "term": "casein",      "explanation": "casein is the primary milk protein" },
      { "term": "caseinate",   "explanation": "caseinate is a salt of casein (milk protein)" },
      { "term": "lactose",     "explanation": "lactose is the sugar found in milk" },
      { "term": "lactalbumin", "explanation": "lactalbumin is a milk whey protein" },
      { "term": "milk solids", "explanation": "milk solids contain milk proteins and lactose" },
      { "term": "milk powder", "explanation": "milk powder is dried whole or skimmed milk" },
      { "term": "butter",      "explanation": "butter is made from milk cream" },
      { "term": "ghee",        "explanation": "ghee is clarified butter, a milk derivative" },
      { "term": "curd",        "explanation": "curd (dahi) is fermented milk" },
      { "term": "dahi",        "explanation": "dahi is the Indian term for curd (fermented milk)" },
      { "term": "paneer",      "explanation": "paneer is a fresh milk cheese" },
      { "term": "khoya",       "explanation": "khoya is reduced whole milk used in Indian sweets" }
    ]
  }
}
```

### `data/ins_codes.json`

Top-level keys are INS numbers as strings. Each entry stores:

```json
{
  "322": {
    "name": "Lecithin",
    "possible_allergens": ["soy", "egg"],
    "variable_source": true,
    "explanation": "INS 322 is lecithin, which can be derived from soy, egg yolk, or sunflower. The source is not always declared.",
    "source": "Codex Alimentarius GSFA; FSSAI Food Additives Regulations 2011"
  },
  "471": {
    "name": "Mono- and diglycerides of fatty acids",
    "possible_allergens": [],
    "variable_source": false,
    "explanation": "INS 471 is mono- and diglycerides of fatty acids, generally of vegetable origin. No confirmed allergen link.",
    "source": "Codex Alimentarius GSFA"
  }
}
```

### `data/samples/`

Ten `.txt` files, each containing a realistic ingredient list from a common Indian packaged food category (biscuit, namkeen, instant noodles, chocolate, dairy product, snack bar, ready-to-eat meal, bread, sauce, breakfast cereal). The demo scenario file contains "casein", "whey", "INS 322", and "natural flavours" without ever writing "milk" or "soy".

---

## Core Modules

### `core/parser.py`

```
parse_ingredients(text: str) -> list[str]
```

1. Lowercase the entire text.
2. Detect and extract trace/facility statements (regex patterns for "may contain", "manufactured in a facility") → stored separately as `trace_statements`.
3. Remove parenthetical sub-lists from the main token stream but add their contents as additional tokens (handles nesting one level deep).
4. Split on `,`, `;`, `(`, `)`, `[`, `]`.
5. Strip whitespace from each token; discard empty strings.
6. Return `ParseResult(tokens: list[str], trace_statements: list[str])`.

### `core/matcher.py`

```
match_allergens(
    parse_result: ParseResult,
    profile_allergens: list[AllergenEntry],
    allergen_data: dict,
    ins_data: dict,
    fuzzy_threshold: int = 85
) -> list[MatchResult]
```

`AllergenEntry`: `{ name: str, severity: Literal["mild","moderate","severe"] }`

`MatchResult`: `{ allergen: str, severity: str, status: Status, matched_terms: list[MatchedTerm], emoji: str }`

`MatchedTerm`: `{ term: str, explanation: str, match_type: Literal["exact","fuzzy","ins","trace","vague"] }`

`Status`: `Literal["PRESENT", "MAY_CONTAIN", "UNCERTAIN"]`

**Matching order for each token:**

1. Exact substring match against all synonyms for all profile allergens → PRESENT.
2. Fuzzy match (rapidfuzz `partial_ratio`) above threshold → PRESENT with match_type="fuzzy".
3. INS code extraction (regex `(?:INS\s*|E)(\d{3,4})|\((\d{3,4})\)`) → look up in ins_data:
   - variable_source=true → UNCERTAIN
   - variable_source=false and allergen in possible_allergens → PRESENT
4. Vague ingredient list match → UNCERTAIN.
5. Trace statement scan → MAY_CONTAIN for allergens named in the statement.

The function is **pure**: it takes data as arguments and returns results with no side effects.

### `core/ins_decoder.py`

```
extract_ins_codes(text: str) -> list[str]
decode_ins(code: str, ins_data: dict) -> InsDecodeResult | None
```

`InsDecodeResult`: `{ code: str, name: str, possible_allergens: list[str], variable_source: bool, explanation: str, source: str }`

Handles all four formats: `INS 322`, `INS322`, `E322`, `(322)`.

### `core/ocr.py`

```
extract_text_from_image(image_bytes: bytes) -> OcrResult
```

`OcrResult`: `{ text: str, confidence: float | None, error: str | None }`

Uses pytesseract. If Tesseract is not installed, returns `OcrResult(text="", error="Tesseract not found. Please install Tesseract OCR.")`. If the image cannot be read, returns a descriptive error rather than raising.

### `core/db.py`

SQLite schema (3 tables):

```sql
CREATE TABLE profiles (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);

CREATE TABLE profile_allergens (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    allergen   TEXT NOT NULL,
    severity   TEXT NOT NULL CHECK(severity IN ('mild','moderate','severe')),
    UNIQUE(profile_id, allergen)
);

CREATE TABLE history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id      INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    timestamp       TEXT NOT NULL,
    ingredient_text TEXT NOT NULL,
    results_json    TEXT NOT NULL,   -- serialised list[MatchResult]
    summary_status  TEXT NOT NULL    -- 'PRESENT' | 'MAY_CONTAIN' | 'UNCERTAIN' | 'NO_MATCH'
);
```

Functions: `create_profile`, `get_profiles`, `delete_profile`, `get_allergens_for_profile`, `set_allergens_for_profile`, `save_history`, `get_history`, `delete_history_entry`.

### `core/report.py`

```
generate_pdf(
    profile_name: str,
    timestamp: str,
    ingredient_text: str,
    match_results: list[MatchResult],
    summary_status: str
) -> bytes
```

Uses `fpdf2`. Returns raw PDF bytes for `st.download_button`. Includes disclaimer on every page footer.

---

## UI Layer

### `app.py`

- Calls `st.set_page_config`.
- Loads allergen and INS data into `st.session_state` on first run (cached).
- Initialises the DB.
- Renders navigation.

### `pages/check.py` (Check page)

Layout:
```
[Header: title + tagline]
[Sidebar: profile selector, allergen list with severity badges, profile CRUD]
[Main area]
  ├─ Input tabs: Manual | Scan | Load Sample
  ├─ [Check button]
  ├─ Risk summary banner  (shown after check)
  ├─ Highlighted ingredient text + legend
  └─ Result cards per allergen (status chip + explanation)
      └─ Download PDF button
```

### `pages/history.py` (History page)

- Filter bar: profile dropdown, status filter.
- Table of past checks: timestamp, profile, summary status, snippet.
- Actions: Reopen (sends ingredient text back to Check page via session_state) | Delete.

### `pages/about.py` (About page)

- App description.
- How it works (plain language).
- Limitations / "Not claimed" section.
- Disclaimer (large, styled).

---

## Status and Colour Coding

| Status | Hex colour | Chip label |
|---|---|---|
| PRESENT | `#D32F2F` (red) | PRESENT |
| MAY_CONTAIN | `#E65100` (deep orange) | MAY CONTAIN |
| UNCERTAIN | `#F9A825` (amber) | UNCERTAIN |
| NO_MATCH | `#1565C0` (blue) | No known match found |

Banner background:
- Red if any PRESENT, or if a severe allergen is MAY_CONTAIN.
- Amber if any MAY_CONTAIN or UNCERTAIN (no PRESENT).
- Blue/green neutral otherwise.

---

## Highlighted Ingredient Text

The ingredient text is rendered as styled HTML inside `st.markdown(..., unsafe_allow_html=True)`. Each matched token is wrapped in a `<mark>` tag with an inline background colour and a `title` attribute containing the explanation (shown as a tooltip on hover).

Overlapping matches (e.g. a token matching two allergens) are rendered with the higher-severity status colour.

---

## Fuzzy Matching Strategy

- Library: `rapidfuzz.fuzz.partial_ratio`
- Default threshold: 85 (configurable in `core/matcher.py` as a module-level constant).
- Applied to each (token, synonym) pair.
- If a fuzzy match fires, the MatchedTerm records `match_type="fuzzy"` and the explanation notes it was a fuzzy match.

---

## INS Code Handling

Because the same INS number can derive from different sources (e.g. INS 322 = lecithin from soy, egg, or sunflower), the rule is:

- `variable_source: true` → always UNCERTAIN, regardless of which allergens are in the profile.
- `variable_source: false` AND the allergen is in `possible_allergens` → PRESENT.
- `variable_source: false` AND no allergen matches → no flag.

This is the only correct behaviour: we cannot confirm presence from a code alone.

---

## Error Handling Matrix

| Condition | Response |
|---|---|
| Empty ingredient text | Show `st.error("Please enter an ingredient list.")` |
| Image not JPG/PNG | Show `st.error("Unsupported format. Upload a JPG or PNG image.")` |
| Image > 10 MB | Show `st.error("Image too large. Maximum size is 10 MB.")` |
| Tesseract not installed | Show `st.warning("OCR unavailable: Tesseract not found. You can still type ingredients manually.")` |
| OCR returns blank text | Show `st.warning("OCR could not extract text from this image. Please type the ingredients manually.")` |
| No active profile | Show `st.error("Please create a profile and add at least one allergen.")` |
| Duplicate profile name | Show `st.error("A profile with that name already exists.")` |
| Missing data file | Show `st.error("Data file missing: <filename>. Please reinstall the app.")` |
| Corrupt JSON | Show `st.error("Could not read data file: <filename>. File may be corrupted.")` |

---

## Session State Keys

| Key | Type | Purpose |
|---|---|---|
| `active_profile_id` | int | Currently selected profile |
| `last_results` | list[MatchResult] | Results of the last check |
| `last_ingredient_text` | str | Ingredient text used in last check |
| `reopen_text` | str | Text injected by History "Reopen" action |
| `allergen_data` | dict | Loaded allergens.json (cached) |
| `ins_data` | dict | Loaded ins_codes.json (cached) |

---

## Configuration

`.streamlit/config.toml`:

```toml
[theme]
primaryColor        = "#E65100"
backgroundColor     = "#FAFAFA"
secondaryBackgroundColor = "#F0F4F8"
textColor           = "#212121"
font                = "sans serif"
```

---

## Build Order

1. Data files (`allergens.json`, `ins_codes.json`, `samples/`) + `core/parser.py` + `core/matcher.py` + `core/ins_decoder.py` + `tests/`.
2. Check page with manual input, result banner, highlighting.
3. Profile management + SQLite (`core/db.py`).
4. INS decoder integration.
5. History page (`pages/history.py`) + PDF report (`core/report.py`).
6. OCR scan (`core/ocr.py`).
7. UI polish, `README.md`, `DECISIONS.md`.

---

## UI Architecture Update (cherry theme + navigation refactor)

### render_html() — root cause fix

Streamlit's CommonMark parser runs before HTML parsing. Any line beginning with 4+ spaces is treated as a fenced code block, so indented HTML inside triple-quoted Python strings renders as raw text. `core/ui.render_html()` fixes this by stripping all leading whitespace from every line before calling `st.markdown`.

### Navigation structure

```
app.py                  ← set_page_config + apply_theme + DB init + st.navigation
views/
  home.py               ← show()  — landing / home page
  check.py              ← show()  — ingredient check
  history.py            ← show()  — check history
  about.py              ← show()  — about / disclaimer
pages/                  ← kept for backwards compat, no longer auto-detected
```

`st.navigation` entries: `st.Page(lambda: view.show(), title="Name", icon="…")`.
Sidebar labels are controlled by `title=`, not by file names.

### Cherry palette (core/ui.py)

| Token | Value | Use |
|---|---|---|
| `CHERRY` | `#D2042D` | Primary brand, buttons, hero gradient |
| `DARK_CHERRY` | `#9B0320` | Headings, hover states |
| `TINT` | `#FDECEF` | Sidebar bg, card tints, info boxes |
| `BORDER_TINT` | `#F7C5CC` | Card borders, dividers |

### Status colours (distinct from brand red)

| Status | Background | Text | Icon |
|---|---|---|---|
| PRESENT | `#7A0016` | `#FFFFFF` | ⛔ |
| MAY CONTAIN | `#C2510A` | `#FFFFFF` | ⚠️ |
| UNCERTAIN | `#D4860A` | `#2B1B1E` | ❓ |
| NO MATCH | `#FFFFFF` | `#9B0320` | ✅ |


---

## Navigation fix — url_path (DEC-14)

`st.Page` with a lambda generates the URL pathname from the callable's repr. All four lambdas produce `<lambda>` so Streamlit raises `StreamlitAPIException: Multiple Pages specified with URL pathname <lambda>`. Fix: supply an explicit `url_path` to each `st.Page`:

```python
st.Page(lambda: _home.show(),    title="Home",    icon="🏠", url_path="home",    default=True)
st.Page(lambda: _check.show(),   title="Check",   icon="🔍", url_path="check")
st.Page(lambda: _history.show(), title="History", icon="🕘", url_path="history")
st.Page(lambda: _about.show(),   title="About",   icon="ℹ️", url_path="about")
```

The `pages/` directory is deleted so auto-detection cannot add duplicate entries.

## Updated cherry palette

| Token | Old | New |
|---|---|---|
| `CHERRY` | `#D2042D` | `#D20A2E` |
| `DARK_CHERRY` | `#9B0320` | `#8F0720` |
| `DEEP_CHERRY` (new) | — | `#5C0516` |
| `TINT` | `#FDECEF` | `#FCE8EB` |
| `PRESENT_BG` | `#7A0016` | `#5C0516` |
| `config.toml primaryColor` | `#D2042D` | `#D20A2E` |
| `config.toml secondaryBg` | `#FDECEF` | `#FCE8EB` |
