import pytest

from src.text_processing import clean_text, split_text_into_chunks


def test_clean_text_collapses_whitespace() -> None:
    assert clean_text("  Network\n\n layers\t matter. ") == "Network layers matter."


def test_split_text_respects_limit_and_repeats_overlap() -> None:
    words = [f"word{index}" for index in range(80)]
    text = " ".join(words)

    chunks = split_text_into_chunks(text, max_chars=100, overlap=20)

    assert len(chunks) > 1
    assert all(len(chunk) <= 100 for chunk in chunks)
    assert all(left.split()[-1] in right for left, right in zip(chunks, chunks[1:]))
    assert " ".join(chunks).replace("  ", " ")


def test_empty_text_returns_no_chunks() -> None:
    assert split_text_into_chunks(" \n\t ") == []


def test_invalid_chunk_settings_are_rejected() -> None:
    with pytest.raises(ValueError, match="max_chars"):
        split_text_into_chunks("notes", max_chars=0)
    with pytest.raises(ValueError, match="overlap"):
        split_text_into_chunks("notes", max_chars=10, overlap=10)
