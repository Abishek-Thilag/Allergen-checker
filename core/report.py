"""
core/report.py — PDF report generation using fpdf2.

No Streamlit imports. Returns raw PDF bytes.
NEVER uses the words "safe" or "allergen-free".
"""
from __future__ import annotations

import textwrap
from pathlib import Path
from typing import List

from fpdf import FPDF, XPos, YPos

from core.constants import (
    DISCLAIMER_TEXT,
    STATUS_MAY_CONTAIN,
    STATUS_NO_MATCH,
    STATUS_PRESENT,
    STATUS_UNCERTAIN,
)
from core.matcher import MatchResult

# ── Colour map (RGB tuples) for PDF ──────────────────────────────────────────
_STATUS_RGB = {
    STATUS_PRESENT:     (211, 47,  47),   # red
    STATUS_MAY_CONTAIN: (230, 81,  0),    # deep orange
    STATUS_UNCERTAIN:   (249, 168, 37),   # amber
    STATUS_NO_MATCH:    (21,  101, 192),  # blue
}

_BANNER_RGB = {
    STATUS_PRESENT:     (255, 205, 210),
    STATUS_MAY_CONTAIN: (255, 224, 178),
    STATUS_UNCERTAIN:   (255, 249, 196),
    STATUS_NO_MATCH:    (227, 242, 253),
}

# Emoji → ASCII fallback for PDF (latin-1 font limitation)
_EMOJI_FALLBACK = {
    "🥛": "[milk]",
    "🥚": "[egg]",
    "🥜": "[peanut]",
    "🌰": "[tree nuts]",
    "🌾": "[wheat]",
    "🫘": "[soy]",
    "🐟": "[fish]",
    "🦐": "[shellfish]",
    "🌿": "[sesame/mustard]",
    "⚠️": "[!]",
}


def _safe_text(text: str) -> str:
    """Replace emoji and non-latin-1 chars with ASCII fallbacks for PDF rendering."""
    for emoji, fallback in _EMOJI_FALLBACK.items():
        text = text.replace(emoji, fallback)
    # Strip any remaining characters outside latin-1
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _determine_summary_status(match_results: List[MatchResult]) -> str:
    if not match_results:
        return STATUS_NO_MATCH
    statuses = {r.status for r in match_results}
    if STATUS_PRESENT in statuses:
        return STATUS_PRESENT
    for r in match_results:
        if r.status == STATUS_MAY_CONTAIN and r.severity == "severe":
            return STATUS_PRESENT
    if STATUS_MAY_CONTAIN in statuses:
        return STATUS_MAY_CONTAIN
    return STATUS_UNCERTAIN


class _PDF(FPDF):
    """FPDF subclass with a fixed footer."""

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(120, 120, 120)
        self.cell(
            0, 5,
            "DISCLAIMER: This tool is an aid, not medical advice. "
            "Always read the original label and consult a doctor.",
            new_x=XPos.LMARGIN, new_y=YPos.NEXT,
            align="C",
        )
        self.set_text_color(33, 33, 33)


def _cell(pdf: FPDF, w, h, txt, **kwargs):
    """Wrapper that maps legacy ln=True/False to new XPos/YPos API."""
    ln = kwargs.pop("ln", None)
    if ln is True:
        kwargs.setdefault("new_x", XPos.LMARGIN)
        kwargs.setdefault("new_y", YPos.NEXT)
    elif ln is False:
        kwargs.setdefault("new_x", XPos.RIGHT)
        kwargs.setdefault("new_y", YPos.TOP)
    pdf.cell(w, h, txt, **kwargs)


def generate_pdf(
    profile_name: str,
    timestamp: str,
    ingredient_text: str,
    match_results: List[MatchResult],
    summary_status: str,
) -> bytes:
    """
    Generate a PDF report for a completed allergen check.

    Returns raw PDF bytes suitable for st.download_button.
    """
    pdf = _PDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.compress = False  # keep content streams uncompressed so text is searchable in raw bytes
    pdf.add_page()

    # ── Header ────────────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(33, 33, 33)
    _cell(pdf, 0, 12, "Food Allergy Ingredient Checker", ln=True, align="C")

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 100, 100)
    _cell(pdf, 0, 6, "Spot hidden allergens in Indian food labels.", ln=True, align="C")
    pdf.ln(4)

    # ── Meta info ─────────────────────────────────────────────────────────────
    pdf.set_draw_color(200, 200, 200)
    pdf.set_line_width(0.3)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(33, 33, 33)
    _cell(pdf, 40, 6, "Profile:", ln=False)
    pdf.set_font("Helvetica", "B", 10)
    _cell(pdf, 0, 6, _safe_text(profile_name), ln=True)

    pdf.set_font("Helvetica", "", 10)
    _cell(pdf, 40, 6, "Date / Time:", ln=False)
    pdf.set_font("Helvetica", "B", 10)
    _cell(pdf, 0, 6, _safe_text(timestamp), ln=True)
    pdf.ln(4)

    # ── Risk summary banner ───────────────────────────────────────────────────
    banner_rgb = _BANNER_RGB.get(summary_status, (227, 242, 253))
    text_rgb = _STATUS_RGB.get(summary_status, (21, 101, 192))

    present_count = sum(1 for r in match_results if r.status == STATUS_PRESENT)
    may_count = sum(1 for r in match_results if r.status == STATUS_MAY_CONTAIN)
    uncertain_count = sum(1 for r in match_results if r.status == STATUS_UNCERTAIN)

    if summary_status == STATUS_NO_MATCH:
        banner_text = "No known match found"
    else:
        parts = []
        if present_count:
            parts.append(f"{present_count} PRESENT")
        if may_count:
            parts.append(f"{may_count} MAY CONTAIN")
        if uncertain_count:
            parts.append(f"{uncertain_count} UNCERTAIN")
        banner_text = ", ".join(parts)

    pdf.set_fill_color(*banner_rgb)
    pdf.set_text_color(*text_rgb)
    pdf.set_font("Helvetica", "B", 13)
    _cell(pdf, 0, 12, f"Risk Summary: {banner_text}", ln=True, fill=True, align="C")
    pdf.set_text_color(33, 33, 33)
    pdf.ln(3)

    # ── Ingredient text ───────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 11)
    _cell(pdf, 0, 7, "Ingredient List Checked:", ln=True)
    pdf.set_font("Helvetica", "", 9)
    wrapped = textwrap.fill(_safe_text(ingredient_text), width=110)
    pdf.set_fill_color(245, 245, 245)
    for line in wrapped.split("\n"):
        _cell(pdf, 0, 5, line, ln=True, fill=True)
    pdf.ln(4)

    # ── Flagged allergens ─────────────────────────────────────────────────────
    if match_results:
        pdf.set_font("Helvetica", "B", 12)
        _cell(pdf, 0, 8, "Flagged Allergens:", ln=True)
        pdf.ln(1)

        for result in match_results:
            status_rgb = _STATUS_RGB.get(result.status, (100, 100, 100))
            banner_fill = _BANNER_RGB.get(result.status, (230, 230, 230))

            pdf.set_fill_color(*banner_fill)
            pdf.set_text_color(*status_rgb)
            pdf.set_font("Helvetica", "B", 11)
            emoji_fb = _EMOJI_FALLBACK.get(result.emoji, result.emoji)
            label = f"  {emoji_fb}  {result.allergen.upper()}  -  {result.status.replace('_', ' ')}"
            _cell(pdf, 0, 9, _safe_text(label), ln=True, fill=True)
            pdf.set_text_color(33, 33, 33)

            pdf.set_font("Helvetica", "I", 9)
            pdf.set_fill_color(255, 255, 255)
            _cell(pdf, 0, 5, f"  Severity: {result.severity}", ln=True)

            pdf.set_font("Helvetica", "", 9)
            for mt in result.matched_terms:
                term_label = f"  - {mt.term}"
                if mt.synonym and mt.synonym != mt.term:
                    term_label += f" (matched as: {mt.synonym})"
                explanation_wrapped = textwrap.fill(mt.explanation, width=100)
                pdf.set_font("Helvetica", "B", 9)
                _cell(pdf, 0, 5, _safe_text(term_label), ln=True)
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(80, 80, 80)
                for line in explanation_wrapped.split("\n"):
                    _cell(pdf, 0, 4, _safe_text(f"    {line}"), ln=True)
                pdf.set_text_color(33, 33, 33)

            pdf.ln(3)
    else:
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(21, 101, 192)
        _cell(pdf, 0, 8,
              "No known match found for the allergens in this profile.",
              ln=True)
        pdf.set_text_color(33, 33, 33)

    # ── Full disclaimer block ─────────────────────────────────────────────────
    if pdf.get_y() > 240:
        pdf.add_page()
    else:
        pdf.ln(6)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(100, 50, 0)
    _cell(pdf, 0, 6, "DISCLAIMER", ln=True)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(33, 33, 33)
    disclaimer_clean = DISCLAIMER_TEXT.replace("⚠️ ", "").replace("⚠️", "")
    disclaimer_wrapped = textwrap.fill(_safe_text(disclaimer_clean), width=110)
    for line in disclaimer_wrapped.split("\n"):
        _cell(pdf, 0, 4, line, ln=True)

    return bytes(pdf.output())
