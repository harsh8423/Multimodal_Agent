
import requests
from dotenv import load_dotenv
import os

load_dotenv()

def scrape_instagram_with_apify(username: str, days: int = 1, search_limit: int = 1, api_token: str = None):
    """
    Search Instagram using Apify's Instagram Search Scraper actor.

    Parameters:
        username (str): The username of the Instagram account to scrape
        days (int): Number of days to scrape (default: 1)
        search_limit (int): Number of results to fetch (default: 1)
        api_token (str): Your Apify API token (optional, will use env var if not provided)

    Returns:
        list: Instagram search results as JSON
    """
    if api_token is None:
        api_token = os.getenv("APIFY_API_TOKEN")
        if not api_token:
            raise ValueError("Apify API token not provided and APIFY_API_TOKEN environment variable not set")

    url = f"https://api.apify.com/v2/acts/apify~instagram-post-scraper/run-sync-get-dataset-items?token={api_token}"

    payload = {
                "resultsLimit": 1,
                "skipPinnedPosts": True,
                "username": [username],
                "onlyPostsNewerThan":f"{days} days",
                "proxyConfiguration": {
                    "useApifyProxy": True,
                    "apifyProxyGroups": ["AUTO"] 
                }
            }


    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200 and response.status_code != 201:
        raise Exception(f"Request failed: {response.status_code}, {response.text}")

    return response.json()

if __name__ == "__main__":
    print(scrape_instagram_with_apify("google", 1))

