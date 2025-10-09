import asyncio
import inspect
import json
from typing import Any, Dict, Optional
from pathlib import Path

# Import the build_prompts function and chat model
from utils.build_prompts import build_system_prompt
from models.chat_openai import orchestrator_function as openai_chatmodel
from utils.utility import _call_openai_chatmodel, _normalize_model_output
from utils.router import call_agent
from utils.tool_router import tool_router
from utils.session_memory import SessionContext
from utils.mongo_store import save_chat_message


async def _maybe_await(value):
    """
    Await `value` if it is awaitable; otherwise return it.
    This is an async function so callers should `await _maybe_await(...)`.
    """
    if inspect.isawaitable(value):
        return await value
    return value

async def social_media_manager(
    message: Dict[str, Any],
    websocket,
    model_name: str = "gpt-5-mini",
    session_context: Optional[SessionContext] = None,
    max_iterations: int = 5,
    *,
    debug: bool = False,
) -> Dict[str, Any]:
    user_text = ""
    user_metadata = {}
    user_image_path = None
    
    if isinstance(message, dict):
        parts = []
        if "text" in message and message["text"]:
            parts.append(str(message["text"]).strip())
        if "image_path" in message and message["image_path"]:
            parts.append(f"[image_saved_at:{message['image_path']}]")
            user_image_path = message["image_path"]
        if "metadata" in message and isinstance(message["metadata"], dict):
            md_sample = ", ".join(f"{k}={v}" for k, v in message["metadata"].items())
            if md_sample:
                parts.append(f"[meta:{md_sample}]")
            user_metadata = message["metadata"].copy()
        user_text = "\n".join(parts).strip()

    if not user_text:
        user_text = "(empty user message)"

    # near top, after building user_text
    if user_text == "(empty user message)":
        # Log and skip — do not call the model
        if session_context:
            await session_context.send_nano("social_media_manager", "Received empty user message")
        return {"agent_required": False, "self_response": ""}


    # Get social media manager memory context if available
    social_media_manager_memory_context = ""
    chat_history_context = ""
    if session_context:
        social_media_manager_memory = await session_context.get_agent_memory("social_media_manager")
        # Sanitize memory to remove control-only frames (e.g., chat_id payloads)
        try:
            entries = await social_media_manager_memory.get_all()
            filtered_lines = []
            from datetime import datetime
            for entry in entries[-50:]:
                content = str(entry.content or "")
                drop = False
                # Heuristic: drop entries that only carry chat_id control info
                if '"chat_id"' in content or "'chat_id'" in content:
                    # Try to parse a JSON blob if present
                    try:
                        start_idx = content.find("{")
                        end_idx = content.rfind("}")
                        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                            import json as _json
                            blob = content[start_idx:end_idx+1]
                            obj = _json.loads(blob)
                            if isinstance(obj, dict) and set(obj.keys()) <= {"chat_id", "type"}:
                                drop = True
                    except Exception:
                        # If we cannot parse but it obviously references only chat_id, drop if it's an ack
                        if "(chat_id:" in content and "What would you like me to do" in content:
                            drop = True
                # Also drop pure acknowledgements of chat switch without user text
                if not drop and "(chat_id:" in content and "User query:" in content and "text" not in content:
                    drop = True
                if drop:
                    continue
                # Keep this line
                ts = entry.timestamp
                try:
                    ts_str = ts.strftime("%H:%M") if isinstance(ts, datetime) else str(ts)
                except Exception:
                    ts_str = str(ts)
                filtered_lines.append(f"[{ts_str}] {content}")
            if filtered_lines:
                social_media_manager_memory_context = "Recent social media manager memory:\n" + "\n".join(filtered_lines)
            else:
                social_media_manager_memory_context = ""
        except Exception:
            # Fallback to raw context if anything goes wrong
            social_media_manager_memory_context = await social_media_manager_memory.get_context_string()
        # Suppress verbose memory context logging
        
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
                    elif role == "assistant":
                        agent_label = agent if agent else "assistant"
                        chat_history_parts.append(f"Assistant ({agent_label}): {content}")
                
                if chat_history_parts:
                    chat_history_context = "Recent conversation:\n" + "\n".join(chat_history_parts)
        
        # Add memory to social media manager memory using new chat-scoped system, but avoid logging pure control frames
        try:
            is_control = False
            if isinstance(message, dict) and "chat_id" in message and not message.get("text") and not message.get("image"):
                is_control = True
            if not is_control:
                # Create memory entry with metadata
                memory_entry = f"User query: {user_text}"
                memory_metadata = {
                    "timestamp": message.get("timestamp"), 
                    "has_image": bool(user_image_path),
                    "image_path": user_image_path if user_image_path else None
                }
                
                # Add user metadata to memory metadata
                if user_metadata:
                    memory_metadata["user_metadata"] = user_metadata
                
                await session_context.append_and_persist_memory(
                    "social_media_manager",
                    memory_entry,
                    memory_metadata
                )
                
                # Also save metadata to social media manager memory for future reference
                if user_metadata:
                    await session_context.append_and_persist_memory(
                        "social_media_manager",
                        f"User metadata context: {json.dumps(user_metadata)}",
                        {"context_type": "user_metadata", "timestamp": message.get("timestamp")}
                    )
                if user_image_path:
                    await session_context.append_and_persist_memory(
                        "social_media_manager",
                        f"User provided image: {user_image_path}",
                        {"context_type": "user_asset", "timestamp": message.get("timestamp")}
                    )
        except Exception:
            pass

    # Build the system prompt using the registry
    try:
        registry_path = Path(__file__).parent.parent / "system_prompts.json"
        system_prompt = build_system_prompt("social_media_manager", str(registry_path))
        
        # Add memory context to system prompt if available
        if social_media_manager_memory_context:
            system_prompt += f"\n\n{social_media_manager_memory_context}"
        
        # Add chat history context to system prompt if available
        if chat_history_context:
            system_prompt += f"\n\n{chat_history_context}"
        
        # Add explicit JSON enforcement
        system_prompt += "\n\nCRITICAL: You MUST always return ONLY valid JSON in the exact schema format. NO additional text, explanations, or prose. Just the JSON object."
            
        # Print system prompt as requested
        print(system_prompt)
    except Exception as e:
        # Fallback to a simple prompt if registry fails
        system_prompt = (
            "You are an intelligent social media manager. Analyze the user query and respond with JSON: "
            "{\"agent_required\": boolean, \"self_response\": \"string if false\", "
            "\"agent_name\": \"research_agent or asset_agent if true\", \"agent_query\": \"string if true\"}"
        )
        
        if session_context:
            await session_context.send_nano("social_media_manager","Failed to load social media manager prompt")

    # Call the social media manager model safely (async or threaded)
    try:
        if session_context:
            await session_context.send_nano("social_media_manager", "thinking…")
        
        raw = await _call_openai_chatmodel(system_prompt, user_text, model_name)
        # If the chat model itself returned an awaitable for some reason, ensure resolution
        raw = await _maybe_await(raw)
        
        if session_context:
            # Nano: model responded
            await session_context.send_nano("social_media_manager", "parsed response")
            
    except Exception as e:
        error_msg = f"Error calling model: {e}"
        if session_context:
            await session_context.send_nano("social_media_manager", "Error calling model")
        
        fallback = {
            "agent_required": False,
            "self_response": error_msg,
        }
        await websocket.send_json({"text": fallback["self_response"]})
        return fallback

    # Normalize raw -> dict
    def _normalize_social_media_management(val: Any) -> Dict[str, Any]:
        if isinstance(val, dict):
            return val
        if isinstance(val, str):
            try:
                return json.loads(val)
            except Exception:
                return {"agent_required": False, "self_response": val}
        return {"agent_required": False, "self_response": str(val)}

    social_media_management = _normalize_social_media_management(raw)

    iteration = 0
    last_text = ""

    while True:
        # Check if we need to call another agent
        needs_agent = bool(social_media_management.get("agent_required", False))
        
        # Check if we need a tool
        needs_tool = bool(social_media_management.get("tool_required", False))
        
        print(f"=== SOCIAL_MEDIA_MANAGER: Loop iteration {iteration}, needs_agent: {needs_agent}, needs_tool: {needs_tool} ===")
        print(f"=== SOCIAL_MEDIA_MANAGER: social_media_management: {social_media_management} ===")

        # Validation: Only one can be true at a time
        if needs_agent and needs_tool:
            error_response = {
                "agent_required": False,
                "self_response": "Invalid social media management state: Both agent_required and tool_required cannot be true simultaneously",
                "error": True
            }
            if session_context:
                await session_context.send_nano("social_media_manager", "Error: Both agent and tool requirements detected")
            await websocket.send_json({"text": error_response["self_response"]})
            return error_response

        if not needs_agent and not needs_tool:
            # No agent or tool required - return the response
            self_response = social_media_management.get("self_response", social_media_management.get("text", ""))
            if not isinstance(self_response, str):
                self_response = str(self_response)

            # If the final response matches the last agent message we sent, avoid duplicating it
            try:
                if self_response.strip() == (last_text or "").strip():
                    if debug:
                        await websocket.send_json({"debug": {"note": "suppressing duplicate final response"}})
                    return {"agent_required": False, "self_response": self_response}
            except Exception:
                pass

            # Nano: answer ready
            if session_context:
                await session_context.send_nano("social_media_manager", "answer ready")

            if session_context:
                await session_context.append_and_persist_memory(
                    "social_media_manager",
                    f"Social Media Manager response: {self_response}",
                    {"response_type": "direct", "timestamp": message.get("timestamp")}
                )
                if session_context.chat_id:
                    await save_chat_message(
                        chat_id=session_context.chat_id,
                        role="assistant",
                        content=self_response,
                        agent="social_media_manager",
                        message_type="final_message"
                    )

            await websocket.send_json({"text": self_response, "agent_name": "social_media_manager"})
            print(f"[social_media_manager-response] {self_response}")

            return {"agent_required": False, "self_response": self_response}

        # Guard against infinite loops
        if iteration >= max_iterations:
            warning_msg = f"Max iterations ({max_iterations}) reached in social media manager; returning best-effort response."
            print(warning_msg)
            if session_context:
                await session_context.send_nano("social_media_manager", "Max Iterations Reached showing last message")
            fallback_text = social_media_management.get("self_response") or last_text or "Max iterations reached."
            await websocket.send_json({"text": fallback_text})
            return {"agent_required": False, "self_response": fallback_text}

        # Handle agent orchestration
        if needs_agent:
            agent_name = social_media_management.get("agent_name", "").strip()
            agent_query = social_media_management.get("agent_query", "").strip()

            if not agent_name or not agent_query:
                error_response = {
                    "agent_required": False,
                    "self_response": "Agent orchestration requested but missing agent_name or agent_query",
                    "error": True
                }
                if session_context:
                    await session_context.send_nano("social_media_manager", "Error: Missing agent_name or agent_query")
                await websocket.send_json({"text": error_response["self_response"]})
                return error_response

            # Validate agent name
            valid_agents = ("research_agent", "asset_agent", "media_analyst", "social_media_search_agent", "media_activist", "copy_writer")
            if agent_name not in valid_agents:
                error_response = {
                    "agent_required": False,
                    "self_response": f"Unknown agent requested: '{agent_name}'. Valid agents: {', '.join(valid_agents)}",
                    "error": True
                }
                if session_context:
                    await session_context.send_nano("social_media_manager", f"Unknown agent: {agent_name}")
                await websocket.send_json({"text": error_response["self_response"]})
                return error_response

            # Log agent call
            if session_context:
                await session_context.send_nano("social_media_manager", f"routing → {agent_name}")
                await session_context.append_and_persist_memory(
                    "social_media_manager",
                    f"Agent call decision: {agent_name} with query: {agent_query}",
                    {"phase": "agent_call", "agent_name": agent_name, "query": agent_query}
                )

            await websocket.send_json({
                "text": f"Routing to {agent_name}...",
                "agent_required": True,
                "agent_name": agent_name,
                "agent_query": agent_query
            })

            try:
                print(f"=== SOCIAL_MEDIA_MANAGER: Calling agent {agent_name} with query: {agent_query} ===")
                result = await call_agent(agent_name, agent_query, model_name, registry_path, session_context, user_metadata, user_image_path)
                print("=== SOCIAL_MEDIA_MANAGER: agent_result ===")
                print(result)
                print("=== SOCIAL_MEDIA_MANAGER: end agent_result ===")
            except Exception as agent_error:
                # Use verification tool to diagnose the agent error
                try:
                    from tools.verification_tool import diagnose_agent_error
                    diagnosis = await diagnose_agent_error(
                        agent_name=agent_name,
                        error_message=str(agent_error),
                        agent_query=agent_query,
                        agent_output=None
                    )
                    
                    # Log diagnosis for debugging
                    if session_context:
                        await session_context.send_nano("social_media_manager", f"Verification tool diagnosis: {diagnosis.get('analysis', 'No analysis available')}")
                    
                    # Check if we should route to a different agent
                    solutions = diagnosis.get('solutions', [])
                    route_solution = next((s for s in solutions if s.get('action') == 'route_to_agent'), None)
                    
                    if route_solution and route_solution.get('patch'):
                        # Try routing to the recommended agent
                        try:
                            recommended_agent = route_solution['patch'].get('agent_name')
                            if recommended_agent and recommended_agent != agent_name:
                                if session_context:
                                    await session_context.send_nano("social_media_manager", f"Re-routing to {recommended_agent} based on verification tool recommendation")
                                
                                # Retry with the recommended agent
                                result = await call_agent(recommended_agent, agent_query, model_name, registry_path, session_context, user_metadata, user_image_path)
                                
                                # Success after re-routing, continue with normal flow
                                if session_context:
                                    await session_context.send_nano("social_media_manager", f"Agent {recommended_agent} succeeded after re-routing")
                                # Continue with normal agent result processing
                            else:
                                raise Exception("No valid agent recommendation")
                        except Exception as retry_error:
                            # Re-routing failed, fall through to error handling
                            pass
                    
                    # If no re-routing or re-routing failed, provide detailed error response
                    error_response = {
                        "agent_required": False,
                        "self_response": f"Agent {agent_name} failed: {diagnosis.get('analysis', str(agent_error))}. Recommended actions: {', '.join([s.get('action', 'unknown') for s in solutions])}",
                        "error": True,
                        "verification_diagnosis": diagnosis
                    }
                    
                except Exception as verification_error:
                    # Verification tool itself failed, use basic error response
                    error_response = {
                        "agent_required": False,
                        "self_response": f"Error calling agent {agent_name}: {str(agent_error)}",
                        "error": True
                    }
                
                if session_context:
                    await session_context.send_nano("social_media_manager", f"Error calling agent {agent_name}")
                await websocket.send_json({"text": error_response["self_response"]})
                return error_response

            # Log successful agent call
            if session_context:
                await session_context.send_nano("social_media_manager", f"agent ✓ {agent_name}")
                await session_context.append_and_persist_memory(
                    "social_media_manager",
                    f"Agent {agent_name} result: {str(result)[:300]}...",
                    {"phase": "agent_result", "agent_name": agent_name, "success": True, "result_type": "agent_output"}
                )
                if session_context.chat_id:
                    await save_chat_message(
                        chat_id=session_context.chat_id,
                        role="agent",
                        content=str(result),
                        agent="social_media_manager"
                    )

            try:
                agent_text = result.get("text", "") if isinstance(result, dict) else str(result)
                last_text = agent_text or last_text
                if agent_text:
                    print(f"[agent-response:{agent_name}] {agent_text}")
            except Exception:
                pass

            # Prepare follow-up query for next iteration
            follow_up_query = f"""
            Original user message: {user_text}

            Agent used: {agent_name}
            Agent query: {agent_query}
            Agent result: {json.dumps(result, indent=2)}

            CRITICAL INSTRUCTION: The agent has completed its task successfully. You MUST now:
            1. Set agent_required to FALSE
            2. You may need to call another agent or use tools based on the agent's response
            3. Update your planner step statuses to reflect the agent's data
            4. Continue with the social media management process if sufficient information is gathered
            5. Provide comprehensive final response incorporating the agent's data
            6. NEVER set both agent_required and tool_required to true simultaneously
            
            CRITICAL: You MUST return ONLY the JSON object in the exact schema format. NO additional text, explanations, or prose. Just the JSON:
            {{
              "agent_required": false,
              "self_response": "your comprehensive response incorporating the agent's data",
              "tool_required": false,
              "planner": {{
                "plan_steps": [...],
                "summary": "updated plan summary"
              }}
            }}
            """

        # Handle tool calling
        elif needs_tool:
            tool_name = social_media_management.get("tool_name")
            input_schema_fields = social_media_management.get("input_schema_fields", {})

            # Normalize input_schema_fields if list of objects was provided
            if isinstance(input_schema_fields, list):
                merged = {}
                for item in input_schema_fields:
                    if isinstance(item, dict):
                        merged.update(item)
                input_schema_fields = merged

            # For tools, add user_id if not present
            user_id = getattr(session_context, 'user_id', None) if session_context else None
            if user_id and isinstance(input_schema_fields, dict) and "user_id" not in input_schema_fields:
                input_schema_fields["user_id"] = user_id

            # Log tool call
            if session_context:
                await session_context.send_nano("social_media_manager", f"tool → {tool_name}")
                await session_context.append_and_persist_memory(
                    "social_media_manager",
                    f"Tool call decision: {tool_name} with parameters: {input_schema_fields}",
                    {"phase": "tool_call", "tool_name": tool_name, "parameters": input_schema_fields}
                )

            # Call the tool using tool_router
            try:
                print(f"=== SOCIAL_MEDIA_MANAGER: Calling tool {tool_name} with params: {input_schema_fields} ===")
                tool_result = await tool_router(tool_name, input_schema_fields)
                print("=== SOCIAL_MEDIA_MANAGER: tool_result ===")
                print(tool_result)
                print("=== SOCIAL_MEDIA_MANAGER: end tool_result ===")
            except Exception as tool_error:
                # Use verification tool to diagnose the error
                try:
                    from tools.verification_tool import diagnose_tool_error
                    diagnosis = await diagnose_tool_error(
                        tool_name=tool_name,
                        tool_call_payload=input_schema_fields,
                        tool_response={"error": str(tool_error)},
                        error_details=str(tool_error)
                    )
                    
                    # Log diagnosis for debugging
                    if session_context:
                        await session_context.send_nano("social_media_manager", f"Verification tool diagnosis: {diagnosis.get('analysis', 'No analysis available')}")
                    
                    # Check if we can auto-fix and retry
                    solutions = diagnosis.get('solutions', [])
                    auto_fix_solution = next((s for s in solutions if s.get('action') == 'auto_fix_and_retry'), None)
                    
                    if auto_fix_solution and auto_fix_solution.get('patch'):
                        # Apply the patch and retry
                        try:
                            patch = auto_fix_solution['patch']
                            if isinstance(patch, dict):
                                input_schema_fields.update(patch)
                            elif isinstance(patch, str):
                                # Try to parse as JSON patch
                                patch_data = json.loads(patch)
                                input_schema_fields.update(patch_data)
                            
                            # Retry the tool call
                            tool_result = await tool_router(tool_name, input_schema_fields)
                            if isinstance(tool_result, dict) and tool_result.get("success") is not False:
                                # Success after auto-fix, continue with normal flow
                                if session_context:
                                    await session_context.send_nano("social_media_manager", f"Tool {tool_name} succeeded after auto-fix")
                                # Continue with normal tool result processing
                            else:
                                raise Exception("Auto-fix failed")
                        except Exception as retry_error:
                            # Auto-fix failed, fall through to error handling
                            pass
                    
                    # If no auto-fix or auto-fix failed, provide detailed error response
                    error_response = {
                        "agent_required": False,
                        "self_response": f"Tool {tool_name} failed: {diagnosis.get('analysis', str(tool_error))}. Recommended actions: {', '.join([s.get('action', 'unknown') for s in solutions])}",
                        "error": True,
                        "verification_diagnosis": diagnosis
                    }
                    
                except Exception as verification_error:
                    # Verification tool itself failed, use basic error response
                    error_response = {
                        "agent_required": False,
                        "self_response": f"Error executing tool {tool_name}: {str(tool_error)}",
                        "error": True
                    }
                
                if session_context:
                    await session_context.send_nano("social_media_manager", f"Error executing tool {tool_name}")
                await websocket.send_json({"text": error_response["self_response"]})
                return error_response

            # Check if tool returned an error
            if isinstance(tool_result, dict) and tool_result.get("success") is False:
                error_response = {
                    "agent_required": False,
                    "self_response": f"Tool {tool_name} returned an error: {tool_result.get('error', 'Unknown error')}",
                    "error": True
                }
                if session_context:
                    await session_context.send_nano("social_media_manager", f"Tool {tool_name} returned error")
                await websocket.send_json({"text": error_response["self_response"]})
                return error_response

            # Log successful tool call
            if session_context:
                await session_context.send_nano("social_media_manager", f"tool ✓ {tool_name}")
                await session_context.append_and_persist_memory(
                    "social_media_manager",
                    f"Tool {tool_name} result: {str(tool_result)[:300]}...",
                    {"phase": "tool_result", "tool_name": tool_name, "success": True, "result_type": "tool_output"}
                )
                if session_context.chat_id:
                    await save_chat_message(
                        chat_id=session_context.chat_id,
                        role="tool",
                        content=str(tool_result),
                        agent="social_media_manager"
                    )

            # Prepare follow-up query for next iteration
            follow_up_query = f"""
            Original user message: {user_text}

            Tool used: {tool_name}
            Tool result: {json.dumps(tool_result, indent=2)}

            CRITICAL INSTRUCTION: The tool has been executed successfully and contains the result. You MUST now:
            1. Set tool_required to FALSE
            2. You may need to call another agent or additional tools based on the tool's response
            3. Update your planner step statuses
            4. Continue with social media management process incorporating the tool's data
            5. Provide comprehensive final response
            6. NEVER set both agent_required and tool_required to true simultaneously
            
            CRITICAL: You MUST return ONLY the JSON object in the exact schema format. NO additional text, explanations, or prose. Just the JSON:
            {{
              "agent_required": false,
              "self_response": "your comprehensive response incorporating the tool's data",
              "tool_required": false,
              "planner": {{
                "plan_steps": [...],
                "summary": "updated plan summary"
              }}
            }}
            """

        print(f"=== SOCIAL_MEDIA_MANAGER: Follow-up query: {follow_up_query[:200]}... ===")

        if session_context:
            await session_context.send_nano("social_media_manager", "Processing result")
            await session_context.append_and_persist_memory(
                "social_media_manager",
                f"Follow-up model call: Processing results for next step",
                {"phase": "follow_up", "query": user_text[:100]}
            )

        print(f"=== SOCIAL_MEDIA_MANAGER: Calling follow-up model ===")
        try:
            raw = await _call_openai_chatmodel(system_prompt, follow_up_query, model_name)
            print(f"=== SOCIAL_MEDIA_MANAGER: Raw model response: {raw} ===")
        except Exception as model_error:
            print(f"=== SOCIAL_MEDIA_MANAGER: MODEL CALL ERROR: {model_error} ===")
            raise model_error
            
        try:
            raw = await _maybe_await(raw)
            social_media_management = _normalize_social_media_management(raw)
            print(f"=== SOCIAL_MEDIA_MANAGER: Normalized social_media_management: {social_media_management} ===")
        except Exception as normalize_error:
            print(f"=== SOCIAL_MEDIA_MANAGER: NORMALIZE ERROR: {normalize_error} ===")
            raise normalize_error

        if session_context:
            await session_context.append_and_persist_memory(
                "social_media_manager",
                f"Follow-up model response: {str(social_media_management)[:200]}...",
                {"phase": "follow_up", "response_type": "model_iteration"}
            )

        print("=== Iteration social media manager response ===")
        print(social_media_management)
        print("=== End iteration response ===")

        iteration += 1
