from google import genai
from google.genai import types
import wave
import base64
import os
import tempfile
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))
from upload_cloudinary import upload_to_cloudinary

load_dotenv()

# Set up the wave file to save the output:
def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
    """
    Write PCM audio data to a WAV file.
    
    Args:
        filename: Output filename
        pcm: Raw PCM audio bytes
        channels: Number of audio channels (1 for mono, 2 for stereo)
        rate: Sample rate in Hz (24000 for Gemini)
        sample_width: Sample width in bytes (2 for 16-bit audio)
    """
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)


# Wrapper function for tool_router compatibility
def gemini_audio(text: str, voice_name: str = "Kore", voice_style: Optional[str] = None, 
                cloudinary_options: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Wrapper function for Gemini audio generation that matches the expected tool interface.
    
    Args:
        text: Text to convert to speech
        voice_name: Voice to use
        voice_style: Voice style enhancement
        cloudinary_options: Options for Cloudinary upload
        
    Returns:
        Dictionary with generation result
    """
    # Enhance text with voice style if provided
    enhanced_text = text
    if voice_style:
        enhanced_text = f"say {voice_style}: {text}"
    
    # Call the main generation function
    return generate_audio(enhanced_text, voice_name, cloudinary_options)

def generate_audio(text, voice_name="Kore", cloudinary_options=None):
    """
    Generate audio from text using Gemini TTS, upload to Cloudinary, and clean up.
    
    Args:
        text: The text to convert to speech
        voice_name: Voice to use (e.g., 'Kore', 'Aoede', 'Charon', 'Fenrir', 'Puck')
        cloudinary_options: Options for Cloudinary upload
    
    Returns:
        dict: Result containing status, url, and msg
    """
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    temp_filename = temp_file.name
    temp_file.close()
    
    try:
        # Generate audio using Gemini TTS
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice_name,
                        )
                    )
                ),
            )
        )
        
        # Get the audio data - it's base64 encoded
        audio_data_b64 = response.candidates[0].content.parts[0].inline_data.data
        mime_type = response.candidates[0].content.parts[0].inline_data.mime_type
        
        # Decode base64 to get raw PCM audio bytes
        pcm_audio = base64.b64decode(audio_data_b64)
        
        # Write to WAV file with proper parameters for Gemini audio
        # Gemini returns: 24kHz, mono (1 channel), 16-bit (2 bytes) PCM
        wave_file(temp_filename, pcm_audio, channels=1, rate=24000, sample_width=2)
        
        # Upload to Cloudinary
        print(f"Uploading audio to Cloudinary...")
        cloudinary_result = upload_to_cloudinary(
            temp_filename,
            cloudinary_options or {}
        )
        
        # Clean up temporary file
        if os.path.exists(temp_filename):
            os.unlink(temp_filename)
        
        return {
            "status": "success",
            "url": cloudinary_result.get("secure_url"),
            "msg": None,
            "data_size": len(pcm_audio),
            "mime_type": mime_type,
            "voice_used": voice_name,
            "text_length": len(text)
        }
        
    except Exception as e:
        # Clean up temporary file on error
        if os.path.exists(temp_filename):
            os.unlink(temp_filename)
        
        return {
            "status": "failed",
            "url": None,
            "msg": str(e)
        }


# Example usage (can be commented out in production)
if __name__ == "__main__":
    result = generate_audio(
        text="Say cheerfully: Oh Harsh, you are so smart",
        voice_name="Kore"
    )
    
    if result["status"] == "success":
        print(f"✅ Audio generated successfully: {result['url']}")
        print(f"   Size: {result['data_size']} bytes")
        print(f"   MIME: {result['mime_type']}")
    else:
        print(f"❌ Error: {result['msg']}")