import json
import os
import sys
from collections import defaultdict

# Config: toggle sectors to include/exclude
INCLUDE_SECTORS = {
    '1': True,  # Recursos Hídricos
    '2': True,  # Segurança Alimentar
    '3': True,  # Segurança Energética
    '4': False, # Infraestrutura Portuária (set to True to include)
    '5': True,  # Saúde
    '6': True,  # Desastres Hidrológicos
    '8': False  # Infraestrutura Rodoviária (set to True to include)
}

sector_id_map = {
    '1': 'Recursos Hídricos',
    '2': 'Segurança Alimentar',
    '3': 'Segurança Energética',
    '4': 'Infraestrutura Portuária',
    '5': 'Saúde',
    '6': 'Desastres Hidrológicos',
    '8': 'Infraestrutura Rodoviária'
}

def build_indicators_hierarchy(records):
    """
    Build hierarchical structure of indicators organized by:
    Strategic Sector → Level 2 (indicador_pai=sector_id) → Level 1 and sub-indicators
    
    The hierarchy structure is:
    - Strategic Sectors have unique IDs when referenced as indicador_pai:
      1 = Recursos Hídricos, 2 = Segurança Alimentar, 3 = Segurança Energética,
      4 = Infraestrutura Portuária, 5 = Saúde, 6 = Desastres Hidrológicos, 
      8 = Infraestrutura Rodoviária
    - Level 2 indicators have indicador_pai = sector_id
    - Level 1 indicators have indicador_pai = Level 2 indicator ID
    
    Returns a nested dictionary with the complete hierarchy.
    """
    # First, create a lookup by ID for easy parent-child linking
    indicators_by_id = {}
    for rec in records:
        indicators_by_id[rec['id']] = {
            'id': rec['id'],
            'nome': rec['nome'],
            'descricao_completa': rec.get('descricao_completa', ''),
            'setor_estrategico': rec.get('setor_estrategico', ''),
            'indicador_pai': rec.get('indicador_pai'),
            'proporcao_direta': rec.get('proporcao_direta', ''),
            'anos': rec.get('anos', ''),
            'nivel': rec.get('nivel'),
            'children': []
        }
    
    # Build parent-child relationships
    for indicator_id, indicator in indicators_by_id.items():
        parent_id = indicator['indicador_pai']
        if parent_id and parent_id in indicators_by_id:
            indicators_by_id[parent_id]['children'].append(indicator)
    
    # Organize by strategic sectors
    hierarchy = {}
    for sector_id, sector_name in sector_id_map.items():
        if not INCLUDE_SECTORS.get(sector_id, True):
            continue  # Skip excluded sectors
        
        # Find Level 2 indicators for this sector (those with indicador_pai = sector_id)
        level_2_indicators = []
        for indicator_id, indicator in indicators_by_id.items():
            if indicator['indicador_pai'] == sector_id:
                level_2_indicators.append(indicator)
        
        if level_2_indicators:
            hierarchy[sector_name] = {
                'sector_id': sector_id,
                'sector_name': sector_name,
                'level_2_indicators': level_2_indicators
            }
    
    # Also include any indicators that don't fit the expected pattern
    orphaned_indicators = []
    for indicator_id, indicator in indicators_by_id.items():
        parent_id = indicator['indicador_pai']
        # If parent_id is not a known sector and not in indicators_by_id, it's orphaned
        if parent_id and parent_id not in sector_id_map and parent_id not in indicators_by_id:
            orphaned_indicators.append(indicator)
    
    if orphaned_indicators:
        hierarchy['_orphaned'] = {
            'sector_id': 'unknown',
            'sector_name': 'Orphaned Indicators',
            'level_2_indicators': orphaned_indicators
        }
    
    return hierarchy

def create_template_files(output_dir="../data/LLM", hierarchy_path="../data/LLM/indicators_hierarchy.json"):
    """
    Create template JSON files for each Level 2 indicator tree using the hierarchy structure.
    Each file is named template_<sector>--<Level 2 indicator_name>.json
    Removes old template_*.json files before generating new ones.
    """
    # Remove old template files
    for fname in os.listdir(output_dir):
        if fname.startswith("template_") and fname.endswith(".json"):
            os.remove(os.path.join(output_dir, fname))

    # Load the hierarchy structure
    with open(hierarchy_path, 'r', encoding='utf-8') as f:
        hierarchy = json.load(f)

    os.makedirs(output_dir, exist_ok=True)

    def flatten_tree(node):
        # Recursively flatten the tree into a list of indicator dicts (for all descendants)
        result = []
        def _walk(n):
            result.append(n)
            for child in n.get('children', []):
                _walk(child)
        _walk(node)
        return result

    for sector in hierarchy:
        sector_name = sector['nome']
        for level2 in sector['children']:
            # Build the template for this Level 2 tree
            indicators = []
            for ind in flatten_tree(level2):
                indicators.append({
                    "indicator_id": ind['id'],
                    "indicator_name:": ind['nome'],
                    "indicador_pai": ind.get('indicador_pai'),
                    "setor_estrategico": ind.get('setor_estrategico', sector_name),
                    "descricao_simples": ind.get('descricao_simples', ''),
                    "descricao_completa": ind.get('descricao_completa', ''),
                    "proporcao_direta": ind.get('proporcao_direta', ''),
                    "anos": ind.get('anos', ''),
                    "value": None,
                    "rangelabel": None,
                    "future_trends": {}
                })
            # Clean filename
            fname = f"template_{sector_name.replace(' ', '_')}--{level2['nome'].replace(' ', '_')}.json"
            fpath = os.path.join(output_dir, fname)
            template = {
                "city_id": "PLACEHOLDER_CITY_ID",
                "city_name": "PLACEHOLDER_CITY_NAME",
                "setor_estrategico": sector_name,
                "level2_indicator": level2['nome'],
                "indicators": indicators
            }
            with open(fpath, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=2, ensure_ascii=False)
            print(f"Template created: {fpath} ({len(indicators)} indicators)")

def generate_hierarchy_file(input_json, output_path='../data/LLM/indicators_hierarchy.json'):
    """
    Generate a simplified JSON file representing the full indicator hierarchy, with only selected keys in a specific order and human-readable parent names.
    Always creates synthetic sector root nodes if not present in the data.
    """
    with open(input_json, 'r', encoding='utf-8') as f:
        records = json.load(f)

    # Map of sector IDs to names
    sector_id_map = {
        '1': 'Recursos Hídricos',
        '2': 'Segurança Alimentar',
        '3': 'Segurança Energética',
        '4': 'Infraestrutura Portuária',
        '5': 'Saúde',
        '6': 'Desastres Hidrológicos',
        '8': 'Infraestrutura Rodoviária'
    }

    # Helper to get parent name
    def get_parent_name(indicador_pai):
        if not indicador_pai:
            return None
        if indicador_pai in sector_id_map:
            return sector_id_map[indicador_pai]
        parent = indicators_by_id.get(indicador_pai)
        return parent['nome'] if parent else None

    # Helper to recursively build simplified node with keys in the requested order
    def simplify_node(node):
        return {
            'id': node['id'],
            'nome': node['nome'],
            'indicador_pai': get_parent_name(node.get('indicador_pai')),
            'setor_estrategico': node.get('setor_estrategico', ''),
            'descricao_simples': node.get('descricao_simples', ''),
            'nivel': node.get('nivel', ''),
            'children': [simplify_node(child) for child in node.get('children', [])]
        }

    # Build lookup by id
    indicators_by_id = {rec['id']: {**rec, 'children': []} for rec in records}
    # Build parent-child relationships
    for rec in records:
        pid = rec.get('indicador_pai')
        if pid and pid in indicators_by_id:
            indicators_by_id[pid]['children'].append(indicators_by_id[rec['id']])

    # For each included sector, create a synthetic root node and attach all top-level indicators
    roots = []
    for sector_id, sector_name in sector_id_map.items():
        if not INCLUDE_SECTORS.get(sector_id, True):
            continue
        # Find all indicators whose indicador_pai == sector_id
        children = [indicators_by_id[rec['id']] for rec in records if rec.get('indicador_pai') == sector_id]
        root = {
            'id': sector_id,
            'nome': sector_name,
            'indicador_pai': None,
            'setor_estrategico': sector_name,
            'descricao_simples': '',
            'nivel': '',
            'children': children
        }
        roots.append(simplify_node(root))

    # Write the simplified hierarchy to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(roots, f, ensure_ascii=False, indent=2)
    print(f"Wrote simplified indicator hierarchy to {output_path}")

def main(input_json='output.json', output_dir='../data/LLM'):
    # Load all indicator records
    with open(input_json, 'r', encoding='utf-8') as f:
        records = json.load(f)

    # Generate the hierarchy file first
    generate_hierarchy_file(input_json)

    # Generate Level 2-per-file templates using the hierarchy
    create_template_files(output_dir=output_dir, hierarchy_path=os.path.join(output_dir, 'indicators_hierarchy.json'))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate LLM input templates and indicator hierarchy.")
    parser.add_argument("--input_json", type=str, default="output.json", help="Input JSON file with indicator records")
    parser.add_argument("--output_dir", type=str, default="../data/LLM", help="Output directory for templates and hierarchy")
    args = parser.parse_args()
    main(args.input_json, args.output_dir)
