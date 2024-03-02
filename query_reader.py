import json

def read_queries(filename):
    try:
        with open(filename, "r") as file:
            queries = json.load(file)
        return queries
    except FileNotFoundError:
        print(f"File '{filename}' not found.")
        return []
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return []

# Test the read_queries function
if __name__ == "__main__":
    queries = read_queries("user_queries.json")
    print("Read queries:", queries)
