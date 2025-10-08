# NEW SDK
from google import genai
from google.genai import types
import json
import os
from typing import Dict, Any, Optional

from dotenv import load_dotenv

load_dotenv()

# Create a global client (API key is automatically detected from environment)
client = genai.Client()

def orchestrator_function_gemini(system_prompt: str, user_query: str, model_name: str = "gemini-2.5-flash") -> Dict[str, Any]:
    """
    Function to interact with Gemini API and get structured responses.
    
    Args:
        system_prompt (str): The system prompt that defines the AI's role and response format
        user_query (str): The user's query/message
        model_name (str): Gemini model to use (default: gemini-2.5-flash)
                         Options: gemini-2.5-flash, gemini-2.5-pro, gemini-2.0-pro
    
    Returns:
        Dict[str, Any]: Parsed JSON response from the AI
    """
    try:
        # Configure generation parameters
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.3,  # Lower temperature for more consistent structured responses
            max_output_tokens=1000,
            response_mime_type="application/json"  # This helps ensure JSON response
        )
        
        # Generate response using the new SDK
        response = client.models.generate_content(
            model=model_name,
            config=config,
            contents=user_query
        )
        
        # Extract the response content
        response_content = response.text.strip()
        
        # Try to parse the JSON response
        try:
            parsed_response = json.loads(response_content)
            return parsed_response
        except json.JSONDecodeError:
            # If JSON parsing fails, return error with raw content
            return {
                "error": "Failed to parse JSON response",
                "raw_response": response_content
            }
            
    except Exception as e:
        return {
            "error": f"API call failed: {str(e)}"
        }

