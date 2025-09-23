import google.generativeai as genai
import json
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables (set GOOGLE_API_KEY or GEMINI_API_KEY in your .env)
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def orchestrator_function_gemini_with_video(
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
        # Initialize the Gemini model with the system instruction
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_prompt
        )

        # Generation configuration: low temperature for structured responses
        generation_config = genai.types.GenerationConfig(
            temperature=0.2,
            max_output_tokens=1800,
            response_mime_type="application/json"
        )

        # Build the content payload
        # NOTE: some genai versions expect {"video_url": ...}, others expect {"media_url": ..., "media_type":"video/mp4"} or nested "media".
        # If you see an error, change the media part shape to match your genai client version.
        contents = [
            {
                "role": "user",
                "parts": [
                    {"text": user_query},
                    {"video_url": video_url}   # <-- change this key if your client requires a different shape
                ]
            }
        ]

        # Call the model
        response = model.generate_content(
            contents,
            generation_config=generation_config
        )

        # Extract response text
        response_content = response.text.strip()

        # Try to parse JSON; if not valid JSON, return raw content for debugging
        try:
            parsed = json.loads(response_content)
            return parsed
        except json.JSONDecodeError:
            return {
                "error": "Failed to parse JSON response from Gemini.",
                "raw_response": response_content
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

    result = orchestrator_function_gemini_with_video(system_prompt, user_query, video_url)
    print(json.dumps(result, indent=2))
