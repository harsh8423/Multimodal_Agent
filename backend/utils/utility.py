import inspect
import json
import asyncio
from typing import Any

from models.chat_openai import orchestrator_function as openai_chatmodel
from models.chat_gemini import orchestrator_function_gemini as gemini_chatmodel


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
    return raw