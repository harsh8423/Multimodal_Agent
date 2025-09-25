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
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import json

# Import all scraper modules
from uitls.scrapers.insta_apifyscrape import scrape_instagram_with_apify
from uitls.scrapers.insta_codescrape import InstagramScraper
from uitls.scrapers.linkedin_apifyscrape import scrape_linkedin_with_apify
from uitls.scrapers.yt_scrape import get_youtube_videos_by_channel
from uitls.scrapers.reddit import get_reddit_data


# Constants
SUPPORTED_PLATFORMS = ['instagram', 'linkedin', 'youtube', 'reddit']

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
            
            result.update({
                'success': True,
                'method_used': 'apify',
                'data': apify_data,
                'count': len(apify_data) if isinstance(apify_data, list) else 1
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
        
        result.update({
            'success': True,
            'method_used': 'code_based',
            'data': code_data,
            'count': len(code_data) if isinstance(code_data, list) else 0
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
        
        return {
            'success': True,
            'platform': 'linkedin',
            'profile_url': profile_url,
            'method_used': 'apify',
            'data': linkedin_data,
            'count': len(linkedin_data) if isinstance(linkedin_data, list) else 0,
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
        
        return {
            'success': True,
            'platform': 'youtube',
            'username': username,
            'method_used': 'official_api',
            'data': youtube_data,
            'count': len(youtube_data) if isinstance(youtube_data, list) else 0,
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
        
        return {
            'success': True,
            'platform': 'reddit',
            'subreddit': subreddit_name,
            'method_used': 'praw',
            'data': reddit_data,
            'count': len(reddit_data.get('posts', [])),
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


def scrape_social_media(
    platform: str,
    identifier: str,
    limit: int = 10,
    days_back: Optional[int] = None,
    category: Optional[str] = None,
    min_score: Optional[int] = None,
    min_comments: Optional[int] = None,
    api_token: Optional[str] = None,
    api_key: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Unified function to scrape data from any supported platform.
    
    Args:
        platform (str): Platform name ('instagram', 'linkedin', 'youtube', 'reddit')
        identifier (str): Username, profile URL, or subreddit name
        limit (int): Maximum number of results to fetch (default: 10)
        days_back (int, optional): Number of days to look back for content
        category (str, optional): Category for Reddit ('hot', 'rising', 'new', 'top')
        min_score (int, optional): Minimum score for Reddit posts
        min_comments (int, optional): Minimum comments for Reddit posts
        api_token (str, optional): API token for Apify services
        api_key (str, optional): API key for YouTube
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
        if platform == 'instagram':
            return scrape_instagram(identifier, limit, days_back, api_token, **kwargs)
        elif platform == 'linkedin':
            return scrape_linkedin(identifier, limit, api_token, **kwargs)
        elif platform == 'youtube':
            return scrape_youtube(identifier, limit, days_back, api_key, **kwargs)
        elif platform == 'reddit':
            return scrape_reddit(identifier, limit, category, min_score, min_comments, **kwargs)
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'platform': platform,
            'identifier': identifier,
            'timestamp': datetime.now().isoformat()
        }

