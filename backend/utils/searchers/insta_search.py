

import requests
import os
from dotenv import load_dotenv

load_dotenv()

def search_instagram_with_apify(search_term: str, search_type: str = "hashtag", search_limit: int = 1, api_token: str = None):
    """
    Search Instagram using Apify's Instagram Search Scraper actor.

    Parameters:
        search_term (str): The search term (e.g., hashtag or username)
        search_type (str): Type of search ('hashtag', 'user', etc.)
        search_limit (int): Number of results to fetch (default: 1)
        api_token (str): Your Apify API token (optional, will use env var if not provided)

    Returns:
        list: Instagram search results as JSON
    """
    if api_token is None:
        api_token = os.getenv("APIFY_API_TOKEN")
        if not api_token:
            raise ValueError("Apify API token not provided and APIFY_API_TOKEN environment variable not set")

    url = f"https://api.apify.com/v2/acts/apify~instagram-search-scraper/run-sync-get-dataset-items?token={api_token}"

    payload = {
        "enhanceUserSearchWithFacebookPage": False,
        "search": search_term,
        "searchLimit": search_limit,
        "searchType": search_type,
        "proxyConfiguration": {
            "useApifyProxy": True,
            "apifyProxyGroups": ["AUTO"]
        }
    }

    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200 or response.status_code != 201:
        raise Exception(f"Request failed: {response.status_code}, {response.text}")

    return response.json()


if __name__ == "__main__":
    search_term = "ai automation"
    search_type = "hashtag"
    search_limit = 1
    api_token = os.getenv("APIFY_API_TOKEN")
    results = search_instagram_with_apify(search_term, search_type, search_limit, api_token)
    print(results)


