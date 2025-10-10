"""
Todo Management API Routes

Provides endpoints for:
1. Getting todos for a chat
2. Creating new todos
3. Updating todo tasks
4. Getting todo details
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from tools.todo_manager import get_todo_manager
from services.auth import auth_service
from models.user import User

router = APIRouter(prefix="/todos", tags=["todos"])


class CreateTodoRequest(BaseModel):
    token: str
    title: Optional[str] = None
    tasks: List[dict]


class UpdateTodoTaskRequest(BaseModel):
    token: str
    todo_id: str
    step_num: int
    status: str
    title: Optional[str] = None
    description: Optional[str] = None


async def get_current_user_from_token(token: str) -> User:
    """Get current user from token"""
    user_id = auth_service.verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.get("/chat/{chat_id}")
async def get_chat_todos(
    chat_id: str,
    token: str,
    status: Optional[str] = None
) -> List[dict]:
    """Get all todos for a specific chat"""
    user = await get_current_user_from_token(token)
    todo_manager = await get_todo_manager()
    
    # Verify chat belongs to user (you might want to add this check)
    # For now, we'll trust that the chat_id is valid
    
    todos = await todo_manager.get_chat_todos(chat_id, status)
    
    return todos


@router.get("/{todo_id}")
async def get_todo(
    todo_id: str,
    token: str
) -> dict:
    """Get a specific todo by ID"""
    user = await get_current_user_from_token(token)
    todo_manager = await get_todo_manager()
    
    todo = await todo_manager.get_todo(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    return todo


@router.post("/create")
async def create_todo(request: CreateTodoRequest) -> dict:
    """Create a new todo list"""
    user = await get_current_user_from_token(request.token)
    todo_manager = await get_todo_manager()
    
    # Extract chat_id from the first task or use a default
    chat_id = None
    if request.tasks and len(request.tasks) > 0:
        chat_id = request.tasks[0].get('chat_id')
    
    if not chat_id:
        raise HTTPException(status_code=400, detail="chat_id is required")
    
    result = await todo_manager.create_todo(
        chat_id=chat_id,
        agent_name="social_media_manager",  # Default agent name
        tasks=request.tasks,
        title=request.title
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to create todo"))
    
    return result


@router.put("/{todo_id}/task/{step_num}")
async def update_todo_task(
    todo_id: str,
    step_num: int,
    request: UpdateTodoTaskRequest
) -> dict:
    """Update a specific task in a todo list"""
    user = await get_current_user_from_token(request.token)
    todo_manager = await get_todo_manager()
    
    updates = {"status": request.status}
    if request.title:
        updates["title"] = request.title
    if request.description:
        updates["description"] = request.description
    
    result = await todo_manager.update_todo_task(todo_id, step_num, updates)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to update todo task"))
    
    return result


@router.get("/{todo_id}/next-task")
async def get_next_todo_task(
    todo_id: str,
    token: str
) -> dict:
    """Get the next pending task from a todo list"""
    user = await get_current_user_from_token(token)
    todo_manager = await get_todo_manager()
    
    next_task = await todo_manager.get_next_pending_task(todo_id)
    
    return {
        "success": True,
        "next_task": next_task
    }