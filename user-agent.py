from fake_useragent import UserAgent
import requests

# Create a UserAgent object
user_agent = UserAgent()

# Get a random user agent
headers = {'User-Agent': user_agent.random}

# Your scraping code here
url = 'https://www.amazon.com/s?k=headphones'
webpage = requests.get(url, headers=headers)

# Print the response
print(webpage)
