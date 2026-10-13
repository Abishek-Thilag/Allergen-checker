"""Tests for core/ocr.py"""
import io
from unittest.mock import MagicMock, patch

import pytest

from core.ocr import OcrResult, extract_text_from_image


def _make_white_png_bytes() -> bytes:
    """Create a minimal valid PNG (1x1 white pixel) for testing."""
    from PIL import Image
    buf = io.BytesIO()
    img = Image.new("RGB", (100, 30), color=(255, 255, 255))
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_result_is_ocrresult_type():
    """Whatever happens, the return value is an OcrResult."""
    # Use a valid PNG but mock pytesseract so no Tesseract needed
    with patch("pytesseract.image_to_data") as mock_ocr:
        mock_ocr.return_value = {
            "text": ["Ingredients", "sugar", "salt"],
            "conf": [90, 85, 88],
        }
        result = extract_text_from_image(_make_white_png_bytes())
    assert isinstance(result, OcrResult)


def test_successful_ocr_has_no_error():
    with patch("pytesseract.image_to_data") as mock_ocr:
        mock_ocr.return_value = {
            "text": ["sugar", "salt", "water"],
            "conf": [90, 88, 92],
        }
        result = extract_text_from_image(_make_white_png_bytes())
    assert result.error is None
    assert "sugar" in result.text


def test_tesseract_not_found_returns_error():
    import pytesseract

    with patch("pytesseract.image_to_data", side_effect=pytesseract.TesseractNotFoundError()):
        result = extract_text_from_image(_make_white_png_bytes())
    assert result.error is not None
    assert "tesseract" in result.error.lower()
    assert result.text == ""


def test_corrupt_bytes_returns_error():
    corrupt_bytes = b"this is not an image"
    result = extract_text_from_image(corrupt_bytes)
    assert result.error is not None
    assert result.text == ""


def test_empty_ocr_output_returns_empty_text():
    with patch("pytesseract.image_to_data") as mock_ocr:
        mock_ocr.return_value = {"text": [], "conf": []}
        result = extract_text_from_image(_make_white_png_bytes())
    assert result.text == ""
    assert result.error is None


def test_confidence_computed_when_words_present():
    with patch("pytesseract.image_to_data") as mock_ocr:
        mock_ocr.return_value = {
            "text": ["hello", "world"],
            "conf": [80, 90],
        }
        result = extract_text_from_image(_make_white_png_bytes())
    assert result.confidence is not None
    assert 70 <= result.confidence <= 100


def test_empty_bytes_input():
    result = extract_text_from_image(b"")
    assert result.error is not None
    assert result.text == ""
