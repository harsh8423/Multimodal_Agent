"""
Instagram Publishing Tool

This tool provides functional programming interface for publishing content to Instagram
using the official Instagram Graph API. Supports images, videos, reels, carousels, and stories.

Authentication Requirements:
- Instagram Business Account
- Facebook Page connected to Instagram account
- App with Instagram Graph API access
- Required permissions: instagram_basic, instagram_content_publish, pages_read_engagement

Setup Instructions:
1. Create a Facebook App at https://developers.facebook.com/
2. Add Instagram Graph API product
3. Configure Instagram Basic Display settings
4. Get Page Access Token with required permissions
5. Set environment variables: INSTAGRAM_ACCESS_TOKEN, FACEBOOK_PAGE_ID
"""

import os
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum


class MediaType(Enum):
    """Instagram media types"""
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    REELS = "REELS"
    STORIES = "STORIES"
    CAROUSEL = "CAROUSEL"


class PrivacyStatus(Enum):
    """Privacy status for posts"""
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"


@dataclass
class InstagramPost:
    """Data class for Instagram post content"""
    media_urls: List[str]
    caption: str
    media_type: MediaType
    alt_text: Optional[str] = None
    user_tags: Optional[List[Dict]] = None
    location_id: Optional[str] = None
    scheduled_publish_time: Optional[datetime] = None


@dataclass
class InstagramResponse:
    """Response from Instagram API"""
    success: bool
    container_id: Optional[str] = None
    media_id: Optional[str] = None
    error_message: Optional[str] = None


class InstagramPublisher:
    """Functional Instagram publishing tool"""
    
    def __init__(self, access_token: str, page_id: str):
        """
        Initialize Instagram publisher
        
        Args:
            access_token: Facebook Page access token
            page_id: Facebook Page ID connected to Instagram account
        """
        self.access_token = access_token
        self.page_id = page_id
        self.base_url = "https://graph.facebook.com/v23.0"
        self.upload_url = "https://rupload.facebook.com"
        
    def _make_request(self, method: str, url: str, data: Optional[Dict] = None, 
                     files: Optional[Dict] = None) -> Dict:
        """Make HTTP request to Instagram API"""
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=data)
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
    
    def _create_media_container(self, post: InstagramPost) -> InstagramResponse:
        """Create media container for Instagram post"""
        if post.media_type == MediaType.CAROUSEL:
            return self._create_carousel_container(post)
        else:
            return self._create_single_media_container(post)
    
    def _create_single_media_container(self, post: InstagramPost) -> InstagramResponse:
        """Create container for single media (image/video/reel/story)"""
        url = f"{self.base_url}/{self.page_id}/media"
        
        data = {
            "access_token": self.access_token,
            "media_type": post.media_type.value,
            "caption": post.caption
        }
        
        # Add media URL
        if post.media_type in [MediaType.IMAGE, MediaType.STORIES]:
            data["image_url"] = post.media_urls[0]
        elif post.media_type in [MediaType.VIDEO, MediaType.REELS]:
            data["video_url"] = post.media_urls[0]
        
        # Add optional parameters
        if post.alt_text:
            data["alt_text"] = post.alt_text
        if post.user_tags:
            data["user_tags"] = json.dumps(post.user_tags)
        if post.location_id:
            data["location_id"] = post.location_id
        if post.scheduled_publish_time:
            data["scheduled_publish_time"] = int(post.scheduled_publish_time.timestamp())
        
        response = self._make_request("POST", url, data)
        
        if "error" in response:
            return InstagramResponse(
                success=False,
                error_message=response["error"]["message"]
            )
        
        return InstagramResponse(
            success=True,
            container_id=response["id"]
        )
    
    def _create_carousel_container(self, post: InstagramPost) -> InstagramResponse:
        """Create container for carousel post"""
        # First create individual media containers
        child_containers = []
        for media_url in post.media_urls:
            child_post = InstagramPost(
                media_urls=[media_url],
                caption="",  # No caption for individual carousel items
                media_type=MediaType.IMAGE if media_url.lower().endswith(('.jpg', '.jpeg', '.png')) else MediaType.VIDEO
            )
            child_response = self._create_single_media_container(child_post)
            if not child_response.success:
                return child_response
            child_containers.append(child_response.container_id)
        
        # Create carousel container
        url = f"{self.base_url}/{self.page_id}/media"
        data = {
            "access_token": self.access_token,
            "media_type": MediaType.CAROUSEL.value,
            "children": ",".join(child_containers),
            "caption": post.caption
        }
        
        if post.scheduled_publish_time:
            data["scheduled_publish_time"] = int(post.scheduled_publish_time.timestamp())
        
        response = self._make_request("POST", url, data)
        
        if "error" in response:
            return InstagramResponse(
                success=False,
                error_message=response["error"]["message"]
            )
        
        return InstagramResponse(
            success=True,
            container_id=response["id"]
        )
    
    def _publish_media(self, container_id: str) -> InstagramResponse:
        """Publish media container"""
        url = f"{self.base_url}/{self.page_id}/media_publish"
        data = {
            "access_token": self.access_token,
            "creation_id": container_id
        }
        
        response = self._make_request("POST", url, data)
        
        if "error" in response:
            return InstagramResponse(
                success=False,
                error_message=response["error"]["message"]
            )
        
        return InstagramResponse(
            success=True,
            media_id=response["id"]
        )
    
    def _check_container_status(self, container_id: str) -> str:
        """Check status of media container"""
        url = f"{self.base_url}/{container_id}"
        params = {
            "access_token": self.access_token,
            "fields": "status_code"
        }
        
        response = self._make_request("GET", url, params)
        
        if "error" in response:
            return "ERROR"
        
        return response.get("status_code", "UNKNOWN")
    
    def publish_post(self, post: InstagramPost) -> InstagramResponse:
        """
        Publish content to Instagram
        
        Args:
            post: InstagramPost object containing content details
            
        Returns:
            InstagramResponse with success status and media ID
        """
        # Create media container
        container_response = self._create_media_container(post)
        if not container_response.success:
            return container_response
        
        # For scheduled posts, don't publish immediately
        if post.scheduled_publish_time and post.scheduled_publish_time > datetime.now():
            return InstagramResponse(
                success=True,
                container_id=container_response.container_id,
                error_message="Post scheduled for later publication"
            )
        
        # Check container status before publishing
        status = self._check_container_status(container_response.container_id)
        if status != "FINISHED":
            return InstagramResponse(
                success=False,
                error_message=f"Container not ready for publishing. Status: {status}"
            )
        
        # Publish the media
        return self._publish_media(container_response.container_id)
    
    def get_publishing_limit(self) -> Dict:
        """Get current publishing rate limit usage"""
        url = f"{self.base_url}/{self.page_id}/content_publishing_limit"
        params = {"access_token": self.access_token}
        
        response = self._make_request("GET", url, params)
        return response
    
    def get_page_info(self) -> Dict:
        """Get Instagram page information"""
        url = f"{self.base_url}/{self.page_id}"
        params = {
            "access_token": self.access_token,
            "fields": "id,name,username,followers_count,follows_count,media_count"
        }
        
        response = self._make_request("GET", url, params)
        return response


# Functional interface functions
def create_instagram_publisher(access_token: str, page_id: str) -> InstagramPublisher:
    """Create Instagram publisher instance"""
    return InstagramPublisher(access_token, page_id)


def publish_image_post(publisher: InstagramPublisher, image_url: str, caption: str,
                      alt_text: Optional[str] = None, scheduled_time: Optional[datetime] = None) -> InstagramResponse:
    """Publish single image post"""
    post = InstagramPost(
        media_urls=[image_url],
        caption=caption,
        media_type=MediaType.IMAGE,
        alt_text=alt_text,
        scheduled_publish_time=scheduled_time
    )
    return publisher.publish_post(post)


def publish_video_post(publisher: InstagramPublisher, video_url: str, caption: str,
                       scheduled_time: Optional[datetime] = None) -> InstagramResponse:
    """Publish single video post"""
    post = InstagramPost(
        media_urls=[video_url],
        caption=caption,
        media_type=MediaType.VIDEO,
        scheduled_publish_time=scheduled_time
    )
    return publisher.publish_post(post)


def publish_reel(publisher: InstagramPublisher, video_url: str, caption: str,
                 scheduled_time: Optional[datetime] = None) -> InstagramResponse:
    """Publish Instagram Reel"""
    post = InstagramPost(
        media_urls=[video_url],
        caption=caption,
        media_type=MediaType.REELS,
        scheduled_publish_time=scheduled_time
    )
    return publisher.publish_post(post)


def publish_story(publisher: InstagramPublisher, media_url: str, 
                  scheduled_time: Optional[datetime] = None) -> InstagramResponse:
    """Publish Instagram Story"""
    post = InstagramPost(
        media_urls=[media_url],
        caption="",  # Stories don't have captions
        media_type=MediaType.STORIES,
        scheduled_publish_time=scheduled_time
    )
    return publisher.publish_post(post)


def publish_carousel(publisher: InstagramPublisher, media_urls: List[str], caption: str,
                     scheduled_time: Optional[datetime] = None) -> InstagramResponse:
    """Publish carousel post with multiple images/videos"""
    post = InstagramPost(
        media_urls=media_urls,
        caption=caption,
        media_type=MediaType.CAROUSEL,
        scheduled_publish_time=scheduled_time
    )
    return publisher.publish_post(post)


def schedule_post(publisher: InstagramPublisher, post: InstagramPost, 
                  publish_time: datetime) -> InstagramResponse:
    """Schedule post for future publication"""
    post.scheduled_publish_time = publish_time
    return publisher.publish_post(post)


# Example usage and authentication setup
def setup_instagram_auth() -> Tuple[str, str]:
    """
    Setup Instagram authentication
    
    Returns:
        Tuple of (access_token, page_id)
        
    Instructions:
    1. Go to https://developers.facebook.com/
    2. Create a new app or use existing one
    3. Add Instagram Graph API product
    4. Get Page Access Token with required permissions:
       - instagram_basic
       - instagram_content_publish
       - pages_read_engagement
    5. Get your Facebook Page ID
    6. Set environment variables or return values directly
    """
    access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    page_id = os.getenv("FACEBOOK_PAGE_ID")
    
    if not access_token or not page_id:
        raise ValueError(
            "Please set INSTAGRAM_ACCESS_TOKEN and FACEBOOK_PAGE_ID environment variables. "
            "See setup_instagram_auth() docstring for detailed instructions."
        )
    
    return access_token, page_id


# Example usage
if __name__ == "__main__":
    # Setup authentication
    try:
        access_token, page_id = setup_instagram_auth()
        publisher = create_instagram_publisher(access_token, page_id)
        
        # Example: Publish an image post
        response = publish_image_post(
            publisher=publisher,
            image_url="https://example.com/image.jpg",
            caption="Check out this amazing image! #instagram #photo",
            alt_text="A beautiful landscape photo"
        )
        
        if response.success:
            print(f"Post published successfully! Media ID: {response.media_id}")
        else:
            print(f"Failed to publish post: {response.error_message}")
            
    except ValueError as e:
        print(f"Authentication error: {e}")