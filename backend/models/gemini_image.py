import google.generativeai as genai
import json
import os
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def orchestrator_function_gemini_with_images(
    system_prompt: str,
    user_query: str,
    image_urls: List[str],
    model_name: str = "gemini-2.5-flash"
) -> Dict[str, Any]:
    """
    Function to interact with Gemini API and analyze images via URLs.

    Args:
        system_prompt (str): System-level instructions for the AI
        user_query (str): The user's query/message
        image_urls (List[str]): List of image URLs to analyze
        model_name (str): Gemini model name (default: gemini-2.5-flash)

    Returns:
        Dict[str, Any]: Parsed JSON response from the AI
    """
    try:
        # Initialize Gemini model
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_prompt
        )

        # Configure generation settings
        generation_config = genai.types.GenerationConfig(
            temperature=0.3,
            max_output_tokens=1200,
            response_mime_type="application/json"
        )

        # Prepare contents: include text + images
        contents = [
            {"role": "user", "parts": [{"text": user_query}]}
        ]

        # Add image URLs
        for url in image_urls:
            contents[0]["parts"].append({"image_url": url})

        # Generate response
        response = model.generate_content(
            contents,
            generation_config=generation_config
        )

        # Extract raw text response
        response_content = response.text.strip()

        # Try parsing JSON
        try:
            parsed_response = json.loads(response_content)
            return parsed_response
        except json.JSONDecodeError:
            return {
                "error": "Failed to parse JSON response",
                "raw_response": response_content
            }

    except Exception as e:
        return {"error": f"API call failed: {str(e)}"}


# 🔹 Example Usage
if __name__ == "__main__":
    system_prompt = "You are an assistant that analyzes images and provides structured JSON responses."
    user_query = "Describe the objects and environment in the given images."
    image_urls = [
        "https://example.com/sample1.jpg",
        "https://example.com/sample2.png"
    ]

    result = orchestrator_function_gemini_with_images(system_prompt, user_query, image_urls)
    print(json.dumps(result, indent=2))
