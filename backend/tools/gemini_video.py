# NEW SDK
from google import genai
from google.genai import types
import json
import os
import requests
import base64
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables (set GOOGLE_API_KEY or GEMINI_API_KEY in your .env)
load_dotenv()

# Create a global client (API key is automatically detected from environment)
client = genai.Client()

def analyze_video(
    system_prompt: str,
    user_query: str,
    video_url: str,
    model_name: str = "gemini-2.5-pro"
) -> Dict[str, Any]:
    """
    Analyze a single video (by URL) using the Gemini model.

    Args:
        system_prompt (str): System-level instructions (assistant role / response format).
        user_query (str): The user's query or instruction about the video.
        video_url (str): Publicly accessible URL of the video to analyze.
        model_name (str): Gemini model to use. Default: "gemini-2.5-pro".

    Returns:
        Dict[str, Any]: Parsed JSON response from Gemini, or an error dict.
    """
    try:
        # Configure generation parameters
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.2,
            max_output_tokens=4000,
            response_mime_type="application/json"
        )

        # Build the content payload
        try:
            # Fetch the video from URL
            response = requests.get(video_url)
            response.raise_for_status()
            
            # Determine MIME type from content type or URL
            content_type = response.headers.get('content-type', 'video/mp4')
            if 'video/' not in content_type:
                content_type = 'video/mp4'  # Default fallback
            
            # Use types.Part.from_bytes for proper video handling
            video_part = types.Part.from_bytes(
                data=response.content,
                mime_type=content_type
            )
            
            contents = [user_query, video_part]
        except Exception as e:
            return {"error": f"Failed to fetch video from {video_url}: {str(e)}"}

        # Generate response using the new SDK
        response = client.models.generate_content(
            model=model_name,
            config=config,
            contents=contents
        )

        # Extract response text
        response_content = response.text.strip()

        # Try to parse JSON; if not valid JSON, return raw content for debugging
        try:
            parsed = json.loads(response_content)
            return parsed
        except json.JSONDecodeError as e:
            # Try to fix common JSON issues
            try:
                # Remove trailing incomplete parts
                cleaned_content = response_content.strip()
                
                # If it ends with incomplete array or object, try to close it
                if cleaned_content.endswith('[') or cleaned_content.endswith('{'):
                    cleaned_content = cleaned_content[:-1]
                elif cleaned_content.endswith('[\'') or cleaned_content.endswith('["'):
                    cleaned_content = cleaned_content[:-2]
                elif cleaned_content.endswith('[\'}'):
                    cleaned_content = cleaned_content[:-3]
                
                # Try to find the last complete object/array and close it
                if cleaned_content.count('{') > cleaned_content.count('}'):
                    cleaned_content += '}' * (cleaned_content.count('{') - cleaned_content.count('}'))
                elif cleaned_content.count('[') > cleaned_content.count(']'):
                    cleaned_content += ']' * (cleaned_content.count('[') - cleaned_content.count(']'))
                
                # Try parsing the cleaned content
                parsed = json.loads(cleaned_content)
                return parsed
                
            except json.JSONDecodeError:
                # If still can't parse, return the raw response with error info
                return {
                    "error": "Failed to parse JSON response from Gemini - response may be truncated",
                    "raw_response": response_content[:1000] + "..." if len(response_content) > 1000 else response_content,
                    "json_error": str(e)
                }

    except Exception as e:
        return {"error": f"API call failed: {str(e)}"}


# Example usage
if __name__ == "__main__":
    system_prompt = (
        "You are a helpful multimodal analyst. Reply with a JSON object containing "
        "fields: summary, detected_objects, timestamps_of_key_events (list), "
        "scene_descriptions (list), safety_concerns (if any)."
    )
    user_query = "Analyze the video and return a structured JSON with objects, actions, and timestamps."
    video_url = "https://example.com/some-video.mp4"

    result = analyze_video(system_prompt, user_query, video_url)
    print(json.dumps(result, indent=2))
