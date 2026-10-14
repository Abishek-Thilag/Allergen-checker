# DECISIONS — Food Allergy Ingredient Checker

This file records significant architectural and design decisions, the options considered, and the rationale for each choice.

---

## DEC-01 — PDF library: fpdf2 over reportlab

**Decision:** Use `fpdf2` for PDF generation.

**Options considered:**
- `reportlab`: The industry standard, very powerful, but heavyweight and its free version has a watermark on the canvas. Configuration is verbose.
- `fpdf2`: A modern, actively maintained fork of PyFPDF. Lightweight, no watermark, clean API for simple documents, good Unicode support.

**Rationale:** Our PDF requirements are straightforward (text layout, no complex graphics). `fpdf2` covers them with far less boilerplate and no licensing friction.

---

## DEC-02 — Fuzzy matching: rapidfuzz over fuzzywuzzy

**Decision:** Use `rapidfuzz` for fuzzy string matching.

**Options considered:**
- `fuzzywuzzy`: The older library, has a C extension dependency (`python-Levenshtein`) for performance.
- `rapidfuzz`: A drop-in replacement for fuzzywuzzy, written in C++, faster by a large margin, MIT-licensed, no separate C extension needed.

**Rationale:** `rapidfuzz` is faster, actively maintained, and has the same API surface we need (`partial_ratio`). There is no reason to use `fuzzywuzzy` in a new project.

---

## DEC-03 — Persistence: SQLite over file-based storage

**Decision:** Use SQLite via the standard library `sqlite3` for all persistence (profiles, history).

**Options considered:**
- JSON files on disk: Simple but hard to query, no transactions, no concurrent safety.
- CSV: Even simpler but unsuitable for relational data (profiles ↔ allergens ↔ history).
- SQLite: Built into Python, zero install cost, transactional, queryable, fully relational.
- PostgreSQL/MySQL: Overkill for a single-user local app; requires a running server.

**Rationale:** SQLite is the correct fit for a local, single-user application. It requires nothing beyond the Python standard library and supports all the queries we need.

---

## DEC-04 — Three-way status (PRESENT / MAY_CONTAIN / UNCERTAIN) instead of boolean

**Decision:** Use exactly three statuses per allergen, not a boolean present/absent.

**Rationale:**
- A boolean safe/not-safe model would require us to either call something "safe" (which we must not do) or call something "present" when it is merely uncertain.
- Real food labels have genuinely uncertain situations: an INS code with multiple possible sources, vague ingredient names ("natural flavours"), cross-contamination statements.
- Three statuses give the user actionable information: PRESENT (act on it), MAY CONTAIN (be cautious), UNCERTAIN (investigate further). Collapsing these would remove information.

---

## DEC-05 — "No known match found" instead of "safe"

**Decision:** Never use the word "safe" or "allergen-free". Use "No known match found" for a clean check.

**Rationale:**
- This is an ethical and medical safety requirement. No automated tool can certify that a product is free from an allergen, because:
  - The dictionary is not exhaustive.
  - OCR can misread text.
  - Labels can be incomplete or incorrect.
  - Cross-contact is not declared on labels.
- The phrase "No known match found" is accurate: we searched and found nothing. We make no claim about what we did not find.

---

## DEC-06 — INS code sourcing policy

**Decision:** Include only INS codes that are explicitly referenced in either FSSAI Food Additives Regulations 2011 or the Codex Alimentarius General Standard for Food Additives (GSFA). Each entry must carry a non-empty `source` field. If a code's allergen source is variable, `variable_source` must be `true` and results must be UNCERTAIN.

**Rationale:**
- Fabricating allergen links for INS codes could cause real harm (false positives causing unnecessary dietary restriction, or worse, false confidence from a missed link).
- Using only verified, cited sources ensures every entry can be checked.
- The variable_source rule ensures we never claim allergen presence when the manufacturing source is unknown.

---

## DEC-07 — OCR placed last in the build order

**Decision:** OCR scan feature (pytesseract) is implemented in Phase 4, after all core logic and the manual input flow are complete.

**Rationale:**
- Tesseract is an external system dependency that may not be present in all environments.
- The core value of the app (ingredient matching) works without OCR.
- Building OCR last means the app is fully functional without it, and OCR is a progressive enhancement. It also makes testing easier: all Phase 1–3 tests can run without Tesseract installed.

---

## DEC-08 — No LLM or external API at runtime

**Decision:** All matching is deterministic, dictionary-based, and offline. No LLM or external API is called at runtime.

**Rationale:**
- Medical-adjacent tools must be predictable. A user needs to be able to explain why the app flagged something and reproduce the result.
- External API calls introduce latency, cost, privacy concerns (ingredient text sent off-device), and availability risk.
- The allergen dictionary is curated and auditable. LLM outputs are not.

---

## DEC-09 — Core modules have no Streamlit imports

**Decision:** Files in `core/` must never import Streamlit.

**Rationale:**
- Streamlit imports the full UI framework and cannot be used outside the Streamlit runtime.
- Keeping core modules Streamlit-free makes them independently testable with `pytest` without needing a running Streamlit server.
- It enforces a clean separation between business logic and presentation.

---

## DEC-10 — Multipage via Streamlit native `pages/` directory

**Decision:** Use Streamlit's built-in multipage support (files in the `pages/` directory) rather than a custom tab or routing system.

**Rationale:**
- Native multipage gives each page its own URL, a working browser back button, and a sidebar navigation link automatically.
- No third-party routing library needed.
- Simpler than rolling our own session-state-based page switching.


---

## DEC-11 — render_html() helper to prevent indentation-as-code-block

**Decision:** All multi-line HTML blocks are passed through `core/ui.render_html()` before being sent to `st.markdown(unsafe_allow_html=True)`.

**Root cause:** Streamlit processes its Markdown argument through CommonMark *before* parsing HTML. CommonMark treats any line starting with 4 or more spaces as a fenced code block. Triple-quoted Python strings inherit the function body's indentation (typically 8–16 spaces), so every HTML element inside them was rendered as a `<pre><code>` block rather than as markup.

**Fix:** `render_html()` strips all leading whitespace from every line (via `textwrap.dedent` + per-line `lstrip`) and collapses consecutive blank lines before calling `st.markdown`. Tests verify no output line starts with 4+ spaces and `unsafe_allow_html=True` is always passed.

---

## DEC-12 — st.navigation with views/ directory

**Decision:** Navigation is wired via `st.navigation` with explicit `st.Page` entries titled "Home", "Check", "History", "About". Page modules live in `views/` not `pages/`.

**Rationale:** Streamlit's file-based auto-detection builds page names from file names, so `pages/check.py` becomes "check" in the sidebar (lowercase). `st.navigation` lets us set `title=` and `icon=` explicitly. Moving pages to `views/` prevents the auto-detector from running at all, giving us full control over labels.

---

## DEC-13 — Cherry red & white theme; distinct status colours

**Decision:** Brand colour is cherry `#D2042D` / dark cherry `#9B0320`. Status colours are kept visually distinct from the brand: PRESENT uses `#7A0016` (very dark red), MAY CONTAIN uses orange `#C2510A`, UNCERTAIN uses amber `#D4860A` with dark text (WCAG AA). Every status also shows a text label and an icon so meaning never depends on colour alone.

**Rationale:** When the brand is already red, a red "allergen found" warning would blend into the UI chrome and lose urgency. Using a distinctly darker, more saturated red for PRESENT and different hue families for MAY CONTAIN and UNCERTAIN keeps the three statuses immediately distinguishable even for colour-blind users (hue + icon + text label triple-coding).


---

## DEC-14 — st.Page requires url_path when using lambdas

**Decision:** Every `st.Page(...)` call in `app.py` must include an explicit `url_path=` argument.

**Root cause:** When `st.Page` is given a lambda as its page function, Streamlit derives the URL pathname from the callable's `__name__` attribute, which is `"<lambda>"` for all lambdas. Four pages with identical pathnames cause `StreamlitAPIException: Multiple Pages specified with URL pathname <lambda>`. Supplying distinct `url_path` values (`"home"`, `"check"`, `"history"`, `"about"`) resolves this. Alternatively, named functions could be used, but `url_path` is more explicit.

---

## DEC-15 — pages/ deleted; st.navigation provides titles

**Decision:** The `pages/` directory was deleted. Navigation is managed entirely by `st.navigation` in `app.py`.

**Rationale:** Streamlit's file-based auto-detection builds page labels from file names in lower case (e.g. `pages/check.py` → "check"). With both `pages/` and `st.navigation` present, Streamlit shows both — the auto-detected lowercase labels and the navigation entries. Deleting `pages/` removes the conflict and gives full control of labels (title, icon) to the `st.Page` declarations.

---

## DEC-16 — Updated cherry palette (#D20A2E / #8F0720 / #5C0516)

**Decision:** Palette updated to `CHERRY=#D20A2E`, `DARK_CHERRY=#8F0720`, `DEEP_CHERRY=#5C0516`, `TINT=#FCE8EB`.

**Status colour mapping:** PRESENT uses `DEEP_CHERRY` (`#5C0516`) — significantly darker than the brand cherry — so it reads as a distinct, urgent warning rather than brand styling. MAY CONTAIN (`#B84500` orange) and UNCERTAIN (`#C97A00` amber) use different hue families. All status colours pass WCAG AA contrast for their text colour. NOT RECOGNISED uses neutral grey to communicate absence of information rather than severity.

---

## DEC-17 — UI Polish: Hero Typography, Capitalized Navigation, and Distinct Status Colors

**Decision:**
1. **Hero Title Specificity:** Styled `.hero h1, .hero h2, .hero h3 { color: #FFFFFF !important; }` with a subtle text-shadow (`0 1px 4px rgba(0,0,0,.30)`). Headings outside the hero remain in dark cherry (`#8F0720`), and the white "Check Ingredients" button preserves dark cherry text.
2. **Sidebar Navigation Titles:** Sidebar displays exactly "Home", "Check", "History", and "About" via `st.navigation` using `st.Page(..., title=..., url_path=...)`. Unique URL paths eliminate lambda naming collisions, `pages/` auto-detection is removed, and `st.set_page_config` resides exclusively in `app.py`.
3. **WCAG AA Status System:**
   - `PRESENT`: Deep cherry (`#5C0516`) with white text and `⛔` icon.
   - `MAY CONTAIN`: Orange (`#B84500`) with white text and `⚠️` icon.
   - `UNCERTAIN`: Yellow (`#EAB308`) with dark text (`#2B1B1E`) and `❓` icon (contrast ratio > 7:1).
   - `NOT RECOGNISED`: Grey (`#F3F4F6` / `#374151`) with `❔` icon.
   - `No known match found`: White card with cherry outline (`#D20A2E`), dark cherry text, and `✅` icon.
   - Every status maintains explicit text labels and icon double/triple-coding.
4. **Theme Cohesion:** Palette (`#D20A2E`, `#8F0720`, `#5C0516`, `#FCE8EB`, `#FFFFFF`) applied across `.streamlit/config.toml` and `core/ui.py`. Removed any leftover off-theme alert colors in favor of the cherry tint system.

---

## DEC-18 — Visual Polish: Hero Live Preview, Quick Preset Chips, and Rich Empty States

**Decision:**
1. **Interactive Hero Preview:** Enriched the landing page hero with a live detection preview card illustrating a dual-allergen detection scenario (Casein/Whey & INS 322).
2. **Quick Preset Chips:** Added 4 one-click ingredient preset buttons in the Check page's Manual tab (`🍫 Chocolate`, `🍪 Biscuit`, `🍜 Noodles`, `🥜 Namkeen`) so users can test the engine instantly without typing.
3. **Engine-Ready Dashboard State:** Replaced the empty dashed box on the Check page with a structured, illustrated inspection readiness dashboard outlining detection capabilities and status references.
4. **Dashboard-Grade History Tiles:** Elevated the History page metrics with iconography, distinct status cards, and an empty state guiding the user to run their first check.

---

## DEC-19 — Dense Layout & Dynamic Elements: Two-Column Check Station, Synonym Sandbox, and Allergen Spectrum

**Decision:**
1. **Container Width and Spacing Constraint:** Adjusted container `max-width: 1380px` centered with tightened vertical gaps (`0.75rem`) and reduced top/bottom padding to prevent elements from stretching into vacant whitespace on ultrawide screens.
2. **Two-Column Check Station:** Structured the Check page into a balanced 62/38 two-column layout:
   - **Left Column:** Quick sample presets, multi-input tabs (Manual/OCR/Sample Library), primary action button, and live audit findings / engine readiness state.
   - **Right Column (Live Context & Intelligence):** Always-visible Profile Watchlist with severity pills (🔴 Severe, 🟠 Moderate, 🟡 Mild), Indian Packaged Food Risk Radar, INS Additive Quick Codex, and 100% On-Device verification guarantee.
3. **Interactive Home Page Elements:**
   - **Live Synonym Sandbox:** Added interactive one-click decode buttons for common Indian aliases (`maida`, `groundnut`, `casein`, `whey`, `INS 322`, `til`, `hing`, `khoya`) that resolve instant explanations on-page.
   - **Top 10 Indian Allergen Spectrum Grid:** Added a 5x2 visual matrix detailing the 10 standard allergen families and their regional aliases.
   - **Allergen Safety FAQ Accordion:** Interactive expanders explaining FSSAI labeling nuances, cross-contamination, and offline privacy.
4. **Enhanced History & Decoder Interactivity:**
   - Added real-time text keyword search across historical ingredient panels.
   - Added category filter pills and live name search for the Hidden Name Reference Decoder table.


