"""
Minimax Audio Clone Tool
Functional programming implementation for voice cloning using Minimax API
"""

import requests
import json
import os
import time
from typing import Dict, List, Optional, Tuple, Any, Union
from functools import partial


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


def build_voice_setting(
    voice_id: str = "English_expressive_narrator",
    speed: float = 1.0,
    volume: float = 1.0,
    pitch: float = 1.0
) -> Dict[str, Any]:
    """
    Build voice setting configuration.
    
    Args:
        voice_id: Voice ID to use
        speed: Speech speed (0.5 - 2.0)
        volume: Volume level (0.1 - 2.0)
        pitch: Pitch adjustment (0.5 - 2.0)
        
    Returns:
        Dictionary containing voice settings
    """
    return {
        "voice_id": voice_id,
        "speed": max(0.5, min(2.0, speed)),
        "vol": max(0.1, min(2.0, volume)),
        "pitch": max(0.5, min(2.0, pitch))
    }


def build_audio_setting(
    sample_rate: int = 32000,
    bitrate: int = 128000,
    format: str = "mp3",
    channel: int = 2
) -> Dict[str, Any]:
    """
    Build audio setting configuration.
    
    Args:
        sample_rate: Audio sample rate
        bitrate: Audio bitrate
        format: Audio format (mp3, wav, etc.)
        channel: Number of audio channels
        
    Returns:
        Dictionary containing audio settings
    """
    return {
        "audio_sample_rate": sample_rate,
        "bitrate": bitrate,
        "format": format,
        "channel": channel
    }


def build_voice_modify(
    pitch: float = 0,
    intensity: float = 0,
    timbre: float = 0,
    sound_effects: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build voice modification settings.
    
    Args:
        pitch: Pitch modification (-1.0 to 1.0)
        intensity: Intensity modification (-1.0 to 1.0)
        timbre: Timbre modification (-1.0 to 1.0)
        sound_effects: Sound effects (e.g., "spacious_echo")
        
    Returns:
        Dictionary containing voice modification settings
    """
    modify = {
        "pitch": max(-1.0, min(1.0, pitch)),
        "intensity": max(-1.0, min(1.0, intensity)),
        "timbre": max(-1.0, min(1.0, timbre))
    }
    
    if sound_effects:
        modify["sound_effects"] = sound_effects
    
    return modify


def build_pronunciation_dict(tone_mappings: Optional[List[str]] = None) -> Dict[str, List[str]]:
    """
    Build pronunciation dictionary for custom pronunciations.
    
    Args:
        tone_mappings: List of tone mappings (e.g., ["Omg/Oh my god"])
        
    Returns:
        Dictionary containing pronunciation settings
    """
    if not tone_mappings:
        return {}
    
    return {
        "tone": tone_mappings
    }


def build_minimax_payload(
    text: str,
    model: str = "speech-2.5-hd-preview",
    language_boost: str = "auto",
    voice_setting: Optional[Dict[str, Any]] = None,
    audio_setting: Optional[Dict[str, Any]] = None,
    voice_modify: Optional[Dict[str, Any]] = None,
    pronunciation_dict: Optional[Dict[str, List[str]]] = None
) -> Dict[str, Any]:
    """
    Build the complete payload for Minimax TTS request.
    
    Args:
        text: Text to convert to speech
        model: Model to use for generation
        language_boost: Language boost setting
        voice_setting: Voice configuration
        audio_setting: Audio configuration
        voice_modify: Voice modification settings
        pronunciation_dict: Pronunciation dictionary
        
    Returns:
        Dictionary containing the complete request payload
    """
    payload = {
        "model": model,
        "text": text,
        "language_boost": language_boost
    }
    
    # Add voice setting
    if voice_setting:
        payload["voice_setting"] = voice_setting
    else:
        payload["voice_setting"] = build_voice_setting()
    
    # Add audio setting
    if audio_setting:
        payload["audio_setting"] = audio_setting
    else:
        payload["audio_setting"] = build_audio_setting()
    
    # Add voice modification
    if voice_modify:
        payload["voice_modify"] = voice_modify
    
    # Add pronunciation dictionary
    if pronunciation_dict:
        payload["pronunciation_dict"] = pronunciation_dict
    
    return payload


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


def query_task_status(task_id: str, headers: Dict[str, str]) -> Tuple[bool, Dict[str, Any]]:
    """
    Query the status of a Minimax TTS task.
    
    Args:
        task_id: Task ID to query
        headers: Request headers
        
    Returns:
        Tuple of (success: bool, response_data: dict)
    """
    url = f"https://api.minimax.io/v1/query/t2a_async_query_v2?task_id={task_id}"
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, {"error": str(e)}


def wait_for_completion(
    task_id: str,
    headers: Dict[str, str],
    max_wait_time: int = 300,
    poll_interval: int = 5
) -> Tuple[bool, Dict[str, Any]]:
    """
    Wait for task completion with polling.
    
    Args:
        task_id: Task ID to monitor
        headers: Request headers
        max_wait_time: Maximum time to wait in seconds
        poll_interval: Polling interval in seconds
        
    Returns:
        Tuple of (success: bool, final_response: dict)
    """
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        success, response_data = query_task_status(task_id, headers)
        
        if not success:
            return False, response_data
        
        status = response_data.get("status", "").lower()
        
        if status == "completed":
            return True, response_data
        elif status == "failed":
            return False, {"error": "Task failed", "response": response_data}
        
        time.sleep(poll_interval)
    
    return False, {"error": "Task timeout", "task_id": task_id}


def generate_minimax_audio(
    text: str,
    api_key: Optional[str] = None,
    voice_id: str = "English_expressive_narrator",
    speed: float = 1.0,
    volume: float = 1.0,
    pitch: float = 1.0,
    audio_format: str = "mp3",
    sample_rate: int = 32000,
    bitrate: int = 128000,
    channels: int = 2,
    voice_pitch_modify: float = 0,
    voice_intensity_modify: float = 0,
    voice_timbre_modify: float = 0,
    sound_effects: Optional[str] = None,
    pronunciation_mappings: Optional[List[str]] = None,
    wait_for_completion_flag: bool = True,
    max_wait_time: int = 300
) -> Dict[str, Any]:
    """
    Generate audio using Minimax voice cloning API.
    
    Args:
        text: Text to convert to speech
        api_key: Minimax API key
        voice_id: Voice ID to use
        speed: Speech speed (0.5 - 2.0)
        volume: Volume level (0.1 - 2.0)
        pitch: Pitch adjustment (0.5 - 2.0)
        audio_format: Audio format (mp3, wav, etc.)
        sample_rate: Audio sample rate
        bitrate: Audio bitrate
        channels: Number of audio channels
        voice_pitch_modify: Pitch modification (-1.0 to 1.0)
        voice_intensity_modify: Intensity modification (-1.0 to 1.0)
        voice_timbre_modify: Timbre modification (-1.0 to 1.0)
        sound_effects: Sound effects
        pronunciation_mappings: Custom pronunciation mappings
        wait_for_completion_flag: Whether to wait for completion
        max_wait_time: Maximum wait time in seconds
        
    Returns:
        Dictionary containing result or error information
    """
    # Validate input
    is_valid, error_msg = validate_text_input(text)
    if not is_valid:
        return {
            "success": False,
            "error": error_msg
        }
    
    try:
        # Create client
        headers = create_minimax_client(api_key)
        
        # Build configurations
        voice_setting = build_voice_setting(voice_id, speed, volume, pitch)
        audio_setting = build_audio_setting(sample_rate, bitrate, audio_format, channels)
        voice_modify = build_voice_modify(
            voice_pitch_modify, voice_intensity_modify, voice_timbre_modify, sound_effects
        )
        pronunciation_dict = build_pronunciation_dict(pronunciation_mappings)
        
        # Build payload
        payload = build_minimax_payload(
            text=text,
            voice_setting=voice_setting,
            audio_setting=audio_setting,
            voice_modify=voice_modify,
            pronunciation_dict=pronunciation_dict
        )
        
        # Submit task
        success, response_data = submit_minimax_task(headers, payload)
        
        if not success:
            return {
                "success": False,
                "error": response_data.get("error", "Failed to submit task")
            }
        
        task_id = response_data.get("task_id")
        file_id = response_data.get("file_id")
        usage_characters = response_data.get("usage_characters")
        
        result = {
            "success": True,
            "task_id": task_id,
            "file_id": file_id,
            "usage_characters": usage_characters,
            "status": "submitted"
        }
        
        # Wait for completion if requested
        if wait_for_completion_flag and task_id:
            wait_success, final_response = wait_for_completion(
                task_id, headers, max_wait_time
            )
            
            if wait_success:
                result.update({
                    "status": "completed",
                    "final_response": final_response
                })
            else:
                result.update({
                    "status": "timeout_or_failed",
                    "error": final_response.get("error", "Unknown error")
                })
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def generate_with_voice_clone(
    text: str,
    voice_id: str,
    api_key: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Generate audio with specific voice clone.
    
    Args:
        text: Text to convert
        voice_id: Voice ID to use
        api_key: Minimax API key
        **kwargs: Additional parameters
        
    Returns:
        Dictionary containing result
    """
    return generate_minimax_audio(
        text=text,
        voice_id=voice_id,
        api_key=api_key,
        **kwargs
    )


def generate_with_emotion(
    text: str,
    emotion: str = "neutral",
    api_key: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Generate audio with emotional tone.
    
    Args:
        text: Text to convert
        emotion: Emotional tone
        api_key: Minimax API key
        **kwargs: Additional parameters
        
    Returns:
        Dictionary containing result
    """
    emotion_settings = {
        "excited": {"speed": 1.2, "volume": 1.1, "voice_intensity_modify": 0.3},
        "calm": {"speed": 0.8, "volume": 0.9, "voice_intensity_modify": -0.2},
        "sad": {"speed": 0.7, "volume": 0.8, "voice_pitch_modify": -0.3},
        "happy": {"speed": 1.1, "volume": 1.0, "voice_pitch_modify": 0.2},
        "angry": {"speed": 1.3, "volume": 1.2, "voice_intensity_modify": 0.5},
        "whisper": {"speed": 0.6, "volume": 0.5, "voice_intensity_modify": -0.5}
    }
    
    settings = emotion_settings.get(emotion.lower(), {})
    kwargs.update(settings)
    
    return generate_minimax_audio(text, api_key, **kwargs)


# Convenience functions for common use cases
def generate_narrator_audio(text: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Generate audio with narrator voice."""
    return generate_with_voice_clone(text, "English_expressive_narrator", api_key)


def generate_female_voice(text: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Generate audio with female voice."""
    return generate_with_voice_clone(text, "English_female_narrator", api_key)


def generate_male_voice(text: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Generate audio with male voice."""
    return generate_with_voice_clone(text, "English_male_narrator", api_key)


def generate_excited_audio(text: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Generate excited audio."""
    return generate_with_emotion(text, "excited", api_key)


def generate_calm_audio(text: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Generate calm audio."""
    return generate_with_emotion(text, "calm", api_key)


# Higher-order functions for functional composition
def with_voice_id(voice_id: str):
    """
    Create a partial function with a specific voice ID.
    
    Args:
        voice_id: Voice ID to use
        
    Returns:
        Partial function with voice ID pre-configured
    """
    return partial(generate_with_voice_clone, voice_id=voice_id)


def with_emotion_type(emotion: str):
    """
    Create a partial function with a specific emotion.
    
    Args:
        emotion: Emotional tone to use
        
    Returns:
        Partial function with emotion pre-configured
    """
    return partial(generate_with_emotion, emotion=emotion)


def with_audio_format(audio_format: str):
    """
    Create a partial function with a specific audio format.
    
    Args:
        audio_format: Audio format to use
        
    Returns:
        Partial function with audio format pre-configured
    """
    return partial(generate_minimax_audio, audio_format=audio_format)


def with_sound_effects(sound_effects: str):
    """
    Create a partial function with specific sound effects.
    
    Args:
        sound_effects: Sound effects to apply
        
    Returns:
        Partial function with sound effects pre-configured
    """
    return partial(generate_minimax_audio, sound_effects=sound_effects)


# Voice mapping for easy access
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
    Generate audio using voice key.
    
    Args:
        text: Text to convert
        voice_key: Voice key (narrator, female, male, child, elderly)
        api_key: Minimax API key
        
    Returns:
        Dictionary containing result
    """
    voice_id = get_voice_id(voice_key)
    return generate_with_voice_clone(text, voice_id, api_key)


# Example usage and testing functions
def test_minimax_audio():
    """
    Test function for Minimax audio generation.
    """
    test_text = "Omg, the real danger is not that computers start thinking like people, but that people start thinking like computers. Computers can only help us with simple tasks."
    
    # Test basic generation
    result = generate_minimax_audio(test_text, wait_for_completion_flag=False)
    print("Basic generation result:", result)
    
    # Test with emotion
    result2 = generate_excited_audio(test_text)
    print("Excited generation result:", result2)
    
    # Test with voice key
    result3 = generate_with_voice_key(test_text, "female")
    print("Female voice generation result:", result3)
    
    return result, result2, result3


if __name__ == "__main__":
    test_minimax_audio()