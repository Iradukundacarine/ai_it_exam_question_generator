from io import BytesIO
from pathlib import Path

import pymupdf
import pytest
from PIL import Image, ImageDraw

from src.pdf_processing import extract_pdf_text

SAMPLE_PDF_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "sample"
    / "networking_fundamentals.pdf"
)


def test_extracts_text_from_sample_pdf() -> None:
    text = extract_pdf_text(SAMPLE_PDF_PATH)

    assert "DHCP" in text
    assert "TCP" in text


def test_missing_pdf_path_is_reported(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        extract_pdf_text(tmp_path / "missing.pdf")


def test_invalid_pdf_is_reported(tmp_path) -> None:
    invalid_pdf = tmp_path / "invalid.pdf"
    invalid_pdf.write_bytes(b"this is not a PDF")

    with pytest.raises(ValueError, match="Unable to read a valid PDF"):
        extract_pdf_text(invalid_pdf)


def test_blank_pdf_is_reported_as_having_no_usable_text(tmp_path) -> None:
    blank_pdf = tmp_path / "blank.pdf"
    document = pymupdf.open()
    document.new_page()
    document.save(blank_pdf)
    document.close()

    with pytest.raises(ValueError, match="No usable text"):
        extract_pdf_text(blank_pdf)


def test_image_only_pdf_uses_ocr_or_explains_missing_tesseract(tmp_path) -> None:
    image_bytes = BytesIO()
    image = Image.new("RGB", (800, 250), "white")
    ImageDraw.Draw(image).text((30, 40), "Linux processes and file permissions", fill="black")
    image.save(image_bytes, format="PNG")

    scanned_pdf = tmp_path / "scanned.pdf"
    document = pymupdf.open()
    page = document.new_page()
    page.insert_image(page.rect, stream=image_bytes.getvalue())
    document.save(scanned_pdf)
    document.close()

    try:
        text = extract_pdf_text(scanned_pdf)
    except ValueError as error:
        assert "Install Tesseract OCR" in str(error)
    else:
        assert "Linux" in text or "permissions" in text
