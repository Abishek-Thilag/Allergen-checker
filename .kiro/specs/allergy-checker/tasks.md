# Tasks — Food Allergy Ingredient Checker

## Phase 1 — Data, Parser, Matcher, INS Decoder, Tests

### Task 1.1 — Create `data/allergens.json`
Define all 10 canonical allergens (milk, egg, peanut, tree nuts, wheat, soy, fish, shellfish, sesame, mustard) with emojis, synonyms (including Indian names), and per-synonym explanations.
- [ ] milk (whey, casein, caseinate, lactose, lactalbumin, milk solids, milk powder, butter, ghee, curd, dahi, paneer, khoya)
- [ ] egg (albumin, ovalbumin, lysozyme, egg white, egg yolk, mayonnaise)
- [ ] peanut (groundnut, arachis oil, peanut butter, monkey nuts)
- [ ] tree nuts (almond, badam, cashew, kaju, walnut, akhrot, pistachio, pista, hazelnut, pecan, macadamia, pine nuts, chestnut, brazil nut)
- [ ] wheat (maida, atta, suji, rava, semolina, durum, gluten, wheat flour, wheat starch, wheat bran, wheat germ)
- [ ] soy (soya, tofu, miso, edamame, soy lecithin, soya flour, soya protein, textured vegetable protein, tvp, tempeh)
- [ ] fish (anchovy, sardine, tuna, salmon, cod, haddock, tilapia, fish sauce, fish paste, worcestershire sauce)
- [ ] shellfish (shrimp, prawn, crab, lobster, crayfish, scallop, oyster, clam, abalone, barnacle)
- [ ] sesame (til, gingelly, sesame oil, sesame seeds, tahini)
- [ ] mustard (mustard seeds, mustard oil, mustard paste, sarson, rai)
- [ ] vague ingredient patterns list (natural flavours, artificial flavours, spices, emulsifier, modified starch, vegetable oil, hydrolysed vegetable protein)

### Task 1.2 — Create `data/ins_codes.json`
Populate with INS/E-codes that have allergen relevance, each with substance name, possible_allergens, variable_source flag, explanation, and source citation.
- [ ] INS 322 (lecithin — soy/egg/sunflower, variable, Codex)
- [ ] INS 101 (riboflavin — milk, variable source possible, Codex)
- [ ] INS 120 (cochineal — shellfish derived historically, now insect, note)
- [ ] INS 160a (beta-carotene — no allergen, but some preparations use soy carrier)
- [ ] INS 270 (lactic acid — generally synthetic, but can be dairy-derived)
- [ ] INS 422 (glycerol — generally vegetable or synthetic)
- [ ] INS 471 (mono- and diglycerides — variable animal/vegetable)
- [ ] INS 481 (sodium stearoyl lactylate — contains lactate, possible milk derivative)
- [ ] INS 570 (stearic acid — animal or vegetable)
- [ ] INS 631 (sodium inosinate — often from fish or pork, variable)
- [ ] INS 635 (disodium 5'-ribonucleotides — often from fish, variable)
- [ ] INS 901 (beeswax — not a food allergen but note bee products)
- [ ] At least 10 more codes common on Indian labels, sourced and cited

### Task 1.3 — Create `data/samples/` (10 sample label texts)
Ten `.txt` files, one per category. Include the demo scenario file.
- [ ] `sample_01_biscuit.txt` — contains maida, butter, milk solids, egg
- [ ] `sample_02_namkeen.txt` — contains groundnut, rava, mustard seeds
- [ ] `sample_03_instant_noodles.txt` — contains maida, gluten, soy sauce
- [ ] `sample_04_chocolate.txt` (DEMO) — contains casein, whey, INS 322, natural flavours, no "milk" or "soy" written
- [ ] `sample_05_dairy_product.txt` — contains milk, dahi, curd, lactalbumin
- [ ] `sample_06_snack_bar.txt` — contains almond, cashew, pista, may contain traces of peanut
- [ ] `sample_07_ready_meal.txt` — contains tofu, soya protein, edamame
- [ ] `sample_08_bread.txt` — contains wheat flour, gluten, egg yolk, sesame seeds
- [ ] `sample_09_sauce.txt` — contains anchovy, worcestershire sauce, fish paste
- [ ] `sample_10_breakfast_cereal.txt` — contains barley, wheat bran, manufactured in a facility that processes milk and nuts

### Task 1.4 — Implement `core/parser.py`
- [ ] `parse_ingredients(text: str) -> ParseResult`
- [ ] Handle nested parentheses (one level deep minimum)
- [ ] Detect trace/facility statements via regex
- [ ] Return `ParseResult(tokens, trace_statements)`
- [ ] Raise `ValueError` on None input; return empty ParseResult on empty string

### Task 1.5 — Implement `core/ins_decoder.py`
- [ ] `extract_ins_codes(text: str) -> list[str]`
- [ ] Regex handles: `INS 322`, `INS322`, `E322`, `(322)` (3–4 digit codes only)
- [ ] `decode_ins(code: str, ins_data: dict) -> InsDecodeResult | None`
- [ ] Returns None for unknown codes
- [ ] Pure function, no side effects

### Task 1.6 — Implement `core/matcher.py`
- [ ] `match_allergens(parse_result, profile_allergens, allergen_data, ins_data, fuzzy_threshold=85) -> list[MatchResult]`
- [ ] Exact match logic
- [ ] Fuzzy match via rapidfuzz
- [ ] INS code integration (calls ins_decoder)
- [ ] Vague ingredient detection → UNCERTAIN
- [ ] Trace statement scan → MAY_CONTAIN
- [ ] Status precedence: PRESENT > MAY_CONTAIN > UNCERTAIN

### Task 1.7 — Write `tests/` (Phase 1)
- [ ] `test_parser.py`: nested ingredients, empty input, trace detection, bracket splitting
- [ ] `test_ins_decoder.py`: all 4 INS formats, unknown code, variable-source code
- [ ] `test_matcher.py`:
  - whey → milk (synonym)
  - maida → wheat (Indian name)
  - groundnut → peanut (Indian name)
  - dahi → milk (Indian name)
  - "INS 322" → UNCERTAIN (variable source)
  - "E322" → UNCERTAIN
  - "(322)" → UNCERTAIN
  - "peanutt" → peanut via fuzzy match
  - "casien" → milk via fuzzy match
  - "natural flavours" → UNCERTAIN
  - "may contain traces of milk" → MAY_CONTAIN
  - "manufactured in a facility that processes wheat" → MAY_CONTAIN
  - empty ingredient text → empty results
  - no match → no MatchResult (never the word "safe")
  - nested: "chocolate (sugar, cocoa butter, milk powder)" → milk PRESENT

---

## Phase 2 — Check Page (Manual Input + Results)

### Task 2.1 — Implement `core/db.py`
- [ ] SQLite schema (profiles, profile_allergens, history)
- [ ] `create_profile(name) -> int`
- [ ] `get_profiles() -> list[Profile]`
- [ ] `delete_profile(id)`
- [ ] `get_allergens_for_profile(profile_id) -> list[AllergenEntry]`
- [ ] `set_allergens_for_profile(profile_id, allergens: list[AllergenEntry])`
- [ ] `save_history(profile_id, timestamp, ingredient_text, results_json, summary_status) -> int`
- [ ] `get_history(profile_id=None, status_filter=None) -> list[HistoryEntry]`
- [ ] `delete_history_entry(id)`
- [ ] Seed a "Demo" profile with milk (severe) and soy (moderate) on first run

### Task 2.2 — Implement `app.py`
- [ ] `st.set_page_config(page_title, page_icon, layout="wide")`
- [ ] Load and cache `allergens.json` and `ins_codes.json` from `data/`
- [ ] Initialise DB
- [ ] Define navigation (multipage via `pages/`)
- [ ] Global disclaimer banner in sidebar

### Task 2.3 — Implement `pages/check.py` (Check page — manual input)
- [ ] Header: title + tagline
- [ ] Sidebar: profile selector, allergen list with severity badges (mild/moderate/severe), profile CRUD (create, switch, delete with confirmation), add/remove allergen with severity picker
- [ ] Input area: text tab (paste/type)
- [ ] "Load sample" button: dropdown of sample files → populates text area
- [ ] "Check" button → calls matcher
- [ ] Risk summary banner (red/amber/blue-green) with count line
- [ ] Highlighted ingredient text (HTML `<mark>` tags, legend)
- [ ] Result cards per flagged allergen: emoji + status chip + "Why flagged?" explanation
- [ ] Download PDF button (calls report.py)
- [ ] "No known match found" neutral banner when no allergens flagged (never "safe")
- [ ] All results saved to history via db.py

### Task 2.4 — Tests for db.py (Phase 2)
- [ ] Profile create, get, delete
- [ ] Duplicate profile name rejection
- [ ] Allergen set/get with severity
- [ ] History save and retrieve
- [ ] History delete

---

## Phase 3 — History Page and PDF Report

### Task 3.1 — Implement `core/report.py`
- [ ] `generate_pdf(profile_name, timestamp, ingredient_text, match_results, summary_status) -> bytes`
- [ ] fpdf2 library
- [ ] Title, profile, date on first page
- [ ] Ingredient text section
- [ ] Summary banner text (status counts)
- [ ] Per-allergen section: emoji + status + explanation
- [ ] Disclaimer footer on every page
- [ ] Never use "safe" or "allergen-free" in the PDF

### Task 3.2 — Implement `pages/history.py`
- [ ] Filter bar: profile dropdown + status filter
- [ ] List of checks: timestamp, profile, summary status, 100-char snippet of ingredient text
- [ ] Reopen button: writes ingredient text to session_state, navigates to Check page
- [ ] Delete button with confirmation
- [ ] Download PDF for any past check

### Task 3.3 — Tests for report.py (Phase 3)
- [ ] PDF bytes are non-empty
- [ ] PDF does not contain the word "safe" or "allergen-free"
- [ ] PDF contains disclaimer text

---

## Phase 4 — OCR Scan

### Task 4.1 — Implement `core/ocr.py`
- [ ] `extract_text_from_image(image_bytes: bytes) -> OcrResult`
- [ ] Graceful error if Tesseract not installed
- [ ] Graceful error if image cannot be decoded
- [ ] Preprocessing: convert to greyscale, no resize by default
- [ ] Returns `OcrResult(text, confidence, error)`

### Task 4.2 — Add Scan tab to `pages/check.py`
- [ ] File uploader (JPG/PNG only, max 10 MB)
- [ ] Show preview of uploaded image
- [ ] Run OCR on upload, display extracted text in editable text area
- [ ] Show warning if OCR output is empty
- [ ] Show warning if Tesseract not installed (fallback to manual)

### Task 4.3 — Tests for ocr.py (Phase 4)
- [ ] Test with a small synthetic PNG (white background, black text)
- [ ] Test graceful error when Tesseract absent (mock pytesseract import)
- [ ] Test oversized image rejection at the UI layer (unit-testable validation)

---

## Phase 5 — UI Polish, README, DECISIONS.md

### Task 5.1 — Create `.streamlit/config.toml`
- [ ] Set primaryColor, backgroundColor, secondaryBackgroundColor, textColor, font

### Task 5.2 — Implement `pages/about.py`
- [ ] App description and how-it-works explanation
- [ ] "What this tool does NOT claim" section (Not claimed)
- [ ] Limitations: OCR accuracy, INS variable sources, dictionary not exhaustive, no guarantee
- [ ] Full disclaimer block (prominent styling)

### Task 5.3 — Write `README.md`
- [ ] Project overview
- [ ] Prerequisites (Python 3.10+, Tesseract OCR install instructions for Windows/macOS/Linux)
- [ ] Installation steps (`pip install -r requirements.txt`)
- [ ] How to run (`streamlit run app.py`)
- [ ] How to run tests (`pytest tests/`)
- [ ] Demo scenario walkthrough
- [ ] Limitations section
- [ ] Disclaimer

### Task 5.4 — Write `DECISIONS.md`
- [ ] Why fpdf2 over reportlab
- [ ] Why rapidfuzz over fuzzywuzzy
- [ ] Why SQLite over file-based persistence
- [ ] Why status is three-way (PRESENT / MAY_CONTAIN / UNCERTAIN) not boolean
- [ ] Why "No known match found" instead of "safe"
- [ ] INS code sourcing policy (only FSSAI/Codex, variable_source rule)
- [ ] OCR placed last in build order (external dependency)

### Task 5.5 — Final review
- [ ] Search entire codebase for the words "safe" and "allergen-free" — remove any occurrence
- [ ] Ensure disclaimer appears in: sidebar, results area, About page, PDF footer
- [ ] Run full test suite: `pytest tests/ -v`
- [ ] Verify demo scenario end-to-end manually


---

## Phase 6 — Navigation & Theme Fixes

### Task 6.1 — Fix startup error (url_path)
- [ ] Add `url_path="home"/"check"/"history"/"about"` to each `st.Page` in `app.py`
- [ ] Delete `pages/` directory (or empty it) to stop Streamlit auto-detection

### Task 6.2 — Update cherry palette in `core/ui.py`
- [ ] `CHERRY = "#D20A2E"`, `DARK_CHERRY = "#8F0720"`, add `DEEP_CHERRY = "#5C0516"`
- [ ] `TINT = "#FCE8EB"`, `BORDER_TINT = "#F5C2C7"`
- [ ] `PRESENT_BG = "#5C0516"`, `PRESENT_BORDER = "#3D000F"`
- [ ] Update CSS in `apply_theme()` to reference new values
- [ ] Update `.streamlit/config.toml`

### Task 6.3 — Tests
- [ ] Add test: page titles are exactly `["Home", "Check", "History", "About"]`
- [ ] Run full pytest suite; fix any failures
- [ ] Add DEC-14 and DEC-15 to DECISIONS.md
