"""
Shared constants for the Food Allergy Ingredient Checker.
No Streamlit imports allowed in this file.
"""

# ── Status strings ────────────────────────────────────────────────────────────
STATUS_PRESENT = "PRESENT"
STATUS_MAY_CONTAIN = "MAY_CONTAIN"
STATUS_UNCERTAIN = "UNCERTAIN"
STATUS_NO_MATCH = "NO_MATCH"

# ── Severity levels ───────────────────────────────────────────────────────────
SEVERITY_MILD = "mild"
SEVERITY_MODERATE = "moderate"
SEVERITY_SEVERE = "severe"

# ── Colours (hex) for use in HTML/CSS and PDF ─────────────────────────────────
COLOUR_PRESENT = "#D32F2F"       # deep red
COLOUR_MAY_CONTAIN = "#E65100"   # deep orange
COLOUR_UNCERTAIN = "#F9A825"     # amber
COLOUR_NO_MATCH = "#1565C0"      # blue

COLOUR_BANNER_PRESENT = "#FFCDD2"    # red tint banner bg
COLOUR_BANNER_MAY_CONTAIN = "#FFE0B2"  # orange tint banner bg
COLOUR_BANNER_UNCERTAIN = "#FFF9C4"  # yellow tint banner bg
COLOUR_BANNER_NO_MATCH = "#E3F2FD"   # blue tint banner bg

# Text colours for banners
COLOUR_BANNER_PRESENT_TEXT = "#B71C1C"
COLOUR_BANNER_MAY_CONTAIN_TEXT = "#BF360C"
COLOUR_BANNER_UNCERTAIN_TEXT = "#F57F17"
COLOUR_BANNER_NO_MATCH_TEXT = "#0D47A1"

# ── Fuzzy matching ────────────────────────────────────────────────────────────
DEFAULT_FUZZY_THRESHOLD = 85

# ── Image upload ──────────────────────────────────────────────────────────────
MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB

# ── Vague ingredient terms → UNCERTAIN ───────────────────────────────────────
# These terms trigger UNCERTAIN status because they can hide allergens.
VAGUE_INGREDIENTS = [
    "natural flavour",
    "natural flavours",
    "natural flavoring",
    "natural flavorings",
    "artificial flavour",
    "artificial flavours",
    "artificial flavoring",
    "artificial flavorings",
    "flavouring",
    "flavourings",
    "flavoring",
    "flavorings",
    "spices",
    "spice",
    "mixed spices",
    "emulsifier",
    "emulsifiers",
    "modified starch",
    "modified food starch",
    "hydrolysed vegetable protein",
    "hydrolyzed vegetable protein",
    "hvp",
    "vegetable oil",
    "vegetable oils",
    "edible vegetable oil",
    "refined vegetable oil",
    "mixed vegetable oil",
    "starch",
    "food starch",
    "plant extract",
    "plant extracts",
    "herb extract",
    "herb extracts",
    "natural colour",
    "natural colours",
    "natural color",
    "natural colors",
    "colour",
    "colours",
    "permitted natural colour",
    "permitted natural colours",
]

# ── Trace / cross-contamination statement patterns ────────────────────────────
# Used to detect MAY CONTAIN situations.
import re

TRACE_PATTERNS = [
    re.compile(
        r"may\s+contain(?:\s+traces?\s+of)?",
        re.IGNORECASE,
    ),
    re.compile(
        r"manufactured\s+in\s+a\s+(?:factory|facility|plant)\s+(?:that\s+)?(?:also\s+)?(?:handles|processes|uses|produces)",
        re.IGNORECASE,
    ),
    re.compile(
        r"produced\s+in\s+a\s+(?:factory|facility|plant)\s+(?:that\s+)?(?:also\s+)?(?:handles|processes|uses)",
        re.IGNORECASE,
    ),
    re.compile(
        r"made\s+in\s+a\s+(?:factory|facility|plant)\s+(?:that\s+)?(?:also\s+)?(?:handles|processes|uses)",
        re.IGNORECASE,
    ),
    re.compile(
        r"packed\s+in\s+a\s+(?:factory|facility|plant)\s+(?:that\s+)?(?:also\s+)?(?:handles|processes|uses)",
        re.IGNORECASE,
    ),
    re.compile(
        r"traces?\s+of",
        re.IGNORECASE,
    ),
    re.compile(
        r"cross[- ]contamination",
        re.IGNORECASE,
    ),
]

# ── Disclaimer ────────────────────────────────────────────────────────────────
DISCLAIMER_TEXT = (
    "⚠️ DISCLAIMER: This tool is an informational aid only, not medical advice. "
    "It may miss allergens due to OCR errors, incomplete dictionaries, or unlabelled ingredients. "
    "Always read the original product label carefully and consult a doctor or dietitian "
    "before making food choices based on allergy concerns. "
    "\"No known match found\" does not mean a product is free from an allergen."
)

DISCLAIMER_TEXT_SHORT = (
    "This tool is an aid, not medical advice. Always read the original label and consult a doctor."
)
