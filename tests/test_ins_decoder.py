"""Tests for core/ins_decoder.py"""
import json
from pathlib import Path

import pytest

from core.ins_decoder import decode_ins, extract_ins_codes

# ── Load real ins_data ────────────────────────────────────────────────────────

INS_DATA_PATH = Path(__file__).parent.parent / "data" / "ins_codes.json"


@pytest.fixture
def ins_data():
    with open(INS_DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


# ── extract_ins_codes ─────────────────────────────────────────────────────────

def test_ins_space_format():
    codes = extract_ins_codes("emulsifier INS 322")
    assert "322" in codes


def test_ins_nospace_format():
    codes = extract_ins_codes("emulsifier INS322")
    assert "322" in codes


def test_e_format():
    codes = extract_ins_codes("emulsifier E322")
    assert "322" in codes


def test_parenthesis_format():
    codes = extract_ins_codes("emulsifier (322)")
    assert "322" in codes


def test_letter_suffix():
    codes = extract_ins_codes("colour INS 160a")
    assert "160a" in codes


def test_e_letter_suffix():
    codes = extract_ins_codes("antioxidant E307")
    assert "307" in codes


def test_multiple_codes():
    codes = extract_ins_codes("INS 322, INS 471, E631")
    assert "322" in codes
    assert "471" in codes
    assert "631" in codes


def test_empty_text_returns_empty():
    assert extract_ins_codes("") == []


def test_no_codes_returns_empty():
    assert extract_ins_codes("sugar, salt, water") == []


def test_case_insensitive_ins():
    codes = extract_ins_codes("ins 322")
    assert "322" in codes


# ── decode_ins ────────────────────────────────────────────────────────────────

def test_decode_322_variable_source(ins_data):
    result = decode_ins("322", ins_data)
    assert result is not None
    assert result.variable_source is True
    assert "soy" in result.possible_allergens or "egg" in result.possible_allergens


def test_decode_1105_egg_allergen(ins_data):
    result = decode_ins("1105", ins_data)
    assert result is not None
    assert "egg" in result.possible_allergens
    assert result.variable_source is False


def test_decode_322_name(ins_data):
    result = decode_ins("322", ins_data)
    assert result is not None
    assert "lecithin" in result.name.lower()


def test_decode_unknown_code_returns_none(ins_data):
    result = decode_ins("9999", ins_data)
    assert result is None


def test_decode_empty_code_returns_none(ins_data):
    result = decode_ins("", ins_data)
    assert result is None


def test_decode_none_ins_data():
    result = decode_ins("322", {})
    assert result is None


def test_decode_has_source(ins_data):
    result = decode_ins("322", ins_data)
    assert result is not None
    assert result.source != ""


def test_decode_has_explanation(ins_data):
    result = decode_ins("322", ins_data)
    assert result is not None
    assert len(result.explanation) > 10


def test_all_entries_have_source(ins_data):
    """Every INS entry must have a non-empty source field."""
    for code, entry in ins_data.items():
        assert entry.get("source"), f"INS {code} has no source"


def test_all_entries_have_explanation(ins_data):
    for code, entry in ins_data.items():
        assert entry.get("explanation"), f"INS {code} has no explanation"


def test_decode_631_fish_variable(ins_data):
    result = decode_ins("631", ins_data)
    assert result is not None
    assert "fish" in result.possible_allergens
    assert result.variable_source is True
