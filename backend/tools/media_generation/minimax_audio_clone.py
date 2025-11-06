"""
Minimax Audio Clone Tool
Simplified synchronous implementation for voice cloning using Minimax API
"""

import requests
import json
import os
import tempfile
import binascii
from typing import Dict, List, Optional, Tuple, Any
from dotenv import load_dotenv
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))
from upload_cloudinary import upload_to_cloudinary

load_dotenv()


def get_api_key(api_key: Optional[str] = None) -> str:
    """
    Get Minimax API key from parameter or environment.
    
    Args:
        api_key: Minimax API key (if not provided, will use environment variable)
        
    Returns:
        API key string
        
    Raises:
        ValueError: If API key is not found
    """
    if not api_key:
        api_key = os.environ.get("MINIMAX_API_KEY")
        if not api_key:
            raise ValueError("MINIMAX_API_KEY not found in environment variables")
    return api_key


def create_headers(api_key: str) -> Dict[str, str]:
    """
    Create request headers for Minimax API.
    
    Args:
        api_key: Minimax API key
        
    Returns:
        Dictionary containing headers for API requests
    """
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


def hex_to_mp3(hex_data: str) -> bytes:
    """
    Convert hex string to MP3 bytes.
    
    Args:
        hex_data: Hex string containing audio data
        
    Returns:
        MP3 audio bytes
        
    Raises:
        ValueError: If hex data is invalid
    """
    try:
        # Remove any whitespace and convert hex to bytes
        hex_clean = hex_data.replace(' ', '').replace('\n', '').replace('\r', '')
        return binascii.unhexlify(hex_clean)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid hex data: {str(e)}")


def save_temp_mp3(audio_bytes: bytes) -> str:
    """
    Save audio bytes to temporary MP3 file.
    
    Args:
        audio_bytes: MP3 audio bytes
        
    Returns:
        Path to temporary file
        
    Raises:
        IOError: If file cannot be created
    """
    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_file.write(audio_bytes)
        temp_file.close()
        return temp_file.name
    except Exception as e:
        raise IOError(f"Failed to create temporary file: {str(e)}")


def upload_audio_to_cloudinary(file_path: str, cloudinary_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Upload audio file to Cloudinary.
    
    Args:
        file_path: Path to audio file
        cloudinary_options: Options for Cloudinary upload
        
    Returns:
        Cloudinary upload result
        
    Raises:
        Exception: If upload fails
    """
    try:
        result = upload_to_cloudinary(file_path, cloudinary_options or {})
        return result
    except Exception as e:
        raise Exception(f"Cloudinary upload failed: {str(e)}")


def cleanup_temp_file(file_path: str) -> None:
    """
    Clean up temporary file.
    
    Args:
        file_path: Path to temporary file
    """
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
    except Exception:
        pass  # Ignore cleanup errors


def generate_audio_sync(
    text: str,
    voice_id: str = "moss_audio_d1efbcbb-a84b-11f0-acd3-2a7238f4ad26",
    voice_setting: Optional[Dict[str, Any]] = None,
    audio_setting: Optional[Dict[str, Any]] = None,
    voice_modify: Optional[Dict[str, Any]] = None,
    pronunciation_dict: Optional[Dict[str, List[str]]] = None,
    api_key: Optional[str] = None,
    cloudinary_options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Unified function to generate audio using synchronous Minimax API.
    Takes voice_id, text, voice settings, audio settings, voice modify, 
    converts hex audio to mp3 and uploads to Cloudinary.
    
    Args:
        text: Text to convert to speech
        voice_id: Voice ID to use
        voice_setting: Voice settings (speed, vol, pitch)
        audio_setting: Audio settings (sample_rate, bitrate, format, channel)
        voice_modify: Voice modification settings (pitch, intensity, timbre, sound_effects)
        pronunciation_dict: Pronunciation dictionary with tone mappings
        api_key: Minimax API key
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
        # Get API key and create headers
        api_key = get_api_key(api_key)
        headers = create_headers(api_key)
        
        # Build payload with defaults
        payload = {
            "model": "speech-2.5-hd-preview",
            "text": text,
            "stream": False,
            "language_boost": "auto",
            "output_format": "hex",
            "voice_setting": voice_setting or {
                "voice_id": voice_id,
                "speed": 1.0,
                "vol": 1.0,
                "pitch": 0
            },
            "audio_setting": audio_setting or {
                "sample_rate": 32000,
                "bitrate": 128000,
                "format": "mp3",
                "channel": 1
            }
        }
        
        # Add optional voice modification
        if voice_modify:
            payload["voice_modify"] = voice_modify
        
        # Make synchronous API call
        url = "https://api.minimax.io/v1/t2a_v2"
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(payload),
            timeout=60
        )
        
        response.raise_for_status()
        response_data = response.json()
        
        # Check for API errors
        if response_data.get("base_resp", {}).get("status_code") != 0:
            return {
                "status": "failed",
                "url": None,
                "msg": f"API Error: {response_data.get('base_resp', {}).get('status_msg', 'Unknown error')}"
            }
        
        # Get hex audio data - the data field contains a dict with audio field
        data_field = response_data.get("data")
        if not data_field:
            return {
                "status": "failed",
                "url": None,
                "msg": f"No data field returned from API. Response keys: {list(response_data.keys())}"
            }
        
        # Extract hex audio string from data.audio
        hex_audio = data_field.get("audio")
        if not hex_audio:
            return {
                "status": "failed",
                "url": None,
                "msg": f"No audio field in data. Data keys: {list(data_field.keys()) if isinstance(data_field, dict) else 'Not a dict'}"
            }
        
        # Check if hex_audio is a string (hex data)
        if not isinstance(hex_audio, str):
            return {
                "status": "failed",
                "url": None,
                "msg": f"Audio data is not a string. Type: {type(hex_audio)}"
            }
        
        # Convert hex to MP3 bytes
        try:
            audio_bytes = hex_to_mp3(hex_audio)
        except ValueError as e:
            return {
                "status": "failed",
                "url": None,
                "msg": f"Failed to convert hex audio: {str(e)}"
            }
        
        # Save to temporary file
        try:
            temp_file_path = save_temp_mp3(audio_bytes)
        except IOError as e:
            return {
                "status": "failed",
                "url": None,
                "msg": f"Failed to save temporary file: {str(e)}"
            }
        
        try:
            # Upload to Cloudinary
            cloudinary_result = upload_audio_to_cloudinary(temp_file_path, cloudinary_options)
            
            # Clean up temporary file
            cleanup_temp_file(temp_file_path)
            
            return {
                "status": "success",
                "url": cloudinary_result.get("secure_url"),
                "msg": None,
                "voice_used": voice_id,
                "text_length": len(text),
                "audio_size": len(audio_bytes)
            }
            
        except Exception as e:
            # Clean up temporary file on error
            cleanup_temp_file(temp_file_path)
            return {
                "status": "failed",
                "url": None,
                "msg": f"Failed to upload to Cloudinary: {str(e)}"
            }
        
    except requests.exceptions.RequestException as e:
        return {
            "status": "failed",
            "url": None,
            "msg": f"API request failed: {str(e)}"
        }
    except json.JSONDecodeError as e:
        return {
            "status": "failed",
            "url": None,
            "msg": f"Invalid JSON response: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "failed",
            "url": None,
            "msg": str(e)
        }




# Wrapper function for tool_router compatibility
def minimax_audio_clone(text: str, voice_sample_url: Optional[str] = None, voice_id: Optional[str] = None, 
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
    # Call the unified audio generation function
    return generate_audio_sync(
        text=text,
        voice_id=voice_id or "English_expressive_narrator",
        api_key=api_key
    )


def test_minimax_audio():
    """
    Test function for Minimax audio generation.
    """
    test_text = "Sahil either go to sleep or study"
    
    # Test synchronous generation
    result = generate_audio_sync(test_text)
    print("Synchronous generation result:", result)
    
    if result["status"] == "success":
        print(f"✅ Audio generated successfully: {result['url']}")
        print(f"   Voice: {result['voice_used']}")
        print(f"   Audio size: {result['audio_size']} bytes")
    else:
        print(f"❌ Error: {result['msg']}")
    
    # Test with custom settings
    custom_settings = {
        "voice_setting": {
            "voice_id": "English_expressive_narrator",
            "speed": 1.2,
            "vol": 1.0,
            "pitch": 0
        },
        "voice_modify": {
            "pitch": 0,
            "intensity": 0,
            "timbre": 0,
            "sound_effects": "spacious_echo"
        }
    }
    
    # result2 = generate_audio_sync(
    #     text="This is a test with custom voice settings and sound effects.",
    #     **custom_settings
    # )
    # print("Custom settings result:", result2)
    
    # if result2["status"] == "success":
    #     print(f"✅ Audio with custom settings generated: {result2['url']}")
    # else:
    #     print(f"❌ Error: {result2['msg']}")
    
    return result


if __name__ == "__main__":
    test_minimax_audio()