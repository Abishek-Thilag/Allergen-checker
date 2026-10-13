"""
core/ins_decoder.py — INS / E-number code extraction and decoding.

Handles formats: INS 322, INS322, E322, (322).
No Streamlit imports. Pure functions only.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

# Matches:
#   INS 322, INS322, INS 160a, INS160a  (with optional letter suffix)
#   E322, E160a
#   (322)  – bare number in parentheses (3–4 digits, optional letter)
_INS_PATTERN = re.compile(
    r"""
    (?:
        INS\s*(\d{3,4}[a-z]?)   # group 1: INS 322 / INS322 / INS160a
        |
        E(\d{3,4}[a-z]?)        # group 2: E322 / E160a
        |
        \((\d{3,4}[a-z]?)\)     # group 3: (322)
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)


@dataclass
class InsDecodeResult:
    """Result of decoding a single INS code."""
    code: str
    name: str
    possible_allergens: List[str]
    variable_source: bool
    explanation: str
    source: str


def extract_ins_codes(text: str) -> List[str]:
    """
    Extract all INS/E-number codes from a text string.

    Returns a list of normalised code strings (lowercase, e.g. "322", "160a").
    Duplicates are preserved (caller decides whether to deduplicate).

    Args:
        text: Any ingredient or label text.

    Returns:
        List of code strings.
    """
    if not text:
        return []
    codes: list[str] = []
    for m in _INS_PATTERN.finditer(text):
        code = (m.group(1) or m.group(2) or m.group(3) or "").lower().strip()
        if code:
            codes.append(code)
    return codes


def decode_ins(code: str, ins_data: dict) -> Optional[InsDecodeResult]:
    """
    Look up an INS code in the provided ins_data dictionary.

    Tries the code as-is, then normalises to lowercase.

    Args:
        code:     Code string, e.g. "322", "160a".
        ins_data: The parsed ins_codes.json dict.

    Returns:
        InsDecodeResult if found, None if the code is not in ins_data.
    """
    if not code or not ins_data:
        return None

    normalised = code.lower().strip()

    # Try exact match first, then lowercase
    entry = ins_data.get(code) or ins_data.get(normalised)
    if entry is None:
        return None

    return InsDecodeResult(
        code=normalised,
        name=entry.get("name", ""),
        possible_allergens=entry.get("possible_allergens", []),
        variable_source=entry.get("variable_source", False),
        explanation=entry.get("explanation", ""),
        source=entry.get("source", ""),
    )
