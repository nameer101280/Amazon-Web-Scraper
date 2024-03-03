# Amazon Scraper Documentation

## Overview
The Amazon Scraper is a Python script developed for scraping product information from Amazon search results based on user queries. It gathers data such as product title, price, total reviews, and image URL, and saves it to a JSON file for further analysis. Additionally, logging functionality has been integrated to track errors and debugging information.

## Design Decisions

### User-Agent Rotation
To avoid detection and potential blocking by Amazon, the script rotates through a pool of user agents provided by the `fake_useragent` library.

### Retry Mechanism
A retry mechanism has been implemented to handle temporary server issues. Failed requests are retried a specified number of times with a delay between each attempt.

### Request Frequency Control
Request frequency is regulated to prevent triggering anti-scraping mechanisms. The script sends requests at a reasonable rate to avoid overwhelming Amazon's servers.

### Header Manipulation
Various headers, including user agents, are experimented with to simulate requests from real web browsers and reduce the likelihood of detection.

## How to Run the Script

1. **Clone the repository**
   - Start by opening the scraper.py file.

2. **Install Python**
   - Ensure Python is installed on your system. If not, download and install Python from the [official website](https://www.python.org/downloads/). Follow the installation instructions for your operating system.

3. **Install Dependencies**
   - Before executing the script, install the required Python libraries using pip, the Python package manager. Open a terminal or command prompt and run the following commands:
     ```
     pip install requests 
     pip install fake_useragent 
     pip install beautifulsoup4 
     pip install lxml 
     pip install fake-useragent 
     ```

4. **Navigate to the Script Directory**
   - Using your terminal or command prompt, navigate to the directory containing the scraper script (`scraper.py`) using the `cd` command:
     ```
     cd path/to/your/script/directory 
     ```

5. **Execute the Script**
   - Run the script by executing the following command in your terminal or command prompt:
     ```
     python scraper.py 
     ```

6. **Enter Search Query**
   - Upon running the script, it will prompt you to enter a search query related to the products you want to scrape from Amazon. For example, enter "headphones", "laptops", "smartphones", "smartwatches", "gaming consoles", "computer storage", "computer monitors", "cameras", "graphic cards" etc.

7. **Wait for Scraping to Complete**
   - The script will commence scraping Amazon search results for the specified query. Progress will be displayed as it traverses each page of results. The scraping process duration may vary based on the number of pages and products per page.

8. **View Scraped Data**
   - Upon completion, the scraped data will be saved to a JSON file. You can view this file to access the collected product information. JSON files will be created in the script directory with names corresponding to the search queries (e.g., `headphones.json`, `laptops.json`, etc.).

## Dependencies
- requests
- fake_useragent
- BeautifulSoup
- lxml (optional)
- random
- json
- logging
- time
- os

This document serves as a comprehensive guide for setting up and utilizing the Amazon Scraper script. If you encounter any issues or have further inquiries, feel free to reach out for assistance.
