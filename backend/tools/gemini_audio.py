"""
Gemini Audio Generation Tool
Functional programming implementation for text-to-speech using Google Gemini API
"""

import os
import wave
import struct
import re
from typing import Dict, List, Optional, Tuple, Any, Union
from functools import partial
from google import genai
from google.genai import types


def create_gemini_client(api_key: Optional[str] = None) -> genai.Client:
    """
    Create Gemini API client.
    
    Args:
        api_key: Gemini API key (if not provided, will use environment variable)
        
    Returns:
        Configured Gemini client
    """
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
    
    return genai.Client(api_key=api_key)


def parse_audio_mime_type(mime_type: str) -> Dict[str, int]:
    """
    Parse bits per sample and rate from an audio MIME type string.
    
    Args:
        mime_type: The audio MIME type string (e.g., "audio/L16;rate=24000")
        
    Returns:
        Dictionary with "bits_per_sample" and "rate" keys
    """
    bits_per_sample = 16
    rate = 24000
    
    # Extract rate from parameters
    parts = mime_type.split(";")
    for param in parts:
        param = param.strip()
        if param.lower().startswith("rate="):
            try:
                rate_str = param.split("=", 1)[1]
                rate = int(rate_str)
            except (ValueError, IndexError):
                pass  # Keep rate as default
        elif param.startswith("audio/L"):
            try:
                bits_per_sample = int(param.split("L", 1)[1])
            except (ValueError, IndexError):
                pass  # Keep bits_per_sample as default
    
    return {"bits_per_sample": bits_per_sample, "rate": rate}


def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
    """
    Convert audio data to WAV format with proper header.
    
    Args:
        audio_data: Raw audio data as bytes
        mime_type: MIME type of the audio data
        
    Returns:
        WAV formatted audio data as bytes
    """
    parameters = parse_audio_mime_type(mime_type)
    bits_per_sample = parameters["bits_per_sample"]
    sample_rate = parameters["rate"]
    num_channels = 1
    data_size = len(audio_data)
    bytes_per_sample = bits_per_sample // 8
    block_align = num_channels * bytes_per_sample
    byte_rate = sample_rate * block_align
    chunk_size = 36 + data_size
    
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",          # ChunkID
        chunk_size,       # ChunkSize
        b"WAVE",          # Format
        b"fmt ",          # Subchunk1ID
        16,               # Subchunk1Size
        1,                # AudioFormat
        num_channels,     # NumChannels
        sample_rate,      # SampleRate
        byte_rate,        # ByteRate
        block_align,      # BlockAlign
        bits_per_sample,  # BitsPerSample
        b"data",          # Subchunk2ID
        data_size         # Subchunk2Size
    )
    return header + audio_data


def save_wave_file(filename: str, audio_data: bytes, channels: int = 1, rate: int = 24000, sample_width: int = 2) -> bool:
    """
    Save audio data as WAV file.
    
    Args:
        filename: Output filename
        audio_data: Raw audio data
        channels: Number of audio channels
        rate: Sample rate
        sample_width: Sample width in bytes
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(rate)
            wf.writeframes(audio_data)
        return True
    except Exception as e:
        print(f"Error saving WAV file: {e}")
        return False


def build_speech_config(
    voice_name: str = "Zephyr",
    speed: float = 1.0,
    pitch: float = 1.0,
    volume: float = 1.0
) -> types.SpeechConfig:
    """
    Build speech configuration for Gemini TTS.
    
    Args:
        voice_name: Name of the voice to use
        speed: Speech speed multiplier
        pitch: Pitch adjustment
        volume: Volume level
        
    Returns:
        Configured SpeechConfig object
    """
    return types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                voice_name=voice_name
            )
        )
    )


def build_generation_config(
    temperature: float = 1.0,
    speech_config: Optional[types.SpeechConfig] = None
) -> types.GenerateContentConfig:
    """
    Build generation configuration for Gemini TTS.
    
    Args:
        temperature: Generation temperature
        speech_config: Speech configuration
        
    Returns:
        Configured GenerateContentConfig object
    """
    if speech_config is None:
        speech_config = build_speech_config()
    
    return types.GenerateContentConfig(
        temperature=temperature,
        response_modalities=["audio"],
        speech_config=speech_config
    )


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
    
    if len(text) > 5000:  # Reasonable limit for TTS
        return False, "Text is too long (max 5000 characters)"
    
    return True, None


def generate_audio_simple(
    text: str,
    api_key: Optional[str] = None,
    voice_name: str = "Zephyr",
    temperature: float = 1.0,
    output_filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate audio from text using Gemini TTS (simple approach).
    
    Args:
        text: Text to convert to speech
        api_key: Gemini API key
        voice_name: Voice to use for generation
        temperature: Generation temperature
        output_filename: Optional output filename
        
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
        client = create_gemini_client(api_key)
        
        # Build configuration
        speech_config = build_speech_config(voice_name)
        config = build_generation_config(temperature, speech_config)
        
        # Generate content
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=text,
            config=config
        )
        
        # Extract audio data
        if (response.candidates and 
            response.candidates[0].content and 
            response.candidates[0].content.parts and
            response.candidates[0].content.parts[0].inline_data):
            
            inline_data = response.candidates[0].content.parts[0].inline_data
            audio_data = inline_data.data
            
            # Save file if filename provided
            if output_filename:
                save_wave_file(output_filename, audio_data)
            
            return {
                "success": True,
                "audio_data": audio_data,
                "mime_type": inline_data.mime_type,
                "filename": output_filename,
                "data_size": len(audio_data)
            }
        else:
            return {
                "success": False,
                "error": "No audio data received from API"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def generate_audio_streaming(
    text: str,
    api_key: Optional[str] = None,
    voice_name: str = "Zephyr",
    temperature: float = 1.0,
    output_filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate audio from text using Gemini TTS (streaming approach).
    
    Args:
        text: Text to convert to speech
        api_key: Gemini API key
        voice_name: Voice to use for generation
        temperature: Generation temperature
        output_filename: Optional output filename
        
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
        client = create_gemini_client(api_key)
        
        # Build configuration
        speech_config = build_speech_config(voice_name)
        config = build_generation_config(temperature, speech_config)
        
        # Build content
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=text)]
            )
        ]
        
        # Generate content with streaming
        audio_chunks = []
        file_index = 0
        
        for chunk in client.models.generate_content_stream(
            model="gemini-2.5-flash-preview-tts",
            contents=contents,
            config=config
        ):
            if (chunk.candidates and 
                chunk.candidates[0].content and 
                chunk.candidates[0].content.parts and
                chunk.candidates[0].content.parts[0].inline_data and
                chunk.candidates[0].content.parts[0].inline_data.data):
                
                inline_data = chunk.candidates[0].content.parts[0].inline_data
                audio_chunks.append(inline_data.data)
                
                # Save individual chunk if filename provided
                if output_filename:
                    chunk_filename = f"{output_filename}_{file_index}.wav"
                    save_wave_file(chunk_filename, inline_data.data)
                    file_index += 1
            else:
                # Handle text responses if any
                if chunk.text:
                    print(f"Text response: {chunk.text}")
        
        # Combine all audio chunks
        if audio_chunks:
            combined_audio = b''.join(audio_chunks)
            
            # Save combined file if filename provided
            if output_filename:
                combined_filename = f"{output_filename}_combined.wav"
                save_wave_file(combined_filename, combined_audio)
            
            return {
                "success": True,
                "audio_data": combined_audio,
                "chunks_count": len(audio_chunks),
                "filename": output_filename,
                "combined_filename": f"{output_filename}_combined.wav" if output_filename else None,
                "data_size": len(combined_audio)
            }
        else:
            return {
                "success": False,
                "error": "No audio chunks received from streaming API"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def generate_audio_with_emotion(
    text: str,
    emotion: str = "cheerful",
    api_key: Optional[str] = None,
    voice_name: str = "Zephyr"
) -> Dict[str, Any]:
    """
    Generate audio with emotional tone.
    
    Args:
        text: Text to convert to speech
        emotion: Emotional tone (cheerful, sad, excited, calm, etc.)
        api_key: Gemini API key
        voice_name: Voice to use
        
    Returns:
        Dictionary containing result or error information
    """
    emotion_prefixes = {
        "cheerful": "Say cheerfully: ",
        "sad": "Say sadly: ",
        "excited": "Say excitedly: ",
        "calm": "Say calmly: ",
        "angry": "Say angrily: ",
        "whisper": "Say in a whisper: ",
        "loud": "Say loudly: "
    }
    
    prefix = emotion_prefixes.get(emotion.lower(), "Say cheerfully: ")
    formatted_text = f"{prefix}{text}"
    
    return generate_audio_simple(
        text=formatted_text,
        api_key=api_key,
        voice_name=voice_name
    )


# Convenience functions for common use cases
def generate_cheerful_audio(text: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Generate cheerful audio."""
    return generate_audio_with_emotion(text, "cheerful", api_key)


def generate_calm_audio(text: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Generate calm audio."""
    return generate_audio_with_emotion(text, "calm", api_key)


def generate_excited_audio(text: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Generate excited audio."""
    return generate_audio_with_emotion(text, "excited", api_key)


# Higher-order functions for functional composition
def with_voice(voice_name: str):
    """
    Create a partial function with a specific voice.
    
    Args:
        voice_name: Voice name to use
        
    Returns:
        Partial function with voice pre-configured
    """
    return partial(generate_audio_simple, voice_name=voice_name)


def with_emotion(emotion: str):
    """
    Create a partial function with a specific emotion.
    
    Args:
        emotion: Emotional tone to use
        
    Returns:
        Partial function with emotion pre-configured
    """
    return partial(generate_audio_with_emotion, emotion=emotion)


def with_temperature(temperature: float):
    """
    Create a partial function with a specific temperature.
    
    Args:
        temperature: Generation temperature
        
    Returns:
        Partial function with temperature pre-configured
    """
    return partial(generate_audio_simple, temperature=temperature)


# Voice mapping for easy access
AVAILABLE_VOICES = {
    "zephyr": "Zephyr",
    "kore": "Kore",
    "nova": "Nova",
    "echo": "Echo"
}


def get_voice_name(voice_key: str) -> str:
    """
    Get voice name from key.
    
    Args:
        voice_key: Voice key (zephyr, kore, nova, echo)
        
    Returns:
        Actual voice name for API
    """
    return AVAILABLE_VOICES.get(voice_key.lower(), "Zephyr")


def generate_with_voice_key(text: str, voice_key: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate audio using voice key.
    
    Args:
        text: Text to convert
        voice_key: Voice key (zephyr, kore, nova, echo)
        api_key: Gemini API key
        
    Returns:
        Dictionary containing result
    """
    voice_name = get_voice_name(voice_key)
    return generate_audio_simple(text, api_key, voice_name)


# Example usage and testing functions
def test_gemini_audio():
    """
    Test function for Gemini audio generation.
    """
    test_text = "Have a wonderful day!"
    
    # Test simple generation
    result = generate_audio_simple(test_text, output_filename="test_output.wav")
    print("Simple generation result:", result)
    
    # Test with emotion
    result2 = generate_cheerful_audio(test_text)
    print("Cheerful generation result:", result2)
    
    # Test with voice key
    result3 = generate_with_voice_key(test_text, "kore")
    print("Voice key generation result:", result3)
    
    return result, result2, result3


if __name__ == "__main__":
    test_gemini_audio()