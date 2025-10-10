# todo_planner.py
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


async def todo_planner(query: str, model_name: str = "gpt-5-mini",
                      registry_path: Optional[str] = None, session_context: Optional[SessionContext] = None,
                      max_iterations: int = 5, user_metadata: Optional[Dict] = None, 
                      user_image_path: Optional[str] = None) -> Any:
    """
    To-do Planner Agent - Specialized agent for creating and managing todo lists and content plans.
    
    Capabilities:
    - Create structured todo lists for complex multi-step tasks
    - Generate content plans for social media platforms
    - Break down complex workflows into manageable steps
    - Track progress and update task statuses
    - Provide efficient task prioritization and organization
    
    The agent focuses on:
    - Todo list creation and management
    - Content planning and structuring
    - Task breakdown and organization
    - Progress tracking and updates
    """
    
    # Log todo_planner start
    if session_context:
        await session_context.send_nano("todo_planner", "starting…")

    # Find registry path (default to project root file)
    if registry_path is None:
        registry_path = Path(__file__).parent.parent / DEFAULT_REGISTRY_FILENAME
    else:
        registry_path = Path(registry_path)

    # Get todo_planner memory context if available
    todo_planner_memory_context = ""
    chat_history_context = ""
    if session_context:
        todo_planner_memory = await session_context.get_agent_memory("todo_planner")
        todo_planner_memory_context = await todo_planner_memory.get_context_string()
        
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
                    elif role == "assistant" and agent == "todo_planner":
                        chat_history_parts.append(f"Assistant (todo_planner): {content}")
                
                if chat_history_parts:
                    chat_history_context = "Recent conversation:\n" + "\n".join(chat_history_parts)
        
        # Add current query to memory using new chat-scoped system
        memory_metadata = {"timestamp": None, "query_type": "todo_planning"}
        
        # Add user metadata to memory metadata if provided
        if user_metadata:
            memory_metadata["user_metadata"] = user_metadata
        if user_image_path:
            memory_metadata["image_path"] = user_image_path
        
        await session_context.append_and_persist_memory(
            "todo_planner",
            f"Todo planning query: {query}",
            memory_metadata
        )
        
        # Also save metadata separately for future reference
        if user_metadata:
            await session_context.append_and_persist_memory(
                "todo_planner",
                f"User metadata context: {json.dumps(user_metadata)}",
                {"context_type": "user_metadata", "timestamp": None}
            )
        if user_image_path:
            await session_context.append_and_persist_memory(
                "todo_planner",
                f"User provided image: {user_image_path}",
                {"context_type": "user_asset", "timestamp": None}
            )

    # Build system prompt for this agent (may raise if registry missing)
    system_prompt = build_system_prompt("todo_planner", str(registry_path),
                                        extra_instructions=f"Memory context: {todo_planner_memory_context}\n\nChat history: {chat_history_context}")
    
    # Add user_id information to the system prompt
    user_id = None
    if session_context:
        user_id = getattr(session_context, 'user_id', None)
    
    if user_id:
        system_prompt += f"\n\nUser ID: {user_id}"
    
    # Add user metadata to system prompt if available
    if user_metadata:
        system_prompt += f"\n\nUser metadata: {json.dumps(user_metadata)}"
    
    if user_image_path:
        system_prompt += f"\n\nUser provided image: {user_image_path}"

    print("=== TODO_PLANNER: Initial call to chat model ===")
    print(f"=== TODO_PLANNER: Query: {query} ===")
    print(f"=== TODO_PLANNER: System prompt length: {len(system_prompt)} ===")

    # Call the chat model with the query
    response = await _call_openai_chatmodel(
        system_prompt=system_prompt,
        user_query=query,
        model_name=model_name
    )

    print("=== TODO_PLANNER: Raw response from chat model ===")
    print(response)
    print("=== TODO_PLANNER: End raw response ===")

    # Normalize the response
    normalized = await _normalize_model_output(response)
    print("=== TODO_PLANNER: Normalized response ===")
    print(normalized)
    print("=== TODO_PLANNER: End normalized response ===")

    # Save the initial response to chat history
    if session_context and session_context.chat_id:
        await save_chat_message(
            chat_id=session_context.chat_id,
            role="assistant",
            content=normalized,
            agent="todo_planner"
        )

    print("=== TODO_PLANNER: Initial response saved to chat history ===")

    # Iterative multi-step execution until tool_required is false or iterations exhausted
    try:
        if isinstance(normalized, str):
            agent_state = json.loads(normalized)
        else:
            agent_state = normalized

        iteration = 0
        last_normalized: Any = normalized

        while True:
            needs_tool = bool(agent_state.get("tool_required", False)) if isinstance(agent_state, dict) else False
            print(f"=== TODO_PLANNER: Loop iteration {iteration}, needs_tool: {needs_tool} ===")
            print(f"=== TODO_PLANNER: agent_state: {agent_state} ===")

            if not needs_tool:
                print(f"=== TODO_PLANNER: No tool required, returning response ===")
                if session_context:
                    await session_context.append_and_persist_memory(
                        "todo_planner",
                        f"No tool required decision: Direct todo planning response",
                        {"phase": "decision", "decision_type": "no_tool", "query": query[:100]}
                    )
                    await session_context.append_and_persist_memory(
                        "todo_planner",
                        f"Direct response: {str(last_normalized)[:200]}...",
                        {"response_type": "direct", "used_tool": None}
                    )
                if isinstance(agent_state, dict):
                    print(f"=== TODO_PLANNER: Returning agent_state dict: {agent_state} ===")
                    print(f"=== TODO_PLANNER: FINAL RETURN TO SOCIAL MEDIA MANAGER: {agent_state} ===")
                    return agent_state
                
                print("=== TODO_PLANNER: direct response ===")
                print(last_normalized)
                print("=== TODO_PLANNER: end direct response ===")
                return {"text": str(last_normalized)}

            if iteration >= max_iterations:
                print(f"=== TODO_PLANNER: Max iterations reached ({max_iterations}) ===")
                if session_context:
                    await session_context.send_nano("todo_planner", "Max iterations reached")
                return {"text": f"Max iterations ({max_iterations}) reached in todo_planner"}

            # Handle tool execution
            tool_name = agent_state.get("tool_name", "").strip()
            input_schema_fields = agent_state.get("input_schema_fields", {})

            if not tool_name:
                print("=== TODO_PLANNER: Tool required but no tool_name provided ===")
                if session_context:
                    await session_context.send_nano("todo_planner", "Error: Tool required but no tool_name")
                return {"text": "Tool required but no tool_name provided", "error": True}

            # ALWAYS override user_id with actual value from session context
            if user_id and isinstance(input_schema_fields, dict):
                input_schema_fields["user_id"] = user_id
                print(f"🔧 TODO_PLANNER: Overriding user_id with actual value: {user_id}")
            
            # For todo tools, ALWAYS override chat_id with actual value from session context
            if tool_name in ["manage_todos", "create_todo_list", "update_todo_task_status", "get_next_todo_task", "add_todo_task", "get_chat_todos"]:
                chat_id = getattr(session_context, 'chat_id', None) if session_context else None
                
                if chat_id and isinstance(input_schema_fields, dict):
                    input_schema_fields["chat_id"] = chat_id
                    print(f"🔧 TODO_PLANNER: Overriding chat_id with actual value: {chat_id}")
                elif not chat_id:
                    print(f"⚠️ WARNING: No chat_id available in session_context for tool {tool_name}")
                    # Use a fallback chat_id to prevent errors
                    if isinstance(input_schema_fields, dict):
                        fallback_chat_id = f"fallback_{session_context.session_id if session_context else 'unknown'}"
                        input_schema_fields["chat_id"] = fallback_chat_id
                        print(f"🔧 TODO_PLANNER: Using fallback chat_id: {fallback_chat_id}")
                
                # Add agent name for todo tools
                if isinstance(input_schema_fields, dict) and "agent_name" not in input_schema_fields:
                    input_schema_fields["agent_name"] = "todo_planner"
            
            # Call the tool using tool_router
            try:
                print(f"=== TODO_PLANNER: Calling tool {tool_name} with params: {input_schema_fields} ===")
                tool_result = await tool_router(tool_name, input_schema_fields)
                print("=== TODO_PLANNER: tool_result ===")
                print(tool_result)
                print("=== TODO_PLANNER: end tool_result ===")
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
                print(f"=== TODO_PLANNER: RETURNING ERROR RESPONSE: {error_response} ===")
                return error_response

            # Handle todo creation success - send to frontend
            if tool_name == "manage_todos" and isinstance(tool_result, dict) and tool_result.get("success"):
                todo_data = tool_result.get("todo_data")
                if todo_data:
                    # Return response with todo data for frontend display
                    response_with_todo = {
                        "text": f"Created todo list: {todo_data.get('title', 'Untitled')}",
                        "tool_required": False,
                        "metadata": {
                            "todo_data": todo_data,
                            "message_type": "todo_created"
                        }
                    }
                    print(f"=== TODO_PLANNER: Returning todo creation response: {response_with_todo} ===")
                    return response_with_todo

            if session_context:
                await session_context.append_and_persist_memory(
                    "todo_planner",
                    f"Tool {tool_name} executed successfully",
                    {"phase": "tool_execution", "tool_name": tool_name, "success": True}
                )

            # Prepare the tool result for the next iteration
            tool_result_text = str(tool_result) if tool_result else "Tool executed successfully"
            
            # Call the chat model again with the tool result
            follow_up_response = await _call_openai_chatmodel(
                system_prompt=system_prompt,
                user_query=f"Previous response: {normalized}\n\nTool {tool_name} result: {tool_result_text}\n\nContinue processing.",
                model_name=model_name
            )

            print("=== TODO_PLANNER: Follow-up response from chat model ===")
            print(follow_up_response)
            print("=== TODO_PLANNER: End follow-up response ===")

            # Normalize the follow-up response
            last_normalized = await _normalize_model_output(follow_up_response)
            print("=== TODO_PLANNER: Normalized follow-up response ===")
            print(last_normalized)
            print("=== TODO_PLANNER: End normalized follow-up response ===")

            # Save the follow-up response to chat history
            if session_context and session_context.chat_id:
                await save_chat_message(
                    chat_id=session_context.chat_id,
                    role="assistant",
                    content=last_normalized,
                    agent="todo_planner"
                )

            # Parse the new agent state
            if isinstance(last_normalized, str):
                agent_state = json.loads(last_normalized)
            else:
                agent_state = last_normalized

            iteration += 1

    except json.JSONDecodeError as e:
        print(f"=== TODO_PLANNER: JSON decode error: {e} ===")
        if session_context:
            await session_context.send_nano("todo_planner", f"JSON decode error: {str(e)}", level="error")
        return {"text": f"JSON decode error: {str(e)}", "error": True}
    except Exception as e:
        print(f"=== TODO_PLANNER: Unexpected error: {e} ===")
        if session_context:
            await session_context.send_nano("todo_planner", f"Unexpected error: {str(e)}", level="error")
        return {"text": f"Unexpected error: {str(e)}", "error": True}

    print("=== TODO_PLANNER: Final return ===")
    
    # Check if we have a successful todo creation response to return
    if isinstance(last_normalized, dict) and last_normalized.get("tool_required") is False:
        # This might be a todo creation response, return it as-is
        return last_normalized
    
    return {"text": str(last_normalized)}