import json
import os
import glob
from typing import Dict, List, Optional

def load_city_filelist(filelist_path: str = "../data/city_filelist.json") -> Dict:
    """Load the city file list mapping city IDs to file paths and metadata."""
    with open(filelist_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_city_data(city_file_path: str) -> Dict:
    """Load city indicator data from the city-specific JSON file."""
    with open(city_file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_template_files(template_dir: str = "../data/LLM") -> Dict[str, Dict]:
    """Load all template files and return as a dictionary keyed by sector name."""
    templates = {}
    template_files = glob.glob(os.path.join(template_dir, "template_*.json"))
    
    for template_file in template_files:
        with open(template_file, 'r', encoding='utf-8') as f:
            template_data = json.load(f)
            # Extract sector name from filename (remove template_ prefix and .json suffix)
            sector_name = os.path.basename(template_file)[9:-5]  # Remove 'template_' and '.json'
            templates[sector_name] = template_data
    
    return templates

def create_indicator_lookup(city_data: Dict) -> Dict[int, Dict]:
    """Create a lookup dictionary of indicators by indicator_id for fast access."""
    indicator_lookup = {}
    
    for indicator in city_data.get('indicators', []):
        indicator_id = indicator.get('indicator_id')
        if indicator_id:
            if indicator_id not in indicator_lookup:
                indicator_lookup[indicator_id] = {}
            
            year = indicator.get('year')
            if year:
                indicator_lookup[indicator_id][year] = indicator
    
    return indicator_lookup

def populate_template(template: Dict, city_data: Dict, indicator_lookup: Dict[int, Dict]) -> Dict:
    """Populate a template with city-specific indicator data."""
    populated = template.copy()
    
    # Set city information
    populated['city_id'] = str(city_data.get('id', ''))
    populated['city_name'] = city_data.get('name', '')
    
    # Populate indicators
    for indicator in populated['indicators']:
        indicator_id_str = indicator.get('indicator_id', '')
        if indicator_id_str:
            try:
                indicator_id = int(indicator_id_str)
                
                # Find matching indicator data for this ID
                if indicator_id in indicator_lookup:
                    # Get the most recent record for this indicator (should be only one per indicator_id)
                    indicator_years = indicator_lookup[indicator_id]
                    latest_year = max(indicator_years.keys())
                    city_indicator_data = indicator_years[latest_year]
                    
                    # Populate present value
                    indicator['value'] = city_indicator_data.get('value')
                    indicator['rangelabel'] = city_indicator_data.get('rangelabel', '')
                    
                    # Add color info if available
                    if 'valuecolor' in city_indicator_data:
                        indicator['valuecolor'] = city_indicator_data['valuecolor']
                    
                    # Populate future trends if available in the city data
                    city_future_trends = city_indicator_data.get('future_trends', {})
                    template_future_trends = indicator.get('future_trends', {})
                    
                    for year in ['2030', '2050']:
                        if year in city_future_trends and year in template_future_trends:
                            city_year_data = city_future_trends[year]
                            template_future_trends[year]['value'] = city_year_data.get('value')
                            template_future_trends[year]['valuelabel'] = city_year_data.get('valuelabel', '')
                            
                            # Add color info if available
                            if 'valuecolor' in city_year_data:
                                template_future_trends[year]['valuecolor'] = city_year_data['valuecolor']
                            
            except (ValueError, TypeError):
                # Skip if indicator_id is not a valid integer
                continue
    
    return populated

def populate_llm_inputs_for_city(city_id: str, 
                                 city_filelist_path: str = "../data/city_filelist.json",
                                 template_dir: str = "../data/LLM",
                                 output_base_dir: str = "../data/LLM") -> bool:
    """
    Populate LLM templates with data for a specific city.
    
    Args:
        city_id: The city ID to process
        city_filelist_path: Path to city_filelist.json
        template_dir: Directory containing template files
        output_base_dir: Base directory for output files
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Load city file list
        city_filelist = load_city_filelist(city_filelist_path)
        
        if city_id not in city_filelist:
            print(f"Error: City ID '{city_id}' not found in city file list")
            return False
        
        city_info = city_filelist[city_id]
        state = city_info['state']
        city_file_path = os.path.join(os.path.dirname(city_filelist_path), city_info['file'])
        
        # Load city data
        if not os.path.exists(city_file_path):
            print(f"Error: City data file not found: {city_file_path}")
            return False
        
        city_data = load_city_data(city_file_path)
        
        # Load templates
        templates = load_template_files(template_dir)
        if not templates:
            print(f"Error: No template files found in {template_dir}")
            return False
        
        # Create indicator lookup for fast access
        indicator_lookup = create_indicator_lookup(city_data)
        
        # Create output directory
        output_dir = os.path.join(output_base_dir, state, city_id)
        os.makedirs(output_dir, exist_ok=True)
        
        # Process each template
        populated_count = 0
        for sector_name, template in templates.items():
            # Populate template with city data
            populated_template = populate_template(template, city_data, indicator_lookup)
            
            # Save populated template (remove template_ prefix)
            output_filename = f"{sector_name.replace('_', ' ')}.json"
            output_path = os.path.join(output_dir, output_filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(populated_template, f, ensure_ascii=False, indent=2)
            
            populated_count += 1
        
        print(f"Successfully populated {populated_count} LLM input files for city {city_id} ({city_info['name']}) in {output_dir}")
        return True
        
    except Exception as e:
        print(f"Error processing city {city_id}: {str(e)}")
        return False

def main():
    """Main function with example usage."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python populate_llm_inputs.py <city_id>")
        print("Example: python populate_llm_inputs.py 5302")
        return
    
    city_id = sys.argv[1]
    success = populate_llm_inputs_for_city(city_id)
    
    if not success:
        sys.exit(1)

if __name__ == '__main__':
    main()
