"""
KIE Image Generation Tool
Functional programming implementation for generating images using KIE API
"""

import requests
import json
import os
import time
import tempfile
from typing import Dict, List, Optional, Tuple, Any
from functools import partial
from dotenv import load_dotenv
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))
from upload_cloudinary import upload_to_cloudinary

load_dotenv()

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
    model: str = "google/nano-banana",
    output_format: str = "png",
    image_size: str = "auto",
    callback_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build the payload for KIE image generation request.
    
    Args:
        prompt: Text prompt for image generation
        model: Model to use for generation
        output_format: Output image format
        image_size: Optional aspect ratio for output image (default: "auto")
        callback_url: Optional callback URL for async processing
        
    Returns:
        Dictionary containing the request payload
    """
    input_data = {
        "prompt": prompt,
        "output_format": output_format
    }
    
    # Only include image_size if specified (not "auto")
    if image_size and image_size != "auto":
        input_data["image_size"] = image_size
    
    payload = {
        "model": model,
        "input": input_data
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


def validate_inputs(prompt: str) -> Tuple[bool, Optional[str]]:
    """
    Validate input parameters for image generation.
    
    Args:
        prompt: Text prompt
        
    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    if not prompt or not prompt.strip():
        return False, "Prompt cannot be empty"
    
    return True, None


def generate_kie_image(
    prompt: str,
    api_key: Optional[str] = None,
    model: str = "google/nano-banana",
    output_format: str = "png",
    image_size: str = "auto",
    callback_url: Optional[str] = None,
    max_wait_time: int = 300,
    poll_interval: int = 10,
    cloudinary_options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate image using KIE API, poll for completion, download, and upload to Cloudinary.
    
    Args:
        prompt: Text prompt for image generation
        api_key: KIE API key (if not provided, will use environment variable)
        model: Model to use for generation
        output_format: Output image format
        image_size: Optional aspect ratio for output image (default: "auto")
        callback_url: Optional callback URL for async processing
        max_wait_time: Maximum time to wait for task completion
        poll_interval: Interval between status polls
        cloudinary_options: Options for Cloudinary upload
        
    Returns:
        Dictionary containing status, url, and msg
    """
    # Get API key from environment if not provided
    if not api_key:
        api_key = os.environ.get("KIE_API_KEY")
        if not api_key:
            return {
                "status": "failed",
                "url": None,
                "msg": "KIE_API_KEY not found in environment variables"
            }
    
    # Validate inputs
    is_valid, error_msg = validate_inputs(prompt)
    if not is_valid:
        return {
            "status": "failed",
            "url": None,
            "msg": error_msg
        }
    
    try:
        # Step 1: Generate the image task
        headers = create_kie_client(api_key)
        payload = build_image_payload(
            prompt=prompt,
            model=model,
            output_format=output_format,
            image_size=image_size,
            callback_url=callback_url
        )
        
        # Make request
        success, response_data = make_kie_request(headers, payload)
        
        if not success:
            return {
                "status": "failed",
                "url": None,
                "msg": response_data.get("error", "Unknown error occurred")
            }
        
        # Try different possible field names for task ID, including nested structures
        task_id = (response_data.get("task_id") or 
                  response_data.get("taskId") or 
                  response_data.get("id") or 
                  response_data.get("job_id") or
                  response_data.get("jobId") or
                  response_data.get("data", {}).get("taskId") or
                  response_data.get("data", {}).get("task_id") or
                  response_data.get("data", {}).get("id") or
                  response_data.get("data", {}).get("recordId"))
        
        print(f"KIE API Response: {response_data}")
        print(f"Extracted Task ID: {task_id}")
        
        if not task_id:
            return {
                "status": "failed",
                "url": None,
                "msg": "No task ID returned from generation request"
            }
        
        # Step 2: Poll for task completion
        print(f"Polling task {task_id} for completion...")
        polling_result = poll_kie_task_status(
            task_id=task_id,
            api_key=api_key,
            max_wait_time=max_wait_time,
            poll_interval=poll_interval
        )
        
        if not polling_result.get("success"):
            return {
                "status": "failed",
                "url": None,
                "msg": polling_result.get("error", "Task polling failed")
            }
        
        image_url = polling_result.get("image_url")
        if not image_url:
            return {
                "status": "failed",
                "url": None,
                "msg": "No image URL returned from completed task"
            }
        
        # Step 3: Download the image
        print(f"Downloading image from: {image_url}")
        download_success, download_result = download_image_from_url(image_url)
        
        if not download_success:
            return {
                "status": "failed",
                "url": None,
                "msg": f"Failed to download image: {download_result}"
            }
        
        temp_file_path = download_result
        
        try:
            # Step 4: Upload to Cloudinary
            print(f"Uploading image to Cloudinary...")
            cloudinary_result = upload_to_cloudinary(
                temp_file_path,
                cloudinary_options or {}
            )
            
            # Step 5: Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            
            return {
                "status": "success",
                "url": cloudinary_result.get("secure_url"),
                "msg": None,
                "task_id": task_id,
                "original_image_url": image_url,
                "model": model,
                "output_format": output_format,
                "image_size": image_size
            }
            
        except Exception as e:
            # Clean up temporary file on error
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            
            return {
                "status": "failed",
                "url": None,
                "msg": f"Failed to upload to Cloudinary: {str(e)}"
            }
    
    except Exception as e:
        return {
            "status": "failed",
            "url": None,
            "msg": str(e)
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

    
    try:
        url = "https://api.kie.ai/api/v1/jobs/recordInfo"
        params = {"taskId": task_id}
        headers = {"Authorization": f"Bearer {api_key}"}

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        # Handle nested response structure
        if result.get("code") == 200 and result.get("data"):
            data = result.get("data", {})
            
            # Extract result URL from resultJson if available
            result_url = None
            if data.get("resultJson"):
                try:
                    import json
                    result_json = json.loads(data.get("resultJson"))
                    if result_json.get("resultUrls") and len(result_json["resultUrls"]) > 0:
                        result_url = result_json["resultUrls"][0]
                except:
                    pass
            
            return {
                "success": True,
                "data": data,
                "status": data.get("state", "unknown"),  # Use 'state' field instead of 'status'
                "output_url": data.get("outputUrl") or data.get("output_url") or result_url,
                "result_url": result_url or data.get("resultUrl") or data.get("result_url")
            }
        else:
            return {
                "success": False,
                "error": result.get("msg", "Unknown error"),
                "data": result
            }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e)
        }


def poll_kie_task_status(task_id: str, api_key: Optional[str] = None, max_wait_time: int = 300, poll_interval: int = 10) -> Dict[str, Any]:
    """
    Poll KIE task status until completion or failure.
    
    Args:
        task_id: Task ID to poll
        api_key: KIE API key
        max_wait_time: Maximum time to wait in seconds (default 5 minutes)
        poll_interval: Interval between polls in seconds (default 10 seconds)
        
    Returns:
        Dictionary containing final task status and result
    """
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        status_result = query_kie_task_status(task_id, api_key)
        
        if not status_result.get("success"):
            return status_result
        
        # Check if task is completed
        task_status = status_result.get("status", "").lower()
        
        if task_status == "success":
            return {
                "success": True,
                "status": "completed",
                "data": status_result.get("data"),
                "image_url": status_result.get("output_url") or status_result.get("result_url")
            }
        elif task_status in ["failed", "error", "fail"]:
            return {
                "success": False,
                "status": "failed",
                "error": status_result.get("error", "Task failed"),
                "data": status_result.get("data")
            }
        elif task_status in ["waiting", "pending", "processing", "running", "submitted"]:
            print(f"Task {task_id} is {task_status}, waiting {poll_interval} seconds...")
            time.sleep(poll_interval)
        else:
            # Unknown status, continue polling
            print(f"Unknown task status: {task_status}, continuing to poll...")
            time.sleep(poll_interval)
    
    return {
        "success": False,
        "status": "timeout",
        "error": f"Task did not complete within {max_wait_time} seconds",
        "task_id": task_id
    }


def download_image_from_url(image_url: str, temp_dir: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Download image from URL to temporary file.
    
    Args:
        image_url: URL of the image to download
        temp_dir: Temporary directory path (optional)
        
    Returns:
        Tuple of (success: bool, file_path: Optional[str])
    """
    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        # Create temporary file
        if temp_dir:
            os.makedirs(temp_dir, exist_ok=True)
            temp_file = tempfile.NamedTemporaryFile(delete=False, dir=temp_dir, suffix='.png')
        else:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        
        temp_file.write(response.content)
        temp_file.close()
        
        return True, temp_file.name
        
    except Exception as e:
        return False, str(e)




# Example usage and testing functions
# Wrapper function for tool_router compatibility
def kie_image_generation(prompt: str, reference_image_url: Optional[str] = None,
                        image_size: str = "auto", api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Wrapper function for KIE image generation that matches the expected tool interface.
    
    Args:
        prompt: Text prompt for image generation
        reference_image_url: Optional reference image URL (not used with nano-banana model)
        model: Model to use for generation
        image_size: Optional image size ratio (default: "auto")
        style_preferences: Style preferences
        api_key: KIE API key
        
    Returns:
        Dictionary with generation result
    """
    # Enhance prompt with style preferences if provided
    enhanced_prompt = prompt
    
    enhanced_prompt += ", high quality, professional photography, detailed, sharp focus, beautiful lighting, aesthetic composition"
    
    # Call the main generation function
    return generate_kie_image(
        prompt=enhanced_prompt,
        model="google/nano-banana",
        output_format="png",
        image_size=image_size,
        api_key=api_key
    )

def test_kie_image_generation():
    """
    Test function for KIE image generation.
    """
    test_prompt = "A simple red apple on a white background"
    
    result = generate_kie_image(test_prompt)
    print("Test result:", result)
    
    if result["status"] == "success":
        print(f"✅ Image generated successfully: {result['url']}")
        print(f"   Task ID: {result['task_id']}")
        print(f"   Model: {result['model']}")
    else:
        print(f"❌ Error: {result['msg']}")
    
    return result


if __name__ == "__main__":
    test_kie_image_generation()