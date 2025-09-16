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
        
        # Fields to keep as-is (only page_num should be preserved)
        self.preserve_fields = {
            'page_num'
        }
        
        # Stats tracking
        self.stats = {
            'total_entries': 0,
            'fields_consolidated': {},
            'type_conversions': {},
            'content_normalizations': {},
            'errors': []
        }

    def normalize_text_content(self, text: str) -> str:
        """Normalize text content for consistency and easier parsing."""
        if not text or not isinstance(text, str):
            return text
        
        original_text = text
        
        # Track what normalizations we apply
        applied_normalizations = []
        
        # 1. Unicode normalization
        import unicodedata
        text = unicodedata.normalize('NFKC', text)
        
        # 2. Convert to lowercase for easier parsing and lookups
        text = text.lower()
        applied_normalizations.append('lowercased')
        
        # 3. Standardize quotes
        text = text.replace('"', '"').replace('"', '"')  # Smart quotes to regular
        text = text.replace(''', "'").replace(''', "'")  # Smart apostrophes to regular
        
        # 4. Standardize hyphens and dashes
        text = text.replace('–', '-').replace('—', '-')  # En/em dash to hyphen
        text = text.replace('−', '-')  # Minus sign to hyphen
        
        # 5. Fix spacing issues
        text = ' '.join(text.split())  # Normalize whitespace
        
        # 6. Fix punctuation spacing
        text = text.replace(' ,', ',').replace(' .', '.')
        text = text.replace(' ;', ';').replace(' :', ':')
        text = text.replace('( ', '(').replace(' )', ')')
        text = text.replace('[ ', '[').replace(' ]', ']')
        
        # 7. Standardize abbreviations and acronyms (keep lowercase)
        text = text.replace('i.e.', 'i.e.,').replace('e.g.', 'e.g.,')  # Add comma after abbreviations
        text = text.replace(' etc', ', etc').replace(',etc', ', etc')  # Fix etc formatting
        
        # 8. Fix common medical/nursing terminology (all lowercase for consistency)
        medical_corrections = {
            'dyspnea': 'dyspnea',  # Ensure consistent spelling
            'tachypnea': 'tachypnea',
            'bradypnea': 'bradypnea',
            'healthcare': 'health care',  # Nursing standard
            'selfcare': 'self-care',
            'wellbeing': 'well-being',
            'ongoing': 'ongoing',
        }
        
        for incorrect, correct in medical_corrections.items():
            if incorrect.lower() in text:
                # Replace with lowercase correct version
                import re
                text = re.sub(re.escape(incorrect.lower()), correct.lower(), text)
        
        # Track if any changes were made
        if text != original_text:
            applied_normalizations.append('text_content_normalized')
            # Update stats
            for norm in applied_normalizations:
                self.stats['content_normalizations'][norm] = self.stats['content_normalizations'].get(norm, 0) + 1
        
        return text.strip()

    def normalize_dict_content(self, value: Any) -> Dict[str, Any]:
        """Normalize dictionary content like client_outcomes."""
        if not isinstance(value, dict):
            return value
        
        normalized_dict = {}
        for key, val in value.items():
            # Normalize the key (lowercase)
            normalized_key = self.normalize_text_content(str(key)) if key else key
            
            # Normalize the value based on its type
            if isinstance(val, str):
                normalized_dict[normalized_key] = self.normalize_text_content(val)
            elif isinstance(val, list):
                normalized_dict[normalized_key] = self.normalize_to_list(val)
            elif isinstance(val, dict):
                normalized_dict[normalized_key] = self.normalize_dict_content(val)
            else:
                normalized_dict[normalized_key] = val
        
        return normalized_dict

    def normalize_to_list(self, value: Any) -> List[str]:
        """Convert various input types to a list of strings with content normalization."""
        if value is None or value == "":
            return []
        elif isinstance(value, list):
            # Handle nested lists and ensure all items are strings with content normalization
            result = []
            for item in value:
                if isinstance(item, str):
                    normalized_item = self.normalize_text_content(item.strip())
                    if normalized_item:  # Only add non-empty items
                        result.append(normalized_item)
                elif item is not None:
                    normalized_item = self.normalize_text_content(str(item).strip())
                    if normalized_item:
                        result.append(normalized_item)
            return result
        elif isinstance(value, str):
            normalized = self.normalize_text_content(value.strip())
            return [normalized] if normalized else []
        else:
            normalized = self.normalize_text_content(str(value).strip())
            return [normalized] if normalized else []

    def normalize_to_string(self, value: Any) -> str:
        """Convert various input types to a single string with content normalization."""
        if value is None or value == "":
            return ""
        elif isinstance(value, list):
            # Join list items with ". " if they look like sentences, otherwise with ", "
            if value:
                # Normalize each item first
                normalized_items = []
                for item in value:
                    if item:
                        normalized_item = self.normalize_text_content(str(item).strip())
                        if normalized_item:
                            normalized_items.append(normalized_item)
                
                if normalized_items:
                    # Check if items look like sentences (end with punctuation)
                    if any(item.endswith(('.', '!', '?')) for item in normalized_items):
                        return " ".join(normalized_items)
                    else:
                        return ", ".join(normalized_items)
            return ""
        elif isinstance(value, str):
            return self.normalize_text_content(value.strip())
        else:
            return self.normalize_text_content(str(value).strip())

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
                    # Keep as-is (only page_num)
                    normalized[target_field] = value if value is not None else normalized.get(target_field)
                elif target_field == 'diagnosis':
                    # Keep diagnosis in original case for readability
                    normalized[target_field] = str(value).strip() if value is not None else ""
                elif target_field == 'client_outcomes':
                    # Normalize dictionary content (lowercase all text)
                    if value is not None:
                        normalized[target_field] = self.normalize_dict_content(value)
                elif target_field in self.string_fields or target_field in ['definition', 'refer_to']:
                    # Convert to string with content normalization (lowercase)
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
        
        print(f"\nContent normalizations:")
        for normalization, count in self.stats['content_normalizations'].items():
            print(f"  {normalization}: {count} text normalizations")
        
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
    input_file = os.path.join('..', 'data', 'output', 'raw_NNN_content.json')
    output_file = os.path.join('..', 'data', 'output', 'normalized_NNN_content_all_fields.json')

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