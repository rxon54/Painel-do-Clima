import json
import os
import re
import yaml
from typing import Dict, Any, Optional

from narrative_models import ClimateNarrative, NarrativeComponent, IndicatorData
from llm_prompts import (
    get_introduction_prompt,
    get_problem_statement_prompt,
    get_risk_driver_prompt,
    get_impact_item_prompt,
    get_daily_implications_prompt,
    get_solutions_prompt,
    get_conclusion_prompt,
)
from render_html import render_narrative_to_html # Import the rendering function
import litellm
from litellm import completion

def load_config(config_path: str = "../config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def setup_llm_config(config: Dict[str, Any]) -> None:
    """Configure LiteLLM and Langfuse based on config file."""
    llm_config = config.get('llm', {})
    observability_config = config.get('observability', {})
    
    # Set API keys from config as environment variables
    if config.get('OPENAI_API_KEY') and not os.getenv('OPENAI_API_KEY'):
        os.environ['OPENAI_API_KEY'] = config['OPENAI_API_KEY']
        print("OpenAI API key loaded from config file")
    
    if config.get('LANGFUSE_PUBLIC_KEY') and not os.getenv('LANGFUSE_PUBLIC_KEY'):
        os.environ['LANGFUSE_PUBLIC_KEY'] = config['LANGFUSE_PUBLIC_KEY']
        print("Langfuse public key loaded from config file")
    
    if config.get('LANGFUSE_SECRET_KEY') and not os.getenv('LANGFUSE_SECRET_KEY'):
        os.environ['LANGFUSE_SECRET_KEY'] = config['LANGFUSE_SECRET_KEY']
        print("Langfuse secret key loaded from config file")
    
    if config.get('LANGFUSE_HOST') and not os.getenv('LANGFUSE_HOST'):
        os.environ['LANGFUSE_HOST'] = config['LANGFUSE_HOST']
        print("Langfuse host loaded from config file")
    
    # Set LiteLLM configuration
    litellm.drop_params = True  # Automatically drop unsupported parameters
    
    # Configure Langfuse OpenTelemetry integration if enabled
    if observability_config.get('enabled', False):
        # Check if required Langfuse environment variables are now set
        if not os.getenv('LANGFUSE_PUBLIC_KEY'):
            print("Warning: LANGFUSE_PUBLIC_KEY not set. Langfuse observability will be disabled.")
            return
        if not os.getenv('LANGFUSE_SECRET_KEY'):
            print("Warning: LANGFUSE_SECRET_KEY not set. Langfuse observability will be disabled.")
            return
        
        # Set Langfuse host from config or use default
        langfuse_host = observability_config.get('host', 'https://cloud.langfuse.com')
        if not os.getenv('LANGFUSE_HOST'):
            os.environ['LANGFUSE_HOST'] = os.environ.get('LANGFUSE_HOST', langfuse_host)
        
        try:
            # Enable Langfuse OpenTelemetry integration
            litellm.success_callback = ["langfuse_otel"]
            litellm.failure_callback = ["langfuse_otel"]
            
            # Set project and environment metadata
            if observability_config.get('project_name'):
                os.environ['LANGFUSE_PROJECT'] = observability_config.get('project_name')
            if observability_config.get('environment'):
                os.environ['LANGFUSE_ENVIRONMENT'] = observability_config.get('environment')
            
            print(f"Langfuse observability enabled for project: {observability_config.get('project_name', 'default')}")
            
        except Exception as e:
            print(f"Warning: Failed to initialize Langfuse observability: {e}")
            print("LLM calls will proceed without observability tracing.")
            # Reset callbacks to avoid errors
            litellm.success_callback = []
            litellm.failure_callback = []

def generate_llm_response(prompt: str, config: Dict[str, Any], component_type: str = "narrative") -> Optional[Dict[str, Any]]:
    """
    Sends a prompt to the LLM using LiteLLM and returns the parsed JSON response.
    """
    llm_config = config.get('llm', {})
    
    try:
        # Temporarily disable callbacks if there are issues
        original_success_callback = litellm.success_callback.copy() if litellm.success_callback else []
        original_failure_callback = litellm.failure_callback.copy() if litellm.failure_callback else []
        
        try:
            response = completion(
                model=llm_config.get('model', 'openai/gpt-4o-mini'),
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates ONLY JSON. Do NOT include any markdown code blocks or extra text. Just the raw JSON object. Ensure the JSON is valid and directly parsable."},
                    {"role": "user", "content": prompt}
                ],
                temperature=llm_config.get('temperature', 0.3),
                max_tokens=llm_config.get('max_tokens', 2000),
                # Add metadata for observability
                metadata={
                    "component_type": component_type,
                    "city_processing": True,
                    "painel_do_clima": True
                },
                # Add tags for better tracing
                tags=["climate-narrative", component_type]
            )
        except Exception as callback_error:
            # If there's a callback error, retry without observability
            if "sdk_integration" in str(callback_error) or "langfuse" in str(callback_error).lower():
                print(f"Warning: Langfuse callback error, retrying without observability: {callback_error}")
                # Temporarily disable callbacks
                litellm.success_callback = []
                litellm.failure_callback = []
                
                response = completion(
                    model=llm_config.get('model', 'openai/gpt-4o-mini'),
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that generates ONLY JSON. Do NOT include any markdown code blocks or extra text. Just the raw JSON object. Ensure the JSON is valid and directly parsable."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=llm_config.get('temperature', 0.3),
                    max_tokens=llm_config.get('max_tokens', 2000),
                )
                
                # Restore original callbacks for next call
                litellm.success_callback = original_success_callback
                litellm.failure_callback = original_failure_callback
            else:
                raise callback_error
        
        raw_content = response.choices[0].message.content  # type: ignore
        if not raw_content:
            print("LLM returned empty content")
            return None
            
        # print(f"Raw LLM response: {raw_content}") # Debugging line
        
        # Attempt to parse directly first
        try:
            parsed_json = json.loads(raw_content)
            # print(f"Directly parsed JSON: {parsed_json}")
            return parsed_json
        except json.JSONDecodeError:
            # If direct parsing fails, try to extract from markdown code block (fallback)
            match = re.search(r"```json\n([\s\S]*?)\n```", raw_content)
            if match:
                json_string = match.group(1)
                # print(f"Extracted JSON from markdown: {json_string}")
                parsed_json = json.loads(json_string)
                return parsed_json
            else:
                print(f"Could not find JSON in markdown block or parse directly. Raw content: {raw_content}")
                return None

    except Exception as e:
        print(f"Error interacting with LLM: {e}")
        return None

def create_climate_narrative(city_id, city_name, problematic_indicators, config):
    """
    Generates a complete climate narrative by calling the LLM for each component.
    """
    narrative_components = []

    # For simplicity, we will use placeholder risk values. In a real scenario, these would be calculated.
    current_risk = 0.35
    projected_risk = 0.55

    print(f"Generating climate narrative for {city_name} (ID: {city_id}) with {len(problematic_indicators)} problematic indicators")

    # 1. Introduction
    intro_prompt = get_introduction_prompt(city_name, current_risk, projected_risk)
    intro_data = generate_llm_response(intro_prompt, config, "introduction")
    if intro_data:
        try:
            narrative_components.append(NarrativeComponent(**intro_data))
            print(f"Successfully added introduction component. Total components: {len(narrative_components)}")
        except Exception as e:
            print(f"Error parsing introduction component: {e} Data: {intro_data}")

    # 2. Problem Statement
    problem_prompt = get_problem_statement_prompt(city_name, current_risk, projected_risk)
    problem_data = generate_llm_response(problem_prompt, config, "problem_statement")
    if problem_data:
        try:
            narrative_components.append(NarrativeComponent(**problem_data))
            print(f"Successfully added problem statement component. Total components: {len(narrative_components)}")
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
                print(f"Successfully added risk driver component: {driver_data.get('title')}. Total components: {len(narrative_components)}")
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
                print(f"Successfully added impact item component: {impact_data.get('title')}. Total components: {len(narrative_components)}")
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
                print(f"Successfully added daily implications component. Total components: {len(narrative_components)}")
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
                print(f"Successfully added solutions component. Total components: {len(narrative_components)}")
            except Exception as e:
                print(f"Error parsing solutions component: {e} Data: {solutions_data}")

    # 7. Conclusion
    conclusion_prompt = get_conclusion_prompt()
    conclusion_data = generate_llm_response(conclusion_prompt, config, "conclusion")
    if conclusion_data:
        try:
            narrative_components.append(NarrativeComponent(**conclusion_data))
            print(f"Successfully added conclusion component. Total components: {len(narrative_components)}")
        except Exception as e:
            print(f"Error parsing conclusion component: {e} Data: {conclusion_data}")

    print(f"Final number of narrative components before returning: {len(narrative_components)}")
    final_narrative = ClimateNarrative(city_id=str(city_id), city_name=city_name, narrative_components=narrative_components)
    
    return final_narrative

# --- Existing code from generate_narratives.py ---

# NOTE: Problematic indicator filtering logic has been moved to 
# backend/filter_problematic_indicators.py for better separation of concerns.
# This module now expects pre-filtered data from the 'problematic_indicators_only' directory.

def generate_narratives(city_id, state_abbr, input_data_dir, output_data_dir):
    """
    Loads pre-filtered sector-based JSON files and prepares data for LLM.
    
    This function now expects that filter_problematic_indicators.py has already been run
    to create the 'problematic_indicators_only' subdirectory with filtered data.
    """
    # Load configuration
    config = load_config()
    setup_llm_config(config)
    
    print(f"Starting narrative generation for city {city_id} in state {state_abbr}")
    
    # Read from the problematic_indicators_only subdirectory
    city_data_path = os.path.join(input_data_dir, state_abbr, str(city_id), "problematic_indicators_only")
    output_city_data_path = os.path.join(output_data_dir, state_abbr, str(city_id))
    os.makedirs(output_city_data_path, exist_ok=True)

    # Check if filtered data directory exists
    if not os.path.exists(city_data_path):
        print(f"Error: Filtered data directory not found: {city_data_path}")
        print("Please run filter_problematic_indicators.py first to create filtered data.")
        return

    all_problematic_indicators = []
    city_name = ""

    for filename in os.listdir(city_data_path):
        if filename.endswith(".json"):
            filepath = os.path.join(city_data_path, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                sector_data = json.load(f)
            
            if not city_name:
                city_name = sector_data.get("city_name", "")

            # Since data is already filtered, just collect all indicators
            problematic_indicators = sector_data.get("indicators", [])
            
            if problematic_indicators:
                all_problematic_indicators.extend(problematic_indicators)

    print(f"Found {len(all_problematic_indicators)} problematic indicators for {city_name}")

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
    print(f"Generated narrative with {len(climate_narrative.narrative_components)} components")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate filtered climate narratives for LLM input.")
    parser.add_argument("city_id", type=int, help="The ID of the city.")
    parser.add_argument("state_abbr", type=str, help="The abbreviation of the state (e.g., PR).")
    parser.add_argument("input_data_dir", type=str, help="Path to the input data directory (e.g., data/LLM).")
    parser.add_argument("output_data_dir", type=str, help="Path to the output data directory (e.g., data/LLM_processed).")

    args = parser.parse_args()

    generate_narratives(args.city_id, args.state_abbr, args.input_data_dir, args.output_data_dir)


