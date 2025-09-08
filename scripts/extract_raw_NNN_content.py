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

# Load the diagnosis list for validation
DIAGNOSES_JSON = OUTPUT_DIR / 'diagnoses_list.json'
with open(DIAGNOSES_JSON, 'r', encoding='utf-8') as f:
    diagnosis_list = json.load(f)

# Create a set for faster lookup and normalize for comparison
diagnosis_set = {diag.lower().strip() for diag in diagnosis_list}

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

# DEBUG: Log all text spans from pages 74-78
print("=" * 80)
print("DEBUGGING PAGES 74-78")
print("=" * 80)

# Process pages 74-78 for debugging
for page_num in range(73, 78):  # 0-indexed, so 73-77 = pages 74-78
    page = doc.load_page(page_num)
    
    print(f"\n--- PAGE {page_num + 1} ---")
    
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            for span in line["spans"]:
                # Add to all_spans for later processing
                all_spans.append({
                    "text": span["text"].strip(),
                    "font": span["font"],
                    "size": span["size"],
                    "color": span["color"],
                    "page_num": page_num + 1,
                    "index": len(all_spans)
                })
                
                # Debug output for current span
                text = span["text"].strip()
                if text:  # Only show non-empty text
                    # Check if this text matches a diagnosis from our list
                    is_diagnosis_match = text.lower().strip() in diagnosis_set
                    diagnosis_indicator = " [DIAGNOSIS MATCH]" if is_diagnosis_match else ""
                    
                    # Check formatting matches
                    is_heading_format = (span["size"] == heading_size and span["color"] == content_color)
                    is_subsection_format = (span["size"] == subsection_size and span["color"] == subsection_color)
                    is_outlier_format = (span["size"] == outlier_subsection_size and span["color"] == outlier_subsection_color)
                    
                    format_indicator = ""
                    if is_heading_format:
                        format_indicator = " [HEADING FORMAT]"
                    elif is_subsection_format:
                        format_indicator = " [SUBSECTION FORMAT]"
                    elif is_outlier_format:
                        format_indicator = " [OUTLIER FORMAT]"
                    
                    print(f"  Size: {span['size']} | Color: {span['color']} | Text: '{text[:90]}'{diagnosis_indicator}{format_indicator}")

# Now process all pages for complete extraction
print("\n" + "=" * 80)
print("PROCESSING ALL PAGES FOR COMPLETE EXTRACTION")
print("=" * 80)

# Reset all_spans and process entire document
all_spans = []
for page_num in range(doc.page_count):
    page = doc.load_page(page_num)
    
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            for span in line["spans"]:
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

# Define special subsection labels that should be treated as valid subsections even with outlier2 formatting
special_subsection_labels = {'definition', 'defining characteristics', 'related factors', 'risk factors', 'suggested noc outcomes', 'suggested nic interventions'}

for span in all_spans:
    # Check if this text matches a diagnosis from our list
    is_diagnosis_match = span["text"].lower().strip() in diagnosis_set
    
    # Diagnosis heading - must match both formatting AND be in diagnosis list
    if (span["size"] == heading_size and 
        span["color"] == content_color and 
        span["text"] and 
        is_diagnosis_match):
        headings.append({
            "text": span["text"],
            "index": span["index"],
            "page_num": span["page_num"]
        })
        # Log when we find a heading in our target pages
        if 74 <= span["page_num"] <= 78:
            print(f"FOUND HEADING: '{span['text']}' on page {span['page_num']}")
    
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
        # Log subsections in our target pages
        if 74 <= span["page_num"] <= 78:
            print(f"FOUND SUBSECTION: '{span['text']}' on page {span['page_num']}")
    
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
        # Log outlier subsections in our target pages
        if 74 <= span["page_num"] <= 78:
            print(f"FOUND OUTLIER SUBSECTION: '{span['text']}' on page {span['page_num']}")
    
    # Special case: Outlier2 formatting with special subsection labels
    elif (span["size"] == outlier_subsection_size2 and 
          span["color"] == outlier_subsection_color2 and 
          span["text"] and 
          span["text"].lower().strip() in special_subsection_labels):
        subsections.append({
            "label": span["text"],
            "index": span["index"],
            "page_num": span["page_num"],
            "type": "special_outlier2"
        })
        # Log special outlier2 subsections in our target pages
        if 74 <= span["page_num"] <= 78:
            print(f"FOUND SPECIAL OUTLIER2 SUBSECTION: '{span['text']}' on page {span['page_num']}")

print("=" * 80)
print("SUMMARY OF TARGET PAGES 74-78:")
target_headings = [h for h in headings if 74 <= h["page_num"] <= 78]
target_subsections = [s for s in subsections if 74 <= s["page_num"] <= 78]
print(f"Found {len(target_headings)} headings in pages 74-78:")
for h in target_headings:
    print(f"  - '{h['text']}' (page {h['page_num']})")
print(f"Found {len(target_subsections)} subsections in pages 74-78")
print("=" * 80)

# Sort headings by their index to maintain document order
headings.sort(key=lambda x: x["index"])

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
        
        # Skip regular outlier subsections (but NOT special_outlier2)
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
                           (span["size"] == outlier_subsection_size and span["color"] == outlier_subsection_color))
            
            # Skip ALL outlier2 spans (both special and non-special) - they are all boundaries
            is_outlier2 = (span["size"] == outlier_subsection_size2 and span["color"] == outlier_subsection_color2)
            
            # Skip outlier2 spans completely (they should never be content)
            if is_outlier2:
                continue
            
            if not is_heading and not is_subsection and span["text"] and span["color"] == content_color:
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

# Step 5: Report statistics and missing diagnoses
found_diagnoses = {d["diagnosis"].lower().strip() for d in diagnosis_sections}
missing_diagnoses = [diag for diag in diagnosis_list if diag.lower().strip() not in found_diagnoses]

print(f"Processed {len(headings)} diagnoses across {doc.page_count} pages")
print(f"Found {len(subsections)} subsections")
print(f"Expected {len(diagnosis_list)} diagnoses, found {len(diagnosis_sections)}")
print(f"Missing {len(missing_diagnoses)} diagnoses:")
for missing in missing_diagnoses[:10]:  # Show first 10 missing
    print(f"  - {missing}")
if len(missing_diagnoses) > 10:
    print(f"  ... and {len(missing_diagnoses) - 10} more")