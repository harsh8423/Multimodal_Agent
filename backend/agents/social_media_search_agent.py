# social_media_search_agent.py
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


async def social_media_search_agent(query: str, model_name: str = "gpt-4o",
                                   registry_path: Optional[str] = None, session_context: Optional[SessionContext] = None,
                                   max_iterations: int = 5, user_metadata: Optional[Dict] = None, user_image_path: Optional[str] = None) -> Any:
    """
    Build social_media_search_agent system prompt from registry and call the chat model with the query.
    This agent specializes in social media search and media downloading using get_media and unified_search tools.
    """
    # Log social media search agent start
    if session_context:
        await session_context.send_nano("social_media_search_agent", "starting…")

    # find registry path (default to project root file)
    if registry_path is None:
        registry_path = Path(__file__).parent.parent / DEFAULT_REGISTRY_FILENAME
    else:
        registry_path = Path(registry_path)

    # Get social media search agent memory context if available
    social_media_memory_context = ""
    chat_history_context = ""
    if session_context:
        social_media_memory = await session_context.get_agent_memory("social_media_search_agent")
        social_media_memory_context = await social_media_memory.get_context_string()
        
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
                    elif role == "assistant" and agent == "social_media_search_agent":
                        chat_history_parts.append(f"Assistant (social_media_search_agent): {content}")
                
                if chat_history_parts:
                    chat_history_context = "Recent conversation:\n" + "\n".join(chat_history_parts)
        
        # Add current query to memory using new chat-scoped system
        memory_metadata = {"timestamp": None, "query_type": "social_media_search"}
        
        # Add user metadata to memory metadata if provided
        if user_metadata:
            memory_metadata["user_metadata"] = user_metadata
        if user_image_path:
            memory_metadata["image_path"] = user_image_path
        
        await session_context.append_and_persist_memory(
            "social_media_search_agent",
            f"Social media search query: {query}",
            memory_metadata
        )
        
        # Also save metadata separately for future reference
        if user_metadata:
            await session_context.append_and_persist_memory(
                "social_media_search_agent",
                f"User metadata context: {json.dumps(user_metadata)}",
                {"context_type": "user_metadata", "timestamp": None}
            )
        if user_image_path:
            await session_context.append_and_persist_memory(
                "social_media_search_agent",
                f"User provided image: {user_image_path}",
                {"context_type": "user_asset", "timestamp": None}
            )

    # Build system prompt for this agent (may raise if registry missing)
    system_prompt = build_system_prompt("social_media_search_agent", str(registry_path),
                                        extra_instructions="{place_holder}")
    
    # Add metadata context to query if provided
    enhanced_query = query
    if user_metadata and isinstance(user_metadata, dict):
        metadata_info = []
        for key, value in user_metadata.items():
            metadata_info.append(f"{key}: {value}")
        if metadata_info:
            enhanced_query = f"{query}\n\nAdditional metadata from user:\n" + "\n".join(metadata_info)
    
    if user_image_path:
        enhanced_query += f"\n\nUser provided image saved at: {user_image_path}"
    
    # Add memory context to system prompt if available
    if social_media_memory_context:
        system_prompt += f"\n\n{social_media_memory_context}"
    
    # Add chat history context to system prompt if available
    if chat_history_context:
        system_prompt += f"\n\n{chat_history_context}"

    print("=== Social Media Search Agent System Prompt ===")
    print(system_prompt)
    print("=== End System Prompt ===")

    # First call to the model to determine if tool is required
    if session_context:
        await session_context.send_nano("social_media_search_agent", "analyzing social media query…")
        # Save model call decision to memory
        await session_context.append_and_persist_memory(
            "social_media_search_agent",
            f"Model call decision: Analyzing query for tool requirements",
            {"phase": "analysis", "query": query[:100]}
        )
    
    raw = await _call_openai_chatmodel(system_prompt, enhanced_query, model_name)
    normalized = await _normalize_model_output(raw)

    if session_context:
        await session_context.send_nano("social_media_search_agent", "parsed response")
        # Save model response to memory
        await session_context.append_and_persist_memory(
            "social_media_search_agent",
            f"Model analysis response: {str(normalized)[:200]}...",
            {"phase": "analysis", "response_type": "model_analysis"}
        )

    print("=== Initial social_media_search_agent response ===")
    print(normalized)
    print("=== End initial response ===")

    try:
        # Parse the JSON response if it's a string, otherwise use as-is
        if isinstance(normalized, str):
            agent_response = json.loads(normalized)
        else:
            agent_response = normalized

        iteration = 0
        last_normalized: Any = normalized

        while True:
            # Validate agent response structure
            if not isinstance(agent_response, dict):
                print(f"Warning: Agent response is not a dict: {type(agent_response)}")
                return {"text": str(last_normalized)}
            
            needs_tool = bool(agent_response.get("tool_required", False))
            tool_name = agent_response.get("tool_name")
            
            # Check if we have a valid tool call
            if needs_tool and not tool_name:
                print("Warning: tool_required is True but no tool_name provided")
                return {"text": str(last_normalized)}

            if not needs_tool:
                # No tool required, return the current response
                if session_context:
                    # Add response to memory using new chat-scoped system
                    await session_context.append_and_persist_memory(
                        "social_media_search_agent",
                        f"Direct response (without tool): {str(last_normalized)[:200]}...",
                        {"response_type": "direct", "used_tool": None}
                    )
                return agent_response

            # Guard against infinite loops
            if iteration >= max_iterations:
                warning_msg = f"Max iterations ({max_iterations}) reached in social_media_search_agent; returning best-effort response."
                print(warning_msg)
                if session_context:
                    await session_context.send_nano("social_media_search_agent", "Max iterations reached: showing last message")
                return {"text": str(last_normalized)}

            input_schema_fields = agent_response.get("input_schema_fields", {})

            # Normalize input_schema_fields if list of objects was provided
            if isinstance(input_schema_fields, list):
                merged = {}
                for item in input_schema_fields:
                    if isinstance(item, dict):
                        merged.update(item)
                input_schema_fields = merged
            
            # Validate input_schema_fields
            if not isinstance(input_schema_fields, dict):
                print(f"Warning: input_schema_fields is not a dict: {type(input_schema_fields)}")
                return {"text": str(last_normalized)}

            # Log tool call
            if session_context:
                await session_context.send_nano("social_media_search_agent", f"tool → {tool_name}")
                # Save tool call decision to memory
                await session_context.append_and_persist_memory(
                    "social_media_search_agent",
                    f"Tool call decision: {tool_name} with parameters: {input_schema_fields}",
                    {"phase": "tool_call", "tool_name": tool_name, "parameters": input_schema_fields}
                )
                

            # Call the tool using tool_router
            tool_result = await tool_router(tool_name, input_schema_fields)

            # Log tool result
            if session_context:
                await session_context.send_nano("social_media_search_agent", f"tool ✓ {tool_name}")
                # Save tool result to memory
                await session_context.append_and_persist_memory(
                    "social_media_search_agent",
                    f"Tool {tool_name} result: {json.dumps(tool_result, indent=2)[:300]}...",
                    {"phase": "tool_result", "tool_name": tool_name, "success": True, "result_type": "tool_output"}
                )
                # Save tool call as message (chat scoped)
                if session_context.chat_id:
                    await save_chat_message(
                        chat_id=session_context.chat_id,
                        role="tool",
                        content=json.dumps(tool_result, indent=2),
                        agent="social_media_search_agent"
                    )
                

            # Add tool result to memory using new chat-scoped system
            if session_context:
                await session_context.append_and_persist_memory(
                    "social_media_search_agent",
                    f"Tool {tool_name} result: {json.dumps(tool_result, indent=2)[:200]}...",
                    {"tool_name": tool_name, "success": True}
                )

            # Create a follow-up query with the tool result
            follow_up_query = f"""
            Original query: {query}

            Tool used: {tool_name}
            Tool result: {json.dumps(tool_result, indent=2)}

            IMPORTANT: Analyze the tool result carefully. If the tool result contains the information needed to answer the original query, set tool_required to false and provide a comprehensive final response. Only set tool_required to true if you genuinely need to call another tool for additional information.

            Continue executing the plan using the planner. If more tool calls are needed, set tool_required true with the next tool and inputs. If finished, set tool_required false and provide final text.
            """

            # Call the model again with the tool result
            if session_context:
                await session_context.send_nano("social_media_search_agent", "Processing tool result")
                # Save follow-up model call to memory
                await session_context.append_and_persist_memory(
                    "social_media_search_agent",
                    f"Follow-up model call: Processing tool results for next step",
                    {"phase": "follow_up", "tool_name": tool_name, "query": query[:100]}
                )

            next_raw = await _call_openai_chatmodel(system_prompt, follow_up_query, model_name)
            next_normalized = await _normalize_model_output(next_raw)
            last_normalized = next_normalized

            if session_context:
                # Save follow-up model response to memory
                await session_context.append_and_persist_memory(
                    "social_media_search_agent",
                    f"Follow-up model response: {str(next_normalized)[:200]}...",
                    {"phase": "follow_up", "response_type": "model_iteration", "tool_name": tool_name}
                )

            print("=== Iteration social_media_search_agent response ===")
            print(next_normalized)
            print("=== End iteration response ===")

            # Prepare for next loop
            if isinstance(next_normalized, str):
                try:
                    agent_response = json.loads(next_normalized)
                except Exception:
                    agent_response = {"tool_required": False, "text": str(next_normalized)}
            else:
                agent_response = next_normalized

            iteration += 1
            
    except json.JSONDecodeError as e:
        error_msg = f"Error parsing agent response as JSON: {e}"
        print(error_msg)
        
        if session_context:
            await session_context.send_nano("social_media_search_agent", "Error parsing agent response as JSON")
        
        return normalized
    except Exception as e:
        error_msg = f"Error in social_media_search_agent: {e}"
        print(error_msg)
        
        if session_context:
            await session_context.send_nano("social_media_search_agent", "Error in social_media_search_agent")
        
        return normalized