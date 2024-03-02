import query_reader
import scraper
import data_saver

if __name__ == "__main__":
    # Read queries from user_queries.json
    queries = query_reader.read_queries("user_queries.json")

    # Iterate over each query and scrape data
    for query in queries:
        print(f"Scraping data for query: {query}")
        scraped_data = scraper.scrape_amazon(query)
        
        # Save the scraped data to a JSON file
        data_saver.save_data_to_json(scraped_data, f"{query}.json")
        print(f"Scraped data saved to '{query}.json'")
