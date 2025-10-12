from groq import Groq
import json
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Groq client
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

def orchestrator_function_groq(system_prompt: str, user_query: str, model_name: str = "llama-3.1-8b-instant") -> Dict[str, Any]:
    """
    Function to interact with Groq API and get structured responses.
    
    Args:
        system_prompt (str): The system prompt that defines the AI's role and response format
        user_query (str): The user's query/message
        model_name (str): Groq model to use (default: llama-3.1-70b-versatile)
                         Options: llama-3.1-70b-versatile, llama-3.1-8b-instant, mixtral-8x7b-32768, gemma2-9b-it
    
    Returns:
        Dict[str, Any]: Parsed JSON response from the AI
    """
    if not groq_client:
        return {
            "error": "Groq API key not found. Please set GROQ_API_KEY environment variable."
        }
    
    try:
        # Create the chat completion request
        # Ensure the system prompt includes JSON requirement for structured response
        enhanced_system_prompt = f"{system_prompt}\n\nIMPORTANT: You must respond with valid JSON format only. Do not include any text outside the JSON structure."
        
        response = groq_client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": enhanced_system_prompt},
                {"role": "user", "content": f"Please respond in JSON format: {user_query}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,  # Lower temperature for more consistent structured responses
        )
        
        # Extract the response content
        if response.choices[0].message.content is None:
            return {
                "error": "API call failed: No response content received from Groq"
            }
        response_content = response.choices[0].message.content.strip()
        
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