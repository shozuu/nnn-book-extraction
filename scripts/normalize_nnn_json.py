import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = PROJECT_ROOT / "data" / "output" / "raw_NNN_content.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "output" / "normalized_NNN_content.json"

def normalize_entry(entry):
    def to_list(val):
        if isinstance(val, list):
            return [str(v).lower() for v in val if isinstance(v, str)]
        elif val is None or val == "":
            return []
        else:
            return [str(val).lower()]

    def to_str(val):
        if isinstance(val, list):
            # If definition is a list, join and lowercase
            return " ".join([str(v).lower() for v in val if isinstance(v, str)])
        elif val is None:
            return ""
        else:
            return str(val).lower()

    return {
        "diagnosis": to_str(entry.get("diagnosis", "")),
        "definition": to_str(entry.get("definition", "")),
        "defining_characteristics": to_list(entry.get("defining_characteristics", [])),
        "related_factors": to_list(entry.get("related_factors", [])),
        "risk_factors": to_list(entry.get("risk_factors", [])),
        "suggested_outcomes": to_list(entry.get("suggested_noc_outcomes", entry.get("suggested_outcomes", []))),
        "suggested_interventions": to_list(entry.get("suggested_nic_interventions", entry.get("suggested_interventions", []))),
    }

def main():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    normalized = [normalize_entry(entry) for entry in data]

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(normalized, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()