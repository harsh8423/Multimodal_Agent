"""
To-Do Manager Tool

This tool allows agents to create, update, and manage todo lists for their tasks.
It integrates with MongoDB to persist todo lists and provides real-time updates
to the frontend via websocket connections.
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from database import get_database
from utils.mongo_store import save_chat_message

logger = logging.getLogger(__name__)


def serialize_for_json(obj: Any) -> Any:
    """
    Convert MongoDB objects to JSON-serializable format
    
    Args:
        obj: Object to serialize
        
    Returns:
        JSON-serializable object
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: serialize_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]
    else:
        return obj


class TodoManager:
    """Manages todo lists for agents"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.todos_collection = database.todos
    
    async def create_todo(self, chat_id: str, agent_name: str, tasks: List[Dict[str, Any]], 
                         title: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new todo list
        
        Args:
            chat_id: Chat ID to associate with the todo
            agent_name: Name of the agent creating the todo
            tasks: List of task dictionaries with step_num, title, description, status
            title: Optional title for the todo list
            
        Returns:
            Dictionary with todo_id and created todo data
        """
        try:
            todo_doc = {
                "chat_id": chat_id,
                "created_by": agent_name,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "title": title or f"Todo List by {agent_name}",
                "tasks": tasks,
                "status": "active"  # active, completed, cancelled
            }
            
            result = await self.todos_collection.insert_one(todo_doc)
            todo_id = str(result.inserted_id)
            
            # Save a chat message to notify the frontend
            await save_chat_message(
                chat_id=chat_id,
                role="assistant",
                content=f"Created todo list: {todo_doc['title']}",
                agent=agent_name,
                message_type="todo_created",
                meta={
                    "todo_id": todo_id,
                    "todo_data": todo_doc,
                    "action": "create"
                }
            )
            
            return {
                "success": True,
                "todo_id": todo_id,
                "todo_data": todo_doc
            }
            
        except Exception as e:
            logger.error(f"Failed to create todo: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_todo_task(self, todo_id: str, step_num: int, 
                              updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a specific task in a todo list
        
        Args:
            todo_id: ID of the todo list
            step_num: Step number to update
            updates: Dictionary with fields to update (title, description, status, etc.)
            
        Returns:
            Dictionary with success status and updated todo data
        """
        try:
            # Find the todo
            todo = await self.todos_collection.find_one({"_id": ObjectId(todo_id)})
            if not todo:
                return {"success": False, "error": "Todo not found"}
            
            # Update the specific task
            updated_tasks = []
            task_updated = False
            
            for task in todo["tasks"]:
                if task["step_num"] == step_num:
                    # Update the task
                    updated_task = {**task, **updates}
                    updated_task["updated_at"] = datetime.now(timezone.utc)
                    updated_tasks.append(updated_task)
                    task_updated = True
                else:
                    updated_tasks.append(task)
            
            if not task_updated:
                return {"success": False, "error": f"Task with step_num {step_num} not found"}
            
            # Update the todo document
            update_doc = {
                "tasks": updated_tasks,
                "updated_at": datetime.now(timezone.utc)
            }
            
            # Check if all tasks are completed
            all_completed = all(task["status"] == "done" for task in updated_tasks)
            if all_completed:
                update_doc["status"] = "completed"
            
            await self.todos_collection.update_one(
                {"_id": ObjectId(todo_id)},
                {"$set": update_doc}
            )
            
            # Get updated todo
            updated_todo = await self.todos_collection.find_one({"_id": ObjectId(todo_id)})
            
            # Save a chat message to notify the frontend
            await save_chat_message(
                chat_id=updated_todo["chat_id"],
                role="assistant",
                content=f"Updated task {step_num}: {updates.get('title', 'Task')} - Status: {updates.get('status', 'updated')}",
                agent=updated_todo["created_by"],
                message_type="todo_updated",
                meta={
                    "todo_id": todo_id,
                    "todo_data": updated_todo,
                    "action": "update",
                    "step_num": step_num,
                    "updates": updates
                }
            )
            
            return {
                "success": True,
                "todo_id": todo_id,
                "todo_data": updated_todo
            }
            
        except Exception as e:
            logger.error(f"Failed to update todo task: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_todo(self, todo_id: str) -> Optional[Dict[str, Any]]:
        """Get a todo by ID"""
        try:
            return await self.todos_collection.find_one({"_id": ObjectId(todo_id)})
        except Exception as e:
            logger.error(f"Failed to get todo: {e}")
            return None
    
    async def get_chat_todos(self, chat_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all todos for a chat
        
        Args:
            chat_id: Chat ID
            status: Optional status filter (active, completed, cancelled)
            
        Returns:
            List of todo documents
        """
        try:
            query = {"chat_id": chat_id}
            if status:
                query["status"] = status
            
            cursor = self.todos_collection.find(query).sort("created_at", -1)
            return await cursor.to_list(length=100)
        except Exception as e:
            logger.error(f"Failed to get chat todos: {e}")
            return []
    
    async def get_next_pending_task(self, todo_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the next pending task from a todo list
        
        Args:
            todo_id: ID of the todo list
            
        Returns:
            Next pending task or None if all tasks are done
        """
        try:
            todo = await self.todos_collection.find_one({"_id": ObjectId(todo_id)})
            if not todo:
                return None
            
            # Find the first pending task
            for task in sorted(todo["tasks"], key=lambda x: x["step_num"]):
                if task["status"] == "pending":
                    return task
            
            return None
        except Exception as e:
            logger.error(f"Failed to get next pending task: {e}")
            return None
    
    async def add_task_to_todo(self, todo_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a new task to an existing todo list
        
        Args:
            todo_id: ID of the todo list
            task: Task dictionary with step_num, title, description, status
            
        Returns:
            Dictionary with success status and updated todo data
        """
        try:
            todo = await self.todos_collection.find_one({"_id": ObjectId(todo_id)})
            if not todo:
                return {"success": False, "error": "Todo not found"}
            
            # Add the new task
            todo["tasks"].append(task)
            todo["updated_at"] = datetime.now(timezone.utc)
            
            await self.todos_collection.update_one(
                {"_id": ObjectId(todo_id)},
                {"$set": {
                    "tasks": todo["tasks"],
                    "updated_at": todo["updated_at"]
                }}
            )
            
            # Get updated todo
            updated_todo = await self.todos_collection.find_one({"_id": ObjectId(todo_id)})
            
            # Save a chat message to notify the frontend
            await save_chat_message(
                chat_id=updated_todo["chat_id"],
                role="assistant",
                content=f"Added new task: {task['title']}",
                agent=updated_todo["created_by"],
                message_type="todo_updated",
                meta={
                    "todo_id": todo_id,
                    "todo_data": updated_todo,
                    "action": "add_task",
                    "new_task": task
                }
            )
            
            return {
                "success": True,
                "todo_id": todo_id,
                "todo_data": updated_todo
            }
            
        except Exception as e:
            logger.error(f"Failed to add task to todo: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Global todo manager instance
_todo_manager = None

async def get_todo_manager() -> TodoManager:
    """Get todo manager instance"""
    global _todo_manager
    if _todo_manager is None:
        database = await get_database()
        _todo_manager = TodoManager(database)
    return _todo_manager


# Unified Todo Management Function
async def manage_todos(action: str, **kwargs) -> Dict[str, Any]:
    """
    Unified function to manage todos - create, update, read, or get next task
    
    Args:
        action: Action to perform ("create", "update", "read", "next_task", "add_task")
        **kwargs: Additional parameters based on action
        
    Returns:
        Dictionary with result data
    """
    todo_manager = await get_todo_manager()
    
    # Print input parameters for debugging
    print(f"🔧 manage_todos called with action: {action}, kwargs: {kwargs}")
    
    try:
        if action == "create":
            # Required: chat_id, agent_name, tasks
            # Optional: title
            chat_id = kwargs.get("chat_id")
            agent_name = kwargs.get("agent_name")
            tasks = kwargs.get("tasks", [])
            title = kwargs.get("title")
            
            if not chat_id or not agent_name:
                return {"success": False, "error": "chat_id and agent_name are required"}
            
            result = await todo_manager.create_todo(chat_id, agent_name, tasks, title)
            print(f"📝 create_todo result: {result}")
            return serialize_for_json(result)
            
        elif action == "update":
            # Required: todo_id, step_num, updates
            todo_id = kwargs.get("todo_id")
            step_num = kwargs.get("step_num")
            updates = kwargs.get("updates", {})
            
            if not todo_id or step_num is None:
                return {"success": False, "error": "todo_id and step_num are required"}
            
            result = await todo_manager.update_todo_task(todo_id, step_num, updates)
            print(f"📝 update_todo_task result: {result}")
            return serialize_for_json(result)
            
        elif action == "read":
            # Required: chat_id
            # Optional: todo_id (for specific todo), status (for filtering)
            chat_id = kwargs.get("chat_id")
            todo_id = kwargs.get("todo_id")
            status = kwargs.get("status")
            
            if not chat_id:
                return {"success": False, "error": "chat_id is required"}
            
            if todo_id:
                # Get specific todo
                todo = await todo_manager.get_todo(todo_id)
                result = {
                    "success": True,
                    "todo": todo
                }
                print(f"📝 get_todo result: {result}")
                return serialize_for_json(result)
            else:
                # Get all todos for chat
                todos = await todo_manager.get_chat_todos(chat_id, status)
                result = {
                    "success": True,
                    "todos": todos
                }
                print(f"📝 get_chat_todos result: {result}")
                return serialize_for_json(result)
                
        elif action == "next_task":
            # Required: todo_id
            todo_id = kwargs.get("todo_id")
            
            if not todo_id:
                return {"success": False, "error": "todo_id is required"}
            
            next_task = await todo_manager.get_next_pending_task(todo_id)
            result = {
                "success": True,
                "next_task": next_task
            }
            print(f"📝 get_next_pending_task result: {result}")
            return serialize_for_json(result)
            
        elif action == "add_task":
            # Required: todo_id, task
            todo_id = kwargs.get("todo_id")
            task = kwargs.get("task")
            
            if not todo_id or not task:
                return {"success": False, "error": "todo_id and task are required"}
            
            result = await todo_manager.add_task_to_todo(todo_id, task)
            print(f"📝 add_task_to_todo result: {result}")
            return serialize_for_json(result)
            
        else:
            return {"success": False, "error": f"Unknown action: {action}"}
            
    except Exception as e:
        logger.error(f"Error in manage_todos: {e}")
        error_result = {"success": False, "error": str(e)}
        print(f"❌ manage_todos error: {error_result}")
        return error_result


# Individual tool functions for backward compatibility
async def create_todo_list(chat_id: str, agent_name: str, tasks: List[Dict[str, Any]], 
                          title: Optional[str] = None) -> Dict[str, Any]:
    """Create a new todo list"""
    return await manage_todos("create", chat_id=chat_id, agent_name=agent_name, tasks=tasks, title=title)


async def update_todo_task_status(chat_id: str, todo_id: str, step_num: int, 
                                 status: str, title: Optional[str] = None, 
                                 description: Optional[str] = None) -> Dict[str, Any]:
    """Update a todo task status"""
    updates = {"status": status}
    if title:
        updates["title"] = title
    if description:
        updates["description"] = description
    
    return await manage_todos("update", todo_id=todo_id, step_num=step_num, updates=updates)


async def get_next_todo_task(chat_id: str, todo_id: str) -> Dict[str, Any]:
    """Get the next pending task from a todo list"""
    return await manage_todos("next_task", todo_id=todo_id)


async def add_todo_task(chat_id: str, todo_id: str, step_num: int, 
                       title: str, description: str, status: str = "pending") -> Dict[str, Any]:
    """Add a new task to an existing todo list"""
    new_task = {
        "step_num": step_num,
        "title": title,
        "description": description,
        "status": status,
        "created_at": datetime.now(timezone.utc)
    }
    
    return await manage_todos("add_task", todo_id=todo_id, task=new_task)


async def get_chat_todos(chat_id: str, status: Optional[str] = None) -> Dict[str, Any]:
    """Get all todos for a chat"""
    return await manage_todos("read", chat_id=chat_id, status=status)