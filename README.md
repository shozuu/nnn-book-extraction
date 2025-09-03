## NNN Book Extraction

Extracts nursing diagnoses and structured content from PDF files.

### Folder Structure

- `data/input/` — place PDFs here (`book.pdf`, `shortened_book.pdf`)
- `data/output/` — generated JSON files
- `scripts/` — Python scripts

### Requirements

- Python 3.9+
- Packages: PyPDF2, pymupdf

Install packages:

```powershell
pip install PyPDF2 pymupdf
```

### How to Run

```powershell
# From the project root or scripts folder:
python scripts/extract_diagnoses_list.py
python scripts/extract_raw_NNN_content.py
```

Outputs will be in `data/output/`.
