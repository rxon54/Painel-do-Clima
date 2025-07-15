import json
import os
from collections import defaultdict

def main(input_json='output.json', output_dir='../data/LLM'):
    # Load all indicator records
    with open(input_json, 'r', encoding='utf-8') as f:
        records = json.load(f)

    # Group by setor_estrategico
    grouped = defaultdict(list)  # { setor: [indicators...] }
    for rec in records:
        setor = rec.get('setor_estrategico', 'Outro')
        indicator = {
            'indicator_id': rec.get('id', ''),
            'indicator_name:': rec.get('nome', ''),
            'descricao_completa': rec.get('descricao_completa', ''),
            'proporcao_direta': rec.get('proporcao_direta', ''),
            'anos': rec.get('anos', ''),
            'value': None,
            'rangelabel': '',
            'future_trends': {
                '2030': {'value': None, 'valuelabel': ''},
                '2050': {'value': None, 'valuelabel': ''}
            } if '2030' in rec.get('anos', '') or '2050' in rec.get('anos', '') else {}
        }
        grouped[setor].append(indicator)

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Write one template file per sector
    for setor, indicators in grouped.items():
        out = {
            'city_id': '',
            'city_name': '',
            'setor_estrategico': setor,
            'indicators': indicators
        }
        setor_safe = setor.replace(' ', '_').replace('/', '_')
        fname = f'template_{setor_safe}.json'
        out_path = os.path.join(output_dir, fname)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Wrote LLM template files to {output_dir}/ (one per sector)")

if __name__ == '__main__':
    main()
