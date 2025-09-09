import json
import logging
from pathlib import Path
from collections import defaultdict

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = PROJECT_ROOT / "data" / "output" / "raw_NNN_content.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "output" / "normalized_NNN_content_all_fields.json"

def normalize_entry(entry, stats):
    """Normalize entry while preserving only core fields and ordering them consistently"""
    
    def to_list(val):
        if isinstance(val, list):
            # Clean, strip, and lowercase each item
            cleaned = []
            for v in val:
                if v is not None and str(v).strip():
                    cleaned_item = str(v).strip().lower()
                    if cleaned_item:  # Only add non-empty items
                        cleaned.append(cleaned_item)
            return cleaned
        elif val is None or val == "":
            return []
        else:
            # Clean, strip, and lowercase single value
            cleaned_val = str(val).strip().lower()
            return [cleaned_val] if cleaned_val else []

    def to_str(val):
        if isinstance(val, list):
            # Clean, strip, lowercase, and join
            cleaned_items = []
            for v in val:
                if v is not None and str(v).strip():
                    cleaned_item = str(v).strip().lower()
                    if cleaned_item:
                        cleaned_items.append(cleaned_item)
            return " ".join(cleaned_items)
        elif val is None:
            return ""
        else:
            # Clean, strip, and lowercase
            return str(val).strip().lower()

    # Helper function to get field value from both singular and plural forms
    def get_field_value(entry, field_base, field_type):
        plural_field = f"{field_base}s"
        singular_field = field_base
        
        # Check for plural form first, then singular
        if plural_field in entry:
            stats[f'{field_type}_plural_found'] += 1
            return entry[plural_field]
        elif singular_field in entry:
            stats[f'{field_type}_singular_found'] += 1
            return entry[singular_field]
        else:
            stats[f'{field_type}_not_found'] += 1
            return []

    # Create normalized entry with consistent field ordering - ONLY CORE FIELDS
    normalized = {}
    
    # Core fields in specified order
    normalized["diagnosis"] = to_str(entry.get("diagnosis", ""))
    
    # Page number (preserve as integer if present)
    if "page_num" in entry:
        normalized["page_num"] = entry["page_num"]
    
    normalized["definition"] = to_str(entry.get("definition", ""))
    normalized["defining_characteristics"] = to_list(entry.get("defining_characteristics", []))
    normalized["associated_condition"] = to_list(entry.get("associated_condition", []))
    
    # Handle related factors (singular/plural variations)
    related_factors = get_field_value(entry, "related_factor", "related_factors")
    normalized["related_factors"] = to_list(related_factors)
    
    # Handle risk factors (singular/plural variations)
    risk_factors = get_field_value(entry, "risk_factor", "risk_factors")
    normalized["risk_factors"] = to_list(risk_factors)
    
    normalized["at_risk_population"] = to_list(entry.get("at-risk_population", []))
    
    # Handle NOC outcomes (singular/plural variations)
    noc_outcomes = get_field_value(entry, "suggested_noc_outcome", "noc_outcomes")
    normalized["suggested_noc_outcomes"] = to_list(noc_outcomes)
    
    # Handle NIC interventions (singular/plural variations)
    nic_interventions = get_field_value(entry, "suggested_nic_intervention", "nic_interventions")
    normalized["suggested_nic_interventions"] = to_list(nic_interventions)
    
    # Track what additional fields exist (for logging purposes only - not extracted)
    standard_fields = {
        "diagnosis", "page_num", "definition", "defining_characteristics", 
        "associated_condition", "related_factors", "related_factor", "risk_factors", "risk_factor",
        "at-risk_population", "suggested_noc_outcomes", "suggested_noc_outcome", 
        "suggested_nic_interventions", "suggested_nic_intervention", "suggested_noc_outcomes_and_example"
    }
    
    additional_fields = set(entry.keys()) - standard_fields
    if additional_fields:
        stats['additional_fields_found'].update(additional_fields)
    
    return normalized

def log_statistics(original_data, normalized_data, field_stats):
    """Log detailed statistics about the normalization process"""
    
    logger.info("=" * 60)
    logger.info("CORE FIELDS ONLY NORMALIZATION STATISTICS")
    logger.info("=" * 60)
    
    # Basic counts
    logger.info(f"Total entries processed: {len(original_data)}")
    logger.info(f"Total entries normalized: {len(normalized_data)}")
    
    # Field variation statistics
    logger.info("\nFIELD VARIATION STATISTICS:")
    logger.info("-" * 30)
    
    # Related factors statistics
    related_total = field_stats['related_factors_plural_found'] + field_stats['related_factors_singular_found']
    logger.info(f"Related Factors fields:")
    logger.info(f"  - Plural form (related_factors): {field_stats['related_factors_plural_found']}")
    logger.info(f"  - Singular form (related_factor): {field_stats['related_factors_singular_found']}")
    logger.info(f"  - Not found: {field_stats['related_factors_not_found']}")
    logger.info(f"  - Total with related factors data: {related_total}")
    if related_total > 0:
        logger.info(f"  - Singular form percentage: {(field_stats['related_factors_singular_found'] / related_total * 100):.1f}%")
    
    # Risk factors statistics
    risk_total = field_stats['risk_factors_plural_found'] + field_stats['risk_factors_singular_found']
    logger.info(f"\nRisk Factors fields:")
    logger.info(f"  - Plural form (risk_factors): {field_stats['risk_factors_plural_found']}")
    logger.info(f"  - Singular form (risk_factor): {field_stats['risk_factors_singular_found']}")
    logger.info(f"  - Not found: {field_stats['risk_factors_not_found']}")
    logger.info(f"  - Total with risk factors data: {risk_total}")
    if risk_total > 0:
        logger.info(f"  - Singular form percentage: {(field_stats['risk_factors_singular_found'] / risk_total * 100):.1f}%")
    
    # NOC Outcomes statistics
    noc_total = field_stats['noc_outcomes_plural_found'] + field_stats['noc_outcomes_singular_found']
    logger.info(f"\nNOC Outcomes fields:")
    logger.info(f"  - Plural form (suggested_noc_outcomes): {field_stats['noc_outcomes_plural_found']}")
    logger.info(f"  - Singular form (suggested_noc_outcome): {field_stats['noc_outcomes_singular_found']}")
    logger.info(f"  - Not found: {field_stats['noc_outcomes_not_found']}")
    logger.info(f"  - Total with NOC data: {noc_total}")
    if noc_total > 0:
        logger.info(f"  - Singular form percentage: {(field_stats['noc_outcomes_singular_found'] / noc_total * 100):.1f}%")
    
    # NIC Interventions statistics
    nic_total = field_stats['nic_interventions_plural_found'] + field_stats['nic_interventions_singular_found']
    logger.info(f"\nNIC Interventions fields:")
    logger.info(f"  - Plural form (suggested_nic_interventions): {field_stats['nic_interventions_plural_found']}")
    logger.info(f"  - Singular form (suggested_nic_intervention): {field_stats['nic_interventions_singular_found']}")
    logger.info(f"  - Not found: {field_stats['nic_interventions_not_found']}")
    logger.info(f"  - Total with NIC data: {nic_total}")
    if nic_total > 0:
        logger.info(f"  - Singular form percentage: {(field_stats['nic_interventions_singular_found'] / nic_total * 100):.1f}%")
    
    # Additional fields found (but not extracted)
    if field_stats['additional_fields_found']:
        logger.info(f"\nADDITIONAL FIELDS FOUND (NOT EXTRACTED):")
        logger.info("-" * 25)
        for field in sorted(field_stats['additional_fields_found']):
            logger.info(f"  - {field}")
    
    # Content statistics
    logger.info("\nCORE FIELDS CONTENT STATISTICS:")
    logger.info("-" * 20)
    
    # Count entries with various fields in normalized data
    entries_with_page_num = sum(1 for entry in normalized_data if 'page_num' in entry)
    entries_with_definition = sum(1 for entry in normalized_data if entry.get('definition'))
    entries_with_outcomes = sum(1 for entry in normalized_data if entry.get('suggested_noc_outcomes'))
    entries_with_interventions = sum(1 for entry in normalized_data if entry.get('suggested_nic_interventions'))
    entries_with_defining_chars = sum(1 for entry in normalized_data if entry.get('defining_characteristics'))
    entries_with_related_factors = sum(1 for entry in normalized_data if entry.get('related_factors'))
    entries_with_risk_factors = sum(1 for entry in normalized_data if entry.get('risk_factors'))
    entries_with_at_risk_pop = sum(1 for entry in normalized_data if entry.get('at_risk_population'))
    entries_with_assoc_condition = sum(1 for entry in normalized_data if entry.get('associated_condition'))
    
    logger.info(f"Entries with page numbers: {entries_with_page_num}")
    logger.info(f"Entries with definitions: {entries_with_definition}")
    logger.info(f"Entries with suggested NOC outcomes: {entries_with_outcomes}")
    logger.info(f"Entries with suggested NIC interventions: {entries_with_interventions}")
    logger.info(f"Entries with defining characteristics: {entries_with_defining_chars}")
    logger.info(f"Entries with related factors: {entries_with_related_factors}")
    logger.info(f"Entries with risk factors: {entries_with_risk_factors}")
    logger.info(f"Entries with at-risk population: {entries_with_at_risk_pop}")
    logger.info(f"Entries with associated conditions: {entries_with_assoc_condition}")
    
    # Show examples of entries that had singular forms
    logger.info("\nEXAMPLES OF ENTRIES WITH SINGULAR FORMS:")
    logger.info("-" * 40)
    
    singular_examples = []
    for i, entry in enumerate(original_data[:50]):
        has_singular_noc = 'suggested_noc_outcome' in entry
        has_singular_nic = 'suggested_nic_intervention' in entry
        has_singular_related = 'related_factor' in entry
        has_singular_risk = 'risk_factor' in entry
        
        if has_singular_noc or has_singular_nic or has_singular_related or has_singular_risk:
            diagnosis = entry.get('diagnosis', 'Unknown')
            fields = []
            if has_singular_noc:
                fields.append('suggested_noc_outcome')
            if has_singular_nic:
                fields.append('suggested_nic_intervention')
            if has_singular_related:
                fields.append('related_factor')
            if has_singular_risk:
                fields.append('risk_factor')
            singular_examples.append(f"  - {diagnosis}: {', '.join(fields)}")
            
        if len(singular_examples) >= 5:
            break
    
    if singular_examples:
        for example in singular_examples:
            logger.info(example)
    else:
        logger.info("  No singular forms found in first 50 entries")
    
    logger.info("\n" + "=" * 60)

def main():
    logger.info(f"Starting core-fields-only normalization of {INPUT_PATH}")
    
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Initialize statistics tracking
    field_stats = defaultdict(int)
    field_stats['additional_fields_found'] = set()
    
    logger.info(f"Loaded {len(data)} entries from raw data")
    
    # Normalize entries and collect statistics
    normalized = []
    for entry in data:
        normalized_entry = normalize_entry(entry, field_stats)
        normalized.append(normalized_entry)
    
    logger.info(f"Normalized {len(normalized)} entries")
    
    # Save normalized data
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(normalized, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved normalized data to {OUTPUT_PATH}")
    
    # Log detailed statistics
    log_statistics(data, normalized, field_stats)

if __name__ == "__main__":
    main()