import google.generativeai as genai
import json
import os
import requests
import base64
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def analyze_image(
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
            max_output_tokens=4000,  # Increased token limit
            response_mime_type="application/json"
        )

        # Prepare contents: include text + images
        parts = [{"text": user_query}]
        
        # Add image URLs by fetching and encoding them
        for url in image_urls:
            try:
                # Fetch the image from URL
                response = requests.get(url)
                response.raise_for_status()
                
                # Encode the image data as base64
                image_data = base64.b64encode(response.content).decode('utf-8')
                
                # Determine MIME type from content type or URL
                content_type = response.headers.get('content-type', 'image/jpeg')
                if 'image/' not in content_type:
                    content_type = 'image/jpeg'  # Default fallback
                
                parts.append({
                    "inline_data": {
                        "mime_type": content_type,
                        "data": image_data
                    }
                })
            except Exception as e:
                return {"error": f"Failed to fetch image from {url}: {str(e)}"}
        
        contents = [{"role": "user", "parts": parts}]

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
                parsed_response = json.loads(cleaned_content)
                return parsed_response
                
            except json.JSONDecodeError:
                # If still can't parse, return the raw response with error info
                return {
                    "error": "Failed to parse JSON response - response may be truncated",
                    "raw_response": response_content[:1000] + "..." if len(response_content) > 1000 else response_content,
                    "json_error": str(e)
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

    result = analyze_image(system_prompt, user_query, image_urls)
    print(json.dumps(result, indent=2))
