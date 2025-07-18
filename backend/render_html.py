import json
from jinja2 import Environment, FileSystemLoader
import os

def render_narrative_to_html(narrative_data, output_path):
    """
    Renders the climate narrative data into an HTML file.
    """
    template_dir = "templates"
    os.makedirs(template_dir, exist_ok=True)
    print(f"Template directory ensured: {template_dir}")

    # Create the template file if it doesn't exist
    template_path = os.path.join(template_dir, "narrative_template.html")
    if not os.path.exists(template_path):
        dummy_template_content = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório Climático para {{ narrative.city_name }}</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 20px; }
        h1, h2, h3 { color: #0056b3; }
        .component { margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .component h3 { margin-top: 0; }
        .impact-item { background-color: #f9f9f9; border-left: 5px solid #ffcc00; padding: 10px; margin-top: 10px; }
        .solutions-list li { margin-bottom: 10px; }
    </style>
</head>
<body>
    <h1>Relatório Climático para {{ narrative.city_name }}</h1>

    {% for component in narrative.narrative_components %}
        <div class="component {{ component.component_type }}">
            <h3>{{ component.title }}</h3>
            {% if component.body_text %}
                <p>{{ component.body_text }}</p>
            {% endif %}

            {% if component.component_type == 'introduction' %}
                <p>Índice de Impacto Climático Atual: <strong>{{ "%.2f"|format(component.current_value) }}</strong></p>
                <p>Índice de Impacto Climático Projetado (2050): <strong>{{ "%.2f"|format(component.projected_value) }}</strong></p>
            {% elif component.component_type == 'problem_statement' %}
                <p>Índice de Impacto Climático Atual: <strong>{{ "%.2f"|format(component.current_value) }}</strong></p>
                <p>Índice de Impacto Climático Projetado (2050): <strong>{{ "%.2f"|format(component.projected_value) }}</strong></p>
            {% elif component.component_type == 'impact_item' %}
                <p>Mudança: <strong>{{ component.stat_change }}</strong></p>
            {% elif component.component_type == 'daily_implications' %}
                <h4>Implicações no Dia a Dia:</h4>
                <ul>
                    {% for implication in component.implications %}
                        <li>{{ implication }}</li>
                    {% endfor %}
                </ul>
            {% elif component.component_type == 'solutions' %}
                <h4>Soluções Propostas:</h4>
                <ul class="solutions-list">
                    {% for solution in component.solutions %}
                        <li><strong>{{ solution.theme }}:</strong> {{ solution.explanation }}</li>
                    {% endfor %}
                </ul>
            {% endif %}
        </div>
    {% endfor %}

</body>
</html>
        """
        with open(template_path, "w", encoding="utf-8") as f:
            f.write(dummy_template_content)
        print(f"Template file created: {template_path}")

    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("narrative_template.html")
    print(f"Template loaded: {template_path}")

    html_content = template.render(narrative=narrative_data)
    print(f"HTML content rendered. Length: {len(html_content)}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"HTML narrative written to {output_path}")

if __name__ == "__main__":
    # Example usage (for testing purposes)
    # This part would typically be called from generate_narratives.py
    city_id = 5329
    state_abbr = "PR"
    processed_data_dir = "data/LLM_processed"

    narrative_filepath = os.path.join(processed_data_dir, state_abbr, str(city_id), "climate_narrative.json")
    output_html_filepath = os.path.join(processed_data_dir, state_abbr, str(city_id), "climate_narrative.html")

    if os.path.exists(narrative_filepath):
        with open(narrative_filepath, "r", encoding="utf-8") as f:
            narrative_data = json.load(f)
        
        render_narrative_to_html(narrative_data, output_html_filepath)
    else:
        print(f"Narrative file not found: {narrative_filepath}")


