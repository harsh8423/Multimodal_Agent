import os
import requests
from dotenv import load_dotenv

load_dotenv()

def get_youtube_videos_by_channel(username: str, published_after: str, max_results: int = 5, api_key: str = None):
    """
    Fetch YouTube videos from a channel by username using YouTube Data API v3.

    Parameters:
        username (str): YouTube channel username (NOT custom URL or handle, e.g. 'GoogleDevelopers')
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
    
    # Step 1: Get channelId from username
    channel_url = "https://www.googleapis.com/youtube/v3/channels"
    channel_params = {
        "part": "id",
        "forUsername": username,
        "key": api_key,
    }
    channel_resp = requests.get(channel_url, params=channel_params)
    if channel_resp.status_code != 200:
        raise Exception(f"Channel lookup failed: {channel_resp.status_code}, {channel_resp.text}")

    channel_data = channel_resp.json()
    if not channel_data.get("items"):
        raise ValueError(f"No channel found for username: {username}")
    channel_id = channel_data["items"][0]["id"]

    # Step 2: Get videos by channelId
    search_url = "https://www.googleapis.com/youtube/v3/search"
    search_params = {
        "part": "snippet",
        "channelId": channel_id,
        "type": "video",
        "order": "date",
        "publishedAfter": published_after,
        "maxResults": max_results,
        "key": api_key,
    }
    response = requests.get(search_url, params=search_params)
    if response.status_code != 200:
        raise Exception(f"Video fetch failed: {response.status_code}, {response.text}")

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


videos = get_youtube_videos_by_channel(
    username="GoogleDevelopers",
    published_after="2024-01-01T00:00:00Z",
    max_results=5
)

for v in videos:
    print(v["title"], v["url"])
