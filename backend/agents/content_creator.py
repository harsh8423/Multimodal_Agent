"""
Content Creator Agent - A powerful master agent for social media content creation

This agent specializes in creating engaging content for Instagram, LinkedIn, and YouTube.
It can orchestrate other agents when needed while handling content creation tasks itself.
Follows the same patterns as orchestrator and research_agent for robustness.
"""

import asyncio
import inspect
import json
from typing import Any, Dict, Optional
from pathlib import Path

# Import the build_prompts function and chat model
from utils.build_prompts import build_system_prompt
from models.chat_openai import orchestrator_function as openai_chatmodel
from utils.utility import _call_openai_chatmodel, _normalize_model_output
from utils.tool_router import tool_router
from utils.session_memory import SessionContext
from utils.mongo_store import save_chat_message

# Dynamic import for agent orchestration to avoid circular dependencies
# from utils.router import call_agent  # Will import when needed

DEFAULT_REGISTRY_FILENAME = "system_prompts.json"

async def _maybe_await(value):
    """
    Await `value` if it is awaitable; otherwise return it.
    This is an async function so callers should `await _maybe_await(...)`.
    """
    if inspect.isawaitable(value):
        return await value
    return value

async def content_creator(
    query: str,
    model_name: str = "gpt-4o-mini",
    registry_path: Optional[str] = None,
    session_context: Optional[SessionContext] = None,
    max_iterations: int = 8,
    user_id: Optional[str] = None,
    user_metadata: Optional[Dict] = None,
    user_image_path: Optional[str] = None,
    **kwargs
) -> Any:
    """
    Content Creator Agent - Master agent for social media content creation
    
    Capabilities:
    - Creates content for Instagram, LinkedIn, and YouTube
    - Handles carousel posts, single images, videos, shorts, reels, text posts
    - Orchestrates other agents (asset_agent, media_analyst, social_media_search_agent) when needed
    - Uses registered tools for content research and analysis
    - Acts as an experienced social media content creator with comprehensive knowledge
    
    Agent Architecture:
    - Can orchestrate other agents (agent_required: true)
    - Can use registered tools (tool_required: true)
    - Never both agent_required and tool_required can be true simultaneously
    - Process continues until neither is required or max_iterations reached
    """
    
    # Log content creator start
    if session_context:
        await session_context.send_nano("content_creator", "starting…")

    # Extract user_id from session context if not provided
    if not user_id and session_context:
        user_id = getattr(session_context, 'user_id', None)

    # Find registry path (default to project root file)
    if registry_path is None:
        registry_path = Path(__file__).parent.parent / DEFAULT_REGISTRY_FILENAME
    else:
        registry_path = Path(registry_path)

    # Get content creator memory context if available
    creator_memory_context = ""
    chat_history_context = ""
    if session_context:
        creator_memory = await session_context.get_agent_memory("content_creator")
        creator_memory_context = await creator_memory.get_context_string()
        
        # Get chat conversation history
        if session_context.chat_id:
            from utils.mongo_store import get_chat_messages
            chat_messages = await get_chat_messages(session_context.chat_id, limit=20)
            if chat_messages:
                chat_history_parts = []
                for msg in chat_messages[-10:]:
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    agent = msg.get("agent", "")
                    timestamp = msg.get("timestamp", "")

                    # Skip old control frames accidentally stored as user content
                    try:
                        if isinstance(content, str) and content.strip().startswith("{"):
                            parsed = json.loads(content)
                            if isinstance(parsed, dict) and set(parsed.keys()) <= {"chat_id", "type"}:
                                continue
                    except Exception:
                        pass

                    if role == "user":
                        chat_history_parts.append(f"User: {content}")
                    elif role == "assistant" and agent == "content_creator":
                        chat_history_parts.append(f"Assistant (content_creator): {content}")
                
                if chat_history_parts:
                    chat_history_context = "Recent conversation:\n" + "\n".join(chat_history_parts)
        
        # Add current query to memory
        memory_metadata = {"timestamp": None, "query_type": "content_creation"}
        
        # Add user metadata to memory metadata if provided
        if user_metadata:
            memory_metadata["user_metadata"] = user_metadata
        if user_image_path:
            memory_metadata["image_path"] = user_image_path
        
        await session_context.append_and_persist_memory(
            "content_creator",
            f"Content Creator query: {query}",
            memory_metadata
        )
        
        # Also save metadata separately for future reference
        if user_metadata:
            await session_context.append_and_persist_memory(
                "content_creator",
                f"User metadata context: {json.dumps(user_metadata)}",
                {"context_type": "user_metadata", "timestamp": None}
            )
        if user_image_path:
            await session_context.append_and_persist_memory(
                "content_creator",
                f"User provided image: {user_image_path}",
                {"context_type": "user_asset", "timestamp": None}
            )

    # Build comprehensive system prompt for content creation
    system_prompt = build_system_prompt("content_creator", str(registry_path), 
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
    
    # Add memory context to system prompt if available
    if creator_memory_context:
        system_prompt += f"\n\n{creator_memory_context}"
    
    # Add chat history context to system prompt if available
    if chat_history_context:
        system_prompt += f"\n\n{chat_history_context}"
    
    # Add follow-up response handling instructions
    system_prompt += f"""

IMPORTANT: When you receive a user response to a follow-up question, you MUST:
1. Parse the user's response and incorporate it into your content creation process
2. Continue with the content creation workflow using the user's input
3. Complete the full content creation task without returning control to the orchestrator
4. Provide the final content creation result directly to the user
5. Set agent_required to FALSE when you have completed the content creation task

CRITICAL APPROVAL HANDLING:
- If the user approves your final response, return it with agent_required=FALSE
- If the user requests changes, modify your response accordingly and ask for approval again
- If the user cancels, return a cancellation message with agent_required=FALSE
- Always ask for approval before returning any final response to the orchestrator

Do NOT return control to the orchestrator until you have fully completed the content creation task."""

    print("=== Content Creator System Prompt ===")
    print(system_prompt)
    print("=== End System Prompt ===")

    # First call to the model to determine if agent/tool is required
    if session_context:
        await session_context.send_nano("content_creator", "thinking…")
        await session_context.append_and_persist_memory(
            "content_creator",
            f"Model call decision: Analyzing query for agent/tool requirements",
            {"phase": "analysis", "query": query[:100], "agent_type": "content_creator"}
        )

    raw = await _call_openai_chatmodel(system_prompt, enhanced_query, model_name)
    raw = await _maybe_await(raw)
    normalized = await _normalize_model_output(raw)

    if session_context:
        await session_context.send_nano("content_creator", "parsed response")
        await session_context.append_and_persist_memory(
            "content_creator",
            f"Model analysis response: {str(normalized)[:200]}...",
            {"phase": "analysis", "response_type": "model_analysis", "agent_type": "content_creator"}
        )

    print("=== Initial content_creator response ===")
    print(normalized)
    print("=== End initial response ===")

    try:
        # Parse the JSON response if it's a string, otherwise use as-is
        if isinstance(normalized, str):
            agent_state = json.loads(normalized)
        else:
            agent_state = normalized
        
        # Check if this is a user response to an approval request
        if isinstance(agent_state, dict) and agent_state.get("awaiting_user_followup"):
            # This is a response to a follow-up question, process it
            print(f"=== CONTENT_CONTENT_CREATOR: Processing user follow-up response ===")
            
            # Add context about the user's response to the query
            user_response_query = f"""
            Original content creation query: {query}
            
            User's response to your follow-up question: {enhanced_query}
            
            CRITICAL INSTRUCTIONS:
            1. Parse the user's response and incorporate it into your content creation process
            2. If the user approved your response, return it with agent_required=FALSE
            3. If the user requested changes, modify your response accordingly and ask for approval again
            4. If the user cancelled, return a cancellation message with agent_required=FALSE
            5. Always ask for approval before returning any final response to the orchestrator
            """
            
            # Process the user's response
            if session_context:
                await session_context.send_nano("content_creator", "processing user response")
                await session_context.append_and_persist_memory(
                    "content_creator",
                    f"User follow-up response: {user_response_query[:200]}...",
                    {"phase": "user_response", "response_type": "follow_up"}
                )
            
            # Call the model again with the user's response
            follow_up_raw = await _call_openai_chatmodel(system_prompt, user_response_query, model_name)
            follow_up_raw = await _maybe_await(follow_up_raw)
            follow_up_normalized = await _normalize_model_output(follow_up_raw)
            
            if session_context:
                await session_context.append_and_persist_memory(
                    "content_creator",
                    f"Follow-up model response: {str(follow_up_normalized)[:200]}...",
                    {"phase": "follow_up_response", "response_type": "model_response"}
                )
            
            # Update agent_state with the new response
            if isinstance(follow_up_normalized, str):
                try:
                    agent_state = json.loads(follow_up_normalized)
                except json.JSONDecodeError:
                    agent_state = {"tool_required": False, "agent_required": False, "text": str(follow_up_normalized)}
            else:
                agent_state = follow_up_normalized
            
            last_normalized = follow_up_normalized

        iteration = 0
        last_normalized: Any = normalized

        while True:
            # Check if we need to call another agent
            needs_agent = bool(agent_state.get("agent_required", False)) if isinstance(agent_state, dict) else False
            
            # Check if we need a tool
            needs_tool = bool(agent_state.get("tool_required", False)) if isinstance(agent_state, dict) else False
            
            print(f"=== CONTENT_CONTENT_CREATOR: Loop iteration {iteration}, needs_agent: {needs_agent}, needs_tool: {needs_tool} ===")
            print(f"=== CONTENT_CONTENT_CREATOR: agent_state: {agent_state} ===")

            # Validation: Only one can be true at a time
            if needs_agent and needs_tool:
                error_response = {
                    "text": "Invalid agent state: Both agent_required and tool_required cannot be true simultaneously",
                    "agent_required": False,
                    "tool_required": False,
                    "error": True
                }
                if session_context:
                    await session_context.send_nano("content_creator", "Error: Both agent and tool requirements detected")
                return error_response

            if not needs_agent and not needs_tool:
                # No agent or tool required, but we need to ask for final approval
                print(f"=== CONTENT_CONTENT_CREATOR: No agent or tool required, asking for final approval ===")
                
                # Check if this is a final response that needs approval
                if isinstance(agent_state, dict) and agent_state.get("text") and not agent_state.get("awaiting_user_followup"):
                    # This is a final response - ask for approval
                    if session_context and getattr(session_context, 'websocket', None):
                        ws = session_context.websocket
                        from datetime import datetime, timezone
                        
                        try:
                            # Prepare the final response for user approval
                            final_response_text = agent_state.get("text", str(last_normalized))
                            
                            # Ask user for approval of the final response
                            approval_payload = {
                                "event": "agent_follow_up_question",
                                "question": "Please review and approve this final content creation response:",
                                "context": f"Final Response:\n\n{final_response_text}",
                                "options": ["Approve", "Request Changes", "Cancel"],
                                "full_message": f"Please review and approve this final content creation response:\n\n{final_response_text}",
                                "agent_name": "content_creator",
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "approval_type": "final_response"
                            }
                            
                            await ws.send_json(approval_payload)
                            
                            if session_context:
                                await session_context.send_nano("content_creator", "awaiting final approval")
                                await session_context.append_and_persist_memory(
                                    "content_creator",
                                    f"Final response ready for approval: {str(final_response_text)[:200]}...",
                                    {"response_type": "final_approval_pending", "timestamp": None}
                                )
                            
                            # Return special response indicating we're waiting for approval
                            return {
                                "awaiting_user_followup": True, 
                                "text": "", 
                                "agent_required": True, 
                                "agent_name": "content_creator",
                                "approval_pending": True,
                                "final_response": agent_state
                            }
                            
                        except Exception as approval_error:
                            print(f"=== CONTENT_CONTENT_CREATOR: Error asking for approval: {approval_error} ===")
                            # Fall back to returning the response if approval fails
                            pass
                
                # If we reach here, either no approval needed or approval failed
                if session_context:
                    await session_context.send_nano("content_creator", "answer ready")
                    await session_context.append_and_persist_memory(
                        "content_creator",
                        f"Direct response (without agent/tool): {str(last_normalized)[:200]}...",
                        {"response_type": "direct", "used_agent": None, "used_tool": None}
                    )
                    
                    await session_context.append_and_persist_memory(
                        "content_creator",
                        f"Final content_creator response: {str(last_normalized)[:200]}...",
                        {"response_type": "final", "timestamp": None}
                    )
                    if session_context.chat_id:
                        await save_chat_message(
                            chat_id=session_context.chat_id,
                            role="assistant",
                            content=str(last_normalized),
                            agent="content_creator",
                            message_type="final_message"
                        )
                
                if isinstance(agent_state, dict):
                    return agent_state
                return {"text": str(last_normalized)}

            # Guard against infinite loops
            if iteration >= max_iterations:
                warning_msg = f"Max iterations ({max_iterations}) reached in content_creator; returning best-effort response."
                print(warning_msg)
                if session_context:
                    await session_context.send_nano("content_creator", "Max iterations reached: showing last message")
                return {"text": str(last_normalized)}

            # Handle agent orchestration
            if needs_agent:
                agent_name = agent_state.get("agent_name")
                agent_query = agent_state.get("agent_query")

                if not agent_name or not agent_query:
                    error_response = {
                        "text": "Agent orchestration requested but missing agent_name or agent_query",
                        "agent_required": False,
                        "tool_required": False,
                        "error": True
                    }
                    if session_context:
                        await session_context.send_nano("content_creator", f"Error: Missing agent_name or agent_query")
                    return error_response

                # Validate agent name
                valid_agents = ("asset_agent", "media_analyst", "social_media_search_agent", "research_agent")
                if agent_name not in valid_agents:
                    error_response = {
                        "text": f"Unknown agent requested: '{agent_name}'. Valid agents: {', '.join(valid_agents)}",
                        "agent_required": False,
                        "tool_required": False,
                        "error": True
                    }
                    if session_context:
                        await session_context.send_nano("content_creator", f"Unknown agent: {agent_name}")
                    return error_response

                # Log agent call
                if session_context:
                    await session_context.send_nano("content_creator", f"agent → {agent_name}")
                    await session_context.append_and_persist_memory(
                        "content_creator",
                        f"Agent call decision: {agent_name} with query: {agent_query}",
                        {"phase": "agent_call", "agent_name": agent_name, "query": agent_query}
                    )

                try:
                    print(f"=== CONTENT_CONTENT_CREATOR: Calling agent {agent_name} with query: {agent_query} ===")
                    # Dynamic import to avoid circular dependencies
                    from utils.router import call_agent
                    agent_result = await call_agent(agent_name, agent_query, model_name, str(registry_path), session_context, user_metadata, user_image_path)
                    print("=== CONTENT_CONTENT_CREATOR: agent_result ===")
                    print(agent_result)
                    print("=== CONTENT_CONTENT_CREATOR: end agent_result ===")
                except Exception as agent_error:
                    error_response = {
                        "text": f"Error calling agent {agent_name}: {str(agent_error)}",
                        "agent_required": False,
                        "tool_required": False,
                        "error": True
                    }
                    if session_context:
                        await session_context.send_nano("content_creator", f"Error calling agent {agent_name}")
                    return error_response

                # Log successful agent call
                if session_context:
                    await session_context.send_nano("content_creator", f"agent ✓ {agent_name}")
                
                # Create JSON serializable version of agent_result
                def json_serializable(obj):
                    if hasattr(obj, 'isoformat'):
                        return obj.isoformat()
                    elif hasattr(obj, '__dict__'):
                        return str(obj)
                    else:
                        return str(obj)
                
                try:
                    agent_result_json = json.dumps(agent_result, indent=2, default=json_serializable)
                except Exception:
                    agent_result_json = str(agent_result)
                
                await session_context.append_and_persist_memory(
                    "content_creator",
                    f"Agent { agent_name} result: {agent_result_json[:300]}...",
                    {"phase": "agent_result", "agent_name": agent_name, "success": True, "result_type": "agent_output"}
                )
                
                if session_context.chat_id:
                    await save_chat_message(
                        chat_id=session_context.chat_id,
                        role="agent",
                        content=agent_result_json,
                        agent="content_creator"
                    )

                # Prepare follow-up query for next iteration
                follow_up_query = f"""
                Original content creation query: {query}

                Agent used: {agent_name}
                Agent query: {agent_query}
                Agent result: {agent_result_json}

                CRITICAL INSTRUCTION: The agent has completed its task successfully. You MUST now:
                1. Set agent_required to FALSE
                2. You may need to call another agent or use tools based on the agent's response
                3. Update your planner step statuses to reflect the agent's data
                4. Continue with content creation process if sufficient information is gathered
                5. Provide comprehensive final content creation response incorporating the agent's data
                6. NEVER set both agent_required and tool_required to true simultaneously
                """

            # Handle tool calling
            elif needs_tool:
                tool_name = agent_state.get("tool_name")
                input_schema_fields = agent_state.get("input_schema_fields", {})

                # Normalize input_schema_fields if list of objects was provided
                if isinstance(input_schema_fields, list):
                    merged = {}
                    for item in input_schema_fields:
                        if isinstance(item, dict):
                            merged.update(item)
                    input_schema_fields = merged

                # Handle WebSocket-style tools inline using the session websocket
                websocket_tools = ["ask_user_follow_up", "send_notification_to_user"]
                if tool_name in websocket_tools and session_context and getattr(session_context, 'websocket', None):
                    ws = session_context.websocket
                    from datetime import datetime, timezone
                    try:
                        if tool_name == "ask_user_follow_up":
                            question = input_schema_fields.get("question") if isinstance(input_schema_fields, dict) else None
                            context_text = input_schema_fields.get("context", "") if isinstance(input_schema_fields, dict) else ""
                            options = input_schema_fields.get("options") if isinstance(input_schema_fields, dict) else None
                            full_message = (f"{context_text}\n\n{question}" if context_text else f"{question}") if question else ""
                            payload = {
                                "event": "agent_follow_up_question",
                                "question": question,
                                "context": context_text,
                                "options": options,
                                "full_message": full_message,
                                "agent_name": "content_creator",
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            }
                            await ws.send_json(payload)
                            if session_context:
                                await session_context.send_nano("content_creator", "asked user a follow-up question")
                            # Signal to orchestrator to pause planning and await user response
                            # Return empty text to prevent duplicate message display
                            # Keep agent_required as True so the same agent handles the follow-up response
                            return {"awaiting_user_followup": True, "text": "", "agent_required": True, "agent_name": "content_creator"}
                        elif tool_name == "send_notification_to_user":
                            message_text = input_schema_fields.get("message") if isinstance(input_schema_fields, dict) else ""
                            notification_type = input_schema_fields.get("notification_type", "info") if isinstance(input_schema_fields, dict) else "info"
                            payload = {
                                "event": "agent_notification",
                                "agent_name": "content_creator",
                                "message": message_text,
                                "notification_type": notification_type,
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            }
                            await ws.send_json(payload)
                            if session_context:
                                await session_context.send_nano("content_creator", f"notification: {notification_type}")
                            # Continue planning after notifying
                            # Fall through to follow-up model step by setting tool_result accordingly
                            tool_result = {"success": True, "notified": True}
                        else:
                            tool_result = {"success": True}
                    except Exception as _ws_err:
                        tool_result = {"success": False, "error": str(_ws_err)}
                else:
                    # For other tools, add user_id if not present
                    if user_id and isinstance(input_schema_fields, dict) and "user_id" not in input_schema_fields:
                        input_schema_fields["user_id"] = user_id

                # Log tool call
                if session_context:
                    await session_context.send_nano("content_creator", f"tool → {tool_name}")
                    await session_context.append_and_persist_memory(
                        "content_creator",
                        f"Tool call decision: {tool_name} with parameters: {input_schema_fields}",
                        {"phase": "tool_call", "tool_name": tool_name, "parameters": input_schema_fields}
                    )

                # Call the tool using tool_router unless it was handled inline above
                if not (tool_name in websocket_tools and isinstance(locals().get('tool_result', None), dict)):
                    try:
                        print(f"=== CONTENT_CONTENT_CREATOR: Calling tool {tool_name} with params: {input_schema_fields} ===")
                        tool_result = await tool_router(tool_name, input_schema_fields)
                        print("=== CONTENT_CONTENT_CREATOR: tool_result ===")
                        print(tool_result)
                        print("=== CONTENT_CONTENT_CREATOR: end tool_result ===")
                    except Exception as tool_error:
                        error_response = {
                            "text": f"Error executing tool {tool_name}: {str(tool_error)}",
                            "tool_required": False,
                            "agent_required": False,
                            "error": True
                        }
                        if session_context:
                            await session_context.send_nano("content_creator", f"Error executing tool {tool_name}")
                        return error_response

                # Check if tool returned an error
                if isinstance(tool_result, dict) and tool_result.get("success") is False:
                    error_response = {
                        "text": f"Tool {tool_name} returned an error: {tool_result.get('error', 'Unknown error')}",
                        "tool_required": False,
                        "agent_required": False,
                        "error": True
                    }
                    if session_context:
                        await session_context.send_nano("content_creator", f"Tool {tool_name} returned error")
                    return error_response

                # Log successful tool call
                if session_context:
                    await session_context.send_nano("content_creator", f"tool ✓ {tool_name}")
                
                try:
                    tool_result_json = json.dumps(tool_result, indent=2, default=json_serializable)
                except Exception:
                    tool_result_json = str(tool_result)
                
                await session_context.append_and_persist_memory(
                    "content_creator",
                    f"Tool {tool_name} result: {tool_result_json[:300]}...",
                    {"phase": "tool_result", "tool_name": tool_name, "success": True, "result_type": "tool_output"}
                )
                
                if session_context.chat_id:
                    await save_chat_message(
                        chat_id=session_context.chat_id,
                        role="tool",
                        content=tool_result_json,
                        agent="content_creator"
                    )

                # Prepare follow-up query for next iteration
                follow_up_query = f"""
                Original content creation query: {query}

                Tool used: {tool_name}
                Tool result: {tool_result_json}

                CRITICAL INSTRUCTION: The tool has been executed successfully and contains the result. You MUST now:
                1. Set tool_required to FALSE
                2. You may need to call another agent or additional tools based on the tool's response
                3. Update your planner step statuses
                4. Continue with content creation process incorporating the tool's data
                5. Provide comprehensive final content creation response
                6. NEVER set both agent_required and tool_required to true simultaneously
                """

            print(f"=== CONTENT_CONTENT_CREATOR: Follow-up query: {follow_up_query[:200]}... ===")

            if session_context:
                await session_context.send_nano("content_creator", "Processing result")
                await session_context.append_and_persist_memory(
                    "content_creator",
                    f"Follow-up model call: Processing results for next step",
                    {"phase": "follow_up", "query": query[:100]}
                )

            print(f"=== CONTENT_CONTENT_CREATOR: Calling follow-up model ===")
            try:
                next_raw = await _call_openai_chatmodel(system_prompt, follow_up_query, model_name)
                print(f"=== CONTENT_CONTENT_CREATOR: Raw model response: {next_raw} ===")
            except Exception as model_error:
                print(f"=== CONTENT_CONTENT_CREATOR: MODEL CALL ERROR: {model_error} ===")
                raise model_error
                
            try:
                next_normalized = await _normalize_model_output(next_raw)
                print(f"=== CONTENT_CONTENT_CREATOR: Normalized model response: {next_normalized} ===")
            except Exception as normalize_error:
                print(f"=== CONTENT_CONTENT_CREATOR: NORMALIZE ERROR: {normalize_error} ===")
                raise normalize_error
                
            last_normalized = next_normalized

            if session_context:
                await session_context.append_and_persist_memory(
                    "content_creator",
                    f"Follow-up model response: {str(next_normalized)[:200]}...",
                    {"phase": "follow_up", "response_type": "model_iteration"}
                )

            print("=== Iteration content_creator response ===")
            print(next_normalized)
            print("=== End iteration response ===")

            # Prepare for next loop
            if isinstance(next_normalized, str):
                try:
                    agent_state = json.loads(next_normalized)
                    print(f"=== CONTENT_CONTENT_CREATOR: Successfully parsed JSON agent_state: {agent_state} ===")
                except json.JSONDecodeError:
                    print(f"=== CONTENT_CONTENT_CREATOR: JSON parse failed, using fallback ===")
                    agent_state = {"tool_required": False, "agent_required": False, "text": str(next_normalized)}
            else:
                agent_state = next_normalized

            iteration += 1
            
    except json.JSONDecodeError as e:
        error_msg = f"Error parsing agent response as JSON: {e}"
        print(error_msg)
        
        if session_context:
            await session_context.send_nano("content_creator", "Error parsing agent response as JSON")
        
        return normalized
        
    except Exception as e:
        error_msg = f"Error in content_creator: {e}"
        print(error_msg)
        
        if session_context:
            await session_context.send_nano("content_creator", "Error in content_creator")
        
        return normalized