import json
import sys

# Usage: python extract_trends_pairs.py input.json output.txt

def extract_pairs(input_json, output_txt):
    with open(input_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    pairs = []
    for item in data:
        anos = item.get('anos')
        ind_id = item.get('id')
        if not anos or not ind_id:
            continue
        # Accept anos as string, e.g. "2019,2030,2050"
        years = [y.strip() for y in anos.split(',')]
        for year in ('2030', '2050'):
            if year in years:
                pairs.append(f"{ind_id}/{year}")
    with open(output_txt, 'w', encoding='utf-8') as f:
        for pair in pairs:
            f.write(pair + '\n')

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python extract_trends_pairs.py input.json output.txt')
        sys.exit(1)
    extract_pairs(sys.argv[1], sys.argv[2])
