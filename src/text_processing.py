import re


def clean_text(text: str) -> str:
    """Collapse PDF layout whitespace into readable single spaces."""
    return re.sub(r"\s+", " ", text).strip()


def split_text_into_chunks(
    text: str,
    max_chars: int = 1200,
    overlap: int = 150,
) -> list[str]:
    """Split text into overlapping chunks without cutting ordinary words."""
    if max_chars < 1:
        raise ValueError("max_chars must be greater than zero.")
    if overlap < 0 or overlap >= max_chars:
        raise ValueError("overlap must be at least zero and smaller than max_chars.")

    cleaned_text = clean_text(text)
    if not cleaned_text:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(cleaned_text):
        end = min(start + max_chars, len(cleaned_text))
        if end < len(cleaned_text):
            boundary = cleaned_text.rfind(" ", start, end)
            if boundary > start:
                end = boundary

        chunk = cleaned_text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(cleaned_text):
            break

        next_start = max(end - overlap, start + 1)
        next_space = cleaned_text.find(" ", next_start)
        start = next_space + 1 if next_space != -1 else end

    return chunks
