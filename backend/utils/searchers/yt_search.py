import os
import requests
from dotenv import load_dotenv

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