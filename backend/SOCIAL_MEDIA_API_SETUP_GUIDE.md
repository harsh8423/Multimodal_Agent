# Social Media API Setup Guide

This guide will walk you through setting up the APIs required to run the social media publisher tools:
- `instagram_publisher.py`
- `facebook_publisher.py` 
- `linkedin_publisher.py`
- `youtube_publisher.py`

## Prerequisites

- Developer accounts for each platform
- Basic understanding of OAuth 2.0
- Access to create apps/credentials on each platform

---

## 1. Instagram Graph API Setup

### Requirements
- Instagram Business Account
- Facebook Page connected to Instagram account
- Facebook Developer Account

### Step-by-Step Setup

1. **Create Facebook App**
   - Go to [Facebook Developers](https://developers.facebook.com/)
   - Click "Create App" → "Business" → "Continue"
   - Enter app name and contact email
   - Add "Instagram Graph API" product

2. **Configure Instagram Basic Display**
   - In your app dashboard, go to "Instagram Basic Display"
   - Add Instagram Testers (your Instagram account)
   - Set up OAuth redirect URIs

3. **Get Page Access Token**
   - Go to "Graph API Explorer" in your app
   - Select your app and generate a User Access Token
   - Add permissions: `instagram_basic`, `instagram_content_publish`, `pages_read_engagement`
   - Exchange for a Page Access Token

4. **Get Required IDs**
   - **Page ID**: Found in your Facebook Page settings
   - **Instagram Business Account ID**: Use Graph API Explorer to get from your page

### Environment Variables
```bash
INSTAGRAM_ACCESS_TOKEN=your_page_access_token_here
FACEBOOK_PAGE_ID=your_facebook_page_id_here
```

---

## 2. Facebook Graph API Setup

### Requirements
- Facebook Developer Account
- Facebook Page (for publishing)

### Step-by-Step Setup

1. **Create Facebook App**
   - Go to [Facebook Developers](https://developers.facebook.com/)
   - Click "Create App" → "Business" → "Continue"
   - Add "Facebook Login" product

2. **Configure App Settings**
   - Set Valid OAuth Redirect URIs
   - Add your domain to App Domains
   - Configure Facebook Login settings

3. **Get Page Access Token**
   - Use Graph API Explorer
   - Generate User Access Token with permissions:
     - `pages_manage_posts`
     - `pages_read_engagement` 
     - `pages_show_list`
   - Exchange for Page Access Token

4. **Get Page ID**
   - Found in your Facebook Page settings
   - Or use Graph API: `/me/accounts`

### Environment Variables
```bash
FACEBOOK_ACCESS_TOKEN=your_page_access_token_here
FACEBOOK_PAGE_ID=your_facebook_page_id_here
```

---

## 3. LinkedIn Marketing API Setup

### Requirements
- LinkedIn Developer Account
- LinkedIn Company Page (for organization posts)
- Marketing Developer Platform access

### Step-by-Step Setup

1. **Create LinkedIn App**
   - Go to [LinkedIn Developers](https://www.linkedin.com/developers/)
   - Click "Create app"
   - Fill in app details and verify your LinkedIn account

2. **Request Marketing Developer Platform Access**
   - In your app dashboard, go to "Products"
   - Request access to "Marketing Developer Platform"
   - Wait for approval (can take several days)

3. **Configure OAuth 2.0**
   - Go to "Auth" tab
   - Add redirect URLs
   - Note your Client ID and Client Secret

4. **Get Access Token**
   - Use OAuth 2.0 flow with scopes:
     - `w_organization_social` (for company posts)
     - `w_member_social` (for personal posts)

5. **Get Organization ID** (if posting as company)
   - Use LinkedIn API: `/organizations` endpoint
   - Or find in your company page URL

### Environment Variables
```bash
LINKEDIN_CLIENT_ID=your_linkedin_client_id_here
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret_here
LINKEDIN_ACCESS_TOKEN=your_linkedin_access_token_here
LINKEDIN_ORGANIZATION_ID=your_organization_id_here  # Optional
```

---

## 4. YouTube Data API v3 Setup

### Requirements
- Google Cloud Project
- YouTube Channel
- OAuth 2.0 credentials

### Step-by-Step Setup

1. **Create Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project or select existing one
   - Enable "YouTube Data API v3"

2. **Create OAuth 2.0 Credentials**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth 2.0 Client ID"
   - Choose "Desktop application"
   - Download the JSON file

3. **Get Refresh Token**
   - Go to [OAuth 2.0 Playground](https://developers.google.com/oauthplayground/)
   - Click the gear icon and check "Use your own OAuth credentials"
   - Enter your Client ID and Client Secret
   - Select scope: `https://www.googleapis.com/auth/youtube.upload`
   - Authorize and exchange for refresh token

4. **Extract Credentials**
   - From downloaded JSON: `client_id`, `client_secret`
   - From OAuth Playground: `refresh_token`

### Environment Variables
```bash
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_REFRESH_TOKEN=your_google_refresh_token_here
```

---

## 5. Environment Variables Template

Create a `.env` file in your backend directory:

```bash
# Instagram/Facebook
INSTAGRAM_ACCESS_TOKEN=your_instagram_page_access_token
FACEBOOK_ACCESS_TOKEN=your_facebook_page_access_token
FACEBOOK_PAGE_ID=your_facebook_page_id

# LinkedIn
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret
LINKEDIN_ACCESS_TOKEN=your_linkedin_access_token
LINKEDIN_ORGANIZATION_ID=your_linkedin_organization_id

# YouTube
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REFRESH_TOKEN=your_google_refresh_token
```

---

## 6. Testing Your Setup

### Test Instagram Publisher
```python
from tools.instagram_publisher import setup_instagram_auth, create_instagram_publisher

try:
    access_token, page_id = setup_instagram_auth()
    publisher = create_instagram_publisher(access_token, page_id)
    print("Instagram setup successful!")
except Exception as e:
    print(f"Instagram setup failed: {e}")
```

### Test Facebook Publisher
```python
from tools.facebook_publisher import setup_facebook_auth, create_facebook_publisher

try:
    access_token, page_id = setup_facebook_auth()
    publisher = create_facebook_publisher(access_token, page_id)
    print("Facebook setup successful!")
except Exception as e:
    print(f"Facebook setup failed: {e}")
```

### Test LinkedIn Publisher
```python
from tools.linkedin_publisher import setup_linkedin_auth, create_linkedin_publisher

try:
    access_token, org_id = setup_linkedin_auth()
    publisher = create_linkedin_publisher(access_token, org_id)
    print("LinkedIn setup successful!")
except Exception as e:
    print(f"LinkedIn setup failed: {e}")
```

### Test YouTube Publisher
```python
from tools.youtube_publisher import setup_youtube_auth, create_youtube_publisher

try:
    client_id, client_secret, refresh_token = setup_youtube_auth()
    publisher = create_youtube_publisher(client_id, client_secret, refresh_token)
    print("YouTube setup successful!")
except Exception as e:
    print(f"YouTube setup failed: {e}")
```

---

## 7. Common Issues & Troubleshooting

### Instagram Issues
- **"Invalid access token"**: Ensure you're using a Page Access Token, not User Access Token
- **"Page not found"**: Verify your Page ID and that it's connected to Instagram
- **"Permission denied"**: Check that your app has the required permissions

### Facebook Issues
- **"App not live"**: Your app needs to be in Live mode for production use
- **"Invalid OAuth access token"**: Token may have expired, regenerate it
- **"Page access required"**: Ensure you have admin access to the Facebook Page

### LinkedIn Issues
- **"Marketing Developer Platform access required"**: Wait for approval or contact LinkedIn
- **"Invalid organization"**: Verify your Organization ID is correct
- **"Insufficient permissions"**: Check that your access token has the right scopes

### YouTube Issues
- **"API not enabled"**: Enable YouTube Data API v3 in Google Cloud Console
- **"Invalid credentials"**: Verify your OAuth 2.0 credentials are correct
- **"Quota exceeded"**: Check your API quota in Google Cloud Console

---

## 8. Security Best Practices

1. **Never commit credentials to version control**
2. **Use environment variables for all sensitive data**
3. **Rotate access tokens regularly**
4. **Use the principle of least privilege for permissions**
5. **Monitor API usage and set up alerts**
6. **Keep your apps in development mode until ready for production**

---

## 9. Rate Limits & Quotas

### Instagram
- 200 API calls per hour per user
- 25 posts per day per account

### Facebook
- 200 calls per hour per user
- 25 posts per day per page

### LinkedIn
- 100,000 API calls per day
- 100 posts per day per organization

### YouTube
- 10,000 units per day (default quota)
- 1 unit per video upload

---

## 10. Next Steps

Once you have all APIs set up:

1. Test each publisher with simple content
2. Implement error handling in your application
3. Set up monitoring for API usage
4. Create backup/fallback strategies
5. Document your specific use cases

For more detailed information, refer to each platform's official documentation:
- [Instagram Graph API](https://developers.facebook.com/docs/instagram-api/)
- [Facebook Graph API](https://developers.facebook.com/docs/graph-api/)
- [LinkedIn Marketing API](https://docs.microsoft.com/en-us/linkedin/marketing/)
- [YouTube Data API](https://developers.google.com/youtube/v3)