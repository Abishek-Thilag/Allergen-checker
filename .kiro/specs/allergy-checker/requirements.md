# Requirements — Food Allergy Ingredient Checker

## Introduction

Indian packaged-food labels use a mix of English, transliterated Hindi, and INS/E-number codes to describe ingredients. People managing food allergies often cannot tell whether a product is safe for them, because an allergen may be hidden under a technical name (e.g. casein = milk), an Indian regional name (e.g. maida = wheat, groundnut = peanut), or an additive code (e.g. INS 322 = lecithin, possibly from soy).

This app provides a deterministic, honest ingredient-checking tool. It never tells the user a product is safe. It flags anything uncertain rather than guessing.

---

## Functional Requirements

### REQ-1 Ingredient Input

- **REQ-1.1** The user can type or paste an ingredient list into a text area.
- **REQ-1.2** The user can upload a label photo (JPG or PNG, max 10 MB). OCR (pytesseract) extracts the text and displays it in an editable text area so the user can correct OCR errors before checking.
- **REQ-1.3** A "Load sample" button loads one of at least 10 realistic sample labels from `data/samples/`. Clicking it populates the editable text area in one click for demo purposes.
- **REQ-1.4** If the input is empty after trimming, the app shows a clear error message and does not proceed to matching.
- **REQ-1.5** If an uploaded file is not a supported image type or exceeds the size limit, the app shows a clear error message.

### REQ-2 Profiles and Allergens

- **REQ-2.1** The sidebar shows a profile selector. Multiple named profiles (e.g. "Me", "Mom") can exist simultaneously.
- **REQ-2.2** The user can create a new profile, switch to an existing one, and delete a profile (with confirmation). Duplicate profile names are rejected with a clear error message.
- **REQ-2.3** Each profile stores an independent list of allergens to check for.
- **REQ-2.4** The user selects allergens from a fixed list: milk, egg, peanut, tree nuts, wheat, soy, fish, shellfish, sesame, mustard. Custom allergens can also be added.
- **REQ-2.5** Each allergen entry in a profile has a severity level: mild, moderate, or severe.
- **REQ-2.6** Severe allergens produce a visually stronger warning style than mild or moderate ones.
- **REQ-2.7** Profiles, allergen selections, and severity levels persist between runs via SQLite.

### REQ-3 Parsing and Matching

- **REQ-3.1** The parser lowercases the text, splits on commas, semicolons, and brackets, trims whitespace, and handles nested parenthetical ingredient lists (e.g. "chocolate (sugar, cocoa butter, milk powder)").
- **REQ-3.2** The matcher reads `data/allergens.json`, which maps each allergen to synonyms and derived names with short explanations. Examples:
  - milk: whey, casein, caseinate, lactose, lactalbumin, milk solids, milk powder, butter, ghee, curd, dahi, paneer, khoya
  - egg: albumin, ovalbumin, lysozyme, egg white, egg yolk, mayonnaise
  - peanut: groundnut, arachis oil, peanut butter
  - wheat: maida, atta, suji, rava, semolina, durum, gluten
  - soy: soya, tofu, miso, edamame, soy lecithin
- **REQ-3.3** The INS decoder reads `data/ins_codes.json` and recognises the formats `INS 322`, `INS322`, `E322`, and `(322)`. Each entry stores the substance name, the allergens it may derive from, a source citation, and whether the source is variable.
- **REQ-3.4** If an INS code has a variable source (e.g. lecithin from soy or sunflower), the result is UNCERTAIN, never PRESENT.
- **REQ-3.5** Only INS codes verifiable against a documented source (FSSAI or Codex Alimentarius) are included; each entry is marked with its source.
- **REQ-3.6** Fuzzy matching uses rapidfuzz with a configurable threshold (default 85) so typos and OCR errors (e.g. "peanutt", "casien") still match.
- **REQ-3.7** The parser detects "may contain traces of …" and "manufactured in a facility that processes …" statements and returns them as MAY CONTAIN results.
- **REQ-3.8** Vague ingredients ("natural flavours", "spices", "emulsifier", "modified starch") are flagged as UNCERTAIN.

### REQ-4 Results and Status

- **REQ-4.1** Exactly three statuses are used per allergen match:
  - **PRESENT**: a matching ingredient or synonym was found in the main ingredient list.
  - **MAY CONTAIN**: a trace or cross-contamination statement was found.
  - **UNCERTAIN**: vague wording, an INS code with a variable source, or unreadable text.
- **REQ-4.2** If no allergen from the active profile matches anything in the ingredient text, the app shows "No known match found". The words "safe" and "allergen-free" are never used anywhere in the UI, reports, or messages.
- **REQ-4.3** A risk summary banner at the top shows a large colour-coded card:
  - Red: anything is PRESENT, or a severe allergen is MAY CONTAIN.
  - Amber: any MAY CONTAIN or UNCERTAIN result.
  - Blue/green neutral: "No known match found".
  - The banner shows counts: e.g. "2 allergens found, 1 uncertain".
- **REQ-4.4** The ingredient text is displayed with colour highlights: red for PRESENT, orange for MAY CONTAIN, yellow for UNCERTAIN, with a legend.
- **REQ-4.5** Every flagged item shows a "Why was this flagged?" explanation (e.g. "casein is a milk protein"), sourced from the JSON data.
- **REQ-4.6** Results display colour-coded status chips with allergen emojis:
  - 🥛 milk, 🥜 peanut, 🥚 egg, 🌾 wheat, 🌰 tree nuts, 🫘 soy, 🐟 fish, 🦐 shellfish, 🌿 sesame, 🌿 mustard.

### REQ-5 Scan History

- **REQ-5.1** Every ingredient check is stored in SQLite: profile name, timestamp, ingredient text, results, and statuses.
- **REQ-5.2** A History page lists past checks. The user can filter by profile and by status (PRESENT / MAY CONTAIN / UNCERTAIN).
- **REQ-5.3** The user can reopen a past check (pre-populating the Check page) or delete it.

### REQ-6 Downloadable Report

- **REQ-6.1** A PDF report can be generated for any check result. It includes: profile name, date, ingredient text, risk summary, each flagged item with its status and explanation, and the disclaimer.
- **REQ-6.2** A download button is shown on the results screen and the History page.

### REQ-7 UI and Design

- **REQ-7.1** `st.set_page_config` sets a title, icon, and wide layout.
- **REQ-7.2** A header shows the app title and tagline "Spot hidden allergens in Indian food labels."
- **REQ-7.3** A soft colour theme is configured in `.streamlit/config.toml`.
- **REQ-7.4** The sidebar contains: profile selector, allergen list with severity badges, and profile management controls. Results render in the main area.
- **REQ-7.5** Three pages: Check, History, About.
- **REQ-7.6** The About page explains limitations and shows the disclaimer.

### REQ-8 Safety and Honesty

- **REQ-8.1** The word "safe" or "allergen-free" never appears in any UI text, message, report, or generated content.
- **REQ-8.2** A disclaimer is always visible: "This tool is an aid, not medical advice. Always read the original label and consult a doctor."
- **REQ-8.3** Uncertain items are always flagged rather than dismissed.
- **REQ-8.4** A "Not claimed" section appears in product.md, the README, and the About page.

### REQ-9 Technical Requirements

- **REQ-9.1** File structure:
  ```
  app.py
  pages/
  core/parser.py
  core/matcher.py
  core/ins_decoder.py
  core/ocr.py
  core/report.py
  core/db.py
  data/allergens.json
  data/ins_codes.json
  data/samples/
  tests/
  ```
- **REQ-9.2** All matching logic in `core/` is pure Python with no Streamlit imports.
- **REQ-9.3** Input validation and error handling covers: empty text, unsupported/oversized images, unreadable OCR output, missing profile, duplicate profile names, missing or corrupt data files — each with a clear user-facing error message.
- **REQ-9.4** pytest tests cover: synonym detection, Indian names, INS code parsing in all formats, UNCERTAIN for variable-source INS codes, nested ingredients, typos via fuzzy match, "may contain" statements, vague ingredients, empty input, no-match wording (never "safe"), profile CRUD, severity styling, history storage, and PDF generation.
- **REQ-9.5** `requirements.txt` lists all dependencies with pinned versions.
- **REQ-9.6** A README includes setup steps (including Tesseract OCR installation), how to run, how to run tests, and a limitations section.

---

## Non-Functional Requirements

- **NFR-1** The ingredient check (excluding OCR) completes within 2 seconds for a typical label text of up to 500 tokens.
- **NFR-2** The SQLite database is stored locally; no data is sent to any external server.
- **NFR-3** The app works offline once dependencies are installed (no external API calls at runtime).
- **NFR-4** The app targets Python 3.10+.

---

## REQ-UI-1 — HTML rendering helper

- **REQ-UI-1.1** A function `render_html(block: str)` in `core/ui.py` strips all leading whitespace from each line and collapses consecutive blank lines before calling `st.markdown(…, unsafe_allow_html=True)`.
- **REQ-UI-1.2** No page file may call `st.markdown(…, unsafe_allow_html=True)` directly with a multi-line HTML block; all such calls must use `render_html()`.
- **REQ-UI-1.3** `render_html()` must be tested: no output line starts with 4+ spaces; no consecutive blank lines; `unsafe_allow_html=True` is always passed.

## REQ-UI-2 — Navigation

- **REQ-UI-2.1** `app.py` uses `st.navigation` with four `st.Page` entries titled **Home**, **Check**, **History**, **About** with icons 🏠 🔍 🕘 ℹ️.
- **REQ-UI-2.2** Page content lives in `views/` (not `pages/`) so Streamlit's file-based auto-detection does not run.
- **REQ-UI-2.3** `st.set_page_config` is called only in `app.py`.

## REQ-UI-3 — Cherry-red theme

- **REQ-UI-3.1** `.streamlit/config.toml` sets `base="light"`, `primaryColor="#D2042D"`, `backgroundColor="#FFFFFF"`, `secondaryBackgroundColor="#FDECEF"`, `textColor="#2B1B1E"`.
- **REQ-UI-3.2** `core/ui.apply_theme()` injects the global CSS; it is called once in `app.py`.
- **REQ-UI-3.3** Palette: cherry `#D2042D`, dark cherry `#9B0320`, tint `#FDECEF`, white `#FFFFFF`.

## REQ-UI-4 — Distinct status colours

- **REQ-UI-4.1** PRESENT: dark red `#7A0016`, white text, ⛔ icon.
- **REQ-UI-4.2** MAY CONTAIN: orange `#C2510A`, white text, ⚠️ icon.
- **REQ-UI-4.3** UNCERTAIN: amber `#D4860A`, dark text (WCAG AA), ❓ icon.
- **REQ-UI-4.4** No known match found: white card, cherry outline, ✅ icon.
- **REQ-UI-4.5** Every status shows a text label as well as colour and icon.

---

## REQ-UI-5 — Navigation fix (url_path)

- **REQ-UI-5.1** Each `st.Page` must have a unique `url_path` argument (`"home"`, `"check"`, `"history"`, `"about"`). Using lambdas without `url_path` causes a `StreamlitAPIException: Multiple Pages specified with URL pathname <lambda>`.
- **REQ-UI-5.2** The `pages/` directory must not exist (or must be empty) so Streamlit's file-based auto-detection does not add duplicate lowercase entries to the sidebar.
- **REQ-UI-5.3** A test must verify the four page titles are exactly `["Home", "Check", "History", "About"]`.

## REQ-UI-6 — Updated cherry palette

- Primary cherry: `#D20A2E` · Dark cherry: `#8F0720` · Deep cherry: `#5C0516`
- Tint: `#FCE8EB` · White: `#FFFFFF` · Text: `#2B1B1E`
- `config.toml`: `primaryColor="#D20A2E"`, `secondaryBackgroundColor="#FCE8EB"`
- PRESENT status: `#5C0516` (deep cherry) with white text and ⛔
- MAY CONTAIN: orange with ⚠️; UNCERTAIN: amber with ❓; grey for unrecognised
