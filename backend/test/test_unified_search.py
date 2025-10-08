#!/usr/bin/env python3
"""
Test script for the unified social media search.

This script demonstrates how to use the unified search with different platforms.
"""

import os
import json
from tools.unified_search import (
    search_social_media, 
    search_multiple_platforms,
    get_supported_search_platforms, 
    get_search_platform_info,
    format_search_results
)


def test_search_platform_info():
    """Test search platform information functionality."""
    print("=== Testing Search Platform Information ===")
    
    for platform in get_supported_search_platforms():
        try:
            info = get_search_platform_info(platform)
            print(f"\n{platform.upper()}:")
            print(f"  Identifier: {info['identifier_type']}")
            print(f"  Example: {info['example']}")
            print(f"  Required ENV vars: {', '.join(info['required_env_vars'])}")
            print(f"  Description: {info['description']}")
        except Exception as e:
            print(f"Error getting info for {platform}: {e}")


def test_reddit_search():
    """Test Reddit search (most likely to work without API keys)."""
    print("\n=== Testing Reddit Search ===")
    
    try:
        result = search_social_media(
            platform='reddit',
            query='python programming tips',
            limit=3,
            days_back=7
        )
        
        print(f"Success: {result['success']}")
        if result['success']:
            print(f"Results found: {result['count']}")
            print(f"Method used: {result['method_used']}")
            
            # Show formatted results
            formatted = format_search_results(result, max_items_per_platform=2)
            print(f"\nFormatted Results:\n{formatted}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"Reddit search test failed: {e}")


def test_youtube_search():
    """Test YouTube search (requires API key)."""
    print("\n=== Testing YouTube Search ===")
    
    # Check if API key is available
    if not os.getenv('YOUTUBE_API_KEY'):
        print("Skipping YouTube search test - YOUTUBE_API_KEY not found in environment")
        return
    
    try:
        result = search_social_media(
            platform='youtube',
            query='python tutorial',
            limit=2,
            days_back=30
        )
        
        print(f"Success: {result['success']}")
        if result['success']:
            print(f"Videos found: {result['count']}")
            print(f"Method used: {result['method_used']}")
            
            # Show formatted results
            formatted = format_search_results(result, max_items_per_platform=2)
            print(f"\nFormatted Results:\n{formatted}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"YouTube search test failed: {e}")


def test_instagram_search():
    """Test Instagram search (requires API token)."""
    print("\n=== Testing Instagram Search ===")
    
    # Check if API token is available
    if not os.getenv('APIFY_API_TOKEN'):
        print("Skipping Instagram search test - APIFY_API_TOKEN not found in environment")
        return
    
    try:
        result = search_social_media(
            platform='instagram',
            query='ai automation',
            limit=2,
            search_type='hashtag'
        )
        
        print(f"Success: {result['success']}")
        if result['success']:
            print(f"Posts found: {result['count']}")
            print(f"Method used: {result['method_used']}")
            print(f"Search type: {result.get('search_type', 'unknown')}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"Instagram search test failed: {e}")


def test_multi_platform_search():
    """Test searching across multiple platforms."""
    print("\n=== Testing Multi-Platform Search ===")
    
    # Determine which platforms to test based on available API keys
    platforms_to_test = ['reddit']  # Reddit is most likely to work
    
    if os.getenv('YOUTUBE_API_KEY'):
        platforms_to_test.append('youtube')
    if os.getenv('APIFY_API_TOKEN'):
        platforms_to_test.append('instagram')
    
    if len(platforms_to_test) < 2:
        print("Skipping multi-platform test - need at least 2 platforms with API keys")
        return
    
    try:
        result = search_multiple_platforms(
            platforms=platforms_to_test,
            query='artificial intelligence',
            limit=2,
            days_back=30
        )
        
        print(f"Platforms searched: {result['platforms_searched']}")
        print(f"Total results: {result['total_results']}")
        
        # Show formatted results
        formatted = format_search_results(result, max_items_per_platform=1)
        print(f"\nFormatted Results:\n{formatted}")
        
    except Exception as e:
        print(f"Multi-platform search test failed: {e}")


def save_test_results():
    """Save test results to a JSON file."""
    print("\n=== Saving Test Results ===")
    
    results = {}
    
    # Test each platform
    platforms_to_test = ['reddit']  # Start with Reddit as it's most likely to work
    
    # Add other platforms if API keys are available
    if os.getenv('YOUTUBE_API_KEY'):
        platforms_to_test.append('youtube')
    if os.getenv('APIFY_API_TOKEN'):
        platforms_to_test.append('instagram')
    
    for platform in platforms_to_test:
        try:
            if platform == 'reddit':
                result = search_social_media(platform, 'python tips', limit=1)
            elif platform == 'instagram':
                result = search_social_media(platform, 'coding', limit=1, search_type='hashtag')
            elif platform == 'youtube':
                result = search_social_media(platform, 'programming', limit=1)
            
            results[platform] = {
                'success': result['success'],
                'count': result.get('count', 0),
                'method_used': result.get('method_used', 'none'),
                'error': result.get('error', None)
            }
            
        except Exception as e:
            results[platform] = {
                'success': False,
                'error': str(e)
            }
    
    # Save results
    with open('search_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("Test results saved to search_test_results.json")
    print(f"Tested platforms: {list(results.keys())}")


def main():
    """Run all tests."""
    print("Unified Social Media Search - Test Suite")
    print("=" * 50)
    
    # Test platform information
    # test_search_platform_info()
    
    # Test individual platforms
    #test_reddit_search()
    #test_youtube_search()
    test_instagram_search()
    
    # Test multi-platform search
    # test_multi_platform_search()
    
    # Save comprehensive test results
    save_test_results()
    
    print("\n" + "=" * 50)
    print("Test suite completed!")
    print("\nUsage Examples:")
    print("1. Basic search:")
    print("   from unified_search import search_social_media")
    print("   result = search_social_media('reddit', 'python tips', limit=5)")
    print()
    print("2. Multi-platform search:")
    print("   from unified_search import search_multiple_platforms")
    print("   result = search_multiple_platforms(['reddit', 'youtube'], 'AI tools', limit=3)")
    print()
    print("3. Get platform information:")
    print("   from unified_search import get_search_platform_info")
    print("   info = get_search_platform_info('youtube')")
    print()
    print("4. Format results:")
    print("   from unified_search import format_search_results")
    print("   formatted = format_search_results(result)")


if __name__ == "__main__":
    main()