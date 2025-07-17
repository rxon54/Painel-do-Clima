"""
Logic & Data Workflow:
1. Configuration & Environment Setup
- Loads configuration from config.yaml using load_config().
- Sets up environment variables for OpenAI and Langfuse (observability) via setup_llm_config().
2. Input Data Handling
- Expects pre-filtered indicator data (problematic indicators only) in a directory structure like:
input_data_dir/<state_abbr>/<city_id>/problematic_indicators_only/
- Reads all JSON files in this directory, each representing a sector’s problematic indicators for the city.
- Aggregates all problematic indicators across sectors for the city.
3. LLM Narrative Generation
- Calls create_climate_narrative() with the city info and all problematic indicators.
- This function orchestrates the generation of seven narrative components (introduction, problem statement, 
risk drivers, impacts, daily implications, solutions, conclusion) by prompting the LLM (via LiteLLM).
- Each component is generated as a structured JSON, parsed, and appended to the narrative.
4. Output Generation
- Saves the complete narrative as a JSON file:
output_data_dir/<state_abbr>/<city_id>/climate_narrative.json
- Renders the narrative to HTML using Jinja2 templates and saves as:
output_data_dir/<state_abbr>/<city_id>/climate_narrative.html
5. CLI Interface
- The script is executable from the command line, requiring four arguments:
city_id, state_abbr, input_data_dir, output_data_dir.

Summary:
This script takes pre-filtered, city-specific climate indicator data, 
generates a multi-part narrative using an LLM, and outputs both JSON and HTML reports for each city. 
It is designed to be run after the filtering step and expects the data to be organized by city and sector. 
All LLM calls are observable via Langfuse if enabled.
"""
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
                model=llm_config.get('model', 'openai/gpt-4.1'),
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
    Now groups components by sector and true Level 2 name from the hierarchy.
    """
    from collections import defaultdict
    # Load indicator metadata for parent chain lookup
    with open(os.path.join(os.path.dirname(__file__), "output.json"), "r", encoding="utf-8") as f:
        indicator_metadata = {str(rec["id"]): rec for rec in json.load(f)}

    def get_true_level2(indicator):
        cur = indicator_metadata.get(str(indicator.get("indicator_id")))
        while cur:
            if cur.get("nivel") == "2":
                return cur.get("nome")
            parent_id = cur.get("indicador_pai")
            if not parent_id or parent_id == cur["id"] or parent_id not in indicator_metadata:
                break
            cur = indicator_metadata.get(str(parent_id))
        return "-"

    grouped = defaultdict(list)
    for ind in problematic_indicators:
        sector = ind.get("setor_estrategico", "-")
        level2 = get_true_level2(ind)
        grouped[(sector, level2)].append(ind)

    narrative_groups = []
    current_risk = 0.35
    projected_risk = 0.55
    print(f"Generating grouped climate narrative for {city_name} (ID: {city_id}) with {len(problematic_indicators)} problematic indicators")

    for (sector, level2), indicators in grouped.items():
        group_components = []
        # Risk Drivers
        risk_drivers_to_process = [ind for ind in indicators if "vulnerabilidade" in ind["indicator_name:"].lower() or "capacidade adaptativa" in ind["indicator_name:"].lower()]
        for indicator in risk_drivers_to_process:
            driver_prompt = get_risk_driver_prompt(indicator)
            driver_data = generate_llm_response(driver_prompt, config, "risk_driver")
            if driver_data:
                try:
                    comp = NarrativeComponent(**driver_data)
                    comp.supporting_indicators = [
                        {
                            "indicator_id": indicator.get("indicator_id"),
                            "indicator_name": indicator.get("indicator_name:"),
                            "setor_estrategico": indicator.get("setor_estrategico"),
                            "level2_indicator": level2,
                            "anos": indicator.get("anos"),
                            "rangelabel": indicator.get("rangelabel"),
                            "value": indicator.get("value"),
                            "future_trends": indicator.get("future_trends", {})
                        }
                    ]
                    group_components.append(comp)
                    print(f"Added risk driver component: {driver_data.get('title')} for sector {sector}, level2 {level2}")
                except Exception as e:
                    print(f"Error parsing risk driver component: {e} Data: {driver_data}")
        # Impacts
        impacts_to_process = [ind for ind in indicators if "seca" in ind["indicator_name:"].lower() or "precipitação" in ind["indicator_name:"].lower()]
        for indicator in impacts_to_process:
            impact_prompt = get_impact_item_prompt(indicator)
            impact_data = generate_llm_response(impact_prompt, config, "impact_item")
            if impact_data:
                try:
                    comp = NarrativeComponent(**impact_data)
                    comp.supporting_indicators = [
                        {
                            "indicator_id": indicator.get("indicator_id"),
                            "indicator_name": indicator.get("indicator_name:"),
                            "setor_estrategico": indicator.get("setor_estrategico"),
                            "level2_indicator": level2,
                            "anos": indicator.get("anos"),
                            "rangelabel": indicator.get("rangelabel"),
                            "value": indicator.get("value"),
                            "future_trends": indicator.get("future_trends", {})
                        }
                    ]
                    group_components.append(comp)
                    print(f"Added impact item component: {impact_data.get('title')} for sector {sector}, level2 {level2}")
                except Exception as e:
                    print(f"Error parsing impact item component: {e} Data: {impact_data}")
        # Only add group if it has components
        if group_components:
            narrative_groups.append({
                "setor_estrategico": sector,
                "level2_indicator": level2,
                "components": group_components
            })

    # Daily Life Implications (global, not grouped)
    narrative_components = []
    for group in narrative_groups:
        narrative_components.extend(group["components"])

    if problematic_indicators:
        implications_summary = ", ".join([ind["indicator_name:"].replace("\n", " ") for ind in problematic_indicators])
        implications_prompt = get_daily_implications_prompt(implications_summary)
        implications_data = generate_llm_response(implications_prompt, config, "daily_implications")
        if implications_data:
            try:
                comp = NarrativeComponent(**implications_data)
                # Do not add supporting_indicators for daily_implications
                narrative_components.append(comp)
                print(f"Added daily implications component.")
            except Exception as e:
                print(f"Error parsing daily implications component: {e} Data: {implications_data}")
    # Solutions (global, not grouped)
    if problematic_indicators:
        solutions_prompt = get_solutions_prompt(implications_summary)
        solutions_data = generate_llm_response(solutions_prompt, config, "solutions")
        if solutions_data:
            try:
                comp = NarrativeComponent(**solutions_data)
                # Do not add supporting_indicators for solutions
                narrative_components.append(comp)
                print(f"Added solutions component.")
            except Exception as e:
                print(f"Error parsing solutions component: {e} Data: {solutions_data}")
    # Conclusion (optional, not requested)
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


