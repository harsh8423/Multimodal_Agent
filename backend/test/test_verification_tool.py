"""
Test script for the verification tool integration.
Tests various error scenarios and verifies the tool provides appropriate diagnoses and solutions.
"""

import asyncio
import json
from tools.verification_tool import verification_tool, diagnose_agent_error, diagnose_tool_error


async def test_schema_mismatch_error():
    """Test verification tool with a schema mismatch error."""
    print("=== Testing Schema Mismatch Error ===")
    
    diagnosis = await diagnose_tool_error(
        tool_name="kie_image_generation",
        tool_call_payload={
            "prompt": "A beautiful sunset",
            "size": "1024x1024"  # Wrong parameter name
        },
        tool_response={
            "error": "invalid_param",
            "param": "size",
            "message": "Parameter 'size' not recognized. Expected 'image_size'"
        },
        error_details="Schema mismatch: tool expects 'image_size' but received 'size'"
    )
    
    print("Diagnosis:", json.dumps(diagnosis, indent=2))
    
    # Verify the diagnosis contains expected elements
    assert "analysis" in diagnosis
    assert "issues" in diagnosis
    assert "solutions" in diagnosis
    
    # Check if it identified the schema mismatch
    issues = diagnosis.get("issues", [])
    schema_issue = next((i for i in issues if "schema" in i.get("type", "").lower()), None)
    assert schema_issue is not None, "Should identify schema mismatch issue"
    
    # Check if it provides a fix
    solutions = diagnosis.get("solutions", [])
    fix_solution = next((s for s in solutions if s.get("action") == "correct_input_schema"), None)
    assert fix_solution is not None, "Should provide input schema correction"
    
    print("✓ Schema mismatch test passed")


async def test_agent_capability_mismatch():
    """Test verification tool with agent capability mismatch."""
    print("=== Testing Agent Capability Mismatch ===")
    
    diagnosis = await diagnose_agent_error(
        agent_name="copy_writer",
        error_message="Agent does not have capability to generate images",
        agent_query="Generate a high-quality image of a sunset",
        agent_output=None
    )
    
    print("Diagnosis:", json.dumps(diagnosis, indent=2))
    
    # Verify the diagnosis
    assert "analysis" in diagnosis
    assert "issues" in diagnosis
    assert "solutions" in diagnosis
    
    # Check if it identified capability mismatch
    issues = diagnosis.get("issues", [])
    capability_issue = next((i for i in issues if "capability" in i.get("type", "").lower()), None)
    assert capability_issue is not None, "Should identify capability mismatch"
    
    print("✓ Agent capability mismatch test passed")


async def test_json_parsing_error():
    """Test verification tool with JSON parsing error."""
    print("=== Testing JSON Parsing Error ===")
    
    diagnosis = await diagnose_agent_error(
        agent_name="copy_writer",
        error_message="JSON parsing error: Expecting ',' delimiter: line 1 column 15 (char 14)",
        agent_query="Generate copy for Instagram post about coffee",
        agent_output='{"content": "Great coffee" "hashtags": ["#coffee", "#morning"]}'
    )
    
    print("Diagnosis:", json.dumps(diagnosis, indent=2))
    
    # Verify the diagnosis
    assert "analysis" in diagnosis
    assert "issues" in diagnosis
    assert "solutions" in diagnosis
    
    # Check if it identified JSON parsing issue
    issues = diagnosis.get("issues", [])
    json_issue = next((i for i in issues if "json" in i.get("type", "").lower() or "parsing" in i.get("type", "").lower()), None)
    assert json_issue is not None, "Should identify JSON parsing issue"
    
    print("✓ JSON parsing error test passed")


async def test_api_error_401():
    """Test verification tool with API authentication error."""
    print("=== Testing API 401 Error ===")
    
    diagnosis = await diagnose_tool_error(
        tool_name="kie_image_generation",
        tool_call_payload={
            "prompt": "A beautiful sunset",
            "image_size": "1024x1024"
        },
        tool_response={
            "error": "authentication_failed",
            "status_code": 401,
            "message": "Invalid API key"
        },
        error_details="HTTP 401: Authentication failed"
    )
    
    print("Diagnosis:", json.dumps(diagnosis, indent=2))
    
    # Verify the diagnosis
    assert "analysis" in diagnosis
    assert "issues" in diagnosis
    assert "solutions" in diagnosis
    
    # Check if it identified authentication issue
    issues = diagnosis.get("issues", [])
    auth_issue = next((i for i in issues if "auth" in i.get("type", "").lower() or "401" in str(i.get("evidence", ""))), None)
    assert auth_issue is not None, "Should identify authentication issue"
    
    print("✓ API 401 error test passed")


async def test_rate_limit_error():
    """Test verification tool with rate limit error."""
    print("=== Testing Rate Limit Error ===")
    
    diagnosis = await diagnose_tool_error(
        tool_name="unified_search",
        tool_call_payload={
            "platform": "instagram",
            "query": "coffee",
            "limit": 50
        },
        tool_response={
            "error": "rate_limit_exceeded",
            "status_code": 429,
            "message": "Too many requests. Please try again later.",
            "retry_after": 60
        },
        error_details="HTTP 429: Rate limit exceeded"
    )
    
    print("Diagnosis:", json.dumps(diagnosis, indent=2))
    
    # Verify the diagnosis
    assert "analysis" in diagnosis
    assert "issues" in diagnosis
    assert "solutions" in diagnosis
    
    # Check if it identified rate limit issue
    issues = diagnosis.get("issues", [])
    rate_limit_issue = next((i for i in issues if "rate" in i.get("type", "").lower() or "429" in str(i.get("evidence", ""))), None)
    assert rate_limit_issue is not None, "Should identify rate limit issue"
    
    print("✓ Rate limit error test passed")


async def test_comprehensive_verification():
    """Test the comprehensive verification tool with multiple parameters."""
    print("=== Testing Comprehensive Verification ===")
    
    diagnosis = await verification_tool(
        planner_step={
            "id": 1,
            "description": "Generate Instagram post content",
            "status": "in_progress"
        },
        agent_name="social_media_manager",
        agent_capabilities=[
            "Content planning and strategy",
            "Agent routing and coordination",
            "Media generation coordination"
        ],
        tool_name="kie_image_generation",
        tool_input_schema={
            "prompt": {"type": "string", "required": True},
            "image_size": {"type": "string", "required": False}
        },
        tool_capabilities={
            "image_generation": True,
            "image_editing": False
        },
        agent_query="Generate an image for Instagram post about coffee",
        tool_call_payload={
            "prompt": "Coffee cup on wooden table",
            "size": "1024x1024"  # Wrong parameter
        },
        tool_response={
            "error": "invalid_parameter",
            "message": "Parameter 'size' not found. Expected 'image_size'"
        },
        error_details="Schema validation failed",
        agent_output=None,
        agent_context=[
            "User requested Instagram post about coffee",
            "Social media manager routed to image generation",
            "Tool call failed due to parameter mismatch"
        ],
        previous_attempts=[],
        available_agents=["copy_writer", "media_activist", "research_agent"],
        available_tools=["kie_image_generation", "gemini_audio", "unified_search"]
    )
    
    print("Comprehensive Diagnosis:", json.dumps(diagnosis, indent=2))
    
    # Verify comprehensive diagnosis
    assert "analysis" in diagnosis
    assert "issues" in diagnosis
    assert "solutions" in diagnosis
    assert "next_steps" in diagnosis
    
    print("✓ Comprehensive verification test passed")


async def run_all_tests():
    """Run all verification tool tests."""
    print("Starting Verification Tool Tests...")
    print("=" * 50)
    
    try:
        await test_schema_mismatch_error()
        await test_agent_capability_mismatch()
        await test_json_parsing_error()
        await test_api_error_401()
        await test_rate_limit_error()
        await test_comprehensive_verification()
        
        print("=" * 50)
        print("✅ All verification tool tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(run_all_tests())