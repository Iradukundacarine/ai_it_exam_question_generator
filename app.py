import re
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import streamlit as st

from src.database import get_recent_results, save_quiz_result
from src.offline_generation import (
    OfflineGenerationError,
    generate_offline_questions,
    retrieve_relevant_chunks,
)
from src.pdf_processing import extract_pdf_text
from src.quiz_logic import QuizResult, grade_quiz
from src.text_processing import split_text_into_chunks


PROJECT_ROOT = Path(__file__).resolve().parent
SUBJECTS = [
    "Networking",
    "Python",
    "Linux",
    "Cybersecurity",
    "Database Management",
    "Artificial Intelligence",
]
QUESTION_COUNTS = [5, 10, 20, 30]
DIFFICULTIES = ["Easy", "Medium", "Hard"]
QUESTION_TYPES = ["Multiple choice", "True/False", "Short answer"]

st.set_page_config(
    page_title="AI IT Exam Question Generator",
    page_icon="Q",
    layout="wide",
)
st.markdown(
    """
    <style>
    :root {
        --ink: #20233a;
        --green: #16a085;
        --green-deep: #11695f;
        --teal-soft: #d8f4ed;
        --violet: #6848e8;
        --violet-soft: #eee9ff;
        --gold: #ffb547;
        --paper: #f5f2ff;
        --card: #ffffff;
        --line: #d9d4ec;
        --shadow: rgba(39, 29, 91, 0.1);
    }
    .stApp {
        background: linear-gradient(135deg, #f5f2ff 0%, #f4fbf8 55%, #fff8eb 100%) !important;
        color: var(--ink) !important;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(165deg, #153d45 0%, #202847 58%, #35275d 100%) !important;
        border-right: 1px solid #443b70;
        box-shadow: 4px 0 24px rgba(29, 30, 69, 0.14);
    }
    [data-testid="stSidebar"] * {
        color: #f7f5ff;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] *,
    [data-testid="stSidebar"] input {
        color: #20233a !important;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
        background: rgba(255, 255, 255, 0.96);
        border: 1px dashed #9c8df0;
        border-radius: 0.9rem;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button {
        color: #20233a !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] {
        background: #ffffff !important;
        border-radius: 0.8rem;
        padding: 0.5rem 0.75rem;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label,
    [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label *,
    [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label p {
        color: #111111 !important;
        opacity: 1 !important;
        -webkit-text-fill-color: #111111 !important;
    }
    .block-container {
        max-width: 1100px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stTabs [role="tablist"] button {
        border-radius: 0.75rem 0.75rem 0 0;
        border: 1px solid transparent;
        background: #e9e5f5;
        color: var(--ink);
    }
    .stTabs [role="tablist"] button[aria-selected="true"] {
        background: linear-gradient(180deg, #e7e0ff, #ffffff);
        border-color: #c9bfff;
        color: #5638cf;
        font-weight: 600;
    }
    h1, h2, h3 { color: var(--ink); }
    h1 {
        font-family: Georgia, serif;
        font-size: 2rem !important;
        line-height: 1.2;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    h2 { font-size: 1.35rem; }
    h3 { font-size: 1.1rem; }
    div[data-testid="stAlert"] {
        background: linear-gradient(135deg, #fff0cc 0%, #fff8e8 100%) !important;
        border: 1px solid #f1b544;
        color: #56350a;
        border-radius: 0.9rem;
        box-shadow: 0 6px 18px rgba(230, 154, 34, 0.16);
    }
    div[data-testid="stAlert"] p { color: #56350a; }
    [data-testid="stMetricValue"] { color: #5638cf; font-weight: 700; }
    .stButton > button {
        border-radius: 0.8rem;
        transition: all 0.2s ease;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #7655f2 0%, #5032c8 100%) !important;
        border-color: #6848e8 !important;
        color: #ffffff !important;
        box-shadow: 0 8px 18px rgba(89, 58, 205, 0.28);
    }
    .stButton > button[kind="primary"]:hover {
        filter: brightness(1.04);
    }
    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stNumberInput > div > div > input,
    .stRadio > div {
        border-radius: 0.8rem;
        border: 1px solid #d9d4ec;
        background: #ffffff;
        box-shadow: 0 4px 12px var(--shadow);
    }
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div:focus-within {
        border-color: var(--violet);
        box-shadow: 0 0 0 3px rgba(107, 91, 223, 0.18);
    }
    .stProgress > div > div {
        background: linear-gradient(90deg, #6848e8 0%, #16a085 100%);
    }
    .stDataFrame {
        border-radius: 0.9rem;
        overflow: hidden;
        border: 1px solid #d9d4ec;
    }
    .stExpander {
        border: 1px solid #d9d4ec;
        border-radius: 0.9rem;
        background: rgba(255,255,255,0.78);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def _clean_learning_unit(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", value or "").strip()
    cleaned = cleaned.strip(" -:;,.()[]{}")
    return cleaned


def extract_learning_units_from_text(text: str, max_units: int = 10) -> list[str]:
    """Find note headings such as 'Learning Unit 1: IP addressing' and keep the best candidates."""
    if not text:
        return []

    candidates: list[str] = []
    seen: set[str] = set()

    patterns = [
        re.compile(r"(?im)^\s*(?:learning\s*unit|unit|topic|chapter)\s*(\d+)\s*[:.-]?\s*(.+?)\s*$"),
        re.compile(r"(?im)^\s*(\d{1,2})[.)-]\s*(?:learning\s*unit\s*\d+\s*[:.-]?\s*)?(.+?)\s*$"),
        re.compile(r"(?im)^\s*(?:learning\s*unit|unit|topic|chapter)\s*(\d+)\s*[-:]\s*(.+?)\s*$"),
    ]

    for line in re.split(r"\n+|\r+", text):
        cleaned = _clean_learning_unit(line)
        if not cleaned or len(cleaned.split()) > 12:
            continue

        for pattern in patterns:
            match = pattern.match(cleaned)
            if not match:
                continue
            unit_value = match.group(2).strip() if len(match.groups()) > 1 else cleaned
            if unit_value:
                candidate = _clean_learning_unit(unit_value)
                if len(candidate) < 3:
                    continue
                candidate_key = candidate.casefold()
                if candidate_key not in seen:
                    seen.add(candidate_key)
                    candidates.append(candidate)
            break

    if not candidates:
        for line in re.split(r"\n+|\r+", text):
            cleaned = _clean_learning_unit(line)
            if not cleaned or len(cleaned.split()) > 10 or not re.search(r"[A-Za-z]", cleaned):
                continue
            if re.search(r"\b(?:network|python|linux|security|database|artificial|ai|protocol|ip|subnet|routing|system|memory|file|command|loop|function|class|test|database|model|design)\b", cleaned, re.IGNORECASE):
                candidate_key = cleaned.casefold()
                if candidate_key not in seen:
                    seen.add(candidate_key)
                    candidates.append(cleaned)

    return candidates[:max_units]


def get_uploaded_learning_units(uploaded_file) -> list[str]:
    if uploaded_file is None:
        return []
    try:
        with TemporaryDirectory() as temporary_directory:
            pdf_path = Path(temporary_directory) / "uploaded.pdf"
            pdf_path.write_bytes(uploaded_file.getvalue())
            extracted_text = extract_pdf_text(pdf_path)
    except Exception:
        return []

    return extract_learning_units_from_text(extracted_text)


def clear_quiz() -> None:
    for key in (
        "questions",
        "answers",
        "question_index",
        "quiz_submitted",
        "quiz_result",
        "source_filename",
        "result_saved",
    ):
        st.session_state.pop(key, None)
    for key in list(st.session_state):
        if key.startswith("answer_"):
            st.session_state.pop(key, None)


def begin_quiz(
    uploaded_file,
    subject: str,
    topic_unit: str,
    count: int,
    difficulty: str,
    question_type: str,
) -> None:
    clear_quiz()
    try:
        with TemporaryDirectory() as temporary_directory:
            pdf_path = Path(temporary_directory) / "uploaded.pdf"
            pdf_path.write_bytes(uploaded_file.getvalue())
            extracted_text = extract_pdf_text(pdf_path)

        chunks = split_text_into_chunks(extracted_text)
        if not chunks:
            raise ValueError("No usable text was found in the uploaded PDF.")

        with st.spinner("Searching your notes locally and building questions..."):
            retrieved_chunks = retrieve_relevant_chunks(
                chunks,
                subject=subject,
                topic_unit=topic_unit,
                top_k=min(max(count, 5), len(chunks)),
            )
            questions = generate_offline_questions(
                retrieved_chunks=retrieved_chunks,
                subject=subject,
                topic_unit=topic_unit,
                difficulty=difficulty,
                count=count,
                question_type=question_type,
            )

        st.session_state.questions = questions
        st.session_state.answers = [None] * len(questions)
        st.session_state.question_index = 0
        st.session_state.quiz_submitted = False
        st.session_state.quiz_result = None
        st.session_state.source_filename = uploaded_file.name
        st.session_state.topic_unit = topic_unit
        st.session_state.question_type = question_type
        st.rerun()
    except (ValueError, OfflineGenerationError) as error:
        st.error(str(error))
    except Exception:
        st.error("The notes could not be processed. Check that the PDF is readable and choose a topic present in it.")


def save_result_once(result: QuizResult, subject: str, difficulty: str) -> None:
    if st.session_state.get("result_saved", False):
        return
    try:
        save_quiz_result(
            subject=subject,
            difficulty=difficulty,
            result=result,
            source_file=st.session_state.get("source_filename", "unknown"),
        )
        st.session_state.result_saved = True
    except Exception:
        st.warning("Your score is ready, but it could not be saved to quiz history.")


st.title("AI IT Exam Question Generator")
st.caption("Build practice questions locally from your own Information Technology notes. No API key or internet is needed.")
st.warning(
    "Questions are built from definitions and statements in your notes. Review them with a teacher before using them for assessment."
)

with st.sidebar:
    st.header("Quiz setup")
    uploaded_pdf = st.file_uploader("Upload PDF notes", type=["pdf"], max_upload_size=20)
    detected_learning_units = get_uploaded_learning_units(uploaded_pdf) if uploaded_pdf is not None else []
    subject = st.selectbox("Subject or topic", SUBJECTS)

    if detected_learning_units:
        topic_unit = st.selectbox(
            "Learning unit or exact topic",
            options=detected_learning_units,
            index=0,
            help="Choose a learning unit directly from the uploaded notes.",
        )
        st.caption("The learning unit list was detected from your PDF notes. Pick one and the generator will search it in the document.")
    else:
        topic_unit = st.text_input(
            "Learning unit or exact topic",
            placeholder="For example: IP addressing and subnet masks",
        )
        st.caption("Enter a content topic from the notes, e.g. Python functions. Set question type and count below.")

    question_type = st.selectbox("Question type", QUESTION_TYPES)
    question_count = st.number_input(
        "Number of questions",
        min_value=1,
        max_value=30,
        value=5,
        step=1,
        help="Choose any number from 1 to 30 depending on how many questions you want.",
    )
    difficulty = st.radio("Difficulty", DIFFICULTIES, horizontal=True)
    st.divider()
    st.caption("PDF extraction, topic matching, and question generation stay on this computer. No notes are sent to an AI service.")
    generate_clicked = st.button("Generate questions", type="primary", width="stretch")

if generate_clicked:
    if uploaded_pdf is None:
        st.error("Upload a PDF before generating a quiz.")
    elif not topic_unit.strip():
        st.error("Enter the learning unit or topic to focus the questions on.")
    else:
        begin_quiz(
            uploaded_pdf,
            subject,
            topic_unit,
            question_count,
            difficulty,
            question_type,
        )

quiz_tab, history_tab = st.tabs(["Practice quiz", "Recent results"])

with quiz_tab:
    questions = st.session_state.get("questions")
    submitted = st.session_state.get("quiz_submitted", False)

    if not questions:
        st.info("Upload a PDF, choose a learning unit and quiz settings, then generate a question set offline.")
    elif submitted:
        result: QuizResult = st.session_state.quiz_result
        st.subheader("Your result")
        metric_columns = st.columns(4)
        metric_columns[0].metric("Score", f"{result.marks_awarded} / {result.total_marks}")
        metric_columns[1].metric("Correct", f"{result.correct_count} / {result.question_count}")
        metric_columns[2].metric("Percentage", f"{result.percentage:.2f}%")
        metric_columns[3].metric("Grade", result.grade)
        st.progress(result.percentage / 100)
        st.subheader("Answer review")
        for question, feedback in zip(questions, result.feedback):
            label = "Correct" if feedback.is_correct else "Review this answer"
            with st.expander(f"Question {feedback.question_number}: {label}"):
                st.write(question["question"])
                st.write(f"Your answer: {feedback.submitted_answer or 'Not answered'}")
                if question.get("question_type") == "Short answer":
                    st.write(f"Correct answer: {feedback.correct_answer}")
                else:
                    st.write(
                        f"Correct answer: {feedback.correct_answer}. "
                        f"{question['options'][feedback.correct_answer]}"
                    )
                st.write(feedback.explanation)
                st.caption(f"Note excerpt: {feedback.source}")
        if st.button("Restart quiz"):
            clear_quiz()
            st.session_state.result_saved = False
            st.rerun()
    else:
        question_index = st.session_state.question_index
        question = questions[question_index]
        st.subheader(f"Question {question_index + 1} of {len(questions)}")
        st.progress((question_index + 1) / len(questions))
        st.caption(
            f"{question.get('question_type', 'Multiple choice')} | "
            f"{st.session_state.get('topic_unit', topic_unit)}"
        )
        st.markdown(f"### {question['question']}")
        previous_answer = st.session_state.answers[question_index]
        current_question_type = question.get("question_type", "Multiple choice")
        if current_question_type == "Short answer":
            selected_answer = st.text_input(
                "Type your answer",
                value=previous_answer or "",
                key=f"answer_text_{question_index}",
            )
        else:
            option_labels = list(question["options"])
            selected_answer = st.radio(
                "Choose one answer",
                options=option_labels,
                index=option_labels.index(previous_answer) if previous_answer in option_labels else None,
                format_func=lambda label: f"{label}. {question['options'][label]}",
                key=f"answer_{question_index}",
            )

        previous_column, next_column = st.columns(2)
        with previous_column:
            if st.button("Previous", disabled=question_index == 0):
                st.session_state.answers[question_index] = selected_answer
                st.session_state.question_index -= 1
                st.rerun()
        with next_column:
            if question_index < len(questions) - 1:
                if st.button("Save and next", type="primary"):
                    st.session_state.answers[question_index] = selected_answer
                    st.session_state.question_index += 1
                    st.rerun()
            elif st.button("Submit quiz", type="primary"):
                st.session_state.answers[question_index] = selected_answer
                result = grade_quiz(questions, st.session_state.answers)
                st.session_state.quiz_result = result
                st.session_state.quiz_submitted = True
                save_result_once(result, subject, difficulty)
                st.rerun()

with history_tab:
    st.subheader("Recent quiz results")
    try:
        recent_results = get_recent_results(limit=20)
        if recent_results:
            history_frame = pd.DataFrame(recent_results)
            history_frame = history_frame.drop(columns=["id"])
            st.dataframe(history_frame, width="stretch", hide_index=True)
        else:
            st.caption("No completed quizzes have been saved yet.")
    except Exception:
        st.error("Quiz history is unavailable. The local database could not be opened.")
