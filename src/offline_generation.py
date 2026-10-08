from __future__ import annotations

import re
from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class OfflineGenerationError(ValueError):
    """The notes cannot support the requested local question set."""


@dataclass(frozen=True)
class NoteFact:
    term: str
    verb: str
    detail: str
    source: str
    aliases: tuple[str, ...] = ()


ABBREVIATION_PATTERN = re.compile(
    r"(?P<expansion>(?:[A-Z][A-Za-z0-9&/-]*)(?:\s+[A-Z][A-Za-z0-9&/-]*){1,6})"
    r"\s+\((?P<abbreviation>[A-Z][A-Z0-9-]{1,})\)"
)
FACT_PATTERN = re.compile(
    r"^(?:(?:[-*•]|\d{1,3}[.)])\s*)?(?:(?:A|An|The)\s+)?"
    r"(?P<term>[A-Za-z0-9_][A-Za-z0-9_&/+.-]*(?:\s+[A-Za-z0-9_][A-Za-z0-9_&/+.-]*){0,5}?)\s+"
    r"(?P<verb>is|are|means|refers to|connects|forwards|translates|identifies|provides|provide|uses|use|allows|allow|"
    r"contains|contain|stores|store|runs|run|executes|execute|returns|return|creates|create|covers|cover|describes|describe|"
    r"includes|include|supports|support|determines|determine|repeats|repeat|performs|perform|accepts|accept|takes|take|"
    r"checks|check|defines|define|assigns|assign|compares|compare|evaluates|evaluate|iterates|iterate|converts|convert|"
    r"prints|print|displays|display|produces|produce|manages|manage|requires|require|has|have|can)\s+"
    r"(?P<detail>.+)$",
    re.IGNORECASE,
)
COLON_FACT_PATTERN = re.compile(
    r"^(?:(?:[-*•]|\d{1,3}[.)])\s*)?"
    r"(?P<term>[A-Za-z][A-Za-z0-9_+/-]*(?:\s+[A-Za-z][A-Za-z0-9_+/-]*){0,5})\s*:\s*"
    r"(?P<detail>.+)$"
)
QUIZ_INSTRUCTIONS_PATTERN = re.compile(
    r"\blearning\s+\d+\b|\b\d+\s+(?:mcq|multiple)\b|\b(?:multiple choice|true/?false|short answer) questions?\b",
    re.IGNORECASE,
)

VERB_FORMS = {
    "connects": "connect",
    "forwards": "forward",
    "translates": "translate",
    "identifies": "identify",
    "provides": "provide",
    "uses": "use",
    "allows": "allow",
    "contains": "contain",
    "stores": "store",
    "runs": "run",
    "executes": "execute",
    "returns": "return",
    "creates": "create",
    "covers": "cover",
    "describes": "describe",
    "includes": "include",
    "supports": "support",
    "determines": "determine",
    "provide": "provide",
    "use": "use",
    "allow": "allow",
    "contain": "contain",
    "store": "store",
    "run": "run",
    "execute": "execute",
    "return": "return",
    "create": "create",
    "cover": "cover",
    "describe": "describe",
    "include": "include",
    "support": "support",
    "determine": "determine",
    "repeats": "repeat",
    "repeat": "repeat",
    "performs": "perform",
    "perform": "perform",
    "accepts": "accept",
    "accept": "accept",
    "takes": "take",
    "take": "take",
    "checks": "check",
    "check": "check",
    "defines": "define",
    "define": "define",
    "assigns": "assign",
    "assign": "assign",
    "compares": "compare",
    "compare": "compare",
    "evaluates": "evaluate",
    "evaluate": "evaluate",
    "iterates": "iterate",
    "iterate": "iterate",
    "converts": "convert",
    "convert": "convert",
    "prints": "print",
    "print": "print",
    "displays": "display",
    "display": "display",
    "produces": "produce",
    "produce": "produce",
    "manages": "manage",
    "manage": "manage",
    "requires": "require",
    "require": "require",
}


def retrieve_relevant_chunks(
    chunks: list[str],
    subject: str,
    topic_unit: str,
    top_k: int = 10,
) -> list[str]:
    """Rank note chunks locally using TF-IDF; no hosted embedding model is used."""
    usable_chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
    if not usable_chunks:
        raise OfflineGenerationError("No usable text was extracted from the uploaded notes.")
    if not topic_unit.strip():
        raise OfflineGenerationError("Enter a learning unit covered by the uploaded notes.")
    if QUIZ_INSTRUCTIONS_PATTERN.search(topic_unit):
        raise OfflineGenerationError(
            "Use the learning-unit box for a content topic from your notes, such as 'Python functions'. "
            "Choose question type and number of questions in their separate controls."
        )

    query = topic_unit.strip()
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
    try:
        vectors = vectorizer.fit_transform([query, subject, *usable_chunks])
    except ValueError as exc:
        raise OfflineGenerationError(
            "The topic or notes contain too little searchable English text. Try a fuller topic name."
        ) from exc

    topic_scores = cosine_similarity(vectors[0:1], vectors[2:]).ravel()
    subject_scores = cosine_similarity(vectors[1:2], vectors[2:]).ravel()
    scores = topic_scores * 0.8 + subject_scores * 0.2
    ranked_indices = scores.argsort()[::-1]
    if not len(ranked_indices) or topic_scores[ranked_indices[0]] < 0.03:
        raise OfflineGenerationError(
            f"The notes do not appear to cover '{topic_unit}'. Choose a topic present in the uploaded document."
        )

    return [usable_chunks[index] for index in ranked_indices[:top_k] if scores[index] >= 0.05]


def _sentences(text: str) -> list[str]:
    candidates = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [sentence.strip() for sentence in candidates if len(sentence.split()) >= 6]


def extract_note_facts(text: str) -> list[NoteFact]:
    """Extract simple definitions and subject-predicate statements from note sentences."""
    facts: list[NoteFact] = []
    seen: set[tuple[str, str, str]] = set()

    for sentence in _sentences(text):
        for match in ABBREVIATION_PATTERN.finditer(sentence):
            expansion = re.sub(r"^(?:A|An|The)\s+", "", match.group("expansion").strip(), flags=re.IGNORECASE)
            abbreviation = match.group("abbreviation").strip()
            key = (abbreviation.casefold(), "stands for", expansion.casefold())
            if key not in seen:
                facts.append(
                    NoteFact(
                        term=abbreviation,
                        verb="stands for",
                        detail=expansion,
                        source=sentence,
                        aliases=(expansion,),
                    )
                )
                seen.add(key)

        sentence_without_abbreviation = ABBREVIATION_PATTERN.sub("", sentence)
        match = FACT_PATTERN.match(sentence_without_abbreviation)
        if match:
            term = match.group("term").strip(" ,;:")
            verb = match.group("verb").casefold()
            detail = match.group("detail").strip().rstrip(".;: ")
        else:
            match = COLON_FACT_PATTERN.match(sentence_without_abbreviation)
            if not match or len(match.group("detail").split()) < 3:
                continue
            term = match.group("term").strip(" ,;:")
            verb = "means"
            detail = match.group("detail").strip().rstrip(".;: ")
        term_words = term.split()
        embedded_articles = [
            index for index, word in enumerate(term_words)
            if word.casefold() in {"a", "an", "the"}
        ]
        source_sentence = sentence
        if embedded_articles:
            article_index = embedded_articles[-1]
            trimmed_term = " ".join(term_words[article_index + 1 :]).strip()
            article_prefix = " ".join(term_words[article_index:])
            source_index = sentence.casefold().find(article_prefix.casefold())
            if trimmed_term and source_index >= 0:
                term = trimmed_term
                source_sentence = sentence[source_index:]
        if term.casefold() in {
            "notes",
            "these notes",
            "those notes",
            "the notes",
            "text",
            "document",
            "example",
            "this",
            "these",
            "it",
            "they",
        }:
            continue
        key = (term.casefold(), verb, detail.casefold())
        if key in seen:
            continue
        facts.append(NoteFact(term=term, verb=verb, detail=detail, source=source_sentence))
        seen.add(key)

    return facts


def _make_options(answer: str, terms: list[str], index: int) -> dict[str, str]:
    distractors: list[str] = []
    for offset in range(len(terms)):
        candidate = terms[(index + offset) % len(terms)]
        if candidate.casefold() != answer.casefold() and candidate.casefold() not in {
            option.casefold() for option in distractors
        }:
            distractors.append(candidate)
        if len(distractors) == 3:
            break
    if len(distractors) < 3:
        return {}

    choices = [answer, *distractors]
    correct_index = index % 4
    choices[0], choices[correct_index] = choices[correct_index], choices[0]
    return dict(zip(("A", "B", "C", "D"), choices))


def _normalized_search_terms(text: str) -> set[str]:
    analyzer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2)).build_analyzer()
    terms: set[str] = set()
    for term in analyzer(text):
        if " " in term:
            continue
        if term.endswith("ies") and len(term) > 4:
            term = f"{term[:-3]}y"
        elif term.endswith(("sses", "shes", "ches", "xes", "zes")) and len(term) > 5:
            term = term[:-2]
        elif term.endswith("ing") and len(term) > 5:
            term = term[:-3]
            if term.endswith(("nn", "tt", "pp", "mm", "rr")):
                term = term[:-1]
        elif term.endswith("s") and not term.endswith("ss") and len(term) > 3:
            term = term[:-1]
        terms.add(term)
    return terms


def _facts_for_topic(
    facts: list[NoteFact],
    topic_unit: str,
) -> list[NoteFact]:
    topic_terms = _normalized_search_terms(topic_unit)
    if not topic_terms:
        raise OfflineGenerationError("Enter a learning unit with searchable topic words.")

    known_acronyms = {
        fact.term.upper()
        for fact in facts
        if re.fullmatch(r"[A-Z][A-Z0-9-]{1,}", fact.term)
    }
    requested_acronyms = set(re.findall(r"\b[A-Z][A-Z0-9-]{1,}\b", topic_unit))
    targeted_acronyms = known_acronyms.intersection(requested_acronyms)
    if targeted_acronyms:
        acronym_facts = [
            fact
            for fact in facts
            if any(
                acronym in fact.term.upper()
                or acronym in fact.source.upper()
                or any(acronym in alias.upper() for alias in fact.aliases)
                for acronym in targeted_acronyms
            )
        ]
        if acronym_facts:
            return acronym_facts

    overlaps = [len(topic_terms.intersection(_normalized_search_terms(fact.source))) for fact in facts]
    best_overlap = max(overlaps, default=0)
    if best_overlap == 0:
        raise OfflineGenerationError(
            f"The notes do not contain definitions or statements matching '{topic_unit}'. "
            "Choose a topic that appears in the uploaded notes."
        )

    return [fact for fact, overlap in zip(facts, overlaps) if overlap >= 1]


def _negated_claim(fact: NoteFact) -> str:
    if fact.verb == "is":
        negative_verb = "is not"
    elif fact.verb == "are":
        negative_verb = "are not"
    elif fact.verb == "means":
        negative_verb = "does not mean"
    elif fact.verb == "refers to":
        negative_verb = "does not refer to"
    elif fact.verb == "stands for":
        negative_verb = "does not stand for"
    elif fact.verb == "has":
        negative_verb = "does not have"
    elif fact.verb == "have":
        negative_verb = "do not have"
    elif fact.verb == "can":
        negative_verb = "cannot"
    else:
        negative_verb = f"does not {VERB_FORMS[fact.verb]}"
    return f"{fact.term} {negative_verb} {fact.detail}"


def generate_offline_questions(
    retrieved_chunks: list[str],
    subject: str,
    topic_unit: str,
    difficulty: str,
    count: int,
    question_type: str,
) -> list[dict]:
    """Build deterministic note-grounded questions locally, without any API calls."""
    if not 1 <= count <= 30:
        raise ValueError("Question count must be between 1 and 30.")
    if question_type not in {"Multiple choice", "True/False", "Short answer"}:
        raise ValueError("Choose Multiple choice, True/False, or Short answer.")
    if difficulty not in {"Easy", "Medium", "Hard"}:
        raise ValueError("Choose Easy, Medium, or Hard difficulty.")

    all_facts = extract_note_facts("\n".join(retrieved_chunks))
    if not all_facts:
        raise OfflineGenerationError(
            f"I could not find clear definitions or complete statements for '{topic_unit}' in the matching notes. "
            "Try a content topic that appears in the document, such as 'Python functions', and choose a lower "
            "question count if the section is short."
        )
    facts = _facts_for_topic(all_facts, topic_unit)

    unique_terms: list[str] = []
    for fact in all_facts:
        for term in (fact.term, *fact.aliases):
            if term.casefold() not in {existing.casefold() for existing in unique_terms}:
                unique_terms.append(term)

    questions: list[dict] = []
    seen_questions: set[str] = set()
    for index, fact in enumerate(facts):
        if question_type == "Multiple choice":
            equivalent_terms = {fact.term.casefold(), *(alias.casefold() for alias in fact.aliases)}
            if difficulty == "Easy":
                candidate_terms = unique_terms
            else:
                same_kind_facts = [
                    other for other in all_facts
                    if (other.verb == "stands for") == (fact.verb == "stands for")
                ]
                candidate_terms = [other.term for other in same_kind_facts]
                if len(candidate_terms) < 4:
                    candidate_terms = unique_terms
                elif difficulty == "Hard":
                    answer_words = set(fact.term.casefold().split())
                    candidate_terms.sort(
                        key=lambda term: (
                            -len(answer_words.intersection(term.casefold().split())),
                            abs(len(term) - len(fact.term)),
                            term.casefold(),
                        )
                    )
            distractor_terms = [term for term in candidate_terms if term.casefold() not in equivalent_terms]
            options = _make_options(fact.term, distractor_terms, index)
            if not options:
                continue
            if fact.verb == "stands for":
                question = f"Which abbreviation in the notes stands for {fact.detail}?"
            else:
                cloze = re.sub(re.escape(fact.term), "_____", fact.source, count=1, flags=re.IGNORECASE)
                question = f"Complete this statement from the notes: {cloze}"
            correct_answer = next(
                label for label, option in options.items() if option.casefold() == fact.term.casefold()
            )
            accepted_answers = []
        elif question_type == "True/False":
            is_true = len(questions) % 2 == 0
            claim = f"{fact.term} {fact.verb} {fact.detail}" if is_true else _negated_claim(fact)
            question = f"True or False, according to the notes: {claim}."
            options = {"A": "True", "B": "False"}
            correct_answer = "A" if is_true else "B"
            accepted_answers = []
        else:
            if fact.verb == "stands for":
                question = f"What does {fact.term} stand for in these notes?"
                correct_answer = fact.detail
                accepted_answers = [fact.term, *fact.aliases]
            else:
                question = f"Which concept from the notes {fact.verb} {fact.detail}?"
                correct_answer = fact.term
                accepted_answers = list(fact.aliases)
            options = {}

        normalized_question = re.sub(r"\W+", " ", question.casefold()).strip()
        if normalized_question in seen_questions:
            continue
        seen_questions.add(normalized_question)
        explanation = f"The uploaded notes state: \"{fact.source}\""
        questions.append(
            {
                "question": question,
                "question_type": question_type,
                "options": options,
                "correct_answer": correct_answer,
                "accepted_answers": accepted_answers,
                "explanation": explanation,
                "source": fact.source,
            }
        )
        if len(questions) == count:
            break

    if len(questions) < count:
        raise OfflineGenerationError(
            f"These notes support {len(questions)} distinct {question_type} questions for '{topic_unit}', "
            f"but you requested {count}. Choose fewer questions or upload more notes about this unit."
        )
    return questions
