
from typing import Any, Optional, Dict
from pathlib import Path
from utils.build_prompts import build_system_prompt
from utils.utility import _call_openai_chatmodel, _normalize_model_output, _call_gemini_chatmodel
from utils.tool_router import tool_router
from utils.session_memory import SessionContext
from utils.mongo_store import save_chat_message

DEFAULT_REGISTRY_FILENAME = "system_prompts.json"

async def asset_agent(query: str, model_name: str = "gpt-5-mini",
                      registry_path: Optional[str] = None, session_context: Optional[SessionContext] = None,
                      max_iterations: int = 5, user_id: Optional[str] = None, 
                      user_metadata: Optional[Dict] = None, user_image_path: Optional[str] = None) -> Any:
    """
    Asset agent for managing and retrieving user data including brands, competitors, scraped posts, and templates.
    Uses flexible function-based tools to handle various data retrieval and multi-task operations.
    """
    
    # Extract user_id from session context if not provided
    if not user_id and session_context:
        user_id = getattr(session_context, 'user_id', None)

    if registry_path is None:
        registry_path = Path(__file__).parent.parent / DEFAULT_REGISTRY_FILENAME
    else:
        registry_path = Path(registry_path)

    # Get asset agent memory context if available
    asset_memory_context = ""
    chat_history_context = ""
    if session_context:
        asset_memory = await session_context.get_agent_memory("asset_agent")
        asset_memory_context = await asset_memory.get_context_string()
        
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
                            import json as _json
                            parsed = _json.loads(content)
                            if isinstance(parsed, dict) and set(parsed.keys()) <= {"chat_id", "type"}:
                                continue
                    except Exception:
                        pass

                    if role == "user":
                        chat_history_parts.append(f"User: {content}")
                    elif role == "assistant" and agent == "asset_agent":
                        chat_history_parts.append(f"Assistant (asset_agent): {content}")
                
                if chat_history_parts:
                    chat_history_context = "Recent conversation:\n" + "\n".join(chat_history_parts)
        
        # Add current query to memory using new chat-scoped system
        memory_metadata = {"timestamp": None, "query_type": "asset"}
        
        # Add user metadata to memory metadata if provided
        if user_metadata:
            memory_metadata["user_metadata"] = user_metadata
        if user_image_path:
            memory_metadata["image_path"] = user_image_path
        
        await session_context.append_and_persist_memory(
            "asset_agent",
            f"Asset query: {query}",
            memory_metadata
        )
        
        # Also save metadata separately for future reference
        if user_metadata:
            await session_context.append_and_persist_memory(
                "asset_agent",
                f"User metadata context: {json.dumps(user_metadata)}",
                {"context_type": "user_metadata", "timestamp": None}
            )
        if user_image_path:
            await session_context.append_and_persist_memory(
                "asset_agent",
                f"User provided image: {user_image_path}",
                {"context_type": "user_asset", "timestamp": None}
            )

    system_prompt = build_system_prompt("asset_agent", str(registry_path),
                                        extra_instructions="{place_holder}")
    
    # Add user_id information to the system prompt
    if user_id:
        system_prompt += f"\n\nIMPORTANT: The current user_id is: {user_id}. Always use this exact user_id in all tool calls."
    
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
    
    # Add memory context to system prompt here: if available
    if asset_memory_context:
        system_prompt += f"\n\n{asset_memory_context}"
    
    # Add chat history context to system prompt if available
    if chat_history_context:
        system_prompt += f"\n\n{chat_history_context}"

    # Print system prompt as requested
    print(system_prompt)

    # Log model call
    if session_context:
        # Save model call decision to memory
        await session_context.append_and_persist_memory(
            "asset_agent",
            f"Model call decision: Processing asset query",
            {"phase": "analysis", "query": query[:100], "agent_type": "asset"}
        )

    raw = await _call_openai_chatmodel(system_prompt, enhanced_query, model_name)
    normalized = await _normalize_model_output(raw)

    # Log model response
    if session_context:
        # Save model response to memory
        await session_context.append_and_persist_memory(
            "asset_agent",
            f"Model analysis response: {str(normalized)[:200]}...",
            {"phase": "analysis", "response_type": "model_analysis", "agent_type": "asset"}
        )

    print("=== asset_agent initial response ===")
    print(normalized)
    print("=== end asset_agent initial response ===")

    # Iterative multi-step execution until tool_required is false or iterations exhausted
    try:
        if isinstance(normalized, str):
            agent_state = __import__("json").loads(normalized)
        else:
            agent_state = normalized

        iteration = 0
        last_normalized: Any = normalized

        while True:
            needs_tool = bool(agent_state.get("tool_required", False)) if isinstance(agent_state, dict) else False
            print(f"=== ASSET_AGENT: Loop iteration {iteration}, needs_tool: {needs_tool} ===")
            print(f"=== ASSET_AGENT: agent_state: {agent_state} ===")

            if not needs_tool:
                print(f"=== ASSET_AGENT: No tool required, returning response ===")
                if session_context:
                    await session_context.append_and_persist_memory(
                        "asset_agent",
                        f"No tool required decision: Direct asset response",
                        {"phase": "decision", "decision_type": "no_tool", "query": query[:100]}
                    )
                    await session_context.append_and_persist_memory(
                        "asset_agent",
                        f"Direct response: {str(last_normalized)[:200]}...",
                        {"response_type": "direct", "used_tool": None}
                    )
                if isinstance(agent_state, dict):
                    print(f"=== ASSET_AGENT: Returning agent_state dict: {agent_state} ===")
                    print(f"=== ASSET_AGENT: FINAL RETURN TO SOCIAL MEDIA MANAGER: {agent_state} ===")
                    return agent_state
                
                print("=== ASSET_AGENT: direct response ===")
                print(last_normalized)
                print("=== ASSET_AGENT: end direct response ===")
                return {"text": str(last_normalized)}

            if iteration >= max_iterations:
                warning_msg = f"Max iterations ({max_iterations}) reached in asset_agent; returning best-effort response."
                print(warning_msg)
                if session_context:
                    await session_context.send_nano("warning", warning_msg, level="warning")
                return {"text": str(last_normalized)}

            tool_name = agent_state.get("tool_name")
            input_schema_fields = agent_state.get("input_schema_fields", {})

            if isinstance(input_schema_fields, list):
                merged = {}
                for item in input_schema_fields:
                    if isinstance(item, dict):
                        merged.update(item)
                input_schema_fields = merged

            # Log tool call
            if session_context:
                await session_context.send_nano("tool_call", f"Calling tool: {tool_name}")
                await session_context.append_and_persist_memory(
                    "asset_agent",
                    f"Tool call decision: {tool_name} with parameters: {input_schema_fields}",
                    {"phase": "tool_call", "tool_name": tool_name, "parameters": input_schema_fields}
                )

            # ALWAYS override user_id with actual value from session context
            if user_id and isinstance(input_schema_fields, dict):
                input_schema_fields["user_id"] = user_id
                print(f"🔧 ASSET_AGENT: Overriding user_id with actual value: {user_id}")
            
            # Call the tool using tool_router
            try:
                print(f"=== ASSET_AGENT: Calling tool {tool_name} with params: {input_schema_fields} ===")
                tool_result = await tool_router(tool_name, input_schema_fields)
                print("=== ASSET_AGENT: tool_result ===")
                print(tool_result)
                print("=== ASSET_AGENT: end tool_result ===")
            except Exception as tool_error:
                # If tool fails, return error response instead of continuing loop
                error_response = {
                    "text": f"Error executing tool {tool_name}: {str(tool_error)}",
                    "tool_required": False,
                    "error": True
                }
                if session_context:
                    await session_context.send_nano("tool_error", f"Tool {tool_name} failed: {str(tool_error)}", level="error")
                return error_response

            # Check if tool returned an error
            if isinstance(tool_result, dict) and tool_result.get("success") is False:
                # Tool returned an error, stop the loop and return the error
                error_response = {
                    "text": f"Tool {tool_name} returned an error: {tool_result.get('error', 'Unknown error')}",
                    "tool_required": False,
                    "error": True
                }
                if session_context:
                    await session_context.send_nano("tool_error", f"Tool {tool_name} returned error: {tool_result.get('error')}", level="error")
                print(f"=== ASSET_AGENT: RETURNING ERROR RESPONSE: {error_response} ===")
                return error_response

            if session_context:
                await session_context.send_nano("tool_result", f"Tool {tool_name} completed successfully")
                
                # Create JSON serializable version of tool_result
                def json_serializable(obj):
                    if hasattr(obj, 'isoformat'):  # datetime objects
                        return obj.isoformat()
                    elif hasattr(obj, '__dict__'):
                        return str(obj)
                    else:
                        return str(obj)
                
                try:
                    tool_result_json = __import__('json').dumps(tool_result, indent=2, default=json_serializable)
                except Exception as json_error:
                    print(f"=== ASSET_AGENT: JSON serialization error: {json_error}, using string representation ===")
                    tool_result_json = str(tool_result)
                
                await session_context.append_and_persist_memory(
                    "asset_agent",
                    f"Tool {tool_name} result: {tool_result_json[:300]}...",
                    {"phase": "tool_result", "tool_name": tool_name, "success": True, "result_type": "tool_output"}
                )
                if session_context.chat_id:
                    await save_chat_message(
                        chat_id=session_context.chat_id,
                        role="tool",
                        content=tool_result_json,
                        agent="asset_agent"
                    )

            # Ask model for the next step
            # Create JSON serializable version for the follow-up query
            try:
                tool_result_for_query = __import__('json').dumps(tool_result, indent=2, default=json_serializable)
            except Exception:
                tool_result_for_query = str(tool_result)
                
            follow_up_query = f"""
            Original asset query: {query}

            Tool used: {tool_name}
            Tool result: {tool_result_for_query}

            CRITICAL INSTRUCTION: If the tool has been executed successfully and contains the result, you MUST now:
            1. Set tool_required to FALSE
            2. Provide a comprehensive final response in the 'text' field that directly answers the user's query
            3. Update the planner step status to 'completed'
            4. Do NOT call any more tools
"""

            print(f"=== ASSET_AGENT: Follow-up query: {follow_up_query} ===")

            if session_context:
                await session_context.send_nano("model_call", "Asset agent processing tool result")
                await session_context.append_and_persist_memory(
                    "asset_agent",
                    f"Follow-up model call: Processing tool results for next step",
                    {"phase": "follow_up", "tool_name": tool_name, "query": query[:100]}
                )

            print(f"=== ASSET_AGENT: Calling follow-up model with query: {follow_up_query[:200]}... ===")
            try:
                next_raw = await _call_openai_chatmodel(system_prompt, follow_up_query, model_name)
                print(f"=== ASSET_AGENT: Raw model response: {next_raw} ===")
            except Exception as model_error:
                print(f"=== ASSET_AGENT: MODEL CALL ERROR: {model_error} ===")
                raise model_error
                
            try:
                next_normalized = await _normalize_model_output(next_raw)
                print(f"=== ASSET_AGENT: Normalized model response: {next_normalized} ===")
            except Exception as normalize_error:
                print(f"=== ASSET_AGENT: NORMALIZE ERROR: {normalize_error} ===")
                raise normalize_error
                
            last_normalized = next_normalized

            if session_context:
                await session_context.append_and_persist_memory(
                    "asset_agent",
                    f"Follow-up model response: {str(next_normalized)[:200]}...",
                    {"phase": "follow_up", "response_type": "model_iteration", "tool_name": tool_name}
                )


            if isinstance(next_normalized, str):
                try:
                    agent_state = __import__("json").loads(next_normalized)
                    print(f"=== ASSET_AGENT: Successfully parsed JSON agent_state: {agent_state} ===")
                except Exception as parse_error:
                    print(f"=== ASSET_AGENT: JSON parse failed: {parse_error}, using fallback ===")
                    agent_state = {"tool_required": False, "text": str(next_normalized)}
            else:
                agent_state = next_normalized

      
            iteration += 1
    except Exception as e:
        # Fall back to returning the first normalized response
        print(f"=== ASSET_AGENT: EXCEPTION OCCURRED: {type(e).__name__}: {str(e)} ===")
        import traceback
        print(f"=== ASSET_AGENT: EXCEPTION TRACEBACK: ===")
        traceback.print_exc()
        print(f"=== ASSET_AGENT: END TRACEBACK ===")
        
        if session_context:
            await session_context.send_nano("error", f"Asset agent loop error: {e}", level="error")
        print(f"=== ASSET_AGENT: EXCEPTION FALLBACK RETURN: {normalized} ===")
        return normalized