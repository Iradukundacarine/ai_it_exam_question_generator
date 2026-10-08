# Teacher Demonstration Script

**Opening**

"This project is the AI IT Exam Question Generator. It helps a student practise from their own IT notes. It extracts text from a PDF, retrieves relevant passages with local TF-IDF, creates note-grounded questions using local templates, marks the answers, and saves a local result summary. It needs no API key or internet connection."

**Demonstration steps**

1. Show `data/sample/networking_fundamentals.pdf` and upload it in the app.
2. Choose Networking, five questions, and Easy difficulty.
3. Point out that PDF processing, topic matching, and question building all run on the computer. There is no API key, external model call, or API fee.
4. Generate the questions and answer them one at a time. Explain that the correct answer and explanation are hidden until submission.
5. Submit the quiz. Show marks, percentage, grade, answer feedback, the supporting note excerpt, and the restart control.
6. Open Recent results and show the timestamped SQLite summary.
7. Explain the local RAG path: TF-IDF retrieves note chunks that match the learning unit; templates use definitions and statements from those chunks, with a quoted source sentence for each answer.

**Closing**

"The local generator rejects unrelated topics and reports when the notes do not contain enough recognizable definitions or statements. It is template-based, not a free-form language model, and still needs teacher review. Scanned PDFs need the optional local Tesseract installation."
