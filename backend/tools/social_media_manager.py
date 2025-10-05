#!/usr/bin/env python3
"""
Social Media Publishing Example

This script demonstrates how to use all four social media publishing tools
to publish the same content across multiple platforms.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List

# Import all publisher tools
from instagram_publisher import (
    create_instagram_publisher, 
    publish_image_post as instagram_image_post,
    publish_video_post as instagram_video_post,
    publish_reel as instagram_reel,
    publish_carousel as instagram_carousel,
    setup_instagram_auth
)

from youtube_publisher import (
    create_youtube_publisher,
    publish_shorts_video,
    publish_video_post as youtube_video_post,
    setup_youtube_auth
)

from linkedin_publisher import (
    create_linkedin_publisher,
    publish_image_post as linkedin_image_post,
    publish_video_post as linkedin_video_post,
    publish_text_post as linkedin_text_post,
    setup_linkedin_auth
)

from facebook_publisher import (
    create_facebook_publisher,
    publish_image_post as facebook_image_post,
    publish_video_post as facebook_video_post,
    publish_text_post as facebook_text_post,
    setup_facebook_auth
)


class SocialMediaManager:
    """Manages publishing across multiple social media platforms"""
    
    def __init__(self):
        """Initialize all publishers"""
        self.publishers = {}
        self._setup_publishers()
    
    def _setup_publishers(self):
        """Setup all social media publishers"""
        try:
            # Instagram
            instagram_token, instagram_page_id = setup_instagram_auth()
            self.publishers['instagram'] = create_instagram_publisher(
                instagram_token, instagram_page_id
            )
            print("✅ Instagram publisher initialized")
        except Exception as e:
            print(f"❌ Instagram setup failed: {e}")
        
        try:
            # YouTube
            youtube_client_id, youtube_client_secret, youtube_refresh_token = setup_youtube_auth()
            self.publishers['youtube'] = create_youtube_publisher(
                youtube_client_id, youtube_client_secret, youtube_refresh_token
            )
            print("✅ YouTube publisher initialized")
        except Exception as e:
            print(f"❌ YouTube setup failed: {e}")
        
        try:
            # LinkedIn
            linkedin_token, linkedin_org_id = setup_linkedin_auth()
            self.publishers['linkedin'] = create_linkedin_publisher(
                linkedin_token, linkedin_org_id
            )
            print("✅ LinkedIn publisher initialized")
        except Exception as e:
            print(f"❌ LinkedIn setup failed: {e}")
        
        try:
            # Facebook
            facebook_token, facebook_page_id = setup_facebook_auth()
            self.publishers['facebook'] = create_facebook_publisher(
                facebook_token, facebook_page_id
            )
            print("✅ Facebook publisher initialized")
        except Exception as e:
            print(f"❌ Facebook setup failed: {e}")
    
    def publish_image_everywhere(self, image_url: str, caption: str, 
                                platforms: List[str] = None) -> Dict[str, Dict]:
        """
        Publish image to multiple platforms
        
        Args:
            image_url: URL of the image to publish
            caption: Caption for the post
            platforms: List of platforms to publish to (default: all available)
            
        Returns:
            Dictionary with results for each platform
        """
        if platforms is None:
            platforms = list(self.publishers.keys())
        
        results = {}
        
        for platform in platforms:
            if platform not in self.publishers:
                results[platform] = {"success": False, "error": "Publisher not available"}
                continue
            
            try:
                if platform == 'instagram':
                    response = instagram_image_post(
                        self.publishers[platform], image_url, caption
                    )
                elif platform == 'linkedin':
                    response = linkedin_image_post(
                        self.publishers[platform], image_url, caption
                    )
                elif platform == 'facebook':
                    response = facebook_image_post(
                        self.publishers[platform], image_url, caption
                    )
                else:
                    results[platform] = {"success": False, "error": "Image posting not supported"}
                    continue
                
                results[platform] = {
                    "success": response.success,
                    "post_id": getattr(response, 'post_id', None) or getattr(response, 'media_id', None),
                    "error": getattr(response, 'error_message', None)
                }
                
            except Exception as e:
                results[platform] = {"success": False, "error": str(e)}
        
        return results
    
    def publish_video_everywhere(self, video_url: str, caption: str,
                                platforms: List[str] = None) -> Dict[str, Dict]:
        """
        Publish video to multiple platforms
        
        Args:
            video_url: URL of the video to publish
            caption: Caption for the post
            platforms: List of platforms to publish to (default: all available)
            
        Returns:
            Dictionary with results for each platform
        """
        if platforms is None:
            platforms = list(self.publishers.keys())
        
        results = {}
        
        for platform in platforms:
            if platform not in self.publishers:
                results[platform] = {"success": False, "error": "Publisher not available"}
                continue
            
            try:
                if platform == 'instagram':
                    response = instagram_video_post(
                        self.publishers[platform], video_url, caption
                    )
                elif platform == 'youtube':
                    # For YouTube, we need a local file path, not URL
                    results[platform] = {
                        "success": False, 
                        "error": "YouTube requires local file path, not URL"
                    }
                    continue
                elif platform == 'linkedin':
                    response = linkedin_video_post(
                        self.publishers[platform], video_url, caption
                    )
                elif platform == 'facebook':
                    response = facebook_video_post(
                        self.publishers[platform], video_url, caption
                    )
                else:
                    results[platform] = {"success": False, "error": "Video posting not supported"}
                    continue
                
                results[platform] = {
                    "success": response.success,
                    "post_id": getattr(response, 'post_id', None) or getattr(response, 'media_id', None),
                    "error": getattr(response, 'error_message', None)
                }
                
            except Exception as e:
                results[platform] = {"success": False, "error": str(e)}
        
        return results
    
    def publish_text_everywhere(self, text: str, platforms: List[str] = None) -> Dict[str, Dict]:
        """
        Publish text to multiple platforms
        
        Args:
            text: Text content to publish
            platforms: List of platforms to publish to (default: all available)
            
        Returns:
            Dictionary with results for each platform
        """
        if platforms is None:
            platforms = ['linkedin', 'facebook']  # Only these support text-only posts
        
        results = {}
        
        for platform in platforms:
            if platform not in self.publishers:
                results[platform] = {"success": False, "error": "Publisher not available"}
                continue
            
            try:
                if platform == 'linkedin':
                    response = linkedin_text_post(self.publishers[platform], text)
                elif platform == 'facebook':
                    response = facebook_text_post(self.publishers[platform], text)
                else:
                    results[platform] = {"success": False, "error": "Text posting not supported"}
                    continue
                
                results[platform] = {
                    "success": response.success,
                    "post_id": getattr(response, 'post_id', None),
                    "error": getattr(response, 'error_message', None)
                }
                
            except Exception as e:
                results[platform] = {"success": False, "error": str(e)}
        
        return results
    
    def schedule_post_everywhere(self, content_type: str, content: str, 
                                scheduled_time: datetime, **kwargs) -> Dict[str, Dict]:
        """
        Schedule post across multiple platforms
        
        Args:
            content_type: Type of content ('image', 'video', 'text')
            content: Content URL or text
            scheduled_time: When to publish
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with results for each platform
        """
        results = {}
        
        if content_type == 'image':
            results = self.publish_image_everywhere(content, kwargs.get('caption', ''))
        elif content_type == 'video':
            results = self.publish_video_everywhere(content, kwargs.get('caption', ''))
        elif content_type == 'text':
            results = self.publish_text_everywhere(content)
        
        # Note: Scheduling implementation would require modifying each publisher
        # to accept scheduled_time parameter
        
        return results


def main():
    """Example usage of the Social Media Manager"""
    
    print("🚀 Initializing Social Media Manager...")
    manager = SocialMediaManager()
    
    print(f"\n📊 Available platforms: {list(manager.publishers.keys())}")
    
    # Example 1: Publish image everywhere
    print("\n📸 Publishing image to all platforms...")
    image_results = manager.publish_image_everywhere(
        image_url="https://example.com/sample-image.jpg",
        caption="Check out this amazing content! #socialmedia #crossplatform"
    )
    
    print("Image publishing results:")
    for platform, result in image_results.items():
        status = "✅" if result["success"] else "❌"
        print(f"  {status} {platform}: {result}")
    
    # Example 2: Publish text to supported platforms
    print("\n📝 Publishing text to supported platforms...")
    text_results = manager.publish_text_everywhere(
        text="Excited to share this update across multiple platforms! 🚀"
    )
    
    print("Text publishing results:")
    for platform, result in text_results.items():
        status = "✅" if result["success"] else "❌"
        print(f"  {status} {platform}: {result}")
    
    # Example 3: Schedule a post
    print("\n⏰ Scheduling post for tomorrow...")
    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
    
    scheduled_results = manager.schedule_post_everywhere(
        content_type='image',
        content="https://example.com/scheduled-image.jpg",
        scheduled_time=tomorrow,
        caption="This post was scheduled for tomorrow! 📅"
    )
    
    print("Scheduled post results:")
    for platform, result in scheduled_results.items():
        status = "✅" if result["success"] else "❌"
        print(f"  {status} {platform}: {result}")


if __name__ == "__main__":
    main()