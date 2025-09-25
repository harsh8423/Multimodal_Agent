import requests
import os
from pathlib import Path
from urllib.parse import urlparse, unquote
from typing import Optional, Tuple, Callable
import mimetypes
from functools import partial


def extract_filename_from_url(url: str) -> str:
    """Extract filename from URL, handling edge cases."""
    parsed = urlparse(url)
    filename = unquote(os.path.basename(parsed.path))
    
    # If no filename in URL, generate one based on URL hash
    if not filename or '.' not in filename:
        url_hash = str(abs(hash(url)))[:8]
        return f"media_file_{url_hash}"
    
    return filename


def get_file_extension_from_headers(headers: dict) -> str:
    """Extract file extension from Content-Type header."""
    content_type = headers.get('content-type', '').split(';')[0].strip()
    extension = mimetypes.guess_extension(content_type)
    return extension or ''


def create_safe_filename(url: str, headers: dict) -> str:
    """Create a safe filename combining URL and header information."""
    base_filename = extract_filename_from_url(url)
    
    # If filename doesn't have extension, try to get it from headers
    if '.' not in base_filename:
        ext = get_file_extension_from_headers(headers)
        base_filename = f"{base_filename}{ext}"
    
    # Sanitize filename
    safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_"
    safe_filename = ''.join(c if c in safe_chars else '_' for c in base_filename)
    
    return safe_filename or "downloaded_media"


def validate_url(url: str) -> bool:
    """Validate if URL is properly formatted."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def make_request_with_headers(url: str, custom_headers: Optional[dict] = None) -> requests.Response:
    """Make HTTP request with proper headers."""
    default_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    headers = {**default_headers, **(custom_headers or {})}
    
    response = requests.get(url, headers=headers, stream=True, timeout=30)
    response.raise_for_status()
    return response


def write_file_chunks(response: requests.Response, filepath: Path) -> int:
    """Write response content to file in chunks and return bytes written."""
    total_bytes = 0
    
    with open(filepath, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:  # filter out keep-alive chunks
                f.write(chunk)
                total_bytes += len(chunk)
    
    return total_bytes


def download_media_file(
    url: str,
    output_dir: str = "downloads",
    filename: Optional[str] = None,
    custom_headers: Optional[dict] = None,
    overwrite: bool = True
) -> Tuple[bool, str, dict]:
    """
    Download media file from CDN URL using functional programming principles.
    
    Args:
        url: CDN URL of the media file
        output_dir: Directory to save the file (default: "downloads")
        filename: Custom filename (optional, will be extracted from URL if not provided)
        custom_headers: Additional HTTP headers (optional)
        overwrite: Whether to overwrite existing files (default: False)
    
    Returns:
        Tuple of (success: bool, message: str, info: dict)
    """
    
    # Validation pipeline
    if not validate_url(url):
        return False, "Invalid URL format", {}
    
    try:
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Make request and get headers
        response = make_request_with_headers(url, custom_headers)
        
        # Determine filename
        final_filename = filename or create_safe_filename(url, response.headers)
        filepath = output_path / final_filename
        
        # Check if file exists and handle overwrite logic
        if filepath.exists() and not overwrite:
            return False, f"File already exists: {filepath}. Use overwrite=True to replace.", {
                "filepath": str(filepath),
                "file_exists": True
            }
        
        # Download and write file
        bytes_written = write_file_chunks(response, filepath)
        
        # Gather file info
        file_info = {
            "filepath": str(filepath),
            "filename": final_filename,
            "size_bytes": bytes_written,
            "size_mb": round(bytes_written / (1024 * 1024), 2),
            "content_type": response.headers.get('content-type', 'unknown'),
            "url": url
        }
        
        return True, f"Successfully downloaded: {final_filename}", file_info
        
    except requests.exceptions.RequestException as e:
        return False, f"Request failed: {str(e)}", {}
    except OSError as e:
        return False, f"File system error: {str(e)}", {}
    except Exception as e:
        return False, f"Unexpected error: {str(e)}", {}


# Utility functions for specific use cases
def create_downloader_with_config(output_dir: str, headers: dict) -> Callable:
    """Create a configured downloader function using partial application."""
    return partial(download_media_file, output_dir=output_dir, custom_headers=headers)


def batch_download_media(urls: list, **kwargs) -> list:
    """Download multiple media files and return results."""
    download_func = partial(download_media_file, **kwargs)
    return [download_func(url) for url in urls]


# Example usage
if __name__ == "__main__":
    # Single file download
    success, message, info = download_media_file(
        "https://www.youtube.com/watch?v=4HhqSYexIwo",
        output_dir="my_downloads",
        overwrite=True
    )
    
    print(f"Success: {success}")
    print(f"Message: {message}")
    if info:
        print(f"File info: {info}")
    
    # # Batch download example
    # urls = [
    #     "https://example.com/image1.jpg",
    #     "https://example.com/video.mp4",
    #     "https://example.com/audio.mp3"
    # ]
    
    # results = batch_download_media(urls, output_dir="batch_downloads")
    # for i, (success, msg, info) in enumerate(results):
    #     print(f"File {i+1}: {'✓' if success else '✗'} {msg}")
    
    # # Configured downloader example
    # my_downloader = create_downloader_with_config(
    #     output_dir="special_downloads",
    #     headers={"Authorization": "Bearer your-token"}
    # )
    
    # result = my_downloader("https://example.com/protected-media.jpg")
    # print(f"Configured download result: {result}")