import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_youtube_videos(query: str, published_after: str, max_results: int = 5, api_key: str = None):
    """
    Fetch YouTube videos directly via YouTube Data API v3 REST endpoint.

    Parameters:
        query (str): Search query string
        published_after (str): ISO 8601 datetime (e.g., "2024-01-01T00:00:00Z")
        max_results (int): Number of results to fetch (default: 5)
        api_key (str): Your YouTube Data API key (optional, will use env var if not provided)

    Returns:
        list: A list of video data dictionaries
    """
    if api_key is None:
        api_key = os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            raise ValueError("YouTube API key not provided and YOUTUBE_API_KEY environment variable not set")
    
    url = "https://www.googleapis.com/youtube/v3/search"

    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "publishedAfter": published_after,
        "maxResults": max_results,
        "key": api_key,
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        raise Exception(f"API request failed: {response.status_code}, {response.text}")

    data = response.json()

    videos = []
    for item in data.get("items", []):
        video_data = {
            "videoId": item["id"]["videoId"],
            "title": item["snippet"]["title"],
            "description": item["snippet"]["description"],
            "publishedAt": item["snippet"]["publishedAt"],
            "channelTitle": item["snippet"]["channelTitle"],
            "channelId": item["snippet"]["channelId"],
            "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
        }
        videos.append(video_data)

    return videos




################################ PERPLEXITY SEARCH #################################

import requests

def search_with_perplexity_sonar(
    search_description: str,
    user_prompt: str,
    model: str = "sonar-pro",
    api_key: str = None
):
    """
    Perform web search + answer synthesis using Perplexity's Sonar Pro model.

    Parameters:
        search_description (str): instruction / context to guide the search (system message)
        user_prompt (str): the actual user query
        model (str): which model to use; default "sonar-pro"
        api_key (str): your Perplexity API key (optional, will use env var if not provided)

    Returns:
        dict: parsed response, including answer, citations, search_results etc.
    """
    if api_key is None:
        api_key = os.getenv("PERPLEXITY_API_KEY")
        if not api_key:
            raise ValueError("Perplexity API key not provided and PERPLEXITY_API_KEY environment variable not set")

    url = "https://api.perplexity.ai/chat/completions"

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    messages = []
    # system message with the description
    if search_description:
        messages.append({"role": "system", "content": search_description})
    # user message
    messages.append({"role": "user", "content": user_prompt})

    payload = {
        "model": model,
        "messages": messages,
    }


    response = requests.post(url, json=payload, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Request failed: {response.status_code}, {response.text}")

    resp_json = response.json()

    # You might get fields like "search_results", "citations", etc.
    # Let's parse and return them.
    result = {
        "answer": resp_json.get("choices", [])[0].get("message", {}).get("content") if resp_json.get("choices") else None,
        "search_results": resp_json.get("search_results"),
        "citations": resp_json.get("citations"),
        "raw_response": resp_json
    }

    return result


########################################### GROUNDING WITH GOOGLE SEARCH #######################################


import requests

def gemini_google_search(search_description: str, model: str = "gemini-2.5-pro", api_key: str = None):
    """
    Perform grounded search using Gemini 2.5 Pro with Google Search tool enabled.

    Parameters:
        search_description (str): The query or description to send
        model (str): Model to use (default: gemini-2.5-pro)
        api_key (str): Your Google API key (optional, will use env var if not provided)

    Returns:
        dict: Parsed response including grounded answer
    """
    if api_key is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Gemini API key not provided and GEMINI_API_KEY environment variable not set")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": search_description}
                ]
            }
        ],
        "tools": [
            {"google_search": {}}
        ]
    }

    response = requests.post(url, headers=headers, json=payload)
 
    if response.status_code != 200:
        raise Exception(f"Request failed: {response.status_code}, {response.text}")

    data = response.json()

    # Extract main text response (if present)
    text_response = None
    try:
        text_response = data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        text_response = None

    return {
        "answer": text_response,
        "raw_response": data
    }




import requests

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

    if response.status_code != 200:
        raise Exception(f"Request failed: {response.status_code}, {response.text}")

    return response.json()


