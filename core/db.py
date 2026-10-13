"""
core/db.py — SQLite persistence layer.

No Streamlit imports. All SQL is in this module.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

DB_PATH = Path(__file__).parent.parent / "allergy_checker.db"

# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class Profile:
    id: int
    name: str
    created_at: str


@dataclass
class AllergenEntry:
    allergen: str
    severity: str  # 'mild' | 'moderate' | 'severe'


@dataclass
class HistoryEntry:
    id: int
    profile_id: int
    profile_name: str
    timestamp: str
    ingredient_text: str
    results_json: str   # raw JSON string
    summary_status: str


# ── Connection helper ─────────────────────────────────────────────────────────

@contextmanager
def _get_conn(db_path: Path = DB_PATH):
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── Schema initialisation ─────────────────────────────────────────────────────

def init_db(db_path: Path = DB_PATH) -> None:
    """Create tables if they do not exist and seed the Demo profile."""
    with _get_conn(db_path) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS profiles (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS profile_allergens (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER NOT NULL
                               REFERENCES profiles(id) ON DELETE CASCADE,
                allergen   TEXT NOT NULL,
                severity   TEXT NOT NULL
                               CHECK(severity IN ('mild','moderate','severe')),
                UNIQUE(profile_id, allergen)
            );

            CREATE TABLE IF NOT EXISTS history (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id      INTEGER NOT NULL
                                    REFERENCES profiles(id) ON DELETE CASCADE,
                timestamp       TEXT NOT NULL,
                ingredient_text TEXT NOT NULL,
                results_json    TEXT NOT NULL,
                summary_status  TEXT NOT NULL
            );
        """)

        # Seed the Demo profile once
        existing = conn.execute(
            "SELECT id FROM profiles WHERE name = 'Demo'"
        ).fetchone()
        if existing is None:
            conn.execute(
                "INSERT INTO profiles (name, created_at) VALUES (?, ?)",
                ("Demo", _now()),
            )
            row = conn.execute(
                "SELECT id FROM profiles WHERE name = 'Demo'"
            ).fetchone()
            demo_id = row["id"]
            conn.executemany(
                "INSERT OR IGNORE INTO profile_allergens (profile_id, allergen, severity) "
                "VALUES (?, ?, ?)",
                [
                    (demo_id, "milk", "severe"),
                    (demo_id, "soy",  "moderate"),
                ],
            )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Profile CRUD ──────────────────────────────────────────────────────────────

def create_profile(name: str, db_path: Path = DB_PATH) -> int:
    """
    Create a new profile.

    Returns:
        The new profile's ID.

    Raises:
        ValueError: If name is empty or already taken.
    """
    name = name.strip()
    if not name:
        raise ValueError("Profile name must not be empty.")
    with _get_conn(db_path) as conn:
        existing = conn.execute(
            "SELECT id FROM profiles WHERE lower(name) = lower(?)", (name,)
        ).fetchone()
        if existing:
            raise ValueError(f'A profile named "{name}" already exists.')
        conn.execute(
            "INSERT INTO profiles (name, created_at) VALUES (?, ?)",
            (name, _now()),
        )
        row = conn.execute(
            "SELECT id FROM profiles WHERE lower(name) = lower(?)", (name,)
        ).fetchone()
        return row["id"]


def get_profiles(db_path: Path = DB_PATH) -> List[Profile]:
    """Return all profiles ordered by creation date."""
    with _get_conn(db_path) as conn:
        rows = conn.execute(
            "SELECT id, name, created_at FROM profiles ORDER BY created_at"
        ).fetchall()
    return [Profile(id=r["id"], name=r["name"], created_at=r["created_at"]) for r in rows]


def delete_profile(profile_id: int, db_path: Path = DB_PATH) -> None:
    """Delete a profile and all its allergens and history (CASCADE)."""
    with _get_conn(db_path) as conn:
        conn.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))


def rename_profile(profile_id: int, new_name: str, db_path: Path = DB_PATH) -> None:
    """Rename a profile."""
    new_name = new_name.strip()
    if not new_name:
        raise ValueError("Profile name must not be empty.")
    with _get_conn(db_path) as conn:
        existing = conn.execute(
            "SELECT id FROM profiles WHERE lower(name) = lower(?) AND id != ?",
            (new_name, profile_id),
        ).fetchone()
        if existing:
            raise ValueError(f'A profile named "{new_name}" already exists.')
        conn.execute(
            "UPDATE profiles SET name = ? WHERE id = ?", (new_name, profile_id)
        )


# ── Allergen management ───────────────────────────────────────────────────────

def get_allergens_for_profile(
    profile_id: int, db_path: Path = DB_PATH
) -> List[AllergenEntry]:
    """Return the allergen list for a profile."""
    with _get_conn(db_path) as conn:
        rows = conn.execute(
            "SELECT allergen, severity FROM profile_allergens "
            "WHERE profile_id = ? ORDER BY allergen",
            (profile_id,),
        ).fetchall()
    return [AllergenEntry(allergen=r["allergen"], severity=r["severity"]) for r in rows]


def set_allergens_for_profile(
    profile_id: int,
    allergens: List[AllergenEntry],
    db_path: Path = DB_PATH,
) -> None:
    """
    Replace the allergen list for a profile (delete-all then insert).
    """
    with _get_conn(db_path) as conn:
        conn.execute(
            "DELETE FROM profile_allergens WHERE profile_id = ?", (profile_id,)
        )
        conn.executemany(
            "INSERT INTO profile_allergens (profile_id, allergen, severity) "
            "VALUES (?, ?, ?)",
            [(profile_id, a.allergen.lower().strip(), a.severity) for a in allergens],
        )


def add_allergen_to_profile(
    profile_id: int,
    allergen: str,
    severity: str,
    db_path: Path = DB_PATH,
) -> None:
    """Add or update a single allergen for a profile."""
    with _get_conn(db_path) as conn:
        conn.execute(
            "INSERT INTO profile_allergens (profile_id, allergen, severity) "
            "VALUES (?, ?, ?) "
            "ON CONFLICT(profile_id, allergen) DO UPDATE SET severity = excluded.severity",
            (profile_id, allergen.lower().strip(), severity),
        )


def remove_allergen_from_profile(
    profile_id: int,
    allergen: str,
    db_path: Path = DB_PATH,
) -> None:
    """Remove a single allergen from a profile."""
    with _get_conn(db_path) as conn:
        conn.execute(
            "DELETE FROM profile_allergens WHERE profile_id = ? AND allergen = ?",
            (profile_id, allergen.lower().strip()),
        )


# ── History ───────────────────────────────────────────────────────────────────

def save_history(
    profile_id: int,
    ingredient_text: str,
    results_json: str,
    summary_status: str,
    db_path: Path = DB_PATH,
) -> int:
    """Save a check result to history. Returns the new history entry id."""
    with _get_conn(db_path) as conn:
        conn.execute(
            "INSERT INTO history "
            "(profile_id, timestamp, ingredient_text, results_json, summary_status) "
            "VALUES (?, ?, ?, ?, ?)",
            (profile_id, _now(), ingredient_text, results_json, summary_status),
        )
        row = conn.execute("SELECT last_insert_rowid() AS id").fetchone()
        return row["id"]


def get_history(
    profile_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    limit: int = 200,
    db_path: Path = DB_PATH,
) -> List[HistoryEntry]:
    """
    Return history entries, optionally filtered by profile and/or status.
    Most recent first.
    """
    query = """
        SELECT h.id, h.profile_id, p.name AS profile_name,
               h.timestamp, h.ingredient_text, h.results_json, h.summary_status
        FROM history h
        JOIN profiles p ON p.id = h.profile_id
        WHERE 1=1
    """
    params: list = []
    if profile_id is not None:
        query += " AND h.profile_id = ?"
        params.append(profile_id)
    if status_filter:
        query += " AND h.summary_status = ?"
        params.append(status_filter)
    query += " ORDER BY h.timestamp DESC LIMIT ?"
    params.append(limit)

    with _get_conn(db_path) as conn:
        rows = conn.execute(query, params).fetchall()

    return [
        HistoryEntry(
            id=r["id"],
            profile_id=r["profile_id"],
            profile_name=r["profile_name"],
            timestamp=r["timestamp"],
            ingredient_text=r["ingredient_text"],
            results_json=r["results_json"],
            summary_status=r["summary_status"],
        )
        for r in rows
    ]


def delete_history_entry(entry_id: int, db_path: Path = DB_PATH) -> None:
    """Delete a single history entry."""
    with _get_conn(db_path) as conn:
        conn.execute("DELETE FROM history WHERE id = ?", (entry_id,))


def get_history_entry(entry_id: int, db_path: Path = DB_PATH) -> Optional[HistoryEntry]:
    """Fetch a single history entry by ID."""
    with _get_conn(db_path) as conn:
        row = conn.execute(
            """
            SELECT h.id, h.profile_id, p.name AS profile_name,
                   h.timestamp, h.ingredient_text, h.results_json, h.summary_status
            FROM history h
            JOIN profiles p ON p.id = h.profile_id
            WHERE h.id = ?
            """,
            (entry_id,),
        ).fetchone()
    if row is None:
        return None
    return HistoryEntry(
        id=row["id"],
        profile_id=row["profile_id"],
        profile_name=row["profile_name"],
        timestamp=row["timestamp"],
        ingredient_text=row["ingredient_text"],
        results_json=row["results_json"],
        summary_status=row["summary_status"],
    )
