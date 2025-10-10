"""
Test script for the Unified Todo Management Function

This script tests the unified manage_todos function by:
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

from tools.todo_manager import manage_todos

async def test_unified_todo_system():
    """Test the unified todo management function"""
    print("🧪 Testing Unified Todo Management Function...")
    
    # Test data
    test_chat_id = "test_chat_unified_123"
    test_agent = "social_media_manager"
    
    # Test 1: Create a todo list
    print("\n📝 Test 1: Creating todo list with unified function...")
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
    
    result = await manage_todos(
        action="create",
        chat_id=test_chat_id,
        agent_name=test_agent,
        tasks=test_tasks,
        title="Unified Todo Test - Social Media Content Creation"
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
    print("\n🔄 Test 2: Updating task status with unified function...")
    update_result = await manage_todos(
        action="update",
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
    print("\n➡️ Test 3: Getting next pending task with unified function...")
    next_task_result = await manage_todos(
        action="next_task",
        todo_id=todo_id
    )
    
    if next_task_result["success"] and next_task_result["next_task"]:
        next_task = next_task_result["next_task"]
        print(f"✅ Next task found: Step {next_task['step_num']} - {next_task['title']}")
    else:
        print("❌ No pending tasks found")
    
    # Test 4: Read todos
    print("\n📋 Test 4: Reading todos with unified function...")
    read_result = await manage_todos(
        action="read",
        chat_id=test_chat_id
    )
    
    if read_result["success"]:
        todos = read_result["todos"]
        print(f"✅ Found {len(todos)} todo(s) for chat")
        for todo in todos:
            completed = len([t for t in todo['tasks'] if t['status'] == 'done'])
            total = len(todo['tasks'])
            print(f"   - {todo['title']}: {completed}/{total} tasks completed")
    else:
        print("❌ Failed to read todos")
    
    # Test 5: Add new task
    print("\n➕ Test 5: Adding new task with unified function...")
    new_task = {
        "step_num": 5,
        "title": "Monitor performance",
        "description": "Track and analyze content performance metrics",
        "status": "pending",
        "created_at": datetime.now(timezone.utc)
    }
    
    add_task_result = await manage_todos(
        action="add_task",
        todo_id=todo_id,
        task=new_task
    )
    
    if add_task_result["success"]:
        print("✅ New task added successfully!")
        print(f"   Total tasks: {len(add_task_result['todo_data']['tasks'])}")
    else:
        print(f"❌ Failed to add task: {add_task_result['error']}")
    
    # Test 6: Complete all tasks
    print("\n✅ Test 6: Completing all tasks with unified function...")
    for i, task in enumerate(test_tasks + [new_task]):
        await manage_todos(
            action="update",
            todo_id=todo_id,
            step_num=task['step_num'],
            updates={"status": "done"}
        )
        print(f"   ✅ Completed task {task['step_num']}: {task['title']}")
    
    # Test 7: Verify completion
    print("\n🎯 Test 7: Verifying completion with unified function...")
    final_read_result = await manage_todos(
        action="read",
        chat_id=test_chat_id,
        todo_id=todo_id
    )
    
    if final_read_result["success"] and final_read_result["todo"]:
        final_todo = final_read_result["todo"]
        completed_tasks = len([t for t in final_todo['tasks'] if t['status'] == 'done'])
        total_tasks = len(final_todo['tasks'])
        print(f"✅ Final status: {completed_tasks}/{total_tasks} tasks completed")
        
        if final_todo['status'] == 'completed':
            print("🎉 Todo list marked as completed!")
        else:
            print("⚠️ Todo list not marked as completed")
    
    print("\n🏁 Unified todo system test completed!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_unified_todo_system())