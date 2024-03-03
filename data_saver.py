import os
import json

def save_data_to_json(data, filename):
    try:
        # Create the "data" directory if it doesn't exist
        if not os.path.exists("data"):
            os.makedirs("data")
        
        # Add the directory path to the filename
        filepath = os.path.join("data", filename)
        
        with open(filepath, "w") as file:
            json.dump(data, file, indent=4)
        print(f"Data saved to {filepath} successfully.")
    except Exception as e:
        print(f"An error occurred while saving the data: {e}")
