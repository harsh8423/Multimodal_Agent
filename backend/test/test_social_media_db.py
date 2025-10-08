"""
Test script for Social Media Database Integration

This script tests the integration between unified_scraper.py and the MongoDB database
to ensure scraped data is properly saved with Cloudinary URLs.
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import connect_to_mongo, close_mongo_connection
from tools.unified_scraper import scrape_social_media
from services.social_media_db import social_media_db
from models.social_media import PlatformType


async def test_instagram_scraping():
    """Test Instagram scraping and database storage"""
    print("Testing Instagram scraping and database storage...")
    
    # Test user ID (you can replace with a real user ID)
    test_user_id = "test_user_123"
    
    try:
        # Scrape Instagram data
        result = await scrape_social_media(
            platform="instagram",
            identifier="google",  # Test with Google's Instagram
            user_id=test_user_id,
            limit=3,
            days_back=7,
            save_to_db=True
        )
        
        print(f"Instagram scraping result: {result.get('success', False)}")
        if result.get('success'):
            print(f"Scraped {result.get('count', 0)} posts")
            print(f"Method used: {result.get('method_used', 'unknown')}")
            
            # Check if data was saved to database
            posts = await social_media_db.get_scraped_posts_by_user(
                user_id=test_user_id,
                platform=PlatformType.INSTAGRAM,
                limit=10
            )
            
            print(f"Found {len(posts)} posts in database")
            
            if posts:
                # Check the first post structure
                first_post = posts[0]
                print("\nFirst post structure:")
                print(f"Platform: {first_post.get('platform')}")
                print(f"Source: {first_post.get('source')}")
                print(f"Scraped at: {first_post.get('scraped_at')}")
                
                # Check platform data
                platform_data = first_post.get('platform_data', {})
                print(f"Platform data keys: {list(platform_data.keys())}")
                
                # Check normalized data
                normalized = first_post.get('normalized', {})
                print(f"Normalized text: {normalized.get('text', '')[:100]}...")
                print(f"Media items: {len(normalized.get('media', []))}")
                
                # Check if URLs are Cloudinary URLs
                for media_item in normalized.get('media', []):
                    url = media_item.get('url', '')
                    if 'cloudinary.com' in url:
                        print(f"✓ Cloudinary URL found: {url[:50]}...")
                    else:
                        print(f"⚠ Non-Cloudinary URL: {url[:50]}...")
        else:
            print(f"Instagram scraping failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"Error testing Instagram: {str(e)}")


async def test_youtube_scraping():
    """Test YouTube scraping and database storage"""
    print("\nTesting YouTube scraping and database storage...")
    
    test_user_id = "test_user_123"
    
    try:
        # Scrape YouTube data
        result = await scrape_social_media(
            platform="youtube",
            identifier="GoogleDevelopers",
            user_id=test_user_id,
            limit=2,
            days_back=30,
            save_to_db=True
        )
        
        print(f"YouTube scraping result: {result.get('success', False)}")
        if result.get('success'):
            print(f"Scraped {result.get('count', 0)} videos")
            
            # Check if data was saved to database
            posts = await social_media_db.get_scraped_posts_by_user(
                user_id=test_user_id,
                platform=PlatformType.YOUTUBE,
                limit=10
            )
            
            print(f"Found {len(posts)} videos in database")
            
            if posts:
                first_video = posts[0]
                normalized = first_video.get('normalized', {})
                print(f"Video title: {normalized.get('text', '')[:100]}...")
                
                # Check thumbnail URL
                for media_item in normalized.get('media', []):
                    url = media_item.get('url', '')
                    if 'cloudinary.com' in url:
                        print(f"✓ Cloudinary thumbnail URL: {url[:50]}...")
                    else:
                        print(f"⚠ Non-Cloudinary thumbnail URL: {url[:50]}...")
        else:
            print(f"YouTube scraping failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"Error testing YouTube: {str(e)}")


async def test_reddit_scraping():
    """Test Reddit scraping and database storage"""
    print("\nTesting Reddit scraping and database storage...")
    
    test_user_id = "test_user_123"
    
    try:
        # Scrape Reddit data
        result = await scrape_social_media(
            platform="reddit",
            identifier="python",
            user_id=test_user_id,
            limit=3,
            category="hot",
            save_to_db=True
        )
        
        print(f"Reddit scraping result: {result.get('success', False)}")
        if result.get('success'):
            print(f"Scraped {result.get('count', 0)} posts")
            
            # Check if data was saved to database
            posts = await social_media_db.get_scraped_posts_by_user(
                user_id=test_user_id,
                platform=PlatformType.REDDIT,
                limit=10
            )
            
            print(f"Found {len(posts)} posts in database")
            
            if posts:
                first_post = posts[0]
                normalized = first_post.get('normalized', {})
                print(f"Post title: {normalized.get('text', '')[:100]}...")
                print(f"Engagement: {normalized.get('engagement', {})}")
        else:
            print(f"Reddit scraping failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"Error testing Reddit: {str(e)}")


async def test_database_operations():
    """Test basic database operations"""
    print("\nTesting database operations...")
    
    test_user_id = "test_user_123"
    
    try:
        # Test creating a brand
        brand_data = {
            "user_id": test_user_id,
            "name": "Test Brand",
            "slug": "test-brand",
            "description": "A test brand for testing purposes",
            "theme": {
                "primary_color": "#FF6B6B",
                "secondary_color": "#4ECDC4",
                "font": "Inter",
                "logo_url": "https://example.com/logo.png"
            },
            "details": {
                "website": "https://testbrand.com",
                "industry": "technology",
                "audience": ["developers", "designers"]
            }
        }
        
        brand_id = await social_media_db.create_brand(brand_data)
        print(f"✓ Created brand with ID: {brand_id}")
        
        # Test retrieving the brand
        brand = await social_media_db.get_brand_by_id(brand_id)
        if brand:
            print(f"✓ Retrieved brand: {brand['name']}")
        
        # Test creating a competitor
        competitor_data = {
            "user_id": test_user_id,
            "brand_id": brand_id,
            "name": "Competitor Brand",
            "platform": PlatformType.INSTAGRAM.value,
            "handle": "@competitor",
            "profile_url": "https://instagram.com/competitor",
            "metrics": {
                "followers": 50000,
                "avg_engagement": 0.05
            }
        }
        
        competitor_id = await social_media_db.create_competitor(competitor_data)
        print(f"✓ Created competitor with ID: {competitor_id}")
        
        # Test retrieving competitors
        competitors = await social_media_db.get_competitors_by_user(test_user_id)
        print(f"✓ Found {len(competitors)} competitors")
        
    except Exception as e:
        print(f"Error testing database operations: {str(e)}")


async def main():
    """Main test function"""
    print("Starting Social Media Database Integration Tests")
    print("=" * 60)
    
    try:
        # Connect to MongoDB
        await connect_to_mongo()
        print("✓ Connected to MongoDB")
        
        # Test database operations
        await test_database_operations()
        
        # Test scraping and database integration
        await test_instagram_scraping()
        await test_youtube_scraping()
        await test_reddit_scraping()
        
        print("\n" + "=" * 60)
        print("All tests completed!")
        
    except Exception as e:
        print(f"Error in main test: {str(e)}")
        
    finally:
        # Close database connection
        await close_mongo_connection()
        print("✓ Disconnected from MongoDB")


if __name__ == "__main__":
    # Run the tests
    asyncio.run(main())