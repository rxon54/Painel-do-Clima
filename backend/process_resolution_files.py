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
    
    # Updated file patterns to handle resolution-aware filenames
    # Pattern: mapa-dados_{resolution}_{state}_{indicator}_{year}.json
    indicator_files = glob.glob(os.path.join(data_dir, 'mapa-dados_*_*.json'))
    future_trend_files = glob.glob(os.path.join(data_dir, 'future_trends_*_*.json'))
    
    # Multi-resolution entity map: {resolution: {state_code: {entity_code: {"id":..., "name":..., "indicators": [...]}}}}
    resolution_entity_map = {}  
    entity_filelist = {}  # Will be organized by resolution
    
    # Resolution-specific entity naming
    resolution_names = {
        'municipio': 'city',
        'microrregiao': 'microregion', 
        'mesorregiao': 'mesoregion',
        'estado': 'state',
        'regiao': 'region'
    }
    

    print(f"Starting entity file processing...")
    print(f"Found {len(indicator_files)} indicator files and {len(future_trend_files)} future trend files")

    # Load present indicator data with resolution detection
    print("\n📊 Loading present indicator data...")
    for i, ind_file in enumerate(indicator_files):
        base = os.path.basename(ind_file)
        parts = base.split('_')
        if len(parts) < 4:  # Expecting: mapa-dados_{resolution}_{state}_{indicator}_{year}.json
            print(f"  Skipping file with unexpected format: {base}")
            continue
            
        resolution = parts[1]  # mesorregiao, municipio, etc.
        state_code = parts[2]
        
        print(f"  Processing {resolution} file {i+1}/{len(indicator_files)}: {base}")
        records = load_json(ind_file)
        entities_in_file = 0
        
        # Initialize resolution structure if not exists
        if resolution not in resolution_entity_map:
            resolution_entity_map[resolution] = {}
            
        for rec in records:
            entity_id = str(rec.get("id"))
            if not entity_id:
                continue
            entities_in_file += 1
            
            if state_code not in resolution_entity_map[resolution]:
                resolution_entity_map[resolution][state_code] = {}
                
            if entity_id not in resolution_entity_map[resolution][state_code]:
                resolution_entity_map[resolution][state_code][entity_id] = {
                    "id": rec.get("id"),
                    "name": rec.get("name") or rec.get("nome") or entity_id,
                    "geocod_ibge": rec.get("geocod_ibge"),  # Store IBGE code
                    "indicators": []
                }
            
            # Prepare indicator entry (copy all fields except id/name/nome)
            indicator_entry = {k: v for k, v in rec.items() if k not in ("id", "name", "nome")}
            indicator_entry["indicator_id"] = rec.get("indicator_id") or rec.get("indicador_id") or rec.get("indicador")
            indicator_entry["year"] = rec.get("year") or rec.get("ano")
            indicator_entry["future_trends"] = {}  # will be filled later
            resolution_entity_map[resolution][state_code][entity_id]["indicators"].append(indicator_entry)
            
        print(f"    → Processed {entities_in_file} {resolution_names.get(resolution, resolution)} entities in state {state_code}")

    # Build a lookup for future trends: {(resolution, state, entity, indicator_id): {year: {scenario: {value, valuecolor, valuelabel}}}}
    print("\n🔮 Building future trends lookup...")
    future_lookup = {}  # (resolution, state_code, entity_code, indicator_id, year, scenario) -> {value, valuecolor, valuelabel}
    for i, ft_file in enumerate(future_trend_files):
        base = os.path.basename(ft_file)
        if i % 50 == 0:  # Show progress every 50 files
            print(f"  Processing future trends file {i+1}/{len(future_trend_files)}: {base}")
        parts = base.split('_')
        if len(parts) < 5:  # Expecting: future_trends_{resolution}_{state}_{indicator}_{year}.json
            continue
            
        resolution = parts[2]
        state_code = parts[3]
        indicator_id = parts[4]
        year_part = parts[5]
        year = year_part.split('.')[0]
        
        ft_json = load_json(ft_file)
        if year in ft_json:
            for scenario, scenario_obj in ft_json[year].items():
                if not isinstance(scenario_obj, dict) or "data" not in scenario_obj:
                    continue
                valuecolor = scenario_obj.get("valuecolor")
                valuelabel = scenario_obj.get("valuelabel")
                for rec in scenario_obj["data"]:
                    entity_code = str(rec.get("id"))
                    value = rec.get("value")
                    if not entity_code or value is None:
                        continue
                    key = (resolution, state_code, entity_code, indicator_id, year, scenario)
                    future_lookup[key] = {
                        "value": value,
                        "valuecolor": valuecolor,
                        "valuelabel": valuelabel
                    }

    # Merge future trends into each indicator entry
    print("\n🔗 Merging future trends with present indicators...")
    total_entities = sum(sum(len(entity_map) for entity_map in resolution_data.values()) 
                        for resolution_data in resolution_entity_map.values())
    entities_processed = 0
    
    for resolution, resolution_data in resolution_entity_map.items():
        print(f"  Processing {resolution} resolution...")
        for state_code, entity_map in resolution_data.items():
            print(f"    State {state_code} ({len(entity_map)} {resolution_names.get(resolution, resolution)} entities)...")
            for entity_code, entity_data in entity_map.items():
                entities_processed += 1
                if entities_processed % 500 == 0:  # Show progress every 500 entities
                    print(f"      → Processed {entities_processed}/{total_entities} entities ({entities_processed/total_entities*100:.1f}%)")
                
                for indicator in entity_data["indicators"]:
                    ind_id = str(indicator.get("indicator_id"))
                    for fut_year in ["2030", "2050"]:
                        # Try all scenarios for this indicator/entity/year
                        for scenario in ["verylow", "low", "mid", "high", "veryhigh"]:
                            key = (resolution, state_code, entity_code, ind_id, fut_year, scenario)
                            if key in future_lookup:
                                indicator["future_trends"][fut_year] = future_lookup[key]
                                break  # Use the first scenario found (or adjust as needed)

    # Write entity files organized by resolution and state
    print("\n💾 Writing entity files...")
    total_entities_to_write = sum(sum(len(entity_map) for entity_map in resolution_data.values()) 
                                 for resolution_data in resolution_entity_map.values())
    entities_written = 0
    
    for resolution, resolution_data in resolution_entity_map.items():
        entity_type = resolution_names.get(resolution, resolution)
        print(f"  Writing {entity_type} files...")
        
        # Initialize filelist for this resolution
        if resolution not in entity_filelist:
            entity_filelist[resolution] = {}
        
        for state_code, entity_map in resolution_data.items():
            # Create output directory: data/{STATE}/ or data/BR/ for regional data
            if resolution == 'regiao':
                out_dir = os.path.join(data_dir, 'BR')  # Regional data goes to BR folder
            else:
                out_dir = os.path.join(data_dir, state_code)  # State-specific data
                
            os.makedirs(out_dir, exist_ok=True)
            print(f"    Writing {len(entity_map)} {entity_type} entities for state {state_code} to {out_dir}...")
            
            for entity_code, entity_data in entity_map.items():
                entities_written += 1
                
                # Use IBGE geocode if available, otherwise use entity ID
                geocode = entity_data.get("geocod_ibge", entity_code)
                out_filename = f"{entity_type}_{geocode}.json"
                out_path = os.path.join(out_dir, out_filename)
                
                save_json(entity_data, out_path)
                
                # Build filelist entry
                relative_path = f"{state_code}/{out_filename}" if resolution != 'regiao' else f"BR/{out_filename}"
                entity_filelist[resolution][entity_code] = {
                    "name": entity_data["name"],
                    "state": state_code,
                    "file": relative_path,
                    "geocod_ibge": geocode,
                    "resolution": resolution
                }
                
                if entities_written % 1000 == 0:  # Show progress every 1000 entities
                    print(f"      → Written {entities_written}/{total_entities_to_write} entity files ({entities_written/total_entities_to_write*100:.1f}%)")

    # Write resolution-aware filelist
    print("\n📋 Writing entity filelist...")
    save_json(entity_filelist, os.path.join(data_dir, "entity_filelist.json"))
    
    total_entities_processed = sum(len(resolution_data) for resolution_data in entity_filelist.values())
    total_resolutions = len(resolution_entity_map)
    print(f"✅ Successfully processed {total_entities_processed} entities across {total_resolutions} resolutions")

    # Move processed files to data/downloads
    print("\n📦 Moving processed files to downloads folder...")
    downloads_dir = os.path.join(data_dir, 'downloads')
    os.makedirs(downloads_dir, exist_ok=True)
    moved_files = 0
    total_files = len(indicator_files) + len(future_trend_files)
    
    for f in indicator_files + future_trend_files:
        try:
            basename = os.path.basename(f)
            dest = os.path.join(downloads_dir, basename)
            os.rename(f, dest)
            moved_files += 1
        except Exception as e:
            print(f"Warning: could not move {f} to downloads: {e}")
    
    print(f"📁 Moved {moved_files}/{total_files} files to downloads folder")
    print(f"\n🎉 Processing complete! Entity files written to:")
    print(f"   • Regular resolutions: {data_dir}/<STATE>/{entity_type}_<geocode>.json")
    print(f"   • Regional resolution: {data_dir}/BR/{entity_type}_<geocode>.json")
    print(f"   • Entity filelist: {data_dir}/entity_filelist.json")

if __name__ == "__main__":
    main()
