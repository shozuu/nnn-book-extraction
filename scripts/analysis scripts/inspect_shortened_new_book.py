import fitz
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = PROJECT_ROOT / 'data' / 'input'
OUTPUT_DIR = PROJECT_ROOT / 'data' / 'output'

PDF_DEFAULT = PROJECT_ROOT / 'shortened_new_book.pdf'
PDF_PATH = (INPUT_DIR / 'shortened_new_book.pdf') if (INPUT_DIR / 'shortened_new_book.pdf').exists() else PDF_DEFAULT

DIAGNOSES_JSON = OUTPUT_DIR / 'new_diagnoses_list.json'
with open(DIAGNOSES_JSON, 'r', encoding='utf-8') as f:
    diagnosis_list = json.load(f)
    
diagnosis_set = {diag.lower().strip() for diag in diagnosis_list}

doc = fitz.open(str(PDF_PATH))

OUTPUT_TEXT = OUTPUT_DIR / 'inspect_shortened_new_book_output.txt'
with open(OUTPUT_TEXT, 'w', encoding='utf-8') as out:
    out.write("=" * 80 + "\n")
    out.write("INSPECTING FORMATTING: PAGES 1-10 OF shortened_new_book.pdf\n")
    out.write("=" * 80 + "\n")

    for page_num in range(194, 208):  # Pages 194-208 (0-indexed)
        out.write(f"\n--- PAGE {page_num + 1} ---\n")
        page = doc.load_page(page_num)
        blocks = page.get_text("dict")["blocks"]
        if not blocks:
            out.write("  [NO BLOCKS FOUND]\n")
            continue
        found_text = False
        for block in blocks:
            for line in block.get("lines", []):
                for span in line["spans"]:
                    text = span["text"].strip()
                    if text:
                        found_text = True
                        is_diag = text.lower().strip() in diagnosis_set
                        diag_indicator = " [DIAGNOSIS MATCH]" if is_diag else ""
                        out.write(
                            f"  Font: {span['font']} | Size: {span['size']} | Color: {span['color']} | "
                            f"Text: '{text[:90]}'{diag_indicator}\n"
                        )
        if not found_text:
            out.write("  [NO TEXT SPANS FOUND]\n")