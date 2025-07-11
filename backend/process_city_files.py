import os
import json
import glob

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(obj, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def main():
    # Use data_dir relative to the script location (backend/data)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, '../data')
    indicator_files = glob.glob(os.path.join(data_dir, 'mapa-dados_*.json'))
    future_trend_files = glob.glob(os.path.join(data_dir, 'future_trends_*.json'))
    state_city_map = {}  # {state_code: {city_code: {"id":..., "name":..., "indicators": [...]}}}
    city_filelist = {}

    # Load present indicator data
    for ind_file in indicator_files:
        base = os.path.basename(ind_file)
        parts = base.split('_')
        if len(parts) < 3:
            continue
        state_code = parts[1]
        records = load_json(ind_file)
        for rec in records:
            city_code = str(rec.get("id"))
            if not city_code:
                continue
            if state_code not in state_city_map:
                state_city_map[state_code] = {}
            if city_code not in state_city_map[state_code]:
                state_city_map[state_code][city_code] = {
                    "id": rec.get("id"),
                    "name": rec.get("name") or rec.get("nome") or city_code,
                    "indicators": []
                }
            # Prepare indicator entry (copy all fields except id/name/nome)
            indicator_entry = {k: v for k, v in rec.items() if k not in ("id", "name", "nome")}
            indicator_entry["indicator_id"] = rec.get("indicator_id") or rec.get("indicador_id") or rec.get("indicador")
            indicator_entry["year"] = rec.get("year") or rec.get("ano")
            indicator_entry["future_trends"] = {}  # will be filled later
            state_city_map[state_code][city_code]["indicators"].append(indicator_entry)

    # Build a lookup for future trends: {(state, city, indicator_id): {year: {scenario: {value, valuecolor, valuelabel}}}}
    future_lookup = {}  # (state_code, city_code, indicator_id, year, scenario) -> {value, valuecolor, valuelabel}
    for ft_file in future_trend_files:
        base = os.path.basename(ft_file)
        parts = base.split('_')
        if len(parts) < 5:
            continue
        state_code = parts[2]
        indicator_id = parts[3]
        year_part = parts[4]
        year = year_part.split('.')[0]
        ft_json = load_json(ft_file)
        if year in ft_json:
            for scenario, scenario_obj in ft_json[year].items():
                if not isinstance(scenario_obj, dict) or "data" not in scenario_obj:
                    continue
                valuecolor = scenario_obj.get("valuecolor")
                valuelabel = scenario_obj.get("valuelabel")
                for rec in scenario_obj["data"]:
                    city_code = str(rec.get("id"))
                    value = rec.get("value")
                    if not city_code or value is None:
                        continue
                    key = (state_code, city_code, indicator_id, year, scenario)
                    future_lookup[key] = {
                        "value": value,
                        "valuecolor": valuecolor,
                        "valuelabel": valuelabel
                    }

    # Merge future trends into each indicator entry
    for state_code, city_map in state_city_map.items():
        for city_code, city_data in city_map.items():
            for indicator in city_data["indicators"]:
                ind_id = str(indicator.get("indicator_id"))
                for fut_year in ["2030", "2050"]:
                    # Try all scenarios for this indicator/city/year
                    for scenario in ["verylow", "low", "mid", "high", "veryhigh"]:
                        key = (state_code, city_code, ind_id, fut_year, scenario)
                        if key in future_lookup:
                            indicator["future_trends"][fut_year] = future_lookup[key]
                            break  # Use the first scenario found (or adjust as needed)

    # Write one file per city, in a folder named after the state code
    for state_code, city_map in state_city_map.items():
        out_dir = os.path.join(data_dir, state_code)
        os.makedirs(out_dir, exist_ok=True)
        for city_code, city_data in city_map.items():
            out_path = os.path.join(out_dir, f"city_{city_code}.json")
            save_json(city_data, out_path)
            city_filelist[city_code] = {
                "name": city_data["name"],
                "state": state_code,
                "file": f"{state_code}/city_{city_code}.json"
            }

    # Sort city_filelist by city name (alphabetically, case-insensitive)
    # sorted_city_filelist = dict(sorted(city_filelist.items(), key=lambda item: (item[1]["name"].lower(), item[0])))
    save_json(city_filelist, os.path.join(data_dir, "city_filelist.json"))
    print(f"Wrote city files to {data_dir}/<STATE>/city_<city_code>.json and city_filelist.json for {len(city_filelist)} cities, including future trends.")

    # Move processed files to data/downloads
    downloads_dir = os.path.join(data_dir, 'downloads')
    os.makedirs(downloads_dir, exist_ok=True)
    for f in indicator_files + future_trend_files:
        try:
            basename = os.path.basename(f)
            dest = os.path.join(downloads_dir, basename)
            os.rename(f, dest)
        except Exception as e:
            print(f"Warning: could not move {f} to downloads: {e}")

if __name__ == "__main__":
    main()
