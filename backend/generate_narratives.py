import json
import os
import re
import yaml
from typing import Dict, Any, Optional

from backend.narrative_models import ClimateNarrative, NarrativeComponent, IndicatorData
from backend.llm_prompts import (
    get_introduction_prompt,
    get_problem_statement_prompt,
    get_risk_driver_prompt,
    get_impact_item_prompt,
    get_daily_implications_prompt,
    get_solutions_prompt,
    get_conclusion_prompt,
)
from backend.render_html import render_narrative_to_html # Import the rendering function
import litellm
from litellm import completion
from langfuse.decorators import observe, langfuse_context

def load_config(config_path: str = "../config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def setup_llm_config(config: Dict[str, Any]) -> None:
    """Configure LiteLLM and Langfuse based on config file."""
    llm_config = config.get('llm', {})
    observability_config = config.get('observability', {})
    
    # Set LiteLLM configuration
    litellm.drop_params = True  # Automatically drop unsupported parameters
    litellm.request_timeout = llm_config.get('timeout', 30)
    litellm.num_retries = llm_config.get('max_retries', 3)
    
    # Configure Langfuse if enabled
    if observability_config.get('enabled', False):
        # Set Langfuse environment variables if not already set
        if not os.getenv('LANGFUSE_PUBLIC_KEY'):
            print("Warning: LANGFUSE_PUBLIC_KEY not set. Langfuse observability will be disabled.")
        if not os.getenv('LANGFUSE_SECRET_KEY'):
            print("Warning: LANGFUSE_SECRET_KEY not set. Langfuse observability will be disabled.")
        if not os.getenv('LANGFUSE_HOST'):
            os.environ['LANGFUSE_HOST'] = 'https://cloud.langfuse.com'
        
        # Enable Langfuse integration
        litellm.success_callback = ["langfuse"]
        litellm.failure_callback = ["langfuse"]
        
        # Set project metadata
        if observability_config.get('project_name'):
            langfuse_context.configure(
                session_id=f"painel-{observability_config.get('environment', 'dev')}"
            )

@observe(name="llm_narrative_generation")
def generate_llm_response(prompt: str, config: Dict[str, Any], component_type: str = "narrative") -> Optional[Dict[str, Any]]:
    """
    Sends a prompt to the LLM using LiteLLM and returns the parsed JSON response.
    """
    llm_config = config.get('llm', {})
    
    try:
        # Add component type as metadata for observability
        langfuse_context.update_current_observation(
            metadata={
                "component_type": component_type,
                "model": llm_config.get('model', 'openai/gpt-4o-mini'),
                "temperature": llm_config.get('temperature', 0.3)
            }
        )
        
        response = completion(
            model=llm_config.get('model', 'openai/gpt-4o-mini'),
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates ONLY JSON. Do NOT include any markdown code blocks or extra text. Just the raw JSON object. Ensure the JSON is valid and directly parsable."},
                {"role": "user", "content": prompt}
            ],
            temperature=llm_config.get('temperature', 0.3),
            max_tokens=llm_config.get('max_tokens', 2000),
        )
        
        raw_content = response.choices[0].message.content
        # print(f"Raw LLM response: {raw_content}") # Debugging line
        
        # Attempt to parse directly first
        try:
            parsed_json = json.loads(raw_content)
            # print(f"Directly parsed JSON: {parsed_json}")
            langfuse_context.update_current_observation(
                output=parsed_json,
                metadata={"parsing_method": "direct"}
            )
            return parsed_json
        except json.JSONDecodeError:
            # If direct parsing fails, try to extract from markdown code block (fallback)
            match = re.search(r"```json\n([\s\S]*?)\n```", raw_content)
            if match:
                json_string = match.group(1)
                # print(f"Extracted JSON from markdown: {json_string}")
                parsed_json = json.loads(json_string)
                langfuse_context.update_current_observation(
                    output=parsed_json,
                    metadata={"parsing_method": "markdown_extraction"}
                )
                return parsed_json
            else:
                print(f"Could not find JSON in markdown block or parse directly. Raw content: {raw_content}")
                langfuse_context.update_current_observation(
                    level="ERROR",
                    status_message="Failed to parse JSON from LLM response"
                )
                return None

    except Exception as e:
        print(f"Error interacting with LLM: {e}")
        langfuse_context.update_current_observation(
            level="ERROR",
            status_message=f"LLM interaction failed: {str(e)}"
        )
        return None

@observe(name="create_climate_narrative")
def create_climate_narrative(city_id, city_name, problematic_indicators, config):
    """
    Generates a complete climate narrative by calling the LLM for each component.
    """
@observe(name="create_climate_narrative")
def create_climate_narrative(city_id, city_name, problematic_indicators, config):
    """
    Generates a complete climate narrative by calling the LLM for each component.
    """
    narrative_components = []
    
    # Add trace metadata for observability
    langfuse_context.update_current_observation(
        input={
            "city_id": city_id,
            "city_name": city_name,
            "problematic_indicators_count": len(problematic_indicators)
        }
    )

    # For simplicity, we will use placeholder risk values. In a real scenario, these would be calculated.
    current_risk = 0.35
    projected_risk = 0.55

    # 1. Introduction
    intro_prompt = get_introduction_prompt(city_name, current_risk, projected_risk)
    intro_data = generate_llm_response(intro_prompt, config, "introduction")
    if intro_data:
        try:
            narrative_components.append(NarrativeComponent(**intro_data))
            # print(f"Successfully added introduction component. Total components: {len(narrative_components)}")
        except Exception as e:
            print(f"Error parsing introduction component: {e} Data: {intro_data}")

    # 2. Problem Statement
    problem_prompt = get_problem_statement_prompt(city_name, current_risk, projected_risk)
    problem_data = generate_llm_response(problem_prompt, config, "problem_statement")
    if problem_data:
        try:
            narrative_components.append(NarrativeComponent(**problem_data))
            # print(f"Successfully added problem statement component. Total components: {len(narrative_components)}")
        except Exception as e:
            print(f"Error parsing problem statement component: {e} Data: {problem_data}")

    # 3. Risk Drivers
    # Filter problematic_indicators for risk drivers
    risk_drivers_to_process = [ind for ind in problematic_indicators if "vulnerabilidade" in ind["indicator_name:"].lower() or "capacidade adaptativa" in ind["indicator_name:"].lower()]
    for indicator in risk_drivers_to_process:
        driver_prompt = get_risk_driver_prompt(indicator)
        driver_data = generate_llm_response(driver_prompt, config, "risk_driver")
        if driver_data:
            try:
                narrative_components.append(NarrativeComponent(**driver_data))
                # print(f"Successfully added risk driver component: {driver_data.get(\'title\')}. Total components: {len(narrative_components)}")
            except Exception as e:
                print(f"Error parsing risk driver component: {e} Data: {driver_data}")

    # 4. Specific Impacts
    # Filter problematic_indicators for specific impacts
    impacts_to_process = [ind for ind in problematic_indicators if "seca" in ind["indicator_name:"].lower() or "precipitação" in ind["indicator_name:"].lower()]
    for indicator in impacts_to_process:
        impact_prompt = get_impact_item_prompt(indicator)
        impact_data = generate_llm_response(impact_prompt, config, "impact_item")
        if impact_data:
            try:
                narrative_components.append(NarrativeComponent(**impact_data))
                # print(f"Successfully added impact item component: {impact_data.get(\'title\')}. Total components: {len(narrative_components)}")
            except Exception as e:
                print(f"Error parsing impact item component: {e} Data: {impact_data}")

    # 5. Daily Life Implications
    # Only generate if there are problematic indicators to summarize
    if problematic_indicators:
        implications_summary = ", ".join([ind["indicator_name:"].replace("\n", " ") for ind in problematic_indicators]) # Clean up newlines
        implications_prompt = get_daily_implications_prompt(implications_summary)
        implications_data = generate_llm_response(implications_prompt, config, "daily_implications")
        if implications_data:
            try:
                narrative_components.append(NarrativeComponent(**implications_data))
                # print(f"Successfully added daily implications component. Total components: {len(narrative_components)}")
            except Exception as e:
                print(f"Error parsing daily implications component: {e} Data: {implications_data}")

    # 6. Solutions
    # Only generate if there are problematic indicators to summarize
    if problematic_indicators:
        solutions_prompt = get_solutions_prompt(implications_summary)
        solutions_data = generate_llm_response(solutions_prompt, config, "solutions")
        if solutions_data:
            try:
                narrative_components.append(NarrativeComponent(**solutions_data))
                # print(f"Successfully added solutions component. Total components: {len(narrative_components)}")
            except Exception as e:
                print(f"Error parsing solutions component: {e} Data: {solutions_data}")

    # 7. Conclusion
    conclusion_prompt = get_conclusion_prompt()
    conclusion_data = generate_llm_response(conclusion_prompt, config, "conclusion")
    if conclusion_data:
        try:
            narrative_components.append(NarrativeComponent(**conclusion_data))
            # print(f"Successfully added conclusion component. Total components: {len(narrative_components)}")
        except Exception as e:
            print(f"Error parsing conclusion component: {e} Data: {conclusion_data}")

    # print(f"Final number of narrative components before returning: {len(narrative_components)}")
    final_narrative = ClimateNarrative(city_id=str(city_id), city_name=city_name, narrative_components=narrative_components)
    
    # Update trace with output metadata
    langfuse_context.update_current_observation(
        output={
            "narrative_components_count": len(narrative_components),
            "city_id": city_id,
            "city_name": city_name
        }
    )
    
    return final_narrative

# --- Existing code from generate_narratives.py ---

def is_indicator_problematic(indicator_data):
    """
    Determines if an indicator is problematic based on its current state and future trends.
    An indicator is problematic if its current state is not good, or if it is good but worsens in the future.
    """
    proporcao_direta = int(indicator_data.get("proporcao_direta", "-1"))
    current_value = indicator_data.get("value")
    rangelabel = indicator_data.get("rangelabel")
    future_trends = indicator_data.get("future_trends", {})

    if current_value is None:
        # If no current value, consider it problematic for now to ensure it is reviewed
        return True

    # Define what constitutes a "good" rangelabel for each proporcao_direta
    # These are the states we want to FILTER OUT (i.e., not problematic in current state)
    GOOD_RANGELABELS_FOR_WORSE_IS_HIGHER = ["Baixo", "Muito baixo"]
    GOOD_RANGELABELS_FOR_BETTER_IS_HIGHER = ["Alto", "Muito alto"]

    # Check if the indicator is "good" in its current state based on rangelabel
    is_currently_good_by_label = False
    if proporcao_direta == 1: # Higher value is worse, so "Baixo" or "Muito baixo" are good
        if rangelabel in GOOD_RANGELABELS_FOR_WORSE_IS_HIGHER:
            is_currently_good_by_label = True
    elif proporcao_direta == 0: # Higher value is better, so "Alto" or "Muito alto" are good
        if rangelabel in GOOD_RANGELABELS_FOR_BETTER_IS_HIGHER:
            is_currently_good_by_label = True

    # If it is not currently good by label, it is problematic
    if not is_currently_good_by_label:
        return True

    # If it is currently good by label, check if it worsens in the future
    for year_str in sorted(future_trends.keys()): # Iterate through years to check for worsening trends
        trend_data = future_trends[year_str]
        future_value = trend_data.get("value")
        
        if future_value is not None:
            if proporcao_direta == 1: # Higher is worse
                if future_value > current_value: # If future value is numerically higher (worse)
                    return True # It is problematic due to worsening trend
            elif proporcao_direta == 0: # Higher is better
                if future_value < current_value: # If future value is numerically lower (worse)
                    return True # It is problematic due to worsening trend

    return False # It is currently good and does not worsen in the future

@observe(name="generate_narratives_main")
def generate_narratives(city_id, state_abbr, input_data_dir, output_data_dir):
    """
    Loads sector-based JSON files, filters indicators, and prepares data for LLM.
    """
    # Load configuration
    config = load_config()
    setup_llm_config(config)
    
    # Add trace metadata
    langfuse_context.update_current_observation(
        input={
            "city_id": city_id,
            "state_abbr": state_abbr,
            "input_data_dir": input_data_dir,
            "output_data_dir": output_data_dir
        }
    )
    
    city_data_path = os.path.join(input_data_dir, state_abbr, str(city_id))
    output_city_data_path = os.path.join(output_data_dir, state_abbr, str(city_id))
    os.makedirs(output_city_data_path, exist_ok=True)

    all_problematic_indicators = []
    city_name = ""

    for filename in os.listdir(city_data_path):
        if filename.endswith(".json"):
            filepath = os.path.join(city_data_path, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                sector_data = json.load(f)
            
            if not city_name:
                city_name = sector_data.get("city_name", "")

            # Filter indicators based on the is_indicator_problematic logic
            # Only include indicators that ARE problematic
            problematic_indicators = [ind for ind in sector_data.get("indicators", []) if is_indicator_problematic(ind)]
            
            if problematic_indicators:
                all_problematic_indicators.extend(problematic_indicators)

    # Generate the full narrative using the LLM
    climate_narrative = create_climate_narrative(city_id, city_name, all_problematic_indicators, config)

    # Save the generated narrative to a new JSON file
    output_filepath = os.path.join(output_city_data_path, "climate_narrative.json")
    with open(output_filepath, "w", encoding="utf-8") as f:
        f.write(climate_narrative.model_dump_json(indent=2))

    # Render the narrative to HTML
    html_output_filepath = os.path.join(output_city_data_path, "climate_narrative.html")
    print(f"Attempting to render HTML to: {html_output_filepath}") # Debug print
    render_narrative_to_html(climate_narrative.model_dump(), html_output_filepath)

    print(f"Climate narrative saved to {output_filepath}")
    print(f"HTML narrative saved to {html_output_filepath}")
    
    # Update trace with output
    langfuse_context.update_current_observation(
        output={
            "climate_narrative_path": output_filepath,
            "html_narrative_path": html_output_filepath,
            "problematic_indicators_count": len(all_problematic_indicators)
        }
    )

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate filtered climate narratives for LLM input.")
    parser.add_argument("city_id", type=int, help="The ID of the city.")
    parser.add_argument("state_abbr", type=str, help="The abbreviation of the state (e.g., PR).")
    parser.add_argument("input_data_dir", type=str, help="Path to the input data directory (e.g., data/LLM).")
    parser.add_argument("output_data_dir", type=str, help="Path to the output data directory (e.g., data/LLM_processed).")

    args = parser.parse_args()

    generate_narratives(args.city_id, args.state_abbr, args.input_data_dir, args.output_data_dir)


