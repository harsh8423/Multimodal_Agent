import inspect
import json
import asyncio
from typing import Any

from models.chat_openai import orchestrator_function as openai_chatmodel
from models.chat_gemini import orchestrator_function_gemini as gemini_chatmodel
from models.chat_groq import orchestrator_function_groq as groq_chatmodel


async def _call_openai_chatmodel(system_prompt: str, user_query: str, model_name: str = "gpt-5-mini"):
    """
    Safely call openai_chatmodel:
      - if openai_chatmodel is async, await it
      - if it's sync, run it in a thread with asyncio.to_thread
    Returns the raw response (dict or string).
    """
    if inspect.iscoroutinefunction(openai_chatmodel):
        return await openai_chatmodel(system_prompt, user_query, model_name)
    # sync function -> run in background thread to avoid blocking event loop
    return await asyncio.to_thread(openai_chatmodel, system_prompt, user_query, model_name)


async def _call_gemini_chatmodel(system_prompt: str, user_query: str, model_name: str = "gemini-2.5-flash"):
    """
    Safely call gemini_chatmodel:
      - if gemini_chatmodel is async, await it
      - if it's sync, run it in a thread with asyncio.to_thread
    Returns the raw response (dict or string).
    """

    if inspect.iscoroutinefunction(gemini_chatmodel):
        return await gemini_chatmodel(system_prompt, user_query, model_name)
    # sync function -> run in background thread to avoid blocking event loop
    return await asyncio.to_thread(gemini_chatmodel, system_prompt, user_query, model_name)


async def _call_groq_chatmodel(system_prompt: str, user_query: str, model_name: str = "llama-3.1-70b-versatile"):
    """
    Safely call groq_chatmodel:
      - if groq_chatmodel is async, await it
      - if it's sync, run it in a thread with asyncio.to_thread
    Returns the raw response (dict or string).
    """
    if inspect.iscoroutinefunction(groq_chatmodel):
        return await groq_chatmodel(system_prompt, user_query, model_name)
    # sync function -> run in background thread to avoid blocking event loop
    return await asyncio.to_thread(groq_chatmodel, system_prompt, user_query, model_name)


async def _normalize_model_output(raw: Any) -> Any:
    """
    Normalize model output: if string and looks like JSON, parse it, otherwise return as-is.
    """
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        raw = raw.strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw
    if raw is None:
        return {"error": "API call failed: No response received"}
    return raw


async def chat_model_router(system_prompt: str, user_query: str, chat_llm_model: str, model_name: str) -> Any:
    """
    Functional chat model router that routes to different chat models based on chat_llm_model name.
    Includes fallback mechanism if primary model fails.
    
    Args:
        system_prompt (str): The system prompt that defines the AI's role and response format
        user_query (str): The user's query/message
        chat_llm_model (str): The chat model provider ("openai", "gemini", "groq")
        model_name (str): The specific model name to use
    
    Returns:
        Any: Raw response from the selected chat model
    """
    chat_llm_model = chat_llm_model.lower()
    
    # Try primary model first
    try:
        if chat_llm_model == "openai":
            result = await _call_gemini_chatmodel(system_prompt, user_query)
        elif chat_llm_model == "gemini":
            result = await _call_gemini_chatmodel(system_prompt, user_query)
        elif chat_llm_model == "groq":
            result = await _call_gemini_chatmodel(system_prompt, user_query)
        else:
            # Default fallback to Gemini if unknown model
            result = await _call_gemini_chatmodel(system_prompt, user_query)
        
        # Check if result indicates failure
        if isinstance(result, dict) and result.get("error"):
            print(f"Primary model ({chat_llm_model}) failed: {result.get('error')}")
            # Fallback to OpenAI
            print("Falling back to OpenAI...")
            return await _call_openai_chatmodel(system_prompt, user_query)
        
        return result
        
    except Exception as e:
        print(f"Primary model ({chat_llm_model}) exception: {str(e)}")
        # Fallback to OpenAI
        print("Falling back to OpenAI...")
        return await _call_openai_chatmodel(system_prompt, user_query)