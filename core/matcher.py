"""
core/matcher.py — Allergen matching logic.

Pure functions. No Streamlit imports.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

from rapidfuzz import fuzz

from core.constants import (
    DEFAULT_FUZZY_THRESHOLD,
    STATUS_MAY_CONTAIN,
    STATUS_PRESENT,
    STATUS_UNCERTAIN,
    VAGUE_INGREDIENTS,
)
from core.ins_decoder import decode_ins, extract_ins_codes
from core.parser import ParseResult

# ── Type aliases ──────────────────────────────────────────────────────────────
MatchType = Literal["exact", "fuzzy", "ins", "trace", "vague"]
Status = Literal["PRESENT", "MAY_CONTAIN", "UNCERTAIN"]


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class AllergenEntry:
    """An allergen configured in a user profile."""
    name: str
    severity: Literal["mild", "moderate", "severe"] = "moderate"


@dataclass
class MatchedTerm:
    """A single matched token/term that contributed to a MatchResult."""
    term: str               # the token as it appeared in the ingredient list
    explanation: str        # human-readable explanation
    match_type: MatchType   # how it was found
    synonym: str = ""       # canonical synonym matched (empty for direct match)


@dataclass
class MatchResult:
    """Result for a single allergen in a profile."""
    allergen: str
    severity: str
    status: Status
    emoji: str
    matched_terms: List[MatchedTerm] = field(default_factory=list)


# ── Status precedence ─────────────────────────────────────────────────────────
_STATUS_RANK: Dict[str, int] = {
    STATUS_PRESENT: 3,
    STATUS_MAY_CONTAIN: 2,
    STATUS_UNCERTAIN: 1,
}


def _higher_status(a: Optional[str], b: str) -> str:
    """Return the higher-priority status between a and b."""
    if a is None:
        return b
    return a if _STATUS_RANK.get(a, 0) >= _STATUS_RANK.get(b, 0) else b


# ── Vague ingredient detection ────────────────────────────────────────────────

# Build a set and also a set of normalised versions for fast lookup
_VAGUE_SET = {v.lower() for v in VAGUE_INGREDIENTS}


def _is_vague(token: str) -> bool:
    """Return True if the token matches a known vague ingredient."""
    t = token.lower().strip()
    if t in _VAGUE_SET:
        return True
    # A longer token contains a vague term (e.g. "permitted natural colour" contains "natural colour")
    # Only allow the vague term to be a substring of the token, not the other way around,
    # to avoid short vague terms like "spice" matching inside unrelated tokens.
    for vague in _VAGUE_SET:
        if len(vague) >= 6 and vague in t:
            return True
    return False


# ── Trace statement allergen extraction ───────────────────────────────────────

def _allergens_in_trace(trace_text: str, allergen_data: dict) -> List[str]:
    """
    Given a trace/cross-contamination statement, return which allergens
    (by canonical name) are mentioned in it.
    """
    lower = trace_text.lower()
    found: list[str] = []
    for allergen_name, allergen_info in allergen_data.items():
        # Check canonical name
        if allergen_name in lower:
            found.append(allergen_name)
            continue
        # Check synonyms
        for syn_entry in allergen_info.get("synonyms", []):
            if syn_entry["term"] in lower:
                found.append(allergen_name)
                break
    return found


# ── Main matching function ────────────────────────────────────────────────────

def match_allergens(
    parse_result: ParseResult,
    profile_allergens: List[AllergenEntry],
    allergen_data: dict,
    ins_data: dict,
    fuzzy_threshold: int = DEFAULT_FUZZY_THRESHOLD,
) -> List[MatchResult]:
    """
    Match a parsed ingredient list against the allergens configured in a profile.

    Args:
        parse_result:      Output from parser.parse_ingredients().
        profile_allergens: List of AllergenEntry from the active profile.
        allergen_data:     Loaded allergens.json dict.
        ins_data:          Loaded ins_codes.json dict.
        fuzzy_threshold:   Minimum rapidfuzz partial_ratio score (0–100).

    Returns:
        List of MatchResult, one per allergen that produced at least one match.
        Allergens with no matches are omitted.
    """
    if not parse_result.tokens and not parse_result.trace_statements:
        return []

    results: list[MatchResult] = []

    for entry in profile_allergens:
        allergen_name = entry.name.lower()
        allergen_info = allergen_data.get(allergen_name)
        if not allergen_info:
            # Custom allergen not in dictionary — skip allergen-data lookup,
            # but still do a direct token scan.
            allergen_info = {"emoji": "⚠️", "synonyms": [{"term": allergen_name, "explanation": f"{allergen_name} (custom allergen)"}]}

        emoji = allergen_info.get("emoji", "⚠️")
        synonyms: list[dict] = allergen_info.get("synonyms", [])

        current_status: Optional[str] = None
        matched_terms: list[MatchedTerm] = []
        seen_terms: set[str] = set()  # avoid duplicate MatchedTerm entries

        # ── 1. Scan tokens for exact & fuzzy matches ──────────────────────────
        for token in parse_result.tokens:
            token_lower = token.lower().strip()
            if not token_lower:
                continue

            # 1a. Vague ingredient check (UNCERTAIN for ALL profile allergens)
            if _is_vague(token_lower):
                if token_lower not in seen_terms:
                    seen_terms.add(token_lower)
                    matched_terms.append(MatchedTerm(
                        term=token_lower,
                        explanation=(
                            f'"{token_lower}" is a vague ingredient that may hide '
                            f"allergens including {allergen_name}"
                        ),
                        match_type="vague",
                    ))
                current_status = _higher_status(current_status, STATUS_UNCERTAIN)
                continue  # don't also try exact/fuzzy for the same token

            # 1b. INS code handling
            ins_codes_in_token = extract_ins_codes(token_lower)
            for code in ins_codes_in_token:
                decode = decode_ins(code, ins_data)
                if decode is None:
                    continue
                allergen_lower_list = [a.lower() for a in decode.possible_allergens]
                if allergen_name not in allergen_lower_list:
                    continue
                key = f"ins_{code}"
                if key in seen_terms:
                    continue
                seen_terms.add(key)
                if decode.variable_source:
                    current_status = _higher_status(current_status, STATUS_UNCERTAIN)
                    matched_terms.append(MatchedTerm(
                        term=token_lower,
                        explanation=decode.explanation,
                        match_type="ins",
                        synonym=f"INS {code}",
                    ))
                else:
                    current_status = _higher_status(current_status, STATUS_PRESENT)
                    matched_terms.append(MatchedTerm(
                        term=token_lower,
                        explanation=decode.explanation,
                        match_type="ins",
                        synonym=f"INS {code}",
                    ))

            # 1c. Exact substring match against synonyms
            matched_exact = False
            for syn_entry in synonyms:
                syn_term = syn_entry["term"].lower()
                explanation = syn_entry["explanation"]
                # Exact substring: synonym appears inside token or token inside synonym
                if syn_term in token_lower or token_lower in syn_term:
                    key = f"exact_{token_lower}"
                    if key not in seen_terms:
                        seen_terms.add(key)
                        matched_terms.append(MatchedTerm(
                            term=token_lower,
                            explanation=explanation,
                            match_type="exact",
                            synonym=syn_term,
                        ))
                    current_status = _higher_status(current_status, STATUS_PRESENT)
                    matched_exact = True
                    break

            if matched_exact:
                continue

            # 1d. Fuzzy match (only if no exact match found for this token)
            best_score = 0
            best_syn: Optional[dict] = None
            for syn_entry in synonyms:
                syn_term = syn_entry["term"].lower()
                # Length ratio guard: don't fuzzy-match tokens whose lengths differ
                # by more than 50% — prevents "whey" matching "wheat flour".
                len_ratio = min(len(syn_term), len(token_lower)) / max(len(syn_term), len(token_lower), 1)
                if len_ratio < 0.5:
                    continue
                # For short terms (<=8 chars) use full ratio (character-level similarity).
                # For longer terms use partial_ratio (substring alignment).
                # Threshold for short-term ratio is slightly lower (80) to catch
                # one-character typos like "casien" → "casein" (scores 83).
                if len(syn_term) <= 8:
                    score = fuzz.ratio(syn_term, token_lower)
                    effective_threshold = max(fuzzy_threshold - 5, 80)
                else:
                    score = fuzz.partial_ratio(syn_term, token_lower)
                    effective_threshold = fuzzy_threshold
                if score > best_score and score >= effective_threshold:
                    best_score = score
                    best_syn = syn_entry
            if best_syn:
                key = f"fuzzy_{token_lower}"
                if key not in seen_terms:
                    seen_terms.add(key)
                    matched_terms.append(MatchedTerm(
                        term=token_lower,
                        explanation=(
                            best_syn["explanation"]
                            + f" (fuzzy match with score {best_score}%)"
                        ),
                        match_type="fuzzy",
                        synonym=best_syn["term"].lower(),
                    ))
                current_status = _higher_status(current_status, STATUS_PRESENT)

        # ── 2. Scan trace statements for MAY_CONTAIN ─────────────────────────
        for trace in parse_result.trace_statements:
            allergens_in_trace = _allergens_in_trace(trace, allergen_data)
            if allergen_name in allergens_in_trace:
                key = f"trace_{trace[:40]}"
                if key not in seen_terms:
                    seen_terms.add(key)
                    matched_terms.append(MatchedTerm(
                        term=trace,
                        explanation=(
                            f'Cross-contamination statement: "{trace}" '
                            f"mentions {allergen_name}"
                        ),
                        match_type="trace",
                    ))
                # MAY_CONTAIN only upgrades status if PRESENT isn't already set
                current_status = _higher_status(current_status, STATUS_MAY_CONTAIN)

        # ── 3. Collect result if any match was found ──────────────────────────
        if current_status is not None and matched_terms:
            results.append(MatchResult(
                allergen=entry.name,
                severity=entry.severity,
                status=current_status,
                emoji=emoji,
                matched_terms=matched_terms,
            ))

    return results
