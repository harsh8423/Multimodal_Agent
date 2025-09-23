
from typing import Any, Optional
from pathlib import Path
from utils.build_prompts import build_system_prompt
from utils.utility import _call_openai_chatmodel, _normalize_model_output
from utils.session_memory import SessionContext
from utils.mongo_store import save_chat_message

DEFAULT_REGISTRY_FILENAME = "system_prompts.json"

async def asset_agent(query: str, model_name: str = "gpt-5-mini",
                      registry_path: Optional[str] = None, session_context: Optional[SessionContext] = None,
                      max_iterations: int = 5) -> Any:
    """
    Build asset_agent system prompt from registry and call the chat model with the query.
    Prints and returns the model response.
    """
    # Log asset agent start
    if session_context:
        await session_context.add_log("asset_agent_started", f"Asset agent processing query: {query[:100]}...")

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
        await session_context.append_and_persist_memory(
            "asset_agent",
            f"Asset query: {query}",
            {"timestamp": None, "query_type": "asset"}
        )

    system_prompt = build_system_prompt("asset_agent", str(registry_path),
                                        extra_instructions="{place_holder}")
    
    # Add memory context to system prompt if available
    if asset_memory_context:
        system_prompt += f"\n\n{asset_memory_context}"
    
    # Add chat history context to system prompt if available
    if chat_history_context:
        system_prompt += f"\n\n{chat_history_context}"

    # Print system prompt as requested
    print(system_prompt)

    # Log model call
    if session_context:
        await session_context.add_log("model_call", "Asset agent calling model")
        # Save model call decision to memory
        await session_context.append_and_persist_memory(
            "asset_agent",
            f"Model call decision: Processing asset query",
            {"phase": "analysis", "query": query[:100], "agent_type": "asset"}
        )

    raw = await _call_openai_chatmodel(system_prompt, query, model_name)
    normalized = await _normalize_model_output(raw)

    # Log model response
    if session_context:
        await session_context.add_log("model_response", "Asset agent received model response")
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

            if not needs_tool:
                if session_context:
                    await session_context.add_log("no_tool_required", "Asset agent determined no tool needed")
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
                    return agent_state
                return {"text": str(last_normalized)}

            if iteration >= max_iterations:
                warning_msg = f"Max iterations ({max_iterations}) reached in asset_agent; returning best-effort response."
                print(warning_msg)
                if session_context:
                    await session_context.add_log("warning", warning_msg, level="warning")
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
                await session_context.add_log("tool_call", f"Calling tool: {tool_name}")
                await session_context.append_and_persist_memory(
                    "asset_agent",
                    f"Tool call decision: {tool_name} with parameters: {input_schema_fields}",
                    {"phase": "tool_call", "tool_name": tool_name, "parameters": input_schema_fields}
                )

            # Inline import to avoid unused import warnings when no tool calls
            from utils.tool_router import tool_router as _tool_router
            tool_result = _tool_router(tool_name, input_schema_fields)

            if session_context:
                await session_context.add_log("tool_result", f"Tool {tool_name} completed successfully")
                await session_context.append_and_persist_memory(
                    "asset_agent",
                    f"Tool {tool_name} result: {__import__('json').dumps(tool_result, indent=2)[:300]}...",
                    {"phase": "tool_result", "tool_name": tool_name, "success": True, "result_type": "tool_output"}
                )
                if session_context.chat_id:
                    await save_chat_message(
                        chat_id=session_context.chat_id,
                        role="tool",
                        content=__import__('json').dumps(tool_result, indent=2),
                        agent="asset_agent"
                    )

            # Ask model for the next step
            follow_up_query = f"""
            Original asset query: {query}

            Tool used: {tool_name}
            Tool result: {__import__('json').dumps(tool_result, indent=2)}

            Continue executing the plan. If more tool calls are needed, set tool_required true with the next tool and inputs. If finished, set tool_required false and provide final text.
            """

            if session_context:
                await session_context.add_log("model_call", "Asset agent processing tool result")
                await session_context.append_and_persist_memory(
                    "asset_agent",
                    f"Follow-up model call: Processing tool results for next step",
                    {"phase": "follow_up", "tool_name": tool_name, "query": query[:100]}
                )

            next_raw = await _call_openai_chatmodel(system_prompt, follow_up_query, model_name)
            next_normalized = await _normalize_model_output(next_raw)
            last_normalized = next_normalized

            if session_context:
                await session_context.add_log("model_response", "Asset agent iteration response generated")
                await session_context.append_and_persist_memory(
                    "asset_agent",
                    f"Follow-up model response: {str(next_normalized)[:200]}...",
                    {"phase": "follow_up", "response_type": "model_iteration", "tool_name": tool_name}
                )

            print("=== asset_agent iteration response ===")
            print(next_normalized)
            print("=== end asset_agent iteration response ===")

            if isinstance(next_normalized, str):
                try:
                    agent_state = __import__("json").loads(next_normalized)
                except Exception:
                    agent_state = {"tool_required": False, "text": str(next_normalized)}
            else:
                agent_state = next_normalized

            iteration += 1
    except Exception as e:
        # Fall back to returning the first normalized response
        if session_context:
            await session_context.add_log("error", f"Asset agent loop error: {e}", level="error")
        return normalized