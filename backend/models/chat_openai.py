from openai import OpenAI
import json
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()



# Initialize OpenAI client
# You can set the API key via environment variable OPENAI_API_KEY
# or pass it directly: client = OpenAI(api_key="your-api-key-here")
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def orchestrator_function(system_prompt: str, user_query: str, model_name: str = "gpt-5-mini") -> Dict[str, Any]:
    """
    Function to interact with OpenAI API and get structured responses.
    
    Args:
        system_prompt (str): The system prompt that defines the AI's role and response format
        user_query (str): The user's query/message
        model_name (str): OpenAI model to use (default: gpt-5-mini)
    
    Returns:
        Dict[str, Any]: Parsed JSON response from the AI
    """
    try:
        # Create the chat completion request using the new API
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
        )
        
        # Extract the response content
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
