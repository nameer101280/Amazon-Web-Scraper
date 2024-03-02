import json

def save_data_to_json(data, filename):
    try:
        with open(filename, "w") as file:
            json.dump(data, file, indent=4)
        print(f"Data saved to {filename} successfully.")
    except Exception as e:
        print(f"An error occurred while saving the data: {e}")
