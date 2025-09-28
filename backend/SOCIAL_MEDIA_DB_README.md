# Social Media Database System

A comprehensive MongoDB-based system for managing social media assets, including brands, templates, competitors, and scraped posts across multiple platforms.

## Features

- **Brand Management**: Store brand information, themes, and posting settings
- **Template System**: Flexible, versioned templates for social media content
- **Competitor Tracking**: Monitor competitor accounts across platforms
- **Scraped Posts Storage**: Store and normalize scraped data from Instagram, LinkedIn, YouTube, and Reddit
- **Cloudinary Integration**: Automatic media processing and CDN storage
- **Cross-Platform Normalization**: Unified data format across all platforms

## Database Collections

### 1. Brands
Store user brand information with themes and settings.

```json
{
  "_id": ObjectId("..."),
  "userId": "user_123",
  "name": "Acme Shoes",
  "slug": "acme-shoes",
  "description": "Comfortable urban shoes",
  "theme": {
    "primaryColor": "#123456",
    "secondaryColor": "#abcdef",
    "font": "Inter",
    "logoUrl": "https://cloudinary.com/..."
  },
  "details": {
    "website": "https://acme.example",
    "industry": "fashion",
    "audience": ["students", "professionals"]
  },
  "defaultPostingSettings": {
    "timezone": "Asia/Kolkata",
    "defaultPlatforms": ["instagram", "linkedin"],
    "postApprovalRequired": true
  },
  "createdAt": ISODate(...),
  "updatedAt": ISODate(...)
}
```

### 2. Templates
Flexible, versioned templates for social media content.

```json
{
  "_id": ObjectId("..."),
  "userId": "user_123",
  "brandId": ObjectId("..."),
  "name": "Launch Reel — Short Hook",
  "type": "reel",
  "version": 3,
  "status": "active",
  "structure": {
    "description": "Short-form reel template for product launch",
    "scenes": [
      {
        "sceneId": 1,
        "durationSec": 3,
        "instructions": "Close-up product reveal",
        "visualHints": ["shallow depth", "backlight"],
        "audioCue": "upbeat_intro"
      }
    ],
    "hooks": [
      {"position": "start", "example": "Here's a 10s trick..."},
      {"position": "end", "cta": "Link in bio"}
    ],
    "placeholders": ["headline", "product_shot", "cta_text"],
    "theme": {
      "mood": "playful",
      "colorPalette": ["#FF6B6B", "#FFD93D"],
      "preferredAspect": ["9:16", "1:1"]
    }
  },
  "references": {
    "images": ["https://cloudinary.com/ref1.jpg"],
    "videos": ["https://cloudinary.com/ref_clip.mp4"],
    "notes": "References for camera angles & pacing"
  }
}
```

### 3. Scraped Posts
Platform-specific data with normalized format for cross-platform queries.

```json
{
  "_id": ObjectId("..."),
  "userId": "user_123",
  "brandId": ObjectId("..."),
  "handleId": ObjectId("..."),
  "platform": "instagram",
  "source": "instaloader-v4",
  "scrapedAt": ISODate("2025-01-24T10:00:00Z"),
  "platformData": {
    "username": "ownerUsername123",
    "post_id": "1789....",
    "post_url": "https://instagram.com/p/abc",
    "displayUrl": "https://cloudinary.com/...",
    "videoUrl": "https://cloudinary.com/...mp4",
    "images": ["https://cloudinary.com/...1.jpg"],
    "type": "carousel",
    "caption": "New drops! #shoes",
    "likesCount": 1200,
    "commentsCount": 45,
    "dimensionsHeight": 1080,
    "dimensionsWidth": 1080
  },
  "normalized": {
    "text": "New drops! #shoes",
    "media": [
      {"type": "image", "url": "https://cloudinary.com/...1.jpg"}
    ],
    "postedAt": null,
    "engagement": {"likes": 1200, "comments": 45},
    "sourceId": "IG_1789...."
  },
  "processing": {
    "status": "normalized",
    "pipeline": "insta-v1",
    "normalizedAt": ISODate(...)
  }
}
```

### 4. Competitors
Platform-agnostic competitor/reference account tracking.

```json
{
  "_id": ObjectId("..."),
  "userId": "user_123",
  "brandId": ObjectId("..."),
  "name": "RivalBrand",
  "platform": "instagram",
  "handle": "@rival",
  "profileUrl": "https://instagram.com/rival",
  "metrics": {
    "followers": 120000,
    "avgEngagement": 0.03
  },
  "scrapeConfig": {
    "scrapedAt": ISODate(...),
    "scrapeFrequency": "weekly",
    "autoScrape": false
  },
  "metadata": {
    "notes": "Good Reels on weekends",
    "tags": ["inspiration", "local"]
  },
  "createdAt": ISODate(...)
}
```

## Usage

### 1. Database Service

```python
from services.social_media_db import social_media_db

# Create a brand
brand_data = {
    "user_id": "user_123",
    "name": "My Brand",
    "slug": "my-brand",
    "description": "Brand description",
    "theme": {
        "primary_color": "#FF6B6B",
        "secondary_color": "#4ECDC4",
        "font": "Inter"
    },
    "details": {
        "website": "https://mybrand.com",
        "industry": "technology"
    }
}
brand_id = await social_media_db.create_brand(brand_data)

# Get brands for a user
brands = await social_media_db.get_brands_by_user("user_123")
```

### 2. Scraping with Database Storage

```python
from tools.unified_scraper import scrape_social_media

# Scrape and save to database
result = await scrape_social_media(
    platform="instagram",
    identifier="google",
    user_id="user_123",
    brand_id="brand_123",
    limit=10,
    save_to_db=True
)

# Retrieve scraped posts
posts = await social_media_db.get_scraped_posts_by_user(
    user_id="user_123",
    platform=PlatformType.INSTAGRAM,
    limit=20
)
```

### 3. Template Management

```python
# Create a template
template_data = {
    "user_id": "user_123",
    "brand_id": "brand_123",
    "name": "Product Launch Reel",
    "type": "reel",
    "structure": {
        "description": "Template for product launches",
        "scenes": [...],
        "hooks": [...],
        "theme": {...}
    }
}
template_id = await social_media_db.create_template(template_data)
```

## Key Features

### Media Processing
- Automatic download of media files from platform URLs
- Upload to Cloudinary CDN for fast delivery
- Replacement of original URLs with Cloudinary URLs
- Support for images and videos

### Data Normalization
- Platform-specific data preserved in `platformData`
- Normalized format in `normalized` for cross-platform queries
- Consistent engagement metrics across platforms
- Unified media item structure

### Error Handling
- Graceful fallbacks when scraping fails
- Processing status tracking
- Error messages stored for debugging
- Batch operations for efficiency

## Testing

Run the test script to verify the integration:

```bash
cd backend
python test_social_media_db.py
```

Run the usage examples:

```bash
cd backend
python example_usage.py
```

## Environment Variables

Make sure these environment variables are set:

```bash
MONGODB_URL=mongodb://localhost:27017
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
APIFY_API_TOKEN=your_apify_token  # Optional
YOUTUBE_API_KEY=your_youtube_key  # Optional
REDDIT_CLIENT_ID=your_reddit_id   # Optional
REDDIT_CLIENT_SECRET=your_reddit_secret  # Optional
REDDIT_USER_AGENT=your_user_agent  # Optional
```

## Supported Platforms

- **Instagram**: Apify API with code-based fallback
- **LinkedIn**: Apify API
- **YouTube**: Official YouTube API
- **Reddit**: PRAW (Python Reddit API Wrapper)

## Database Indexes

Recommended indexes for optimal performance:

```javascript
// Brands collection
db.brands.createIndex({"userId": 1, "slug": 1}, {"unique": true})
db.brands.createIndex({"userId": 1})

// Templates collection
db.templates.createIndex({"userId": 1, "brandId": 1})
db.templates.createIndex({"userId": 1, "type": 1, "status": 1})

// Scraped posts collection
db.scraped_posts.createIndex({"userId": 1, "platform": 1, "scrapedAt": -1})
db.scraped_posts.createIndex({"userId": 1, "brandId": 1})
db.scraped_posts.createIndex({"normalized.sourceId": 1})

// Competitors collection
db.competitors.createIndex({"userId": 1, "platform": 1})
db.competitors.createIndex({"userId": 1, "brandId": 1})
```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API    │    │   MongoDB       │
│                 │    │                  │    │                 │
│ - Brand UI      │◄──►│ - Routes         │◄──►│ - brands        │
│ - Template UI   │    │ - Services       │    │ - templates     │
│ - Analytics UI  │    │ - Models         │    │ - scraped_posts │
└─────────────────┘    └──────────────────┘    │ - competitors   │
                                │               └─────────────────┘
                                ▼
                       ┌──────────────────┐
                       │  Unified Scraper │
                       │                  │
                       │ - Instagram      │
                       │ - LinkedIn       │
                       │ - YouTube        │
                       │ - Reddit         │
                       └──────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   Cloudinary     │
                       │                  │
                       │ - Media Storage  │
                       │ - CDN Delivery   │
                       └──────────────────┘
```

This system provides a complete solution for social media asset management with automatic data processing, storage, and retrieval capabilities.