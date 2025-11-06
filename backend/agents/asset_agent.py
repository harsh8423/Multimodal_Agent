
from typing import Any, Optional, Dict, List
from pathlib import Path
from utils.build_prompts import build_system_prompt
from utils.utility import chat_model_router, _normalize_model_output
from utils.tool_router import tool_router
from config.chat_model_config import get_final_config

DEFAULT_REGISTRY_FILENAME = "system_prompts.json"

# Global temporary conversation history (session-scoped)
_conversation_history: Dict[str, List[Dict[str, str]]] = {}

def _get_conversation_context(session_id: str, max_messages: int = 10) -> str:
    """Get conversation context for LLM from temporary memory"""
    if session_id not in _conversation_history:
        return ""
    
    history = _conversation_history[session_id]
    if not history:
        return ""
    
    # Get the last max_messages
    recent_history = history[-max_messages:]
    
    context_parts = []
    for msg in recent_history:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        context_parts.append(f"{role.capitalize()}: {content}")
    
    return "Recent conversation:\n" + "\n".join(context_parts)

def _add_to_conversation(session_id: str, role: str, content: str):
    """Add message to temporary conversation history"""
    if session_id not in _conversation_history:
        _conversation_history[session_id] = []
    
    _conversation_history[session_id].append({
        "role": role,
        "content": content,
        "timestamp": __import__("datetime").datetime.utcnow().isoformat()
    })
    
    # Keep only last 20 messages to prevent memory bloat
    if len(_conversation_history[session_id]) > 20:
        _conversation_history[session_id] = _conversation_history[session_id][-20:]

def _clear_conversation(session_id: str):
    """Clear conversation history for a specific session"""
    if session_id in _conversation_history:
        del _conversation_history[session_id]

def _get_conversation_stats() -> Dict[str, int]:
    """Get statistics about conversation history (for debugging)"""
    return {session_id: len(history) for session_id, history in _conversation_history.items()}

async def asset_agent(query: str, model_name: Optional[str] = None, chat_llm_model: Optional[str] = None,
                      registry_path: Optional[str] = None, max_iterations: int = 5, user_id: Optional[str] = None, 
                      user_metadata: Optional[Dict] = None, user_image_path: Optional[str] = None, 
                      session_id: Optional[str] = None) -> Any:
    """
    Asset agent for managing and retrieving user data including brands, competitors, scraped posts, and templates.
    Uses flexible function-based tools to handle various data retrieval and multi-task operations.
    """
    # Get chat model configuration from central config
    config = get_final_config(agent_name="asset_agent")
    
    # Use provided parameters or fall back to config
    final_model_name = model_name or config["model_name"]
    final_chat_llm_model = chat_llm_model or config["chat_llm_model"]

    if registry_path is None:
        registry_path = Path(__file__).parent.parent / DEFAULT_REGISTRY_FILENAME
    else:
        registry_path = Path(registry_path)

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

    # Add conversation context if session_id is provided
    conversation_context = ""
    if session_id:
        conversation_context = _get_conversation_context(session_id)
        if conversation_context:
            system_prompt += f"\n\n{conversation_context}"
        
        # Add current user query to conversation history
        _add_to_conversation(session_id, "user", query)

    # Print system prompt as requested
    print(system_prompt)

    raw = await chat_model_router(system_prompt, enhanced_query, final_chat_llm_model, final_model_name)
    normalized = await _normalize_model_output(raw)

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
                if isinstance(agent_state, dict):
                    print(f"=== ASSET_AGENT: Returning agent_state dict: {agent_state} ===")
                    print(f"=== ASSET_AGENT: FINAL RETURN: {agent_state} ===")
                    
                    # Add assistant response to conversation history
                    if session_id:
                        response_text = agent_state.get("text", str(agent_state))
                        _add_to_conversation(session_id, "assistant", response_text)
                    
                    return agent_state
                
                print("=== ASSET_AGENT: direct response ===")
                print(last_normalized)
                print("=== ASSET_AGENT: end direct response ===")
                
                # Add assistant response to conversation history
                if session_id:
                    _add_to_conversation(session_id, "assistant", str(last_normalized))
                
                return {"text": str(last_normalized)}

            if iteration >= max_iterations:
                warning_msg = f"Max iterations ({max_iterations}) reached in asset_agent; returning best-effort response."
                print(warning_msg)
                
                # Add assistant response to conversation history
                if session_id:
                    _add_to_conversation(session_id, "assistant", str(last_normalized))
                
                return {"text": str(last_normalized)}

            tool_name = agent_state.get("tool_name")
            input_schema_fields = agent_state.get("input_schema_fields", {})

            if isinstance(input_schema_fields, list):
                merged = {}
                for item in input_schema_fields:
                    if isinstance(item, dict):
                        merged.update(item)
                input_schema_fields = merged


            # ALWAYS override user_id with actual value from session context
            if user_id and isinstance(input_schema_fields, dict):
                input_schema_fields["user_id"] = user_id
                print(f"🔧 ASSET_AGENT: Overriding user_id with actual value: {user_id}")
            
            # Special handling for CRUD tools - transform parameters to match function signatures
            if isinstance(input_schema_fields, dict):
                transformed_params = {}
                
                # Handle CREATE operations (need to bundle data into *_data parameter)
                if tool_name in ["create_brand", "create_competitor", "create_template"]:
                    data_type = tool_name.replace("create_", "")
                    data_dict = {}
                    
                    # Extract relevant fields for each data type
                    if data_type == "brand":
                        for key in ["name", "slug", "description", "website", "industry", "target_audience"]:
                            if key in input_schema_fields:
                                data_dict[key] = input_schema_fields.pop(key)
                        
                        # Add required fields with defaults if not provided
                        if "theme" not in data_dict:
                            data_dict["theme"] = {
                                "primary_color": "#3B82F6",
                                "secondary_color": "#1E40AF", 
                                "font": "Inter",
                                "logo_url": None
                            }
                        
                        if "details" not in data_dict:
                            data_dict["details"] = {
                                "website": data_dict.get("website"),
                                "industry": data_dict.get("industry"),
                                "audience": data_dict.get("target_audience", [])
                            }
                        
                        # Clean up individual fields that are now in details
                        for field in ["website", "industry", "target_audience"]:
                            if field in data_dict:
                                del data_dict[field]
                        
                        # Add default posting settings
                        if "default_posting_settings" not in data_dict:
                            data_dict["default_posting_settings"] = {
                                "timezone": "UTC",
                                "default_platforms": ["instagram", "linkedin"],
                                "post_approval_required": False
                            }
                    
                    elif data_type == "competitor":
                        for key in ["name", "platform", "handle", "description", "website", "industry"]:
                            if key in input_schema_fields:
                                data_dict[key] = input_schema_fields.pop(key)
                        
                        # Add required fields with defaults if not provided
                        if "platform" not in data_dict:
                            data_dict["platform"] = "instagram"
                        
                        if "handle" not in data_dict:
                            data_dict["handle"] = data_dict.get("name", "").lower().replace(" ", "_")
                        
                        if "profile_url" not in data_dict:
                            platform = data_dict.get("platform", "instagram")
                            handle = data_dict.get("handle", "")
                            if platform == "instagram":
                                data_dict["profile_url"] = f"https://instagram.com/{handle}"
                            elif platform == "linkedin":
                                data_dict["profile_url"] = f"https://linkedin.com/in/{handle}"
                            elif platform == "youtube":
                                data_dict["profile_url"] = f"https://youtube.com/@{handle}"
                            else:
                                data_dict["profile_url"] = f"https://{platform}.com/{handle}"
                    
                    elif data_type == "template":
                        for key in ["name", "content", "category", "description", "brand_id"]:
                            if key in input_schema_fields:
                                data_dict[key] = input_schema_fields.pop(key)
                        
                        # Add required fields with defaults if not provided
                        if "type" not in data_dict:
                            data_dict["type"] = "instagram_post"
                        
                        if "structure" not in data_dict:
                            data_dict["structure"] = {
                                "content": data_dict.get("content", ""),
                                "media_placeholders": [],
                                "hashtags": [],
                                "call_to_action": ""
                            }
                    
                    transformed_params = {
                        "user_id": input_schema_fields.get("user_id", user_id),
                        f"{data_type}_data": data_dict
                    }
                
                # Handle UPDATE operations (need brand_id/competitor_id/template_id and update_data)
                elif tool_name in ["update_brand", "update_competitor", "update_template"]:
                    data_type = tool_name.replace("update_", "")
                    update_data = {}
                    
                    # Extract ID field
                    id_field = f"{data_type}_id"
                    entity_id = input_schema_fields.pop(id_field, None)
                    
                    # Extract update fields (exclude user_id and id fields)
                    for key, value in input_schema_fields.items():
                        if key not in ["user_id", id_field]:
                            update_data[key] = value
                    
                    transformed_params = {
                        "user_id": input_schema_fields.get("user_id", user_id),
                        f"{data_type}_id": entity_id,
                        "update_data": update_data
                    }
                
                # Handle DELETE operations (need user_id and entity_id)
                elif tool_name in ["delete_brand", "delete_competitor", "delete_template"]:
                    data_type = tool_name.replace("delete_", "")
                    id_field = f"{data_type}_id"
                    entity_id = input_schema_fields.pop(id_field, None)
                    
                    transformed_params = {
                        "user_id": input_schema_fields.get("user_id", user_id),
                        f"{data_type}_id": entity_id
                    }
                
                # Handle scrape_competitor_data (user_id, competitor_id, limit)
                elif tool_name == "scrape_competitor_data":
                    competitor_id = input_schema_fields.pop("competitor_id", None)
                    limit = input_schema_fields.pop("limit", 10)
                    
                    transformed_params = {
                        "user_id": input_schema_fields.get("user_id", user_id),
                        "competitor_id": competitor_id,
                        "limit": limit
                    }
                
                # Handle perform_bulk_scraping (user_id, scraping_requests)
                elif tool_name == "perform_bulk_scraping":
                    scraping_requests = input_schema_fields.pop("scraping_requests", [])
                    
                    transformed_params = {
                        "user_id": input_schema_fields.get("user_id", user_id),
                        "scraping_requests": scraping_requests
                    }
                
                # If we transformed parameters, use them
                if transformed_params:
                    input_schema_fields = transformed_params
                    print(f"🔧 ASSET_AGENT: Transformed {tool_name} params: {input_schema_fields}")
            
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
                return error_response

            # Check if tool returned an error
            if isinstance(tool_result, dict) and tool_result.get("success") is False:
                # Tool returned an error, stop the loop and return the error
                error_response = {
                    "text": f"Tool {tool_name} returned an error: {tool_result.get('error', 'Unknown error')}",
                    "tool_required": False,
                    "error": True
                }
                print(f"=== ASSET_AGENT: RETURNING ERROR RESPONSE: {error_response} ===")
                return error_response

            # Ask model for the next step
            # Create JSON serializable version for the follow-up query
            def json_serializable(obj):
                if hasattr(obj, 'isoformat'):  # datetime objects
                    return obj.isoformat()
                elif hasattr(obj, '__dict__'):
                    return str(obj)
                else:
                    return str(obj)
            
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

            print(f"=== ASSET_AGENT: Calling follow-up model with query: {follow_up_query[:200]}... ===")
            try:
                next_raw = await chat_model_router(system_prompt, follow_up_query, final_chat_llm_model, final_model_name)
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
        
        # Add assistant response to conversation history even in error case
        if session_id:
            _add_to_conversation(session_id, "assistant", str(normalized))
        
        print(f"=== ASSET_AGENT: EXCEPTION FALLBACK RETURN: {normalized} ===")
        return normalized