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

async def orchestrator(
    message: Dict[str, Any],
    websocket,
    model_name: str = "gpt-5-mini",
    session_context: Optional[SessionContext] = None,
    max_iterations: int = 5,
    *,
    debug: bool = False,
) -> Dict[str, Any]:
    user_text = ""
    if isinstance(message, dict):
        parts = []
        if "text" in message and message["text"]:
            parts.append(str(message["text"]).strip())
        if "image_path" in message and message["image_path"]:
            parts.append(f"[image_saved_at:{message['image_path']}]")
        if "metadata" in message and isinstance(message["metadata"], dict):
            md_sample = ", ".join(f"{k}={v}" for k, v in message["metadata"].items())
            if md_sample:
                parts.append(f"[meta:{md_sample}]")
        user_text = "\n".join(parts).strip()

    if not user_text:
        user_text = "(empty user message)"

    # near top, after building user_text
    if user_text == "(empty user message)":
        # Log and skip — do not call the model
        if session_context:
            await session_context.send_nano("orchestrator", "Received empty user message")
        return {"agent_required": False, "self_response": ""}


    # Get orchestrator memory context if available
    orchestrator_memory_context = ""
    chat_history_context = ""
    if session_context:
        orchestrator_memory = await session_context.get_agent_memory("orchestrator")
        # Sanitize memory to remove control-only frames (e.g., chat_id payloads)
        try:
            entries = await orchestrator_memory.get_all()
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
                orchestrator_memory_context = "Recent orchestrator memory:\n" + "\n".join(filtered_lines)
            else:
                orchestrator_memory_context = ""
        except Exception:
            # Fallback to raw context if anything goes wrong
            orchestrator_memory_context = await orchestrator_memory.get_context_string()
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
        
        # Add memory to orchestrator memory using new chat-scoped system, but avoid logging pure control frames
        try:
            is_control = False
            if isinstance(message, dict) and "chat_id" in message and not message.get("text") and not message.get("image"):
                is_control = True
            if not is_control:
                await session_context.append_and_persist_memory(
                    "orchestrator",
                    f"User query: {user_text}",
                    {"timestamp": message.get("timestamp"), "has_image": "image_path" in message}
                )
        except Exception:
            pass

    # Build the system prompt using the registry
    try:
        registry_path = Path(__file__).parent.parent / "system_prompts.json"
        system_prompt = build_system_prompt("orchestrator", str(registry_path))
        
        # Add memory context to system prompt if available
        if orchestrator_memory_context:
            system_prompt += f"\n\n{orchestrator_memory_context}"
        
        # Add chat history context to system prompt if available
        if chat_history_context:
            system_prompt += f"\n\n{chat_history_context}"
            
        # Print system prompt as requested
        print(system_prompt)
    except Exception as e:
        # Fallback to a simple prompt if registry fails
        system_prompt = (
            "You are an intelligent orchestrator. Analyze the user query and respond with JSON: "
            "{\"agent_required\": boolean, \"self_response\": \"string if false\", "
            "\"agent_name\": \"research_agent or asset_agent if true\", \"agent_query\": \"string if true\"}"
        )
        
        if session_context:
            await session_context.send_nano("orchestrator","Failed to load orchestrator prompt")

    # Call the orchestration model safely (async or threaded)
    try:
        if session_context:
            await session_context.send_nano("orchestrator", "thinking…")
        
        raw = await _call_openai_chatmodel(system_prompt, user_text, model_name)
        # If the chat model itself returned an awaitable for some reason, ensure resolution
        raw = await _maybe_await(raw)
        
        if session_context:
            # Nano: model responded
            await session_context.send_nano("orchestrator", "parsed response")
            
    except Exception as e:
        error_msg = f"Error calling model: {e}"
        if session_context:
            await session_context.send_nano("orchestrator", "Error calling model")
        
        fallback = {
            "agent_required": False,
            "self_response": error_msg,
        }
        await websocket.send_json({"text": fallback["self_response"]})
        return fallback

    # Normalize raw -> dict
    def _normalize_orchestration(val: Any) -> Dict[str, Any]:
        if isinstance(val, dict):
            return val
        if isinstance(val, str):
            try:
                return json.loads(val)
            except Exception:
                return {"agent_required": False, "self_response": val}
        return {"agent_required": False, "self_response": str(val)}

    orchestration = _normalize_orchestration(raw)

    iteration = 0
    last_text = ""

    while True:
        agent_required = bool(orchestration.get("agent_required", False))
        if not agent_required:
            self_response = orchestration.get("self_response", orchestration.get("text", ""))
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
                await session_context.send_nano("orchestrator", "answer ready")

            if session_context:
                await session_context.append_and_persist_memory(
                    "orchestrator",
                    f"Orchestrator response: {self_response}",
                    {"response_type": "direct", "timestamp": message.get("timestamp")}
                )
                if session_context.chat_id:
                    await save_chat_message(
                        chat_id=session_context.chat_id,
                        role="assistant",
                        content=self_response,
                        agent="orchestrator",
                        message_type="final_message"
                    )
                    # log persistence removed

            await websocket.send_json({"text": self_response})
            print(f"[orchestrator-response] {self_response}")

            return {"agent_required": False, "self_response": self_response}

        # Guard against infinite loops
        if iteration >= max_iterations:
            warning_msg = f"Max iterations ({max_iterations}) reached in orchestrator; returning best-effort response."
            print(warning_msg)
            if session_context:
                await session_context.send_nano("orchestrator", "Max Iterations Reached showing last message")
            fallback_text = orchestration.get("self_response") or last_text or "Max iterations reached."
            await websocket.send_json({"text": fallback_text})
            return {"agent_required": False, "self_response": fallback_text}

        agent_name = orchestration.get("agent_name", "").strip()
        # Nano: routing information
        if session_context and agent_name:
            await session_context.send_nano("orchestrator", f"routing → {agent_name}")
        agent_query = orchestration.get("agent_query", "").strip()

        if agent_name not in ("research_agent", "asset_agent", "media_analyst"):  ##### To be made dynamic later 
            err_msg = f"Unknown agent requested: '{agent_name}'."
            if session_context:
                await session_context.send_nano("orchestrator", err_msg)
            await websocket.send_json({"text": err_msg})
            return {"agent_required": False, "self_response": err_msg}

        if not agent_query:
            err_msg = "Agent requested but no agent_query provided."
            if session_context:
                await session_context.send_nano("orchestrator", err_msg)
            await websocket.send_json({"text": err_msg})
            return {"agent_required": False, "self_response": err_msg}

        if session_context:
            
            await session_context.append_and_persist_memory(
                "orchestrator",
                f"Routing decision: {agent_name} for query: {agent_query}",
                {"agent_name": agent_name, "query": agent_query, "decision_type": "routing"}
            )
            

        await websocket.send_json({
            "text": f"Routing to {agent_name}...",
            "agent_required": True,
            "agent_name": agent_name,
            "agent_query": agent_query
        })

        result = await call_agent(agent_name, agent_query, model_name, registry_path, session_context)

        if session_context:
            await session_context.send_nano("orchestrator", f"{agent_name} finished the task")
            await session_context.append_and_persist_memory(
                agent_name,
                f"Agent response: {str(result)}",
                {"response_type": "final", "query": agent_query, "timestamp": message.get("timestamp")}
            )
            await session_context.append_and_persist_memory(
                "orchestrator",
                f"Agent {agent_name} completed with response: {str(result)[:200]}...",
                {"agent_name": agent_name, "query": agent_query, "response_type": "agent_completion"}
            )
            if session_context.chat_id:
                await save_chat_message(
                    chat_id=session_context.chat_id,
                    role="assistant",
                    content=str(result),
                    agent=agent_name,
                    message_type="final_message"
                )

        try:
            agent_text = result.get("text", "") if isinstance(result, dict) else str(result)
            last_text = agent_text or last_text
            if agent_text:
                print(f"[agent-response:{agent_name}] {agent_text}")
        except Exception:
            pass

        # await websocket.send_json({
        #     "text": result.get("text", "") if isinstance(result, dict) else str(result),
        #     "agent_required": True,
        #     "agent_name": agent_name,
        #     "agent_query": agent_query
        # })

        # Ask model to continue planner with the new agent result
        follow_up_query = (
            f"Original user message: {user_text}\n\n"
            f"Agent used: {agent_name}\n"
            f"Agent result: {json.dumps(result)}\n\n"
            "Continue executing the plan using the planner. If more agent work is required, set agent_required true with the next agent and a concise agent_query. If finished, set agent_required false and provide self_response."
        )

        if session_context:
            await session_context.send_nano("orchestrator", f"Processing {agent_name} result")
            await session_context.append_and_persist_memory(
                "orchestrator",
                "Follow-up model call: Processing agent results for next step",
                {"phase": "follow_up", "agent_name": agent_name}
            )

        raw = await _call_openai_chatmodel(system_prompt, follow_up_query, model_name)
        raw = await _maybe_await(raw)
        orchestration = _normalize_orchestration(raw)
        iteration += 1

