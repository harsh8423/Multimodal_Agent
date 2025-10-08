"""
Minimax Audio Clone Tool
Simplified implementation for voice cloning using Minimax API
"""

import requests
import json
import os
import time
import tempfile
from typing import Dict, List, Optional, Tuple, Any
from dotenv import load_dotenv
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))
from upload_cloudinary import upload_to_cloudinary

load_dotenv()


def create_minimax_client(api_key: Optional[str] = None) -> Dict[str, str]:
    """
    Create Minimax API client configuration.
    
    Args:
        api_key: Minimax API key (if not provided, will use environment variable)
        
    Returns:
        Dictionary containing headers for API requests
    """
    if not api_key:
        api_key = os.environ.get("MINIMAX_API_KEY")
        if not api_key:
            raise ValueError("MINIMAX_API_KEY not found in environment variables")
    
    return {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }


def validate_text_input(text: str) -> Tuple[bool, Optional[str]]:
    """
    Validate text input for TTS generation.
    
    Args:
        text: Text to convert to speech
        
    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    if not text or not text.strip():
        return False, "Text cannot be empty"
    
    if len(text) > 10000:  # Reasonable limit for TTS
        return False, "Text is too long (max 10000 characters)"
    
    return True, None


def submit_minimax_task(headers: Dict[str, str], payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Submit TTS task to Minimax API.
    
    Args:
        headers: Request headers
        payload: Request payload
        
    Returns:
        Tuple of (success: bool, response_data: dict)
    """
    url = "https://api.minimax.io/v1/t2a_async_v2"
    
    try:
        print(f"Submitting payload: {json.dumps(payload, indent=2)}")
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(payload),
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        response_data = response.json()
        print(f"Response data: {response_data}")
        
        # Check for API errors
        if response_data.get("base_resp", {}).get("status_code") != 0:
            return False, {
                "error": f"API Error: {response_data.get('base_resp', {}).get('status_msg', 'Unknown error')}",
                "status_code": response_data.get("base_resp", {}).get("status_code"),
                "response": response_data
            }
        
        response.raise_for_status()
        return True, response_data
        
    except requests.exceptions.RequestException as e:
        return False, {"error": str(e)}
    except json.JSONDecodeError as e:
        return False, {"error": f"Invalid JSON response: {str(e)}"}


def generate_minimax_audio(
    text: str,
    api_key: Optional[str] = None,
    voice_id: str = "English_expressive_narrator",
    file_format: str = "mp3",
    pronunciation_mappings: Optional[List[str]] = None,
    sound_effects: Optional[str] = None,
    max_wait_time: int = 300,
    poll_interval: int = 10,
    cloudinary_options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate audio using Minimax API, poll for completion, download, and upload to Cloudinary.
    
    Args:
        text: Text to convert to speech
        api_key: Minimax API key
        voice_id: Voice ID to use
        file_format: Audio format (mp3, wav, etc.)
        pronunciation_mappings: Custom pronunciation mappings
        sound_effects: Sound effects to apply
        max_wait_time: Maximum time to wait for task completion
        poll_interval: Interval between status polls
        cloudinary_options: Options for Cloudinary upload
        
    Returns:
        Dictionary containing status, url, and msg
    """
    # Validate input
    is_valid, error_msg = validate_text_input(text)
    if not is_valid:
        return {
            "status": "failed",
            "url": None,
            "msg": error_msg
        }
    
    try:
        # Step 1: Generate the audio task
        headers = create_minimax_client(api_key)
        
        # Build payload exactly like the working example
        payload = {
            "model": "speech-2.5-hd-preview",
            "text": text,
            "language_boost": "auto",
            "voice_setting": {
                "voice_id": voice_id,
                "speed": 1,
                "vol": 1,
                "pitch": 1
            },
            "audio_setting": {
                "audio_sample_rate": 32000,
                "bitrate": 128000,
                "format": file_format,
                "channel": 2
            }
        }
        
        # Add optional pronunciation dictionary
        if pronunciation_mappings:
            payload["pronunciation_dict"] = {
                "tone": pronunciation_mappings
            }
        
        # Add optional voice modification
        if sound_effects:
            payload["voice_modify"] = {
                "pitch": 0,
                "intensity": 0,
                "timbre": 0,
                "sound_effects": sound_effects
            }
        
        # Submit task
        success, response_data = submit_minimax_task(headers, payload)
        
        if not success:
            return {
                "status": "failed",
                "url": None,
                "msg": response_data.get("error", "Failed to submit task")
            }
        
        task_id = response_data.get("task_id")
        if not task_id:
            return {
                "status": "failed",
                "url": None,
                "msg": "No task ID returned from generation request"
            }
        
        # Step 2: Poll for task completion
        print(f"Polling task {task_id} for completion...")
        polling_result = poll_minimax_task_status(
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
        
        audio_url = polling_result.get("audio_url")
        if not audio_url:
            return {
                "status": "failed",
                "url": None,
                "msg": "No audio URL returned from completed task"
            }
        
        # Step 3: Download the audio
        print(f"Downloading audio from: {audio_url}")
        download_success, download_result = download_audio_from_url(audio_url)
        
        if not download_success:
            return {
                "status": "failed",
                "url": None,
                "msg": f"Failed to download audio: {download_result}"
            }
        
        temp_file_path = download_result
        
        try:
            # Step 4: Upload to Cloudinary
            print(f"Uploading audio to Cloudinary...")
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
                "voice_used": voice_id,
                "text_length": len(text),
                "file_format": file_format,
                "original_audio_url": audio_url
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


# Voice mapping for easy access (using valid Minimax voice IDs)
AVAILABLE_VOICES = {
    "narrator": "English_expressive_narrator",
    "female": "English_female_narrator",
    "male": "English_male_narrator",
    "child": "English_child_voice",
    "elderly": "English_elderly_voice"
}


def get_voice_id(voice_key: str) -> str:
    """
    Get voice ID from key.
    
    Args:
        voice_key: Voice key (narrator, female, male, child, elderly)
        
    Returns:
        Actual voice ID for API
    """
    return AVAILABLE_VOICES.get(voice_key.lower(), "English_expressive_narrator")


def generate_with_voice_key(text: str, voice_key: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate audio using voice key for convenience.
    
    Args:
        text: Text to convert
        voice_key: Voice key (narrator, female, male, child, elderly)
        api_key: Minimax API key
        
    Returns:
        Dictionary containing result
    """
    voice_id = get_voice_id(voice_key)
    return generate_minimax_audio(text, api_key, voice_id)


def query_minimax_task_status(task_id: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Query the status of a Minimax TTS task.
    
    Args:
        task_id: Task ID to query
        api_key: Minimax API key
        
    Returns:
        Dictionary containing task status information
    """
    if not api_key:
        api_key = os.environ.get("MINIMAX_API_KEY")
        if not api_key:
            return {
                "success": False,
                "error": "MINIMAX_API_KEY not found in environment variables"
            }
    
    if not task_id:
        return {
            "success": False,
            "error": "Task ID is required"
        }
    
    try:
        url = "https://api.minimax.io/v1/t2a_async_v2/query"
        headers = create_minimax_client(api_key)
        params = {"task_id": task_id}
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        # Check for API errors
        if result.get("base_resp", {}).get("status_code") != 0:
            return {
                "success": False,
                "error": f"API Error: {result.get('base_resp', {}).get('status_msg', 'Unknown error')}",
                "status_code": result.get("base_resp", {}).get("status_code"),
                "response": result
            }
        
        return {
            "success": True,
            "data": result,
            "status": result.get("status", "unknown"),
            "audio_url": result.get("audio_url")
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e)
        }
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Invalid JSON response: {str(e)}"
        }


def poll_minimax_task_status(task_id: str, api_key: Optional[str] = None, max_wait_time: int = 300, poll_interval: int = 10) -> Dict[str, Any]:
    """
    Poll Minimax task status until completion or failure.
    
    Args:
        task_id: Task ID to poll
        api_key: Minimax API key
        max_wait_time: Maximum time to wait in seconds (default 5 minutes)
        poll_interval: Interval between polls in seconds (default 10 seconds)
        
    Returns:
        Dictionary containing final task status and result
    """
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        status_result = query_minimax_task_status(task_id, api_key)
        
        if not status_result.get("success"):
            return status_result
        
        # Check if task is completed
        task_status = status_result.get("status", "").lower()
        
        if task_status == "success" or task_status == "completed":
            return {
                "success": True,
                "status": "completed",
                "data": status_result.get("data"),
                "audio_url": status_result.get("audio_url")
            }
        elif task_status == "failed" or task_status == "error":
            return {
                "success": False,
                "status": "failed",
                "error": status_result.get("error", "Task failed"),
                "data": status_result.get("data")
            }
        elif task_status in ["pending", "processing", "running"]:
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


def download_audio_from_url(audio_url: str, temp_dir: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Download audio from URL to temporary file.
    
    Args:
        audio_url: URL of the audio to download
        temp_dir: Temporary directory path (optional)
        
    Returns:
        Tuple of (success: bool, file_path: Optional[str])
    """
    try:
        response = requests.get(audio_url, timeout=30)
        response.raise_for_status()
        
        # Create temporary file
        if temp_dir:
            os.makedirs(temp_dir, exist_ok=True)
            temp_file = tempfile.NamedTemporaryFile(delete=False, dir=temp_dir, suffix='.mp3')
        else:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        
        temp_file.write(response.content)
        temp_file.close()
        
        return True, temp_file.name
        
    except Exception as e:
        return False, str(e)




# Example usage and testing functions
# Wrapper function for tool_router compatibility
def minimax_audio_clone(text: str, voice_sample_url: str, voice_id: Optional[str] = None, 
                       quality: str = "high", upload_to_cloudinary: bool = True, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Wrapper function for Minimax audio cloning that matches the expected tool interface.
    
    Args:
        text: Text to generate in cloned voice
        voice_sample_url: URL of voice sample for cloning
        voice_id: Optional voice ID for existing cloned voice
        quality: Audio quality setting
        upload_to_cloudinary: Whether to upload to Cloudinary
        api_key: Minimax API key
        
    Returns:
        Dictionary with generation result
    """
    # Call the main generation function
    return generate_minimax_audio(
        text=text,
        voice_sample_url=voice_sample_url,
        voice_id=voice_id,
        quality=quality,
        upload_to_cloudinary=upload_to_cloudinary,
        api_key=api_key
    )

def test_minimax_audio():
    """
    Test function for Minimax audio generation.
    """
    test_text = "Hello, this is a test of the Minimax audio generation system."
    
    # Test simplified generation
    result = generate_minimax_audio(test_text)
    print("Simplified generation result:", result)
    
    if result["status"] == "success":
        print(f"✅ Audio generated successfully: {result['url']}")
        print(f"   Voice: {result['voice_used']}")
        print(f"   Format: {result['file_format']}")
    else:
        print(f"❌ Error: {result['msg']}")
    
    # Test with pronunciation mappings
    result2 = generate_minimax_audio(
        "Omg, this is amazing!",
        pronunciation_mappings=["Omg/Oh my god"]
    )
    print("With pronunciation mappings:", result2)
    
    if result2["status"] == "success":
        print(f"✅ Audio with pronunciation generated: {result2['url']}")
    else:
        print(f"❌ Error: {result2['msg']}")
    
    return result, result2


if __name__ == "__main__":
    test_minimax_audio()