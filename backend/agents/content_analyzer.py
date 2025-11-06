#!/usr/bin/env python3
"""
Content Analyzer Agent

This agent analyzes user content creation requests to understand:
1. User intent and requirements
2. Missing information that needs to be gathered
3. Appropriate workflow type (simple vs complex)
4. Required context and research needs
5. Content specifications and constraints

It acts as an intelligent gatekeeper before content creation begins.
"""

import asyncio
import inspect
import json
from pathlib import Path
from typing import Any, Dict, Optional, List
from utils.build_prompts import build_system_prompt
from utils.utility import chat_model_router, _normalize_model_output
from utils.tool_router import tool_router
from utils.session_memory import SessionContext
from utils.mongo_store import save_chat_message
from config.chat_model_config import get_final_config

DEFAULT_REGISTRY_FILENAME = "system_prompts.json"


async def content_analyzer(query: str, model_name: Optional[str] = None, chat_llm_model: Optional[str] = None,
                          registry_path: Optional[str] = None, session_context: Optional[SessionContext] = None,
                          max_iterations: int = 3, user_metadata: Optional[Dict] = None, 
                          user_image_path: Optional[str] = None) -> Any:
    """
    Content Analyzer Agent - Analyzes user content creation requests intelligently.
    
    Capabilities:
    - Analyze user intent and extract requirements
    - Identify missing information and context needs
    - Determine appropriate workflow complexity
    - Suggest research and reference gathering needs
    - Provide intelligent recommendations for next steps
    
    The agent focuses on:
    - Understanding what the user actually wants
    - Identifying gaps in information
    - Recommending appropriate workflow paths
    - Gathering context before content creation
    """
    # Get chat model configuration from central config
    config = get_final_config(agent_name="content_analyzer")
    
    # Use provided parameters or fall back to config
    final_model_name = model_name or config["model_name"]
    final_chat_llm_model = chat_llm_model or config["chat_llm_model"]
    
    # Log content analyzer start
    if session_context:
        await session_context.send_nano("content_analyzer", "analyzing content request…")

    # Find registry path (default to project root file)
    if registry_path is None:
        registry_path = Path(__file__).parent.parent / DEFAULT_REGISTRY_FILENAME
    else:
        registry_path = Path(registry_path)

    # Get content analyzer memory context if available
    analyzer_memory_context = ""
    chat_history_context = ""
    if session_context:
        analyzer_memory = await session_context.get_agent_memory("content_analyzer")
        analyzer_memory_context = await analyzer_memory.get_context_string()
        
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
                    elif role == "assistant" and agent == "content_analyzer":
                        chat_history_parts.append(f"Assistant (content_analyzer): {content}")
                
                if chat_history_parts:
                    chat_history_context = "Recent conversation:\n" + "\n".join(chat_history_parts)
        
        # Add current query to memory using new chat-scoped system
        memory_metadata = {"timestamp": None, "query_type": "content_analysis"}
        
        # Add user metadata to memory metadata if provided
        if user_metadata:
            memory_metadata["user_metadata"] = user_metadata
        if user_image_path:
            memory_metadata["image_path"] = user_image_path
        
        await session_context.append_and_persist_memory(
            "content_analyzer",
            f"Content analysis query: {query}",
            memory_metadata
        )
        
        # Also save metadata separately for future reference
        if user_metadata:
            await session_context.append_and_persist_memory(
                "content_analyzer",
                f"User metadata context: {json.dumps(user_metadata)}",
                {"context_type": "user_metadata", "timestamp": None}
            )
        if user_image_path:
            await session_context.append_and_persist_memory(
                "content_analyzer",
                f"User provided image: {user_image_path}",
                {"context_type": "user_asset", "timestamp": None}
            )

    # Build system prompt
    system_prompt = f"""You are CONTENT ANALYZER — an intelligent agent that analyzes user content creation requests to understand intent, requirements, and workflow needs.

{analyzer_memory_context}

{chat_history_context}

CORE RESPONSIBILITIES:
1. **Intent Analysis**: Understand what the user actually wants to create
2. **Requirement Extraction**: Identify specific requirements, constraints, and preferences
3. **Gap Analysis**: Determine what information is missing or needs clarification
4. **Workflow Recommendation**: Suggest appropriate workflow complexity and approach
5. **Context Gathering**: Identify what research, references, or brand information is needed
6. **Smart Routing**: Recommend whether to proceed with simple creation or complex planning

ANALYSIS FRAMEWORK:
- **Content Type**: What type of content (post, reel, carousel, video, etc.)
- **Platform**: Target platform(s) and their specific requirements
- **Purpose**: Marketing goal, audience, message, call-to-action
- **Brand Context**: Brand voice, style, existing assets, templates
- **References**: Examples, inspiration, competitor content
- **Constraints**: Timeline, budget, technical limitations
- **Missing Info**: What critical information is not provided

DECISION LOGIC:
- **Simple Requests**: Clear requirements, minimal context needed → Direct to appropriate agent
- **Complex Requests**: Multiple platforms, unclear requirements, needs research → Recommend planning workflow
- **Incomplete Requests**: Missing critical information → Ask clarifying questions first
- **Research Needed**: No brand context, no references, no clear direction → Recommend research phase

OUTPUT SCHEMA (return ONLY JSON):
{{
  "analysis": {{
    "content_type": "string (detected content type)",
    "platform": "string (target platform)",
    "intent": "string (what user wants to achieve)",
    "complexity": "simple|moderate|complex",
    "completeness": "complete|partial|incomplete"
  }},
  "requirements": {{
    "clear_requirements": ["list of clearly stated requirements"],
    "missing_requirements": ["list of missing critical information"],
    "optional_requirements": ["list of nice-to-have information"]
  }},
  "recommendations": {{
    "workflow_type": "direct_creation|planning_workflow|research_first",
    "next_steps": ["recommended next actions"],
    "clarifying_questions": ["questions to ask user if needed"],
    "research_needs": ["what research/references are needed"]
  }},
  "context_needs": {{
    "brand_info": "boolean (needs brand context)",
    "references": "boolean (needs examples/inspiration)",
    "research": "boolean (needs topic research)",
    "competitor_analysis": "boolean (needs competitor insights)"
  }},
  "routing": {{
    "agent_required": "boolean",
    "agent_name": "string (if agent_required true)",
    "agent_query": "string (if agent_required true)",
    "reasoning": "string (why this routing decision)"
  }}
}}

EXAMPLES:

User: "Create an Instagram post about our new product"
Analysis: {{
  "analysis": {{
    "content_type": "image_post",
    "platform": "instagram", 
    "intent": "product promotion",
    "complexity": "moderate",
    "completeness": "incomplete"
  }},
  "requirements": {{
    "clear_requirements": ["Instagram post", "new product"],
    "missing_requirements": ["product details", "brand voice", "target audience", "call-to-action"],
    "optional_requirements": ["visual style preferences", "hashtag strategy"]
  }},
  "recommendations": {{
    "workflow_type": "research_first",
    "next_steps": ["Gather product information", "Define brand voice", "Research target audience"],
    "clarifying_questions": ["What is the new product?", "Who is your target audience?", "What action should users take?"],
    "research_needs": ["product details", "brand guidelines", "audience insights"]
  }},
  "context_needs": {{
    "brand_info": true,
    "references": true,
    "research": true,
    "competitor_analysis": false
  }},
  "routing": {{
    "agent_required": true,
    "agent_name": "todo_planner",
    "agent_query": "Create a comprehensive content creation plan for Instagram product post. Need to gather: product details, brand voice, target audience, and visual references first.",
    "reasoning": "Incomplete requirements require structured planning workflow"
  }}
}}

User: "Generate a 30-second reel with this script: 'Welcome to our channel...'"
Analysis: {{
  "analysis": {{
    "content_type": "reel",
    "platform": "instagram",
    "intent": "channel introduction",
    "complexity": "simple",
    "completeness": "complete"
  }},
  "requirements": {{
    "clear_requirements": ["30-second reel", "provided script", "channel introduction"],
    "missing_requirements": [],
    "optional_requirements": ["visual style", "music preferences"]
  }},
  "recommendations": {{
    "workflow_type": "direct_creation",
    "next_steps": ["Generate visuals", "Add audio", "Create final reel"],
    "clarifying_questions": [],
    "research_needs": []
  }},
  "context_needs": {{
    "brand_info": false,
    "references": false,
    "research": false,
    "competitor_analysis": false
  }},
  "routing": {{
    "agent_required": true,
    "agent_name": "copy_writer",
    "agent_query": "Create Instagram reel content with provided script: 'Welcome to our channel...'",
    "reasoning": "Clear requirements allow direct content creation"
  }}
}}

CRITICAL RULES:
1. Always analyze the completeness of the request
2. Identify missing critical information
3. Recommend appropriate workflow complexity
4. Ask clarifying questions when needed
5. Route to appropriate agent based on analysis
6. Return ONLY the JSON schema above
"""

    # Add memory context to system prompt if available
    if analyzer_memory_context:
        system_prompt += f"\n\n{analyzer_memory_context}"
    
    # Add chat history context to system prompt if available
    if chat_history_context:
        system_prompt += f"\n\n{chat_history_context}"

    print("=== Content Analyzer System Prompt ===")
    print(system_prompt)
    print("=== End System Prompt ===")

    # First call to the model to analyze the request
    if session_context:
        await session_context.send_nano("content_analyzer", "analyzing user request…")
        # Save model call decision to memory
        await session_context.append_and_persist_memory(
            "content_analyzer",
            f"Analyzing content request: {query[:100]}",
            {"phase": "analysis", "query": query[:100]}
        )
    
    raw = await chat_model_router(system_prompt, query, final_chat_llm_model, final_model_name)
    normalized = await _normalize_model_output(raw)

    if session_context:
        await session_context.send_nano("content_analyzer", "analysis complete")
        # Save model response to memory
        await session_context.append_and_persist_memory(
            "content_analyzer",
            f"Analysis complete: {str(normalized)[:200]}...",
            {"phase": "analysis", "response_type": "analysis_complete"}
        )

    print("=== Content Analyzer response ===")
    print(normalized)
    print("=== End response ===")

    try:
        # Parse the JSON response if it's a string, otherwise use as-is
        if isinstance(normalized, str):
            agent_state = json.loads(normalized)
        else:
            agent_state = normalized

        # Content analyzer typically doesn't need multiple iterations
        # It analyzes once and provides routing recommendations
        
        if session_context:
            await session_context.append_and_persist_memory(
                "content_analyzer",
                f"Final analysis result: {str(agent_state)[:300]}...",
                {"phase": "final", "analysis_complete": True}
            )

        return agent_state

    except Exception as e:
        error_msg = f"Content analyzer error: {e}"
        if session_context:
            await session_context.send_nano("content_analyzer", "analysis error")
        
        return {
            "analysis": {
                "content_type": "unknown",
                "platform": "unknown",
                "intent": "unclear",
                "complexity": "complex",
                "completeness": "incomplete"
            },
            "requirements": {
                "clear_requirements": [],
                "missing_requirements": ["Unable to analyze request"],
                "optional_requirements": []
            },
            "recommendations": {
                "workflow_type": "research_first",
                "next_steps": ["Please clarify your content creation request"],
                "clarifying_questions": ["What type of content do you want to create?"],
                "research_needs": ["content requirements"]
            },
            "context_needs": {
                "brand_info": True,
                "references": True,
                "research": True,
                "competitor_analysis": False
            },
            "routing": {
                "agent_required": False,
                "agent_name": "",
                "agent_query": "",
                "reasoning": f"Analysis failed: {error_msg}"
            }
        }