"""
AdaptaBrasil Batch API Ingestor

Fetches climate indicator data for Brazilian municipalities from the AdaptaBrasil API in batch mode, as configured in config.yaml.

Usage:
    python adaptabrasil_batch_ingestor.py

- Reads parameters from config.yaml (states, delay, output dir, debug).
- Supports single state (state: "PR") or multiple states (state: "RS, SP, RJ").
- For each state and each indicator/year pair, fetches data from both mapa-dados and future trends APIs.
- Adds a delay between requests (configurable via delay_seconds).
- Optionally saves full API responses for debugging.
- Output: JSON files in the specified output directory with state-specific naming.

Expected config.yaml structure:
    state: "PR"  # Single state
    # OR
    state: "RS, SP, RJ"  # Multiple states (comma-separated)
    delay_seconds: 2.0
    output_dir: "../data/"
    save_full_response: true
    mapa_dados_file: "mapa-dados.txt"
    trends_file: "trends-2030-2050.txt"

"""
import os
import time
import json
import yaml
import requests
import logging
from typing import List, Dict, Any

def print_progress_bar(current: int, total: int, length: int = 50, prefix: str = "Progress"):
    """Print a progress bar to console"""
    if total == 0:
        return
    percent = current / total
    filled_length = int(length * percent)
    bar = '█' * filled_length + '░' * (length - filled_length)
    print(f'\r{prefix}: |{bar}| {current}/{total} ({percent:.1%})', end='', flush=True)

# Setup logging
logging.basicConfig(
    filename="batch_ingestor.log",
    filemode="a",
    format="%(asctime)s %(levelname)s: %(message)s",
    level=logging.INFO
)

def load_config(path: str = "../config.yaml") -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def fetch_indicators(state: str, indicator_id: str, year: int, resolution: str = "municipio") -> Any:
    """
    Fetches all entities' values for a given indicator_id in a state/year for specified resolution.
    """
    url = f"https://sistema.adaptabrasil.mcti.gov.br/api/mapa-dados/{state}/{resolution}/{indicator_id}/{year}/null/adaptabrasil"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

# fetch future trends for a given indicator_id in a state/year
def fetch_future_trends(state: str, indicator_id: str, year: int, resolution: str = "municipio") -> Any:
    """
    Fetches future trends for a given indicator_id in a state/year for specified resolution.
    """
    url = f"https://sistema.adaptabrasil.mcti.gov.br/api/total/{state}/{resolution}/{indicator_id}/null/{year}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()



def save_json(data: Any, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def fetch_with_retries(fetch_fn, *args, max_retries=3, backoff=2, log_context=None, **kwargs):
    attempt = 0
    while attempt < max_retries:
        try:
            result = fetch_fn(*args, **kwargs)
            if log_context:
                logging.info(f"SUCCESS: {log_context} (attempt {attempt+1})")
            return result
        except Exception as e:
            attempt += 1
            wait = backoff ** attempt
            msg = f"Attempt {attempt} failed: {e}. Retrying in {wait}s... Context: {log_context}"
            print(msg)
            logging.warning(msg)
            time.sleep(wait)
    fail_msg = f"FAILED after {max_retries} attempts. Context: {log_context}"
    print(fail_msg)
    logging.error(fail_msg)
    return None

def parse_states(state_config: str) -> List[str]:
    """
    Parse state configuration to handle both single state and comma-separated states.
    
    Args:
        state_config: State configuration from config.yaml (e.g., "PR" or "RS, SP, RJ")
        
    Returns:
        List of state codes
    """
    if isinstance(state_config, str):
        # Handle comma-separated states
        states = [state.strip().upper() for state in state_config.split(',')]
        return [state for state in states if state]  # Filter out empty strings
    elif isinstance(state_config, list):
        # Handle list format
        return [str(state).strip().upper() for state in state_config]
    else:
        # Single state
        return [str(state_config).strip().upper()]

def load_indicator_year_pairs(path: str = "mapa-dados.txt"):
    """
    Loads indicator_id/year pairs from mapa-dados.txt, skipping comments and blank lines.
    Returns a list of (indicator_id, year) tuples.
    """
    pairs = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "/" in line:
                indicator_id, year = line.split("/")
                pairs.append((indicator_id.strip(), int(year.strip())))
    return pairs

def main():
    logging.info("=== Batch Ingestor Started ===")
    config = load_config()
    states = parse_states(config["state"])
    resolution = config.get("resolution", "municipio")  # Get resolution from config
    delay = float(config.get("delay_seconds", config.get("delay", 1.0)))  # Support both delay_seconds and delay
    output_dir = config.get("output_dir", "output/")
    debug = config.get("save_full_response", config.get("debug", False))  # Support both save_full_response and debug

    ensure_dir(output_dir)
    
    # Determine if we need a special folder structure for supra-state resolutions
    is_regional_resolution = resolution == "regiao"
    if is_regional_resolution:
        # For regional data, create a BR (Brasil) folder
        br_output_dir = os.path.join(output_dir, "BR")
        ensure_dir(br_output_dir)
        effective_output_dir = br_output_dir
        # For regional resolution, we'll still process by state but save in BR folder
        logging.info(f"Using regional resolution '{resolution}' - files will be saved in BR/ folder")
    else:
        effective_output_dir = output_dir
        logging.info(f"Using intra-state resolution '{resolution}' - files will be saved by state")
    
    # Calculate total workload for progress tracking
    mapa_dados_indicators = load_indicator_year_pairs(config.get("mapa_dados_file", "mapa-dados.txt"))
    try:
        trends_indicators = load_indicator_year_pairs(config.get("trends_file", "trends-2030-2050.txt"))
    except FileNotFoundError:
        trends_indicators = []
    
    indicators_per_state = len(mapa_dados_indicators) + len(trends_indicators)
    total_requests = len(states) * indicators_per_state
    
    print(f"\n🌍 AdaptaBrasil Batch Ingestor")
    print(f"═" * 50)
    print(f"📍 States to process: {len(states)} ({', '.join(states)})")
    print(f"🎯 Resolution: {resolution}")  # Show current resolution
    print(f"� Output directory: {effective_output_dir}")
    if is_regional_resolution:
        print(f"🌎 Regional resolution detected - using BR/ folder structure")
    print(f"�📊 Present indicators per state: {len(mapa_dados_indicators)}")
    print(f"🔮 Future trend indicators per state: {len(trends_indicators)}")
    print(f"📈 Total indicators per state: {indicators_per_state}")
    print(f"🎯 Total API requests: {total_requests}")
    print(f"⏱️  Estimated time: ~{(total_requests * delay) / 60:.1f} minutes")
    print(f"═" * 50)
    
    logging.info(f"Processing {len(states)} state(s): {', '.join(states)}")
    logging.info(f"Total requests to be made: {total_requests}")

    total_success, total_fail = 0, 0
    global_progress = 0

    # Process each state
    for state_idx, state in enumerate(states):
        logging.info(f"=== Processing State: {state} ===")
        print(f"\n\n🏛️  State {state_idx + 1}/{len(states)}: {state}")
        print(f"─" * 30)
        
        # Load indicator_id/year pairs from mapa-dados.txt (present)
        indicators = load_indicator_year_pairs(config.get("mapa_dados_file", "mapa-dados.txt"))
        
        success, fail = 0, 0
        state_progress = 0
        state_total = len(indicators)
        
        print(f"📊 Processing {len(indicators)} present indicators...")
        for i, (indicator_id, year) in enumerate(indicators):
            log_ctx = f"mapa-dados request: state={state}, L2={indicator_id}, year={year}"
            
            # Update progress bars
            state_progress += 1
            global_progress += 1
            print_progress_bar(state_progress, indicators_per_state, prefix=f"  State {state}")
            print(f" | {indicator_id}/{year}")
            print_progress_bar(global_progress, total_requests, prefix="  Overall")
            
            ab_response = fetch_with_retries(fetch_indicators, state, indicator_id, year, resolution, log_context=log_ctx)
            if ab_response is not None:
                summary_path = os.path.join(effective_output_dir, f"mapa-dados_{resolution}_{state}_{indicator_id}_{year}.json")
                save_json(ab_response, summary_path)
                if debug:
                    debug_path = os.path.join(effective_output_dir, f"mapa-dados_{resolution}_{state}_{indicator_id}_{year}_raw.json")
                    save_json(ab_response, debug_path)
                success += 1
            else:
                fail += 1
            time.sleep(delay)

        # Load indicator_id/year pairs from trends file (future trends)
        trends_file = config.get("trends_file", "trends-2030-2050.txt")
        try:
            trends_indicators = load_indicator_year_pairs(trends_file)
        except FileNotFoundError:
            logging.warning(f"Trends file '{trends_file}' not found. Skipping future trends batch for state {state}.")
            trends_indicators = []

        # Fetch future trends for each indicator
        if trends_indicators:
            print(f"\n🔮 Processing {len(trends_indicators)} future trend indicators...")
            logging.info(f"=== Fetching Future Trends for State: {state} ===")
            for i, (indicator_id, year) in enumerate(trends_indicators):
                log_ctx = f"future trends request: state={state}, L2={indicator_id}, year={year}"
                
                # Update progress bars
                state_progress += 1
                global_progress += 1
                print_progress_bar(state_progress, indicators_per_state, prefix=f"  State {state}")
                print(f" | {indicator_id}/{year}")
                print_progress_bar(global_progress, total_requests, prefix="  Overall")
                
                future_response = fetch_with_retries(fetch_future_trends, state, indicator_id, year, resolution, log_context=log_ctx)
                if future_response is not None:
                    future_path = os.path.join(effective_output_dir, f"future_trends_{resolution}_{state}_{indicator_id}_{year}.json")
                    save_json(future_response, future_path)
                    if debug:
                        debug_path = os.path.join(effective_output_dir, f"future_trends_{resolution}_{state}_{indicator_id}_{year}_raw.json")
                        save_json(future_response, debug_path)
                    success += 1
                else:
                    fail += 1
                time.sleep(delay)
        else:
            logging.info(f"No future trends to process for state {state}.")
        
        # State completion summary
        print(f"\n✅ State {state} completed: {success} success, {fail} failures")
        logging.info(f"=== State {state} Finished: {success} indicators processed with success, {fail} failures ===")
        total_success += success
        total_fail += fail

    # Final summary
    print(f"\n\n🎉 BATCH PROCESSING COMPLETE!")
    print(f"═" * 50)
    print(f"🌍 States processed: {len(states)} ({', '.join(states)})")
    print(f"✅ Total successful requests: {total_success}")
    print(f"❌ Total failed requests: {total_fail}")
    print(f"📊 Success rate: {(total_success / (total_success + total_fail) * 100):.1f}%" if (total_success + total_fail) > 0 else "No requests made")
    print(f"⏱️  Total requests made: {total_success + total_fail}")
    print(f"═" * 50)
    
    logging.info(f"=== Batch Ingestor Finished: {total_success} total indicators processed with success, {total_fail} total failures across {len(states)} state(s) ===")
    print(f"\n=== Final Summary ===")
    print(f"States processed: {', '.join(states)}")
    print(f"Total success: {total_success}")
    print(f"Total failures: {total_fail}")

if __name__ == "__main__":
    main()
