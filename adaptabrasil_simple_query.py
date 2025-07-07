import requests
import json


# This query shows evolutions and tendencies for all cities of PR for the year 2015.
# Values come in 5 groups: very low, low, mid, high, very high
#API_URL = "https://sistema.adaptabrasil.mcti.gov.br/api/total/PR/municipio/1000/2022/null"

# THis query is for the Level 1 of the hierarchy (1000)
# it filters the indicators for the state of Paraná (PR) for the year 2015, granularity at the municipality level
#API_URL="https://sistema.adaptabrasil.mcti.gov.br/api/mapa-dados/PR/municipio/1000/2015/null/adaptabrasil" 

# This query brings the values for all the indicators for the given L1 (1000)
# it filters the indicators for the city of Ponta Grossa (5387), for the year 2022
#API_URL = "https://sistema.adaptabrasil.mcti.gov.br/api/info/BR/municipio/1000/5387/2022/null"

API_URL = "https://sistema.adaptabrasil.mcti.gov.br/api/info/BR/municipio/60100/5329/2018/null"


def fetch_data(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def show_all_items(data):
    # Show all items in 'nextlevel' and 'lastlevel'
    all_items = []
    # If data is a list, iterate over each dict
    if isinstance(data, list):
        for entry in data:
            for key in ['nextlevel', 'lastlevel']:
                items = entry.get(key, [])
                if isinstance(items, list):
                    all_items.extend(items)
    elif isinstance(data, dict):
        for key in ['nextlevel', 'lastlevel']:
            items = data.get(key, [])
            if isinstance(items, list):
                all_items.extend(items)
    else:
        print("Unexpected data format.")
        return
    if all_items:
        print(f"\nAll items in 'nextlevel' and 'lastlevel' (total: {len(all_items)}):")
        for item in all_items:
            print(f"id: {item.get('id')},  value: {item.get('value')}, year: {item.get('year')}, title: {item.get('title')}, pessimist: {item.get('pessimist')}")
    else:
        print("No items found in 'nextlevel' or 'lastlevel'.")

def show_full_response(data):
    print("\nFull API response:")
    print(json.dumps(data, indent=2, ensure_ascii=False))

def main():
    data = fetch_data(API_URL)
    show_full_response(data)

if __name__ == "__main__":
    main()
