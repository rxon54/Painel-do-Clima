import json
from collections import defaultdict

def generate_html_from_json(json_file='adaptaBrasilAPIEstrutura_filtered.json', html_file='../frontend/indicators_doc.html'):
    with open(json_file, 'r', encoding='utf-8') as f:
        indicators = json.load(f)

    # Group indicators by setor_estrategico
    grouped = defaultdict(list)
    for ind in indicators:
        setor = ind.get('setor_estrategico', 'Outro')
        grouped[setor].append(ind)

    html = [
        '<!DOCTYPE html>',
        '<html lang="pt-BR">',
        '<head>',
        '  <meta charset="UTF-8">',
        '  <title>AdaptaBrasil Indicadores - Documentação</title>',
        '  <style>',
        '    body { font-family: Arial, sans-serif; margin: 2em; }',
        '    h2 { margin-top: 2em; }',
        '    .indicator-section { border-bottom: 1px solid #ccc; padding-bottom: 1em; margin-bottom: 2em; }',
        '    .indicator-link { font-size: 0.95em; }',
        '    .index-list { margin-bottom: 2em; }',
        '    .index-list ul { margin: 0 0 0 1em; padding: 0; }',
        '    .index-list li { margin-bottom: 0.2em; }',
        '    .setor-title { margin-top: 2em; color: #1a4a7a; }',
        '  </style>',
        '</head>',
        '<body>',
        '  <h1>Documentação dos Indicadores AdaptaBrasil</h1>',
        '  <div class="index-list">',
        '    <h2>Índice</h2>'
    ]

    # Build clickable index
    for setor in sorted(grouped.keys()):
        html.append(f'    <h3 class="setor-title">{setor}</h3>')
        html.append('    <ul>')
        for ind in grouped[setor]:
            ind_id = ind.get('id', '')
            nome = ind.get('nome', '')
            html.append(f'      <li><a href="#indicator{ind_id}">{nome} <small>(ID: {ind_id})</small></a></li>')
        html.append('    </ul>')
    html.append('  </div>')

    # Build indicator sections grouped by setor
    for setor in sorted(grouped.keys()):
        html.append(f'<h2 class="setor-title" id="setor-{setor.replace(" ", "-")}">{setor}</h2>')
        for ind in grouped[setor]:
            ind_id = ind.get('id', '')
            nome = ind.get('nome', '')
            desc = ind.get('descricao_completa', '')
            url = ind.get('url_mostra_mapas_na_tela', '')
            html.append(f'<section class="indicator-section" id="indicator{ind_id}">')
            html.append(f'  <h3>{nome} <small>(ID: {ind_id})</small></h3>')
            html.append(f'  <p><strong>Setor estratégico:</strong> {setor}</p>')
            html.append(f'  <p><strong>Descrição:</strong><br>{desc}</p>')
            if url:
                html.append(f'  <p class="indicator-link"><a href="{url}" target="_blank">Ver mapa no sistema</a></p>')
            html.append('</section>')

    html.append('</body></html>')

    with open(html_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(html))

    print(f"HTML documentation generated: {html_file}")

if __name__ == "__main__":
    generate_html_from_json()