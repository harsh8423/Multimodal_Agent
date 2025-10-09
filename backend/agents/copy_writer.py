# copy_writer.py
import asyncio
import inspect
import json
from pathlib import Path
from typing import Any, Dict, Optional
from utils.build_prompts import build_system_prompt

from utils.utility import _call_openai_chatmodel, _normalize_model_output
from utils.session_memory import SessionContext
from utils.mongo_store import save_chat_message

DEFAULT_REGISTRY_FILENAME = "system_prompts.json"


async def copy_writer(query: str, model_name: str = "gpt-4o-mini",
                     registry_path: Optional[str] = None, session_context: Optional[SessionContext] = None,
                     user_metadata: Optional[Dict] = None, user_image_path: Optional[str] = None) -> Any:
    """
    Single-step copy_writer agent that executes the query received from social_media_manager
    and returns the content back to it. Unlike research_agent, this agent does not use tools
    and focuses solely on generating platform-native copy and scripts.
    """
    # Log copy_writer start
    if session_context:
        await session_context.send_nano("copy_writer", "starting…")

    # find registry path (default to project root file)
    if registry_path is None:
        registry_path = Path(__file__).parent.parent / DEFAULT_REGISTRY_FILENAME
    else:
        registry_path = Path(registry_path)

    # Get copy_writer memory context if available
    copy_writer_memory_context = ""
    chat_history_context = ""
    if session_context:
        copy_writer_memory = await session_context.get_agent_memory("copy_writer")
        copy_writer_memory_context = await copy_writer_memory.get_context_string()
        
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
                    elif role == "assistant" and agent == "copy_writer":
                        chat_history_parts.append(f"Assistant (copy_writer): {content}")
                
                if chat_history_parts:
                    chat_history_context = "Recent conversation:\n" + "\n".join(chat_history_parts)
        
        # Add current query to memory using new chat-scoped system
        memory_metadata = {"timestamp": None, "query_type": "copy_writing"}
        
        # Add user metadata to memory metadata if provided
        if user_metadata:
            memory_metadata["user_metadata"] = user_metadata
        if user_image_path:
            memory_metadata["image_path"] = user_image_path
        
        await session_context.append_and_persist_memory(
            "copy_writer",
            f"Copy writing query: {query}",
            memory_metadata
        )
        
        # Also save metadata separately for future reference
        if user_metadata:
            await session_context.append_and_persist_memory(
                "copy_writer",
                f"User metadata context: {json.dumps(user_metadata)}",
                {"context_type": "user_metadata", "timestamp": None}
            )
        if user_image_path:
            await session_context.append_and_persist_memory(
                "copy_writer",
                f"User provided image: {user_image_path}",
                {"context_type": "user_asset", "timestamp": None}
            )

    # Build system prompt for this agent (may raise if registry missing)
    system_prompt = build_system_prompt("copy_writer", str(registry_path),
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
    if copy_writer_memory_context:
        system_prompt += f"\n\n{copy_writer_memory_context}"
    
    # Add chat history context to system prompt if available
    if chat_history_context:
        system_prompt += f"\n\n{chat_history_context}"

    print("=== Copy Writer Agent System Prompt ===")
    print(system_prompt)
    print("=== End System Prompt ===")

    # Single call to the model - no tool usage, no iterations
    if session_context:
        await session_context.send_nano("copy_writer", "generating content…")
        # Save model call to memory
        await session_context.append_and_persist_memory(
            "copy_writer",
            f"Model call: Generating copy content for query",
            {"phase": "content_generation", "query": query[:100]}
        )
    
    raw = await _call_openai_chatmodel(system_prompt, enhanced_query, model_name)
    normalized = await _normalize_model_output(raw)

    if session_context:
        await session_context.send_nano("copy_writer", "content generated")
        # Save model response to memory
        await session_context.append_and_persist_memory(
            "copy_writer",
            f"Model response: {str(normalized)[:200]}...",
            {"phase": "content_generation", "response_type": "final_output"}
        )

    print("=== Copy Writer Agent response ===")
    print(normalized)
    print("=== End response ===")

    try:
        # Parse the JSON response if it's a string, otherwise use as-is
        if isinstance(normalized, str):
            agent_response = json.loads(normalized)
        else:
            agent_response = normalized

        # Save response to memory using new chat-scoped system
        if session_context:
            await session_context.append_and_persist_memory(
                "copy_writer",
                f"Final response: {str(agent_response)[:200]}...",
                {"response_type": "final", "used_tool": None}
            )

        # Return the response directly - no tool usage or iterations
        if isinstance(agent_response, dict):
            return agent_response
        return {"text": str(normalized)}
            
    except json.JSONDecodeError as e:
        error_msg = f"Error parsing copy_writer response as JSON: {e}"
        print(error_msg)
        
        # Use verification tool to diagnose JSON parsing error
        try:
            from tools.verification_tool import diagnose_agent_error
            diagnosis = await diagnose_agent_error(
                agent_name="copy_writer",
                error_message=f"JSON parsing error: {str(e)}",
                agent_query=query,
                agent_output=str(normalized)
            )
            
            if session_context:
                await session_context.send_nano("copy_writer", f"Verification tool diagnosis: {diagnosis.get('analysis', 'No analysis available')}")
            
            # Check if we can retry with prompt fix
            solutions = diagnosis.get('solutions', [])
            retry_solution = next((s for s in solutions if s.get('action') == 'retry_with_prompt_fix'), None)
            
            if retry_solution and retry_solution.get('patch'):
                # Apply prompt fix and retry
                try:
                    fixed_system_prompt = system_prompt + "\n\n" + retry_solution['patch']
                    raw = await _call_openai_chatmodel(fixed_system_prompt, enhanced_query, model_name)
                    normalized = await _normalize_model_output(raw)
                    
                    # Try parsing again
                    if isinstance(normalized, str):
                        agent_response = json.loads(normalized)
                        return agent_response
                    return {"text": str(normalized)}
                except Exception as retry_error:
                    # Retry failed, continue with original error handling
                    pass
            
        except Exception as verification_error:
            # Verification tool failed, continue with original error handling
            pass
        
        if session_context:
            await session_context.send_nano("copy_writer", "Error parsing response as JSON")
        
        return normalized
    except Exception as e:
        error_msg = f"Error in copy_writer: {e}"
        print(error_msg)
        
        # Use verification tool to diagnose general error
        try:
            from tools.verification_tool import diagnose_agent_error
            diagnosis = await diagnose_agent_error(
                agent_name="copy_writer",
                error_message=str(e),
                agent_query=query,
                agent_output=None
            )
            
            if session_context:
                await session_context.send_nano("copy_writer", f"Verification tool diagnosis: {diagnosis.get('analysis', 'No analysis available')}")
            
        except Exception as verification_error:
            # Verification tool failed, continue with original error handling
            pass
        
        if session_context:
            await session_context.send_nano("copy_writer", "Error in copy_writer")
        
        return normalized