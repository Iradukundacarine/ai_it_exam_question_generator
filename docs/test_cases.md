# Test Cases and Expected Results

| Test | Input or action | Expected result |
|---|---|---|
| Extract readable PDF | Included Networking sample | Text returned with Networking terms such as DHCP and TCP |
| Missing PDF | Nonexistent path | `FileNotFoundError` identifies that the file is missing |
| Invalid PDF | Non-PDF bytes saved with a `.pdf` suffix | Clear invalid-PDF `ValueError` |
| Empty PDF | Valid blank PDF page | Clear no-usable-text `ValueError` |
| Image-only PDF | PDF page contains a raster image | OCR extracts text when Tesseract is installed; otherwise installation guidance is displayed |
| Clean text | Newlines and repeated whitespace | One readable space between words |
| Chunk long text | Text longer than the configured limit | Multiple chunks within the limit with overlap |
| Invalid chunk settings | Zero limit or overlap at least the limit | `ValueError` explains the invalid setting |
| Retrieve relevant passage | Networking query against sample notes | The more relevant note chunk ranks first |
| No API configuration | Run the app without an API key or network | App still retrieves notes and builds questions locally |
| MCQ generation | Notes contain at least four extracted concepts | Each question has exactly four note-derived options and a correct answer |
| True/False generation | Notes contain supported definitions/statements | Questions use True/False choices and the explanation quotes the notes |
| Short-answer generation | Notes contain supported definitions/statements | Correct answers and normalized accepted aliases are returned |
| Unrelated topic | Select a learning unit absent from the PDF | App explains that no matching notes were found; it does not fabricate questions |
| Insufficient notes | Notes lack enough recognizable facts for the requested count | App explains the supported count and asks for fewer questions or more notes |
| Correct answer | Submit the correct option | One mark and correct feedback after submission |
| Incorrect or blank answer | Submit a wrong option or leave blank | Zero marks for that question; explanation shown after submission |
| Grade boundaries | Percentages at 49, 50, 60, 70, and 80 | Grades F, D, C, B, and A respectively |
| Save result | Complete a quiz | SQLite row includes timestamp, settings, score, percentage, grade, and source filename |
| Restart | Select Restart quiz | Active answers and result are cleared; history remains saved |

Run automated tests from the project root with `python -m pytest tests -q`. Tests make no network or API requests.
