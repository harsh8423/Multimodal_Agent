# media_analyst.py
import asyncio
import inspect
import json
from pathlib import Path
from typing import Any, Dict, Optional
from utils.build_prompts import build_system_prompt

from utils.utility import _call_openai_chatmodel, _normalize_model_output
from utils.tool_router import tool_router
from utils.session_memory import SessionContext
from utils.mongo_store import save_chat_message

DEFAULT_REGISTRY_FILENAME = "system_prompts.json"


async def media_analyst(query: str, model_name: str = "gpt-4o",
                        registry_path: Optional[str] = None, session_context: Optional[SessionContext] = None) -> Any:
    """
    Build media_analyst system prompt from registry and call the chat model with the query.
    This agent performs direct analysis without multi-step operations or rechecking messages.
    """
    # Log media analyst start
    if session_context:
        await session_context.send_nano("media_analyst", "starting…")

    # find registry path (default to project root file)
    if registry_path is None:
        registry_path = Path(__file__).parent.parent / DEFAULT_REGISTRY_FILENAME
    else:
        registry_path = Path(registry_path)

    # Get media analyst memory context if available
    media_memory_context = ""
    chat_history_context = ""
    if session_context:
        media_memory = await session_context.get_agent_memory("media_analyst")
        media_memory_context = await media_memory.get_context_string()
        
        # Get chat conversation history
        if session_context.chat_id:
            from utils.mongo_store import get_chat_messages
            chat_messages = await get_chat_messages(session_context.chat_id, limit=20)
            if chat_messages:
                chat_history_parts = []
                for msg in chat_messages[-10:]:  # Last 10 messages
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    agent = msg.get("agent", "")
                    timestamp = msg.get("timestamp", "")
                    
                    # Skip old control frames accidentally stored as user content (e.g., chat_id-only)
                    try:
                        if isinstance(content, str) and content.strip().startswith("{"):
                            parsed = json.loads(content)
                            if isinstance(parsed, dict) and set(parsed.keys()) <= {"chat_id", "type"}:
                                continue
                    except Exception:
                        pass

                    if role == "user":
                        chat_history_parts.append(f"User: {content}")
                    elif role == "assistant" and agent == "media_analyst":
                        chat_history_parts.append(f"Assistant (media_analyst): {content}")
                
                if chat_history_parts:
                    chat_history_context = "Recent conversation:\n" + "\n".join(chat_history_parts)
        
        # Add current query to memory using new chat-scoped system
        await session_context.append_and_persist_memory(
            "media_analyst",
            f"Media analysis query: {query}",
            {"timestamp": None, "query_type": "media_analysis"}
        )

    # Build system prompt for this agent (may raise if registry missing)
    system_prompt = build_system_prompt("media_analyst", str(registry_path),
                                        extra_instructions="{place_holder}")
    
    # Add memory context to system prompt if available
    if media_memory_context:
        system_prompt += f"\n\n{media_memory_context}"
    
    # Add chat history context to system prompt if available
    if chat_history_context:
        system_prompt += f"\n\n{chat_history_context}"

    print("=== Media Analyst System Prompt ===")
    print(system_prompt)
    print("=== End System Prompt ===")

    # Call the model to determine if tool is required
    if session_context:
        await session_context.send_nano("media_analyst", "analyzing media…")
        # Save model call decision to memory
        await session_context.append_and_persist_memory(
            "media_analyst",
            f"Model call decision: Analyzing media query for tool requirements",
            {"phase": "analysis", "query": query[:100]}
        )
    
    raw = await _call_openai_chatmodel(system_prompt, query, model_name)
    normalized = await _normalize_model_output(raw)

    if session_context:
        await session_context.send_nano("media_analyst", "parsed response")
        # Save model response to memory
        await session_context.append_and_persist_memory(
            "media_analyst",
            f"Model analysis response: {str(normalized)[:200]}...",
            {"phase": "analysis", "response_type": "model_analysis"}
        )

    print("=== Media Analyst response ===")
    print(normalized)
    print("=== End response ===")

    try:
        # Parse the JSON response if it's a string, otherwise use as-is
        if isinstance(normalized, str):
            agent_response = json.loads(normalized)
        else:
            agent_response = normalized

        needs_tool = bool(agent_response.get("tool_required", False)) if isinstance(agent_response, dict) else False

        if not needs_tool:
            # No tool required, return the current response directly
            if session_context:
                # Add response to memory using new chat-scoped system
                await session_context.append_and_persist_memory(
                    "media_analyst",
                    f"Direct response (without tool): {str(normalized)[:200]}...",
                    {"response_type": "direct", "used_tool": None}
                )
            if isinstance(agent_response, dict):
                return agent_response
            return {"text": str(normalized)}

        # Tool is required - call it once and return the result directly
        tool_name = agent_response.get("tool_name")
        input_schema_fields = agent_response.get("input_schema_fields", {})

        # Normalize input_schema_fields if list of objects was provided
        if isinstance(input_schema_fields, list):
            merged = {}
            for item in input_schema_fields:
                if isinstance(item, dict):
                    merged.update(item)
            input_schema_fields = merged

        # Log tool call
        if session_context:
            await session_context.send_nano("media_analyst", f"tool → {tool_name}")
            # Save tool call decision to memory
            await session_context.append_and_persist_memory(
                "media_analyst",
                f"Tool call decision: {tool_name} with parameters: {input_schema_fields}",
                {"phase": "tool_call", "tool_name": tool_name, "parameters": input_schema_fields}
            )

        # Call the tool using tool_router
        tool_result = tool_router(tool_name, input_schema_fields)

        # Log tool result
        if session_context:
            await session_context.send_nano("media_analyst", f"tool ✓ {tool_name}")
            # Save tool result to memory
            await session_context.append_and_persist_memory(
                "media_analyst",
                f"Tool {tool_name} result: {json.dumps(tool_result, indent=2)[:300]}...",
                {"phase": "tool_result", "tool_name": tool_name, "success": True, "result_type": "tool_output"}
            )
            # Save tool call as message (chat scoped)
            if session_context.chat_id:
                await save_chat_message(
                    chat_id=session_context.chat_id,
                    role="tool",
                    content=json.dumps(tool_result, indent=2),
                    agent="media_analyst"
                )

        # Return the tool result directly without further processing
        if session_context:
            await session_context.append_and_persist_memory(
                "media_analyst",
                f"Final tool result: {json.dumps(tool_result, indent=2)[:200]}...",
                {"tool_name": tool_name, "success": True, "final_result": True}
            )

        # Return the tool result as the final response
        return tool_result
            
    except json.JSONDecodeError as e:
        error_msg = f"Error parsing agent response as JSON: {e}"
        print(error_msg)
        
        if session_context:
            await session_context.send_nano("media_analyst", "Error parsing agent response as JSON")
        
        return normalized
    except Exception as e:
        error_msg = f"Error in media_analyst: {e}"
        print(error_msg)
        
        if session_context:
            await session_context.send_nano("media_analyst", "Error in media_analyst")
        
        return normalized
