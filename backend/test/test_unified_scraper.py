#!/usr/bin/env python3
"""
Test script for the unified social media scraper.

This script demonstrates how to use the unified scraper with different platforms.
"""

import os
import json
from tools.unified_scraper import scrape_social_media, get_supported_platforms, get_platform_info


def test_platform_info():
    """Test platform information functionality."""
    print("=== Testing Platform Information ===")
    
    for platform in get_supported_platforms():
        try:
            info = get_platform_info(platform)
            print(f"\n{platform.upper()}:")
            print(f"  Identifier: {info['identifier_type']}")
            print(f"  Example: {info['example']}")
            print(f"  Required ENV vars: {', '.join(info['required_env_vars'])}")
            print(f"  Description: {info['description']}")
        except Exception as e:
            print(f"Error getting info for {platform}: {e}")


def test_reddit_scraping():
    """Test Reddit scraping (most likely to work without API keys)."""
    print("\n=== Testing Reddit Scraping ===")
    
    try:
        result = scrape_social_media(
            platform='reddit',
            identifier='python',
            limit=2,
            category='hot',
            min_score=5
        )
        
        print(f"Success: {result['success']}")
        if result['success']:
            print(f"Posts found: {result['count']}")
            print(f"Method used: {result['method_used']}")
            
            # Show first post title if available
            if result['data'] and 'posts' in result['data'] and result['data']['posts']:
                first_post = result['data']['posts'][0]
                print(f"First post: {first_post.get('title', 'No title')[:50]}...")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"Reddit test failed: {e}")


def test_instagram_scraping():
    """Test Instagram scraping with fallback."""
    print("\n=== Testing Instagram Scraping ===")
    
    try:
        result = scrape_social_media(
            platform='instagram',
            identifier='google',
            limit=3,
            days_back=30
        )
        
        print(f"Success: {result['success']}")
        if result['success']:
            print(f"Posts found: {result['count']}")
            print(f"Method used: {result['method_used']}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"Instagram test failed: {e}")


def test_youtube_scraping():
    """Test YouTube scraping (requires API key)."""
    print("\n=== Testing YouTube Scraping ===")
    
    # Check if API key is available
    if not os.getenv('YOUTUBE_API_KEY'):
        print("Skipping YouTube test - YOUTUBE_API_KEY not found in environment")
        return
    
    try:
        result = scrape_social_media(
            platform='youtube',
            identifier='GoogleDevelopers',
            limit=2,
            days_back=30
        )
        
        print(f"Success: {result['success']}")
        if result['success']:
            print(f"Videos found: {result['count']}")
            print(f"Method used: {result['method_used']}")
            
            # Show first video title if available
            if result['data'] and len(result['data']) > 0:
                first_video = result['data'][0]
                print(f"First video: {first_video.get('title', 'No title')[:50]}...")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"YouTube test failed: {e}")


def test_linkedin_scraping():
    """Test LinkedIn scraping (requires API token)."""
    print("\n=== Testing LinkedIn Scraping ===")
    
    # Check if API token is available
    if not os.getenv('APIFY_API_TOKEN'):
        print("Skipping LinkedIn test - APIFY_API_TOKEN not found in environment")
        return
    
    try:
        result = scrape_social_media(
            platform='linkedin',
            identifier='https://www.linkedin.com/in/satyanadella/',
            limit=2
        )
        
        print(f"Success: {result['success']}")
        if result['success']:
            print(f"Posts found: {result['count']}")
            print(f"Method used: {result['method_used']}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"LinkedIn test failed: {e}")


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
        platforms_to_test.extend(['instagram', 'linkedin'])
    
    for platform in platforms_to_test:
        try:
            if platform == 'reddit':
                result = scrape_social_media(platform, 'python', limit=1)
            elif platform == 'instagram':
                result = scrape_social_media(platform, 'google', limit=1)
            elif platform == 'youtube':
                result = scrape_social_media(platform, 'GoogleDevelopers', limit=1)
            elif platform == 'linkedin':
                result = scrape_social_media(platform, 'https://www.linkedin.com/in/satyanadella/', limit=1)
            
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
    with open('test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("Test results saved to test_results.json")
    print(f"Tested platforms: {list(results.keys())}")


def main():
    """Run all tests."""
    print("Unified Social Media Scraper - Test Suite")
    print("=" * 50)
    
    # Test platform information
    test_platform_info()
    
    # Test individual platforms
    test_reddit_scraping()
    test_instagram_scraping()
    test_youtube_scraping()
    test_linkedin_scraping()
    
    # Save comprehensive test results
    save_test_results()
    
    print("\n" + "=" * 50)
    print("Test suite completed!")
    print("\nUsage Examples:")
    print("1. Basic usage:")
    print("   from unified_scraper import scrape_social_media")
    print("   result = scrape_social_media('reddit', 'python', limit=5)")
    print()
    print("2. With additional parameters:")
    print("   result = scrape_social_media('instagram', 'google', limit=3, days_back=7)")
    print()
    print("3. Get platform information:")
    print("   from unified_scraper import get_platform_info")
    print("   info = get_platform_info('youtube')")


if __name__ == "__main__":
    main()