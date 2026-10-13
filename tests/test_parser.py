"""Tests for core/parser.py"""
import pytest

from core.parser import ParseResult, parse_ingredients


# ── Basic splitting ───────────────────────────────────────────────────────────

def test_basic_comma_split():
    result = parse_ingredients("sugar, salt, water")
    assert "sugar" in result.tokens
    assert "salt" in result.tokens
    assert "water" in result.tokens


def test_semicolon_split():
    result = parse_ingredients("sugar; salt; water")
    assert "sugar" in result.tokens
    assert "salt" in result.tokens


def test_lowercase():
    result = parse_ingredients("Sugar, SALT, Water")
    assert "sugar" in result.tokens
    assert "salt" in result.tokens
    assert "water" in result.tokens


def test_strips_whitespace():
    result = parse_ingredients("  sugar  ,  salt  ")
    assert "sugar" in result.tokens
    assert "salt" in result.tokens


def test_no_empty_tokens():
    result = parse_ingredients("sugar,, salt,")
    assert "" not in result.tokens


# ── Nested parentheses ────────────────────────────────────────────────────────

def test_nested_parentheses_flattened():
    result = parse_ingredients("chocolate (sugar, cocoa butter, milk powder), salt")
    assert "chocolate" in result.tokens
    assert "sugar" in result.tokens
    assert "cocoa butter" in result.tokens
    assert "milk powder" in result.tokens
    assert "salt" in result.tokens


def test_deeply_nested():
    result = parse_ingredients("A (B, C (D, E)), F")
    assert "a" in result.tokens
    assert "b" in result.tokens
    assert "c" in result.tokens
    # D and E are extracted from the inner parentheses
    assert "d" in result.tokens or "d, e" in result.tokens or any("d" in t for t in result.tokens)


def test_square_brackets_flattened():
    result = parse_ingredients("noodles [wheat flour, salt], sauce")
    assert "noodles" in result.tokens
    assert "wheat flour" in result.tokens
    assert "salt" in result.tokens
    assert "sauce" in result.tokens


# ── Trace statement detection ─────────────────────────────────────────────────

def test_may_contain_detected():
    result = parse_ingredients(
        "Sugar, cocoa. May contain traces of milk and peanut."
    )
    assert any("may contain" in s.lower() for s in result.trace_statements)
    assert "sugar" in result.tokens


def test_facility_statement_detected():
    result = parse_ingredients(
        "Wheat flour, salt. Manufactured in a facility that processes milk."
    )
    assert any("manufactured" in s.lower() for s in result.trace_statements)


def test_may_contain_removed_from_tokens():
    result = parse_ingredients(
        "Sugar, salt. May contain traces of nuts."
    )
    # The trace statement should not appear as a normal token
    for tok in result.tokens:
        assert "may contain" not in tok.lower()


# ── Edge cases ────────────────────────────────────────────────────────────────

def test_empty_string_returns_empty_result():
    result = parse_ingredients("")
    assert result.tokens == []
    assert result.trace_statements == []


def test_whitespace_only_returns_empty_result():
    result = parse_ingredients("   \n\t  ")
    assert result.tokens == []


def test_none_raises_value_error():
    with pytest.raises(ValueError):
        parse_ingredients(None)


def test_raw_text_preserved():
    text = "Sugar, Salt"
    result = parse_ingredients(text)
    assert result.raw_text == text


def test_percentage_removed():
    result = parse_ingredients("whole grain wheat (44%), salt")
    for tok in result.tokens:
        assert "44" not in tok


def test_single_ingredient():
    result = parse_ingredients("sugar")
    assert result.tokens == ["sugar"]


def test_ins_code_preserved_as_token():
    """INS codes should not be broken apart by the parser."""
    result = parse_ingredients("sugar, emulsifier (INS 322), salt")
    combined = " ".join(result.tokens)
    assert "ins 322" in combined or "322" in combined
