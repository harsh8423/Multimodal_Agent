#!/usr/bin/env python3
"""
Functional programming approach to download videos and images from YouTube and Instagram using yt-dlp and instaloader.
Extended to capture post captions, descriptions, and body text.
Requirements: 
- pip install yt-dlp
- pip install instaloader (for Instagram images)
- pip install requests
"""

import os
import sys
from functools import wraps, partial
from typing import Optional, Dict, Any, Callable, List, Tuple
import subprocess
import json
from pathlib import Path
import re
import requests
from urllib.parse import urlparse
from linkedinscrape import search_linkedin_with_apify


# Pure functions for configuration
def get_default_config() -> Dict[str, Any]:
    """Returns default configuration for yt-dlp."""
    return {
        'format': 'best[ext=mp4]/best',
        'outtmpl': 'my_downloads/%(title)s_%(id)s.%(ext)s',
        'quiet': False,
        'no_warnings': False,
        'extract_flat': False,
        'ignoreerrors': False,
        'retries': 3,
        'fragment_retries': 3,
        'file_access_retries': 3,
        'no_check_certificate': True,
        'verbose': False,
        'writeinfojson': False,  # Disabled - we'll create our own unified JSON
        'writedescription': False  # Disabled - we'll extract description into unified JSON
    }


def detect_content_type(url: str) -> str:
    """Detect the type of content from URL."""
    url_lower = url.lower()
    if 'youtube.com/shorts' in url_lower or 'youtube.com/short' in url_lower:
        return 'youtube_shorts'
    elif 'youtube.com' in url_lower or 'youtu.be' in url_lower:
        return 'youtube'
    elif 'instagram.com/p/' in url_lower:
        return 'instagram_post'
    elif 'instagram.com/reel/' in url_lower:
        return 'instagram_reel'
    elif 'instagram.com/stories/' in url_lower:
        return 'instagram_story'
    elif 'instagram.com' in url_lower:
        return 'instagram'
    elif 'linkedin.com/posts/' in url_lower:
        return 'linkedin_post'
    elif 'linkedin.com/feed/update/' in url_lower:
        return 'linkedin_feed'
    elif 'linkedin.com/pulse/' in url_lower:
        return 'linkedin_article'
    elif 'linkedin.com' in url_lower:
        return 'linkedin'
    else:
        return 'unknown'


def get_platform_config(url: str) -> Dict[str, Any]:
    """Returns platform-specific configuration based on URL and content type."""
    content_type = detect_content_type(url)
    
    configs = {
        'youtube': {
            'format': 'best[ext=mp4]/best',
            'outtmpl': 'my_downloads/%(title)s_%(id)s.%(ext)s',
            'writeinfojson': False,
            'writedescription': False
        },
        'youtube_shorts': {
            'format': 'best[ext=mp4]/best',
            'outtmpl': 'my_downloads/%(title)s_%(id)s.%(ext)s',
            'writeinfojson': False,
            'writedescription': False
        },
        'instagram_reel': {
            'format': 'best',
            'outtmpl': 'my_downloads/%(title)s_%(id)s.%(ext)s',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            'writeinfojson': False,
            'writedescription': False
        },
        'instagram_post': {
            'outtmpl': 'my_downloads/%(title)s_%(id)s.%(ext)s',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            'writeinfojson': False,
            'writedescription': False
        },
        'instagram_story': {
            'format': 'best',
            'outtmpl': 'my_downloads/%(title)s_%(id)s.%(ext)s',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            'writeinfojson': False,
            'writedescription': False
        },
        'instagram': {
            'format': 'best',
            'outtmpl': 'my_downloads/%(title)s_%(id)s.%(ext)s',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            'writeinfojson': False,
            'writedescription': False
        }
    }
    
    return configs.get(content_type, {})


def extract_instagram_shortcode(url: str) -> Optional[str]:
    """Extract Instagram post shortcode from URL."""
    patterns = [
        r'instagram\.com/p/([A-Za-z0-9_-]+)',
        r'instagram\.com/reel/([A-Za-z0-9_-]+)',
        r'instagram\.com/tv/([A-Za-z0-9_-]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def clean_instagram_url(url: str) -> str:
    """Clean Instagram URL by removing tracking parameters."""
    # Remove query parameters
    clean_url = url.split('?')[0]
    
    # Ensure URL ends with trailing slash for Instagram
    if 'instagram.com' in clean_url and not clean_url.endswith('/'):
        clean_url += '/'
    
    return clean_url


def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """Pure function to merge multiple configuration dictionaries."""
    result = {}
    for config in configs:
        result.update(config)
    return result


def extract_unified_metadata(data: Dict[str, Any], content_type: str) -> Dict[str, Any]:
    """Extract unified metadata fields for all content types."""
    # Initialize with default values
    metadata = {
        'caption': '',
        'likes': 0,
        'comments': 0,
        'published_date': '',
        'username': ''
    }
    
    try:
        # Extract caption/description
        metadata['caption'] = data.get('description', data.get('caption', ''))
        
        # Extract likes count
        metadata['likes'] = data.get('like_count', data.get('likes', 0))
        
        # Extract comment count
        metadata['comments'] = data.get('comment_count', data.get('comments', 0))
        
        # Extract published date
        upload_date = data.get('upload_date', data.get('date', ''))
        if upload_date:
            # Convert YYYYMMDD format to readable date
            if len(upload_date) == 8 and upload_date.isdigit():
                year = upload_date[:4]
                month = upload_date[4:6]
                day = upload_date[6:8]
                metadata['published_date'] = f"{year}-{month}-{day}"
            else:
                metadata['published_date'] = str(upload_date)
        
        # Extract username/channel name
        metadata['username'] = data.get('uploader', data.get('owner_username', data.get('channel', '')))
        
        # Add content type for reference
        metadata['content_type'] = content_type
        
    except Exception as e:
        print(f"Warning: Error extracting metadata: {e}")
    
    return metadata


def extract_metadata_from_json(json_file_path: str) -> Dict[str, Any]:
    """Extract metadata from yt-dlp JSON info file."""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {
                'title': data.get('title', ''),
                'description': data.get('description', ''),
                'uploader': data.get('uploader', ''),
                'upload_date': data.get('upload_date', ''),
                'view_count': data.get('view_count', 0),
                'like_count': data.get('like_count', 0),
                'comment_count': data.get('comment_count', 0),
                'duration': data.get('duration', 0),
                'hashtags': data.get('hashtags', []),
                'thumbnail': data.get('thumbnail', '')
            }
    except Exception as e:
        return {'error': f'Failed to read metadata: {str(e)}'}


def read_description_file(desc_file_path: str) -> Optional[str]:
    """Read description from .description file."""
    try:
        with open(desc_file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception:
        return None


# Higher-order functions and decorators
def with_error_handling(func: Callable) -> Callable:
    """Decorator to add error handling to functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except subprocess.CalledProcessError as e:
            error_output = e.stderr if e.stderr else str(e)
            return {'success': False, 'error': f'Download failed: {error_output}', 'details': e.stdout}
        except FileNotFoundError as e:
            return {'success': False, 'error': f'Required tool not found: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}
    return wrapper


def with_logging(func: Callable) -> Callable:
    """Decorator to add logging to functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        url = args[0] if args else kwargs.get('url', 'Unknown')
        content_type = detect_content_type(url)
        print(f"Starting download: {url}")
        print(f"Content type detected: {content_type}")
        result = func(*args, **kwargs)
        if result.get('success'):
            print(f"Download completed successfully!")
            if 'files' in result:
                print(f"Downloaded {len(result['files'])} file(s)")
            if 'metadata' in result:
                print(f"Metadata extracted successfully")
        else:
            print(f"Download failed: {result.get('error')}")
        return result
    return wrapper


# Composition functions
def compose(*functions):
    """Compose multiple functions into a single function."""
    def inner(arg):
        result = arg
        for func in reversed(functions):
            result = func(result)
        return result
    return inner


def validate_url(url: str) -> Optional[str]:
    """Validate and clean the URL."""
    if not url:
        raise ValueError("URL cannot be empty")
    
    url = url.strip()
    
    # Clean Instagram URLs
    if 'instagram.com' in url.lower():
        url = clean_instagram_url(url)
    
    if not any(domain in url.lower() for domain in ['youtube.com', 'youtu.be', 'instagram.com']):
        raise ValueError("URL must be from YouTube or Instagram")
    
    return url


def create_output_dir(config: Dict[str, Any]) -> Dict[str, Any]:
    """Create output directory based on config."""
    outtmpl = config.get('outtmpl', '')
    if '/' in outtmpl:
        dir_path = Path(outtmpl).parent
        dir_path.mkdir(parents=True, exist_ok=True)
    return config


# Instagram-specific download using instaloader
def download_instagram_with_instaloader(url: str, output_dir: str = 'my_downloads') -> Dict[str, Any]:
    """
    Download Instagram content using instaloader as a fallback.
    This handles images and carousels better than yt-dlp.
    Now also extracts captions and metadata.
    """
    try:
        import instaloader
        
        # Create instaloader instance with metadata enabled
        L = instaloader.Instaloader(
            dirname_pattern=output_dir,
            filename_pattern='{shortcode}_{mediaid}',
            download_video_thumbnails=False,
            post_metadata_txt_pattern='{caption}',  # Save caption
            save_metadata=True,  # Save metadata JSON
            compress_json=False
        )
        
        # Extract shortcode from URL
        shortcode = extract_instagram_shortcode(url)
        if not shortcode:
            return {'success': False, 'error': 'Could not extract Instagram post ID'}
        
        # Download the post
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        
        # Extract raw metadata before downloading
        raw_metadata = {
            'caption': post.caption if hasattr(post, 'caption') else '',
            'likes': post.likes if hasattr(post, 'likes') else 0,
            'comments': post.comments if hasattr(post, 'comments') else 0,
            'date': post.date.isoformat() if hasattr(post, 'date') else '',
            'owner_username': post.owner_username if hasattr(post, 'owner_username') else '',
            'is_video': post.is_video if hasattr(post, 'is_video') else False,
            'video_view_count': post.video_view_count if hasattr(post, 'video_view_count') and post.is_video else None
        }
        
        # Extract unified metadata
        unified_metadata = extract_unified_metadata(raw_metadata, 'instagram_post')
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Save simplified metadata to JSON file
        metadata_file = Path(output_dir) / f'{shortcode}_metadata.json'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(unified_metadata, f, indent=2, ensure_ascii=False)
        
        files = []
        # Download post
        L.download_post(post, target=output_dir)
        
        # Find downloaded files
        for file in Path(output_dir).glob(f'{shortcode}*'):
            files.append(str(file))
        
        return {
            'success': True,
            'files': files,
            'method': 'instaloader',
            'metadata': unified_metadata,
            'caption': unified_metadata['caption']
        }
        
    except ImportError:
        return {
            'success': False,
            'error': 'instaloader not installed. Install with: pip install instaloader'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Instaloader failed: {str(e)}'
        }


# Main download functions
def build_yt_dlp_command(url: str, config: Dict[str, Any]) -> List[str]:
    """Build yt-dlp command from URL and configuration."""
    cmd = ['yt-dlp']
    
    # Add format option
    if 'format' in config:
        cmd.extend(['-f', config['format']])
    
    # Add output template
    if 'outtmpl' in config:
        cmd.extend(['-o', config['outtmpl']])
    
    # Add metadata extraction
    if config.get('writeinfojson'):
        cmd.append('--write-info-json')
    
    if config.get('writedescription'):
        cmd.append('--write-description')
    
    # Add retries
    if 'retries' in config:
        cmd.extend(['--retries', str(config['retries'])])
    
    # Add fragment retries
    if 'fragment_retries' in config:
        cmd.extend(['--fragment-retries', str(config['fragment_retries'])])
    
    # Add quiet mode
    if config.get('quiet'):
        cmd.append('-q')
    
    # Add verbose mode for debugging
    if config.get('verbose'):
        cmd.append('-v')
    
    # Handle no certificate check
    if config.get('no_check_certificate'):
        cmd.append('--no-check-certificate')
    
    # Instagram specific headers
    if 'instagram.com' in url.lower():
        cmd.extend([
            '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            '--add-header', 'Accept-Language:en-US,en;q=0.9'
        ])
    
    # Add the URL
    cmd.append(url)
    
    return cmd


def try_yt_dlp_download(url: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Try to download using yt-dlp with metadata extraction."""
    # First, get metadata using --dump-json
    metadata_command = ['yt-dlp', '--dump-json', url]
    try:
        metadata_result = subprocess.run(metadata_command, capture_output=True, text=True, check=True)
        raw_metadata = json.loads(metadata_result.stdout)
    except Exception as e:
        print(f"Warning: Could not extract metadata: {e}")
        raw_metadata = {}
    
    # Now download the actual file
    command = build_yt_dlp_command(url, config)
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        
        # Extract file info from output
        files = extract_output_filenames(result.stdout, result.stderr, config)
        
        # Extract unified metadata
        content_type = detect_content_type(url)
        unified_metadata = extract_unified_metadata(raw_metadata, content_type)
        
        # Save simplified metadata to JSON file
        if files:
            # Find the base filename (without extension)
            base_file = None
            for file in files:
                if not file.endswith('.info.json') and not file.endswith('.description'):
                    base_file = Path(file).stem
                    break
            
            if base_file:
                metadata_file = f"my_downloads/{base_file}_metadata.json"
                Path("my_downloads").mkdir(parents=True, exist_ok=True)
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(unified_metadata, f, indent=2, ensure_ascii=False)
        
        return {
            'success': True,
            'files': files if files else ['Download completed'],
            'method': 'yt-dlp',
            'output': result.stdout,
            'metadata': unified_metadata,
            'caption': unified_metadata.get('caption', '')
        }
    except subprocess.CalledProcessError as e:
        # Check if it's an image post error
        if 'There is no video in this post' in (e.stderr or '') or 'There is no video in this post' in (e.stdout or ''):
            return {
                'success': False,
                'error': 'Image post detected',
                'is_image': True
            }
        raise e


@with_error_handling
@with_logging
def download_video(url: str, custom_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Main function to download video/image from URL using functional composition.
    Now includes caption/description extraction.
    
    Args:
        url: The URL of the video/image to download
        custom_config: Optional custom configuration to override defaults
    
    Returns:
        Dictionary with success status, file info, metadata, and caption/description
    """
    # Validate URL
    clean_url = validate_url(url)

    content_type = detect_content_type(clean_url)
    if content_type in ['linkedin_post', 'linkedin_feed', 'linkedin_article', 'linkedin']:
        result = search_linkedin_with_apify(clean_url, 1)
        result.update({
            'url': clean_url,
            'config': {'outtmpl': 'my_downloads/linkedin_%(title)s_%(id)s.%(ext)s'}
        })
        return result
    
    # Compose configuration
    config_pipeline = compose(
        create_output_dir,
        partial(merge_configs, custom_config or {}),
        partial(merge_configs, get_platform_config(clean_url)),
    )
    
    final_config = config_pipeline(get_default_config())
    
    # For Instagram posts, try yt-dlp first, then fall back to instaloader
    if 'instagram.com/p/' in clean_url.lower():

        # Extract output directory from config
        output_dir = str(Path(final_config.get('outtmpl', 'Instagram/Posts')).parent)
        result = download_instagram_with_instaloader(clean_url, output_dir)
        
        # If it's an image post, try instaloader
        if not result.get('success'):
            print("Detected image post, trying alternative method...")
            
            result = try_yt_dlp_download(clean_url, final_config)
            
            
            if result.get('success'):
                result.update({
                    'url': clean_url,
                    'config': final_config
                })
                return result
            else:
                # If instaloader also fails, try gallery-dl as last resort
                print("Trying gallery-dl as final fallback...")
                result = download_with_gallery_dl(clean_url, output_dir)
                if result.get('success'):
                    result.update({
                        'url': clean_url,
                        'config': final_config
                    })
                    return result
        
        if result.get('success'):
            result.update({
                'url': clean_url,
                'config': final_config
            })
        return result
    else:
        # For non-Instagram posts, use yt-dlp
        result = try_yt_dlp_download(clean_url, final_config)
        result.update({
            'url': clean_url,
            'config': final_config
        })
        return result


def download_with_gallery_dl(url: str, output_dir: str = 'my_downloads') -> Dict[str, Any]:
    """
    Download using gallery-dl as a last resort.
    Now includes metadata extraction via --write-metadata option.
    Requires: pip install gallery-dl
    """
    try:
        import subprocess
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        cmd = [
            'gallery-dl',
            '--dest', output_dir,
            '--filename', '{shortcode}_{num}.{extension}',
            '--write-metadata',  # Added to save metadata
            '--postprocessors', '[{"name": "metadata", "event": "post", "filename": "{shortcode}_metadata.json"}]',
            url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Find downloaded files
        files = []
        metadata = {}
        caption = None
        shortcode = extract_instagram_shortcode(url)
        if shortcode:
            for file in Path(output_dir).glob(f'*{shortcode}*'):
                files.append(str(file))
                # Check for metadata file
                if file.suffix == '.json':
                    try:
                        with open(file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            caption = data.get('description', data.get('caption', ''))
                            metadata = data
                    except Exception:
                        pass
        
        return {
            'success': True if files else False,
            'files': files,
            'method': 'gallery-dl',
            'metadata': metadata if metadata else None,
            'caption': caption
        }
        
    except FileNotFoundError:
        return {
            'success': False,
            'error': 'gallery-dl not installed. Install with: pip install gallery-dl'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'gallery-dl failed: {str(e)}'
        }


def extract_output_filenames(stdout: str, stderr: str, config: Dict[str, Any]) -> List[str]:
    """Extract the output filenames from yt-dlp output."""
    files = []
    
    # Look for files in my_downloads directory
    downloads_dir = Path('my_downloads')
    if downloads_dir.exists():
        # Look for common video/image file extensions
        extensions = ['.mp4', '.webm', '.mkv', '.avi', '.mov', '.jpg', '.jpeg', '.png', '.webp']
        for ext in extensions:
            for file_path in downloads_dir.glob(f'*{ext}'):
                files.append(str(file_path))
    
    # If no files found in my_downloads, try to parse output text as fallback
    if not files:
        output = stdout + '\n' + stderr
        patterns = [
            r'\[download\] Destination: (.+)',
            r'\[download\] (.+) has already been downloaded',
            r'Merging formats into "(.+)"',
            r'\[ExtractAudio\] Destination: (.+)',
            r'\[ffmpeg\] Merging formats into "(.+)"'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, output)
            files.extend(matches)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_files = []
    for file in files:
        if file not in seen:
            seen.add(file)
            unique_files.append(file)
    
    return unique_files if unique_files else []


# Curry functions for partial application
def create_downloader(default_config: Dict[str, Any]) -> Callable:
    """
    Create a customized downloader with default configuration.
    This demonstrates currying and partial application.
    """
    return partial(download_video, custom_config=default_config)


# Specialized downloaders
def create_instagram_downloader() -> Callable:
    """Create a specialized Instagram downloader with metadata."""
    instagram_config = {
        'outtmpl': 'Instagram/%(uploader)s/%(title)s_%(id)s.%(ext)s',
        'no_check_certificate': True,
        'writeinfojson': True,
        'writedescription': True
    }
    return create_downloader(instagram_config)


def create_audio_downloader() -> Callable:
    """Create a specialized audio downloader."""
    audio_config = {
        'format': 'bestaudio[ext=m4a]/bestaudio',
        'outtmpl': 'Audio/%(title)s.%(ext)s',
        'writeinfojson': True,
        'writedescription': True
    }
    return create_downloader(audio_config)


# Batch processing using map
def download_multiple(urls: list, custom_config: Optional[Dict[str, Any]] = None) -> list:
    """
    Download multiple videos using functional map.
    
    Args:
        urls: List of URLs to download
        custom_config: Optional custom configuration
    
    Returns:
        List of results for each download
    """
    downloader = partial(download_video, custom_config=custom_config)
    return list(map(downloader, urls))


# Filter functions
def filter_successful(results: list) -> list:
    """Filter only successful downloads from results."""
    return list(filter(lambda r: r.get('success'), results))


def filter_failed(results: list) -> list:
    """Filter only failed downloads from results."""
    return list(filter(lambda r: not r.get('success'), results))


def filter_with_captions(results: list) -> list:
    """Filter downloads that have captions/descriptions."""
    return list(filter(lambda r: r.get('caption') is not None, results))


# Utility function to extract all captions from results
def extract_all_captions(results: list) -> Dict[str, str]:
    """Extract all captions/descriptions from download results."""
    captions = {}
    for result in results:
        if result.get('success') and result.get('caption'):
            url = result.get('url', 'unknown')
            captions[url] = result.get('caption')
    return captions


# Example usage and testing
def main():
    """Example usage of the download functions with caption extraction."""
    
    print("Social Media Downloader with Caption Extraction")
    print("=" * 50)
    
    # Test URLs
    test_urls = {
        "YouTube Video": "https://youtu.be/oIWzOJOr9tY?si=FiuOuBrSuqAIf3pr",
        "YouTube Shorts": "https://youtube.com/shorts/L8jg1jKFIcU?si=eU__lgjjDJ8KYU-_",
        "Instagram Reel": "https://www.instagram.com/reel/DOU-ZHoke64/?utm_source=ig_web_copy_link",
        "Instagram Post": "https://www.instagram.com/p/DO-YTeLEpVG/?utm_source=ig_web_copy_link&igsh=MzRlODBiNWFlZA==",
        "LinkedIn Post": "https://www.linkedin.com/posts/danish-shabbir-dev_nodejs-essential-tips-tricks-for-developers-ugcPost-7376053361298685952-tgwV?utm_source=share&utm_medium=member_desktop&rcm=ACoAAERqEDoBK89IKDslvi1-3g2Jty-9jRd4NtM",
    }

    # Download a single video with metadata
    # Pick the first URL from the test_urls dictionary
    # first_url = list(test_urls.values())[0]
    # result = download_video(first_url)
    
    results = download_multiple(list(test_urls.values()))
    
    print("\nDownload Results:")
    print("=" * 50)
    
    for i, result in enumerate(results, 1):
        print(f"\nResult {i}:")
        print(f"Success: {result.get('success')}")
        if result.get('success'):
            print(f"Files: {result.get('files')}")
            if result.get('metadata'):
                metadata = result.get('metadata')
                print(f"Caption: {metadata.get('caption', '')[:100]}...")
                print(f"Username: {metadata.get('username', '')}")
                print(f"Likes: {metadata.get('likes', 0)}")
                print(f"Comments: {metadata.get('comments', 0)}")
                print(f"Published Date: {metadata.get('published_date', '')}")
                print(f"Content Type: {metadata.get('content_type', '')}")
        else:
            print(f"Error: {result.get('error')}")
    
    # # Download multiple videos
    # 
    # # Extract all captions
    # all_captions = extract_all_captions(results)
    # print("\nExtracted Captions:")
    # for url, caption in all_captions.items():
    #     print(f"{url}: {caption[:100]}...")
    
    # print("\n" + "=" * 50)
    # print("New Features Added:")
    # print("1. Automatic caption/description extraction")
    # print("2. Metadata saved as JSON files")
    # print("3. Captions saved as separate text files")
    # print("4. Enhanced result dictionary with 'caption' and 'metadata' fields")
    
    # print("\nAvailable download methods:")
    # print("1. yt-dlp (primary method for videos) - with --write-info-json and --write-description")
    # print("2. instaloader (fallback for Instagram) - with caption and metadata extraction")
    # print("3. gallery-dl (final fallback) - with --write-metadata option")
    
    # print("\nTo download with captions, use:")
    # print("  result = download_video('URL')")
    # print("  caption = result.get('caption')")
    # print("  metadata = result.get('metadata')")
    
    # print("\nFor batch downloads with caption extraction:")
    # print("  results = download_multiple(['URL1', 'URL2', 'URL3'])")
    # print("  captions = extract_all_captions(results)")
    
    # print("\nFilter downloads with captions:")
    # print("  with_captions = filter_with_captions(results)")


if __name__ == "__main__":
    main()