#!/usr/bin/env python3
"""
NNN Content Normalization Script
Normalizes new_raw_NNN_content.json based on field analysis and user requirements

Field Consolidations:
- suggested_interventions: Consolidate all NIC intervention variants
- suggested_outcomes: Consolidate all NOC outcome variants  
- refer_to: Consolidate all reference fields containing "Refer to"
- at_risk_population: Rename from at-risk_population

Data Type Standardizations:
- definition: Standardize to string
- All characteristic/factor fields: Standardize to lists
- Handle mixed string/list types consistently
"""

import json
import os
from typing import Dict, List, Any, Union
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NNNContentNormalizer:
    def __init__(self):
        # Field mapping definitions based on analysis
        self.field_mappings = {
            'suggested_nic_interventions': [
                'suggested_nic_intervention',
                'suggested_nic_interventions', 
                'suggested_nursing_interventions'
            ],
            'suggested_noc_outcomes': [
                'suggested_noc_outcome',
                'suggested_noc_outcomes',
                'suggested_noc_outcomes_(visual)',
                'suggested_noc_outcomes_and_example'
            ],
            'refer_to': [
                'nic,_noc,_client_outcomes,_nursing_interventions_and_rationales,_and_references',
                'nic,_noc,_client_outcomes,_nursing_interventions_and_rationales,_client/family_teaching,_and_references',
                'nic,_noc,_client_outcomes,_nursing_interventions_and_rationales,_client/family_teaching_and_discharge_planning,_and_references',
                'nic,_noc,_client_outcomes,_nursing_interventions_and_rationales,_client/family_teaching_and_discharge_planning_and_references',
                'nic,_noc,_client_outcomes,_nursing_interventions_and_rationales_,_client/family_teaching,_and_references',
                'noc,_nic,_client_outcomes,_nursing_interventions_and_rationales,_and_references',
                'noc,_nic,_client_outcomes,_nursing_interventions_and_rationales,_client/family_teaching,_and_references',
                'noc,_nic,_client_outcomes,_nursing_interventions_and_rationales,_client/family_teaching_and_discharge_planning,_and_references',
                'noc,_nic,_client_outcomes,_nursing_interventions_and_rationales,_client/family_teaching_and_discharge_planning_and_references'
            ],
            'at_risk_population': ['at-risk_population']
        }
        
        # Fields that should be lists
        self.list_fields = {
            'defining_characteristics',
            'related_factors', 
            'risk_factors',
            'at_risk_population',
            'associated_conditions',
            'suggested_interventions',
            'suggested_outcomes'
        }
        
        # Fields that should be strings
        self.string_fields = {
            'diagnosis',
            'definition',
            'refer_to'
        }
        
        # Fields to keep as-is
        self.preserve_fields = {
            'page_num',
            'client_outcomes'
        }
        
        # Stats tracking
        self.stats = {
            'total_entries': 0,
            'fields_consolidated': {},
            'type_conversions': {},
            'errors': []
        }

    def normalize_to_list(self, value: Any) -> List[str]:
        """Convert various input types to a list of strings."""
        if value is None or value == "":
            return []
        elif isinstance(value, list):
            # Handle nested lists and ensure all items are strings
            result = []
            for item in value:
                if isinstance(item, str):
                    result.append(item.strip())
                elif item is not None:
                    result.append(str(item).strip())
            return [item for item in result if item]  # Remove empty strings
        elif isinstance(value, str):
            return [value.strip()] if value.strip() else []
        else:
            return [str(value).strip()] if str(value).strip() else []

    def normalize_to_string(self, value: Any) -> str:
        """Convert various input types to a single string."""
        if value is None or value == "":
            return ""
        elif isinstance(value, list):
            # Join list items with ". " if they look like sentences, otherwise with ", "
            if value:
                # Check if items look like sentences (end with punctuation)
                if any(item.strip().endswith(('.', '!', '?')) for item in value if isinstance(item, str)):
                    return " ".join(str(item).strip() for item in value if item)
                else:
                    return ", ".join(str(item).strip() for item in value if item)
            return ""
        elif isinstance(value, str):
            return value.strip()
        else:
            return str(value).strip()

    def consolidate_fields(self, entry: Dict[str, Any], target_field: str, source_fields: List[str]) -> List[str]:
        """Consolidate multiple source fields into a single target field."""
        consolidated_values = []
        found_fields = []
        
        for source_field in source_fields:
            if source_field in entry:
                found_fields.append(source_field)
                value = entry[source_field]
                if value is not None and value != "":
                    if isinstance(value, list):
                        consolidated_values.extend(self.normalize_to_list(value))
                    else:
                        normalized = self.normalize_to_list(value)
                        consolidated_values.extend(normalized)
        
        # Track consolidation stats
        if found_fields:
            if target_field not in self.stats['fields_consolidated']:
                self.stats['fields_consolidated'][target_field] = {'count': 0, 'source_fields_found': set()}
            self.stats['fields_consolidated'][target_field]['count'] += 1
            self.stats['fields_consolidated'][target_field]['source_fields_found'].update(found_fields)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_values = []
        for value in consolidated_values:
            if value not in seen:
                seen.add(value)
                unique_values.append(value)
        
        return unique_values

    def arrange_fields_hierarchically(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Arrange fields in logical hierarchical order for nursing diagnoses."""
        # Define the hierarchical field order
        field_hierarchy = [
            # 1. Identification
            'diagnosis',
            'page_num',
            
            # 2. Definition
            'definition',
            
            # 3. Diagnostic Indicators (NANDA-I structure)
            'defining_characteristics',   # For actual diagnoses
            'related_factors',           # For actual diagnoses  
            'risk_factors',              # For risk diagnoses
            
            # 4. Population Context
            'at_risk_population',
            'associated_conditions',
            
            # 5. Nursing Outcomes & Interventions
            'suggested_noc_outcomes',
            'suggested_nic_interventions',
            'client_outcomes',
            
            # 6. References
            'refer_to'
        ]
        
        # Create ordered dictionary following hierarchy
        ordered_entry = {}
        
        # Add fields in hierarchical order if they exist
        for field in field_hierarchy:
            if field in entry:
                ordered_entry[field] = entry[field]
        
        # Add any remaining fields that weren't in our hierarchy (shouldn't happen, but safety)
        for field, value in entry.items():
            if field not in ordered_entry:
                logger.debug(f"Adding non-hierarchical field: {field}")
                ordered_entry[field] = value
        
        return ordered_entry

    def normalize_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a single diagnosis entry preserving original field presence."""
        normalized = {}
        processed_fields = set()
        
        try:
            # 1. Handle field consolidations first
            for target_field, source_fields in self.field_mappings.items():
                if target_field == 'refer_to':
                    # Special handling for refer_to - should be string, not list
                    consolidated = self.consolidate_fields(entry, target_field, source_fields)
                    if consolidated:
                        normalized[target_field] = consolidated[0]  # Take first/primary reference
                        if len(consolidated) > 1:
                            logger.warning(f"Multiple refer_to values found, using first: {consolidated[0]}")
                else:
                    # Regular consolidation to list (suggested_nic_interventions, suggested_noc_outcomes, at_risk_population)
                    consolidated = self.consolidate_fields(entry, target_field, source_fields)
                    if consolidated:
                        normalized[target_field] = consolidated
                
                # Mark source fields as processed
                for source_field in source_fields:
                    if source_field in entry:
                        processed_fields.add(source_field)
            
            # 2. Process remaining fields that exist in the original entry
            for field_name, value in entry.items():
                if field_name in processed_fields:
                    continue  # Skip already consolidated fields
                
                # Map field names to standardized schema
                target_field = field_name
                
                # Handle direct field mappings to standardized schema
                if field_name == 'suggested_noc_outcomes':
                    target_field = 'suggested_noc_outcomes'
                elif field_name == 'suggested_nic_interventions':
                    target_field = 'suggested_nic_interventions'
                elif field_name == 'at-risk_population':
                    target_field = 'at_risk_population'
                
                # Process the field based on its expected type
                if target_field in self.preserve_fields:
                    # Keep as-is (page_num, client_outcomes)
                    normalized[target_field] = value if value is not None else normalized.get(target_field)
                elif target_field in self.string_fields or target_field in ['diagnosis', 'definition', 'refer_to']:
                    # Convert to string
                    original_type = type(value).__name__
                    if value is not None and value != "":
                        normalized[target_field] = self.normalize_to_string(value)
                        if original_type != 'str':
                            self.stats['type_conversions'][f"{target_field}_to_string"] = self.stats['type_conversions'].get(f"{target_field}_to_string", 0) + 1
                else:
                    # Convert to list (all characteristic/factor fields)
                    original_type = type(value).__name__
                    if value is not None and value != "":
                        normalized[target_field] = self.normalize_to_list(value)
                        if original_type != 'list':
                            self.stats['type_conversions'][f"{target_field}_to_list"] = self.stats['type_conversions'].get(f"{target_field}_to_list", 0) + 1
            
            # 3. Ensure core required fields exist (only the absolutely essential ones)
            if 'diagnosis' not in normalized:
                logger.warning(f"Missing diagnosis field in entry")
                normalized['diagnosis'] = "Unknown Diagnosis"
            
            if 'page_num' not in normalized:
                logger.warning(f"Missing page_num field in entry: {normalized.get('diagnosis', 'Unknown')}")
                normalized['page_num'] = 0
            elif normalized['page_num'] == 0 and 'page_num' in entry:
                try:
                    normalized['page_num'] = int(entry['page_num']) if entry['page_num'] is not None else 0
                except (ValueError, TypeError):
                    logger.warning(f"Invalid page_num in entry {normalized['diagnosis']}: {entry.get('page_num')}")
                    normalized['page_num'] = 0
            
            # 4. Arrange fields in hierarchical order
            ordered_entry = self.arrange_fields_hierarchically(normalized)
            return ordered_entry
            
        except Exception as e:
            error_msg = f"Error normalizing entry {entry.get('diagnosis', 'Unknown')}: {str(e)}"
            logger.error(error_msg)
            self.stats['errors'].append(error_msg)
            return entry  # Return original on error

    def normalize_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize the entire dataset."""
        logger.info(f"Starting normalization of {len(data)} entries...")
        self.stats['total_entries'] = len(data)
        
        normalized_data = []
        for i, entry in enumerate(data):
            if i % 50 == 0:
                logger.info(f"Processing entry {i+1}/{len(data)}")
            
            normalized_entry = self.normalize_entry(entry)
            normalized_data.append(normalized_entry)
        
        logger.info("Normalization complete!")
        return normalized_data

    def print_stats(self):
        """Print normalization statistics."""
        print("\n" + "="*60)
        print("NORMALIZATION STATISTICS")
        print("="*60)
        
        print(f"Total entries processed: {self.stats['total_entries']}")
        print(f"Errors encountered: {len(self.stats['errors'])}")
        
        print(f"\nField consolidations performed:")
        for field, stats in self.stats['fields_consolidated'].items():
            print(f"  {field}: {stats['count']} entries consolidated")
            print(f"    Source fields found: {sorted(stats['source_fields_found'])}")
        
        print(f"\nData type conversions:")
        for conversion, count in self.stats['type_conversions'].items():
            print(f"  {conversion}: {count} conversions")
        
        if self.stats['errors']:
            print(f"\nErrors:")
            for error in self.stats['errors'][:5]:  # Show first 5 errors
                print(f"  {error}")
            if len(self.stats['errors']) > 5:
                print(f"  ... and {len(self.stats['errors']) - 5} more errors")

def load_json_data(file_path: str) -> List[Dict[str, Any]]:
    """Load JSON data from file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON: {e}")
        return []

def save_json_data(data: List[Dict[str, Any]], file_path: str):
    """Save data to JSON file."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Normalized data saved to: {file_path}")
    except Exception as e:
        logger.error(f"Error saving file: {e}")

def main():
    # File paths
    input_file = os.path.join('..', 'data', 'output', 'new_raw_NNN_content.json')
    output_file = os.path.join('..', 'data', 'output', 'normalized_new_NNN_content.json')
    
    print("=== NNN Content Normalization Script ===")
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    print()
    
    # Load data
    logger.info("Loading input data...")
    data = load_json_data(input_file)
    if not data:
        print("Error: Could not load input data.")
        return
    
    # Create normalizer and process data
    normalizer = NNNContentNormalizer()
    normalized_data = normalizer.normalize_data(data)
    
    # Save normalized data
    save_json_data(normalized_data, output_file)
    
    # Print statistics
    normalizer.print_stats()
    
    # Validation summary
    print(f"\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    print(f"Input entries: {len(data)}")
    print(f"Output entries: {len(normalized_data)}")
    print(f"Data integrity: {'✅ PASSED' if len(data) == len(normalized_data) else '❌ FAILED'}")
    
    # Quick sample check
    if normalized_data:
        sample = normalized_data[0]
        print(f"\nSample normalized entry fields:")
        for field in sorted(sample.keys()):
            value_type = type(sample[field]).__name__
            if isinstance(sample[field], list):
                count = len(sample[field])
                print(f"  {field}: {value_type}[{count}]")
            else:
                print(f"  {field}: {value_type}")
    
    print(f"\n🎉 Normalization complete! Check output file: {output_file}")

if __name__ == "__main__":
    main()