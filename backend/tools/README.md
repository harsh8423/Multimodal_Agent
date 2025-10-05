# Social Media Publishing Tools

This repository contains four functional programming tools for publishing content to major social media platforms using their official APIs:

1. **Instagram Publisher** - Images, videos, reels, carousels, stories with scheduling
2. **YouTube Publisher** - Shorts and regular videos with scheduling
3. **LinkedIn Publisher** - Text, images, videos, articles, carousels, polls with scheduling
4. **Facebook Publisher** - Text, images, videos, carousels, links with scheduling

## Features

- ✅ **Functional Programming**: Pure functions with no side effects
- ✅ **Official APIs**: Uses only official platform APIs
- ✅ **Scheduling Support**: Schedule posts for future publication
- ✅ **Multiple Content Types**: Support for various content formats
- ✅ **Error Handling**: Comprehensive error handling and validation
- ✅ **Type Safety**: Full type hints and dataclasses
- ✅ **Authentication Helpers**: Built-in OAuth flow helpers

## Quick Start

### 1. Instagram Publisher

```python
from backend.tools.instagram_publisher import (
    create_instagram_publisher, 
    publish_image_post,
    setup_instagram_auth
)

# Setup authentication
access_token, page_id = setup_instagram_auth()
publisher = create_instagram_publisher(access_token, page_id)

# Publish an image post
response = publish_image_post(
    publisher=publisher,
    image_url="https://example.com/image.jpg",
    caption="Check out this amazing image! #instagram #photo",
    alt_text="A beautiful landscape photo"
)

if response.success:
    print(f"Post published! Media ID: {response.media_id}")
```

### 2. YouTube Publisher

```python
from backend.tools.youtube_publisher import (
    create_youtube_publisher,
    publish_shorts_video,
    setup_youtube_auth
)

# Setup authentication
client_id, client_secret, refresh_token = setup_youtube_auth()
publisher = create_youtube_publisher(client_id, client_secret, refresh_token)

# Publish a Shorts video
response = publish_shorts_video(
    publisher=publisher,
    video_path="path/to/shorts_video.mp4",
    title="Amazing Shorts Video! #Shorts",
    description="Check out this incredible short video content!",
    tags=["shorts", "viral", "funny"]
)

if response.success:
    print(f"Video published! Video ID: {response.video_id}")
```

### 3. LinkedIn Publisher

```python
from backend.tools.linkedin_publisher import (
    create_linkedin_publisher,
    publish_image_post,
    setup_linkedin_auth
)

# Setup authentication
access_token, organization_id = setup_linkedin_auth()
publisher = create_linkedin_publisher(access_token, organization_id)

# Publish an image post
response = publish_image_post(
    publisher=publisher,
    image_url="https://example.com/image.jpg",
    caption="Excited to share this update with my network! #LinkedIn"
)

if response.success:
    print(f"Post published! Post ID: {response.post_id}")
```

### 4. Facebook Publisher

```python
from backend.tools.facebook_publisher import (
    create_facebook_publisher,
    publish_image_post,
    setup_facebook_auth
)

# Setup authentication
access_token, page_id = setup_facebook_auth()
publisher = create_facebook_publisher(access_token, page_id)

# Publish an image post
response = publish_image_post(
    publisher=publisher,
    image_url="https://example.com/image.jpg",
    message="Excited to share this amazing update! #Facebook"
)

if response.success:
    print(f"Post published! Post ID: {response.post_id}")
```

## Authentication Setup

### Instagram Authentication

1. **Create Facebook App**:
   - Go to [Facebook Developers](https://developers.facebook.com/)
   - Create a new app or use existing one
   - Add Instagram Graph API product

2. **Configure Instagram Basic Display**:
   - Go to Instagram Basic Display settings
   - Add valid OAuth redirect URIs
   - Create Instagram app

3. **Get Page Access Token**:
   - Connect Instagram account to Facebook Page
   - Get Page Access Token with permissions:
     - `instagram_basic`
     - `instagram_content_publish`
     - `pages_read_engagement`

4. **Set Environment Variables**:
   ```bash
   export INSTAGRAM_ACCESS_TOKEN="your_page_access_token"
   export FACEBOOK_PAGE_ID="your_page_id"
   ```

### YouTube Authentication

1. **Create Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project or select existing
   - Enable YouTube Data API v3

2. **Create OAuth 2.0 Credentials**:
   - Go to Credentials → Create Credentials → OAuth 2.0 Client ID
   - Choose "Desktop application"
   - Download JSON file

3. **Get Refresh Token**:
   - Go to [OAuth 2.0 Playground](https://developers.google.com/oauthplayground/)
   - Select YouTube Data API v3
   - Select scope: `https://www.googleapis.com/auth/youtube.upload`
   - Authorize and exchange for refresh token

4. **Set Environment Variables**:
   ```bash
   export GOOGLE_CLIENT_ID="your_client_id"
   export GOOGLE_CLIENT_SECRET="your_client_secret"
   export GOOGLE_REFRESH_TOKEN="your_refresh_token"
   ```

### LinkedIn Authentication

1. **Create LinkedIn App**:
   - Go to [LinkedIn Developers](https://www.linkedin.com/developers/)
   - Create new app or use existing
   - Request Marketing Developer Platform access

2. **Configure OAuth 2.0**:
   - Add redirect URIs
   - Request permissions: `w_organization_social`, `w_member_social`

3. **Get Access Token**:
   - Use OAuth 2.0 flow to get access token
   - Get organization ID if posting on behalf of organization

4. **Set Environment Variables**:
   ```bash
   export LINKEDIN_ACCESS_TOKEN="your_access_token"
   export LINKEDIN_ORGANIZATION_ID="your_organization_id"  # Optional
   ```

### Facebook Authentication

1. **Create Facebook App**:
   - Go to [Facebook Developers](https://developers.facebook.com/)
   - Create new app or use existing
   - Add Facebook Login product

2. **Get Page Access Token**:
   - Get Page Access Token with permissions:
     - `pages_manage_posts`
     - `pages_read_engagement`
     - `pages_show_list`

3. **Set Environment Variables**:
   ```bash
   export FACEBOOK_ACCESS_TOKEN="your_page_access_token"
   export FACEBOOK_PAGE_ID="your_page_id"
   ```

## Content Types Supported

### Instagram
- ✅ Single image posts
- ✅ Single video posts
- ✅ Instagram Reels
- ✅ Instagram Stories
- ✅ Carousel posts (up to 10 items)
- ✅ Scheduled publishing

### YouTube
- ✅ Regular videos
- ✅ YouTube Shorts
- ✅ Custom thumbnails
- ✅ Video metadata (title, description, tags)
- ✅ Scheduled publishing
- ✅ Privacy settings (public, private, unlisted)

### LinkedIn
- ✅ Text-only posts
- ✅ Image posts
- ✅ Video posts
- ✅ Article posts (with links)
- ✅ Carousel posts (sponsored only)
- ✅ Poll posts
- ✅ Scheduled publishing

### Facebook
- ✅ Text-only posts
- ✅ Image posts
- ✅ Video posts
- ✅ Carousel posts (multiple images)
- ✅ Link posts
- ✅ Short videos (like Reels)
- ✅ Scheduled publishing

## Scheduling Posts

All tools support scheduling posts for future publication:

```python
from datetime import datetime, timedelta

# Schedule post for tomorrow at 2 PM
scheduled_time = datetime.now() + timedelta(days=1)
scheduled_time = scheduled_time.replace(hour=14, minute=0, second=0, microsecond=0)

# Instagram
response = publish_image_post(
    publisher=instagram_publisher,
    image_url="https://example.com/image.jpg",
    caption="Scheduled post!",
    scheduled_time=scheduled_time
)

# YouTube
response = publish_shorts_video(
    publisher=youtube_publisher,
    video_path="video.mp4",
    title="Scheduled Shorts Video",
    description="This was scheduled!",
    scheduled_time=scheduled_time
)

# LinkedIn
response = publish_image_post(
    publisher=linkedin_publisher,
    image_url="https://example.com/image.jpg",
    caption="Scheduled LinkedIn post",
    scheduled_time=scheduled_time
)

# Facebook
response = publish_image_post(
    publisher=facebook_publisher,
    image_url="https://example.com/image.jpg",
    message="Scheduled Facebook post",
    scheduled_time=scheduled_time
)
```

## Error Handling

All tools return structured response objects with success status and error messages:

```python
response = publish_image_post(publisher, image_url, caption)

if response.success:
    print(f"Success! Post ID: {response.post_id}")
else:
    print(f"Error: {response.error_message}")
```

## Rate Limits

Each platform has different rate limits:

- **Instagram**: 100 posts per 24 hours
- **YouTube**: 6 uploads per day (unverified), higher limits for verified accounts
- **LinkedIn**: Varies by account type and permissions
- **Facebook**: Varies by page size and activity

## Best Practices

1. **Always check rate limits** before publishing
2. **Use proper error handling** for all API calls
3. **Validate content** before uploading (file sizes, formats)
4. **Test with small content** before bulk operations
5. **Monitor API quotas** and usage
6. **Keep access tokens secure** and refresh them regularly

## Dependencies

```bash
pip install requests python-dateutil
```

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
1. Check the official API documentation for each platform
2. Verify your authentication setup
3. Check rate limits and quotas
4. Review error messages for specific guidance

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Disclaimer

These tools are for educational and development purposes. Always comply with each platform's Terms of Service and API usage policies. The authors are not responsible for any misuse or violations of platform policies.