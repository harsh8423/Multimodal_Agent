"""
Verification Tool - Comprehensive error diagnosis and solution generation for agent/tool execution failures.

This tool analyzes failed or suspicious agent/tool executions and provides:
- Root cause analysis with confidence scores
- Prioritized remediation actions
- Automated fix suggestions
- Safety warnings for sensitive operations
"""

import json
import asyncio
from typing import Any, Dict, List, Optional, Union
from models.chat_openai import orchestrator_function as openai_chatmodel


async def verification_tool(
    planner_step: Optional[Dict[str, Any]] = None,
    agent_name: Optional[str] = None,
    agent_capabilities: Optional[Union[List[str], Dict[str, Any]]] = None,
    tool_name: Optional[str] = None,
    tool_input_schema: Optional[Dict[str, Any]] = None,
    tool_capabilities: Optional[Dict[str, Any]] = None,
    agent_query: Optional[str] = None,
    tool_call_payload: Optional[Dict[str, Any]] = None,
    tool_response: Optional[Dict[str, Any]] = None,
    error_details: Optional[Union[Dict[str, Any], str]] = None,
    agent_output: Optional[Union[Dict[str, Any], str]] = None,
    agent_context: Optional[List[str]] = None,
    previous_attempts: Optional[List[Dict[str, Any]]] = None,
    available_agents: Optional[List[str]] = None,
    available_tools: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Comprehensive verification tool that diagnoses agent/tool execution issues and provides solutions.
    
    Args:
        planner_step: The orchestrator step/agent step that invoked the agent/tool
        agent_name: Name of the agent that failed
        agent_capabilities: Capabilities of the agent (list or dict)
        tool_name: Name of the tool that failed
        tool_input_schema: Expected input schema for the tool
        tool_capabilities: Capabilities of the tool
        agent_query: The prompt/arguments the agent sent
        tool_call_payload: The exact JSON/args sent to the tool
        tool_response: What the tool returned (success or error)
        error_details: Stack trace, error code, status, latency, retries
        agent_output: What the agent produced as output
        agent_context: Short chronological log lines
        previous_attempts: Prior attempts and fixes tried
        available_agents: List of available agents for routing suggestions
        available_tools: List of available tools for fallback suggestions
        
    Returns:
        Dict containing diagnosis, issues, solutions, and next steps
    """
    
    # Build the verification prompt
    verification_prompt = build_verification_prompt(
        planner_step=planner_step,
        agent_name=agent_name,
        agent_capabilities=agent_capabilities,
        tool_name=tool_name,
        tool_input_schema=tool_input_schema,
        tool_capabilities=tool_capabilities,
        agent_query=agent_query,
        tool_call_payload=tool_call_payload,
        tool_response=tool_response,
        error_details=error_details,
        agent_output=agent_output,
        agent_context=agent_context,
        previous_attempts=previous_attempts,
        available_agents=available_agents,
        available_tools=available_tools
    )
    
    try:
        # Call the LLM for diagnosis
        response = await openai_chatmodel(
            messages=[{"role": "system", "content": verification_prompt}],
            model="gpt-4",
            temperature=0.1,  # Low temperature for consistent, deterministic analysis
            max_tokens=2000
        )
        
        # Parse the response
        if isinstance(response, str):
            try:
                diagnosis = json.loads(response)
            except json.JSONDecodeError:
                # If response is not JSON, wrap it in a structured format
                diagnosis = {
                    "analysis": response,
                    "issues": [],
                    "solutions": [],
                    "next_steps": [],
                    "safety_warnings": []
                }
        else:
            diagnosis = response
            
        # Ensure required fields exist
        diagnosis.setdefault("issues", [])
        diagnosis.setdefault("solutions", [])
        diagnosis.setdefault("next_steps", [])
        diagnosis.setdefault("safety_warnings", [])
        
        return diagnosis
        
    except Exception as e:
        # Fallback error handling
        return {
            "analysis": f"Verification tool failed to analyze the issue: {str(e)}",
            "issues": [
                {
                    "type": "verification_tool_failure",
                    "description": f"Verification tool encountered an error: {str(e)}",
                    "severity": "high",
                    "confidence": 1.0,
                    "evidence": f"Exception: {str(e)}"
                }
            ],
            "solutions": [
                {
                    "action": "raise_error_to_user",
                    "description": "Manual intervention required - verification system failed",
                    "patch": None,
                    "priority": 1
                }
            ],
            "next_steps": [
                "Check verification tool logs",
                "Verify LLM API connectivity",
                "Review input parameters for completeness"
            ],
            "safety_warnings": [
                "Verification tool failure may indicate system instability"
            ]
        }


def build_verification_prompt(
    planner_step: Optional[Dict[str, Any]] = None,
    agent_name: Optional[str] = None,
    agent_capabilities: Optional[Union[List[str], Dict[str, Any]]] = None,
    tool_name: Optional[str] = None,
    tool_input_schema: Optional[Dict[str, Any]] = None,
    tool_capabilities: Optional[Dict[str, Any]] = None,
    agent_query: Optional[str] = None,
    tool_call_payload: Optional[Dict[str, Any]] = None,
    tool_response: Optional[Dict[str, Any]] = None,
    error_details: Optional[Union[Dict[str, Any], str]] = None,
    agent_output: Optional[Union[Dict[str, Any], str]] = None,
    agent_context: Optional[List[str]] = None,
    previous_attempts: Optional[List[Dict[str, Any]]] = None,
    available_agents: Optional[List[str]] = None,
    available_tools: Optional[List[str]] = None
) -> str:
    """Build the comprehensive verification prompt for the LLM."""
    
    prompt = """You are VERIFICATION_TOOL — a focused, safety-first LLM whose job is to inspect a failed or suspicious agent/tool execution and produce precise diagnostics, prioritized root causes, and concrete remediation actions. You get only the data provided in the request. Do not invent facts, do not call external services, and do not perform any action besides proposing fixes. Be concise, deterministic, and actionable.

ANALYSIS RULES (must follow):
- Use only the provided data. If something critical is missing for diagnosis, state that and ask the single most critical follow-up question.
- Prefer minimal, conservative changes that fix the immediate failure rather than large rearchitecting suggestions.
- If recommending a different agent/tool, include which of the provided available_agents fits and why (match capabilities).
- When recommending prompt improvements, give a before/after prompt snippet and a one-line rationale.
- When correcting an input schema mismatch, provide the corrected JSON with exact key names and types. Indicate whether fields are optional/required.
- Give a numeric confidence (0.0–1.0) for each issue you identify.
- Classify severity as critical (blocks user or may leak data), high (major failure), medium (degrades quality), low (minor or cosmetic).
- If tool response included an error code (e.g., 401, 403, 429, 500), map common causes and exact remediation (credentials, rate limit, transient retry, parameter fix).
- If the agent called the wrong agent/tool (capability mismatch), explain precisely which capability was misjudged and list concrete candidate agents/tools to use instead (from available_agents).

AVAILABLE ACTIONS:
- auto_fix_and_retry (safest, small change you can propose)
- retry_with_prompt_fix (improve prompt/args)
- correct_input_schema (map/fix parameter names/types)
- route_to_agent (recommend a better agent and why)
- fallback_tool (recommend alternate tool)
- require_user_input (ask user for missing field; provide exact question)
- raise_error_to_user (expose issue to user with suggested wording)
- abort (do not retry; manual intervention required)

OUTPUT FORMAT (return valid JSON only):
{
  "analysis": "Brief summary of what went wrong and why",
  "issues": [
    {
      "type": "issue_category",
      "description": "Detailed description of the issue",
      "severity": "critical|high|medium|low",
      "confidence": 0.0-1.0,
      "evidence": "Specific log/tool snippet or reasoning that supports this diagnosis"
    }
  ],
  "solutions": [
    {
      "action": "one_of_the_available_actions",
      "description": "What this action will accomplish",
      "patch": "exact JSON patch or replacement snippet (null if not applicable)",
      "priority": 1-5
    }
  ],
  "next_steps": [
    "Step 1: specific actionable item",
    "Step 2: specific actionable item",
    "Step 3: specific actionable item"
  ],
  "safety_warnings": [
    "Warning about data exposure, permissions, or irreversible actions"
  ]
}

INPUT DATA TO ANALYZE:
"""
    
    # Add all provided data to the prompt
    if planner_step:
        prompt += f"\nPLANNER_STEP: {json.dumps(planner_step, indent=2)}"
    
    if agent_name:
        prompt += f"\nAGENT_NAME: {agent_name}"
    
    if agent_capabilities:
        prompt += f"\nAGENT_CAPABILITIES: {json.dumps(agent_capabilities, indent=2)}"
    
    if tool_name:
        prompt += f"\nTOOL_NAME: {tool_name}"
    
    if tool_input_schema:
        prompt += f"\nTOOL_INPUT_SCHEMA: {json.dumps(tool_input_schema, indent=2)}"
    
    if tool_capabilities:
        prompt += f"\nTOOL_CAPABILITIES: {json.dumps(tool_capabilities, indent=2)}"
    
    if agent_query:
        prompt += f"\nAGENT_QUERY: {agent_query}"
    
    if tool_call_payload:
        prompt += f"\nTOOL_CALL_PAYLOAD: {json.dumps(tool_call_payload, indent=2)}"
    
    if tool_response:
        prompt += f"\nTOOL_RESPONSE: {json.dumps(tool_response, indent=2)}"
    
    if error_details:
        prompt += f"\nERROR_DETAILS: {json.dumps(error_details, indent=2) if isinstance(error_details, dict) else error_details}"
    
    if agent_output:
        prompt += f"\nAGENT_OUTPUT: {json.dumps(agent_output, indent=2) if isinstance(agent_output, dict) else agent_output}"
    
    if agent_context:
        prompt += f"\nAGENT_CONTEXT: {json.dumps(agent_context, indent=2)}"
    
    if previous_attempts:
        prompt += f"\nPREVIOUS_ATTEMPTS: {json.dumps(previous_attempts, indent=2)}"
    
    if available_agents:
        prompt += f"\nAVAILABLE_AGENTS: {json.dumps(available_agents, indent=2)}"
    
    if available_tools:
        prompt += f"\nAVAILABLE_TOOLS: {json.dumps(available_tools, indent=2)}"
    
    prompt += "\n\nAnalyze the above data and provide your diagnosis in the specified JSON format."
    
    return prompt


# Synchronous wrapper for compatibility
def verification_tool_sync(
    planner_step: Optional[Dict[str, Any]] = None,
    agent_name: Optional[str] = None,
    agent_capabilities: Optional[Union[List[str], Dict[str, Any]]] = None,
    tool_name: Optional[str] = None,
    tool_input_schema: Optional[Dict[str, Any]] = None,
    tool_capabilities: Optional[Dict[str, Any]] = None,
    agent_query: Optional[str] = None,
    tool_call_payload: Optional[Dict[str, Any]] = None,
    tool_response: Optional[Dict[str, Any]] = None,
    error_details: Optional[Union[Dict[str, Any], str]] = None,
    agent_output: Optional[Union[Dict[str, Any], str]] = None,
    agent_context: Optional[List[str]] = None,
    previous_attempts: Optional[List[Dict[str, Any]]] = None,
    available_agents: Optional[List[str]] = None,
    available_tools: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Synchronous wrapper for the verification tool."""
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(verification_tool(
            planner_step=planner_step,
            agent_name=agent_name,
            agent_capabilities=agent_capabilities,
            tool_name=tool_name,
            tool_input_schema=tool_input_schema,
            tool_capabilities=tool_capabilities,
            agent_query=agent_query,
            tool_call_payload=tool_call_payload,
            tool_response=tool_response,
            error_details=error_details,
            agent_output=agent_output,
            agent_context=agent_context,
            previous_attempts=previous_attempts,
            available_agents=available_agents,
            available_tools=available_tools
        ))
    except RuntimeError:
        # If no event loop is running, create a new one
        return asyncio.run(verification_tool(
            planner_step=planner_step,
            agent_name=agent_name,
            agent_capabilities=agent_capabilities,
            tool_name=tool_name,
            tool_input_schema=tool_input_schema,
            tool_capabilities=tool_capabilities,
            agent_query=agent_query,
            tool_call_payload=tool_call_payload,
            tool_response=tool_response,
            error_details=error_details,
            agent_output=agent_output,
            agent_context=agent_context,
            previous_attempts=previous_attempts,
            available_agents=available_agents,
            available_tools=available_tools
        ))


# Helper function to extract available agents and tools from registry
def get_available_agents_and_tools() -> tuple[List[str], List[str]]:
    """Extract available agents and tools from the agent registry."""
    try:
        from utils.agent_registry import get_registry
        
        registry = get_registry()
        available_agents = list(registry.get("agents", {}).keys())
        available_tools = list(registry.get("tools", {}).keys())
        
        return available_agents, available_tools
    except Exception:
        # Fallback if registry is not available
        return [], []


# Convenience function for common error scenarios
async def diagnose_agent_error(
    agent_name: str,
    error_message: str,
    agent_query: str,
    agent_output: Optional[str] = None,
    tool_name: Optional[str] = None,
    tool_response: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convenience function for diagnosing common agent errors.
    
    Args:
        agent_name: Name of the agent that failed
        error_message: Error message or details
        agent_query: The query sent to the agent
        agent_output: Output from the agent (if any)
        tool_name: Name of tool that was called (if any)
        tool_response: Response from the tool (if any)
        
    Returns:
        Diagnosis results
    """
    available_agents, available_tools = get_available_agents_and_tools()
    
    return await verification_tool(
        agent_name=agent_name,
        agent_query=agent_query,
        error_details=error_message,
        agent_output=agent_output,
        tool_name=tool_name,
        tool_response=tool_response,
        available_agents=available_agents,
        available_tools=available_tools
    )


# Convenience function for tool errors
async def diagnose_tool_error(
    tool_name: str,
    tool_call_payload: Dict[str, Any],
    tool_response: Dict[str, Any],
    error_details: str
) -> Dict[str, Any]:
    """
    Convenience function for diagnosing tool execution errors.
    
    Args:
        tool_name: Name of the tool that failed
        tool_call_payload: Parameters sent to the tool
        tool_response: Response from the tool
        error_details: Error details
        
    Returns:
        Diagnosis results
    """
    available_agents, available_tools = get_available_agents_and_tools()
    
    return await verification_tool(
        tool_name=tool_name,
        tool_call_payload=tool_call_payload,
        tool_response=tool_response,
        error_details=error_details,
        available_agents=available_agents,
        available_tools=available_tools
    )