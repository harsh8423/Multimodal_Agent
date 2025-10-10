"""
Test script for the Todo Management System

This script tests the todo system integration by:
1. Creating a test todo list
2. Updating task statuses
3. Retrieving todos
4. Testing the complete workflow
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timezone

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.todo_manager import get_todo_manager

async def test_todo_system():
    """Test the complete todo system"""
    print("🧪 Testing Todo Management System...")
    
    # Get todo manager
    todo_manager = await get_todo_manager()
    
    # Test data
    test_chat_id = "test_chat_123"
    test_agent = "social_media_manager"
    
    # Test 1: Create a todo list
    print("\n📝 Test 1: Creating todo list...")
    test_tasks = [
        {
            "step_num": 1,
            "title": "Research competitors",
            "description": "Find and analyze competitor content strategies",
            "status": "pending"
        },
        {
            "step_num": 2,
            "title": "Create content plan",
            "description": "Develop structured content plan based on research",
            "status": "pending"
        },
        {
            "step_num": 3,
            "title": "Generate content",
            "description": "Create actual content pieces (posts, videos, etc.)",
            "status": "pending"
        },
        {
            "step_num": 4,
            "title": "Review and publish",
            "description": "Final review and publish content",
            "status": "pending"
        }
    ]
    
    result = await todo_manager.create_todo(
        chat_id=test_chat_id,
        agent_name=test_agent,
        tasks=test_tasks,
        title="Social Media Content Creation Workflow"
    )
    
    if result["success"]:
        todo_id = result["todo_id"]
        print(f"✅ Todo created successfully! ID: {todo_id}")
        print(f"   Title: {result['todo_data']['title']}")
        print(f"   Tasks: {len(result['todo_data']['tasks'])}")
    else:
        print(f"❌ Failed to create todo: {result['error']}")
        return
    
    # Test 2: Update task status
    print("\n🔄 Test 2: Updating task status...")
    update_result = await todo_manager.update_todo_task(
        todo_id=todo_id,
        step_num=1,
        updates={"status": "in-progress"}
    )
    
    if update_result["success"]:
        print("✅ Task status updated successfully!")
        print(f"   Task 1 status: {update_result['todo_data']['tasks'][0]['status']}")
    else:
        print(f"❌ Failed to update task: {update_result['error']}")
    
    # Test 3: Get next pending task
    print("\n➡️ Test 3: Getting next pending task...")
    next_task = await todo_manager.get_next_pending_task(todo_id)
    
    if next_task:
        print(f"✅ Next task found: Step {next_task['step_num']} - {next_task['title']}")
    else:
        print("❌ No pending tasks found")
    
    # Test 4: Get chat todos
    print("\n📋 Test 4: Getting chat todos...")
    chat_todos = await todo_manager.get_chat_todos(test_chat_id)
    
    if chat_todos:
        print(f"✅ Found {len(chat_todos)} todo(s) for chat")
        for todo in chat_todos:
            completed = len([t for t in todo['tasks'] if t['status'] == 'done'])
            total = len(todo['tasks'])
            print(f"   - {todo['title']}: {completed}/{total} tasks completed")
    else:
        print("❌ No todos found for chat")
    
    # Test 5: Complete all tasks
    print("\n✅ Test 5: Completing all tasks...")
    for i, task in enumerate(test_tasks):
        await todo_manager.update_todo_task(
            todo_id=todo_id,
            step_num=task['step_num'],
            updates={"status": "done"}
        )
        print(f"   ✅ Completed task {task['step_num']}: {task['title']}")
    
    # Test 6: Verify completion
    print("\n🎯 Test 6: Verifying completion...")
    final_todo = await todo_manager.get_todo(todo_id)
    if final_todo:
        completed_tasks = len([t for t in final_todo['tasks'] if t['status'] == 'done'])
        total_tasks = len(final_todo['tasks'])
        print(f"✅ Final status: {completed_tasks}/{total_tasks} tasks completed")
        
        if final_todo['status'] == 'completed':
            print("🎉 Todo list marked as completed!")
        else:
            print("⚠️ Todo list not marked as completed")
    
    print("\n🏁 Todo system test completed!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_todo_system())