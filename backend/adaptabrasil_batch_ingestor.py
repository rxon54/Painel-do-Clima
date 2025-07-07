"""
AdaptaBrasil Batch API Ingestor

Fetches climate indicator data for Brazilian municipalities from the AdaptaBrasil API in batch mode, as configured in config.yaml.

Usage:
    python adaptabrasil_batch_ingestor.py

- Reads parameters from config.yaml (state, year, cities, L2 indicators, delay, output dir, debug).
- For each city and each Level 2 indicator, fetches all sublevel indicator values and saves as one file per city per L2 indicator (including all sublevels).
- Adds a delay between requests (default: 1s, configurable).
- Optionally saves full API responses for debugging.
- Output: JSON files in the specified output directory.

Expected config.yaml structure:
    state: "PR"
    year: 2022
    cities: ["4106902", "4104808"]
    l2_indicators: ["6000", "7000"]
    delay: 1.0
    output_dir: "output/"
    debug: false

"""
import os
import time
import json
import yaml
import requests
import logging
from typing import List, Dict, Any

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

def fetch_indicators(state: str, indicator_id: str, year: int) -> Any:   
    """
    Fetches all cities' values for a given indicator_id in a state/year.
    """
    url = f"https://sistema.adaptabrasil.mcti.gov.br/api/mapa-dados/{state}/municipio/{indicator_id}/{year}/null/adaptabrasil"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

# fetch future trends for a given indicator_id in a state/year
def fetch_future_trends(state: str, indicator_id: str, year: int) -> Any:
    """
    Fetches future trends for a given indicator_id in a state/year.
    """
    url = f"https://sistema.adaptabrasil.mcti.gov.br/api/total/{state}/municipio/{indicator_id}/null/{year}"
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
    state = config["state"]
    delay = float(config.get("delay", 1.0))
    output_dir = config.get("output_dir", "output/")
    debug = config.get("debug", False)

    ensure_dir(output_dir)

    # Load indicator_id/year pairs from mapa-dados.txt (present)
    indicators = load_indicator_year_pairs(config.get("mapa_dados_file", "mapa-dados.txt"))

    success, fail = 0, 0
    for indicator_id, year in indicators:
        log_ctx = f"mapa-dados request: state={state}, L2={indicator_id}, year={year}"
        print(f"Fetching {log_ctx}")
        ab_response = fetch_with_retries(fetch_indicators, state, indicator_id, year, log_context=log_ctx)
        if ab_response is not None:
            summary_path = os.path.join(output_dir, f"mapa-dados_{state}_{indicator_id}_{year}.json")
            save_json(ab_response, summary_path)
            if debug:
                debug_path = os.path.join(output_dir, f"mapa-dados_{state}_{indicator_id}_{year}_raw.json")
                save_json(ab_response, debug_path)
            success += 1
        else:
            fail += 1
        time.sleep(delay)

    # Load indicator_id/year pairs from trends file (future trends)
    trends_file = config.get("trends_file", "trends-2030-2050.txt")
    try:
        indicators = load_indicator_year_pairs(trends_file)
    except FileNotFoundError:
        logging.warning(f"Trends file '{trends_file}' not found. Skipping future trends batch.")
        indicators = []

    # Fetch future trends for each indicator
    if indicators:
        logging.info("=== Fetching Future Trends ===")
        for indicator_id, year in indicators:
            log_ctx = f"future trends request: state={state}, L2={indicator_id}, year={year}"
            print(f"Fetching {log_ctx}")
            future_response = fetch_with_retries(fetch_future_trends, state, indicator_id, year, log_context=log_ctx)
            if future_response is not None:
                future_path = os.path.join(output_dir, f"future_trends_{state}_{indicator_id}_{year}.json")
                save_json(future_response, future_path)
                if debug:
                    debug_path = os.path.join(output_dir, f"future_trends_{state}_{indicator_id}_{year}_raw.json")
                    save_json(future_response, debug_path)
                success += 1
            else:
                fail += 1
            time.sleep(delay)
    else:
        logging.info("No future trends to process.")
    logging.info(f"=== Batch Ingestor Finished: {success} indicators processed with success, {fail} failures ===")

if __name__ == "__main__":
    main()
