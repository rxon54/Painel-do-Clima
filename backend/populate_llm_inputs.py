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
    """Load all new Level 2 template files and return as a dictionary keyed by filename (without .json)."""
    templates = {}
    template_files = glob.glob(os.path.join(template_dir, "template_*--*.json"))
    for template_file in template_files:
        with open(template_file, 'r', encoding='utf-8') as f:
            template_data = json.load(f)
            # Use the filename (without extension) as the key
            key = os.path.basename(template_file)[9:-5]  # Remove 'template_' and '.json'
            templates[key] = template_data
    return templates

def create_indicator_lookup(city_data: Dict) -> Dict[str, Dict]:
    """Create a lookup dictionary of indicators by indicator_id (as str) for fast access."""
    indicator_lookup = {}
    for indicator in city_data.get('indicators', []):
        indicator_id = str(indicator.get('indicator_id'))
        if indicator_id:
            if indicator_id not in indicator_lookup:
                indicator_lookup[indicator_id] = {}
            year = indicator.get('year')
            if year:
                indicator_lookup[indicator_id][year] = indicator
    return indicator_lookup

def load_indicator_metadata(metadata_path: str = "output.json") -> dict:
    """Load indicator metadata from output.json, keyed by indicator_id as str."""
    with open(metadata_path, 'r', encoding='utf-8') as f:
        records = json.load(f)
    return {str(rec['id']): rec for rec in records}

def populate_template(template: Dict, city_data: Dict, indicator_lookup: Dict[str, Dict], indicator_metadata: Dict[str, dict]) -> Dict:
    """Populate a Level 2 template with city-specific indicator data, including proporcao_direta from metadata."""
    populated = json.loads(json.dumps(template))  # Deep copy
    populated['city_id'] = str(city_data.get('id', ''))
    populated['city_name'] = city_data.get('name', '')
    for indicator in populated['indicators']:
        indicator_id = str(indicator.get('indicator_id'))
        # Set proporcao_direta from metadata if available
        if indicator_id in indicator_metadata:
            indicator['proporcao_direta'] = indicator_metadata[indicator_id].get('proporcao_direta', '')
        if indicator_id and indicator_id in indicator_lookup:
            # Get the most recent year for this indicator
            indicator_years = indicator_lookup[indicator_id]
            latest_year = max(indicator_years.keys())
            city_indicator_data = indicator_years[latest_year]
            indicator['value'] = city_indicator_data.get('value')
            indicator['rangelabel'] = city_indicator_data.get('rangelabel', '')
            if 'valuecolor' in city_indicator_data:
                indicator['valuecolor'] = city_indicator_data['valuecolor']
            city_future_trends = city_indicator_data.get('future_trends', {})
            template_future_trends = indicator.get('future_trends', {})
            for year in template_future_trends.keys():
                if year in city_future_trends:
                    city_year_data = city_future_trends[year]
                    template_future_trends[year]['value'] = city_year_data.get('value')
                    template_future_trends[year]['valuelabel'] = city_year_data.get('valuelabel', '')
                    if 'valuecolor' in city_year_data:
                        template_future_trends[year]['valuecolor'] = city_year_data['valuecolor']
    return populated

def populate_llm_inputs_for_city(city_id: str, 
                                 city_filelist_path: str = "../data/city_filelist.json",
                                 template_dir: str = "../data/LLM",
                                 output_base_dir: str = "../data/LLM",
                                 indicator_metadata_path: str = "output.json") -> bool:
    """
    Populate new Level 2 LLM templates with data for a specific city.
    Output files are named to match the template (minus 'template_' and .json),
    and are placed in the same output dir structure as before.
    """
    try:
        city_filelist = load_city_filelist(city_filelist_path)
        if city_id not in city_filelist:
            print(f"Error: City ID '{city_id}' not found in city file list")
            return False
        city_info = city_filelist[city_id]
        state = city_info['state']
        city_file_path = os.path.join(os.path.dirname(city_filelist_path), city_info['file'])
        if not os.path.exists(city_file_path):
            print(f"Error: City data file not found: {city_file_path}")
            return False
        city_data = load_city_data(city_file_path)
        templates = load_template_files(template_dir)
        if not templates:
            print(f"Error: No template files found in {template_dir}")
            return False
        indicator_lookup = create_indicator_lookup(city_data)
        indicator_metadata = load_indicator_metadata(indicator_metadata_path)
        output_dir = os.path.join(output_base_dir, state, city_id)
        os.makedirs(output_dir, exist_ok=True)
        populated_count = 0
        for template_key, template in templates.items():
            populated_template = populate_template(template, city_data, indicator_lookup, indicator_metadata)
            output_filename = f"{template_key.replace('_', ' ')}.json"
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
