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
    data_dir = "data"
    # Find all indicator files (e.g., mapa-dados_*.json)
    indicator_files = glob.glob(os.path.join(data_dir, 'mapa-dados_*.json'))
    state_city_map = {}  # {state_code: {city_code: {...}}}
    city_filelist = {}   # {city_code: {name, state, file}}

    for ind_file in indicator_files:
        base = os.path.basename(ind_file)
        # Extract state code from filename: mapa-dados_<STATE>_...
        parts = base.split('_')
        if len(parts) < 3:
            continue
        state_code = parts[1]
        if state_code not in state_city_map:
            state_city_map[state_code] = {}
        records = load_json(ind_file)
        for rec in records:
            city_code = str(rec.get("id"))  # Use 'id' as city_code
            if not city_code:
                continue
            if city_code not in state_city_map[state_code]:
                state_city_map[state_code][city_code] = {
                    "name": rec.get("name") or rec.get("nome") or city_code,
                    "indicators": []
                }
            state_city_map[state_code][city_code]["indicators"].append(rec)

    # Write one file per city, in a folder named after the state code
    for state_code, city_map in state_city_map.items():
        out_dir = os.path.join(data_dir, state_code)
        os.makedirs(out_dir, exist_ok=True)
        for city_code, city_data in city_map.items():
            out_path = os.path.join(out_dir, f"city_{city_code}.json")
            save_json(city_data, out_path)
            # Add to city_filelist for frontend
            city_filelist[city_code] = {
                "name": city_data["name"],
                "state": state_code,
                "file": f"{state_code}/city_{city_code}.json"
            }

    # Save city_filelist.json for frontend
    save_json(city_filelist, os.path.join(data_dir, "city_filelist.json"))
    print(f"Wrote city files to {data_dir}/<STATE>/city_<city_code>.json and city_filelist.json for {len(city_filelist)} cities.")

if __name__ == "__main__":
    main()
