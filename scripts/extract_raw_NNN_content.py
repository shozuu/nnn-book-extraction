import fitz
import json
from pathlib import Path

# Resolve project root as the parent of the scripts/ folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = PROJECT_ROOT / 'data' / 'input'
OUTPUT_DIR = PROJECT_ROOT / 'data' / 'output'
INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PDF_DEFAULT = PROJECT_ROOT / 'shortened_book.pdf'
PDF_PATH = (INPUT_DIR / 'shortened_book.pdf') if (INPUT_DIR / 'shortened_book.pdf').exists() else PDF_DEFAULT

doc = fitz.open(str(PDF_PATH))

heading_font = "font0000000022986fa2"
heading_size = 20.880001068115234

subsection_font = "font0000000022986fa2"
subsection_size = 9.360000610351562
subsection_color = 8388608
content_color = 0
outlier_subsection_size = 11.520000457763672
outlier_subsection_color = 11815958
outlier_subsection_size2 = 15.120000839233398
outlier_subsection_color2 = 2907757

# Step 1: Extract all text spans with their metadata in order
all_spans = []

# Process all pages in the document
for page_num in range(doc.page_count):
    page = doc.load_page(page_num)
    
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            for span in line["spans"]:

                # format checker
                # print(f'Text: "{span["text"]}", Font: {span["font"]}, Size: {span["size"]}, Color: {span["color"]}')
                
                all_spans.append({
                    "text": span["text"].strip(),
                    "font": span["font"],
                    "size": span["size"],
                    "color": span["color"],
                    "page_num": page_num + 1,
                    "index": len(all_spans)
                })

# Step 2: Identify headings and subsections from spans
headings = []
subsections = []

for span in all_spans:
    # Diagnosis heading
    if span["size"] == heading_size and span["color"] == content_color and span["text"]:
        headings.append({
            "text": span["text"],
            "index": span["index"],
            "page_num": span["page_num"]
        })
    
    # Subsection heading (regular)
    elif (span["size"] == subsection_size and 
          span["font"] == subsection_font and 
          span["color"] == subsection_color and 
          span["text"]):
        subsections.append({
            "label": span["text"],
            "index": span["index"],
            "page_num": span["page_num"],
            "type": "regular"
        })
    
    # Subsection heading (outlier)
    elif (span["size"] == outlier_subsection_size and 
          span["color"] == outlier_subsection_color and 
          span["text"]):
        subsections.append({
            "label": span["text"],
            "index": span["index"],
            "page_num": span["page_num"],
            "type": "outlier"
        })

# Step 3: Extract content for each diagnosis
diagnosis_sections = []

# Define subsections to exclude
excluded_subsections = [
    "nursing_interventions_and",
    "nursing_intervention_and",
    "nursing_interventions_and_",
    "and_references",
    "client_outcomes",
    "patient_outcomes",
]

for i, heading in enumerate(headings):
    start_idx = heading["index"] + 1
    end_idx = headings[i + 1]["index"] if i + 1 < len(headings) else len(all_spans)
    
    # Find subsections within this diagnosis section
    section_subs = [s for s in subsections if start_idx <= s["index"] < end_idx]
    
    section_data = {}
    
    for j, subsection in enumerate(section_subs):
        sub_label = subsection["label"]
        
        # Skip excluded subsections
        if sub_label and sub_label.lower().replace(" ", "_") in excluded_subsections:
            continue
        
        # Skip outlier subsections
        if subsection.get("type") == "outlier":
            continue
        
        # Determine content range for this subsection
        content_start = subsection["index"] + 1
        content_end = (section_subs[j + 1]["index"] if j + 1 < len(section_subs) 
                      else end_idx)
        
        # Extract all content text between this subsection and the next
        content_texts = []
        for span_idx in range(content_start, content_end):
            span = all_spans[span_idx]
            
            # Skip if this span is a heading or subsection itself
            is_heading = (span["size"] == heading_size and span["color"] == content_color)
            is_subsection = ((span["size"] == subsection_size and span["color"] == subsection_color) or
                           (span["size"] == outlier_subsection_size and span["color"] == outlier_subsection_color) or
                           (span["size"] == outlier_subsection_size2 and span["color"] == outlier_subsection_color2))
            
            if not is_heading and not is_subsection and span["text"]:
                content_texts.append(span["text"])
        
        if sub_label and content_texts:
            content = " ".join(content_texts).replace("\n", " ").strip()
            
            # If content contains semicolons, split into a list
            if ";" in content:
                section_data[sub_label.lower().replace(" ", "_")] = [c.strip() for c in content.split(";") if c.strip()]
            else:
                section_data[sub_label.lower().replace(" ", "_")] = content

    diagnosis_sections.append({
        "diagnosis": heading["text"],
        "page_num": heading["page_num"],
        **section_data
    })

# Step 4: Save to JSON
OUTPUT_JSON = OUTPUT_DIR / 'raw_NNN_content.json'
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(diagnosis_sections, f, ensure_ascii=False, indent=2)

print(f"Processed {len(headings)} diagnoses across {doc.page_count} pages")
print(f"Found {len(subsections)} subsections")