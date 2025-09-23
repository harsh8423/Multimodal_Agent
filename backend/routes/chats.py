"""
Chat Management API Routes

Provides endpoints for:
1. Getting user's chat history
2. Creating new chats
3. Getting chat details and messages
4. Switching between chats
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from utils.mongo_store import get_store
from services.auth import auth_service
from models.user import User

router = APIRouter(prefix="/chats", tags=["chats"])


class CreateChatRequest(BaseModel):
    token: str
    title: Optional[str] = None


async def get_current_user_from_token(token: str) -> User:
    """Get current user from token"""
    user_id = auth_service.verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.get("/history")
async def get_chat_history(
    token: str,
    limit: int = 50
) -> List[dict]:
    """Get user's chat history"""
    user = await get_current_user_from_token(token)
    store = await get_store()
    
    chats = await store.get_user_chats(user.id, limit)
    
    # Return simplified chat info
    return [
        {
            "chat_id": chat["chat_id"],
            "title": chat.get("title", "Untitled Chat"),
            "created_at": chat["created_at"],
            "last_active": chat["last_active"],
            "message_count": chat.get("message_count", 0)
        }
        for chat in chats
    ]


@router.post("/create")
async def create_chat(request: CreateChatRequest) -> dict:
    """Create a new chat"""
    user = await get_current_user_from_token(request.token)
    store = await get_store()
    
    chat_id = await store.create_chat(
        user_id=user.id,
        title=request.title or "New Chat"
    )
    
    return {
        "chat_id": chat_id,
        "title": request.title or "New Chat",
        "created_at": None,  # Will be set by create_chat
        "message_count": 0
    }


@router.get("/{chat_id}/messages")
async def get_chat_messages(
    chat_id: str,
    token: str,
    limit: int = 100
) -> List[dict]:
    """Get messages for a specific chat"""
    user = await get_current_user_from_token(token)
    store = await get_store()
    
    # Verify chat belongs to user
    chat = await store.get_chat(chat_id)
    if not chat or chat.get("user_id") != user.id:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    messages = await store.get_chat_messages(chat_id, limit)
    
    return [
        {
            "timestamp": msg["timestamp"],
            "role": msg["role"],
            "agent": msg.get("agent"),
            "content": msg["content"],
            "message_type": msg.get("message_type", "final_message"),
            "metadata": msg.get("meta", {})
        }
        for msg in messages
    ]


@router.get("/{chat_id}/details")
async def get_chat_details(
    chat_id: str,
    token: str
) -> dict:
    """Get detailed information about a chat"""
    user = await get_current_user_from_token(token)
    store = await get_store()
    
    # Get chat details
    chat = await store.get_chat(chat_id)
    if not chat or chat.get("user_id") != user.id:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Get message count
    messages = await store.get_chat_messages(chat_id, 1000)  # Get all messages for count
    message_count = len(messages)
    
    return {
        "chat_id": chat["chat_id"],
        "title": chat.get("title", "Untitled Chat"),
        "created_at": chat["created_at"],
        "last_active": chat["last_active"],
        "metadata": chat.get("meta", {}),
        "message_count": message_count
    }


@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: str,
    token: str
) -> dict:
    """Delete a chat and all associated data"""
    user = await get_current_user_from_token(token)
    store = await get_store()
    
    # Verify chat belongs to user
    chat = await store.get_chat(chat_id)
    if not chat or chat.get("user_id") != user.id:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    success = await store.delete_chat(chat_id)
    
    if success:
        return {"message": "Chat deleted successfully", "chat_id": chat_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete chat")


@router.put("/{chat_id}/title")
async def update_chat_title(
    chat_id: str,
    token: str,
    title: str
) -> dict:
    """Update chat title"""
    user = await get_current_user_from_token(token)
    store = await get_store()
    
    # Verify chat belongs to user
    chat = await store.get_chat(chat_id)
    if not chat or chat.get("user_id") != user.id:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Update title in database
    try:
        from datetime import datetime, timezone
        await store.chats_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"title": title, "last_active": datetime.now(timezone.utc)}}
        )
        return {"message": "Title updated successfully", "title": title}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update title: {str(e)}")