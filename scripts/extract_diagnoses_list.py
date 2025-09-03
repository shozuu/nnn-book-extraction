import re
import PyPDF2
import json
from pathlib import Path

# Resolve project root as the parent of the scripts/ folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = PROJECT_ROOT / 'data' / 'input'
OUTPUT_DIR = PROJECT_ROOT / 'data' / 'output'

INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PDF_DEFAULT = PROJECT_ROOT / 'book.pdf'
PDF_PATH = (INPUT_DIR / 'book.pdf') if (INPUT_DIR / 'book.pdf').exists() else PDF_DEFAULT

# Extracts all the text from specified page
def extract_text_from_page(pdf_path, page_number):
    with open(pdf_path, "rb") as infile:
        reader = PyPDF2.PdfReader(infile)
        page = reader.pages[page_number - 1]
        text = page.extract_text()
        return text

def extract_diagnoses(text):
    # Removes all the leading and trailing whitespace
    text = text.strip()

    # Remove header if present at the start
    if text.startswith("NANDA-I Diagnoses"):
        text = text[len("NANDA-I Diagnoses"):].strip()

    # Split by comma followed by a number (diagnosis separator)
    entries = re.split(r',\s*\d+', text)

    diagnoses = []

    for entry in entries:
        entry = entry.strip()
        
        # Skips empty strings
        if not entry:
            continue

        # Remove leading numbers and spaces
        diagnosis = re.sub(r'^\d+\s*', '', entry)
        diagnoses.append(diagnosis)
    return diagnoses

diagnoses = []
# loop through 64 to 67 inclusive
for page_num in range(64, 68):
    page_text = extract_text_from_page(str(PDF_PATH), page_num)
    diagnoses.extend(extract_diagnoses(page_text))

print(diagnoses)

# Export diagnoses list to a json file
OUTPUT_JSON = OUTPUT_DIR / 'diagnoses_list.json'
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(diagnoses, f, ensure_ascii=False, indent=2)