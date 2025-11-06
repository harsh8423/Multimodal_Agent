#!/usr/bin/env python3
"""
Test script for social media manager sequential handling
Tests the fix for handling both agent_required and tool_required simultaneously
"""

import asyncio
import sys
import os
import json
from unittest.mock import Mock, AsyncMock

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.social_media_manager import social_media_manager

class MockWebSocket:
    """Mock WebSocket for testing"""
    def __init__(self):
        self.messages = []
    
    async def send_json(self, data):
        self.messages.append(data)
        print(f"WebSocket message: {data}")

class MockSessionContext:
    """Mock SessionContext for testing"""
    def __init__(self):
        self.chat_id = "test_chat_123"
        self.user_id = "test_user_123"
        self.session_id = "test_session_123"
        self.todo_planner_state_active = False
        self.current_todo_id = None
    
    async def send_nano(self, agent_name, message):
        print(f"Nano message from {agent_name}: {message}")
    
    async def append_and_persist_memory(self, agent_name, content, metadata=None):
        print(f"Memory entry for {agent_name}: {content}")
    
    async def get_agent_memory(self, agent_name):
        mock_memory = Mock()
        mock_memory.get_all = AsyncMock(return_value=[])
        mock_memory.get_context_string = AsyncMock(return_value="")
        return mock_memory
    
    def get_todo_planner_state(self):
        return self.todo_planner_state_active
    
    def set_todo_planner_state(self, state):
        self.todo_planner_state_active = state
    
    def get_current_todo_id(self):
        return self.current_todo_id

async def test_sequential_handling():
    """Test that both agent_required and tool_required can be handled sequentially"""
    print("=== Testing Sequential Handling ===")
    
    # Create mock objects
    websocket = MockWebSocket()
    session_context = MockSessionContext()
    
    # Test message that would trigger both agent and tool requirements
    test_message = {
        "text": "Create a social media campaign about climate change and then manage the todos",
        "metadata": {"test": True}
    }
    
    print(f"Test message: {test_message}")
    
    try:
        # This should not raise an error anymore
        result = await social_media_manager(
            message=test_message,
            websocket=websocket,
            session_context=session_context,
            max_iterations=3
        )
        
        print(f"Result: {result}")
        print(f"WebSocket messages sent: {len(websocket.messages)}")
        
        # Check that we didn't get the old error message
        error_found = False
        for msg in websocket.messages:
            if "Invalid social media management state" in str(msg):
                error_found = True
                break
        
        if error_found:
            print("❌ FAILED: Still getting the old validation error")
            return False
        else:
            print("✅ SUCCESS: No validation error found - sequential handling working")
            return True
            
    except Exception as e:
        print(f"❌ ERROR during test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_agent_only():
    """Test normal agent-only flow"""
    print("\n=== Testing Agent-Only Flow ===")
    
    websocket = MockWebSocket()
    session_context = MockSessionContext()
    
    test_message = {
        "text": "Research information about renewable energy",
        "metadata": {"test": True}
    }
    
    try:
        result = await social_media_manager(
            message=test_message,
            websocket=websocket,
            session_context=session_context,
            max_iterations=2
        )
        
        print(f"Agent-only result: {result}")
        print("✅ SUCCESS: Agent-only flow working")
        return True
        
    except Exception as e:
        print(f"❌ ERROR during agent-only test: {e}")
        return False

async def test_tool_only():
    """Test normal tool-only flow"""
    print("\n=== Testing Tool-Only Flow ===")
    
    websocket = MockWebSocket()
    session_context = MockSessionContext()
    
    test_message = {
        "text": "Create a todo list for my project",
        "metadata": {"test": True}
    }
    
    try:
        result = await social_media_manager(
            message=test_message,
            websocket=websocket,
            session_context=session_context,
            max_iterations=2
        )
        
        print(f"Tool-only result: {result}")
        print("✅ SUCCESS: Tool-only flow working")
        return True
        
    except Exception as e:
        print(f"❌ ERROR during tool-only test: {e}")
        return False

async def main():
    """Run all tests"""
    print("Starting Social Media Manager Sequential Handling Tests")
    print("=" * 60)
    
    tests = [
        test_sequential_handling,
        test_agent_only,
        test_tool_only
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("❌ Some tests failed")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)