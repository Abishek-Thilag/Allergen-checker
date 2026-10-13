"""
core/parser.py — Ingredient text parser.

No Streamlit imports. Pure functions only.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

from core.constants import TRACE_PATTERNS


@dataclass
class ParseResult:
    """Result of parsing an ingredient list."""
    tokens: List[str] = field(default_factory=list)
    trace_statements: List[str] = field(default_factory=list)
    raw_text: str = ""


# Regex to split on commas, semicolons, and brackets (opening only — we
# handle brackets by flattening them first).
_SPLIT_RE = re.compile(r"[,;]+")

# Regex to detect INS/E codes so we don't accidentally split "INS 322" on spaces.
# We pre-protect them before splitting.
_INS_RE = re.compile(
    r"\b(?:INS\s*\d{3,4}[a-z]?|E\d{3,4}[a-z]?)\b",
    re.IGNORECASE,
)


def _extract_trace_statements(text: str) -> tuple[list[str], str]:
    """
    Scan 'text' for lines / sentences that look like trace / facility
    statements.  Return (list_of_trace_statements, cleaned_text) where
    cleaned_text has those sentences removed so they are not double-counted
    as normal tokens.
    """
    trace_statements: list[str] = []
    remaining_lines: list[str] = []

    # Split on sentence-ending punctuation or newlines to examine each clause.
    clauses = re.split(r"[.\n]+", text)
    for clause in clauses:
        stripped = clause.strip()
        if not stripped:
            continue
        matched = False
        for pattern in TRACE_PATTERNS:
            if pattern.search(stripped):
                trace_statements.append(stripped)
                matched = True
                break
        if not matched:
            remaining_lines.append(stripped)

    cleaned = ". ".join(remaining_lines)
    return trace_statements, cleaned


def _flatten_parentheses(text: str) -> str:
    """
    Replace parenthetical groups with their contents joined by commas so
    nested ingredients become top-level tokens.

    "chocolate (sugar, cocoa butter, milk powder)"
    → "chocolate, sugar, cocoa butter, milk powder"

    Handles one level of nesting; deeper nesting is flattened iteratively
    up to 5 passes.
    """
    paren_re = re.compile(r"\(([^()]*)\)")
    for _ in range(5):
        new_text, n = paren_re.subn(lambda m: ", " + m.group(1) + ",", text)
        if n == 0:
            break
        text = new_text
    # Clean up any doubled commas introduced by the substitution
    text = re.sub(r",\s*,+", ",", text)
    return text


def _flatten_brackets(text: str) -> str:
    """Same as _flatten_parentheses but for square brackets."""
    bracket_re = re.compile(r"\[([^\[\]]*)\]")
    for _ in range(5):
        new_text, n = bracket_re.subn(lambda m: ", " + m.group(1) + ",", text)
        if n == 0:
            break
        text = new_text
    text = re.sub(r",\s*,+", ",", text)
    return text


def parse_ingredients(text: str) -> ParseResult:
    """
    Parse a raw ingredient list string into a ParseResult.

    Steps:
    1. Validate input.
    2. Extract and remove trace/facility statements.
    3. Lowercase.
    4. Flatten nested parentheses and brackets.
    5. Split on commas and semicolons.
    6. Strip and deduplicate tokens.

    Args:
        text: Raw ingredient list string.

    Returns:
        ParseResult with tokens and trace_statements.

    Raises:
        ValueError: If text is None.
    """
    if text is None:
        raise ValueError("Ingredient text must not be None.")

    raw = text
    text = text.strip()
    if not text:
        return ParseResult(tokens=[], trace_statements=[], raw_text=raw)

    # 1. Extract trace statements before lowercasing so patterns match correctly.
    trace_statements, cleaned = _extract_trace_statements(text)

    # 2. Lowercase
    cleaned = cleaned.lower()

    # 3. Flatten nested groups
    cleaned = _flatten_parentheses(cleaned)
    cleaned = _flatten_brackets(cleaned)

    # 4. Remove percentage annotations like "(44%)" or "44%" after a token
    cleaned = re.sub(r"\b\d+(?:\.\d+)?\s*%", "", cleaned)

    # 5. Split on commas / semicolons
    raw_tokens = _SPLIT_RE.split(cleaned)

    # 6. Clean up each token
    tokens: list[str] = []
    seen: set[str] = set()
    for tok in raw_tokens:
        tok = tok.strip(" \t\r\n.[]()\"'")
        # Remove leading/trailing punctuation that slipped through
        tok = re.sub(r"^[\W_]+|[\W_]+$", "", tok)
        if tok and tok not in seen:
            seen.add(tok)
            tokens.append(tok)

    return ParseResult(tokens=tokens, trace_statements=trace_statements, raw_text=raw)
