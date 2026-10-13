"""Tests for core/report.py"""
import pytest

from core.matcher import MatchedTerm, MatchResult
from core.report import generate_pdf
from core.constants import STATUS_PRESENT, STATUS_UNCERTAIN, STATUS_NO_MATCH


def _sample_results():
    return [
        MatchResult(
            allergen="milk",
            severity="severe",
            status=STATUS_PRESENT,
            emoji="🥛",
            matched_terms=[
                MatchedTerm(
                    term="casein",
                    explanation="casein is the primary milk protein",
                    match_type="exact",
                    synonym="casein",
                )
            ],
        ),
        MatchResult(
            allergen="soy",
            severity="moderate",
            status=STATUS_UNCERTAIN,
            emoji="🫘",
            matched_terms=[
                MatchedTerm(
                    term="ins 322",
                    explanation="INS 322 is lecithin, which can come from soy or sunflower",
                    match_type="ins",
                    synonym="INS 322",
                )
            ],
        ),
    ]


def test_pdf_generates_non_empty_bytes():
    pdf_bytes = generate_pdf(
        profile_name="Demo",
        timestamp="2026-10-12T15:00:00+00:00",
        ingredient_text="sugar, casein, INS 322, natural flavours",
        match_results=_sample_results(),
        summary_status=STATUS_PRESENT,
    )
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 100  # a real PDF is at least several KB


def test_pdf_starts_with_pdf_header():
    """PDF files always start with %PDF-"""
    pdf_bytes = generate_pdf(
        profile_name="Me",
        timestamp="2026-10-12T00:00:00+00:00",
        ingredient_text="whey, salt",
        match_results=_sample_results(),
        summary_status=STATUS_PRESENT,
    )
    assert pdf_bytes[:4] == b"%PDF"


def test_pdf_does_not_contain_word_safe():
    pdf_bytes = generate_pdf(
        profile_name="Me",
        timestamp="2026-10-12T00:00:00+00:00",
        ingredient_text="sugar, salt, water",
        match_results=[],
        summary_status=STATUS_NO_MATCH,
    )
    # Decode PDF bytes to text for simple word search (latin-1 preserves raw bytes)
    content = pdf_bytes.decode("latin-1", errors="replace").lower()
    assert "is safe" not in content
    assert "allergen-free" not in content


def test_pdf_with_no_results_no_match_status():
    pdf_bytes = generate_pdf(
        profile_name="Test",
        timestamp="2026-10-12T00:00:00+00:00",
        ingredient_text="water, salt",
        match_results=[],
        summary_status=STATUS_NO_MATCH,
    )
    assert len(pdf_bytes) > 0


def test_pdf_contains_disclaimer():
    pdf_bytes = generate_pdf(
        profile_name="Test",
        timestamp="2026-10-12T00:00:00+00:00",
        ingredient_text="water, salt",
        match_results=[],
        summary_status=STATUS_NO_MATCH,
    )
    # fpdf2 embeds text as PDF string literals — search the raw bytes
    # DISCLAIMER appears as a PDF text string in the content stream
    assert b"DISCLAIMER" in pdf_bytes


def test_pdf_contains_profile_name():
    pdf_bytes = generate_pdf(
        profile_name="UniqueProfileXYZ",
        timestamp="2026-10-12T00:00:00+00:00",
        ingredient_text="sugar",
        match_results=[],
        summary_status=STATUS_NO_MATCH,
    )
    assert b"UniqueProfileXYZ" in pdf_bytes


def test_pdf_no_match_says_no_known_match():
    pdf_bytes = generate_pdf(
        profile_name="Test",
        timestamp="2026-10-12T00:00:00+00:00",
        ingredient_text="sugar, water",
        match_results=[],
        summary_status=STATUS_NO_MATCH,
    )
    # "No known match found" must appear as plain text in the PDF stream
    assert b"No known match found" in pdf_bytes
