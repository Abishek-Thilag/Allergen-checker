"""Tests for core/matcher.py"""
import json
from pathlib import Path
from typing import List

import pytest

from core.matcher import AllergenEntry, MatchResult, match_allergens
from core.parser import parse_ingredients
from core.constants import STATUS_PRESENT, STATUS_MAY_CONTAIN, STATUS_UNCERTAIN

BASE = Path(__file__).parent.parent / "data"


@pytest.fixture
def allergen_data():
    with open(BASE / "allergens.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def ins_data():
    with open(BASE / "ins_codes.json", encoding="utf-8") as f:
        return json.load(f)


def check(text: str, allergens: List[str], allergen_data, ins_data, severity="moderate"):
    profile = [AllergenEntry(name=a, severity=severity) for a in allergens]
    pr = parse_ingredients(text)
    return match_allergens(pr, profile, allergen_data, ins_data)


def find_result(results: List[MatchResult], allergen: str):
    for r in results:
        if r.allergen.lower() == allergen.lower():
            return r
    return None


# ── Synonym detection ─────────────────────────────────────────────────────────

def test_whey_detects_milk(allergen_data, ins_data):
    results = check("sugar, whey, cocoa", ["milk"], allergen_data, ins_data)
    r = find_result(results, "milk")
    assert r is not None
    assert r.status == STATUS_PRESENT


def test_casein_detects_milk(allergen_data, ins_data):
    results = check("sugar, casein, salt", ["milk"], allergen_data, ins_data)
    r = find_result(results, "milk")
    assert r is not None
    assert r.status == STATUS_PRESENT


def test_caseinate_detects_milk(allergen_data, ins_data):
    results = check("sodium caseinate, sugar", ["milk"], allergen_data, ins_data)
    r = find_result(results, "milk")
    assert r is not None
    assert r.status == STATUS_PRESENT


def test_albumin_detects_egg(allergen_data, ins_data):
    results = check("albumin, wheat", ["egg"], allergen_data, ins_data)
    r = find_result(results, "egg")
    assert r is not None
    assert r.status == STATUS_PRESENT


def test_ovalbumin_detects_egg(allergen_data, ins_data):
    results = check("ovalbumin, sugar", ["egg"], allergen_data, ins_data)
    r = find_result(results, "egg")
    assert r is not None
    assert r.status == STATUS_PRESENT


# ── Indian names ──────────────────────────────────────────────────────────────

def test_maida_detects_wheat(allergen_data, ins_data):
    results = check("maida, sugar, salt", ["wheat"], allergen_data, ins_data)
    r = find_result(results, "wheat")
    assert r is not None
    assert r.status == STATUS_PRESENT


def test_atta_detects_wheat(allergen_data, ins_data):
    results = check("atta, water, yeast", ["wheat"], allergen_data, ins_data)
    r = find_result(results, "wheat")
    assert r is not None
    assert r.status == STATUS_PRESENT


def test_rava_detects_wheat(allergen_data, ins_data):
    results = check("rava, salt, oil", ["wheat"], allergen_data, ins_data)
    r = find_result(results, "wheat")
    assert r is not None


def test_groundnut_detects_peanut(allergen_data, ins_data):
    results = check("groundnut oil, salt", ["peanut"], allergen_data, ins_data)
    r = find_result(results, "peanut")
    assert r is not None
    assert r.status == STATUS_PRESENT


def test_dahi_detects_milk(allergen_data, ins_data):
    results = check("dahi, sugar", ["milk"], allergen_data, ins_data)
    r = find_result(results, "milk")
    assert r is not None
    assert r.status == STATUS_PRESENT


def test_ghee_detects_milk(allergen_data, ins_data):
    results = check("ghee, sugar, salt", ["milk"], allergen_data, ins_data)
    r = find_result(results, "milk")
    assert r is not None
    assert r.status == STATUS_PRESENT


def test_paneer_detects_milk(allergen_data, ins_data):
    results = check("paneer, spices", ["milk"], allergen_data, ins_data)
    r = find_result(results, "milk")
    assert r is not None
    assert r.status == STATUS_PRESENT


def test_til_detects_sesame(allergen_data, ins_data):
    results = check("til seeds, sugar", ["sesame"], allergen_data, ins_data)
    r = find_result(results, "sesame")
    assert r is not None
    assert r.status == STATUS_PRESENT


def test_rai_detects_mustard(allergen_data, ins_data):
    results = check("rai, curry leaves, salt", ["mustard"], allergen_data, ins_data)
    r = find_result(results, "mustard")
    assert r is not None
    assert r.status == STATUS_PRESENT


def test_badam_detects_tree_nuts(allergen_data, ins_data):
    results = check("badam, kaju, pista", ["tree nuts"], allergen_data, ins_data)
    r = find_result(results, "tree nuts")
    assert r is not None
    assert r.status == STATUS_PRESENT


# ── INS code handling ─────────────────────────────────────────────────────────

def test_ins322_space_uncertain_for_soy(allergen_data, ins_data):
    results = check("sugar, emulsifier INS 322, cocoa", ["soy"], allergen_data, ins_data)
    r = find_result(results, "soy")
    assert r is not None
    assert r.status == STATUS_UNCERTAIN


def test_ins322_nospace_uncertain_for_soy(allergen_data, ins_data):
    results = check("sugar, emulsifier INS322, cocoa", ["soy"], allergen_data, ins_data)
    r = find_result(results, "soy")
    assert r is not None
    assert r.status == STATUS_UNCERTAIN


def test_e322_uncertain_for_soy(allergen_data, ins_data):
    results = check("sugar, E322, salt", ["soy"], allergen_data, ins_data)
    r = find_result(results, "soy")
    assert r is not None
    assert r.status == STATUS_UNCERTAIN


def test_parenthesis_322_uncertain(allergen_data, ins_data):
    results = check("emulsifier (322), sugar", ["soy"], allergen_data, ins_data)
    r = find_result(results, "soy")
    assert r is not None
    assert r.status == STATUS_UNCERTAIN


def test_ins322_uncertain_for_egg(allergen_data, ins_data):
    results = check("chocolate, INS 322, milk powder", ["egg"], allergen_data, ins_data)
    r = find_result(results, "egg")
    assert r is not None
    assert r.status == STATUS_UNCERTAIN


def test_ins1105_present_for_egg(allergen_data, ins_data):
    """INS 1105 (lysozyme from egg) has variable_source=False, so it is PRESENT."""
    results = check("cheese, INS 1105, salt", ["egg"], allergen_data, ins_data)
    r = find_result(results, "egg")
    assert r is not None
    assert r.status == STATUS_PRESENT


# ── Fuzzy matching ────────────────────────────────────────────────────────────

def test_fuzzy_peanutt(allergen_data, ins_data):
    results = check("peanutt, sugar", ["peanut"], allergen_data, ins_data)
    r = find_result(results, "peanut")
    assert r is not None
    assert r.status == STATUS_PRESENT


def test_fuzzy_casien(allergen_data, ins_data):
    results = check("casien, sugar", ["milk"], allergen_data, ins_data)
    r = find_result(results, "milk")
    assert r is not None
    assert r.status == STATUS_PRESENT


def test_fuzzy_sesam(allergen_data, ins_data):
    results = check("sesam seeds, sugar", ["sesame"], allergen_data, ins_data)
    r = find_result(results, "sesame")
    assert r is not None


# ── Vague ingredients ─────────────────────────────────────────────────────────

def test_natural_flavours_uncertain(allergen_data, ins_data):
    results = check("sugar, natural flavours, cocoa", ["milk"], allergen_data, ins_data)
    r = find_result(results, "milk")
    assert r is not None
    assert r.status == STATUS_UNCERTAIN


def test_spices_uncertain(allergen_data, ins_data):
    results = check("wheat, spices, salt", ["milk"], allergen_data, ins_data)
    r = find_result(results, "milk")
    assert r is not None
    assert r.status == STATUS_UNCERTAIN


def test_emulsifier_uncertain(allergen_data, ins_data):
    results = check("sugar, emulsifier, cocoa butter", ["soy"], allergen_data, ins_data)
    r = find_result(results, "soy")
    assert r is not None
    assert r.status == STATUS_UNCERTAIN


# ── MAY CONTAIN (trace statements) ───────────────────────────────────────────

def test_may_contain_milk(allergen_data, ins_data):
    results = check(
        "sugar, cocoa. May contain traces of milk.",
        ["milk"],
        allergen_data,
        ins_data,
    )
    r = find_result(results, "milk")
    assert r is not None
    assert r.status == STATUS_MAY_CONTAIN


def test_facility_statement_wheat(allergen_data, ins_data):
    results = check(
        "oats, honey. Manufactured in a facility that processes wheat.",
        ["wheat"],
        allergen_data,
        ins_data,
    )
    r = find_result(results, "wheat")
    assert r is not None
    assert r.status == STATUS_MAY_CONTAIN


# ── Status precedence ─────────────────────────────────────────────────────────

def test_present_beats_uncertain(allergen_data, ins_data):
    """If a token is PRESENT and another is UNCERTAIN, result must be PRESENT."""
    results = check(
        "casein, natural flavours, sugar",
        ["milk"],
        allergen_data,
        ins_data,
    )
    r = find_result(results, "milk")
    assert r is not None
    assert r.status == STATUS_PRESENT


def test_present_beats_may_contain(allergen_data, ins_data):
    text = "sugar, whey, cocoa. May contain traces of milk."
    results = check(text, ["milk"], allergen_data, ins_data)
    r = find_result(results, "milk")
    assert r is not None
    assert r.status == STATUS_PRESENT


# ── Nested ingredients (demo scenario) ───────────────────────────────────────

def test_nested_milk_powder_detected(allergen_data, ins_data):
    results = check(
        "chocolate (sugar, cocoa butter, milk powder), salt",
        ["milk"],
        allergen_data,
        ins_data,
    )
    r = find_result(results, "milk")
    assert r is not None
    assert r.status == STATUS_PRESENT


# ── DEMO scenario ─────────────────────────────────────────────────────────────

def test_demo_scenario_no_milk_soy_word(allergen_data, ins_data):
    """
    The demo label contains casein, whey, INS 322, natural flavours
    but never writes 'milk' or 'soy'.
    - casein/whey → milk PRESENT
    - INS 322 → soy UNCERTAIN
    - natural flavours → both UNCERTAIN (but milk overridden by PRESENT)
    """
    text = (
        "Sugar, cocoa butter, cocoa mass, casein, whey, "
        "emulsifier (INS 322), natural flavours, vanilla extract, salt."
    )
    results = check(text, ["milk", "soy"], allergen_data, ins_data)

    milk_r = find_result(results, "milk")
    soy_r = find_result(results, "soy")

    assert milk_r is not None
    assert milk_r.status == STATUS_PRESENT

    assert soy_r is not None
    assert soy_r.status == STATUS_UNCERTAIN


# ── Edge cases ────────────────────────────────────────────────────────────────

def test_empty_text_returns_empty(allergen_data, ins_data):
    results = check("", ["milk", "wheat"], allergen_data, ins_data)
    assert results == []


def test_no_match_result_empty(allergen_data, ins_data):
    results = check("water, salt, sugar", ["milk"], allergen_data, ins_data)
    assert results == []


def test_no_match_never_says_safe(allergen_data, ins_data):
    """Verify that no MatchResult carries any 'safe' wording."""
    results = check("water, salt", ["milk"], allergen_data, ins_data)
    for r in results:
        for mt in r.matched_terms:
            assert "safe" not in mt.explanation.lower()
            assert "allergen-free" not in mt.explanation.lower()


def test_multiple_allergens_independent(allergen_data, ins_data):
    text = "whey, groundnut, sugar"
    results = check(text, ["milk", "peanut", "wheat"], allergen_data, ins_data)
    allergen_names = {r.allergen for r in results}
    assert "milk" in allergen_names
    assert "peanut" in allergen_names
    assert "wheat" not in allergen_names  # not in text


def test_severity_stored_in_result(allergen_data, ins_data):
    profile = [AllergenEntry(name="milk", severity="severe")]
    pr = parse_ingredients("casein, sugar")
    results = match_allergens(pr, profile, allergen_data, ins_data)
    assert results[0].severity == "severe"
