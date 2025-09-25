"""
Unified Social Media Search

This module provides a unified functional interface to search content across multiple social media platforms:
- Instagram (with Apify API)
- YouTube (with official API)
- Reddit (with PRAW)

The unified function automatically routes to the appropriate search function based on the platform name.
"""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

# Import all search modules
from utils.searchers.insta_search import search_instagram_with_apify
from utils.searchers.yt_search import get_youtube_videos
from utils.searchers.reddit_search import search_reddit


# Constants
SUPPORTED_SEARCH_PLATFORMS = ['instagram', 'youtube', 'reddit']

SEARCH_PLATFORM_INFO = {
    'instagram': {
        'identifier_type': 'search_term',
        'example': 'ai automation',
        'required_env_vars': ['APIFY_API_TOKEN'],
        'optional_params': ['search_type', 'api_token'],
        'description': 'Searches Instagram posts using Apify API (hashtags, users, etc.)'
    },
    'youtube': {
        'identifier_type': 'query',
        'example': 'python tutorial',
        'required_env_vars': ['YOUTUBE_API_KEY'],
        'optional_params': ['published_after', 'api_key'],
        'description': 'Searches YouTube videos using official API'
    },
    'reddit': {
        'identifier_type': 'query',
        'example': 'trending ai tools',
        'required_env_vars': ['REDDIT_CLIENT_ID', 'REDDIT_CLIENT_SECRET', 'REDDIT_USER_AGENT'],
        'optional_params': ['days_back'],
        'description': 'Searches Reddit posts across all subreddits using PRAW'
    }
}


def get_supported_search_platforms() -> List[str]:
    """Return list of supported search platforms."""
    return SUPPORTED_SEARCH_PLATFORMS.copy()


def get_search_platform_info(platform: str) -> Dict[str, Any]:
    """
    Get information about a specific search platform's requirements.
    
    Args:
        platform (str): Platform name
        
    Returns:
        Dict containing platform information
    """
    platform = platform.lower()
    
    if platform not in SEARCH_PLATFORM_INFO:
        raise ValueError(f"Unknown search platform: {platform}")
    
    return SEARCH_PLATFORM_INFO[platform]


def search_instagram(
    search_term: str, 
    limit: int, 
    search_type: Optional[str], 
    api_token: Optional[str],
    **kwargs
) -> Dict[str, Any]:
    """
    Search Instagram content using Apify API.
    """
    try:
        print(f"Searching Instagram for: {search_term}")
        
        instagram_data = search_instagram_with_apify(
            search_term=search_term,
            search_type=search_type or 'hashtag',
            search_limit=limit,
            api_token=api_token
        )
        
        return {
            'success': True,
            'platform': 'instagram',
            'search_term': search_term,
            'search_type': search_type or 'hashtag',
            'method_used': 'apify',
            'data': instagram_data,
            'count': len(instagram_data) if isinstance(instagram_data, list) else 0,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'success': False,
            'platform': 'instagram',
            'search_term': search_term,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


def search_youtube(
    query: str, 
    limit: int, 
    days_back: Optional[int], 
    api_key: Optional[str],
    **kwargs
) -> Dict[str, Any]:
    """
    Search YouTube videos using official API.
    """
    try:
        print(f"Searching YouTube for: {query}")
        
        # Calculate published_after date
        if days_back:
            published_after = (datetime.now() - timedelta(days=days_back)).isoformat() + 'Z'
        else:
            published_after = kwargs.get('published_after', '2024-01-01T00:00:00Z')
        
        youtube_data = get_youtube_videos(
            query=query,
            published_after=published_after,
            max_results=limit,
            api_key=api_key
        )
        
        return {
            'success': True,
            'platform': 'youtube',
            'query': query,
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
            'query': query,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


def search_reddit_posts(
    query: str, 
    limit: int, 
    days_back: Optional[int],
    **kwargs
) -> Dict[str, Any]:
    """
    Search Reddit posts using PRAW.
    """
    try:
        print(f"Searching Reddit for: {query}")
        
        reddit_data = search_reddit(
            query=query,
            limit=limit,
            days_back=days_back or 30
        )
        
        return {
            'success': True,
            'platform': 'reddit',
            'query': query,
            'method_used': 'praw',
            'data': reddit_data,
            'count': reddit_data.get('metadata', {}).get('total_results', 0),
            'days_back': days_back or 30,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'success': False,
            'platform': 'reddit',
            'query': query,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


def search_social_media(
    platform: str,
    query: str,
    limit: int = 10,
    days_back: Optional[int] = None,
    search_type: Optional[str] = None,
    api_token: Optional[str] = None,
    api_key: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Unified function to search content across any supported platform.
    
    Args:
        platform (str): Platform name ('instagram', 'youtube', 'reddit')
        query (str): Search query string
        limit (int): Maximum number of results to fetch (default: 10)
        days_back (int, optional): Number of days to look back for content
        search_type (str, optional): Type of search for Instagram ('hashtag', 'user', etc.)
        api_token (str, optional): API token for Apify services
        api_key (str, optional): API key for YouTube
        **kwargs: Additional platform-specific parameters
        
    Returns:
        Dict containing search results and metadata
        
    Raises:
        ValueError: If platform is not supported
        Exception: If search fails
    """
    platform = platform.lower()
    
    if platform not in SUPPORTED_SEARCH_PLATFORMS:
        raise ValueError(f"Unsupported search platform: {platform}. Supported platforms: {SUPPORTED_SEARCH_PLATFORMS}")
    
    try:
        if platform == 'instagram':
            return search_instagram(query, limit, search_type, api_token, **kwargs)
        elif platform == 'youtube':
            return search_youtube(query, limit, days_back, api_key, **kwargs)
        elif platform == 'reddit':
            return search_reddit_posts(query, limit, days_back, **kwargs)
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'platform': platform,
            'query': query,
            'timestamp': datetime.now().isoformat()
        }


def search_multiple_platforms(
    platforms: List[str],
    query: str,
    limit: int = 10,
    days_back: Optional[int] = None,
    search_type: Optional[str] = None,
    api_token: Optional[str] = None,
    api_key: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Search across multiple platforms simultaneously.
    
    Args:
        platforms (List[str]): List of platform names to search
        query (str): Search query string
        limit (int): Maximum number of results per platform
        days_back (int, optional): Number of days to look back
        search_type (str, optional): Type of search for Instagram
        api_token (str, optional): API token for Apify services
        api_key (str, optional): API key for YouTube
        **kwargs: Additional platform-specific parameters
        
    Returns:
        Dict containing results from all platforms
    """
    results = {
        'query': query,
        'platforms_searched': platforms,
        'total_results': 0,
        'platform_results': {},
        'timestamp': datetime.now().isoformat()
    }
    
    for platform in platforms:
        try:
            platform_result = search_social_media(
                platform=platform,
                query=query,
                limit=limit,
                days_back=days_back,
                search_type=search_type,
                api_token=api_token,
                api_key=api_key,
                **kwargs
            )
            
            results['platform_results'][platform] = platform_result
            if platform_result.get('success', False):
                results['total_results'] += platform_result.get('count', 0)
                
        except Exception as e:
            results['platform_results'][platform] = {
                'success': False,
                'error': str(e),
                'platform': platform,
                'query': query
            }
    
    return results


def format_search_results(results: Dict[str, Any], max_items_per_platform: int = 3) -> str:
    """
    Format search results into a readable string.
    
    Args:
        results: Results from search_social_media or search_multiple_platforms
        max_items_per_platform: Maximum items to show per platform
        
    Returns:
        Formatted string with search results
    """
    if 'platform_results' in results:
        # Multi-platform results
        output = [f"Search Results for: '{results['query']}'"]
        output.append(f"Total Results: {results['total_results']}")
        output.append("=" * 60)
        
        for platform, platform_result in results['platform_results'].items():
            if platform_result.get('success', False):
                output.append(f"\n{platform.upper()} ({platform_result.get('count', 0)} results):")
                
                data = platform_result.get('data', [])
                if isinstance(data, list):
                    for i, item in enumerate(data[:max_items_per_platform], 1):
                        if platform == 'youtube':
                            output.append(f"  {i}. {item.get('title', 'No title')}")
                            output.append(f"     Channel: {item.get('channelTitle', 'Unknown')}")
                            output.append(f"     URL: {item.get('url', 'No URL')}")
                        elif platform == 'reddit':
                            posts = item.get('posts', [])
                            for j, post in enumerate(posts[:max_items_per_platform], 1):
                                output.append(f"  {j}. {post.get('title', 'No title')}")
                                output.append(f"     r/{post.get('subreddit', 'unknown')} | Score: {post.get('upvotes', 0)}")
                                output.append(f"     URL: {post.get('permalink', 'No URL')}")
                        elif platform == 'instagram':
                            output.append(f"  {i}. Instagram post data")
                            output.append(f"     Type: {platform_result.get('search_type', 'unknown')}")
                else:
                    output.append(f"  No structured data available")
            else:
                output.append(f"\n{platform.upper()}: Error - {platform_result.get('error', 'Unknown error')}")
        
        return "\n".join(output)
    
    else:
        # Single platform results
        if results.get('success', False):
            output = [f"Search Results for: '{results.get('query', results.get('search_term', 'Unknown'))}'"]
            output.append(f"Platform: {results['platform'].upper()}")
            output.append(f"Results: {results.get('count', 0)}")
            output.append("=" * 40)
            
            data = results.get('data', [])
            if isinstance(data, list):
                for i, item in enumerate(data[:max_items_per_platform], 1):
                    if results['platform'] == 'youtube':
                        output.append(f"{i}. {item.get('title', 'No title')}")
                        output.append(f"   Channel: {item.get('channelTitle', 'Unknown')}")
                        output.append(f"   URL: {item.get('url', 'No URL')}")
                    elif results['platform'] == 'reddit':
                        posts = item.get('posts', [])
                        for j, post in enumerate(posts[:max_items_per_platform], 1):
                            output.append(f"{j}. {post.get('title', 'No title')}")
                            output.append(f"   r/{post.get('subreddit', 'unknown')} | Score: {post.get('upvotes', 0)}")
                            output.append(f"   URL: {post.get('permalink', 'No URL')}")
                    elif results['platform'] == 'instagram':
                        output.append(f"{i}. Instagram post data")
                        output.append(f"   Type: {results.get('search_type', 'unknown')}")
            
            return "\n".join(output)
        else:
            return f"Search failed: {results.get('error', 'Unknown error')}"