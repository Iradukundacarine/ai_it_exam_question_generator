import pytest

from src.offline_generation import (
    OfflineGenerationError,
    extract_note_facts,
    generate_offline_questions,
    retrieve_relevant_chunks,
)


NOTES = """Networking Fundamentals
A Local Area Network (LAN) connects devices in a limited area.
A Wide Area Network (WAN) spans a larger geographic area.
A network switch connects devices within a LAN.
A router connects different networks and forwards IP packets.
The Domain Name System (DNS) translates domain names into IP addresses.
The Dynamic Host Configuration Protocol (DHCP) provides network settings automatically.
"""


def test_retrieval_uses_local_tfidf_and_filters_unrelated_topic() -> None:
    chunks = [
        "A router connects different networks and forwards IP packets.",
        "Python functions can accept parameters and return values.",
    ]

    matches = retrieve_relevant_chunks(chunks, "Networking", "router networks")

    assert matches == [chunks[0]]
    with pytest.raises(OfflineGenerationError, match="do not appear to cover"):
        retrieve_relevant_chunks(chunks, "Python", "database normalization")
    with pytest.raises(OfflineGenerationError, match="content topic from your notes"):
        retrieve_relevant_chunks(chunks, "Networking", "10 multiple questiomn on learning 1")


def test_extracts_acronym_and_definition_facts_from_notes() -> None:
    facts = extract_note_facts(NOTES)

    assert any(fact.term == "LAN" and fact.detail == "Local Area Network" for fact in facts)
    assert any(fact.term == "router" and fact.verb == "connects" for fact in facts)


def test_extracts_common_class_note_sentence_and_label_formats() -> None:
    notes = (
        "Python is a high-level programming language. "
        "Variables store values used by a program. "
        "Functions: reusable blocks of code that perform a task."
    )

    facts = extract_note_facts(notes)

    assert any(fact.term == "Python" and fact.verb == "is" for fact in facts)
    assert any(fact.term == "Variables" and fact.verb == "store" for fact in facts)
    assert any(fact.term == "Functions" and "reusable blocks" in fact.detail for fact in facts)


def test_extracts_common_programming_action_sentences() -> None:
    facts = extract_note_facts(
        "A loop repeats a block of code until a condition changes. "
        "A function accepts arguments and returns a result. "
        "A class defines the structure of objects."
    )

    assert any(fact.term == "loop" and fact.verb == "repeats" for fact in facts)
    assert any(fact.term == "function" and fact.verb == "accepts" for fact in facts)
    assert any(fact.term == "class" and fact.verb == "defines" for fact in facts)


def test_page_title_is_not_mixed_into_first_definition() -> None:
    facts = extract_note_facts(
        "Networking Fundamentals A computer network is a group of connected devices that exchange data."
    )

    first_definition = next(fact for fact in facts if fact.verb == "is")
    assert first_definition.term == "computer network"
    assert first_definition.source.startswith("A computer network")


@pytest.mark.parametrize("question_type", ["Multiple choice", "True/False", "Short answer"])
def test_offline_generator_returns_valid_note_grounded_questions(question_type: str) -> None:
    questions = generate_offline_questions(
        [NOTES],
        subject="Networking",
        topic_unit="network devices and addressing",
        difficulty="Easy",
        count=5,
        question_type=question_type,
    )

    assert len(questions) == 5
    assert all(item["question_type"] == question_type for item in questions)
    assert all(item["source"] in NOTES for item in questions)
    assert all(item["explanation"].endswith(f'"{item["source"]}"') for item in questions)
    if question_type == "Multiple choice":
        assert all(set(item["options"]) == {"A", "B", "C", "D"} for item in questions)
        assert all(item["correct_answer"] in item["options"] for item in questions)
        for item in questions:
            if "abbreviation" in item["question"]:
                assert item["options"][item["correct_answer"]] == "LAN" or item["options"][item["correct_answer"]] in {
                    "WAN",
                    "DNS",
                    "DHCP",
                }
                assert item["correct_answer"] in {"A", "B", "C", "D"}
    elif question_type == "True/False":
        assert all(set(item["options"]) == {"A", "B"} for item in questions)
    else:
        assert all(item["options"] == {} for item in questions)


def test_generator_refuses_to_invent_questions_when_notes_are_too_small() -> None:
    with pytest.raises(OfflineGenerationError, match="could not find clear definitions"):
        generate_offline_questions(
            ["These notes are a short sentence without a clear definition."],
            subject="Python",
            topic_unit="classes",
            difficulty="Easy",
            count=5,
            question_type="Multiple choice",
        )


def test_hard_mcq_uses_similar_same_kind_distractors() -> None:
    question = generate_offline_questions(
        [NOTES],
        subject="Networking",
        topic_unit="LAN WAN abbreviations",
        difficulty="Hard",
        count=1,
        question_type="Multiple choice",
    )[0]

    assert question["options"][question["correct_answer"]] == "LAN"
    assert set(question["options"].values()) == {"LAN", "WAN", "DNS", "DHCP"}


def test_questions_are_filtered_to_the_selected_learning_unit() -> None:
    questions = generate_offline_questions(
        [NOTES],
        subject="Networking",
        topic_unit="DNS and DHCP network configuration",
        difficulty="Easy",
        count=2,
        question_type="Multiple choice",
    )

    assert all(
        "DNS" in question["source"] or "DHCP" in question["source"]
        for question in questions
    )


def test_broad_network_topic_keeps_one_term_matches() -> None:
    questions = generate_offline_questions(
        [NOTES],
        subject="Networking",
        topic_unit="network devices and addressing",
        difficulty="Easy",
        count=5,
        question_type="True/False",
    )

    assert len(questions) == 5
    assert all(question["source"] in NOTES for question in questions)


def test_explicit_acronym_topic_stays_narrow_after_broad_subject_match() -> None:
    questions = generate_offline_questions(
        [NOTES],
        subject="Networking",
        topic_unit="DNS and DHCP network configuration",
        difficulty="Easy",
        count=2,
        question_type="Multiple choice",
    )

    assert all("DNS" in question["source"] or "DHCP" in question["source"] for question in questions)


def test_unmatched_topic_does_not_use_general_notes_as_filler() -> None:
    with pytest.raises(OfflineGenerationError, match="do not contain definitions or statements matching"):
        generate_offline_questions(
            [NOTES],
            subject="Networking",
            topic_unit="database normalization",
            difficulty="Easy",
            count=1,
            question_type="True/False",
        )
