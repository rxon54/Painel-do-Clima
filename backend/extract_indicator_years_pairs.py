import json
import sys
import os

# Usage: python extract_indicator_years_pairs.py input.json [output_directory]

def extract_pairs(input_json, output_dir='.'):
    with open(input_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    trends_pairs = []  # For 2030 and 2050
    mapa_pairs = []    # For first year in each list
    
    for item in data:
        anos = item.get('anos')
        ind_id = item.get('id')
        if not anos or not ind_id:
            continue
        
        # Clean up the anos string - remove brackets and split by comma
        anos_clean = anos.strip('[]"').replace('"', '').replace("'", '')
        years = [y.strip() for y in anos_clean.split(',')]
        
        # Extract trends pairs (2030 and 2050)
        for year in ('2030', '2050'):
            if year in years:
                trends_pairs.append(f"{ind_id}/{year}")
        
        # Extract mapa pairs (first year in the list)
        if years and years[0]:  # Make sure there's at least one year
            first_year = years[0].strip()
            if first_year:  # Make sure it's not empty
                mapa_pairs.append(f"{ind_id}/{first_year}")
    
    # Write trends file
    trends_file = os.path.join(output_dir, 'trends-2030-2050.txt')
    with open(trends_file, 'w', encoding='utf-8') as f:
        for pair in trends_pairs:
            f.write(pair + '\n')
    print(f"Trends pairs written to: {trends_file} ({len(trends_pairs)} pairs)")
    
    # Write mapa-dados file
    mapa_file = os.path.join(output_dir, 'mapa-dados.txt')
    with open(mapa_file, 'w', encoding='utf-8') as f:
        for pair in mapa_pairs:
            f.write(pair + '\n')
    print(f"Mapa-dados pairs written to: {mapa_file} ({len(mapa_pairs)} pairs)")

if __name__ == '__main__':
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print('Usage: python extract_indicator_years_pairs.py input.json [output_directory]')
        print('  input.json: JSON file to process')
        print('  output_directory: Directory to write output files (default: current directory)')
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_directory = sys.argv[2] if len(sys.argv) == 3 else '.'
    
    extract_pairs(input_file, output_directory)
