"""Tests for core/db.py"""
import json
import tempfile
from pathlib import Path

import pytest

from core.db import (
    AllergenEntry,
    add_allergen_to_profile,
    create_profile,
    delete_history_entry,
    delete_profile,
    get_allergens_for_profile,
    get_history,
    get_history_entry,
    get_profiles,
    init_db,
    remove_allergen_from_profile,
    save_history,
    set_allergens_for_profile,
)


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "test.db"
    init_db(db_path=path)
    return path


# ── Profile CRUD ──────────────────────────────────────────────────────────────

def test_demo_profile_seeded(db_path):
    profiles = get_profiles(db_path=db_path)
    names = [p.name for p in profiles]
    assert "Demo" in names


def test_create_profile(db_path):
    pid = create_profile("Me", db_path=db_path)
    assert isinstance(pid, int)
    profiles = get_profiles(db_path=db_path)
    assert any(p.name == "Me" for p in profiles)


def test_create_duplicate_profile_raises(db_path):
    create_profile("Mom", db_path=db_path)
    with pytest.raises(ValueError, match="already exists"):
        create_profile("Mom", db_path=db_path)


def test_create_empty_name_raises(db_path):
    with pytest.raises(ValueError):
        create_profile("", db_path=db_path)


def test_delete_profile(db_path):
    pid = create_profile("Temp", db_path=db_path)
    delete_profile(pid, db_path=db_path)
    profiles = get_profiles(db_path=db_path)
    assert not any(p.name == "Temp" for p in profiles)


# ── Allergen management ───────────────────────────────────────────────────────

def test_set_and_get_allergens(db_path):
    pid = create_profile("Test", db_path=db_path)
    allergens = [
        AllergenEntry(allergen="milk", severity="severe"),
        AllergenEntry(allergen="wheat", severity="mild"),
    ]
    set_allergens_for_profile(pid, allergens, db_path=db_path)
    fetched = get_allergens_for_profile(pid, db_path=db_path)
    assert len(fetched) == 2
    fetched_names = {a.allergen for a in fetched}
    assert "milk" in fetched_names
    assert "wheat" in fetched_names


def test_set_allergens_replaces_existing(db_path):
    pid = create_profile("Test2", db_path=db_path)
    set_allergens_for_profile(pid, [AllergenEntry("milk", "severe")], db_path=db_path)
    set_allergens_for_profile(pid, [AllergenEntry("wheat", "mild")], db_path=db_path)
    fetched = get_allergens_for_profile(pid, db_path=db_path)
    names = {a.allergen for a in fetched}
    assert "wheat" in names
    assert "milk" not in names


def test_add_allergen_to_profile(db_path):
    pid = create_profile("Test3", db_path=db_path)
    add_allergen_to_profile(pid, "peanut", "severe", db_path=db_path)
    fetched = get_allergens_for_profile(pid, db_path=db_path)
    assert any(a.allergen == "peanut" for a in fetched)


def test_remove_allergen_from_profile(db_path):
    pid = create_profile("Test4", db_path=db_path)
    add_allergen_to_profile(pid, "egg", "moderate", db_path=db_path)
    remove_allergen_from_profile(pid, "egg", db_path=db_path)
    fetched = get_allergens_for_profile(pid, db_path=db_path)
    assert not any(a.allergen == "egg" for a in fetched)


def test_demo_profile_allergens_seeded(db_path):
    profiles = get_profiles(db_path=db_path)
    demo = next(p for p in profiles if p.name == "Demo")
    allergens = get_allergens_for_profile(demo.id, db_path=db_path)
    names = {a.allergen for a in allergens}
    assert "milk" in names
    assert "soy" in names


def test_demo_milk_severity_is_severe(db_path):
    profiles = get_profiles(db_path=db_path)
    demo = next(p for p in profiles if p.name == "Demo")
    allergens = get_allergens_for_profile(demo.id, db_path=db_path)
    milk = next(a for a in allergens if a.allergen == "milk")
    assert milk.severity == "severe"


# ── History ───────────────────────────────────────────────────────────────────

def test_save_and_get_history(db_path):
    pid = create_profile("HistTest", db_path=db_path)
    hid = save_history(
        profile_id=pid,
        ingredient_text="sugar, whey",
        results_json=json.dumps([{"allergen": "milk", "status": "PRESENT"}]),
        summary_status="PRESENT",
        db_path=db_path,
    )
    assert isinstance(hid, int)
    entries = get_history(profile_id=pid, db_path=db_path)
    assert len(entries) == 1
    assert entries[0].ingredient_text == "sugar, whey"
    assert entries[0].summary_status == "PRESENT"


def test_history_filter_by_status(db_path):
    pid = create_profile("FilterTest", db_path=db_path)
    save_history(pid, "sugar", json.dumps([]), "PRESENT", db_path=db_path)
    save_history(pid, "salt",  json.dumps([]), "NO_MATCH", db_path=db_path)
    present = get_history(profile_id=pid, status_filter="PRESENT", db_path=db_path)
    no_match = get_history(profile_id=pid, status_filter="NO_MATCH", db_path=db_path)
    assert len(present) == 1
    assert len(no_match) == 1


def test_delete_history_entry(db_path):
    pid = create_profile("DelTest", db_path=db_path)
    hid = save_history(pid, "test", json.dumps([]), "NO_MATCH", db_path=db_path)
    delete_history_entry(hid, db_path=db_path)
    entries = get_history(profile_id=pid, db_path=db_path)
    assert len(entries) == 0


def test_get_history_entry_by_id(db_path):
    pid = create_profile("GetByID", db_path=db_path)
    hid = save_history(pid, "wheat, gluten", json.dumps([]), "PRESENT", db_path=db_path)
    entry = get_history_entry(hid, db_path=db_path)
    assert entry is not None
    assert entry.ingredient_text == "wheat, gluten"


def test_cascade_delete_removes_history(db_path):
    pid = create_profile("Cascade", db_path=db_path)
    save_history(pid, "sugar", json.dumps([]), "NO_MATCH", db_path=db_path)
    delete_profile(pid, db_path=db_path)
    entries = get_history(profile_id=pid, db_path=db_path)
    assert entries == []
