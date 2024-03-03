
# Amazon Scraper

## Documentation Overview
Amazon Scraper is a Python script designed to scrape product information from Amazon search results based on user queries. It extracts data such as product title, price, total reviews, and image URL, saving it to a JSON file for further analysis.

## Design Decisions
### User-Agent Rotation:
To evade detection and potential blocking by Amazon, the script rotates through a pool of user agents provided by the fake_useragent library.

### Retry Mechanism:
A retry mechanism is implemented to handle temporary server issues. Failed requests are retried a specified number of times with a delay between each attempt.

### Request Frequency Control:
Request frequency is regulated to avoid triggering anti-scraping mechanisms. The script sends requests at a reasonable rate to prevent overwhelming Amazon's servers.

### Header Manipulation:
Various headers, including user agents, are experimented with to simulate requests from real web browsers and reduce the likelihood of detection.

## How to Run the Script

1. **Open the Source file:**
   - Start by opeining the `scraper.py` script file in your IDE. 

2. **Install Python:**
   - Ensure that you have Python installed on your system. You can download and install Python from the official website: [Python Downloads](https://www.python.org/downloads/). Follow the installation instructions based on your operating system.

3. **Install Dependencies:**
   - Before running the script, you need to install the required Python libraries. Open a terminal or command prompt and use pip, the Python package manager, to install the necessary dependencies:
     ```
     pip install requests
     pip install fake_useragent
     pip install beautifulsoup4
     ```

4. **Navigate to the Script Directory:**
   - Use your terminal or command prompt to navigate to the directory where the scraper script (`scraper.py`) is located. You can use the `cd` command to change directories:
     ```
     cd path/to/your/script/directory
     ```

5. **Run the Script:**
   - Execute the script by running the following command in your terminal or command prompt:
     ```
     python scraper.py
     ```

6. **Enter Search Query:**
   - After running the script, it will prompt you to enter a search query. This query should be related to the products you want to scrape from Amazon. For example, you can enter "headphones", "laptops", "smartphones", "cameras", "gaming consoles", "computer monitors", "computer storage", "keyboards", "graphic cards".

7. **Wait for Scraping to Complete:**
   - Once you've entered the search query, the script will start scraping Amazon search results for the specified query. It will display the progress as it goes through each page of results. The scraping process may take some time depending on the number of pages to scrape and the number of products per page.

8. **View Scraped Data:**
   - After the scraping process is complete, the script will save the scraped data to a JSON file. You can then view this file to access the collected product information. The JSON files will be created in the same directory where the script is located, with names corresponding to the search queries (e.g., `headphones.json`, `laptops.json`, etc.).

## Dependencies
- requests
- fake_useragent
- BeautifulSoup



