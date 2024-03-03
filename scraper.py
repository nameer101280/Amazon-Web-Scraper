import requests
import random
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

class Product:
    def __init__(self, title, price, total_reviews, image_url):
        self.title = title
        self.price = price
        self.total_reviews = total_reviews
        self.image_url = image_url

    def to_dict(self):
        return {
            "title": self.title,
            "price": self.price,
            "total_reviews": self.total_reviews,
            "image_url": self.image_url
        }

def scrape_amazon(query):
    base_url = f"https://www.amazon.com/s"
    products = []

    try:
        for page in range(1, 21):  # Scraping first 20 pages
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
            soup = BeautifulSoup(response.content, "html.parser")
            product_blocks = soup.find_all("div", {"data-component-type": "s-search-result"})
            if not product_blocks:
                print(f"No product blocks found on page {page} for query '{query}'")
            else:
                print(f"Number of products found on page {page}: {len(product_blocks)}")
                for block in product_blocks:
                    try:
                        title = block.find("span", {"class": "a-size-medium"}).text.strip()
                        price = block.find("span", {"class": "a-price-whole"}).text.strip()
                        total_reviews = block.find("span", {"class": "a-size-base"}).text.strip()
                        image_url = block.find("img", {"class": "s-image"})["src"]
                        product = Product(title, price, total_reviews, image_url)
                        products.append(product.to_dict()) 
                        if len(products) == 10:
                            break
                    except AttributeError as e:
                        logging.error(f"Error parsing product on page {page}: {e}")
                        continue
            time.sleep(random.uniform(1, 3))  # Add a delay between requests
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
