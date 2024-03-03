import query_reader
import scraper
import data_saver

if __name__ == "__main__":
    # Read queries from user_queries.json
    try:
        queries = query_reader.read_queries("user_queries.json")
    except FileNotFoundError:
        print("Error: user_queries.json not found.")
        exit(1)
    except Exception as e:
        print(f"Error occurred while reading user_queries.json: {e}")
        exit(1)

    # Iterate over each query and scrape data
    for query in queries:
        print(f"Scraping data for query: {query}")
        try:
            scraped_data = scraper.scrape_amazon(query)
            # Save the scraped data to a JSON file
            data_saver.save_data_to_json(scraped_data, f"{query}.json")
            print(f"Scraped data saved to '{query}.json'")
        except Exception as e:
            print(f"Error occurred while scraping data for query '{query}': {e}")
