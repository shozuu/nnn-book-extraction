import fitz
import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = PROJECT_ROOT / 'data' / 'input'
OUTPUT_DIR = PROJECT_ROOT / 'data' / 'output'

PDF_PATH = INPUT_DIR / 'shortened_new_book.pdf'
DIAGNOSES_JSON = OUTPUT_DIR / 'new_diagnoses_list.json'

doc = fitz.open(str(PDF_PATH))

# Formatting constants
DIAGNOSIS_FONT = "HelveticaNeueLTStd-Bd"
DIAGNOSIS_SIZE = 14.0
DIAGNOSIS_COLOR = 16777215

SUBSECTION_SIZE = 10.0
SUBSECTION_COLOR = 4153748

CONTENT_FONTS = {"MinionPro-Regular", "MinionPro-Bold", "MinionPro-It"}
CONTENT_SIZE = 9.5
CONTENT_COLOR = 2301728

STOP_SUBSECTION = "nursing interventions and"

def normalize_text(text):
    """Normalize hyphens, dashes, apostrophes, quotes, and remove invisible chars."""
    if not isinstance(text, str):
        return text
    # Remove zero-width and non-printable characters
    text = re.sub(r"[\u200b-\u200f\u202a-\u202e\u2060-\u206f]", "", text)
    # Normalize hyphens/dashes
    text = (
        text.replace("­", "-")   # soft hyphen
            .replace("\u2010", "-")  # hyphen
            .replace("\u2011", "-")  # non-breaking hyphen
            .replace("\u2012", "-")  # figure dash
            .replace("\u2013", "-")  # en dash
            .replace("\u2014", "-")  # em dash
            .replace("\u2212", "-")  # minus sign
            .replace("–", "-")       # en dash (common in copy-paste)
            .replace("—", "-")       # em dash (common in copy-paste)
    )
    text = re.sub(r"-+", "-", text)
    text = re.sub(r"\s*-\s*", "-", text)
    # Normalize apostrophes/quotes
    text = (
        text.replace("’", "'")
            .replace("‘", "'")
            .replace("“", '"')
            .replace("”", '"')
            .replace("´", "'")
            .replace("`", "'")
    )
    return text.strip()

with open(DIAGNOSES_JSON, 'r', encoding='utf-8') as f:
    diagnosis_list = json.load(f)
diagnosis_list = [normalize_text(diag.lower().strip()) for diag in diagnosis_list]
diagnosis_set = set(diagnosis_list)

def normalize_key(text):
    key = normalize_text(text.lower())
    key = re.sub(r"-+", "-", key)
    key = key.strip().replace(" ", "_")
    return key

def normalize_val(text):
    return normalize_text(text.strip())

all_spans = []
for page_num in range(doc.page_count):
    page = doc.load_page(page_num)
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            for span in line["spans"]:
                all_spans.append({
                    "text": normalize_text(span["text"].strip()),
                    "font": span["font"],
                    "size": span["size"],
                    "color": span["color"],
                    "page_num": page_num + 1,
                    "index": len(all_spans)
                })

results = []
diagnosis_found = set()
i = 0
while i < len(all_spans):
    span = all_spans[i]
    # Find diagnosis heading
    heading_text = normalize_text(span["text"].lower().strip())
    if heading_text in diagnosis_set:
        diagnosis = normalize_val(span["text"])
        diagnosis_found.add(normalize_text(diagnosis.lower().strip()))
        i += 1
        entry = {"diagnosis": diagnosis, "page_num": span["page_num"]}
        # Extract subsections until STOP_SUBSECTION or next diagnosis
        while i < len(all_spans):
            sub_span = all_spans[i]
            # Check for next diagnosis heading
            if (sub_span["font"] == DIAGNOSIS_FONT and
                sub_span["size"] == DIAGNOSIS_SIZE and
                sub_span["color"] == DIAGNOSIS_COLOR and
                normalize_text(sub_span["text"].lower().strip()) in diagnosis_set):
                break

            # Concatenate subsection heading if split across spans
            if (sub_span["size"] == SUBSECTION_SIZE and sub_span["color"] == SUBSECTION_COLOR):
                sub_label = sub_span["text"]
                j = i + 1
                while (j < len(all_spans) and
                       all_spans[j]["size"] == SUBSECTION_SIZE and
                       all_spans[j]["color"] == SUBSECTION_COLOR and
                       all_spans[j]["page_num"] == sub_span["page_num"]):
                    sub_label += " " + all_spans[j]["text"]
                    j += 1
                norm_label = normalize_key(sub_label)
                
                # Stop at "Nursing Interventions and"
                if norm_label.startswith(STOP_SUBSECTION.replace(" ", "_")):
                    break

                i = j  # <-- Always advance i past the subsection heading

                # Special handling for client outcomes
                if norm_label == "client_outcomes":
                    client_outcomes = {}
                    # Look for the "Client Will (Specify Time Frame)" line
                    if (i < len(all_spans) and
                        all_spans[i]["font"] == "HelveticaNeueLTStd-Bd" and
                        all_spans[i]["size"] == 9.5 and
                        all_spans[i]["color"] == 10242925):
                        client_will = all_spans[i]["text"]
                        i += 1
                        outcomes = []
                        # Loop until next subsection or diagnosis heading
                        while i < len(all_spans):
                            s = all_spans[i]
                            # Stop at next subsection or diagnosis heading
                            is_subsection = (s["size"] == SUBSECTION_SIZE and s["color"] == SUBSECTION_COLOR)
                            is_diagnosis = (s["font"] == DIAGNOSIS_FONT and s["size"] == DIAGNOSIS_SIZE and s["color"] == DIAGNOSIS_COLOR and normalize_text(s["text"].lower().strip()) in diagnosis_set)
                            if is_subsection or is_diagnosis:
                                break
                            # Skip bullets
                            if (s["font"] == "MinionPro-Regular" and s["size"] == 15.0 and s["color"] == 2301728):
                                i += 1
                                continue
                            # Collect content lines
                            if (s["font"] == "MinionPro-Regular" and s["size"] == 9.5 and s["color"] == 2301728):
                                # Merge consecutive content lines (handle line breaks)
                                content_text = s["text"]
                                k = i + 1
                                while (k < len(all_spans) and
                                       all_spans[k]["font"] == "MinionPro-Regular" and
                                       all_spans[k]["size"] == 9.5 and
                                       all_spans[k]["color"] == 2301728 and
                                       all_spans[k]["page_num"] == s["page_num"]):
                                    content_text += " " + all_spans[k]["text"]
                                    k += 1
                                outcomes.append(normalize_val(content_text))
                                i = k
                                continue
                            i += 1
                        client_outcomes["client_will"] = normalize_val(client_will)
                        client_outcomes["outcomes"] = [normalize_val(o) for o in outcomes]
                        entry[norm_label] = client_outcomes
                    continue

                # Extract content for other subsections (original logic)
                content = []
                i = j
                while (i < len(all_spans) and
                       (all_spans[i]["font"] in CONTENT_FONTS) and
                       all_spans[i]["size"] == CONTENT_SIZE and
                       all_spans[i]["color"] == CONTENT_COLOR):
                    content_text = all_spans[i]["text"]
                    k = i + 1
                    while (k < len(all_spans) and
                           all_spans[k]["font"] in CONTENT_FONTS and
                           all_spans[k]["size"] == CONTENT_SIZE and
                           all_spans[k]["color"] == CONTENT_COLOR and
                           all_spans[k]["page_num"] == all_spans[i]["page_num"]):
                        content_text += " " + all_spans[k]["text"]
                        k += 1
                    content.append(normalize_val(content_text))
                    i = k
                # Store as array if any content has semicolons, else as string or array
                if content:
                    joined = " ".join(content).replace("\n", " ").strip()
                    if ";" in joined:
                        entry[norm_label] = [normalize_val(c) for c in joined.split(";") if c.strip()]
                    elif len(content) == 1:
                        entry[norm_label] = content[0]
                    else:
                        entry[norm_label] = [normalize_val(c) for c in content]
                continue
            i += 1
        # Only append if entry has more than just diagnosis and page_num
        if len(entry) > 2:
            results.append(entry)
    else:
        # Only print if this span looks like a heading (diagnosis formatting) and contains a hyphen
        if (
            span["font"] == DIAGNOSIS_FONT and
            span["size"] == DIAGNOSIS_SIZE and
            span["color"] == DIAGNOSIS_COLOR and
            "-" in span["text"]
        ):
            print(
                f"DEBUG: Missed heading: '{span['text']}' | "
                f"Normalized: '{heading_text}' | "
                f"Page: {span['page_num']} | "
                f"Font: {span['font']} | Size: {span['size']} | Color: {span['color']}"
            )
        i += 1

# Save to JSON
OUTPUT_JSON = OUTPUT_DIR / 'new_raw_NNN_content.json'
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

# Status log for every diagnosis in the list
print("=" * 60)
print("Diagnosis extraction status:")
for diag in diagnosis_list:
    # Use normalized text
    found = normalize_text(diag.lower().strip()) in diagnosis_found
    print(f"{diag:50} : {'FOUND' if found else 'MISSING'}")
print("=" * 60)
print(f"Total diagnoses in list: {len(diagnosis_list)}")
print(f"Diagnoses found in PDF: {len(diagnosis_found)}")
print(f"Diagnoses missing: {len(diagnosis_list) - len(diagnosis_found)}")