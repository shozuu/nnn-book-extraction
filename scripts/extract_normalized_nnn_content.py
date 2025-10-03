#!/usr/bin/env python3
"""
Script to extract specific fields from normalized_NNN_content_all_fields.json
and create a simplified version with standardized field names.

Output includes only the specified fields with lowercase titles:
- diagnosis
- definition
- defining_characteristics
- related_factors
- risk_factors
- at_risk_population
- associated_conditions
- suggested_outcomes (mapped from suggested_noc_outcomes)
- suggested_interventions (mapped from suggested_nic_interventions)
"""

import json
import os
from typing import Dict, List, Any


def extract_normalized_content(input_file: str, output_file: str) -> None:
    """
    Extract and normalize specific fields from the input JSON file.
    
    Args:
        input_file: Path to the input JSON file
        output_file: Path to the output JSON file
    """
    
    # Load the input data
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Define the target schema with default empty values
    target_fields = {
        "diagnosis": "",
        "definition": "",
        "defining_characteristics": [],
        "related_factors": [],
        "risk_factors": [],
        "at_risk_population": [],
        "associated_conditions": [],
        "suggested_outcomes": [],
        "suggested_interventions": []
    }
    
    # Field mapping from source to target
    field_mapping = {
        "diagnosis": "diagnosis",
        "definition": "definition", 
        "defining_characteristics": "defining_characteristics",
        "related_factors": "related_factors",
        "risk_factors": "risk_factors",
        "at_risk_population": "at_risk_population",
        "associated_conditions": "associated_conditions",
        "suggested_noc_outcomes": "suggested_outcomes",
        "suggested_nic_interventions": "suggested_interventions"
    }
    
    extracted_data = []
    
    for entry in data:
        # Create new entry with target schema
        new_entry = target_fields.copy()
        
        # Extract and map fields
        for source_field, target_field in field_mapping.items():
            if source_field in entry:
                value = entry[source_field]
                
                # Convert diagnosis to lowercase
                if target_field == "diagnosis" and isinstance(value, str):
                    new_entry[target_field] = value.lower()
                else:
                    new_entry[target_field] = value
            # If field doesn't exist, it keeps the default empty value
        
        extracted_data.append(new_entry)
    
    # Save the extracted data
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(extracted_data, f, indent=2, ensure_ascii=False)
    
    print(f"Extracted {len(extracted_data)} entries")
    print(f"Output saved to: {output_file}")


def main():
    """Main function to run the extraction."""
    
    # Define file paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    
    input_file = os.path.join(repo_root, "data", "output", "normalized_NNN_content_all_fields.json")
    output_file = os.path.join(repo_root, "data", "output", "normalized_NNN_content.json")
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}")
        return
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    print(f"Processing: {input_file}")
    print(f"Output will be saved to: {output_file}")
    print()
    
    # Run the extraction
    extract_normalized_content(input_file, output_file)
    
    # Print some statistics
    with open(output_file, 'r', encoding='utf-8') as f:
        result_data = json.load(f)
    
    print(f"\nSummary:")
    print(f"- Total entries: {len(result_data)}")
    
    # Check field completeness
    field_stats = {}
    for field in ["diagnosis", "definition", "defining_characteristics", "related_factors", 
                  "risk_factors", "at_risk_population", "associated_conditions", "suggested_outcomes", "suggested_interventions"]:
        non_empty_count = sum(1 for entry in result_data if entry.get(field))
        field_stats[field] = non_empty_count
    
    print(f"\nField statistics (non-empty entries):")
    for field, count in field_stats.items():
        percentage = (count / len(result_data)) * 100
        print(f"- {field}: {count}/{len(result_data)} ({percentage:.1f}%)")


if __name__ == "__main__":
    main()