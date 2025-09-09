import json
import logging
from pathlib import Path
from collections import defaultdict

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = PROJECT_ROOT / "data" / "output" / "raw_NNN_content.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "output" / "normalized_NNN_content.json"

def normalize_entry(entry, stats):
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

    return {
        "diagnosis": to_str(entry.get("diagnosis", "")),
        "definition": to_str(entry.get("definition", "")),
        "defining_characteristics": to_list(get_field_value(entry, "defining_characteristic", "defining_characteristics")),
        "related_factors": to_list(get_field_value(entry, "related_factor", "related_factors")),
        "risk_factors": to_list(get_field_value(entry, "risk_factor", "risk_factors")),
        "suggested_outcomes": to_list(get_field_value(entry, "suggested_noc_outcome", "noc_outcomes")),
        "suggested_interventions": to_list(get_field_value(entry, "suggested_nic_intervention", "nic_interventions")),
    }

def log_statistics(original_data, normalized_data, field_stats):
    """Log detailed statistics about the normalization process"""
    
    logger.info("=" * 60)
    logger.info("NORMALIZATION STATISTICS")
    logger.info("=" * 60)
    
    # Basic counts
    logger.info(f"Total entries processed: {len(original_data)}")
    logger.info(f"Total entries normalized: {len(normalized_data)}")
    
    # Field variation statistics
    logger.info("\nFIELD VARIATION STATISTICS:")
    logger.info("-" * 30)
    
    # Defining characteristics statistics
    def_char_total = field_stats['defining_characteristics_plural_found'] + field_stats['defining_characteristics_singular_found']
    logger.info(f"Defining Characteristics fields:")
    logger.info(f"  - Plural form (defining_characteristics): {field_stats['defining_characteristics_plural_found']}")
    logger.info(f"  - Singular form (defining_characteristic): {field_stats['defining_characteristics_singular_found']}")
    logger.info(f"  - Not found: {field_stats['defining_characteristics_not_found']}")
    logger.info(f"  - Total with defining characteristics data: {def_char_total}")
    if def_char_total > 0:
        logger.info(f"  - Singular form percentage: {(field_stats['defining_characteristics_singular_found'] / def_char_total * 100):.1f}%")
    
    # Related factors statistics
    related_total = field_stats['related_factors_plural_found'] + field_stats['related_factors_singular_found']
    logger.info(f"\nRelated Factors fields:")
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
    
    # Content statistics
    logger.info("\nCONTENT STATISTICS:")
    logger.info("-" * 20)
    
    # Count entries with various fields in normalized data
    entries_with_definition = sum(1 for entry in normalized_data if entry.get('definition'))
    entries_with_defining_chars = sum(1 for entry in normalized_data if entry['defining_characteristics'])
    entries_with_related_factors = sum(1 for entry in normalized_data if entry['related_factors'])
    entries_with_risk_factors = sum(1 for entry in normalized_data if entry['risk_factors'])
    entries_with_outcomes = sum(1 for entry in normalized_data if entry['suggested_outcomes'])
    entries_with_interventions = sum(1 for entry in normalized_data if entry['suggested_interventions'])
    
    logger.info(f"Entries with definitions: {entries_with_definition}")
    logger.info(f"Entries with defining characteristics: {entries_with_defining_chars}")
    logger.info(f"Entries with related factors: {entries_with_related_factors}")
    logger.info(f"Entries with risk factors: {entries_with_risk_factors}")
    logger.info(f"Entries with suggested NOC outcomes: {entries_with_outcomes}")
    logger.info(f"Entries with suggested NIC interventions: {entries_with_interventions}")
    
    # Data preservation check
    logger.info("\nDATA PRESERVATION CHECK:")
    logger.info("-" * 25)
    
    entries_with_any_content = sum(1 for entry in normalized_data if any([
        entry.get('definition'),
        entry['defining_characteristics'],
        entry['related_factors'],
        entry['risk_factors'],
        entry['suggested_outcomes'],
        entry['suggested_interventions']
    ]))
    
    logger.info(f"Entries with any content: {entries_with_any_content}")
    logger.info(f"Empty entries: {len(normalized_data) - entries_with_any_content}")
    
    # Show examples of entries that had singular forms
    logger.info("\nEXAMPLES OF ENTRIES WITH SINGULAR FORMS:")
    logger.info("-" * 40)
    
    singular_examples = []
    for i, entry in enumerate(original_data[:100]):  # Check first 100 entries
        has_singular_def_char = 'defining_characteristic' in entry
        has_singular_related = 'related_factor' in entry
        has_singular_risk = 'risk_factor' in entry
        has_singular_noc = 'suggested_noc_outcome' in entry
        has_singular_nic = 'suggested_nic_intervention' in entry
        
        if has_singular_def_char or has_singular_related or has_singular_risk or has_singular_noc or has_singular_nic:
            diagnosis = entry.get('diagnosis', f'Entry #{i}')
            fields = []
            if has_singular_def_char:
                fields.append('defining_characteristic')
            if has_singular_related:
                fields.append('related_factor')
            if has_singular_risk:
                fields.append('risk_factor')
            if has_singular_noc:
                fields.append('suggested_noc_outcome')
            if has_singular_nic:
                fields.append('suggested_nic_intervention')
            singular_examples.append(f"  - {diagnosis}: {', '.join(fields)}")
            
        if len(singular_examples) >= 8:  # Show max 8 examples
            break
    
    if singular_examples:
        for example in singular_examples:
            logger.info(example)
    else:
        logger.info("  No singular forms found in first 100 entries")
    
    # Summary statistics
    logger.info("\nSUMMARY:")
    logger.info("-" * 10)
    
    total_fields_with_variations = 0
    total_singular_instances = 0
    
    for field_type in ['defining_characteristics', 'related_factors', 'risk_factors', 'noc_outcomes', 'nic_interventions']:
        plural_count = field_stats[f'{field_type}_plural_found']
        singular_count = field_stats[f'{field_type}_singular_found']
        total = plural_count + singular_count
        
        if total > 0:
            total_fields_with_variations += 1
            total_singular_instances += singular_count
    
    logger.info(f"Field types with singular/plural variations found: {total_fields_with_variations}")
    logger.info(f"Total singular form instances captured: {total_singular_instances}")
    
    if total_singular_instances > 0:
        logger.info(f"✓ Successfully captured {total_singular_instances} instances that would have been missed without singular/plural handling!")
    
    logger.info("\n" + "=" * 60)

def main():
    logger.info(f"Starting normalization of {INPUT_PATH}")
    
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Initialize statistics tracking
    field_stats = defaultdict(int)
    
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