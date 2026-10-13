# Food Allergy Ingredient Checker

**Spot hidden allergens in Indian food labels.**

A local, offline Streamlit web app that helps people with food allergies check
whether a packaged Indian food product contains ingredients they must avoid —
including allergens hidden under technical names, Indian regional names, and
INS/E-number additive codes.

---

## What it does

- Catches allergens listed as `casein` (milk), `maida` (wheat), `groundnut` (peanut),
  `ghee` (milk), `dahi` (milk), `til` (sesame), `rai` (mustard), and many more.
- Decodes INS/E-number additive codes (e.g. INS 322 = lecithin, possibly from soy or egg).
- Flags vague ingredients ("natural flavours", "spices") as UNCERTAIN.
- Detects "may contain traces of …" and facility statements.
- Fuzzy-matches typos and OCR errors (e.g. "peanutt", "casien").
- Three honest statuses: **PRESENT**, **MAY CONTAIN**, **UNCERTAIN**. Never says "safe".

---

## What this tool does NOT claim

1. **Does NOT declare any product safe.** "No known match found" is not a safety clearance.
2. **Does NOT guarantee completeness.** The dictionary is curated but not exhaustive.
3. **Does NOT provide medical advice.** Consult a doctor for allergy management.
4. **OCR can misread text.** Always review extracted text before checking.
5. **INS codes can have multiple sources.** Variable-source codes are always UNCERTAIN.
6. **Does not cover all Indian regional languages.** Hindi/Urdu transliterations only.
7. **Does not check for cross-contact during cooking.** Declared labels only.
8. **"No known match found" ≠ free from allergen.**

---

## Prerequisites

- Python 3.10 or later
- Tesseract OCR (for the label scan feature — optional for manual input)

### Install Tesseract OCR

| Platform | Command / link |
|---|---|
| Windows | Download installer from https://github.com/UB-Mannheim/tesseract/wiki |
| macOS | `brew install tesseract` |
| Ubuntu/Debian | `sudo apt install tesseract-ocr` |
| Fedora/RHEL | `sudo dnf install tesseract` |

After installing on Windows, add the Tesseract installation directory
(e.g. `C:\Program Files\Tesseract-OCR`) to your system `PATH`.

---

## Installation

```bash
# 1. Clone / download the project
cd projk

# 2. (Recommended) create a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## How to run

```bash
streamlit run app.py
```

The app opens at http://localhost:8501 in your browser.

---

## How to run tests

```bash
pytest tests/ -v
```

All tests run offline. Tesseract is not required — the OCR tests mock pytesseract.

---

## Demo scenario

1. Select the **Demo** profile (pre-loaded with milk: severe, soy: moderate).
2. Go to the **Check** page.
3. Click the **Load Sample** tab and choose **Sample 04 Chocolate** (the demo label).
4. Click **Check ingredients**.

Expected result:
- 🔴 **PRESENT**: milk (casein, whey found)
- 🟡 **UNCERTAIN**: soy (INS 322 = lecithin, variable source)
- 🟡 **UNCERTAIN**: both allergens (natural flavours is vague)
- Red risk banner
- No use of the word "safe"

---

## Project structure

```
app.py              — Streamlit entry point
pages/
  check.py          — Check page (ingredient input, results)
  history.py        — History page
  about.py          — About / limitations / disclaimer
core/
  constants.py      — Shared constants
  parser.py         — Ingredient text parser
  matcher.py        — Allergen matching logic
  ins_decoder.py    — INS/E-number decoder
  ocr.py            — pytesseract wrapper
  report.py         — PDF report generator
  db.py             — SQLite access layer
data/
  allergens.json    — Allergen synonym dictionary (10 allergens)
  ins_codes.json    — INS/E-number decoder data
  samples/          — 10 sample label text files
tests/              — pytest test suite (107 tests)
.streamlit/
  config.toml       — Colour theme
requirements.txt
DECISIONS.md        — Architecture decision records
```

---

## Disclaimer

This tool is an informational aid only, not medical advice. It may miss allergens
due to OCR errors, incomplete dictionaries, or unlabelled ingredients. Always read
the original product label carefully and consult a doctor or dietitian before making
food choices based on allergy concerns. "No known match found" does not mean a
product is free from an allergen.
