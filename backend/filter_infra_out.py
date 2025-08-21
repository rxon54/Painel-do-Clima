#!/usr/bin/env python3
"""
Filter Infrastructure Sectors Out

This script removes all indicators related to infrastructure sectors that are
not directly linked to cities and return null data from the API.

Usage:
    python filter_infra_out.py input.json output.json

Infrastructure sectors to filter out:
- 40000: Infraestrutura Portuária
- 70000: Infraestrutura Rodoviária  
- 80000: Infraestrutura Ferroviária

The script removes:
1. Any indicators with these exact IDs (if they exist)
2. Any indicators that have these IDs as their parent (indicador_pai)
3. Recursively removes any indicators that have filtered indicators as parents
"""

import json
import sys
import os

# Infrastructure sector IDs to filter out
INFRA_SECTORS = {'40000', '70000', '80000'}

def filter_infrastructure_indicators(input_file, output_file):
    """
    Filter out infrastructure indicators from the JSON file.
    
    Args:
        input_file (str): Path to input JSON file
        output_file (str): Path to output JSON file
    """
    try:
        # Load the input JSON
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Loaded {len(data)} indicators from {input_file}")
        
        # Keep track of IDs to filter out (start with the main infrastructure sectors)
        ids_to_filter = set(INFRA_SECTORS)
        
        # Find all indicators to filter out (recursive)
        changed = True
        while changed:
            changed = False
            for item in data:
                indicator_id = str(item.get('id', ''))
                parent_id = str(item.get('indicador_pai', ''))
                
                # If this indicator's parent is in our filter list, add it to filter list
                if parent_id in ids_to_filter and indicator_id not in ids_to_filter:
                    ids_to_filter.add(indicator_id)
                    changed = True
                    print(f"  -> Marking {indicator_id} for removal (child of {parent_id})")
        
        # Filter out the indicators
        filtered_data = []
        removed_count = 0
        
        for item in data:
            indicator_id = str(item.get('id', ''))
            
            if indicator_id in ids_to_filter:
                removed_count += 1
                print(f"  -> Removing indicator {indicator_id}: {item.get('nome', 'N/A')}")
            else:
                filtered_data.append(item)
        
        print(f"\nFiltering complete:")
        print(f"  Original indicators: {len(data)}")
        print(f"  Removed indicators: {removed_count}")
        print(f"  Remaining indicators: {len(filtered_data)}")
        
        # Write the filtered JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(filtered_data, f, indent=4, ensure_ascii=False)
        
        print(f"\nFiltered data saved to: {output_file}")
        
        # Print summary of what was removed
        print(f"\nRemoved indicators by sector:")
        sector_counts = {}
        for item in data:
            indicator_id = str(item.get('id', ''))
            if indicator_id in ids_to_filter:
                parent_id = str(item.get('indicador_pai', ''))
                if parent_id in INFRA_SECTORS:
                    sector = parent_id
                elif indicator_id in INFRA_SECTORS:
                    sector = indicator_id
                else:
                    sector = 'nested'
                
                sector_counts[sector] = sector_counts.get(sector, 0) + 1
        
        for sector, count in sector_counts.items():
            if sector in INFRA_SECTORS:
                sector_name = {
                    '40000': 'Infraestrutura Portuária',
                    '70000': 'Infraestrutura Rodoviária', 
                    '80000': 'Infraestrutura Ferroviária'
                }.get(sector, sector)
                print(f"  {sector} ({sector_name}): {count} indicators")
            else:
                print(f"  {sector}: {count} indicators")
                
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        return False
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in input file: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True

def main():
    if len(sys.argv) != 3:
        print("Usage: python filter_infra_out.py input.json output.json")
        print()
        print("This script filters out infrastructure indicators that are not linked to cities:")
        print("  - 40000: Infraestrutura Portuária")
        print("  - 70000: Infraestrutura Rodoviária")
        print("  - 80000: Infraestrutura Ferroviária")
        print()
        print("Example:")
        print("  python filter_infra_out.py adaptaBrasilAPIEstrutura.json adaptaBrasilAPIEstrutura_filtered.json")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' does not exist.")
        sys.exit(1)
    
    # Check if output directory exists
    output_dir = os.path.dirname(os.path.abspath(output_file))
    if not os.path.exists(output_dir):
        print(f"Error: Output directory '{output_dir}' does not exist.")
        sys.exit(1)
    
    # Run the filtering
    if filter_infrastructure_indicators(input_file, output_file):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
