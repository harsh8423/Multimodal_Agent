"""
KIE Image Generation Tool
Functional programming implementation for generating images using KIE API
"""

import requests
import json
import os
from typing import Dict, List, Optional, Tuple, Any
from functools import partial


def create_kie_client(api_key: str) -> Dict[str, str]:
    """
    Create KIE API client configuration.
    
    Args:
        api_key: KIE API key
        
    Returns:
        Dictionary containing headers for API requests
    """
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }


def build_image_payload(
    prompt: str,
    image_urls: List[str],
    model: str = "google/nano-banana-edit",
    output_format: str = "png",
    image_size: str = "1:1",
    callback_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build the payload for KIE image generation request.
    
    Args:
        prompt: Text prompt for image generation
        image_urls: List of input image URLs
        model: Model to use for generation
        output_format: Output image format
        image_size: Aspect ratio for output image
        callback_url: Optional callback URL for async processing
        
    Returns:
        Dictionary containing the request payload
    """
    payload = {
        "model": model,
        "input": {
            "prompt": prompt,
            "image_urls": image_urls,
            "output_format": output_format,
            "image_size": image_size
        }
    }
    
    if callback_url:
        payload["callBackUrl"] = callback_url
        
    return payload


def make_kie_request(headers: Dict[str, str], payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Make HTTP request to KIE API.
    
    Args:
        headers: Request headers
        payload: Request payload
        
    Returns:
        Tuple of (success: bool, response_data: dict)
    """
    url = "https://api.kie.ai/api/v1/jobs/createTask"
    
    try:
        response = requests.post(
            url, 
            headers=headers, 
            data=json.dumps(payload),
            timeout=30
        )
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, {"error": str(e)}


def validate_inputs(prompt: str, image_urls: List[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate input parameters for image generation.
    
    Args:
        prompt: Text prompt
        image_urls: List of image URLs
        
    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    if not prompt or not prompt.strip():
        return False, "Prompt cannot be empty"
    
    if not image_urls or not isinstance(image_urls, list):
        return False, "Image URLs must be a non-empty list"
    
    if not all(isinstance(url, str) and url.strip() for url in image_urls):
        return False, "All image URLs must be non-empty strings"
    
    return True, None


def generate_kie_image(
    prompt: str,
    image_urls: List[str],
    api_key: Optional[str] = None,
    model: str = "google/nano-banana-edit",
    output_format: str = "png",
    image_size: str = "1:1",
    callback_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate image using KIE API with functional programming approach.
    
    Args:
        prompt: Text prompt for image generation
        image_urls: List of input image URLs
        api_key: KIE API key (if not provided, will use environment variable)
        model: Model to use for generation
        output_format: Output image format
        image_size: Aspect ratio for output image
        callback_url: Optional callback URL for async processing
        
    Returns:
        Dictionary containing the result or error information
    """
    # Get API key from environment if not provided
    if not api_key:
        api_key = os.environ.get("KIE_API_KEY")
        if not api_key:
            return {
                "success": False,
                "error": "KIE_API_KEY not found in environment variables"
            }
    
    # Validate inputs
    is_valid, error_msg = validate_inputs(prompt, image_urls)
    if not is_valid:
        return {
            "success": False,
            "error": error_msg
        }
    
    # Create client and build payload
    headers = create_kie_client(api_key)
    payload = build_image_payload(
        prompt=prompt,
        image_urls=image_urls,
        model=model,
        output_format=output_format,
        image_size=image_size,
        callback_url=callback_url
    )
    
    # Make request
    success, response_data = make_kie_request(headers, payload)
    
    if success:
        return {
            "success": True,
            "data": response_data,
            "task_id": response_data.get("task_id"),
            "status": "submitted"
        }
    else:
        return {
            "success": False,
            "error": response_data.get("error", "Unknown error occurred")
        }


def query_kie_task_status(task_id: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Query the status of a KIE image generation task.
    
    Args:
        task_id: Task ID to query
        api_key: KIE API key (if not provided, will use environment variable)
        
    Returns:
        Dictionary containing task status information
    """
    if not api_key:
        api_key = os.environ.get("KIE_API_KEY")
        if not api_key:
            return {
                "success": False,
                "error": "KIE_API_KEY not found in environment variables"
            }
    
    if not task_id:
        return {
            "success": False,
            "error": "Task ID is required"
        }
    
    headers = create_kie_client(api_key)
    url = f"https://api.kie.ai/api/v1/jobs/{task_id}"
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return {
            "success": True,
            "data": response.json()
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e)
        }




# Example usage and testing functions
def test_kie_image_generation():
    """
    Test function for KIE image generation.
    """
    test_prompt = "turn this photo into a character figure. Behind it, place a box with the character's image printed on it, and a computer showing the Blender modeling process on its screen. In front of the box, add a round plastic base with the character figure standing on it. set the scene indoors if possible"
    test_urls = ["https://file.aiquickdraw.com/custom-page/akr/section-images/1756223420389w8xa2jfe.png"]
    
    result = generate_kie_image(test_prompt, test_urls)
    print("Test result:", result)
    return result


if __name__ == "__main__":
    test_kie_image_generation()