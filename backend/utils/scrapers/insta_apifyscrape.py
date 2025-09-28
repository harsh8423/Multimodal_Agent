
import requests
from dotenv import load_dotenv
import os
import json

load_dotenv()

def scrape_instagram_with_apify(username: str, days: int = 1, search_limit: int = 3, api_token: str = None):
    """
    Search Instagram using Apify's Instagram Search Scraper actor.

    Parameters:
        username (str): The username of the Instagram account to scrape
        days (int): Number of days to scrape (default: 1)
        search_limit (int): Number of results to fetch (default: 1)
        api_token (str): Your Apify API token (optional, will use env var if not provided)

    Returns:
        list: Instagram search results as JSON with filtered fields
    """
    if api_token is None:
        api_token = os.getenv("APIFY_API_TOKEN")
        if not api_token:
            raise ValueError("Apify API token not provided and APIFY_API_TOKEN environment variable not set")

    url = f"https://api.apify.com/v2/acts/apify~instagram-post-scraper/run-sync-get-dataset-items?token={api_token}"

    payload = {
                "resultsLimit": search_limit,
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

    # Get the raw response
    raw_data = response.json()
    
    # Save raw response for debugging
    json.dump(raw_data, open("response.json", "w"))
    
    # Filter to return only specified fields
    filtered_data = []
    for post in raw_data:
        filtered_post = {
            "username": post.get("ownerUsername", ""),
            "post_id": post.get("id", ""),
            "post_url": post.get("url", ""),
            "displayUrl": post.get("displayUrl", ""),
            "videoUrl": post.get("videoUrl", ""),
            "images": post.get("images", []),
            "type": post.get("type", ""),
            "caption": post.get("caption", ""),
            "likesCount": post.get("likesCount", 0),
            "commentsCount": post.get("commentsCount", 0),
            "dimensionsHeight": post.get("dimensionsHeight", 0),
            "dimensionsWidth": post.get("dimensionsWidth", 0)
        }
        filtered_data.append(filtered_post)

    return filtered_data

