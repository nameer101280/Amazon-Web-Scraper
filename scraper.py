import requests
import random
import re
import json
from bs4 import BeautifulSoup
from requests.exceptions import RequestException
import logging
import time
import os

# User-Agent rotation
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
]

# Logging
logging.basicConfig(filename='scraper.log', level=logging.ERROR)

RATINGS_LABEL = re.compile(r"[\d,]+\s+ratings?")


def parse_products(html):
    """Extract product dicts from an Amazon search-results page."""
    soup = BeautifulSoup(html, "html.parser")
    products = []
    for block in soup.find_all("div", {"data-component-type": "s-search-result"}):
        heading = block.find("h2")
        title = heading.get_text(strip=True) if heading else None
        if not title:
            continue
        price_tag = block.select_one("span.a-price span.a-offscreen")
        reviews_tag = block.find("a", attrs={"aria-label": RATINGS_LABEL})
        image_tag = block.find("img", {"class": "s-image"})
        products.append({
            "title": title,
            "price": price_tag.get_text(strip=True) if price_tag else None,
            "total_reviews": re.sub(r"\D", "", reviews_tag["aria-label"]) if reviews_tag else None,
            "image_url": image_tag["src"] if image_tag else None,
        })
    return products


AMAZON_SEARCH_URL = "https://www.amazon.com/s"


def scrape_amazon(query, base_url=AMAZON_SEARCH_URL, pages=20, delay_range=(1, 3)):
    """Scrape `pages` of search results for `query`, one page at a time.

    base_url and delay_range are injectable so benchmarks can point at a
    local server and control the politeness delay.
    """
    products = []

    try:
        for page in range(1, pages + 1):
            params = {
                "k": query,
                "ref": "nb_sb_noss_1",
                "page": page
            }
            print(f"Scraping page {page} for query '{query}'")
            headers = {
                "User-Agent": random.choice(user_agents),
                "Accept-Language": "en-US,en;q=0.5",  
                "Referer": "https://www.google.com/"  
            }
            response = requests.get(base_url, params=params, headers=headers)
            response.raise_for_status()  # Raise an exception for status codes
            page_products = parse_products(response.content)
            if not page_products:
                print(f"No product blocks found on page {page} for query '{query}'")
            else:
                print(f"Number of products found on page {page}: {len(page_products)}")
                products.extend(page_products)
            if delay_range[1] > 0:
                time.sleep(random.uniform(*delay_range))  # Add a delay between requests
    except RequestException as e:
        logging.error(f"Request error occurred during scraping: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

    return products

def save_data_to_json(data, filename):
    data_folder = "data"
    os.makedirs(data_folder, exist_ok=True)  # Create the "data" folder if it doesn't exist
    filepath = os.path.join(data_folder, filename)
    with open(filepath, 'w') as json_file:
        json.dump(data, json_file, indent=4)
    print(f"Data saved to {filepath} successfully.")

if __name__ == "__main__":
    query = input("Enter your search query: ")
    scraped_data = scrape_amazon(query)
    if scraped_data:
        file_name = f"{query}.json"
        save_data_to_json(scraped_data, file_name)
    else:
        print("No data scraped.")
