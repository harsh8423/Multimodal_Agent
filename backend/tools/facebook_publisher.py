"""
Facebook Publishing Tool

This tool provides functional programming interface for publishing content to Facebook
using the official Facebook Graph API. Supports text posts, images, videos, carousels,
and scheduling.

Authentication Requirements:
- Facebook Developer Account
- Facebook App with Graph API access
- Facebook Page access
- Required permissions: pages_manage_posts, pages_read_engagement, pages_show_list

Setup Instructions:
1. Go to https://developers.facebook.com/
2. Create a new app or use existing one
3. Add Facebook Login product
4. Get Page Access Token with required permissions
5. Set environment variables: FACEBOOK_ACCESS_TOKEN, FACEBOOK_PAGE_ID
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum


class PostType(Enum):
    """Facebook post types"""
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    CAROUSEL = "CAROUSEL"
    LINK = "LINK"


class PrivacyStatus(Enum):
    """Facebook post privacy status"""
    PUBLIC = "PUBLIC"
    FRIENDS = "FRIENDS"
    CUSTOM = "CUSTOM"


@dataclass
class FacebookPost:
    """Data class for Facebook post content"""
    message: str
    post_type: PostType
    media_urls: Optional[List[str]] = None
    link_url: Optional[str] = None
    link_caption: Optional[str] = None
    link_description: Optional[str] = None
    privacy_status: PrivacyStatus = PrivacyStatus.PUBLIC
    scheduled_publish_time: Optional[datetime] = None
    place_id: Optional[str] = None
    tags: Optional[List[str]] = None


@dataclass
class FacebookResponse:
    """Response from Facebook API"""
    success: bool
    post_id: Optional[str] = None
    error_message: Optional[str] = None


class FacebookPublisher:
    """Functional Facebook publishing tool"""
    
    def __init__(self, access_token: str, page_id: str):
        """
        Initialize Facebook publisher
        
        Args:
            access_token: Facebook Page access token
            page_id: Facebook Page ID
        """
        self.access_token = access_token
        self.page_id = page_id
        self.base_url = "https://graph.facebook.com/v23.0"
    
    def _make_request(self, method: str, url: str, data: Optional[Dict] = None,
                     files: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict:
        """Make HTTP request to Facebook API"""
        headers = {
            "Authorization": f"Bearer {self.access_token}",
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
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            try:
                error_data = response.json()
                return {"error": error_data}
            except:
                return {"error": {"message": str(e)}}
    
    def _upload_photo(self, photo_url: str, caption: str = "") -> Optional[str]:
        """Upload photo to Facebook"""
        url = f"{self.base_url}/{self.page_id}/photos"
        
        data = {
            "access_token": self.access_token,
            "url": photo_url,
            "caption": caption
        }
        
        response = self._make_request("POST", url, data)
        
        if "error" in response:
            return None
        
        return response.get("id")
    
    def _upload_video(self, video_url: str, description: str = "") -> Optional[str]:
        """Upload video to Facebook"""
        url = f"{self.base_url}/{self.page_id}/videos"
        
        data = {
            "access_token": self.access_token,
            "file_url": video_url,
            "description": description
        }
        
        response = self._make_request("POST", url, data)
        
        if "error" in response:
            return None
        
        return response.get("id")
    
    def _create_text_post(self, post: FacebookPost) -> FacebookResponse:
        """Create text-only post"""
        url = f"{self.base_url}/{self.page_id}/feed"
        
        data = {
            "access_token": self.access_token,
            "message": post.message
        }
        
        if post.privacy_status != PrivacyStatus.PUBLIC:
            data["privacy"] = {"value": post.privacy_status.value}
        
        if post.place_id:
            data["place"] = post.place_id
        
        if post.scheduled_publish_time:
            data["scheduled_publish_time"] = int(post.scheduled_publish_time.timestamp())
            data["published"] = False
        
        response = self._make_request("POST", url, data)
        
        if "error" in response:
            return FacebookResponse(
                success=False,
                error_message=response["error"].get("message", "Unknown error")
            )
        
        post_id = response.get("id")
        return FacebookResponse(success=True, post_id=post_id)
    
    def _create_image_post(self, post: FacebookPost) -> FacebookResponse:
        """Create image post"""
        if not post.media_urls:
            return FacebookResponse(success=False, error_message="No image URL provided")
        
        # Upload photo
        photo_id = self._upload_photo(post.media_urls[0], post.message)
        if not photo_id:
            return FacebookResponse(success=False, error_message="Failed to upload photo")
        
        url = f"{self.base_url}/{self.page_id}/feed"
        
        data = {
            "access_token": self.access_token,
            "message": post.message,
            "attached_media": [{"media_fbid": photo_id}]
        }
        
        if post.privacy_status != PrivacyStatus.PUBLIC:
            data["privacy"] = {"value": post.privacy_status.value}
        
        if post.place_id:
            data["place"] = post.place_id
        
        if post.scheduled_publish_time:
            data["scheduled_publish_time"] = int(post.scheduled_publish_time.timestamp())
            data["published"] = False
        
        response = self._make_request("POST", url, data)
        
        if "error" in response:
            return FacebookResponse(
                success=False,
                error_message=response["error"].get("message", "Unknown error")
            )
        
        post_id = response.get("id")
        return FacebookResponse(success=True, post_id=post_id)
    
    def _create_video_post(self, post: FacebookPost) -> FacebookResponse:
        """Create video post"""
        if not post.media_urls:
            return FacebookResponse(success=False, error_message="No video URL provided")
        
        # Upload video
        video_id = self._upload_video(post.media_urls[0], post.message)
        if not video_id:
            return FacebookResponse(success=False, error_message="Failed to upload video")
        
        url = f"{self.base_url}/{self.page_id}/feed"
        
        data = {
            "access_token": self.access_token,
            "message": post.message,
            "attached_media": [{"media_fbid": video_id}]
        }
        
        if post.privacy_status != PrivacyStatus.PUBLIC:
            data["privacy"] = {"value": post.privacy_status.value}
        
        if post.place_id:
            data["place"] = post.place_id
        
        if post.scheduled_publish_time:
            data["scheduled_publish_time"] = int(post.scheduled_publish_time.timestamp())
            data["published"] = False
        
        response = self._make_request("POST", url, data)
        
        if "error" in response:
            return FacebookResponse(
                success=False,
                error_message=response["error"].get("message", "Unknown error")
            )
        
        post_id = response.get("id")
        return FacebookResponse(success=True, post_id=post_id)
    
    def _create_carousel_post(self, post: FacebookPost) -> FacebookResponse:
        """Create carousel post with multiple photos"""
        if not post.media_urls or len(post.media_urls) < 2:
            return FacebookResponse(success=False, error_message="Carousel requires at least 2 photos")
        
        # Upload all photos
        photo_ids = []
        for photo_url in post.media_urls:
            photo_id = self._upload_photo(photo_url)
            if not photo_id:
                return FacebookResponse(success=False, error_message=f"Failed to upload photo: {photo_url}")
            photo_ids.append(photo_id)
        
        url = f"{self.base_url}/{self.page_id}/feed"
        
        data = {
            "access_token": self.access_token,
            "message": post.message,
            "attached_media": [{"media_fbid": photo_id} for photo_id in photo_ids]
        }
        
        if post.privacy_status != PrivacyStatus.PUBLIC:
            data["privacy"] = {"value": post.privacy_status.value}
        
        if post.place_id:
            data["place"] = post.place_id
        
        if post.scheduled_publish_time:
            data["scheduled_publish_time"] = int(post.scheduled_publish_time.timestamp())
            data["published"] = False
        
        response = self._make_request("POST", url, data)
        
        if "error" in response:
            return FacebookResponse(
                success=False,
                error_message=response["error"].get("message", "Unknown error")
            )
        
        post_id = response.get("id")
        return FacebookResponse(success=True, post_id=post_id)
    
    def _create_link_post(self, post: FacebookPost) -> FacebookResponse:
        """Create link post"""
        if not post.link_url:
            return FacebookResponse(success=False, error_message="No link URL provided")
        
        url = f"{self.base_url}/{self.page_id}/feed"
        
        data = {
            "access_token": self.access_token,
            "message": post.message,
            "link": post.link_url
        }
        
        if post.link_caption:
            data["caption"] = post.link_caption
        if post.link_description:
            data["description"] = post.link_description
        
        if post.privacy_status != PrivacyStatus.PUBLIC:
            data["privacy"] = {"value": post.privacy_status.value}
        
        if post.place_id:
            data["place"] = post.place_id
        
        if post.scheduled_publish_time:
            data["scheduled_publish_time"] = int(post.scheduled_publish_time.timestamp())
            data["published"] = False
        
        response = self._make_request("POST", url, data)
        
        if "error" in response:
            return FacebookResponse(
                success=False,
                error_message=response["error"].get("message", "Unknown error")
            )
        
        post_id = response.get("id")
        return FacebookResponse(success=True, post_id=post_id)
    
    def publish_post(self, post: FacebookPost) -> FacebookResponse:
        """
        Publish content to Facebook
        
        Args:
            post: FacebookPost object containing content details
            
        Returns:
            FacebookResponse with success status and post ID
        """
        if post.post_type == PostType.TEXT:
            return self._create_text_post(post)
        elif post.post_type == PostType.IMAGE:
            return self._create_image_post(post)
        elif post.post_type == PostType.VIDEO:
            return self._create_video_post(post)
        elif post.post_type == PostType.CAROUSEL:
            return self._create_carousel_post(post)
        elif post.post_type == PostType.LINK:
            return self._create_link_post(post)
        else:
            return FacebookResponse(
                success=False,
                error_message=f"Unsupported post type: {post.post_type}"
            )
    
    def get_post(self, post_id: str) -> Dict:
        """Get post information"""
        url = f"{self.base_url}/{post_id}"
        params = {
            "access_token": self.access_token,
            "fields": "id,message,created_time,updated_time,likes.summary(true),comments.summary(true),shares"
        }
        response = self._make_request("GET", url, params=params)
        return response
    
    def delete_post(self, post_id: str) -> Dict:
        """Delete a post"""
        url = f"{self.base_url}/{post_id}"
        params = {"access_token": self.access_token}
        response = self._make_request("DELETE", url, params=params)
        return response
    
    def get_page_info(self) -> Dict:
        """Get page information"""
        url = f"{self.base_url}/{self.page_id}"
        params = {
            "access_token": self.access_token,
            "fields": "id,name,username,followers_count,fan_count,posts"
        }
        response = self._make_request("GET", url, params=params)
        return response
    
    def get_page_posts(self, limit: int = 25) -> Dict:
        """Get page posts"""
        url = f"{self.base_url}/{self.page_id}/posts"
        params = {
            "access_token": self.access_token,
            "fields": "id,message,created_time,updated_time,likes.summary(true),comments.summary(true),shares",
            "limit": limit
        }
        response = self._make_request("GET", url, params=params)
        return response
    
    def get_scheduled_posts(self) -> Dict:
        """Get scheduled posts"""
        url = f"{self.base_url}/{self.page_id}/posts"
        params = {
            "access_token": self.access_token,
            "fields": "id,message,created_time,scheduled_publish_time",
            "is_published": "false"
        }
        response = self._make_request("GET", url, params=params)
        return response


# Functional interface functions
def create_facebook_publisher(access_token: str, page_id: str) -> FacebookPublisher:
    """Create Facebook publisher instance"""
    return FacebookPublisher(access_token, page_id)


def publish_text_post(publisher: FacebookPublisher, message: str,
                     privacy_status: PrivacyStatus = PrivacyStatus.PUBLIC,
                     scheduled_time: Optional[datetime] = None) -> FacebookResponse:
    """Publish text-only post"""
    post = FacebookPost(
        message=message,
        post_type=PostType.TEXT,
        privacy_status=privacy_status,
        scheduled_publish_time=scheduled_time
    )
    return publisher.publish_post(post)


def publish_image_post(publisher: FacebookPublisher, image_url: str, message: str,
                      privacy_status: PrivacyStatus = PrivacyStatus.PUBLIC,
                      scheduled_time: Optional[datetime] = None) -> FacebookResponse:
    """Publish image post"""
    post = FacebookPost(
        message=message,
        post_type=PostType.IMAGE,
        media_urls=[image_url],
        privacy_status=privacy_status,
        scheduled_publish_time=scheduled_time
    )
    return publisher.publish_post(post)


def publish_video_post(publisher: FacebookPublisher, video_url: str, message: str,
                       privacy_status: PrivacyStatus = PrivacyStatus.PUBLIC,
                       scheduled_time: Optional[datetime] = None) -> FacebookResponse:
    """Publish video post"""
    post = FacebookPost(
        message=message,
        post_type=PostType.VIDEO,
        media_urls=[video_url],
        privacy_status=privacy_status,
        scheduled_publish_time=scheduled_time
    )
    return publisher.publish_post(post)


def publish_carousel_post(publisher: FacebookPublisher, image_urls: List[str], message: str,
                          privacy_status: PrivacyStatus = PrivacyStatus.PUBLIC,
                          scheduled_time: Optional[datetime] = None) -> FacebookResponse:
    """Publish carousel post with multiple images"""
    post = FacebookPost(
        message=message,
        post_type=PostType.CAROUSEL,
        media_urls=image_urls,
        privacy_status=privacy_status,
        scheduled_publish_time=scheduled_time
    )
    return publisher.publish_post(post)


def publish_link_post(publisher: FacebookPublisher, link_url: str, message: str,
                     caption: Optional[str] = None, description: Optional[str] = None,
                     privacy_status: PrivacyStatus = PrivacyStatus.PUBLIC,
                     scheduled_time: Optional[datetime] = None) -> FacebookResponse:
    """Publish link post"""
    post = FacebookPost(
        message=message,
        post_type=PostType.LINK,
        link_url=link_url,
        link_caption=caption,
        link_description=description,
        privacy_status=privacy_status,
        scheduled_publish_time=scheduled_time
    )
    return publisher.publish_post(post)


def schedule_post(publisher: FacebookPublisher, post: FacebookPost, 
                  publish_time: datetime) -> FacebookResponse:
    """Schedule post for future publication"""
    post.scheduled_publish_time = publish_time
    return publisher.publish_post(post)


def publish_short_video(publisher: FacebookPublisher, video_url: str, message: str,
                        privacy_status: PrivacyStatus = PrivacyStatus.PUBLIC,
                        scheduled_time: Optional[datetime] = None) -> FacebookResponse:
    """Publish short video (like Facebook Reels)"""
    post = FacebookPost(
        message=message,
        post_type=PostType.VIDEO,
        media_urls=[video_url],
        privacy_status=privacy_status,
        scheduled_publish_time=scheduled_time
    )
    return publisher.publish_post(post)


# Authentication setup functions
def setup_facebook_auth() -> Tuple[str, str]:
    """
    Setup Facebook authentication
    
    Returns:
        Tuple of (access_token, page_id)
        
    Instructions:
    1. Go to https://developers.facebook.com/
    2. Create a new app or use existing one
    3. Add Facebook Login product
    4. Get Page Access Token with required permissions:
       - pages_manage_posts
       - pages_read_engagement
       - pages_show_list
    5. Get your Facebook Page ID
    6. Set environment variables or return values directly
    """
    access_token = os.getenv("FACEBOOK_ACCESS_TOKEN")
    page_id = os.getenv("FACEBOOK_PAGE_ID")
    
    if not access_token or not page_id:
        raise ValueError(
            "Please set FACEBOOK_ACCESS_TOKEN and FACEBOOK_PAGE_ID environment variables. "
            "See setup_facebook_auth() docstring for detailed instructions."
        )
    
    return access_token, page_id


def get_facebook_oauth_url(app_id: str, redirect_uri: str, state: str = "random_state") -> str:
    """
    Generate Facebook OAuth 2.0 authorization URL
    
    Args:
        app_id: Facebook App ID
        redirect_uri: Redirect URI
        state: State parameter for security
        
    Returns:
        Authorization URL for user to visit
    """
    scope = "pages_manage_posts,pages_read_engagement,pages_show_list"
    auth_url = (
        f"https://www.facebook.com/v23.0/dialog/oauth?"
        f"client_id={app_id}&"
        f"redirect_uri={redirect_uri}&"
        f"scope={scope}&"
        f"state={state}&"
        f"response_type=code"
    )
    return auth_url


def exchange_facebook_code_for_token(app_id: str, app_secret: str, code: str,
                                     redirect_uri: str) -> Dict:
    """
    Exchange Facebook authorization code for access token
    
    Args:
        app_id: Facebook App ID
        app_secret: Facebook App Secret
        code: Authorization code from OAuth flow
        redirect_uri: Redirect URI used in authorization
        
    Returns:
        Dictionary containing access_token
    """
    url = "https://graph.facebook.com/v23.0/oauth/access_token"
    data = {
        "client_id": app_id,
        "client_secret": app_secret,
        "redirect_uri": redirect_uri,
        "code": code
    }
    
    try:
        response = requests.get(url, params=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def get_page_access_token(user_access_token: str, page_id: str) -> Dict:
    """
    Get page access token from user access token
    
    Args:
        user_access_token: User access token
        page_id: Facebook Page ID
        
    Returns:
        Dictionary containing page access token
    """
    url = f"https://graph.facebook.com/v23.0/{page_id}"
    params = {
        "fields": "access_token",
        "access_token": user_access_token
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


# Example usage
if __name__ == "__main__":
    # Setup authentication
    try:
        access_token, page_id = setup_facebook_auth()
        publisher = create_facebook_publisher(access_token, page_id)
        
        # Example: Publish a text post
        response = publish_text_post(
            publisher=publisher,
            message="Excited to share this amazing update with our community! #Facebook #SocialMedia"
        )
        
        if response.success:
            print(f"Post published successfully! Post ID: {response.post_id}")
        else:
            print(f"Failed to publish post: {response.error_message}")
            
    except ValueError as e:
        print(f"Authentication error: {e}")