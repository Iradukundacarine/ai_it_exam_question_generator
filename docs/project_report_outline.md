# Project Report Outline

## 1. Introduction
Introduce Information Technology study notes, practice assessment, and the proposed AI IT Exam Question Generator. Explain that the system uses local retrieval-augmented generation (RAG) to connect template-built questions to uploaded notes without a hosted AI service.

## 2. Problem Statement
Students may have lengthy PDF notes but limited time to create practice questions. Manual question writing takes effort, while generic AI questions may not reflect the taught material.

## 3. Objectives
- Accept IT notes in PDF format and extract selectable text, with local Tesseract OCR fallback for image-only pages.
- Clean and chunk extracted text for semantic retrieval.
- Retrieve note excerpts relevant to a chosen subject and difficulty.
- Generate validated four-option MCQs grounded in retrieved excerpts.
- Let students answer questions and receive automatic scoring and explanations after submission.
- Save result summaries and timestamps in a local SQLite database.

## 4. Methodology
Describe the iterative stages: requirements analysis, environment setup, PDF extraction, text preparation, local TF-IDF retrieval, extractive question templates, quiz implementation, interface development, persistence, and testing. Explain RAG simply: find relevant notes first, then build questions from their definitions and statements.

## 5. System Requirements
### Hardware
A Windows computer capable of running Python and Streamlit. No GPU, local language model, or embedding-model download is needed.

### Software
Windows 10/11, Python 3.10+, Jupyter/VS Code, PyMuPDF, Pandas, Streamlit, scikit-learn, and SQLite (included with Python). Tesseract is optional for scanned PDFs.

### Service requirements
No API credentials, network access, model download, or paid service is needed to generate questions.

## 6. System Design
### Components
- Streamlit UI: PDF upload, settings, question navigation, feedback, and history.
- PDF processor: opens PDF files and extracts page text with PyMuPDF.
- Text processor: normalizes whitespace and creates overlapping chunks.
- Retriever: uses local TF-IDF vectors and cosine similarity to rank note chunks for a learning unit.
- Question generator: parses note definitions and simple statements, builds MCQ/True-False/short-answer templates, and attaches exact source sentences.
- Quiz logic: marks answers, calculates marks/percentage/grade, and prepares feedback.
- SQLite layer: stores result summaries and timestamps.

### Data flow
PDF upload -> local extraction/OCR -> cleaning and chunking -> local TF-IDF retrieval -> template question generation -> student answers -> marking and feedback -> SQLite result summary.

### Security and privacy
The application makes no external AI calls and accepts no API keys. PDF text, local retrieval, question generation, and SQLite storage stay on the computer. The result database stores scores and source filenames, not note contents or questions.

## 7. Implementation
Describe the Python modules under `src/`, the Streamlit entry point `app.py`, the Jupyter notebook, and the sample Networking notes PDF. Explain the choice of an in-memory cosine-similarity index instead of FAISS/Chroma for a small, temporary set of note chunks. Note that scanned PDFs use PyMuPDF OCR and require a local Tesseract installation.

## 8. Testing
Summarize tests for readable, invalid, empty, missing, and image-only PDFs; whitespace cleanup; chunk limits and overlap; local topic ranking; all question formats; unsupported topics and insufficient notes; answer marking; grade boundaries; and SQLite persistence. Include expected and actual results from the test run.

## 9. Limitations
The template-based generator cannot produce every kind of question and may not parse unusual note layouts. Scanned-PDF OCR requires a separately installed Tesseract executable. Retrieval is lexical and can miss synonyms. The app has no user accounts or teacher review dashboard.

## 10. Conclusion
State how the project automates practice-question preparation while grounding questions in course notes, marking answers, and saving results. Relate outcomes to the objectives.

## 11. Recommendations and Future Work
Improve offline extraction for more note layouts, add teacher approval workflows, persistent local indexing for larger note collections, optional local generative models, authentication and multi-student profiles, exportable reports, multilingual notes, and broader evaluation with teachers and students.
