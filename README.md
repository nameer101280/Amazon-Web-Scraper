
# Amazon Scraper

## Documentation Overview
Amazon Scraper is a Python script designed to scrape product information from Amazon search results based on user-provided queries. It extracts data such as product title, price, total reviews, and image URL, saving it to a JSON file for further analysis.

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
1. Clone the repository to your local machine.
2 Run the script by executing `python scraper.py`.
3. Enter your search query when prompted.
4. The script will scrape Amazon search results for the specified query and save the data to a JSON file.

## Dependencies
- requests
- fake_useragent
- BeautifulSoup

## Contributing
Contributions, such as bug reports, feature requests, and pull requests, are welcome! 

