import json

def get_introduction_prompt(city_name, current_risk, projected_risk):
    return f"""You are an expert climate communicator for the \'Painel do Clima\' project. Your goal is to explain complex climate data in an accessible, engaging, and informative way for a broad audience (general public, newsrooms, policymakers). Avoid emojis for now. Focus on clear, concise language. The tone should be serious but empowering, highlighting both challenges and solutions. Use Brazilian Portuguese. 

Generate an introductory narrative component for {city_name}. This component should:
- Briefly introduce the topic of climate change in {city_name}.
- Explain what a \'Climate Impact Index\' is (a score from 0 to 1, where higher is worse).
- State the current Climate Impact Index for {current_risk} and the projected index for 2050 ({projected_risk}).
- Emphasize the significance of the change.

Output should be a JSON object with the following structure:
{{
  "component_type": "introduction",
  "title": "Como o Clima de {city_name} está Mudando?",
  "body_text": "[Your explanation here]",
  "current_value": {current_risk},
  "projected_value": {projected_risk}
}}
"""

def get_problem_statement_prompt(city_name, current_risk, projected_risk):
    return f"""You are an expert climate communicator for the \'Painel do Clima\' project. Your goal is to explain complex climate data in an accessible, engaging, and informative way for a broad audience (general public, newsrooms, policymakers). Avoid emojis for now. Focus on clear, concise language. The tone should be serious but empowering, highlighting both challenges and solutions. Use Brazilian Portuguese. 

Generate a narrative component that quantifies the climate problem for {city_name}. This component should:
- Reiterate the current Climate Impact Index ({current_risk}) and the projected index for 2050 ({projected_risk}).
- Explain the meaning of these numbers in simple terms, emphasizing the increase in problems.
- Use an analogy if helpful (e.g., \'almost double the problems\').

Output should be a JSON object with the following structure:
{{
  "component_type": "problem_statement",
  "title": "O que é esse tal de \'Índice de Impacto Climático\'?",
  "body_text": "[Your explanation here]",
  "current_value": {current_risk},
  "projected_value": {projected_risk}
}}
"""

def get_risk_driver_prompt(indicator_data):
    return f"""You are an expert climate communicator for the \'Painel do Clima\' project. Your goal is to explain complex climate data in an accessible, engaging, and informative way for a broad audience (general public, newsrooms, policymakers). Avoid emojis for now. Focus on clear, concise language. The tone should be serious but empowering, highlighting both challenges and solutions. Use Brazilian Portuguese. 

Generate a narrative component for a climate risk driver. This component should:
- Explain the indicator \'{indicator_data["indicator_name:"]}\' in simple terms.
- Describe its relevance to climate risk.
- Provide a concise explanation of its current state and implications for the city.
- Use the provided \'descricao_completa\' for context, but rephrase it for a general audience.

Indicator Data: {json.dumps(indicator_data, ensure_ascii=False, indent=2)}

Output should be a JSON object with the following structure:
{{
  "component_type": "risk_driver",
  "title": "{indicator_data["indicator_name:"]}",
  "body_text": "[Your explanation here]",
  "value": {indicator_data["value"]},
  "rangelabel": "{indicator_data["rangelabel"]}"
}}
"""

def get_impact_item_prompt(indicator_data):
    return f"""You are an expert climate communicator for the \'Painel do Clima\' project. Your goal is to explain complex climate data in an accessible, engaging, and informative way for a broad audience (general public, newsrooms, policymakers). Avoid emojis for now. Focus on clear, concise language. The tone should be serious but empowering, highlighting both challenges and solutions. Use Brazilian Portuguese. 

Generate a narrative component for a specific climate impact. This component should:
- State the indicator \'{indicator_data["indicator_name:"]}\' .
- Clearly present the \'stat-change\' (current vs. projected value) in an understandable format.
- Explain the real-world implications of this change for daily life in the city.
- Use the provided \'descricao_completa\' for context, but rephrase it for a general audience.

Indicator Data: {json.dumps(indicator_data, ensure_ascii=False, indent=2)}

Output should be a JSON object with the following structure:
{{
  "component_type": "impact_item",
  "title": "{indicator_data["indicator_name:"]}",
  "stat_change": "[e.g., 6 -> 10 or +2°C]",
  "body_text": "[Your explanation here]",
  "current_value": {indicator_data["value"]},
  "future_trends": {json.dumps(indicator_data["future_trends"], ensure_ascii=False)}
}}
"""

def get_daily_implications_prompt(problematic_indicators_summary):
    return f"""You are an expert climate communicator for the \'Painel do Clima\' project. Your goal is to explain complex climate data in an accessible, engaging, and informative way for a broad audience (general public, newsrooms, policymakers). Avoid emojis for now. Focus on clear, concise language. The tone should be serious but empowering, highlighting both challenges and solutions. Use Brazilian Portuguese. 

Based on the following summary of problematic climate indicators, generate a narrative component detailing the daily life implications for citizens. This should be a list of short, impactful phrases describing everyday consequences.

Problematic Indicators Summary: {problematic_indicators_summary}

Output should be a JSON object with the following structure:
{{
  "component_type": "daily_implications",
  "title": "O que isso Significa no Dia a Dia?",
  "implications": [
    "[Implication 1]",
    "[Implication 2]"
  ]
}}
"""

def get_solutions_prompt(problematic_indicators_summary):
    return f"""You are an expert climate communicator for the \'Painel do Clima\' project. Your goal is to explain complex climate data in an accessible, engaging, and informative way for a broad audience (general public, newsrooms, policymakers). Avoid emojis for now. Focus on clear, concise language. The tone should be serious but empowering, highlighting both challenges and solutions. Use Brazilian Portuguese. 

Based on the following summary of problematic climate indicators, generate a narrative component proposing actionable solutions and preparation strategies. This should be a list of high-level solution themes with brief explanations.

Problematic Indicators Summary: {problematic_indicators_summary}

Output should be a JSON object with the following structure:
{{
  "component_type": "solutions",
  "title": "Como Podemos nos Preparar?",
  "solutions": [
    {{"theme": "[Solution Theme 1]", "explanation": "[Explanation 1]"}},
    {{"theme": "[Solution Theme 2]", "explanation": "[Explanation 2]"}}
  ]
}}
"""

def get_conclusion_prompt():
    return f"""You are an expert climate communicator for the \'Painel do Clima\' project. Your goal is to explain complex climate data in an accessible, engaging, and informative way for a broad audience (general public, newsrooms, policymakers). Avoid emojis for now. Focus on clear, concise language. The tone should be serious but empowering, highlighting both challenges and solutions. Use Brazilian Portuguese. 

Generate a concluding message for the climate narrative. This should be a positive and empowering message that encourages action and highlights that the future is not fixed.

Output should be a JSON object with the following structure:
{{
  "component_type": "conclusion",
  "title": "A boa notícia:",
  "body_text": "[Your concluding message here]"
}}
"""


