"""
Session Memory System for Multimodal Agent

This module provides:
1. AgentMemory - per-agent in-memory storage with size limits
2. SessionContext - manages session state, memory, and logging
3. SessionManager - manages multiple sessions across WebSocket connections
"""

import asyncio
import json
import uuid
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Deque
from collections import deque
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    """Single memory entry for an agent"""
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        return cls(
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {})
        )


class AgentMemory:
    """Per-agent memory with size limits"""
    
    def __init__(self, agent_name: str, max_entries: int = 50, max_tokens: int = 4000):
        self.agent_name = agent_name
        self.max_entries = max_entries
        self.max_tokens = max_tokens
        self._entries: Deque[MemoryEntry] = deque(maxlen=max_entries)
        self._lock = asyncio.Lock()
    
    async def add(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a new memory entry"""
        async with self._lock:
            entry = MemoryEntry(
                content=content,
                timestamp=datetime.now(timezone.utc),
                metadata=metadata or {}
            )
            self._entries.append(entry)
    
    async def get_recent(self, count: int = 10) -> List[MemoryEntry]:
        """Get recent memory entries"""
        async with self._lock:
            return list(self._entries)[-count:]
    
    async def get_all(self) -> List[MemoryEntry]:
        """Get all memory entries"""
        async with self._lock:
            return list(self._entries)
    
    async def get_context_string(self, max_tokens: Optional[int] = None) -> str:
        """Get memory as a formatted context string for prompts"""
        async with self._lock:
            if not self._entries:
                return ""
            
            tokens = max_tokens or self.max_tokens
            context_parts = []
            current_tokens = 0
            
            # Start from most recent entries
            for entry in reversed(self._entries):
                entry_text = f"[{entry.timestamp.strftime('%H:%M')}] {entry.content}"
                estimated_tokens = len(entry_text.split()) * 1.3  # Rough token estimate
                
                if current_tokens + estimated_tokens > tokens:
                    break
                
                context_parts.insert(0, entry_text)
                current_tokens += estimated_tokens
            
            if context_parts:
                return f"Recent {self.agent_name} memory:\n" + "\n".join(context_parts)
            return ""
    
    async def clear(self) -> None:
        """Clear all memory entries"""
        async with self._lock:
            self._entries.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize memory to dict"""
        return {
            "agent_name": self.agent_name,
            "entries": [entry.to_dict() for entry in self._entries]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMemory':
        """Deserialize memory from dict"""
        memory = cls(
            agent_name=data["agent_name"],
            max_entries=data.get("max_entries", 50),
            max_tokens=data.get("max_tokens", 4000)
        )
        for entry_data in data.get("entries", []):
            memory._entries.append(MemoryEntry.from_dict(entry_data))
        return memory


@dataclass
class LogEntry:
    """Structured log entry for real-time streaming"""
    step: str
    level: str = "info"  # info, warning, error
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "level": self.level,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }


class SessionContext:
    """Manages session state, memory, and logging for a WebSocket connection"""
    
    def __init__(self, session_id: Optional[str] = None, chat_id: Optional[str] = None, 
                 user_id: Optional[str] = None, agent_names: Optional[List[str]] = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.chat_id = chat_id  # persistent chat id for this session
        self.user_id = user_id
        self.created_at = datetime.now(timezone.utc)
        self.last_active = self.created_at
        
        # Agent memories with larger capacity for in-memory storage
        self.agent_memories: Dict[str, AgentMemory] = {}
        for agent_name in (agent_names or ["research_agent", "asset_agent", "orchestrator"]):
            self.agent_memories[agent_name] = AgentMemory(agent_name, max_entries=200)
        
        # Real-time log queue (for streaming to client) - NOT persisted to MongoDB
        self.log_queue: Deque[LogEntry] = deque(maxlen=100)
        
        # Session metadata - NOT persisted to MongoDB
        self.metadata: Dict[str, Any] = {}
        
        # WebSocket reference (set by SessionManager)
        self.websocket: Optional[Any] = None
        
        # Track last persisted timestamps to avoid duplicate writes
        self._last_persisted_ts: Dict[str, float] = {}
        
        self._log_lock = asyncio.Lock()
    
    async def send_nano(self, agent: str, message: str) -> None:
        """Send a lightweight, transient nano message to the websocket client.

        These are not persisted; intended for fine-grained live status updates.
        """
        if not self.websocket:
            return
        try:
            await self.websocket.send_json({
                "event": "nano_message",
                "agent": agent,
                "message": message,
                "session_id": self.session_id,
                "chat_id": self.chat_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            logger.warning(f"Failed to send nano message: {e}")

    async def get_agent_memory(self, agent_name: str) -> AgentMemory:
        """Get memory for a specific agent"""
        if agent_name not in self.agent_memories:
            self.agent_memories[agent_name] = AgentMemory(agent_name)
        return self.agent_memories[agent_name]
    
    async def add_log(self, step: str, message: str = "", level: str = "info", 
                     details: Optional[Dict[str, Any]] = None, stream: bool = True) -> LogEntry:
        """Stream-only: convert logs to nano messages; do not persist or retain."""
        # Update last active but avoid keeping an in-memory log history
        async with self._log_lock:
            self.last_active = datetime.now(timezone.utc)

        # Emit nano message summarizing the log (suppress 'system' agent)
        if stream and self.websocket:
            try:
                agent = details.get("agent") if isinstance(details, dict) else None
                # Do not send nano if no agent provided or agent explicitly 'system'
                if not agent or str(agent).strip().lower() == "system":
                    raise Exception("suppress_system_nano")
                nm = f"{step}: {message}" if message else step
                await self.websocket.send_json({
                    "event": "nano_message",
                    "agent": agent,
                    "message": nm,
                    "session_id": self.session_id,
                    "chat_id": self.chat_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            except Exception as e:
                if str(e) != "suppress_system_nano":
                    logger.warning(f"Failed to stream nano from add_log: {e}")

        # Return a lightweight LogEntry for compatibility (not stored)
        return LogEntry(step=step, level=level, message=message, details=details or {})
    
    async def get_recent_logs(self, count: int = 20) -> List[LogEntry]:
        """Logs are not retained; return empty list."""
        return []
    
    async def get_all_logs(self) -> List[LogEntry]:
        """Logs are not retained; return empty list."""
        return []
    
    # -------------------
    # Chat-scoped memory hydration and persistence
    # -------------------
    async def hydrate_memories_from_db(self, chat_id: str, limit_per_agent: int = 200):
        """Hydrate in-memory memories from database for a chat"""
        self.chat_id = chat_id
        print(f"[DEBUG] Hydrating memories for chat_id: {chat_id}")
        
        try:
            # Import here to avoid circular imports
            from utils.mongo_store import load_agent_memories, get_chat_messages
            
            # Load memories for all agents
            for agent_name in self.agent_memories.keys():
                docs = await load_agent_memories(chat_id, agent=agent_name, limit=limit_per_agent)
                print(f"[DEBUG] Loaded {len(docs)} memories for agent {agent_name}")
                
                # Clear existing in-memory entries for this agent
                self.agent_memories[agent_name]._entries.clear()
                
                # Convert mongo docs to memory entries
                for doc in docs:
                    # Convert datetime to timestamp
                    ts = doc.get("ts")
                    if hasattr(ts, 'timestamp'):
                        timestamp = datetime.fromtimestamp(ts.timestamp(), tz=timezone.utc)
                    else:
                        timestamp = datetime.now(timezone.utc)
                    
                    content_str = doc.get("content", "")
                    meta = doc.get("meta", {})

                    # Skip control-only chat_id payloads accidentally stored as memory
                    skip = False
                    try:
                        if isinstance(content_str, str):
                            # JSON style {"chat_id": ...}
                            if '"chat_id"' in content_str:
                                start_idx = content_str.find("{")
                                end_idx = content_str.rfind("}")
                                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                                    import json as _json
                                    blob = content_str[start_idx:end_idx+1]
                                    obj = _json.loads(blob)
                                    if isinstance(obj, dict) and set(obj.keys()) <= {"chat_id", "type"}:
                                        skip = True
                            # Python dict style {'chat_id': ...}
                            if not skip and "'chat_id'" in content_str and '{' in content_str and '}' in content_str:
                                inner = content_str[content_str.find('{'):content_str.rfind('}')+1]
                                # heuristic: if it only mentions chat_id and maybe type, skip
                                if (":" in inner) and ("," not in inner) and "chat_id" in inner and "text" not in inner:
                                    skip = True
                            # Heuristic for prefixed formats
                            if not skip and "User query:" in content_str and "chat_id" in content_str and "text" not in content_str:
                                skip = True
                    except Exception:
                        pass
                    if skip:
                        continue

                    entry = MemoryEntry(
                        content=content_str,
                        timestamp=timestamp,
                        metadata=meta
                    )
                    self.agent_memories[agent_name]._entries.append(entry)
                
                # Update last persisted timestamp
                if docs:
                    last_doc = docs[-1]
                    last_ts = last_doc.get("ts")
                    if hasattr(last_ts, 'timestamp'):
                        self._last_persisted_ts[agent_name] = last_ts.timestamp()
                    else:
                        self._last_persisted_ts[agent_name] = time.time()

            # Additionally, hydrate from chat messages per agent so prompts reflect actual prior assistant replies
            try:
                all_msgs = await get_chat_messages(chat_id, limit=1000)
            except Exception as e:
                all_msgs = []
                logger.warning(f"Failed to load chat messages for hydration: {e}")

            if all_msgs:
                for msg in all_msgs:
                    role = msg.get("role")
                    agent = msg.get("agent") or ""
                    content = msg.get("content", "")
                    ts = msg.get("timestamp")

                    # Only inject assistant messages into the corresponding agent memory
                    if role == "assistant" and agent in self.agent_memories:
                        # Skip control-like content that only contains chat_id control frames
                        skip = False
                        try:
                            if isinstance(content, str) and content.strip().startswith("{"):
                                import json as _json
                                obj = _json.loads(content)
                                if isinstance(obj, dict) and set(obj.keys()) <= {"chat_id", "type"}:
                                    skip = True
                        except Exception:
                            pass
                        if skip:
                            continue

                        if hasattr(ts, 'timestamp'):
                            timestamp = datetime.fromtimestamp(ts.timestamp(), tz=timezone.utc)
                        else:
                            timestamp = datetime.now(timezone.utc)

                        entry = MemoryEntry(
                            content=f"Assistant reply: {content}",
                            timestamp=timestamp,
                            metadata={"source": "chat_message", "role": "assistant"}
                        )
                        self.agent_memories[agent]._entries.append(entry)
                
                # Optionally, add recent user messages to orchestrator memory for routing context
                if "orchestrator" in self.agent_memories:
                    for msg in all_msgs[-50:]:
                        if msg.get("role") == "user":
                            content = msg.get("content", "")
                            ts = msg.get("timestamp")
                            if hasattr(ts, 'timestamp'):
                                timestamp = datetime.fromtimestamp(ts.timestamp(), tz=timezone.utc)
                            else:
                                timestamp = datetime.now(timezone.utc)
                            entry = MemoryEntry(
                                content=f"User said: {content}",
                                timestamp=timestamp,
                                metadata={"source": "chat_message", "role": "user"}
                            )
                            self.agent_memories["orchestrator"]._entries.append(entry)
            
            self.last_active = datetime.now(timezone.utc)
            logger.info(f"Hydrated memories for chat {chat_id}")
            print(f"[DEBUG] Memory hydration completed for chat {chat_id}")
            
        except Exception as e:
            logger.error(f"Failed to hydrate memories for chat {chat_id}: {e}")
            print(f"[DEBUG] Memory hydration failed for chat {chat_id}: {e}")
            raise
    
    async def persist_memories_to_db(self):
        """Persist in-memory agent memories to database"""
        if not self.chat_id:
            logger.warning("No chat_id set, cannot persist memories")
            return
        
        try:
            # Import here to avoid circular imports
            from utils.mongo_store import append_agent_memory
            
            for agent_name, memory in self.agent_memories.items():
                last_ts = self._last_persisted_ts.get(agent_name, 0)
                
                # Only persist entries newer than last persisted timestamp
                for entry in memory._entries:
                    entry_ts = entry.timestamp.timestamp()
                    # Do not persist entries that originated from chat messages hydration to avoid duplication
                    if entry_ts > last_ts and entry.metadata.get("source") != "chat_message":
                        await append_agent_memory(
                            self.chat_id, 
                            agent_name, 
                            entry.content, 
                            meta=entry.metadata
                        )
                        self._last_persisted_ts[agent_name] = entry_ts
            
            logger.info(f"Persisted memories for chat {self.chat_id}")
            
        except Exception as e:
            logger.error(f"Failed to persist memories for chat {self.chat_id}: {e}")
            raise
    
    async def append_and_persist_memory(self, agent_name: str, content: str, 
                                      meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add memory entry and immediately persist to database"""
        if not self.chat_id:
            logger.warning("No chat_id set, cannot persist memory")
            # Still add to in-memory memory
            memory = await self.get_agent_memory(agent_name)
            await memory.add(content, meta)
            return {"content": content, "meta": meta or {}, "ts": time.time()}
        
        try:
            # Add to in-memory memory
            memory = await self.get_agent_memory(agent_name)
            await memory.add(content, meta)
            
            # Get the latest entry (just added)
            if memory._entries:
                latest_entry = memory._entries[-1]
                entry_ts = latest_entry.timestamp.timestamp()
                
                # Check if this is a new entry to persist
                last_ts = self._last_persisted_ts.get(agent_name, 0)
                if entry_ts > last_ts:
                    # Import here to avoid circular imports
                    from utils.mongo_store import append_agent_memory
                    
                    await append_agent_memory(
                        self.chat_id, 
                        agent_name, 
                        latest_entry.content, 
                        meta=latest_entry.metadata
                    )
                    self._last_persisted_ts[agent_name] = entry_ts
                
                return {
                    "content": latest_entry.content,
                    "meta": latest_entry.metadata,
                    "ts": entry_ts
                }
            
        except Exception as e:
            logger.error(f"Failed to append and persist memory: {e}")
            raise
        
        return {"content": content, "meta": meta or {}, "ts": time.time()}
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize session context to dict"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "agent_memories": {name: memory.to_dict() for name, memory in self.agent_memories.items()},
            "logs": [log.to_dict() for log in self.log_queue],
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionContext':
        """Deserialize session context from dict"""
        ctx = cls(
            session_id=data["session_id"],
            user_id=data.get("user_id"),
            agent_names=list(data.get("agent_memories", {}).keys())
        )
        ctx.created_at = datetime.fromisoformat(data["created_at"])
        ctx.last_active = datetime.fromisoformat(data["last_active"])
        ctx.metadata = data.get("metadata", {})
        
        # Restore agent memories
        for name, memory_data in data.get("agent_memories", {}).items():
            ctx.agent_memories[name] = AgentMemory.from_dict(memory_data)
        
        # Restore logs
        for log_data in data.get("logs", []):
            log_entry = LogEntry(
                step=log_data["step"],
                level=log_data.get("level", "info"),
                message=log_data.get("message", ""),
                details=log_data.get("details", {}),
                timestamp=datetime.fromisoformat(log_data["timestamp"])
            )
            ctx.log_queue.append(log_entry)
        
        return ctx


class SessionManager:
    """Manages multiple WebSocket sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, SessionContext] = {}
        self._lock = asyncio.Lock()
    
    async def create_session(self, user_id: Optional[str] = None, 
                           agent_names: Optional[List[str]] = None,
                           websocket: Optional[Any] = None,
                           chat_id: Optional[str] = None) -> SessionContext:
        """Create a new session"""
        session_id = str(uuid.uuid4())
        ctx = SessionContext(
            session_id=session_id,
            chat_id=chat_id,
            user_id=user_id,
            agent_names=agent_names
        )
        ctx.websocket = websocket
        
        async with self._lock:
            self.sessions[session_id] = ctx
        
        # Send session started event
        if websocket:
            try:
                await websocket.send_json({
                    "event": "session_started",
                    "session_id": session_id,
                    "chat_id": chat_id,
                    "timestamp": ctx.created_at.isoformat()
                })
            except Exception as e:
                logger.warning(f"Failed to send session_started event: {e}")
        
        return ctx
    
    async def get_session(self, session_id: str) -> Optional[SessionContext]:
        """Get an existing session"""
        async with self._lock:
            return self.sessions.get(session_id)
    
    async def remove_session(self, session_id: str) -> Optional[SessionContext]:
        """Remove a session (on WebSocket disconnect)"""
        async with self._lock:
            return self.sessions.pop(session_id, None)
    
    async def list_sessions(self) -> List[str]:
        """List all active session IDs"""
        async with self._lock:
            return list(self.sessions.keys())
    
    async def cleanup_inactive_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up inactive sessions"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        sessions_to_remove = []
        
        async with self._lock:
            for session_id, ctx in self.sessions.items():
                if ctx.last_active < cutoff_time:
                    sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                del self.sessions[session_id]
        
        return len(sessions_to_remove)


# Global session manager instance
SESSION_MANAGER = SessionManager()


# Helper functions for easy access
async def create_session(user_id: Optional[str] = None, 
                        agent_names: Optional[List[str]] = None,
                        websocket: Optional[Any] = None,
                        chat_id: Optional[str] = None) -> SessionContext:
    """Create a new session"""
    return await SESSION_MANAGER.create_session(user_id, agent_names, websocket, chat_id)


async def get_session(session_id: str) -> Optional[SessionContext]:
    """Get an existing session"""
    return await SESSION_MANAGER.get_session(session_id)


async def remove_session(session_id: str) -> Optional[SessionContext]:
    """Remove a session"""
    return await SESSION_MANAGER.remove_session(session_id)