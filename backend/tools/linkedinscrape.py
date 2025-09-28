
import requests
import os
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def extract_unified_linkedin_metadata(linkedin_data: dict) -> dict:
    """Extract unified metadata from LinkedIn data."""
    # Initialize with default values
    metadata = {
        'caption': '',
        'likes': 0,
        'comments': 0,
        'published_date': '',
        'username': '',
        'content_type': 'linkedin_post',
        'media_urls': []
    }
    
    try:
        # Extract caption/text
        metadata['caption'] = linkedin_data.get('text', '')
        
        # Extract likes count
        metadata['likes'] = linkedin_data.get('numLikes', 0)
        
        # Extract comment count
        metadata['comments'] = linkedin_data.get('numComments', 0)
        
        # Extract published date
        posted_at = linkedin_data.get('postedAtISO', '')
        if posted_at:
            try:
                # Parse ISO date and format as YYYY-MM-DD
                dt = datetime.fromisoformat(posted_at.replace('Z', '+00:00'))
                metadata['published_date'] = dt.strftime('%Y-%m-%d')
            except:
                metadata['published_date'] = posted_at
        
        # Extract username
        author = linkedin_data.get('author', {})
        metadata['username'] = author.get('authorName', author.get('firstName', '') + ' ' + author.get('lastName', '')).strip()
        
        # Extract media URLs (coverPages)
        document = linkedin_data.get('document', {})
        cover_pages = document.get('coverPages', [])
        metadata['media_urls'] = cover_pages if cover_pages else []
        
    except Exception as e:
        print(f"Warning: Error extracting LinkedIn metadata: {e}")
    
    return metadata

def download_linkedin_media(media_urls: list, output_dir: str = 'my_downloads') -> list:
    """Download LinkedIn media files."""
    downloaded_files = []
    
    if not media_urls:
        return downloaded_files
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    for i, url in enumerate(media_urls):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Determine file extension from URL or content type
            if '.jpg' in url.lower() or 'image/jpeg' in response.headers.get('content-type', ''):
                ext = '.jpg'
            elif '.png' in url.lower() or 'image/png' in response.headers.get('content-type', ''):
                ext = '.png'
            else:
                ext = '.jpg'  # Default to jpg
            
            filename = f"linkedin_media_{i+1}{ext}"
            filepath = Path(output_dir) / filename
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            downloaded_files.append(str(filepath))
            print(f"Downloaded: {filename}")
            
        except Exception as e:
            print(f"Warning: Could not download media {i+1}: {e}")
    
    return downloaded_files

def search_linkedin_with_apify(search_url: str, search_limit: int = 1, api_token: str = None):
    """
    Search LinkedIn using Apify's LinkedIn Post Scraper actor.

    Parameters:
        search_url (str): The LinkedIn post URL
        search_limit (int): Number of results to fetch (default: 1)
        api_token (str): Your Apify API token (optional, will use env var if not provided)

    Returns:
        dict: Unified LinkedIn result with metadata and downloaded files
    """
    if api_token is None:
        api_token = os.getenv("APIFY_API_TOKEN")
        if not api_token:
            raise ValueError("Apify API token not provided and APIFY_API_TOKEN environment variable not set")

    url = f"https://api.apify.com/v2/acts/supreme_coder~linkedin-post/run-sync-get-dataset-items?token={api_token}"

    payload = {
        "deepScrape": False,
        "limitPerSource": search_limit,
        "rawData": False,
        "urls": [search_url],
        "proxyConfiguration": {
            "useApifyProxy": True,
            "apifyProxyGroups": ["AUTO"]
        }
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code not in [200, 201]:
            return {
                'success': False,
                'error': f'LinkedIn API request failed: {response.status_code}, {response.text}',
                'files': [],
                'metadata': {}
            }

        data = response.json()
        
        if not data or len(data) == 0:
            return {
                'success': False,
                'error': 'No LinkedIn data found',
                'files': [],
                'metadata': {}
            }
        
        # Extract unified metadata
        unified_metadata = extract_unified_linkedin_metadata(data[0])
        
        # Download media files
        downloaded_files = download_linkedin_media(unified_metadata.get('media_urls', []))
        
        # Save metadata to JSON file
        if downloaded_files or unified_metadata.get('caption'):
            metadata_file = f"my_downloads/linkedin_post_metadata.json"
            Path("my_downloads").mkdir(parents=True, exist_ok=True)
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(unified_metadata, f, indent=2, ensure_ascii=False)
        
        return {
            'success': True,
            'files': downloaded_files,
            'method': 'linkedin_scraper',
            'metadata': unified_metadata,
            'caption': unified_metadata.get('caption', '')
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'LinkedIn scraping failed: {str(e)}',
            'files': [],
            'metadata': {}
        }

if __name__ == "__main__":
    search_url = "https://www.linkedin.com/posts/danish-shabbir-dev_nodejs-essential-tips-tricks-for-developers-ugcPost-7376053361298685952-tgwV?utm_source=share&utm_medium=member_desktop&rcm=ACoAAERqEDoBK89IKDslvi1-3g2Jty-9jRd4NtM"
    search_limit = 1
    api_token = os.getenv("APIFY_API_TOKEN")
    data = search_linkedin_with_apify(search_url, search_limit, api_token)
    
    print(data)


