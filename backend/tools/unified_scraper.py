"""
Unified Social Media Scraper

This module provides a unified functional interface to scrape data from multiple social media platforms:
- Instagram (with Apify API and code-based scraping fallback)
- LinkedIn (with Apify API)
- YouTube (with official API)
- Reddit (with PRAW)

The unified function automatically routes to the appropriate scraper based on the platform name.
"""

import asyncio
import os
import tempfile
import shutil
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import json

# Import all scraper modules
from utils.scrapers.insta_apifyscrape import scrape_instagram_with_apify
from utils.scrapers.insta_codescrape import InstagramScraper
from utils.scrapers.linkedin_apifyscrape import scrape_linkedin_with_apify
from utils.scrapers.yt_scrape import get_youtube_videos_by_channel
from utils.scrapers.reddit import get_reddit_data

# Import utilities for media handling
from utils.dowloader import download_media_file
from utils.upload_cloudinary import upload_to_cloudinary

# Import database service for saving scraped data
from services.social_media_db import social_media_db
from models.social_media import PlatformType, ProcessingStatus


# Constants
SUPPORTED_PLATFORMS = ['instagram', 'linkedin', 'youtube', 'reddit']

# Media processing functions
def process_media_url(url: str, platform: str, temp_dir: str) -> Optional[str]:
    """
    Download media from URL, upload to Cloudinary, and return CDN URL.
    
    Args:
        url: Media URL to process
        platform: Platform name for folder organization
        temp_dir: Temporary directory for downloads
        
    Returns:
        Cloudinary CDN URL or None if processing failed
    """
    if not url:
        return None
        
    try:
        print(f"Processing media URL: {url[:100]}...")
        
        # Download media file
        success, message, file_info = download_media_file(
            url=url,
            output_dir=temp_dir,
            overwrite=True
        )
        
        if not success:
            print(f"Failed to download media: {message}")
            return None
            
        file_path = file_info["filepath"]
        print(f"Downloaded to: {file_path}")
        print(f"File size: {file_info.get('size_mb', 0)} MB")
        print(f"Content type: {file_info.get('content_type', 'unknown')}")
        
        # Determine resource type and folder
        resource_type = "video" if any(ext in file_path.lower() for ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']) else "image"
        folder = f"social_media/{platform}"
        
        # Upload to Cloudinary
        cloudinary_response = upload_to_cloudinary(
            file_path=file_path,
            options={
                "resourceType": resource_type,
                "folder": folder
            }
        )
        
        # Clean up temporary file
        try:
            os.remove(file_path)
            print(f"Cleaned up temporary file: {file_path}")
        except OSError as e:
            print(f"Warning: Could not delete temporary file {file_path}: {e}")
            
        cloudinary_url = cloudinary_response.get("secure_url")
        print(f"Cloudinary URL: {cloudinary_url}")
        return cloudinary_url
        
    except Exception as e:
        print(f"Error processing media URL {url}: {str(e)}")
        return None


def process_instagram_media(post_data: Dict[str, Any], temp_dir: str) -> Dict[str, Any]:
    """Process Instagram media URLs and replace with Cloudinary URLs."""
    processed_post = post_data.copy()
    
    # Process video URL
    if post_data.get("videoUrl"):
        cloudinary_url = process_media_url(post_data["videoUrl"], "instagram", temp_dir)
        if cloudinary_url:
            processed_post["videoUrl"] = cloudinary_url
    
    # Process display URL (main image)
    if post_data.get("displayUrl"):
        cloudinary_url = process_media_url(post_data["displayUrl"], "instagram", temp_dir)
        if cloudinary_url:
            processed_post["displayUrl"] = cloudinary_url
    
    # Process images array
    if post_data.get("images") and isinstance(post_data["images"], list):
        processed_images = []
        for image_url in post_data["images"]:
            cloudinary_url = process_media_url(image_url, "instagram", temp_dir)
            processed_images.append(cloudinary_url if cloudinary_url else image_url)
        processed_post["images"] = processed_images
    
    return processed_post


def process_linkedin_media(post_data: Dict[str, Any], temp_dir: str) -> Dict[str, Any]:
    """Process LinkedIn media URLs and replace with Cloudinary URLs."""
    processed_post = post_data.copy()
    
    # Process postImages array
    if post_data.get("postImages") and isinstance(post_data["postImages"], list):
        processed_images = []
        for image_obj in post_data["postImages"]:
            # LinkedIn images are objects with url, width, height, expiresAt
            if isinstance(image_obj, dict) and "url" in image_obj:
                image_url = image_obj["url"]
                cloudinary_url = process_media_url(image_url, "linkedin", temp_dir)
                if cloudinary_url:
                    # Replace the URL in the object
                    processed_image_obj = image_obj.copy()
                    processed_image_obj["url"] = cloudinary_url
                    processed_images.append(processed_image_obj)
                else:
                    processed_images.append(image_obj)  # Keep original if processing failed
            else:
                processed_images.append(image_obj)  # Keep as-is if not a valid image object
        processed_post["postImages"] = processed_images
    
    return processed_post


def process_youtube_media(video_data: Dict[str, Any], temp_dir: str) -> Dict[str, Any]:
    """Process YouTube media URLs and replace with Cloudinary URLs."""
    processed_video = video_data.copy()
    
    # Process thumbnail URL
    if video_data.get("thumbnail_url"):
        cloudinary_url = process_media_url(video_data["thumbnail_url"], "youtube", temp_dir)
        if cloudinary_url:
            processed_video["thumbnail_url"] = cloudinary_url
    
    # Note: YouTube video_url is a watch URL, not a direct media file
    # We don't download the actual video content, just the thumbnail
    
    return processed_video


def process_media_for_platform(data: List[Dict[str, Any]], platform: str) -> List[Dict[str, Any]]:
    """Process media URLs for all posts/videos in the data."""
    if platform == "reddit":
        # Reddit doesn't need media processing
        return data
    
    # Create temporary directory for downloads
    temp_dir = tempfile.mkdtemp(prefix=f"media_download_{platform}_")
    
    try:
        processed_data = []
        for item in data:
            if platform == "instagram":
                processed_item = process_instagram_media(item, temp_dir)
            elif platform == "linkedin":
                processed_item = process_linkedin_media(item, temp_dir)
            elif platform == "youtube":
                processed_item = process_youtube_media(item, temp_dir)
            else:
                processed_item = item
                
            processed_data.append(processed_item)
        
        return processed_data
        
    finally:
        # Clean up temporary directory
        try:
            shutil.rmtree(temp_dir)
        except OSError:
            pass


PLATFORM_INFO = {
    'instagram': {
        'identifier_type': 'username',
        'example': 'google',
        'required_env_vars': ['APIFY_API_TOKEN (optional)'],
        'optional_params': ['days_back', 'api_token'],
        'description': 'Scrapes Instagram posts with Apify API fallback to code-based scraping'
    },
    'linkedin': {
        'identifier_type': 'profile_url',
        'example': 'https://www.linkedin.com/in/satyanadella/',
        'required_env_vars': ['APIFY_API_TOKEN'],
        'optional_params': ['api_token'],
        'description': 'Scrapes LinkedIn profile posts using Apify API'
    },
    'youtube': {
        'identifier_type': 'channel_username',
        'example': 'GoogleDevelopers',
        'required_env_vars': ['YOUTUBE_API_KEY'],
        'optional_params': ['days_back', 'published_after', 'api_key'],
        'description': 'Scrapes YouTube channel videos using official API'
    },
    'reddit': {
        'identifier_type': 'subreddit_name',
        'example': 'python',
        'required_env_vars': ['REDDIT_CLIENT_ID', 'REDDIT_CLIENT_SECRET', 'REDDIT_USER_AGENT'],
        'optional_params': ['category', 'min_score', 'min_comments', 'comment_limit'],
        'description': 'Scrapes Reddit posts and comments using PRAW'
    }
}


def get_supported_platforms() -> List[str]:
    """Return list of supported platforms."""
    return SUPPORTED_PLATFORMS.copy()


def get_platform_info(platform: str) -> Dict[str, Any]:
    """
    Get information about a specific platform's requirements.
    
    Args:
        platform (str): Platform name
        
    Returns:
        Dict containing platform information
    """
    platform = platform.lower()
    
    if platform not in PLATFORM_INFO:
        raise ValueError(f"Unknown platform: {platform}")
    
    return PLATFORM_INFO[platform]


def scrape_instagram(
    username: str, 
    limit: int, 
    days_back: Optional[int], 
    api_token: Optional[str],
    **kwargs
) -> Dict[str, Any]:
    """
    Scrape Instagram data with fallback from Apify to code-based scraping.
    """
    result = {
        'platform': 'instagram',
        'username': username,
        'timestamp': datetime.now().isoformat(),
        'method_used': None
    }
    
    # Try Apify first if API token is available
    if api_token or os.getenv("APIFY_API_TOKEN"):
        try:
            print(f"Attempting Instagram scraping with Apify for @{username}")
            days = days_back or 1
            apify_data = scrape_instagram_with_apify(
                username=username,
                days=days,
                search_limit=limit,
                api_token=api_token
            )
            
            # Process media URLs and replace with Cloudinary URLs
            processed_data = process_media_for_platform(apify_data, 'instagram')
            
            result.update({
                'success': True,
                'method_used': 'apify',
                'data': processed_data,
                'count': len(processed_data) if isinstance(processed_data, list) else 1
            })
            return result
            
        except Exception as e:
            print(f"Apify Instagram scraping failed: {e}")
            print("Falling back to code-based scraping...")
    
    # Fallback to code-based scraping
    try:
        print(f"Attempting Instagram scraping with code-based method for @{username}")
        
        # Create scraper instance
        scraper = InstagramScraper()
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            code_data = loop.run_until_complete(
                scraper.scrape_user_posts_alternative(username, limit)
            )
        finally:
            loop.close()
        
        # Process media URLs and replace with Cloudinary URLs
        processed_data = process_media_for_platform(code_data, 'instagram')
        
        result.update({
            'success': True,
            'method_used': 'code_based',
            'data': processed_data,
            'count': len(processed_data) if isinstance(processed_data, list) else 0
        })
        return result
        
    except Exception as e:
        result.update({
            'success': False,
            'error': f"Both Instagram scraping methods failed. Last error: {str(e)}",
            'method_used': 'none'
        })
        return result


def scrape_linkedin(
    profile_url: str, 
    limit: int, 
    api_token: Optional[str],
    **kwargs
) -> Dict[str, Any]:
    """
    Scrape LinkedIn profile posts using Apify.
    """
    try:
        print(f"Scraping LinkedIn profile: {profile_url}")
        linkedin_data = scrape_linkedin_with_apify(
            profile_url=profile_url,
            max_posts=limit,
            api_token=api_token
        )
        
        # Process media URLs and replace with Cloudinary URLs
        processed_data = process_media_for_platform(linkedin_data, 'linkedin')
        
        return {
            'success': True,
            'platform': 'linkedin',
            'profile_url': profile_url,
            'method_used': 'apify',
            'data': processed_data,
            'count': len(processed_data) if isinstance(processed_data, list) else 0,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'success': False,
            'platform': 'linkedin',
            'profile_url': profile_url,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


def scrape_youtube(
    username: str, 
    limit: int, 
    days_back: Optional[int], 
    api_key: Optional[str],
    **kwargs
) -> Dict[str, Any]:
    """
    Scrape YouTube channel videos using official API.
    """
    try:
        print(f"Scraping YouTube channel: {username}")
        
        # Calculate published_after date
        if days_back:
            published_after = (datetime.now() - timedelta(days=days_back)).isoformat() + 'Z'
        else:
            published_after = kwargs.get('published_after', '2024-01-01T00:00:00Z')
        
        youtube_data = get_youtube_videos_by_channel(
            username=username,
            published_after=published_after,
            max_results=limit,
            api_key=api_key
        )
        
        # Process media URLs and replace with Cloudinary URLs
        processed_data = process_media_for_platform(youtube_data, 'youtube')
        
        return {
            'success': True,
            'platform': 'youtube',
            'username': username,
            'method_used': 'official_api',
            'data': processed_data,
            'count': len(processed_data) if isinstance(processed_data, list) else 0,
            'published_after': published_after,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'success': False,
            'platform': 'youtube',
            'username': username,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


def scrape_reddit(
    subreddit_name: str, 
    limit: int, 
    category: Optional[str], 
    min_score: Optional[int], 
    min_comments: Optional[int],
    **kwargs
) -> Dict[str, Any]:
    """
    Scrape Reddit subreddit posts using PRAW.
    """
    try:
        print(f"Scraping Reddit subreddit: r/{subreddit_name}")
        
        reddit_data = get_reddit_data(
            subreddit_name=subreddit_name,
            category=category or 'hot',
            post_limit=limit,
            comment_limit=kwargs.get('comment_limit', 5),
            min_score=min_score or 0,
            min_comments=min_comments or 0
        )
        
        # Extract posts from the reddit_data structure
        posts = reddit_data.get('posts', [])
        
        return {
            'success': True,
            'platform': 'reddit',
            'subreddit': subreddit_name,
            'method_used': 'praw',
            'data': posts,  # Return just the posts list
            'count': len(posts),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'success': False,
            'platform': 'reddit',
            'subreddit': subreddit_name,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


async def scrape_social_media(
    platform: str,
    identifier: str,
    user_id: str,
    brand_id: Optional[str] = None,
    handle_id: Optional[str] = None,
    limit: int = 10,
    days_back: Optional[int] = None,
    category: Optional[str] = None,
    min_score: Optional[int] = None,
    min_comments: Optional[int] = None,
    api_token: Optional[str] = None,
    api_key: Optional[str] = None,
    save_to_db: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    Unified function to scrape data from any supported platform.
    
    Args:
        platform (str): Platform name ('instagram', 'linkedin', 'youtube', 'reddit')
        identifier (str): Username, profile URL, or subreddit name
        user_id (str): User ID for database storage
        brand_id (str, optional): Brand ID if scraping for a specific brand
        handle_id (str, optional): Handle ID from brands.handles
        limit (int): Maximum number of results to fetch (default: 10)
        days_back (int, optional): Number of days to look back for content
        category (str, optional): Category for Reddit ('hot', 'rising', 'new', 'top')
        min_score (int, optional): Minimum score for Reddit posts
        min_comments (int, optional): Minimum comments for Reddit posts
        api_token (str, optional): API token for Apify services
        api_key (str, optional): API key for YouTube
        save_to_db (bool): Whether to save scraped data to database (default: True)
        **kwargs: Additional platform-specific parameters
        
    Returns:
        Dict containing scraped data and metadata
        
    Raises:
        ValueError: If platform is not supported
        Exception: If scraping fails
    """
    platform = platform.lower()
    
    if platform not in SUPPORTED_PLATFORMS:
        raise ValueError(f"Unsupported platform: {platform}. Supported platforms: {SUPPORTED_PLATFORMS}")
    
    try:
        # Scrape data from the platform
        if platform == 'instagram':
            result = scrape_instagram(identifier, limit, days_back, api_token, **kwargs)
        elif platform == 'linkedin':
            result = scrape_linkedin(identifier, limit, api_token, **kwargs)
        elif platform == 'youtube':
            result = scrape_youtube(identifier, limit, days_back, api_key, **kwargs)
        elif platform == 'reddit':
            result = scrape_reddit(identifier, limit, category, min_score, min_comments, **kwargs)
        
        # Save to database if scraping was successful and save_to_db is True
        if result.get('success') and save_to_db and result.get('data'):
            await save_scraped_data_to_db(
                result['data'], 
                platform, 
                user_id, 
                brand_id, 
                handle_id,
                result.get('method_used', 'unknown')
            )
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'platform': platform,
            'identifier': identifier,
            'timestamp': datetime.now().isoformat()
        }


async def save_scraped_data_to_db(
    data: List[Dict[str, Any]], 
    platform: str, 
    user_id: str, 
    brand_id: Optional[str] = None,
    handle_id: Optional[str] = None,
    source: str = "unknown"
) -> List[str]:
    """
    Save scraped data to MongoDB with normalized format.
    
    Args:
        data: List of scraped post/video data
        platform: Platform name
        user_id: User ID
        brand_id: Optional brand ID
        handle_id: Optional handle ID
        source: Scraping method used
        
    Returns:
        List of inserted document IDs
    """
    try:
        platform_enum = PlatformType(platform.lower())
        posts_to_save = []
        
        for item in data:
            # Normalize the platform-specific data
            normalized = await social_media_db.normalize_scraped_post(item, platform_enum)
            
            # Create scraped post document
            post_doc = {
                "user_id": user_id,
                "brand_id": brand_id,
                "handle_id": handle_id,
                "platform": platform_enum.value,
                "source": source,
                "platform_data": item,  # Keep original platform-specific data
                "normalized": normalized,
                "processing": {
                    "status": ProcessingStatus.NORMALIZED.value,
                    "pipeline": f"{platform}-v1",
                    "normalized_at": datetime.utcnow()
                },
                "metadata": {}
            }
            
            posts_to_save.append(post_doc)
        
        # Save all posts in batch
        if posts_to_save:
            saved_ids = await social_media_db.save_scraped_posts_batch(posts_to_save)
            print(f"Saved {len(saved_ids)} {platform} posts to database")
            return saved_ids
        
        return []
        
    except Exception as e:
        print(f"Error saving {platform} data to database: {str(e)}")
        return []

