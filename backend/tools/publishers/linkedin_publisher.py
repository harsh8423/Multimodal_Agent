"""
LinkedIn Publishing Tool

This tool provides functional programming interface for publishing content to LinkedIn
using the official LinkedIn Marketing API. Supports text posts, images, videos, articles, 
carousels, and scheduling.

Authentication Requirements:
- LinkedIn Developer Account
- LinkedIn App with Marketing Developer Platform access
- Required permissions: w_organization_social, w_member_social
- Organization or personal LinkedIn account

Setup Instructions:
1. Go to https://www.linkedin.com/developers/
2. Create a new app or use existing one
3. Request Marketing Developer Platform access
4. Get OAuth 2.0 credentials
5. Set environment variables: LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET, LINKEDIN_ACCESS_TOKEN
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum


class ContentType(Enum):
    """LinkedIn content types"""
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    ARTICLE = "ARTICLE"
    CAROUSEL = "CAROUSEL"
    MULTI_IMAGE = "MULTI_IMAGE"
    POLL = "POLL"


class Visibility(Enum):
    """LinkedIn post visibility"""
    PUBLIC = "PUBLIC"
    CONNECTIONS = "CONNECTIONS"


class DistributionType(Enum):
    """LinkedIn distribution types"""
    MAIN_FEED = "MAIN_FEED"
    SPONSORED = "SPONSORED"


@dataclass
class LinkedInPost:
    """Data class for LinkedIn post content"""
    commentary: str
    content_type: ContentType
    media_urls: Optional[List[str]] = None
    article_url: Optional[str] = None
    poll_question: Optional[str] = None
    poll_options: Optional[List[str]] = None
    visibility: Visibility = Visibility.PUBLIC
    scheduled_publish_time: Optional[datetime] = None
    alt_text: Optional[str] = None
    content_landing_page: Optional[str] = None
    call_to_action_label: Optional[str] = None


@dataclass
class LinkedInResponse:
    """Response from LinkedIn API"""
    success: bool
    post_id: Optional[str] = None
    error_message: Optional[str] = None


class LinkedInPublisher:
    """Functional LinkedIn publishing tool"""
    
    def __init__(self, access_token: str, organization_id: Optional[str] = None):
        """
        Initialize LinkedIn publisher
        
        Args:
            access_token: LinkedIn OAuth 2.0 access token
            organization_id: LinkedIn organization ID (for organization posts)
        """
        self.access_token = access_token
        self.organization_id = organization_id
        self.base_url = "https://api.linkedin.com/rest"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "LinkedIn-Version": "202412",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json"
        }
    
    def _make_request(self, method: str, url: str, data: Optional[Dict] = None,
                     files: Optional[Dict] = None) -> Dict:
        """Make HTTP request to LinkedIn API"""
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, params=data)
            elif method.upper() == "POST":
                if files:
                    headers = self.headers.copy()
                    headers.pop("Content-Type")  # Let requests set multipart boundary
                    response = requests.post(url, headers=headers, data=data, files=files)
                else:
                    response = requests.post(url, headers=self.headers, json=data)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=self.headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=self.headers)
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
    
    def _upload_image(self, image_url: str) -> Optional[str]:
        """Upload image to LinkedIn and get URN"""
        # Initialize image upload
        init_url = f"{self.base_url}/images?action=initializeUpload"
        init_data = {
            "initializeUploadRequest": {
                "owner": f"urn:li:organization:{self.organization_id}" if self.organization_id else "urn:li:person:me"
            }
        }
        
        init_response = self._make_request("POST", init_url, init_data)
        if "error" in init_response:
            return None
        
        upload_url = init_response["value"]["uploadUrl"]
        image_urn = init_response["value"]["image"]
        
        # Upload image file
        try:
            image_response = requests.get(image_url)
            image_response.raise_for_status()
            
            upload_response = requests.post(
                upload_url,
                files={"file": image_response.content},
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            upload_response.raise_for_status()
            
            return image_urn
            
        except requests.exceptions.RequestException:
            return None
    
    def _upload_video(self, video_url: str) -> Optional[str]:
        """Upload video to LinkedIn and get URN"""
        # Initialize video upload
        init_url = f"{self.base_url}/videos?action=initializeUpload"
        init_data = {
            "initializeUploadRequest": {
                "owner": f"urn:li:organization:{self.organization_id}" if self.organization_id else "urn:li:person:me"
            }
        }
        
        init_response = self._make_request("POST", init_url, init_data)
        if "error" in init_response:
            return None
        
        upload_url = init_response["value"]["uploadUrl"]
        video_urn = init_response["value"]["video"]
        
        # Upload video file
        try:
            video_response = requests.get(video_url)
            video_response.raise_for_status()
            
            upload_response = requests.post(
                upload_url,
                files={"file": video_response.content},
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            upload_response.raise_for_status()
            
            return video_urn
            
        except requests.exceptions.RequestException:
            return None
    
    def _create_text_post(self, post: LinkedInPost) -> LinkedInResponse:
        """Create text-only post"""
        url = f"{self.base_url}/posts"
        
        data = {
            "author": f"urn:li:organization:{self.organization_id}" if self.organization_id else "urn:li:person:me",
            "commentary": post.commentary,
            "visibility": post.visibility.value,
            "distribution": {
                "feedDistribution": DistributionType.MAIN_FEED.value,
                "targetEntities": [],
                "thirdPartyDistributionChannels": []
            },
            "lifecycleState": "PUBLISHED"
        }
        
        if post.scheduled_publish_time:
            data["scheduledAt"] = int(post.scheduled_publish_time.timestamp() * 1000)
            data["lifecycleState"] = "SCHEDULED"
        
        response = self._make_request("POST", url, data)
        
        if "error" in response:
            return LinkedInResponse(
                success=False,
                error_message=response["error"].get("message", "Unknown error")
            )
        
        post_id = response.get("id")
        return LinkedInResponse(success=True, post_id=post_id)
    
    def _create_image_post(self, post: LinkedInPost) -> LinkedInResponse:
        """Create image post"""
        if not post.media_urls:
            return LinkedInResponse(success=False, error_message="No image URL provided")
        
        # Upload image
        image_urn = self._upload_image(post.media_urls[0])
        if not image_urn:
            return LinkedInResponse(success=False, error_message="Failed to upload image")
        
        url = f"{self.base_url}/posts"
        
        data = {
            "author": f"urn:li:organization:{self.organization_id}" if self.organization_id else "urn:li:person:me",
            "commentary": post.commentary,
            "visibility": post.visibility.value,
            "distribution": {
                "feedDistribution": DistributionType.MAIN_FEED.value,
                "targetEntities": [],
                "thirdPartyDistributionChannels": []
            },
            "content": {
                "media": {
                    "id": image_urn,
                    "altText": post.alt_text or ""
                }
            },
            "lifecycleState": "PUBLISHED"
        }
        
        if post.content_landing_page:
            data["contentLandingPage"] = post.content_landing_page
        if post.call_to_action_label:
            data["contentCallToActionLabel"] = post.call_to_action_label
        
        if post.scheduled_publish_time:
            data["scheduledAt"] = int(post.scheduled_publish_time.timestamp() * 1000)
            data["lifecycleState"] = "SCHEDULED"
        
        response = self._make_request("POST", url, data)
        
        if "error" in response:
            return LinkedInResponse(
                success=False,
                error_message=response["error"].get("message", "Unknown error")
            )
        
        post_id = response.get("id")
        return LinkedInResponse(success=True, post_id=post_id)
    
    def _create_video_post(self, post: LinkedInPost) -> LinkedInResponse:
        """Create video post"""
        if not post.media_urls:
            return LinkedInResponse(success=False, error_message="No video URL provided")
        
        # Upload video
        video_urn = self._upload_video(post.media_urls[0])
        if not video_urn:
            return LinkedInResponse(success=False, error_message="Failed to upload video")
        
        url = f"{self.base_url}/posts"
        
        data = {
            "author": f"urn:li:organization:{self.organization_id}" if self.organization_id else "urn:li:person:me",
            "commentary": post.commentary,
            "visibility": post.visibility.value,
            "distribution": {
                "feedDistribution": DistributionType.MAIN_FEED.value,
                "targetEntities": [],
                "thirdPartyDistributionChannels": []
            },
            "content": {
                "media": {
                    "id": video_urn,
                    "altText": post.alt_text or ""
                }
            },
            "lifecycleState": "PUBLISHED"
        }
        
        if post.content_landing_page:
            data["contentLandingPage"] = post.content_landing_page
        if post.call_to_action_label:
            data["contentCallToActionLabel"] = post.call_to_action_label
        
        if post.scheduled_publish_time:
            data["scheduledAt"] = int(post.scheduled_publish_time.timestamp() * 1000)
            data["lifecycleState"] = "SCHEDULED"
        
        response = self._make_request("POST", url, data)
        
        if "error" in response:
            return LinkedInResponse(
                success=False,
                error_message=response["error"].get("message", "Unknown error")
            )
        
        post_id = response.get("id")
        return LinkedInResponse(success=True, post_id=post_id)
    
    def _create_article_post(self, post: LinkedInPost) -> LinkedInResponse:
        """Create article post"""
        if not post.article_url:
            return LinkedInResponse(success=False, error_message="No article URL provided")
        
        url = f"{self.base_url}/posts"
        
        data = {
            "author": f"urn:li:organization:{self.organization_id}" if self.organization_id else "urn:li:person:me",
            "commentary": post.commentary,
            "visibility": post.visibility.value,
            "distribution": {
                "feedDistribution": DistributionType.MAIN_FEED.value,
                "targetEntities": [],
                "thirdPartyDistributionChannels": []
            },
            "content": {
                "article": {
                    "source": post.article_url
                }
            },
            "lifecycleState": "PUBLISHED"
        }
        
        if post.scheduled_publish_time:
            data["scheduledAt"] = int(post.scheduled_publish_time.timestamp() * 1000)
            data["lifecycleState"] = "SCHEDULED"
        
        response = self._make_request("POST", url, data)
        
        if "error" in response:
            return LinkedInResponse(
                success=False,
                error_message=response["error"].get("message", "Unknown error")
            )
        
        post_id = response.get("id")
        return LinkedInResponse(success=True, post_id=post_id)
    
    def _create_carousel_post(self, post: LinkedInPost) -> LinkedInResponse:
        """Create carousel post (sponsored only)"""
        if not post.media_urls or len(post.media_urls) < 2:
            return LinkedInResponse(success=False, error_message="Carousel requires at least 2 media items")
        
        # Upload all images/videos
        media_urns = []
        for media_url in post.media_urls:
            if media_url.lower().endswith(('.jpg', '.jpeg', '.png')):
                media_urn = self._upload_image(media_url)
            else:
                media_urn = self._upload_video(media_url)
            
            if not media_urn:
                return LinkedInResponse(success=False, error_message=f"Failed to upload media: {media_url}")
            media_urns.append(media_urn)
        
        url = f"{self.base_url}/posts"
        
        data = {
            "author": f"urn:li:organization:{self.organization_id}" if self.organization_id else "urn:li:person:me",
            "commentary": post.commentary,
            "visibility": post.visibility.value,
            "distribution": {
                "feedDistribution": DistributionType.SPONSORED.value,  # Carousel requires sponsored
                "targetEntities": [],
                "thirdPartyDistributionChannels": []
            },
            "content": {
                "carousel": {
                    "cards": [{"media": {"id": urn}} for urn in media_urns]
                }
            },
            "lifecycleState": "PUBLISHED"
        }
        
        if post.scheduled_publish_time:
            data["scheduledAt"] = int(post.scheduled_publish_time.timestamp() * 1000)
            data["lifecycleState"] = "SCHEDULED"
        
        response = self._make_request("POST", url, data)
        
        if "error" in response:
            return LinkedInResponse(
                success=False,
                error_message=response["error"].get("message", "Unknown error")
            )
        
        post_id = response.get("id")
        return LinkedInResponse(success=True, post_id=post_id)
    
    def _create_poll_post(self, post: LinkedInPost) -> LinkedInResponse:
        """Create poll post"""
        if not post.poll_question or not post.poll_options or len(post.poll_options) < 2:
            return LinkedInResponse(success=False, error_message="Poll requires question and at least 2 options")
        
        url = f"{self.base_url}/posts"
        
        data = {
            "author": f"urn:li:organization:{self.organization_id}" if self.organization_id else "urn:li:person:me",
            "commentary": post.commentary,
            "visibility": post.visibility.value,
            "distribution": {
                "feedDistribution": DistributionType.MAIN_FEED.value,
                "targetEntities": [],
                "thirdPartyDistributionChannels": []
            },
            "content": {
                "poll": {
                    "question": post.poll_question,
                    "options": [{"text": option} for option in post.poll_options]
                }
            },
            "lifecycleState": "PUBLISHED"
        }
        
        if post.scheduled_publish_time:
            data["scheduledAt"] = int(post.scheduled_publish_time.timestamp() * 1000)
            data["lifecycleState"] = "SCHEDULED"
        
        response = self._make_request("POST", url, data)
        
        if "error" in response:
            return LinkedInResponse(
                success=False,
                error_message=response["error"].get("message", "Unknown error")
            )
        
        post_id = response.get("id")
        return LinkedInResponse(success=True, post_id=post_id)
    
    def publish_post(self, post: LinkedInPost) -> LinkedInResponse:
        """
        Publish content to LinkedIn
        
        Args:
            post: LinkedInPost object containing content details
            
        Returns:
            LinkedInResponse with success status and post ID
        """
        if post.content_type == ContentType.TEXT:
            return self._create_text_post(post)
        elif post.content_type == ContentType.IMAGE:
            return self._create_image_post(post)
        elif post.content_type == ContentType.VIDEO:
            return self._create_video_post(post)
        elif post.content_type == ContentType.ARTICLE:
            return self._create_article_post(post)
        elif post.content_type == ContentType.CAROUSEL:
            return self._create_carousel_post(post)
        elif post.content_type == ContentType.POLL:
            return self._create_poll_post(post)
        else:
            return LinkedInResponse(
                success=False,
                error_message=f"Unsupported content type: {post.content_type}"
            )
    
    def get_post(self, post_id: str) -> Dict:
        """Get post information"""
        url = f"{self.base_url}/posts/{post_id}"
        response = self._make_request("GET", url)
        return response
    
    def delete_post(self, post_id: str) -> Dict:
        """Delete a post"""
        url = f"{self.base_url}/posts/{post_id}"
        response = self._make_request("DELETE", url)
        return response
    
    def get_organization_info(self) -> Dict:
        """Get organization information"""
        if not self.organization_id:
            return {"error": {"message": "Organization ID not provided"}}
        
        url = f"{self.base_url}/organizations/{self.organization_id}"
        params = {
            "projection": "(id,name,vanityName,logoV2(original~:playableStreams))"
        }
        response = self._make_request("GET", url, params)
        return response


# Functional interface functions
def create_linkedin_publisher(access_token: str, organization_id: Optional[str] = None) -> LinkedInPublisher:
    """Create LinkedIn publisher instance"""
    return LinkedInPublisher(access_token, organization_id)


def publish_text_post(publisher: LinkedInPublisher, text: str,
                     visibility: Visibility = Visibility.PUBLIC,
                     scheduled_time: Optional[datetime] = None) -> LinkedInResponse:
    """Publish text-only post"""
    post = LinkedInPost(
        commentary=text,
        content_type=ContentType.TEXT,
        visibility=visibility,
        scheduled_publish_time=scheduled_time
    )
    return publisher.publish_post(post)


def publish_image_post(publisher: LinkedInPublisher, image_url: str, caption: str,
                      alt_text: Optional[str] = None, visibility: Visibility = Visibility.PUBLIC,
                      scheduled_time: Optional[datetime] = None) -> LinkedInResponse:
    """Publish image post"""
    post = LinkedInPost(
        commentary=caption,
        content_type=ContentType.IMAGE,
        media_urls=[image_url],
        alt_text=alt_text,
        visibility=visibility,
        scheduled_publish_time=scheduled_time
    )
    return publisher.publish_post(post)


def publish_video_post(publisher: LinkedInPublisher, video_url: str, caption: str,
                       alt_text: Optional[str] = None, visibility: Visibility = Visibility.PUBLIC,
                       scheduled_time: Optional[datetime] = None) -> LinkedInResponse:
    """Publish video post"""
    post = LinkedInPost(
        commentary=caption,
        content_type=ContentType.VIDEO,
        media_urls=[video_url],
        alt_text=alt_text,
        visibility=visibility,
        scheduled_publish_time=scheduled_time
    )
    return publisher.publish_post(post)


def publish_article_post(publisher: LinkedInPublisher, article_url: str, caption: str,
                         visibility: Visibility = Visibility.PUBLIC,
                         scheduled_time: Optional[datetime] = None) -> LinkedInResponse:
    """Publish article post"""
    post = LinkedInPost(
        commentary=caption,
        content_type=ContentType.ARTICLE,
        article_url=article_url,
        visibility=visibility,
        scheduled_publish_time=scheduled_time
    )
    return publisher.publish_post(post)


def publish_carousel_post(publisher: LinkedInPublisher, media_urls: List[str], caption: str,
                          visibility: Visibility = Visibility.PUBLIC,
                          scheduled_time: Optional[datetime] = None) -> LinkedInResponse:
    """Publish carousel post (sponsored only)"""
    post = LinkedInPost(
        commentary=caption,
        content_type=ContentType.CAROUSEL,
        media_urls=media_urls,
        visibility=visibility,
        scheduled_publish_time=scheduled_time
    )
    return publisher.publish_post(post)


def publish_poll_post(publisher: LinkedInPublisher, question: str, options: List[str],
                     caption: str = "", visibility: Visibility = Visibility.PUBLIC,
                     scheduled_time: Optional[datetime] = None) -> LinkedInResponse:
    """Publish poll post"""
    post = LinkedInPost(
        commentary=caption,
        content_type=ContentType.POLL,
        poll_question=question,
        poll_options=options,
        visibility=visibility,
        scheduled_publish_time=scheduled_time
    )
    return publisher.publish_post(post)


def schedule_post(publisher: LinkedInPublisher, post: LinkedInPost, 
                  publish_time: datetime) -> LinkedInResponse:
    """Schedule post for future publication"""
    post.scheduled_publish_time = publish_time
    return publisher.publish_post(post)


# Authentication setup functions
def setup_linkedin_auth() -> Tuple[str, Optional[str]]:
    """
    Setup LinkedIn authentication
    
    Returns:
        Tuple of (access_token, organization_id)
        
    Instructions:
    1. Go to https://www.linkedin.com/developers/
    2. Create a new app or use existing one
    3. Request Marketing Developer Platform access
    4. Get OAuth 2.0 credentials
    5. Use OAuth 2.0 flow to get access token
    6. Get organization ID if posting on behalf of organization
    7. Set environment variables or return values directly
    """
    access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    organization_id = os.getenv("LINKEDIN_ORGANIZATION_ID")
    
    if not access_token:
        raise ValueError(
            "Please set LINKEDIN_ACCESS_TOKEN environment variable. "
            "See setup_linkedin_auth() docstring for detailed instructions."
        )
    
    return access_token, organization_id


def get_linkedin_oauth_url(client_id: str, redirect_uri: str, state: str = "random_state") -> str:
    """
    Generate LinkedIn OAuth 2.0 authorization URL
    
    Args:
        client_id: LinkedIn OAuth 2.0 client ID
        redirect_uri: Redirect URI
        state: State parameter for security
        
    Returns:
        Authorization URL for user to visit
    """
    scope = "w_organization_social w_member_social"
    auth_url = (
        f"https://www.linkedin.com/oauth/v2/authorization?"
        f"response_type=code&"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"state={state}&"
        f"scope={scope}"
    )
    return auth_url


def exchange_linkedin_code_for_token(client_id: str, client_secret: str, code: str,
                                    redirect_uri: str) -> Dict:
    """
    Exchange LinkedIn authorization code for access token
    
    Args:
        client_id: LinkedIn OAuth 2.0 client ID
        client_secret: LinkedIn OAuth 2.0 client secret
        code: Authorization code from OAuth flow
        redirect_uri: Redirect URI used in authorization
        
    Returns:
        Dictionary containing access_token
    """
    url = "https://www.linkedin.com/oauth/v2/accessToken"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
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
        access_token, organization_id = setup_linkedin_auth()
        publisher = create_linkedin_publisher(access_token, organization_id)
        
        # Example: Publish a text post
        response = publish_text_post(
            publisher=publisher,
            text="Excited to share this amazing update with my network! #LinkedIn #Networking"
        )
        
        if response.success:
            print(f"Post published successfully! Post ID: {response.post_id}")
        else:
            print(f"Failed to publish post: {response.error_message}")
            
    except ValueError as e:
        print(f"Authentication error: {e}")