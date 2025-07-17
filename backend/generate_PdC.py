import json
import os
import litellm
from litellm import completion
import yaml
from generate_narratives import setup_llm_config, load_config
import re

# Module: generate_climate_summary.py
# Usage:
#   from generate_climate_summary import generate_html_summary
#   html = generate_html_summary(raw_text, llm_config)

PROMPT_TEMPLATE = '''
Transforme o seguinte texto em um resumo climático em JSON.

Texto de entrada:
"""
{raw_text}
"""

Instruções:
1) Agrupe componentes por "Setor" e "Nível 2".
2) Para cada grupo, crie um objeto com:
   - title: texto para <h2> no formato "Impacto no(a) <Setor> como consequência de(o/a) <Nível 2>"
   - narrative: parágrafo de introdução em linguagem acessível que gere conscientização.
   - indicators: lista de indicadores, cada um com:
       * name
       * value_current
       * value_future (se aplicável)
       * description: texto verboso explicando significado, impacto e ações.
3) Retorne somente o JSON válido.
'''

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Resumo Climático - {city}</title>
  <style>
    body {{ font-family: 'Segoe UI', sans-serif; background: #f4f4f4; color: #333; margin: 0; padding: 0; }}
    .container {{ max-width: 960px; margin: 0 auto; padding: 20px; }}
    .header {{ background: #004080; color: white; padding: 20px; border-radius: 6px; }}
    h1 {{ margin: 0; font-size: 24px; }}
    h2 {{ color: #004080; margin-top: 40px; }}
    .section {{ background: white; border-radius: 6px; padding: 20px; margin-top: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }}
    .indicator {{ margin-top: 10px; padding: 10px; background: #f9f9f9; border-left: 4px solid #2196F3; }}
    .label {{ font-weight: bold; }}
    .green {{ border-color: #4CAF50; }}
    .yellow {{ border-color: #FFEB3B; }}
    .orange {{ border-color: #FF9800; }}
    .red {{ border-color: #F44336; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Resumo Climático - {city}</h1>
      <p>Indicadores organizados por Setor e Subtema (Nível 2).</p>
    </div>
    {{% for section in data %}}
    <h2>{{{{section.title}}}}</h2>
    <div class="section">
      <p>{{{{section.narrative}}}}</p>
      {{% for ind in section.indicators %}}
      <div class="indicator {{{{ind.color_class}}}}">
        <div class="label">{{{{ind.name}}}}</div>
        <p>{{{{ind.description}}}}</p>
      </div>
      {{% endfor %}}
    </div>
    {{% endfor %}}
  </div>
</body>
</html>'''


def generate_html_summary(raw_text: str, city: str, llm_config: dict) -> str:
    """
    Gera HTML de resumo climático para a cidade informada, com base em texto bruto de indicadores.
    """
    # Ensure API keys and observability are set up
    config = load_config()
    setup_llm_config(config)
    prompt = PROMPT_TEMPLATE.format(raw_text=raw_text)
    response = completion(
        model=llm_config.get('model', 'openai/gpt-4o-mini'),
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates ONLY JSON. Do NOT include any markdown or extra text. Just the raw JSON object."},
            {"role": "user", "content": prompt}
        ],
        temperature=llm_config.get('temperature', 0.3),
        max_tokens=llm_config.get('max_tokens', 2000),
    )
    # Robust JSON extraction (direct or markdown block)
    raw_content = None
    # Try OpenAI/standard .choices[0].message.content
    choices = getattr(response, 'choices', None)
    if choices and len(choices) > 0:
        message = getattr(choices[0], 'message', None)
        if message:
            raw_content = getattr(message, 'content', None)
    # Try .content (LiteLLM streaming)
    if raw_content is None:
        raw_content = getattr(response, 'content', None)
    # Fallback to str
    if not isinstance(raw_content, str):
        raw_content = str(response)
    if not raw_content:
        raise ValueError("LLM response content is empty or not a string")
    try:
        data = json.loads(raw_content)
    except json.JSONDecodeError:
        match = re.search(r"```json\n([\s\S]*?)\n```", raw_content)
        if match:
            json_string = match.group(1)
            data = json.loads(json_string)
        else:
            raise ValueError(f"Could not parse JSON from LLM response: {raw_content}")

    # Debug: print the parsed data type and value
    print("[DEBUG] LLM output type:", type(data))
    if isinstance(data, dict):
        # Try to find the first list value in the dict
        for v in data.values():
            if isinstance(v, list):
                data = v
                break
        else:
            raise ValueError(f"LLM returned a dict but no list found: {data}")
    elif isinstance(data, str):
        raise ValueError(f"LLM returned a string, not a list: {data}")
    elif not isinstance(data, list):
        raise ValueError(f"LLM returned unexpected type: {type(data)} value: {data}")

    # Render HTML
    html = HTML_TEMPLATE.format(city=city)

    # Helper: map rangelabel/valuecolor to color_class
    def get_color_class(ind_name):
        if 'narrative_json' in globals():
            for comp in narrative_json.get('narrative_components', []):
                for si in comp.get('supporting_indicators', []) or []:
                    if ind_name.lower() in si.get('indicator_name', '').lower():
                        label = si.get('rangelabel', '').lower()
                        if label == 'muito baixo' or label == 'baixo':
                            return 'green'
                        if label == 'médio':
                            return 'yellow'
                        if label == 'alto':
                            return 'orange'
                        if label == 'muito alto':
                            return 'red'
                        color = si.get('valuecolor', '').lower()
                        if '#4caf50' in color or '#02c650' in color:
                            return 'green'
                        if '#ffeb3b' in color or '#a9de00' in color or '#ffcd00' in color:
                            return 'yellow'
                        if '#ff9800' in color:
                            return 'orange'
                        if '#f44336' in color:
                            return 'red'
        return ''

    # Montagem manual: substitua {{% for section in data %}}...
    sections_html = ''
    for sec in data:
        title = sec.get('title', '')
        narrative = sec.get('narrative', '')
        sections_html += f"<h2>{title}</h2>\n"
        sections_html += "<div class=\"section\">\n"
        sections_html += f"  <p>{narrative}</p>\n"
        for ind in sec.get('indicators', []):
            name = ind.get('name', '')
            color_class = ind.get('color_class', '') or get_color_class(name)
            description = ind.get('description', '')
            sections_html += f"  <div class=\"indicator {color_class}\">\n"
            sections_html += f"    <div class=\"label\">{name}</div>\n"
            sections_html += f"    <p>{description}</p>\n"
            sections_html += "  </div>\n"
        sections_html += "</div>\n"  # Always close .section after each section

    # Insere sections_html no template
    html = html.replace("{{% for section in data %}}", "")
    html = html.replace("{{% endfor %}}", "")
    html = html.replace("{{% for ind in section.indicators %}}", "")
    html = html.replace("{{% endfor %}}", "")
    # Remove any leftover template blocks (if present)
    html = re.sub(r"\{\{.*?\}\}", "", html, flags=re.DOTALL)
    html = re.sub(r"\{\%.*?\%\}", "", html, flags=re.DOTALL)

    # Insert narrative sections after header close
    header_marker = '</div>\n    <!-- END HEADER -->'
    if header_marker not in html:
        # fallback to header close
        header_marker = '</div>\n'
    html_parts = html.split(header_marker, 1)
    if len(html_parts) == 2:
        html = html_parts[0] + header_marker + sections_html + html_parts[1]
    else:
        html += sections_html

    # --- Add daily implications and solutions if present ---
    # Extract from narrative_json (passed as global in main)
    daily = None
    solutions = None
    if 'narrative_json' in globals():
        # Find daily_implications and solutions components
        for comp in narrative_json.get('narrative_components', []):
            if comp.get('component_type') == 'daily_implications':
                implications = comp.get('implications')
                if implications and isinstance(implications, list):
                    daily = '<ul>' + ''.join(f'<li>{i}</li>' for i in implications) + '</ul>'
                elif comp.get('body_text'):
                    daily = comp['body_text']
            if comp.get('component_type') == 'solutions':
                sols = comp.get('solutions')
                if sols and isinstance(sols, list):
                    solutions = '<ul>' + ''.join(f'<li><b>{s.get('theme','')}</b>: {s.get('explanation','')}</li>' for s in sols) + '</ul>'
                elif comp.get('body_text'):
                    solutions = comp['body_text']
    # Render if present
    summary_sections = ''
    if daily:
        summary_sections += '\n<section class="section">\n  <h2>Implicações Cotidianas</h2>\n  ' + daily + '\n</section>'
    if solutions:
        summary_sections += '\n<section class="section">\n  <h2>Soluções e Recomendações</h2>\n  ' + solutions + '\n</section>'

    # Insert summary sections before the closing .container div (only once)
    container_end = '</div>'  # .container
    idx_body = html.find('</body>')
    idx_last_div = html.rfind(container_end, 0, idx_body)
    if summary_sections and idx_last_div != -1:
        html = html[:idx_last_div] + summary_sections + html[idx_last_div:]
    elif summary_sections:
        html = html.replace('</body>', summary_sections + '\n</body>')

    return html

def load_llm_config(config_path="../config.yaml"):
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config.get('llm', {})

def extract_narrative_text(narrative_json):
    """
    Concatenate all narrative component texts for LLM summary input.
    """
    texts = []
    for comp in narrative_json.get("narrative_components", []):
        if comp.get("body_text"):
            texts.append(comp["body_text"])
    return "\n\n".join(texts)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate PdC HTML summary from climate_narrative.json")
    parser.add_argument("narrative_json_path", help="Path to climate_narrative.json")
    parser.add_argument("output_html_path", nargs="?", help="Output HTML file path (optional)")
    parser.add_argument("--city", help="City name (optional, overrides JSON)")
    parser.add_argument("--config", default="../config.yaml", help="Path to config.yaml for LLM config")
    args = parser.parse_args()

    with open(args.narrative_json_path, "r", encoding="utf-8") as f:
        global narrative_json
        narrative_json = json.load(f)
    city = args.city or narrative_json.get("city_name", "Cidade")
    llm_config = load_llm_config(args.config)
    raw_text = extract_narrative_text(narrative_json)
    html = generate_html_summary(raw_text, city, llm_config)
    output_path = args.output_html_path or os.path.splitext(args.narrative_json_path)[0] + "_PdC.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"PdC HTML summary generated for {city} and saved to {output_path}")

if __name__ == "__main__":
    main()
