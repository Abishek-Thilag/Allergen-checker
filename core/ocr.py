"""
core/ocr.py — pytesseract OCR wrapper.

No Streamlit imports. Returns structured results rather than raising.
"""
from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Optional


@dataclass
class OcrResult:
    """Result of an OCR extraction attempt."""
    text: str
    confidence: Optional[float]
    error: Optional[str]


def extract_text_from_image(image_bytes: bytes) -> OcrResult:
    """
    Extract text from an image using pytesseract.

    Gracefully handles:
    - Tesseract not installed (returns error message)
    - Image that cannot be decoded (returns error message)
    - Empty OCR output (returns empty text with no error)

    Args:
        image_bytes: Raw bytes of a JPG or PNG image.

    Returns:
        OcrResult with extracted text (may be empty), confidence, and error.
    """
    # ── Import Pillow ─────────────────────────────────────────────────────────
    try:
        from PIL import Image, UnidentifiedImageError
    except ImportError:
        return OcrResult(
            text="",
            confidence=None,
            error="Pillow is not installed. Run: pip install Pillow",
        )

    # ── Import pytesseract ────────────────────────────────────────────────────
    try:
        import pytesseract
    except ImportError:
        return OcrResult(
            text="",
            confidence=None,
            error=(
                "pytesseract is not installed. Run: pip install pytesseract  "
                "and also install Tesseract OCR from https://github.com/UB-Mannheim/tesseract/wiki"
            ),
        )

    # ── Decode image ──────────────────────────────────────────────────────────
    try:
        img = Image.open(io.BytesIO(image_bytes))
    except UnidentifiedImageError:
        return OcrResult(
            text="",
            confidence=None,
            error="Could not read the image. Make sure it is a valid JPG or PNG file.",
        )
    except Exception as exc:
        return OcrResult(
            text="",
            confidence=None,
            error=f"Error opening image: {exc}",
        )

    # ── Pre-process: convert to greyscale ────────────────────────────────────
    try:
        img = img.convert("L")  # greyscale — improves OCR accuracy
    except Exception:
        pass  # proceed with original if conversion fails

    # ── Run OCR ───────────────────────────────────────────────────────────────
    try:
        data = pytesseract.image_to_data(
            img,
            output_type=pytesseract.Output.DICT,
            config="--psm 6",  # assume uniform block of text
        )
    except pytesseract.TesseractNotFoundError:
        return OcrResult(
            text="",
            confidence=None,
            error=(
                "Tesseract OCR is not installed or not found in PATH. "
                "Install it from https://github.com/UB-Mannheim/tesseract/wiki "
                "(Windows) or via your package manager (Linux/macOS), "
                "then restart the app."
            ),
        )
    except Exception as exc:
        return OcrResult(
            text="",
            confidence=None,
            error=f"OCR failed: {exc}",
        )

    # ── Build text and confidence ─────────────────────────────────────────────
    words = []
    confidences = []
    for word, conf in zip(data.get("text", []), data.get("conf", [])):
        word = word.strip()
        if word:
            words.append(word)
            try:
                c = float(conf)
                if c >= 0:
                    confidences.append(c)
            except (ValueError, TypeError):
                pass

    extracted_text = " ".join(words)
    avg_confidence = (sum(confidences) / len(confidences)) if confidences else None

    return OcrResult(
        text=extracted_text,
        confidence=avg_confidence,
        error=None,
    )
