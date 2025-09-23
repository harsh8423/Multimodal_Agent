"""
Chat Title Generation Utility

Generates meaningful chat titles from user messages using AI models.
"""

import asyncio
import logging
from typing import Optional
from models.chat_gemini import orchestrator_function_gemini

logger = logging.getLogger(__name__)


async def generate_chat_title(user_message: str, model_name: str = "gemini-2.5-flash") -> str:
    """
    Generate a concise chat title (3-5 words) from the user's first message.
    
    Args:
        user_message: The user's message content
        model_name: The model to use for title generation
        
    Returns:
        A concise title (4-8 words) or "New Chat" if generation fails
    """
    if not user_message or not user_message.strip():
        return "New Chat"
    
    # Clean the message for title generation
    clean_message = user_message.strip()
    if len(clean_message) > 200:
        clean_message = clean_message[:200] + "..."
    
    # First try to use AI model if API key is available
    try:
        print(f"[title-generator] Generating title for message: '{clean_message[:50]}...'")
        # Use the synchronous orchestrator_function_gemini in an async context
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            orchestrator_function_gemini,
            "Generate a 4-8 word title for this message",
            f"User message: {clean_message}",
            model_name
        )
        print(f"[title-generator] Received response: {response}")
        
        if response and "error" not in response:
            # Handle different response types
            if isinstance(response, str):
                # Direct string response
                title = response.strip()
                print(f"[title-generator] Using direct string response: '{title}'")
            elif isinstance(response, dict):
                # Dictionary response
                if "raw_response" in response:
                    title = response["raw_response"].strip()
                    print(f"[title-generator] Using raw_response: '{title}'")
                else:
                    # If it's a parsed JSON response, look for common fields
                    title = response.get("title") or response.get("text") or response.get("content") or str(response).strip()
                    print(f"[title-generator] Using parsed response: '{title}'")
            else:
                # Fallback for other types
                title = str(response).strip()
                print(f"[title-generator] Using string conversion: '{title}'")
            
            # Clean up the title
            title = title.replace('"', '').replace("'", "").strip()
            print(f"[title-generator] Cleaned title: '{title}'")
            
            # Ensure it's not too long (split and take first few words)
            words = title.split()
            if len(words) > 8:
                title = " ".join(words[:5])
                print(f"[title-generator] Truncated title: '{title}'")
            
            # Ensure it's not empty or too short
            if len(title) < 4:
                print(f"[title-generator] Title too short, using fallback")
                return generate_fallback_title(clean_message)
            
            print(f"[title-generator] Final title: '{title}'")
            return title
        else:
            logger.warning(f"Error in title generation response: {response}")
            print(f"[title-generator] Error response, using fallback")
            return generate_fallback_title(clean_message)
            
    except Exception as e:
        logger.error(f"Failed to generate chat title with AI: {e}")
        print(f"[title-generator] AI generation failed, using fallback: {e}")
        return generate_fallback_title(clean_message)


def generate_fallback_title(message: str) -> str:
    """
    Generate a simple title from the message without using AI.
    This is a fallback when AI is not available.
    """
    print(f"[title-generator] Using fallback title generation for: '{message[:50]}...'")
    
    # Simple keyword-based title generation
    message_lower = message.lower()
    
    # Common patterns
    if any(word in message_lower for word in ['hello', 'hi', 'hey', 'greeting']):
        return "Greeting"
    elif any(word in message_lower for word in ['help', 'assist', 'support']):
        return "Help Request"
    elif any(word in message_lower for word in ['how', 'what', 'why', 'when', 'where']):
        return "Question"
    elif any(word in message_lower for word in ['cook', 'recipe', 'food', 'cooking']):
        return "Cooking Help"
    elif any(word in message_lower for word in ['weather', 'temperature', 'rain', 'sunny']):
        return "Weather Query"
    elif any(word in message_lower for word in ['resume', 'cv', 'job', 'career']):
        return "Career Help"
    elif any(word in message_lower for word in ['book', 'flight', 'travel', 'trip']):
        return "Travel Planning"
    elif any(word in message_lower for word in ['explain', 'understand', 'learn', 'teach']):
        return "Learning Request"
    elif any(word in message_lower for word in ['write', 'create', 'make', 'build']):
        return "Creation Help"
    elif any(word in message_lower for word in ['search', 'find', 'look', 'research']):
        return "Search Request"
    else:
        # Take first few words and capitalize
        words = message.split()[:3]
        if words:
            title = " ".join(word.capitalize() for word in words)
            return title if len(title) > 2 else "New Chat"
        else:
            return "New Chat"


async def generate_chat_title_sync(user_message: str, model_name: str = "gemini-2.5-flash") -> str:
    """
    Synchronous wrapper for title generation.
    """
    try:
        return await generate_chat_title(user_message, model_name)
    except Exception as e:
        logger.error(f"Sync title generation failed: {e}")
        return "New Chat"