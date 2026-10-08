# AI IT Exam Question Generator

An offline academic practice-quiz application that extracts text from IT notes, retrieves relevant passages locally, builds note-grounded questions without a hosted language model, marks answers, and stores result summaries locally.

## Project status

Implemented in this project:

- PDF text extraction and rejection of malformed or empty PDFs, with an OCR fallback for scanned pages.
- Text cleanup and overlapping, word-aware chunking.
- Local TF-IDF retrieval using scikit-learn; no embedding download or hosted model is used.
- Deterministic question templates from extracted definitions and note statements, with source excerpts and duplicate checks.
- Learning-unit targeting and selectable multiple-choice, True/False, and short-answer formats.
- Four-option quizzes, one question at a time, automatic marking, explanations after submission, score, percentage, and grade.
- SQLite result history with UTC timestamps.
- Streamlit interface, local sample notes, and a development notebook.

Not implemented: free-form LLM-generated questions, user accounts, persistent vector indexing, teacher administration, and question-history storage. Generated questions are extractive/template-based and should be reviewed by a teacher.

## Architecture

1. Streamlit accepts a PDF and quiz settings.
2. PyMuPDF extracts selectable text or uses local Tesseract OCR for image-only pages; the text processor cleans and chunks it.
3. Scikit-learn TF-IDF ranks chunks against the student's subject and learning unit. This works locally and does not download a model.
4. A deterministic generator turns definitions and subject-predicate statements from the retrieved chunks into MCQ, True/False, or short-answer prompts. Every question includes its exact source sentence; insufficient notes are rejected.
5. Quiz logic marks answers after submission. SQLite stores a result summary, timestamp, subject, difficulty, and source filename. The question text and PDF contents are not stored in the result database.

RAG means Retrieval-Augmented Generation: retrieve relevant note passages before building questions from them. This version does not call a language model; it uses local retrieval and transparent question templates so it needs no API key, network connection, or API billing. It is less flexible than an LLM and can only create question types supported by recognizable statements in the notes.

## Folder structure

```text
ai_it_exam_question_generator/
|-- app.py
|-- requirements.txt
|-- .gitignore
|-- data/
|   |-- sample/networking_fundamentals.pdf
|   `-- uploads/                 # local uploads; ignored by Git
|-- docs/
|   |-- demo_script.md
|   |-- project_report_outline.md
|   `-- test_cases.md
|-- notebooks/01_pdf_extraction.ipynb
|-- src/
|   |-- database.py
|   |-- offline_generation.py
|   |-- pdf_processing.py
|   |-- quiz_logic.py
|   `-- text_processing.py
`-- tests/
```

## Requirements

- Windows 10 or 11.
- Python 3.10 or newer; this project was installed and checked with Python 3.14.7.
- Tesseract OCR for image-only or scanned PDFs. Normal text PDFs do not require it.
- No API key, model download, network connection, or paid API access is needed to generate quizzes.

PDF extraction, TF-IDF retrieval, and question generation happen locally. For scanned PDFs, the optional Tesseract OCR executable must be installed separately; OCR itself runs locally.

## Windows installation

Open PowerShell in the `CAT` folder, then run:

```powershell
Set-Location .\ai_it_exam_question_generator
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m ipykernel install --user --name ai-it-exam-question-generator --display-name "Python (AI IT Exam Question Generator)"
```

If PowerShell blocks activation, run the venv interpreter directly instead:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

In VS Code, open `notebooks/01_pdf_extraction.ipynb` and choose the `Python (AI IT Exam Question Generator)` kernel.

### Optional: Enable OCR for scanned PDFs

Install the Windows Tesseract OCR engine using the installer linked from the [UB Mannheim Tesseract page](https://github.com/UB-Mannheim/tesseract/wiki). Include English language data and enable adding Tesseract to `PATH`. Restart VS Code and verify in PowerShell:

```powershell
tesseract --version
```

PyMuPDF uses Tesseract to recognize text in image-only pages. Neither OCR text nor notes are sent to an external AI service.

## Run the app

From the project folder with its environment active:

```powershell
streamlit run app.py
```

Then open the local URL printed in the terminal, normally `http://127.0.0.1:8501`.

Upload a PDF, choose a subject, enter a learning unit (for example, `IP addressing and subnet masks`), choose a question format, count, and difficulty, then select **Generate questions**. Answer each question, submit the last one, review the quoted supporting sentence, and use **Restart quiz** to begin again. The **Recent results** tab shows local SQLite history.

A sample PDF is included at `data/sample/networking_fundamentals.pdf`.

## Tests

From the project root:

```powershell
python -m pytest tests -q
```

The tests cover PDF and OCR errors, local topic retrieval, all three question formats, insufficient notes, refusal of unrelated topics, answer marking, grade boundaries, and SQLite history. Tests make no external API requests.

## Grading

Each question is worth one mark. The grade bands are A: 80-100%, B: 70-79%, C: 60-69%, D: 50-59%, and F: below 50%. Unanswered questions count as incorrect.

## Limitations and responsible use

- OCR for scanned PDFs requires a separate Tesseract installation; it is not installed automatically by `requirements.txt`.
- The local generator is template-based, not a free-form language model. It may not support unusual note layouts or generate enough questions for a narrow topic.
- Retrieval uses exact term overlap (TF-IDF), so it may miss relevant passages that use very different wording.
- Results are stored on the local computer and are not associated with student accounts.
- If the notes do not support the requested question count, the app reports the supported count instead of inventing questions.
