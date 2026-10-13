---
inclusion: always
---

# Product Steering — Food Allergy Ingredient Checker

## What this product is

A local, single-user Streamlit web app that helps people with food allergies check whether a packaged Indian food product contains ingredients they need to avoid. It cross-references ingredient lists against a curated dictionary of allergen synonyms, Indian regional names, and INS/E-number additive codes.

## Primary users

- People managing food allergies (their own or a family member's).
- Parents checking children's snacks.
- People navigating Indian packaged food where allergen names are not obvious.

## Core value propositions

1. Catches allergens hidden under technical names (e.g. casein = milk, maida = wheat).
2. Decodes Indian-specific ingredient names (groundnut = peanut, ghee = milk, dahi = milk).
3. Decodes INS/E additive codes with honest uncertainty when a code has multiple possible sources.
4. Honest three-way status — never claims a product is safe.

---

## What this tool does NOT claim ("Not claimed")

This section must appear in `product.md`, the `README.md`, and the About page. It is the safety and honesty contract of the product.

1. **This tool does NOT declare any product safe.**
   It reports "No known match found" when it cannot find a match. That is not a safety clearance. The label must still be read in full.

2. **This tool does NOT guarantee completeness.**
   The allergen synonym dictionary is curated but not exhaustive. New ingredient names, brand names, and regional terms may not be present.

3. **This tool does NOT provide medical advice.**
   It is an informational aid only. Users with severe allergies must consult a doctor or dietitian before relying on any automated tool.

4. **OCR can misread text.**
   Scanned ingredient text may contain errors. Users should always review and correct the extracted text before checking.

5. **INS codes can have multiple sources.**
   E.g. INS 322 (lecithin) can come from soy, egg, or sunflower. When the source is variable, the tool reports UNCERTAIN — it never claims the allergen is present or absent from a code alone.

6. **This tool does not cover all regional languages.**
   It covers common Hindi/Urdu transliterations but not all Indian regional languages (Tamil, Telugu, Bengali, Kannada, Marathi, etc.).

7. **This tool does not check for cross-contact during cooking.**
   It only analyses declared ingredient labels.

8. **"No known match found" ≠ "safe".**
   This phrase is used deliberately. It means the tool found nothing to flag — not that the product is free from the allergen.

---

## Language rules (enforced in all code, UI, and generated text)

- Never use the word **"safe"** in any context related to allergen results.
- Never use the phrase **"allergen-free"**.
- Use **"No known match found"** when no allergen is detected.
- Always show the disclaimer on every results screen and in every PDF report.
- Flag uncertainty rather than guess.
