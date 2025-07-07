import csv
import json

def csv_to_json(csv_file_path='adaptaBrasilAPIEstrutura.csv', json_file_path='output.json'):
    """
    Convert a CSV file with pipe delimiter to a JSON file.

    Args:
        csv_file_path (str): Path to the input CSV file.
        json_file_path (str): Path to the output JSON file.
    """
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter='|')
            headers = next(reader)  # Read the header line
            data = []
            for row in reader:
                # Create a dictionary for each row
                row_data = dict(zip(headers, row))
                data.append(row_data)

        with open(json_file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, indent=4, ensure_ascii=False)
        print(f"Conversion complete. JSON file saved as {json_file_path}")
    except FileNotFoundError:
        print(f"Error: The file {csv_file_path} was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

# Run the function with default file names
if __name__ == "__main__":
    csv_to_json()

