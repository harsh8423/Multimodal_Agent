"""
MongoDB Store for Session and Chat Persistence

This module provides async MongoDB operations for:
1. Session management (create, update, retrieve)
2. Chat-scoped persistence (chats, messages, agent memories)
3. Message storage (chat history with message types)
4. Log persistence (structured logs)
"""

import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Union
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from database import get_database
from utils.session_memory import SessionContext, LogEntry, AgentMemory

logger = logging.getLogger(__name__)


class MongoStore:
    """MongoDB store for session and chat data persistence"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        
        # Chat-scoped collections only
        self.chats_collection = database.chats
        self.chat_messages_collection = database.chat_messages
        self.agent_memories_collection = database.agent_memories
        # Logs collection is no longer used; logs are not persisted
        self.logs_collection = database.logs
    
    
    # -------------------
    # Chat document helpers
    # -------------------
    async def create_chat(self, chat_id: Optional[str] = None, user_id: Optional[str] = None, 
                         title: Optional[str] = None, meta: Optional[Dict[str, Any]] = None) -> str:
        """Create a new chat document"""
        chat_id = chat_id or str(uuid.uuid4())
        doc = {
            "chat_id": chat_id,
            "user_id": user_id,
            "title": title or "",
            "created_at": datetime.now(timezone.utc),
            "last_active": datetime.now(timezone.utc),
            "meta": meta or {}
        }
        await self.chats_collection.update_one(
            {"chat_id": chat_id}, 
            {"$set": doc}, 
            upsert=True
        )
        return chat_id
    
    async def update_chat_last_active(self, chat_id: str) -> bool:
        """Update last_active timestamp for a chat"""
        try:
            result = await self.chats_collection.update_one(
                {"chat_id": chat_id},
                {"$set": {"last_active": datetime.now(timezone.utc)}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update chat last active: {e}")
            return False
    
    async def update_chat_title(self, chat_id: str, title: str) -> bool:
        """Update chat title"""
        try:
            result = await self.chats_collection.update_one(
                {"chat_id": chat_id},
                {"$set": {"title": title, "last_active": datetime.now(timezone.utc)}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update chat title: {e}")
            return False
    
    async def delete_chat(self, chat_id: str) -> bool:
        """Delete a chat and all associated data"""
        try:
            # Delete chat document
            await self.chats_collection.delete_one({"chat_id": chat_id})
            # Delete all messages for this chat
            await self.chat_messages_collection.delete_many({"chat_id": chat_id})
            # Delete all agent memories for this chat
            await self.agent_memories_collection.delete_many({"chat_id": chat_id})
            # Logs are not persisted anymore; nothing to delete
            return True
        except Exception as e:
            logger.error(f"Failed to delete chat: {e}")
            return False
    
    async def get_chat(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """Get chat document by chat_id"""
        try:
            return await self.chats_collection.find_one({"chat_id": chat_id})
        except Exception as e:
            logger.error(f"Failed to get chat: {e}")
            return None
    
    async def get_user_chats(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent chats for a user"""
        try:
            cursor = self.chats_collection.find(
                {"user_id": user_id}
            ).sort("last_active", -1).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Failed to get user chats: {e}")
            return []
    
    # -------------------
    # Chat Messages
    # -------------------
    async def save_chat_message(self, chat_id: str, role: str, content: Any, 
                               agent: Optional[str] = None, message_type: str = "final_message", 
                               meta: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Save a chat message (excludes nano_message per requirement)"""
        # Do NOT store nano_message (per requirement)
        if message_type == "nano_message":
            return None
            
        doc = {
            "chat_id": chat_id,
            "timestamp": datetime.now(timezone.utc),
            "role": role,
            "agent": agent,
            "message_type": message_type,
            "content": content,
            "meta": meta or {}
        }
        
        try:
            result = await self.chat_messages_collection.insert_one(doc)
            # Update chat's last active
            await self.update_chat_last_active(chat_id)
            return {"_id": result.inserted_id, **doc}
        except Exception as e:
            logger.error(f"Failed to save chat message: {e}")
            return None
    
    async def get_chat_messages(self, chat_id: str, limit: int = 200, asc: bool = True) -> List[Dict[str, Any]]:
        """Get messages for a chat"""
        try:
            sort_order = 1 if asc else -1
            cursor = self.chat_messages_collection.find(
                {"chat_id": chat_id}
            ).sort("timestamp", sort_order).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Failed to get chat messages: {e}")
            return []
    
    # -------------------
    # Agent Memories (append & load)
    # -------------------
    async def append_agent_memory(self, chat_id: str, agent: str, content: str, 
                                 meta: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Append a new agent memory entry"""
        doc = {
            "chat_id": chat_id,
            "agent": agent,
            "ts": datetime.now(timezone.utc),
            "content": content,
            "meta": meta or {}
        }
        
        try:
            result = await self.agent_memories_collection.insert_one(doc)
            await self.update_chat_last_active(chat_id)
            return {"_id": result.inserted_id, **doc}
        except Exception as e:
            logger.error(f"Failed to append agent memory: {e}")
            return None
    
    async def load_agent_memories(self, chat_id: str, agent: Optional[str] = None, 
                                 limit: int = 100) -> List[Dict[str, Any]]:
        """Load agent memories for a chat"""
        try:
            query = {"chat_id": chat_id}
            if agent:
                query["agent"] = agent
            
            cursor = self.agent_memories_collection.find(query).sort("ts", 1).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Failed to load agent memories: {e}")
            return []
    
    async def clear_agent_memories(self, chat_id: str, agent: Optional[str] = None) -> int:
        """Clear agent memories for a chat"""
        try:
            query = {"chat_id": chat_id}
            if agent:
                query["agent"] = agent
            
            result = await self.agent_memories_collection.delete_many(query)
            return result.deleted_count
        except Exception as e:
            logger.error(f"Failed to clear agent memories: {e}")
            return 0
    
    # -------------------
    # Chat-scoped Logs
    # -------------------
    async def append_chat_log(self, chat_id: str, step: str, message: str, 
                             level: str = "info", details: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """No-op: Logs are not persisted. Kept for compatibility."""
        return None
    
    async def get_chat_logs(self, chat_id: str, limit: int = 200) -> List[Dict[str, Any]]:
        """No-op: Logs are not persisted; always return empty list."""
        return []


# Global store instance
_store_instance: Optional[MongoStore] = None


async def get_store() -> MongoStore:
    """Get the global MongoDB store instance"""
    global _store_instance
    if _store_instance is None:
        database = await get_database()
        _store_instance = MongoStore(database)
    return _store_instance


# Convenience functions


# Chat-scoped convenience functions
async def create_chat(chat_id: Optional[str] = None, user_id: Optional[str] = None, 
                     title: Optional[str] = None, meta: Optional[Dict[str, Any]] = None) -> str:
    """Create a new chat"""
    store = await get_store()
    return await store.create_chat(chat_id, user_id, title, meta)


async def update_chat_last_active(chat_id: str) -> bool:
    """Update chat last active timestamp"""
    store = await get_store()
    return await store.update_chat_last_active(chat_id)


async def update_chat_title(chat_id: str, title: str) -> bool:
    """Update chat title"""
    store = await get_store()
    return await store.update_chat_title(chat_id, title)


async def delete_chat(chat_id: str) -> bool:
    """Delete a chat and all associated data"""
    store = await get_store()
    return await store.delete_chat(chat_id)


async def get_chat(chat_id: str) -> Optional[Dict[str, Any]]:
    """Get chat document"""
    store = await get_store()
    return await store.get_chat(chat_id)


async def get_user_chats(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get user's chats"""
    store = await get_store()
    return await store.get_user_chats(user_id, limit)


async def save_chat_message(chat_id: str, role: str, content: Any, 
                           agent: Optional[str] = None, message_type: str = "final_message", 
                           meta: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Save a chat message"""
    store = await get_store()
    return await store.save_chat_message(chat_id, role, content, agent, message_type, meta)


async def get_chat_messages(chat_id: str, limit: int = 200, asc: bool = True) -> List[Dict[str, Any]]:
    """Get chat messages"""
    store = await get_store()
    return await store.get_chat_messages(chat_id, limit, asc)


async def append_agent_memory(chat_id: str, agent: str, content: str, 
                            meta: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Append agent memory"""
    store = await get_store()
    return await store.append_agent_memory(chat_id, agent, content, meta)


async def load_agent_memories(chat_id: str, agent: Optional[str] = None, 
                             limit: int = 100) -> List[Dict[str, Any]]:
    """Load agent memories"""
    store = await get_store()
    return await store.load_agent_memories(chat_id, agent, limit) 


async def clear_agent_memories(chat_id: str, agent: Optional[str] = None) -> int:
    """Clear agent memories"""
    store = await get_store()
    return await store.clear_agent_memories(chat_id, agent)


async def append_chat_log(chat_id: str, step: str, message: str, 
                         level: str = "info", details: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Compatibility wrapper: No-op log append."""
    return None


async def get_chat_logs(chat_id: str, limit: int = 200) -> List[Dict[str, Any]]:
    """Compatibility wrapper: Logs disabled; return empty list."""
    return []