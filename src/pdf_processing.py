from pathlib import Path

import pymupdf


def extract_pdf_text(pdf_path: str | Path) -> str:
    """Extract selectable text and OCR image-only pages when Tesseract is available."""
    path = Path(pdf_path)
    if not path.is_file():
        raise FileNotFoundError(f"PDF file not found: {path}")

    try:
        with pymupdf.open(path) as document:
            page_text: list[str] = []
            for page in document:
                text = page.get_text("text").strip()
                if not text and page.get_images():
                    try:
                        text_page = page.get_textpage_ocr(language="eng", dpi=200, full=True)
                        text = page.get_text("text", textpage=text_page).strip()
                    except Exception as exc:
                        raise ValueError(
                            "This PDF contains scanned pages. Install Tesseract OCR for Windows, "
                            "add it to PATH, and restart the app to extract text from scanned notes."
                        ) from exc
                page_text.append(text)
    except (pymupdf.FileDataError, RuntimeError) as exc:
        raise ValueError(f"Unable to read a valid PDF file: {path}") from exc

    text = "\n\n".join(page for page in page_text if page).strip()
    if not text:
        raise ValueError(
            "No usable text was found. The PDF may be empty or may contain only images without readable text."
        )

    return text
