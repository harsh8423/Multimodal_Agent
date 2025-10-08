"""
Media Activist Agent - Specialized agent for media generation and enhancement

This agent specializes in generating and enhancing media content including:
- Image generation with detailed prompt enhancement
- Audio generation with text-to-speech capabilities
- Voice cloning using advanced AI models
- Image comparison and improvement suggestions
- Fallback mechanisms for robust media generation

The agent follows the same patterns as research_agent and content_creator for consistency.
"""

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


async def media_activist(query: str, model_name: str = "gpt-5-mini",
                        registry_path: Optional[str] = None, session_context: Optional[SessionContext] = None,
                        max_iterations: int = 5, user_metadata: Optional[Dict] = None, 
                        user_image_path: Optional[str] = None) -> Any:
    """
    Media Activist Agent - Specialized for media generation and enhancement
    
    Capabilities:
    - Image generation with enhanced prompts and quality control
    - Audio generation with text-to-speech (Gemini + Microsoft TTS fallback)
    - Voice cloning using Minimax AI
    - Image comparison and improvement suggestions
    - Metadata handling for all generated media
    
    The agent enhances user queries before calling tools:
    - For image generation: Adds detailed artistic and technical prompts
    - For audio generation: Enhances text with emotional context and voice instructions
    - For voice cloning: Provides clear cloning instructions
    """
    
    # Log media activist start
    if session_context:
        await session_context.send_nano("media_activist", "starting…")

    # Find registry path (default to project root file)
    if registry_path is None:
        registry_path = Path(__file__).parent.parent / DEFAULT_REGISTRY_FILENAME
    else:
        registry_path = Path(registry_path)

    # Get media activist memory context if available
    activist_memory_context = ""
    chat_history_context = ""
    if session_context:
        activist_memory = await session_context.get_agent_memory("media_activist")
        activist_memory_context = await activist_memory.get_context_string()
        
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
                    elif role == "assistant" and agent == "media_activist":
                        chat_history_parts.append(f"Assistant (media_activist): {content}")
                
                if chat_history_parts:
                    chat_history_context = "Recent conversation:\n" + "\n".join(chat_history_parts)
        
        # Add current query to memory
        memory_metadata = {"timestamp": None, "query_type": "media_generation"}
        
        # Add user metadata to memory metadata if provided
        if user_metadata:
            memory_metadata["user_metadata"] = user_metadata
        if user_image_path:
            memory_metadata["image_path"] = user_image_path
        
        await session_context.append_and_persist_memory(
            "media_activist",
            f"Media generation query: {query}",
            memory_metadata
        )
        
        # Also save metadata separately for future reference
        if user_metadata:
            await session_context.append_and_persist_memory(
                "media_activist",
                f"User metadata context: {json.dumps(user_metadata)}",
                {"context_type": "user_metadata", "timestamp": None}
            )
        if user_image_path:
            await session_context.append_and_persist_memory(
                "media_activist",
                f"User provided image: {user_image_path}",
                {"context_type": "user_asset", "timestamp": None}
            )

    # Build system prompt for this agent
    system_prompt = build_system_prompt("media_activist", str(registry_path),
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
    if activist_memory_context:
        system_prompt += f"\n\n{activist_memory_context}"
    
    # Add chat history context to system prompt if available
    if chat_history_context:
        system_prompt += f"\n\n{chat_history_context}"

    print("=== Media Activist System Prompt ===")
    print(system_prompt)
    print("=== End System Prompt ===")

    # First call to the model to determine if tool is required
    if session_context:
        await session_context.send_nano("media_activist", "thinking…")
        # Save model call decision to memory
        await session_context.append_and_persist_memory(
            "media_activist",
            f"Model call decision: Analyzing query for media generation requirements",
            {"phase": "analysis", "query": query[:100]}
        )
    
    raw = await _call_openai_chatmodel(system_prompt, enhanced_query, model_name)
    normalized = await _normalize_model_output(raw)

    if session_context:
        await session_context.send_nano("media_activist", "parsed response")
        # Save model response to memory
        await session_context.append_and_persist_memory(
            "media_activist",
            f"Model analysis response: {str(normalized)[:200]}...",
            {"phase": "analysis", "response_type": "model_analysis"}
        )

    print("=== Initial media_activist response ===")
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
            needs_tool = bool(agent_response.get("tool_required", False)) if isinstance(agent_response, dict) else False

            if not needs_tool:
                # No tool required, return the current response
                if session_context:
                    # Add response to memory
                    await session_context.append_and_persist_memory(
                        "media_activist",
                        f"Direct response (without tool): {str(last_normalized)[:200]}...",
                        {"response_type": "direct", "used_tool": None}
                    )
                    
                    # Save final response to chat with media metadata
                    if session_context.chat_id:
                        # Extract media metadata from final response
                        media_metadata = None
                        if isinstance(last_normalized, dict):
                            media_metadata = {}
                            if last_normalized.get("generated_image_url"):
                                media_metadata["generated_image_url"] = last_normalized["generated_image_url"]
                            if last_normalized.get("audio_url"):
                                media_metadata["audio_url"] = last_normalized["audio_url"]
                            if last_normalized.get("video_url"):
                                media_metadata["video_url"] = last_normalized["video_url"]
                            if last_normalized.get("cloudinary_url"):
                                media_metadata["cloudinary_url"] = last_normalized["cloudinary_url"]
                        
                        await save_chat_message(
                            chat_id=session_context.chat_id,
                            role="assistant",
                            content=str(last_normalized),
                            agent="media_activist",
                            message_type="final_message",
                            meta=media_metadata
                        )
                
                if isinstance(agent_response, dict):
                    return agent_response
                return {"text": str(last_normalized)}

            # Guard against infinite loops
            if iteration >= max_iterations:
                warning_msg = f"Max iterations ({max_iterations}) reached in media_activist; returning best-effort response."
                print(warning_msg)
                if session_context:
                    await session_context.send_nano("media_activist", "Max iterations reached: showing last message")
                return {"text": str(last_normalized)}

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
                await session_context.send_nano("media_activist", f"tool → {tool_name}")
                # Save tool call decision to memory
                await session_context.append_and_persist_memory(
                    "media_activist",
                    f"Tool call decision: {tool_name} with parameters: {input_schema_fields}",
                    {"phase": "tool_call", "tool_name": tool_name, "parameters": input_schema_fields}
                )

            # Call the tool using tool_router
            tool_result = await tool_router(tool_name, input_schema_fields)

            # Log tool result
            if session_context:
                await session_context.send_nano("media_activist", f"tool ✓ {tool_name}")
                # Save tool result to memory
                await session_context.append_and_persist_memory(
                    "media_activist",
                    f"Tool {tool_name} result: {json.dumps(tool_result, indent=2)[:300]}...",
                    {"phase": "tool_result", "tool_name": tool_name, "success": True, "result_type": "tool_output"}
                )
                # Save tool call as message (chat scoped) with media metadata
                if session_context.chat_id:
                    # Extract media metadata from tool result
                    media_metadata = None
                    if isinstance(tool_result, dict):
                        media_metadata = {}
                        if tool_result.get("generated_image_url"):
                            media_metadata["generated_image_url"] = tool_result["generated_image_url"]
                        if tool_result.get("audio_url"):
                            media_metadata["audio_url"] = tool_result["audio_url"]
                        if tool_result.get("video_url"):
                            media_metadata["video_url"] = tool_result["video_url"]
                        if tool_result.get("cloudinary_url"):
                            media_metadata["cloudinary_url"] = tool_result["cloudinary_url"]
                    
                    await save_chat_message(
                        chat_id=session_context.chat_id,
                        role="tool",
                        content=json.dumps(tool_result, indent=2),
                        agent="media_activist",
                        meta=media_metadata
                    )

            # Handle special cases for media generation tools
            if tool_name == "gemini_audio" and isinstance(tool_result, dict) and tool_result.get("success") is False:
                # Gemini audio failed, try Microsoft TTS as fallback
                print(f"=== MEDIA_ACTIVIST: Gemini audio failed, trying Microsoft TTS fallback ===")
                fallback_result = await tool_router("microsoft_tts", input_schema_fields)
                
                if session_context:
                    await session_context.send_nano("media_activist", f"fallback → microsoft_tts")
                    await session_context.append_and_persist_memory(
                        "media_activist",
                        f"Fallback to Microsoft TTS: {json.dumps(fallback_result, indent=2)[:200]}...",
                        {"phase": "fallback", "original_tool": "gemini_audio", "fallback_tool": "microsoft_tts"}
                    )
                
                # Use fallback result
                tool_result = fallback_result
                tool_name = "microsoft_tts"
            
            if tool_name == "kie_image_generation" and isinstance(tool_result, dict):
                # Check if we need to compare with reference image
                if tool_result.get("success") and "generated_image_url" in tool_result:
                    generated_url = tool_result["generated_image_url"]
                    reference_url = input_schema_fields.get("reference_image_url")
                    
                    if reference_url:
                        # Compare generated image with reference
                        comparison_result = await _compare_images(
                            generated_url, reference_url, input_schema_fields.get("prompt", ""), 
                            session_context
                        )
                        
                        if comparison_result.get("similarity_score", 0) < 0.75:
                            # Images don't match well enough, ask for improvements
                            improvement_prompt = comparison_result.get("improvement_suggestions", 
                                                                      "Please improve the generated image to better match the reference.")
                            
                            # Create improvement query
                            improvement_query = f"""
                            The generated image doesn't match the reference well enough (similarity: {comparison_result.get('similarity_score', 0):.2f}).
                            
                            Generated image: {generated_url}
                            Reference image: {reference_url}
                            Original prompt: {input_schema_fields.get('prompt', '')}
                            
                            Improvement suggestions: {improvement_prompt}
                            
                            Please generate an improved version of the image that better matches the reference.
                            """
                            
                            # Update the follow-up query to include improvement request
                            follow_up_query = f"""
                            Original query: {query}

                            Tool used: {tool_name}
                            Tool result: {json.dumps(tool_result, indent=2)}

                            Additional analysis: {json.dumps(comparison_result, indent=2)}

                            Improvement request: {improvement_query}

                            Continue with the improvement process. If more tool calls are needed, set tool_required true with the next tool and inputs. If finished, set tool_required false and provide final text.
                            """
                        else:
                            # Images match well enough, continue normally
                            follow_up_query = f"""
                            Original query: {query}

                            Tool used: {tool_name}
                            Tool result: {json.dumps(tool_result, indent=2)}

                            Image comparison: {json.dumps(comparison_result, indent=2)}

                            Continue executing the plan. If more tool calls are needed, set tool_required true with the next tool and inputs. If finished, set tool_required false and provide final text.
                            """
                    else:
                        # No reference image, continue normally
                        follow_up_query = f"""
                        Original query: {query}

                        Tool used: {tool_name}
                        Tool result: {json.dumps(tool_result, indent=2)}

                        Continue executing the plan. If more tool calls are needed, set tool_required true with the next tool and inputs. If finished, set tool_required false and provide final text.
                        """
                else:
                    # Tool failed or no image generated, continue normally
                    follow_up_query = f"""
                    Original query: {query}

                    Tool used: {tool_name}
                    Tool result: {json.dumps(tool_result, indent=2)}

                    Continue executing the plan. If more tool calls are needed, set tool_required true with the next tool and inputs. If finished, set tool_required false and provide final text.
                    """
            else:
                # Standard follow-up query for other tools
                follow_up_query = f"""
                Original query: {query}

                Tool used: {tool_name}
                Tool result: {json.dumps(tool_result, indent=2)}

                Continue executing the plan using the planner. If more tool calls are needed, set tool_required true with the next tool and inputs. If finished, set tool_required false and provide final text.
                """

            # Call the model again with the tool result
            if session_context:
                await session_context.send_nano("media_activist", "Processing tool result")
                # Save follow-up model call to memory
                await session_context.append_and_persist_memory(
                    "media_activist",
                    f"Follow-up model call: Processing tool results for next step",
                    {"phase": "follow_up", "tool_name": tool_name, "query": query[:100]}
                )

            next_raw = await _call_openai_chatmodel(system_prompt, follow_up_query, model_name)
            next_normalized = await _normalize_model_output(next_raw)
            last_normalized = next_normalized

            if session_context:
                # Save follow-up model response to memory
                await session_context.append_and_persist_memory(
                    "media_activist",
                    f"Follow-up model response: {str(next_normalized)[:200]}...",
                    {"phase": "follow_up", "response_type": "model_iteration", "tool_name": tool_name}
                )

            print("=== Iteration media_activist response ===")
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
            await session_context.send_nano("media_activist", "Error parsing agent response as JSON")
        
        return normalized
    except Exception as e:
        error_msg = f"Error in media_activist: {e}"
        print(error_msg)
        
        if session_context:
            await session_context.send_nano("media_activist", "Error in media_activist")
        
        return normalized


async def _compare_images(generated_url: str, reference_url: str, prompt: str, 
                         session_context: Optional[SessionContext] = None) -> Dict[str, Any]:
    """
    Compare generated image with reference image and provide improvement suggestions.
    
    Args:
        generated_url: URL of the generated image
        reference_url: URL of the reference image
        prompt: Original prompt used for generation
        session_context: Session context for logging
        
    Returns:
        Dictionary containing similarity score and improvement suggestions
    """
    try:
        # Use analyze_image tool to compare both images
        comparison_prompt = f"""
        Compare the generated image with the reference image based on the original prompt: "{prompt}"
        
        Analyze:
        1. Visual similarity (composition, colors, style, objects)
        2. Adherence to the prompt requirements
        3. Quality and artistic merit
        4. Specific areas that need improvement
        
        Provide a similarity score (0-1) and detailed improvement suggestions.
        """
        
        # Call analyze_image tool for comparison
        comparison_result = await tool_router("analyze_image", {
            "system_prompt": "You are an expert image analyst. Return JSON with similarity_score (0-1), improvement_suggestions (list), and detailed_analysis (string).",
            "user_query": comparison_prompt,
            "image_urls": [generated_url, reference_url]
        })
        
        if session_context:
            await session_context.append_and_persist_memory(
                "media_activist",
                f"Image comparison result: {json.dumps(comparison_result, indent=2)[:200]}...",
                {"phase": "image_comparison", "generated_url": generated_url, "reference_url": reference_url}
            )
        
        return comparison_result
        
    except Exception as e:
        print(f"Error in image comparison: {e}")
        return {
            "similarity_score": 0.5,
            "improvement_suggestions": ["Unable to perform detailed comparison due to technical error"],
            "error": str(e)
        }


def enhance_image_prompt(user_prompt: str, style_preferences: Optional[Dict] = None) -> str:
    """
    Enhance user prompt for better image generation results.
    
    Args:
        user_prompt: Original user prompt
        style_preferences: Optional style preferences from user
        
    Returns:
        Enhanced prompt with artistic and technical details
    """
    base_enhancements = [
        "high quality, professional photography",
        "detailed, sharp focus",
        "beautiful lighting",
        "aesthetic composition"
    ]
    
    if style_preferences:
        if style_preferences.get("style"):
            base_enhancements.append(f"in {style_preferences['style']} style")
        if style_preferences.get("mood"):
            base_enhancements.append(f"with {style_preferences['mood']} mood")
        if style_preferences.get("color_scheme"):
            base_enhancements.append(f"using {style_preferences['color_scheme']} color scheme")
    
    enhanced_prompt = f"{user_prompt}, {', '.join(base_enhancements)}"
    return enhanced_prompt


def enhance_audio_prompt(user_text: str, voice_style: Optional[str] = None) -> str:
    """
    Enhance user text for better audio generation results.
    
    Args:
        user_text: Original text to convert to speech
        voice_style: Optional voice style (cheerful, serious, etc.)
        
    Returns:
        Enhanced text with voice instructions
    """
    if voice_style:
        return f"say {voice_style}: {user_text}"
    return user_text