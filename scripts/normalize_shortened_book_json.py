import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = PROJECT_ROOT / "data" / "output" / "shortened_new_book_content.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "output" / "normalized_shortened_book_content.json"

def normalize_entry(entry):
    def to_list(val):
        if isinstance(val, list):
            return [str(v).strip().lower() for v in val if isinstance(v, str)]
        elif val is None or val == "":
            return []
        else:
            return [str(val).strip().lower()]

    def to_str(val):
        if isinstance(val, list):
            return " ".join([str(v).strip().lower() for v in val if isinstance(v, str)])
        elif val is None:
            return ""
        else:
            return str(val).strip().lower()

    return {
        "diagnosis": to_str(entry.get("diagnosis", "")),
        "definition": to_str(entry.get("definition", "")),
        "defining_characteristics": to_list(entry.get("defining_characteristics", [])),
        "related_factors": to_list(entry.get("related_factors", [])),
        "risk_factors": to_list(entry.get("risk_factors", [])),
        "suggested_noc_outcomes": to_list(entry.get("suggested_noc_outcomes", [])),
        "suggested_nic_interventions": to_list(entry.get("suggested_nic_interventions", [])),
    }

def main():
    print(f"Reading input from {INPUT_PATH}")
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Loaded {len(data)} entries.")

    print("Normalizing entries...")
    normalized = [normalize_entry(entry) for entry in data]
    print(f"Normalized {len(normalized)} entries.")

    print(f"Saving normalized data to {OUTPUT_PATH}")
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(normalized, f, indent=2, ensure_ascii=False)
    print("Done.")

if __name__ == "__main__":
    main()