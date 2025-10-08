#!/usr/bin/env python3
"""
Test script for media_activist agent and tools
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.tool_router import tool_router, get_available_tools
from utils.router import call_agent

async def test_available_tools():
    """Test that media generation tools are available"""
    print("=== Testing Available Tools ===")
    tools = get_available_tools()
    print(f"Total available tools: {len(tools)}")
    
    media_tools = [tool for tool in tools if any(keyword in tool for keyword in ['kie', 'gemini_audio', 'minimax', 'microsoft_tts'])]
    print(f"Media generation tools found: {media_tools}")
    
    expected_tools = ['kie_image_generation', 'gemini_audio', 'minimax_audio_clone', 'microsoft_tts']
    for tool in expected_tools:
        if tool in tools:
            print(f"✅ {tool} is available")
        else:
            print(f"❌ {tool} is NOT available")
    
    return media_tools

async def test_media_activist_agent():
    """Test that media_activist agent can be called"""
    print("\n=== Testing Media Activist Agent ===")
    
    try:
        # Test a simple query that should route to media_activist
        query = "Generate an image of a sunset"
        print(f"Testing query: {query}")
        
        result = await call_agent(
            agent_name="media_activist",
            query=query,
            model_name="gpt-4o-mini"
        )
        
        print(f"✅ Media activist agent responded successfully")
        print(f"Response type: {type(result)}")
        if isinstance(result, dict):
            print(f"Response keys: {list(result.keys())}")
        return True
        
    except Exception as e:
        print(f"❌ Media activist agent failed: {e}")
        return False

async def test_tool_routing():
    """Test that media generation tools can be routed"""
    print("\n=== Testing Tool Routing ===")
    
    # Test KIE image generation tool
    try:
        result = await tool_router(
            tool_name="kie_image_generation",
            input_schema_fields={
                "prompt": "A beautiful sunset over mountains",
                "model": "google/nano-banana-edit"
            }
        )
        print(f"✅ KIE image generation tool routed successfully")
        print(f"Result type: {type(result)}")
        return True
    except Exception as e:
        print(f"❌ KIE image generation tool failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting Media Activist Tests\n")
    
    # Test 1: Available tools
    media_tools = await test_available_tools()
    
    # Test 2: Agent routing
    agent_success = await test_media_activist_agent()
    
    # Test 3: Tool routing (only if tools are available)
    tool_success = False
    if media_tools:
        tool_success = await test_tool_routing()
    
    # Summary
    print("\n=== Test Summary ===")
    print(f"Media tools available: {len(media_tools) > 0}")
    print(f"Agent routing works: {agent_success}")
    print(f"Tool routing works: {tool_success}")
    
    if len(media_tools) > 0 and agent_success:
        print("🎉 Media activist setup appears to be working!")
    else:
        print("⚠️  Some issues detected. Check the errors above.")

if __name__ == "__main__":
    asyncio.run(main())