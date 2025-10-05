"""
YouTube Shorts Publishing Tool

This tool provides functional programming interface for publishing YouTube Shorts
using the official YouTube Data API v3. Supports video uploads, scheduling, and metadata management.

Authentication Requirements:
- Google Cloud Project with YouTube Data API v3 enabled
- OAuth 2.0 credentials (client_id, client_secret)
- YouTube channel access
- Required scopes: https://www.googleapis.com/auth/youtube.upload

Setup Instructions:
1. Go to Google Cloud Console (https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable YouTube Data API v3
4. Create OAuth 2.0 credentials (Desktop application type)
5. Download credentials JSON file
6. Set environment variables: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import base64
import hashlib
import hmac
import time


class PrivacyStatus(Enum):
    """YouTube video privacy status"""
    PUBLIC = "public"
    PRIVATE = "private"
    UNLISTED = "unlisted"


class VideoCategory(Enum):
    """YouTube video categories"""
    ENTERTAINMENT = "24"
    MUSIC = "10"
    COMEDY = "23"
    EDUCATION = "27"
    SCIENCE_TECHNOLOGY = "28"
    SPORTS = "17"
    GAMING = "20"
    NEWS_POLITICS = "25"
    HOWTO_STYLE = "26"
    AUTOS_VEHICLES = "2"
    TRAVEL_EVENTS = "19"
    PEOPLE_BLOGS = "22"


@dataclass
class YouTubeVideo:
    """Data class for YouTube video content"""
    title: str
    description: str
    video_file_path: str
    privacy_status: PrivacyStatus = PrivacyStatus.PUBLIC
    category_id: str = VideoCategory.ENTERTAINMENT.value
    tags: Optional[List[str]] = None
    thumbnail_path: Optional[str] = None
    scheduled_publish_time: Optional[datetime] = None
    made_for_kids: bool = False


@dataclass
class YouTubeResponse:
    """Response from YouTube API"""
    success: bool
    video_id: Optional[str] = None
    error_message: Optional[str] = None
    upload_url: Optional[str] = None


class YouTubePublisher:
    """Functional YouTube Shorts publishing tool"""
    
    def __init__(self, client_id: str, client_secret: str, refresh_token: str):
        """
        Initialize YouTube publisher
        
        Args:
            client_id: Google OAuth 2.0 client ID
            client_secret: Google OAuth 2.0 client secret
            refresh_token: OAuth 2.0 refresh token
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.access_token = None
        self.token_expires_at = None
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.upload_url = "https://www.googleapis.com/upload/youtube/v3/videos"
        
    def _get_access_token(self) -> str:
        """Get valid access token, refreshing if necessary"""
        if self.access_token and self.token_expires_at and datetime.now() < self.token_expires_at:
            return self.access_token
        
        # Refresh the access token
        url = "https://oauth2.googleapis.com/token"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token"
        }
        
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            token_data = response.json()
            
            self.access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
            
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to refresh access token: {str(e)}")
    
    def _make_request(self, method: str, url: str, data: Optional[Dict] = None,
                     files: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict:
        """Make HTTP request to YouTube API"""
        headers = {
            "Authorization": f"Bearer {self._get_access_token()}",
            "Content-Type": "application/json"
        }
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                if files:
                    headers.pop("Content-Type")  # Let requests set multipart boundary
                    response = requests.post(url, headers=headers, data=data, files=files)
                else:
                    response = requests.post(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {"error": {"message": str(e)}}
    
    def _upload_video_file(self, video_path: str, metadata: Dict) -> YouTubeResponse:
        """Upload video file to YouTube"""
        if not os.path.exists(video_path):
            return YouTubeResponse(
                success=False,
                error_message=f"Video file not found: {video_path}"
            )
        
        # Prepare video metadata
        video_metadata = {
            "snippet": {
                "title": metadata["title"],
                "description": metadata["description"],
                "categoryId": metadata["category_id"],
                "tags": metadata.get("tags", [])
            },
            "status": {
                "privacyStatus": metadata["privacy_status"],
                "selfDeclaredMadeForKids": metadata.get("made_for_kids", False)
            }
        }
        
        # Add scheduled publish time if provided
        if metadata.get("scheduled_publish_time"):
            video_metadata["status"]["publishAt"] = metadata["scheduled_publish_time"].isoformat() + "Z"
            video_metadata["status"]["privacyStatus"] = "private"  # Must be private for scheduled
        
        # Upload video
        url = f"{self.upload_url}?part=snippet,status&uploadType=multipart"
        
        files = {
            "video": open(video_path, "rb")
        }
        
        data = {
            "metadata": json.dumps(video_metadata)
        }
        
        try:
            response = requests.post(
                url,
                headers={"Authorization": f"Bearer {self._get_access_token()}"},
                files=files,
                data=data
            )
            response.raise_for_status()
            result = response.json()
            
            files["video"].close()
            
            return YouTubeResponse(
                success=True,
                video_id=result["id"]
            )
            
        except requests.exceptions.RequestException as e:
            if "video" in files:
                files["video"].close()
            return YouTubeResponse(
                success=False,
                error_message=str(e)
            )
    
    def _upload_thumbnail(self, video_id: str, thumbnail_path: str) -> bool:
        """Upload custom thumbnail for video"""
        if not os.path.exists(thumbnail_path):
            return False
        
        url = f"{self.base_url}/thumbnails/set"
        params = {"videoId": video_id}
        
        try:
            with open(thumbnail_path, "rb") as thumbnail_file:
                response = requests.post(
                    url,
                    headers={"Authorization": f"Bearer {self._get_access_token()}"},
                    params=params,
                    files={"thumbnail": thumbnail_file}
                )
                response.raise_for_status()
                return True
                
        except requests.exceptions.RequestException:
            return False
    
    def publish_video(self, video: YouTubeVideo) -> YouTubeResponse:
        """
        Publish video to YouTube
        
        Args:
            video: YouTubeVideo object containing video details
            
        Returns:
            YouTubeResponse with success status and video ID
        """
        # Prepare metadata
        metadata = {
            "title": video.title,
            "description": video.description,
            "category_id": video.category_id,
            "privacy_status": video.privacy_status.value,
            "tags": video.tags or [],
            "made_for_kids": video.made_for_kids,
            "scheduled_publish_time": video.scheduled_publish_time
        }
        
        # Upload video
        upload_response = self._upload_video_file(video.video_file_path, metadata)
        
        if not upload_response.success:
            return upload_response
        
        # Upload thumbnail if provided
        if video.thumbnail_path and upload_response.video_id:
            self._upload_thumbnail(upload_response.video_id, video.thumbnail_path)
        
        return upload_response
    
    def get_video_info(self, video_id: str) -> Dict:
        """Get information about a published video"""
        url = f"{self.base_url}/videos"
        params = {
            "part": "snippet,status,statistics",
            "id": video_id
        }
        
        response = self._make_request("GET", url, params=params)
        return response
    
    def update_video(self, video_id: str, updates: Dict) -> Dict:
        """Update video metadata"""
        url = f"{self.base_url}/videos"
        
        # Get current video info
        current_info = self.get_video_info(video_id)
        if "error" in current_info:
            return current_info
        
        # Merge updates with current info
        video_data = current_info["items"][0]
        snippet = video_data["snippet"]
        status = video_data["status"]
        
        if "title" in updates:
            snippet["title"] = updates["title"]
        if "description" in updates:
            snippet["description"] = updates["description"]
        if "tags" in updates:
            snippet["tags"] = updates["tags"]
        if "privacy_status" in updates:
            status["privacyStatus"] = updates["privacy_status"]
        
        data = {
            "id": video_id,
            "snippet": snippet,
            "status": status
        }
        
        response = self._make_request("PUT", url, data)
        return response
    
    def delete_video(self, video_id: str) -> Dict:
        """Delete a video"""
        url = f"{self.base_url}/videos"
        params = {"id": video_id}
        
        response = self._make_request("DELETE", url, params=params)
        return response
    
    def get_channel_info(self) -> Dict:
        """Get channel information"""
        url = f"{self.base_url}/channels"
        params = {
            "part": "snippet,statistics",
            "mine": "true"
        }
        
        response = self._make_request("GET", url, params=params)
        return response


# Functional interface functions
def create_youtube_publisher(client_id: str, client_secret: str, refresh_token: str) -> YouTubePublisher:
    """Create YouTube publisher instance"""
    return YouTubePublisher(client_id, client_secret, refresh_token)


def publish_shorts_video(publisher: YouTubePublisher, video_path: str, title: str,
                        description: str, tags: Optional[List[str]] = None,
                        scheduled_time: Optional[datetime] = None) -> YouTubeResponse:
    """Publish YouTube Shorts video"""
    video = YouTubeVideo(
        title=title,
        description=description,
        video_file_path=video_path,
        tags=tags,
        scheduled_publish_time=scheduled_time,
        category_id=VideoCategory.ENTERTAINMENT.value
    )
    return publisher.publish_video(video)


def publish_scheduled_video(publisher: YouTubePublisher, video: YouTubeVideo,
                           publish_time: datetime) -> YouTubeResponse:
    """Schedule video for future publication"""
    video.scheduled_publish_time = publish_time
    video.privacy_status = PrivacyStatus.PRIVATE  # Must be private for scheduled
    return publisher.publish_video(video)


def publish_private_video(publisher: YouTubePublisher, video_path: str, title: str,
                          description: str) -> YouTubeResponse:
    """Publish private video"""
    video = YouTubeVideo(
        title=title,
        description=description,
        video_file_path=video_path,
        privacy_status=PrivacyStatus.PRIVATE
    )
    return publisher.publish_video(video)


def publish_unlisted_video(publisher: YouTubePublisher, video_path: str, title: str,
                           description: str) -> YouTubeResponse:
    """Publish unlisted video"""
    video = YouTubeVideo(
        title=title,
        description=description,
        video_file_path=video_path,
        privacy_status=PrivacyStatus.UNLISTED
    )
    return publisher.publish_video(video)


def update_video_metadata(publisher: YouTubePublisher, video_id: str, 
                          title: Optional[str] = None, description: Optional[str] = None,
                          tags: Optional[List[str]] = None) -> Dict:
    """Update video metadata"""
    updates = {}
    if title:
        updates["title"] = title
    if description:
        updates["description"] = description
    if tags:
        updates["tags"] = tags
    
    return publisher.update_video(video_id, updates)


def change_video_privacy(publisher: YouTubePublisher, video_id: str, 
                        privacy_status: PrivacyStatus) -> Dict:
    """Change video privacy status"""
    return publisher.update_video(video_id, {"privacy_status": privacy_status.value})


# Authentication setup functions
def setup_youtube_auth() -> Tuple[str, str, str]:
    """
    Setup YouTube authentication
    
    Returns:
        Tuple of (client_id, client_secret, refresh_token)
        
    Instructions:
    1. Go to Google Cloud Console (https://console.cloud.google.com/)
    2. Create a new project or select existing one
    3. Enable YouTube Data API v3
    4. Go to Credentials and create OAuth 2.0 Client ID
    5. Choose "Desktop application" as application type
    6. Download the JSON file
    7. Use the OAuth 2.0 Playground to get refresh token:
       - Go to https://developers.google.com/oauthplayground/
       - Select YouTube Data API v3
       - Select scope: https://www.googleapis.com/auth/youtube.upload
       - Authorize and exchange for refresh token
    8. Set environment variables or return values directly
    """
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN")
    
    if not all([client_id, client_secret, refresh_token]):
        raise ValueError(
            "Please set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_REFRESH_TOKEN "
            "environment variables. See setup_youtube_auth() docstring for detailed instructions."
        )
    
    return client_id, client_secret, refresh_token


def get_oauth_url(client_id: str, redirect_uri: str = "urn:ietf:wg:oauth:2.0:oob") -> str:
    """
    Generate OAuth 2.0 authorization URL
    
    Args:
        client_id: Google OAuth 2.0 client ID
        redirect_uri: Redirect URI (default is for desktop apps)
        
    Returns:
        Authorization URL for user to visit
    """
    scope = "https://www.googleapis.com/auth/youtube.upload"
    auth_url = (
        f"https://accounts.google.com/o/oauth2/auth?"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"scope={scope}&"
        f"response_type=code&"
        f"access_type=offline"
    )
    return auth_url


def exchange_code_for_token(client_id: str, client_secret: str, code: str,
                           redirect_uri: str = "urn:ietf:wg:oauth:2.0:oob") -> Dict:
    """
    Exchange authorization code for access and refresh tokens
    
    Args:
        client_id: Google OAuth 2.0 client ID
        client_secret: Google OAuth 2.0 client secret
        code: Authorization code from OAuth flow
        redirect_uri: Redirect URI used in authorization
        
    Returns:
        Dictionary containing access_token and refresh_token
    """
    url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri
    }
    
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


# Example usage
if __name__ == "__main__":
    # Setup authentication
    try:
        client_id, client_secret, refresh_token = setup_youtube_auth()
        publisher = create_youtube_publisher(client_id, client_secret, refresh_token)
        
        # Example: Publish a Shorts video
        response = publish_shorts_video(
            publisher=publisher,
            video_path="path/to/shorts_video.mp4",
            title="Amazing Shorts Video! #Shorts",
            description="Check out this incredible short video content!",
            tags=["shorts", "viral", "funny", "entertainment"]
        )
        
        if response.success:
            print(f"Video published successfully! Video ID: {response.video_id}")
        else:
            print(f"Failed to publish video: {response.error_message}")
            
    except ValueError as e:
        print(f"Authentication error: {e}")