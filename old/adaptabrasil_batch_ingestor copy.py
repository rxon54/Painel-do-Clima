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

def load_config(path: str = "config.yaml") -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def fetch_l2_summary(state: str, l2_code: str, year: int) -> Any:
    """
    Fetches all cities' values for a given L2 indicator in a state/year.
    """
    url = f"https://sistema.adaptabrasil.mcti.gov.br/api/mapa-dados/{state}/municipio/{l2_code}/{year}/null/adaptabrasil"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def fetch_city_l2_details(l2_code: str, city_code: str, year: int) -> Any:
    """
    Fetches all sublevel indicators for a city under a given L2 indicator.
    """
    url = f"https://sistema.adaptabrasil.mcti.gov.br/api/info/BR/municipio/{l2_code}/{city_code}/2015/null"
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

def main():
    logging.info("=== Batch Ingestor Started ===")
    config = load_config()
    state = config["state"]
    year = config["year"]
    cities = config["cities"]
    l2_indicators = config["l2_indicators"]
    delay = float(config.get("delay", 1.0))
    output_dir = config.get("output_dir", "output/")
    debug = config.get("debug", False)

    ensure_dir(output_dir)

    # 1. Fetch and save L2 summary for each L2 indicator
    l2_success, l2_fail = 0, 0
    for l2_code in l2_indicators:
        log_ctx = f"L2 summary: state={state}, L2={l2_code}, year={year}"
        print(f"Fetching {log_ctx}")
        l2_summary = fetch_with_retries(fetch_l2_summary, state, l2_code, year, log_context=log_ctx)
        if l2_summary is not None:
            summary_path = os.path.join(output_dir, f"{state}_L2_{l2_code}_{year}_summary.json")
            save_json(l2_summary, summary_path)
            if debug:
                debug_path = os.path.join(output_dir, f"{state}_L2_{l2_code}_{year}_summary_raw.json")
                save_json(l2_summary, debug_path)
            l2_success += 1
        else:
            l2_fail += 1
        time.sleep(delay)

    # 2. Fetch and save per-city L2 details
    city_success, city_fail = 0, 0
    for city in cities:
        for l2_code in l2_indicators:
            log_ctx = f"City details: city={city}, L2={l2_code}, year={year}"
            print(f"Fetching {log_ctx}")
            city_l2_details = fetch_with_retries(fetch_city_l2_details, l2_code, city, year, log_context=log_ctx)
            if city_l2_details is not None:
                out_path = os.path.join(output_dir, f"{city}_L2_{l2_code}_{year}.json")
                save_json(city_l2_details, out_path)
                if debug:
                    debug_path = os.path.join(output_dir, f"{city}_L2_{l2_code}_{year}_raw.json")
                    save_json(city_l2_details, debug_path)
                city_success += 1
            else:
                city_fail += 1
            time.sleep(delay)
    
    # Write filelist.json for all *_L2_*.json in data/
    import glob
    data_dir = "data"
    filelist_path = os.path.join(data_dir, "filelist.json")
    os.makedirs(data_dir, exist_ok=True)
    filelist = [os.path.basename(f) for f in glob.glob(os.path.join(data_dir, "*_L2_*.json"))]
    with open(filelist_path, "w", encoding="utf-8") as f:
        json.dump(sorted(filelist), f, ensure_ascii=False, indent=2)
    logging.info(f"Wrote filelist.json with {len(filelist)} files to {filelist_path}")
    logging.info(f"=== Batch Ingestor Finished: L2 success={l2_success}, L2 fail={l2_fail}, City success={city_success}, City fail={city_fail} ===")

if __name__ == "__main__":
    main()
