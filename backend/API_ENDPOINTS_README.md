# Social Media Management API Endpoints

This document provides a comprehensive overview of all API endpoints for the Social Media Management system.

## Base URL
```
http://localhost:8000
```

## Authentication
All endpoints require authentication using JWT tokens. Include the token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

## Endpoints Overview

### 1. Brands Management (`/api/brands`)

#### Create Brand
```http
POST /api/brands/
Content-Type: application/json

{
  "name": "Acme Shoes",
  "slug": "acme-shoes",
  "description": "Comfortable urban shoes",
  "theme": {
    "primary_color": "#123456",
    "secondary_color": "#abcdef",
    "font": "Inter",
    "logo_url": "https://cloudinary.com/..."
  },
  "details": {
    "website": "https://acme.example",
    "industry": "fashion",
    "audience": ["students", "professionals"]
  },
  "default_posting_settings": {
    "timezone": "Asia/Kolkata",
    "default_platforms": ["instagram", "linkedin"],
    "post_approval_required": true
  }
}
```

#### Get Brands
```http
GET /api/brands/?page=1&limit=20&search=acme
```

#### Get Brand by ID
```http
GET /api/brands/{brand_id}
```

#### Update Brand
```http
PUT /api/brands/{brand_id}
Content-Type: application/json

{
  "name": "Updated Brand Name",
  "theme": {
    "primary_color": "#654321"
  }
}
```

#### Delete Brand
```http
DELETE /api/brands/{brand_id}
```

#### Get Brand Statistics
```http
GET /api/brands/{brand_id}/stats
```

#### Duplicate Brand
```http
POST /api/brands/{brand_id}/duplicate?new_name=New Brand&new_slug=new-brand
```

### 2. Templates Management (`/api/templates`)

#### Create Template
```http
POST /api/templates/
Content-Type: application/json

{
  "brand_id": "brand_123",
  "name": "Product Launch Reel",
  "type": "reel",
  "structure": {
    "description": "Short-form reel template for product launches",
    "scenes": [
      {
        "scene_id": 1,
        "duration_sec": 3,
        "instructions": "Product reveal with dramatic music",
        "visual_hints": ["close-up", "backlight", "slow motion"],
        "audio_cue": "dramatic_intro"
      }
    ],
    "hooks": [
      {"position": "start", "example": "This changes everything..."},
      {"position": "end", "cta": "Link in bio to get yours"}
    ],
    "placeholders": ["product_name", "key_feature", "price"],
    "theme": {
      "mood": "exciting",
      "color_palette": ["#FF6B6B", "#4ECDC4", "#45B7D1"],
      "preferred_aspect": ["9:16", "1:1"]
    },
    "description_prompt": "Generate 3 caption options (<=110 chars) with 3 relevant hashtags"
  },
  "references": {
    "images": ["https://cloudinary.com/ref1.jpg"],
    "videos": ["https://cloudinary.com/ref_clip.mp4"],
    "notes": "References for camera angles and pacing"
  }
}
```

#### Get Templates
```http
GET /api/templates/?brand_id=brand_123&type=reel&status=active&page=1&limit=20
```

#### Get Template by ID
```http
GET /api/templates/{template_id}
```

#### Update Template
```http
PUT /api/templates/{template_id}
Content-Type: application/json

{
  "name": "Updated Template Name",
  "status": "archived"
}
```

#### Delete Template
```http
DELETE /api/templates/{template_id}
```

#### Duplicate Template
```http
POST /api/templates/{template_id}/duplicate?new_name=New Template
```

#### Archive Template
```http
POST /api/templates/{template_id}/archive
```

#### Activate Template
```http
POST /api/templates/{template_id}/activate
```

#### Get Template Statistics
```http
GET /api/templates/{template_id}/stats
```

### 3. Competitors Management (`/api/competitors`)

#### Create Competitor
```http
POST /api/competitors/
Content-Type: application/json

{
  "brand_id": "brand_123",
  "name": "Competitor Brand",
  "platform": "instagram",
  "handle": "@competitor",
  "profile_url": "https://instagram.com/competitor",
  "metrics": {
    "followers": 50000,
    "avg_engagement": 0.05
  },
  "scrape_config": {
    "scrape_frequency": "weekly",
    "auto_scrape": false
  },
  "metadata": {
    "notes": "Good Reels on weekends",
    "tags": ["inspiration", "local"]
  }
}
```

#### Get Competitors
```http
GET /api/competitors/?brand_id=brand_123&platform=instagram&page=1&limit=20
```

#### Get Competitor by ID
```http
GET /api/competitors/{competitor_id}
```

#### Update Competitor
```http
PUT /api/competitors/{competitor_id}
Content-Type: application/json

{
  "name": "Updated Competitor Name",
  "metrics": {
    "followers": 60000,
    "avg_engagement": 0.06
  }
}
```

#### Delete Competitor
```http
DELETE /api/competitors/{competitor_id}
```

#### Update Competitor Metrics
```http
PUT /api/competitors/{competitor_id}/metrics
Content-Type: application/json

{
  "followers": 75000,
  "avg_engagement": 0.07,
  "posts_count": 1200
}
```

#### Get Competitor Statistics
```http
GET /api/competitors/{competitor_id}/stats
```

#### Scrape Competitor
```http
POST /api/competitors/{competitor_id}/scrape?limit=10
```

#### Duplicate Competitor
```http
POST /api/competitors/{competitor_id}/duplicate?new_name=New Competitor
```

### 4. Scraped Posts Management (`/api/scraped-posts`)

#### Get Scraped Posts
```http
GET /api/scraped-posts/?brand_id=brand_123&platform=instagram&status=normalized&page=1&limit=20&sort_by=scraped_at&sort_order=desc
```

#### Get Post by ID
```http
GET /api/scraped-posts/{post_id}
```

#### Delete Post
```http
DELETE /api/scraped-posts/{post_id}
```

#### Get Posts Analytics
```http
GET /api/scraped-posts/analytics/overview?brand_id=brand_123&platform=instagram&days_back=30
```

#### Get Engagement Analytics
```http
GET /api/scraped-posts/analytics/engagement?brand_id=brand_123&days_back=30
```

#### Bulk Delete Posts
```http
POST /api/scraped-posts/bulk-delete
Content-Type: application/json

["post_id_1", "post_id_2", "post_id_3"]
```

#### Advanced Search
```http
GET /api/scraped-posts/search/advanced?query=product launch&min_likes=100&has_media=true&page=1&limit=20
```

### 5. Scraping Operations (`/api/scraping`)

#### Scrape Single Platform
```http
POST /api/scraping/scrape
Content-Type: application/json

{
  "platform": "instagram",
  "identifier": "google",
  "brand_id": "brand_123",
  "limit": 10,
  "days_back": 7,
  "save_to_db": true
}
```

#### Batch Scraping
```http
POST /api/scraping/scrape/batch
Content-Type: application/json

{
  "requests": [
    {
      "platform": "instagram",
      "identifier": "google",
      "limit": 5
    },
    {
      "platform": "youtube",
      "identifier": "GoogleDevelopers",
      "limit": 3
    }
  ],
  "save_to_db": true
}
```

#### Get Supported Platforms
```http
GET /api/scraping/platforms
```

#### Get Scraping Status
```http
GET /api/scraping/status/instagram/google
```

#### Scrape Competitor
```http
POST /api/scraping/competitor/{competitor_id}/scrape?limit=10
```

#### Get Scraping History
```http
GET /api/scraping/history?platform=instagram&days_back=7&page=1&limit=20
```

## Response Formats

### Success Response
```json
{
  "id": "object_id",
  "name": "Resource Name",
  "created_at": "2025-01-24T10:00:00Z",
  "updated_at": "2025-01-24T10:00:00Z"
}
```

### Error Response
```json
{
  "detail": "Error message",
  "error": "Detailed error information"
}
```

### List Response
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "limit": 20
}
```

## Query Parameters

### Pagination
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20, max: 100)

### Filtering
- `brand_id`: Filter by brand ID
- `platform`: Filter by platform (instagram, linkedin, youtube, reddit)
- `status`: Filter by status
- `search`: Search term
- `date_from`: Filter from date
- `date_to`: Filter to date

### Sorting
- `sort_by`: Sort field
- `sort_order`: Sort order (asc/desc)

## Platform-Specific Parameters

### Instagram
- `identifier`: Username (without @)
- `days_back`: Number of days to look back
- `api_token`: Apify API token (optional)

### LinkedIn
- `identifier`: Profile URL
- `api_token`: Apify API token (required)

### YouTube
- `identifier`: Channel username
- `days_back`: Number of days to look back
- `api_key`: YouTube API key (required)

### Reddit
- `identifier`: Subreddit name (without r/)
- `category`: hot, rising, new, top
- `min_score`: Minimum score
- `min_comments`: Minimum comments

## Rate Limits
- Scraping endpoints: 10 requests per minute
- Other endpoints: 100 requests per minute

## Error Codes
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `500`: Internal Server Error

## Examples

### Complete Workflow Example

1. **Create a Brand**
```bash
curl -X POST "http://localhost:8000/api/brands/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Brand",
    "slug": "my-brand",
    "description": "A great brand",
    "theme": {
      "primary_color": "#FF6B6B",
      "secondary_color": "#4ECDC4",
      "font": "Inter"
    },
    "details": {
      "website": "https://mybrand.com",
      "industry": "technology"
    }
  }'
```

2. **Add a Competitor**
```bash
curl -X POST "http://localhost:8000/api/competitors/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "brand_id": "BRAND_ID",
    "name": "Competitor",
    "platform": "instagram",
    "handle": "@competitor",
    "profile_url": "https://instagram.com/competitor"
  }'
```

3. **Scrape Competitor Data**
```bash
curl -X POST "http://localhost:8000/api/scraping/competitor/COMPETITOR_ID/scrape?limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

4. **Get Scraped Posts**
```bash
curl -X GET "http://localhost:8000/api/scraped-posts/?brand_id=BRAND_ID&platform=instagram" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

5. **Create a Template**
```bash
curl -X POST "http://localhost:8000/api/templates/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "brand_id": "BRAND_ID",
    "name": "Product Launch Template",
    "type": "reel",
    "structure": {
      "description": "Template for product launches",
      "theme": {
        "mood": "exciting",
        "color_palette": ["#FF6B6B", "#4ECDC4"],
        "preferred_aspect": ["9:16"]
      }
    }
  }'
```

This API provides a complete solution for social media asset management with full CRUD operations, scraping capabilities, and analytics.