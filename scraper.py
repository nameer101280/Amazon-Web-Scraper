import requests
import fake_useragent
from bs4 import BeautifulSoup
from data_saver import save_data_to_json

# Set up the User-Agent rotation
ua = fake_useragent.UserAgent()

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
    base_url = f"https://www.amazon.com/s?k={query}&ref=nb_sb_noss_1"
    products = []

    try:
        headers = {
            "User-Agent": ua.random,
            "Accept-Language": "en-US,en;q=0.5",  # Adding accept language header
            "Referer": "https://www.google.com/"  # Adding referer header
        }
        for page in range(1, 21):  # Scraping first 20 pages
            params = {
                "k": query,
                "page": page
            }
            print(f"Scraping page {page} for query '{query}'")
            response = requests.get(base_url, params=params, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "html.parser")
                product_blocks = soup.find_all("div", {"data-component-type": "s-search-result"})
                if not product_blocks:
                    print(f"No product blocks found on page {page} for query '{query}'")
                    break  # Stop scraping further pages
                print(f"Number of products found on page {page}: {len(product_blocks)}")
                for block in product_blocks:
                    try:
                        title = block.find("h2").text.strip()
                        price = block.find("span", {"class": "a-offscreen"}).text.strip()
                        total_reviews = block.find("a", {"class": "a-popover-trigger"}).find("span", {"class": "a-icon-alt"}).text.strip()
                        image_url = block.find("img", {"class": "s-image"})["src"]
                        product = Product(title, price, total_reviews, image_url)
                        products.append(product.to_dict())  # Convert product to dictionary
                    except AttributeError as e:
                        print(f"Error parsing product on page {page}: {e}")
            else:
                print(f"Failed to fetch page {page} for query '{query}'. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error occurred during scraping: {e}")

    return products
