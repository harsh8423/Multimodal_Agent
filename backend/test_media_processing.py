#!/usr/bin/env python3
"""
Test script for media processing integration in unified_scraper.py
"""

import os
import sys
from dotenv import load_dotenv

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.unified_scraper import scrape_social_media

load_dotenv()

def test_instagram_scraping():
    """Test Instagram scraping with media processing."""
    print("Testing Instagram scraping with media processing...")
    
    try:
        result = scrape_social_media(
            platform='instagram',
            identifier='google',
            limit=2,
            days_back=7
        )
        
        print(f"Success: {result.get('success')}")
        print(f"Method used: {result.get('method_used')}")
        print(f"Count: {result.get('count')}")
        
        if result.get('success') and result.get('data'):
            for i, post in enumerate(result['data'][:2]):  # Show first 2 posts
                print(f"\nPost {i+1}:")
                print(f"  Username: {post.get('username')}")
                print(f"  Type: {post.get('type')}")
                print(f"  Video URL: {post.get('videoUrl', 'None')[:100]}...")
                print(f"  Display URL: {post.get('displayUrl', 'None')[:100]}...")
                print(f"  Images count: {len(post.get('images', []))}")
                
                # Check if URLs are Cloudinary URLs
                if post.get('videoUrl') and 'cloudinary.com' in post.get('videoUrl', ''):
                    print("  ✓ Video URL processed to Cloudinary")
                if post.get('displayUrl') and 'cloudinary.com' in post.get('displayUrl', ''):
                    print("  ✓ Display URL processed to Cloudinary")
        
    except Exception as e:
        print(f"Error testing Instagram: {e}")

def test_linkedin_scraping():
    """Test LinkedIn scraping with media processing."""
    print("\nTesting LinkedIn scraping with media processing...")
    
    try:
        result = scrape_social_media(
            platform='linkedin',
            identifier='https://www.linkedin.com/in/niraj-kumar-91635924a/',
            limit=2
        )
        
        print(f"Success: {result.get('success')}")
        print(f"Method used: {result.get('method_used')}")
        print(f"Count: {result.get('count')}")
        
        if result.get('success') and result.get('data'):
            for i, post in enumerate(result['data'][:2]):  # Show first 2 posts
                print(f"\nPost {i+1}:")
                print(f"  Author: {post.get('author_name')}")
                print(f"  Type: {post.get('type')}")
                print(f"  Post Images count: {len(post.get('postImages', []))}")
                
                # Check if URLs are Cloudinary URLs
                for j, img_url in enumerate(post.get('postImages', [])[:2]):
                    if 'cloudinary.com' in img_url:
                        print(f"  ✓ Image {j+1} processed to Cloudinary")
                    else:
                        print(f"  - Image {j+1} not processed: {img_url[:50]}...")
        
    except Exception as e:
        print(f"Error testing LinkedIn: {e}")

def test_youtube_scraping():
    """Test YouTube scraping with media processing."""
    print("\nTesting YouTube scraping with media processing...")
    
    try:
        result = scrape_social_media(
            platform='youtube',
            identifier='GoogleDevelopers',
            limit=2,
            days_back=30
        )
        
        print(f"Success: {result.get('success')}")
        print(f"Method used: {result.get('method_used')}")
        print(f"Count: {result.get('count')}")
        
        if result.get('success') and result.get('data'):
            for i, video in enumerate(result['data'][:2]):  # Show first 2 videos
                print(f"\nVideo {i+1}:")
                print(f"  Title: {video.get('title', '')[:50]}...")
                print(f"  Channel: {video.get('channel_name')}")
                print(f"  Thumbnail URL: {video.get('thumbnail_url', 'None')[:100]}...")
                
                # Check if URL is Cloudinary URL
                if video.get('thumbnail_url') and 'cloudinary.com' in video.get('thumbnail_url', ''):
                    print("  ✓ Thumbnail URL processed to Cloudinary")
        
    except Exception as e:
        print(f"Error testing YouTube: {e}")

def test_reddit_scraping():
    """Test Reddit scraping (no media processing expected)."""
    print("\nTesting Reddit scraping (no media processing)...")
    
    try:
        result = scrape_social_media(
            platform='reddit',
            identifier='python',
            limit=2
        )
        
        print(f"Success: {result.get('success')}")
        print(f"Method used: {result.get('method_used')}")
        print(f"Count: {result.get('count')}")
        
        if result.get('success') and result.get('data'):
            for i, post in enumerate(result['data'][:2]):  # Show first 2 posts
                print(f"\nPost {i+1}:")
                print(f"  Title: {post.get('title', '')[:50]}...")
                print(f"  Author: {post.get('author')}")
                print(f"  URL: {post.get('url', 'None')[:50]}...")
                print("  ✓ Reddit posts don't require media processing")
        
    except Exception as e:
        print(f"Error testing Reddit: {e}")

if __name__ == "__main__":
    print("=== Testing Media Processing Integration ===\n")
    
    # Check required environment variables
    required_vars = ['CLOUDINARY_CLOUD_NAME', 'CLOUDINARY_UPLOAD_PRESET']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Warning: Missing environment variables: {missing_vars}")
        print("Media processing may fail without proper Cloudinary configuration.\n")
    
    # Run tests
    # test_instagram_scraping()
    test_linkedin_scraping()
    # test_youtube_scraping()
    # test_reddit_scraping()
    
    print("\n=== Test Complete ===")