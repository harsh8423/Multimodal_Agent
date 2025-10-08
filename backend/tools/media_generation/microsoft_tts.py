import requests
import json
import os
import wave
import base64
import tempfile
from dotenv import load_dotenv
from typing import Dict, Optional, List, Any
import time
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))
from upload_cloudinary import upload_to_cloudinary

load_dotenv()

class MicrosoftTTS:
    """
    Microsoft Text-to-Speech REST API client with neural voices support.
    """
    
    def __init__(self, subscription_key: str = None, region: str = None):
        """
        Initialize Microsoft TTS client.
        
        Args:
            subscription_key: Azure Speech Services subscription key
            region: Azure region (e.g., 'eastus', 'westus2')
        """
        self.subscription_key = subscription_key or os.environ.get("AZURE_SPEECH_KEY")
        self.region = region or os.environ.get("AZURE_SPEECH_REGION", "eastus")
        self.base_url = f"https://{self.region}.tts.speech.microsoft.com"
        
        if not self.subscription_key:
            raise ValueError("Azure Speech Services subscription key is required")
    
    def get_access_token(self) -> str:
        """
        Get access token for Azure Speech Services.
        
        Returns:
            str: Access token for API requests
        """
        token_url = f"https://{self.region}.api.cognitive.microsoft.com/sts/v1.0/issuetoken"
        headers = {
            'Ocp-Apim-Subscription-Key': self.subscription_key
        }
        
        response = requests.post(token_url, headers=headers)
        response.raise_for_status()
        return response.text
 
    def synthesize_speech(self, 
                         text: str, 
                         voice_name: str = "en-US-AriaNeural",
                         output_format: str = "riff-24khz-16bit-mono-pcm",
                         rate: str = "0%",
                         pitch: str = "0%",
                         volume: str = "0%") -> bytes:
        """
        Synthesize speech from text using Microsoft TTS.
        
        Args:
            text: Text to convert to speech
            voice_name: Voice to use (e.g., 'en-US-AriaNeural', 'en-US-JennyNeural')
            output_format: Audio format (riff-24khz-16bit-mono-pcm, riff-48khz-16bit-mono-pcm, etc.)
            rate: Speech rate (-50% to +200%)
            pitch: Speech pitch (-50% to +50%)
            volume: Speech volume (-50% to +50%)
        
        Returns:
            bytes: Raw audio data
        """
        token = self.get_access_token()
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/ssml+xml',
            'X-Microsoft-OutputFormat': output_format
        }
        
        # Create SSML with neural voice
        ssml = f"""
        <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>
            <voice name='{voice_name}'>
                <prosody rate='{rate}' pitch='{pitch}' volume='{volume}'>
                    {text}
                </prosody>
            </voice>
        </speak>
        """
        
        synthesis_url = f"{self.base_url}/cognitiveservices/v1"
        response = requests.post(synthesis_url, headers=headers, data=ssml)
        response.raise_for_status()
        
        return response.content
    
    def save_audio(self, audio_data: bytes, filename: str) -> Dict:
        """
        Save audio data to file.
        
        Args:
            audio_data: Raw audio bytes
            filename: Output filename
        
        Returns:
            Dict: Result with success status and file info
        """
        try:
            with open(filename, 'wb') as f:
                f.write(audio_data)
            
            return {
                "success": True,
                "filename": filename,
                "size": len(audio_data)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Wrapper function for tool_router compatibility
def microsoft_tts(text: str, voice_name: str = "en-US-JennyNeural", 
                 style: Optional[str] = None, subscription_key: Optional[str] = None, region: Optional[str] = None) -> Dict[str, Any]:
    """
    Wrapper function for Microsoft TTS that matches the expected tool interface.
    
    Args:
        text: Text to convert to speech
        voice_name: Voice name
        style: Voice style
        subscription_key: Azure Speech Services subscription key
        region: Azure region
        
    Returns:
        Dictionary with generation result
    """
    # Create MicrosoftTTS instance
    tts = MicrosoftTTS(subscription_key, region)
    
    # Call the main generation function
    return generate_audio_microsoft(
        text=text,
        voice_name=voice_name,
        cloudinary_options={"upload": True},  # Always upload to Cloudinary
        cheerful=style == "cheerful" if style else False
    )

def generate_audio_microsoft(text: str, 
                           voice_name: str = "en-US-AriaNeural",
                           rate: str = "0%",
                           pitch: str = "0%",
                           volume: str = "0%",
                           cloudinary_options: Optional[Dict] = None,
                           cheerful: bool = False) -> Dict:
    """
    Generate audio from text using Microsoft TTS, upload to Cloudinary, and clean up.
    
    Args:
        text: Text to convert to speech
        voice_name: Neural voice to use
        rate: Speech rate (-50% to +200%)
        pitch: Speech pitch (-50% to +50%)
        volume: Speech volume (-50% to +50%)
        cloudinary_options: Options for Cloudinary upload
        cheerful: If True, uses enhanced prosody for cheerful voice
    
    Returns:
        Dict: Result containing status, url, and msg
    """
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    temp_filename = temp_file.name
    temp_file.close()
    
    try:
        # Adjust parameters for cheerful voice if requested
        if cheerful:
            rate = "10%"  # Slightly faster for cheerfulness
            pitch = "50%"  # Slightly higher pitch
            volume = "30%"  # Slightly louder
        
        # Generate audio using Microsoft TTS
        tts = MicrosoftTTS()
        
        # Generate audio
        audio_data = tts.synthesize_speech(
            text=text,
            voice_name=voice_name,
            rate=rate,
            pitch=pitch,
            volume=volume
        )
        
        # Save to temporary file
        with open(temp_filename, 'wb') as f:
            f.write(audio_data)
        
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
            "voice_used": voice_name,
            "text_length": len(text),
            "rate": rate,
            "pitch": pitch,
            "volume": volume,
            "file_size": len(audio_data),
            "cheerful": cheerful
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


# Example usage and testing
if __name__ == "__main__":
    # Test basic functionality
    print("🎤 Testing Microsoft Text-to-Speech...")
    
    # Test 1: Basic audio generation
    result = generate_audio_microsoft(
        text="Have a wonderful day! Microsoft TTS makes everything sound great!",
        voice_name="en-US-JennyNeural"
    )
    
    if result["status"] == "success":
        print(f"✅ Basic audio generated: {result['url']}")
        print(f"   Voice: {result['voice_used']}")
        print(f"   Size: {result['file_size']} bytes")
    else:
        print(f"❌ Error: {result['msg']}")
    
    # Test 2: Cheerful audio generation
    result2 = generate_audio_microsoft(
        text="This is a cheerful test message!",
        voice_name="en-US-AriaNeural",
        cheerful=True
    )
    
    if result2["status"] == "success":
        print(f"✅ Cheerful audio generated: {result2['url']}")
        print(f"   Voice: {result2['voice_used']}")
        print(f"   Cheerful: {result2['cheerful']}")
    else:
        print(f"❌ Error: {result2['msg']}")
 